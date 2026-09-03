"""D-060 link reachability — same-snapshot raw auto-wiring + frozen HTTP execution.

Pure/static/mock only (no protected bytes, no live HTTP, no model load).
Supersedes D-059 stage-only `calls == []` HOLD as implementation-stage-only fact;
proves canonical build_real_adapters/main_canonical_dev wiring (no manual injection).
"""
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from retrieval_v3.real_adapters import (
    RAW_EVIDENCE_SQL,
    RealEvaluationSession,
    RealSafetyAdapter,
    TransportOutcome,
    build_real_adapters,
    check_url_with_transport,
    http_client_transport,
)


def _safety_payload(visible):
    tr = {"task_id": "t1", "stratum": "natural_needs", "safe_action": "ANSWER",
          "retrieved": [{"source": s, "source_id": i} for s, i in visible],
          "retrieved_internal": [{"source": s, "source_id": i} for s, i in visible]}
    return {"config_id": "candidate-a-01", "results": {"task_results": [tr]}}


def _gov24_raw(online, detail="https://www.gov.kr/portal/detail"):
    return {"serviceList": {"상세조회URL": detail},
            "serviceDetail": {"온라인신청사이트URL": online}}


def _youth_raw(aply, ref1):
    return {"aplyUrlAddr": aply, "refUrlAddr1": ref1}


class FakeCursor:
    def __init__(self, conn):
        self._conn = conn
        self._rows = []

    def execute(self, sql, params=None):
        self._conn.statements.append(sql)
        flat = " ".join(str(sql).split())
        if flat == "SHOW TimeZone":
            self._rows = [self._conn.tz_value]
        elif flat == "SELECT CURRENT_DATE":
            self._rows = [self._conn.date_value]
        elif "FROM policy p LEFT JOIN" in flat:
            self._rows = list(self._conn.corpus_rows)
        elif "SELECT p.source, p.source_id, p.raw" in flat:
            self._rows = list(self._conn.raw_rows)
        else:
            raise AssertionError(f"unexpected SQL in D-060 mock: {flat[:100]}")

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)

    def close(self):
        pass


class FakeConn:
    def __init__(self, corpus_rows=(), raw_rows=()):
        self.corpus_rows = list(corpus_rows)
        self.raw_rows = list(raw_rows)
        self.tz_value = ("GMT",)
        self.date_value = ("2026-09-03",)
        self.statements = []
        self.set_session_calls = []
        self.closed = False

    def set_session(self, readonly=None, autocommit=None, isolation_level=None):
        self.set_session_calls.append((readonly, autocommit, isolation_level))

    def cursor(self):
        return FakeCursor(self)

    def close(self):
        self.closed = True


def _corpus_row(pid, source, sid, apply_url):
    # chunkless policy row (chunk_id None => no vector needed), 19 columns
    return (pid, source, sid, f"t-{sid}", f"o-{sid}", "sup", "sum",
            "kw", None, None, None, apply_url, None, None, None, None,
            None, None, None)


def _make_session(corpus_specs, raw_rows):
    """corpus_specs: list of (pid, source, sid, apply_url). raw_rows: list of (source, sid, raw)."""
    corpus_specs_sorted = sorted(corpus_specs, key=lambda t: (t[1], t[2]))
    corpus_rows = [_corpus_row(pid, s, i, u) for pid, s, i, u in corpus_specs_sorted]
    raw_sorted = sorted(list(raw_rows), key=lambda t: (t[0], t[1]))
    conn = FakeConn(corpus_rows=corpus_rows, raw_rows=raw_sorted)
    seen = {"calls": 0}

    def connect(dsn):
        seen["calls"] += 1
        assert seen["calls"] == 1, "second DB connection opened (fail: must reuse governing session)"
        return conn

    sess = RealEvaluationSession(env={"DATABASE_URL": "postgres://mock"}, connect_fn=connect)
    return sess, conn, seen


def _capture_and_load(sess):
    sess.capture_executor("SHOW TimeZone")
    sess.capture_executor("SELECT CURRENT_DATE")
    return sess.load_corpus_policies()


def _ok_transport(calls=None, status=200):
    def transport(url, method, timeout):
        if calls is not None:
            calls.append(url)
        return TransportOutcome(status=status)
    return transport


def test_d060_raw_sql_static_select_only_deterministic():
    flat = " ".join(RAW_EVIDENCE_SQL.split())
    head = flat.upper()
    assert head.startswith("SELECT")
    assert "ORDER BY" in head and "SOURCE" in head and "SOURCE_ID" in head
    for forbidden in ("INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER",
                      "TRUNCATE", "GRANT", "COPY", "VACUUM", "SET TIME ZONE",
                      "SET SESSION", "SET LOCAL", "LIMIT", "CURRENT_DATE"):
        assert forbidden not in head, f"raw evidence must stay SELECT-only, found {forbidden}"


def test_d060_construction_io_free_and_canonical_defaults():
    sess, conn, seen = _make_session([], [])
    adapters = build_real_adapters(sess, http_transport=_ok_transport())
    assert seen["calls"] == 0, "construction must perform no IO"
    safety = adapters["safety_evidence_fn"]
    assert safety._raw_lookup is not None, "canonical builder must auto-bind same-session raw evidence"
    assert callable(safety._raw_lookup)
    assert getattr(safety._raw_lookup, "__self__", None) is sess
    assert safety._http_transport is not None


def test_d060_canonical_auto_wiring_official_pass_http_pass():
    online = "https://apply.example/g1"
    sess, conn, seen = _make_session(
        [(1, "gov24", "g1", online)],
        [( "gov24", "g1", _gov24_raw(online))],
    )
    _capture_and_load(sess)
    calls = []
    adapters = build_real_adapters(sess, http_transport=_ok_transport(calls))
    ev = adapters["safety_evidence_fn"](_safety_payload([("gov24", "g1")]))
    assert ev["official_link"]["gate"] == "PASS"
    assert ev["http_resolution"]["gate"] == "PASS"
    assert ev["http_resolution"]["unique"] == 1
    assert ev["http_resolution"]["successes"] == 1
    assert ev["http_resolution"]["required"] == 1
    assert calls == [online]
    assert ev["cost"]["gate"] == "HOLD"
    assert seen["calls"] == 1, "raw evidence must reuse the governing connection"


def test_d060_raw_cached_no_second_query():
    online = "https://apply.example/g1"
    sess, conn, seen = _make_session(
        [(1, "gov24", "g1", online)],
        [("gov24", "g1", _gov24_raw(online))],
    )
    _capture_and_load(sess)
    adapters = build_real_adapters(sess, http_transport=_ok_transport())
    safety = adapters["safety_evidence_fn"]
    safety(_safety_payload([("gov24", "g1")]))
    raw_statements = [s for s in conn.statements if "p.source, p.source_id, p.raw" in " ".join(str(s).split())]
    assert len(raw_statements) == 1
    safety(_safety_payload([("gov24", "g1")]))
    raw_statements2 = [s for s in conn.statements if "p.source, p.source_id, p.raw" in " ".join(str(s).split())]
    assert len(raw_statements2) == 1, "second safety call must use cached raw map"
    assert seen["calls"] == 1


def test_d060_raw_before_capture_forbidden():
    sess, conn, seen = _make_session([], [])
    with pytest.raises(RuntimeError, match="capture"):
        sess.get_link_raw("gov24", "g1")
    assert seen["calls"] == 0, "failed pre-capture raw must not open a connection"


def test_d060_duplicate_raw_fail_closed_no_http():
    online = "https://apply.example/g1"
    sess, conn, seen = _make_session(
        [(1, "gov24", "g1", online)],
        [("gov24", "g1", _gov24_raw(online)), ("gov24", "g1", _gov24_raw(online))],
    )
    _capture_and_load(sess)
    calls = []
    adapters = build_real_adapters(sess, http_transport=_ok_transport(calls))
    ev = adapters["safety_evidence_fn"](_safety_payload([("gov24", "g1")]))
    assert ev["official_link"]["gate"] == "HOLD"
    assert ev["http_resolution"]["gate"] == "HOLD"
    assert calls == [], "non-authoritative denominator must never invoke HTTP"


def test_d060_malformed_identity_fail_closed():
    online = "https://apply.example/g1"
    sess, conn, seen = _make_session(
        [(1, "gov24", "g1", online)],
        [("  ", "g1", _gov24_raw(online))],
    )
    _capture_and_load(sess)
    calls = []
    adapters = build_real_adapters(sess, http_transport=_ok_transport(calls))
    ev = adapters["safety_evidence_fn"](_safety_payload([("gov24", "g1")]))
    assert ev["official_link"]["gate"] == "HOLD"
    assert ev["http_resolution"]["gate"] == "HOLD"
    assert calls == []


def test_d060_missing_and_nondict_raw_hold_no_http():
    online = "https://apply.example/y1"
    # missing raw
    sess, _, _ = _make_session([(1, "youth", "p0", online)], [])
    _capture_and_load(sess)
    calls = []
    ev = build_real_adapters(sess, http_transport=_ok_transport(calls))["safety_evidence_fn"](
        _safety_payload([("youth", "p0")]))
    assert ev["official_link"]["gate"] == "HOLD"
    assert ev["http_resolution"]["gate"] == "HOLD"
    assert calls == []
    # non-dict raw
    sess2, _, _ = _make_session([(1, "youth", "p0", online)], [("youth", "p0", None)])
    _capture_and_load(sess2)
    calls2 = []
    ev2 = build_real_adapters(sess2, http_transport=_ok_transport(calls2))["safety_evidence_fn"](
        _safety_payload([("youth", "p0")]))
    assert ev2["official_link"]["gate"] == "HOLD"
    assert ev2["http_resolution"]["gate"] == "HOLD"
    assert calls2 == []
    # malformed query identity never yields PASS
    sess3, _, _ = _make_session([(1, "youth", "p0", online)], [("youth", "p0", _youth_raw(online, online))])
    _capture_and_load(sess3)
    calls3 = []
    ev3 = build_real_adapters(sess3, http_transport=_ok_transport(calls3))["safety_evidence_fn"](
        {"config_id": "candidate-a-01", "results": {"task_results": [
            {"task_id": "t1", "stratum": "natural_needs", "safe_action": "ANSWER",
             "retrieved": [{"source": "youth", "source_id": "  "}],
             "retrieved_internal": [{"source": "youth", "source_id": "  "}]}]}})
    assert ev3["http_resolution"]["gate"] == "HOLD"
    assert calls3 == []


def test_d060_dedupe_trim_exact_single_http_call():
    url = "https://apply.example/shared"
    sess, _, _ = _make_session(
        [(1, "gov24", "g1", url), (2, "gov24", "g2", "  " + url + "  ")],
        [("gov24", "g1", _gov24_raw(url)), ("gov24", "g2", _gov24_raw(url))],
    )
    _capture_and_load(sess)
    calls = []
    ev = build_real_adapters(sess, http_transport=_ok_transport(calls))["safety_evidence_fn"](
        _safety_payload([("gov24", "g1"), ("gov24", "g2")]))
    assert ev["official_link"]["gate"] == "PASS"
    assert ev["official_link"]["unique"] == 1
    assert ev["http_resolution"]["gate"] == "PASS"
    assert ev["http_resolution"]["unique"] == 1
    assert calls == [url], "dedupe denominator executes exactly once per unique URL"


def test_d060_http_matrix_pass_nogo_hold():
    # PASS: all succeed
    u1, u2 = "https://a.example/1", "https://a.example/2"
    sess, _, _ = _make_session(
        [(1, "gov24", "g1", u1), (2, "gov24", "g2", u2)],
        [("gov24", "g1", _gov24_raw(u1)), ("gov24", "g2", _gov24_raw(u2))],
    )
    _capture_and_load(sess)
    calls = []
    ev = build_real_adapters(sess, http_transport=_ok_transport(calls))["safety_evidence_fn"](
        _safety_payload([("gov24", "g1"), ("gov24", "g2")]))
    assert ev["http_resolution"]["gate"] == "PASS"
    assert ev["http_resolution"]["unique"] == 2
    assert ev["http_resolution"]["required"] == 2
    assert sorted(calls) == sorted([u1, u2])
    # NO-GO: one HTTP 404 with small denominator (ceil(.99*2)=2)
    def mixed(url, method, timeout):
        calls_mixed.append(url)
        return TransportOutcome(status=200 if url == u1 else 404)
    calls_mixed = []
    sess2, _, _ = _make_session(
        [(1, "gov24", "g1", u1), (2, "gov24", "g2", u2)],
        [("gov24", "g1", _gov24_raw(u1)), ("gov24", "g2", _gov24_raw(u2))],
    )
    _capture_and_load(sess2)
    ev2 = build_real_adapters(sess2, http_transport=mixed)["safety_evidence_fn"](
        _safety_payload([("gov24", "g1"), ("gov24", "g2")]))
    assert ev2["http_resolution"]["gate"] == "NO-GO"
    assert ev2["http_resolution"]["successes"] == 1
    assert ev2["http_resolution"]["required"] == 2
    # HOLD: denominator 0 => no HTTP
    sess3, _, _ = _make_session([(1, "youth", "p0", None)], [("youth", "p0", {"aplyUrlAddr": "", "refUrlAddr1": ""})])
    _capture_and_load(sess3)
    calls3 = []
    ev3 = build_real_adapters(sess3, http_transport=_ok_transport(calls3))["safety_evidence_fn"](
        _safety_payload([("youth", "p0")]))
    assert ev3["http_resolution"]["gate"] == "HOLD"
    assert calls3 == []
    # HOLD: official NO-GO (drift) => HTTP not executed even with healthy transport
    sess4, _, _ = _make_session(
        [(1, "youth", "p0", "https://invented.example/evil")],
        [("youth", "p0", _youth_raw("https://real.example/a", "https://ref.example/b"))],
    )
    _capture_and_load(sess4)
    calls4 = []
    ev4 = build_real_adapters(sess4, http_transport=_ok_transport(calls4))["safety_evidence_fn"](
        _safety_payload([("youth", "p0")]))
    assert ev4["official_link"]["gate"] == "NO-GO"
    assert ev4["http_resolution"]["gate"] == "HOLD"
    assert calls4 == []


def test_d060_99pct_threshold_100_unique():
    specs, raws, urls = [], [], []
    for i in range(100):
        u = f"https://bulk.example/{i}"
        urls.append(u)
        specs.append((1000 + i, "gov24", f"b{i}", u))
        raws.append(("gov24", f"b{i}", _gov24_raw(u)))

    def bulk_payload():
        # Adapter measures visible top-5 per task; spread 100 identities over 20 tasks.
        tasks = []
        for t in range(20):
            chunk = [( "gov24", f"b{t * 5 + k}") for k in range(5)]
            tasks.append({"task_id": f"tb{t}", "stratum": "natural_needs", "safe_action": "ANSWER",
                          "retrieved": [{"source": s, "source_id": i} for s, i in chunk],
                          "retrieved_internal": [{"source": s, "source_id": i} for s, i in chunk]})
        return {"config_id": "candidate-a-01", "results": {"task_results": tasks}}

    sess, _, _ = _make_session(specs, raws)
    _capture_and_load(sess)
    # 99/100 => PASS (required 99)
    def ninety_nine(url, method, timeout):
        return TransportOutcome(status=404 if url == urls[-1] else 200)
    ev = build_real_adapters(sess, http_transport=ninety_nine)["safety_evidence_fn"](bulk_payload())
    assert ev["http_resolution"]["unique"] == 100
    assert ev["http_resolution"]["required"] == 99
    assert ev["http_resolution"]["successes"] == 99
    assert ev["http_resolution"]["gate"] == "PASS"
    # 98/100 => NO-GO
    sess2, _, _ = _make_session(specs, raws)
    _capture_and_load(sess2)

    def ninety_eight(url, method, timeout):
        return TransportOutcome(status=404 if url in (urls[-1], urls[-2]) else 200)
    ev2 = build_real_adapters(sess2, http_transport=ninety_eight)["safety_evidence_fn"](bulk_payload())
    assert ev2["http_resolution"]["required"] == math.ceil(0.99 * 100) == 99
    assert ev2["http_resolution"]["successes"] == 98
    assert ev2["http_resolution"]["gate"] == "NO-GO"


def test_d060_explicit_injection_still_overrides():
    sess, _, _ = _make_session([(1, "gov24", "g1", "https://apply.example/g1")], [])
    _capture_and_load(sess)
    sentinel = {("gov24", "g1"): _gov24_raw("https://apply.example/g1")}
    adapters = build_real_adapters(sess, http_transport=_ok_transport(), raw_lookup=sentinel)
    assert adapters["safety_evidence_fn"]._raw_lookup is sentinel


def test_d060_d057_state_machine_unchanged():
    # Frozen retry/redirect/fallback ownership spot-checks via counting mock transport.
    seen = []

    def ok(url, method, timeout):
        seen.append((url, method))
        return TransportOutcome(status=200)
    assert check_url_with_transport("https://x.example/", ok) is True
    assert seen == [("https://x.example/", "HEAD")]

    seen.clear()

    def notfound(url, method, timeout):
        seen.append((url, method))
        return TransportOutcome(status=404)
    assert check_url_with_transport("https://x.example/", notfound) is False
    assert seen == [("https://x.example/", "HEAD")]

    attempts = []

    def flaky(url, method, timeout):
        attempts.append(url)
        return TransportOutcome(status=200) if len(attempts) == 2 else TransportOutcome(status=500)
    assert check_url_with_transport("https://x.example/", flaky) is True
    assert len(attempts) == 2, "5xx must retry within the frozen state machine"
    assert http_client_transport.__name__ == "http_client_transport"


def test_d060_fail_on_old_static_proof():
    # ff9a579 lacked same-session auto-wiring and HTTP execution; current bytes must contain both.
    # No git history access here (boundary); this static proof fails on old bytes by construction.
    src = pathlib.Path(__file__).resolve().parent.joinpath("retrieval_v3", "real_adapters.py").read_text(encoding="utf-8")
    assert "RAW_EVIDENCE_SQL" in src
    assert "def get_link_raw" in src
    assert "check_url_with_transport(u, self._http_transport)" in src
    assert "math.ceil(0.99 * len(unique_urls))" in src
