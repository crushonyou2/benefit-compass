"""D-057 narrow repair — single-attempt HTTP primitive + REPEATABLE READ snapshot.

Web HOLD repair (same logical stage, no FIRST dev):
A) `http_client_transport` is ONE HTTP attempt (no retry, no redirect follow);
   outer `check_url_with_transport` exclusively owns retry/redirect/method/
   fallback/hop sequencing with urljoin-relative resolution. Connect 5s and
   read 10s enforced mechanically (constructor 5, explicit connect, socket
   settimeout 10 before request, close exact-once).
B) ONE governing connection configured BEFORE the first statement as one
   read-only REPEATABLE READ transaction with autocommit FALSE, covering
   capture -> corpus load/fingerprint -> every D-003 baseline SQL.

Fake/monkeypatched http.client + socket only. No real benchmark HTTP, no
protected dev/holdout plaintext, no real DB connect/query, no model load.
"""
import datetime
import hashlib
import json
import pathlib
import socket
import ssl
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from retrieval_v3.real_adapters import (
    CORPUS_SQL,
    D003_SQL,
    RealD003Baseline,
    RealEvaluationSession,
    RealProtectedLoader,
    TransportOutcome,
    build_real_adapters,
    check_url_with_transport,
    http_client_transport,
)
from retrieval_v3.runner import Runner
from retrieval_v3.candidate_registry import load_and_validate
from retrieval_v3.safety import (
    MockHttpResponse,
    check_single_url_with_mock,
)
from retrieval_v3 import audit as _audit

SYN_TZ = "SYNTH-TZ"
SYN_DATE = "2026-02-10"


def _vec_text(seed, n=768):
    import random as _r
    rnd = _r.Random(seed)
    return "[" + ",".join(f"{x:.6f}" for x in (rnd.uniform(-1, 1) for _ in range(n))) + "]"


def _corpus_rows(specs):
    rows = []
    for pid, source, sid, nchunks, biz_end in specs:
        for ci in range(nchunks):
            rows.append((
                pid, source, sid, f"t-{sid}", f"o-{sid}", "sup", "sum",
                "kw", None, None, None, f"https://apply.example/{sid}",
                biz_end, None, None, None,
                pid * 100 + ci, ci, _vec_text(pid * 10 + ci),
            ))
    rows.sort(key=lambda r: (r[1], r[2], r[17], r[16]))
    return rows


class FakeCursor:
    def __init__(self, conn):
        self._conn = conn
        self._rows = []

    def execute(self, sql, params=None):
        self._conn.statements.append(sql)
        self._conn.params.append(params)
        flat = " ".join(str(sql).split())
        if flat == "SHOW TimeZone":
            self._rows = [self._conn.tz_value]
        elif flat == "SELECT CURRENT_DATE":
            self._rows = [self._conn.date_value]
        elif "WITH nearest" in flat:
            self._rows = list(self._conn.d003_rows)
        elif "FROM policy p LEFT JOIN" in flat:
            self._rows = list(self._conn.corpus_rows)
        else:
            raise AssertionError(f"unexpected SQL in D-057 mock: {flat[:90]}")

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)

    def close(self):
        pass


class FakeConn:
    def __init__(self, corpus_rows=(), tz_value=(SYN_TZ,), date_value=None, d003_rows=()):
        self.corpus_rows = list(corpus_rows)
        self.tz_value = tz_value
        self.date_value = date_value if date_value is not None else (datetime.date(2026, 2, 10),)
        self.d003_rows = list(d003_rows)
        self.statements = []
        self.params = []
        self.closed = False
        self.set_session_calls = []
        self.events = []

    def set_session(self, readonly=None, autocommit=None, isolation_level=None):
        self.set_session_calls.append({"readonly": readonly, "autocommit": autocommit, "isolation_level": isolation_level})
        self.events.append("set_session")

    def cursor(self):
        self.events.append("cursor")
        return FakeCursor(self)

    def close(self):
        self.closed = True


def _session(conn, dsn="postgres://mock"):
    seen = {}

    def connect(got):
        seen["dsn"] = got
        seen["calls"] = seen.get("calls", 0) + 1
        return conn

    session = RealEvaluationSession(env={"DATABASE_URL": dsn}, connect_fn=connect)
    return session, seen


# ---- A) single-attempt primitive mechanics (fake http.client) ----

class _FakeSock:
    def __init__(self):
        self.timeouts = []

    def settimeout(self, t):
        self.timeouts.append(t)


class _FakeResp:
    def __init__(self, status, location=None):
        self.status = status
        self._location = location

    def getheader(self, name):
        if name == "Location":
            return self._location
        return None


def _patch_conns(monkeypatch, script, record, fail_mode=None):
    """Patch HTTPConnection/HTTPSConnection with scripted single-response fakes.

    script: dict {(host, path): (status, location)} or callable.
    record: dict collecting constructor timeout, connect, request, close counts.
    fail_mode: None | 'connect-timeout' | 'request-timeout' | 'tls' | 'network'.
    """
    import http.client as _hc

    instances = []
    record["instances"] = instances

    class _FakeHTTP:
        def __init__(self, host, port=None, timeout=None, context=None):
            self.host = host
            self.port = port
            self.timeout_at_construct = timeout
            self.context = context
            self.connected = False
            self.requests = []
            self.closes = 0
            self.sock = _FakeSock()
            instances.append(self)
            record.setdefault("construct_timeouts", []).append(timeout)

        def connect(self):
            record["connects"] = record.get("connects", 0) + 1
            if fail_mode == "connect-timeout":
                raise socket.timeout("connect timed out")
            if fail_mode == "tls":
                raise ssl.SSLError("handshake failed")
            if fail_mode == "network":
                raise ConnectionRefusedError("refused")
            self.connected = True

        def request(self, method, path, headers=None):
            assert self.connected, "request before explicit connect"
            assert self.sock.timeouts == [10], f"socket read timeout 10 must precede request, got {self.sock.timeouts}"
            record.setdefault("requests", []).append((self.host, path, method))
            self.requests.append((method, path))
            if fail_mode == "request-timeout":
                raise socket.timeout("read timed out")

        def getresponse(self):
            key = (self.host, self.requests[-1][1] if self.requests else "/")
            if callable(script):
                st, loc = script(self.host, self.requests[-1][1], self.requests[-1][0])
            elif isinstance(script, dict):
                st, loc = script.get(key, (200, None))
            else:
                st, loc = script
            record.setdefault("responses", []).append((st, loc))
            return _FakeResp(st, loc)

        def close(self):
            self.closes += 1
            record["closes"] = record.get("closes", 0) + 1

    monkeypatch.setattr(_hc, "HTTPConnection", _FakeHTTP)
    monkeypatch.setattr(_hc, "HTTPSConnection", _FakeHTTP)
    return _FakeHTTP


def test_d057_transport_connect5_read10_http(monkeypatch):
    record = {}
    _patch_conns(monkeypatch, (200, None), record)
    out = http_client_transport("http://example.com/a", "HEAD", (5, 10))
    assert isinstance(out, TransportOutcome) and out.status == 200 and out.error is None
    assert record["construct_timeouts"] == [5], f"constructor must carry connect timeout 5, got {record['construct_timeouts']}"
    assert record.get("connects") == 1, "explicit connect required"
    inst = record["instances"][0]
    assert inst.sock.timeouts == [10], "connected socket must be set to read timeout 10 before request"
    assert record["requests"] == [("example.com", "/a", "HEAD")]
    assert record.get("closes") == 1, "close exact-once on success"


def test_d057_transport_connect5_read10_https(monkeypatch):
    record = {}
    _patch_conns(monkeypatch, (200, None), record)
    out = http_client_transport("https://example.com/s?q=1", "GET", (5, 10))
    assert out.status == 200
    assert record["construct_timeouts"] == [5]
    assert record.get("connects") == 1
    assert record["requests"] == [("example.com", "/s?q=1", "GET")]
    assert record.get("closes") == 1


def test_d057_transport_close_once_on_timeout(monkeypatch):
    record = {}
    _patch_conns(monkeypatch, (200, None), record, fail_mode="request-timeout")
    out = http_client_transport("http://example.com/a", "HEAD", (5, 10))
    assert out.error == "timeout" and out.status is None
    assert record.get("closes") == 1, "close exact-once on read-timeout failure"


def test_d057_transport_close_once_on_connect_failure(monkeypatch):
    record = {}
    _patch_conns(monkeypatch, (200, None), record, fail_mode="connect-timeout")
    out = http_client_transport("http://example.com/a", "HEAD", (5, 10))
    assert out.error == "timeout"
    assert record.get("closes") == 1, "close exact-once on connect failure"


def test_d057_transport_tls_and_network_classification(monkeypatch):
    record = {}
    _patch_conns(monkeypatch, (200, None), record, fail_mode="tls")
    assert http_client_transport("https://example.com/a", "HEAD", (5, 10)).error == "tls"
    assert record.get("closes") == 1
    record2 = {}
    _patch_conns(monkeypatch, (200, None), record2, fail_mode="network")
    assert http_client_transport("http://example.com/a", "HEAD", (5, 10)).error == "network"
    assert record2.get("closes") == 1


def test_d057_transport_single_attempt_301_no_follow(monkeypatch):
    record = {}
    _patch_conns(monkeypatch, {("example.com", "/start"): (301, "http://example.com/next")}, record)
    out = http_client_transport("http://example.com/start", "HEAD", (5, 10))
    assert out.status == 301 and out.location == "http://example.com/next"
    assert record["requests"] == [("example.com", "/start", "HEAD")], "ONE transport call must cause exactly ONE request"
    assert all(u != "http://example.com/next" or True for u in [r[0] for r in record["requests"]])
    assert len(record["instances"]) == 1, "no hidden second connection for the redirect"


def test_d057_outer_owns_redirect_relative_method_preserved():
    calls = []

    def t(url, method, timeout):
        assert timeout == (5, 10)
        calls.append((url, method))
        if len(calls) == 1:
            assert url == "http://example.com/start" and method == "HEAD"
            return TransportOutcome(status=301, location="/next")
        assert url == "http://example.com/next" and method == "HEAD", f"outer must resolve relative Location via urljoin preserving method, got {url} {method}"
        return TransportOutcome(status=200)

    assert check_url_with_transport("http://example.com/start", t) is True
    assert calls == [("http://example.com/start", "HEAD"), ("http://example.com/next", "HEAD")]


def test_d057_outer_redirect_fresh_retry_budget_per_hop():
    calls = []

    def t(url, method, timeout):
        calls.append(url)
        n = len(calls)
        if n == 1:
            return TransportOutcome(status=500)
        if n == 2:
            return TransportOutcome(status=301, location="http://example.com/h2")
        if n == 3:
            return TransportOutcome(status=500)
        return TransportOutcome(status=200)

    assert check_url_with_transport("http://example.com/h1", t) is True
    assert len(calls) == 4, f"each hop gets a fresh max-2 budget, got {len(calls)} calls"


def test_d057_outer_more_than_3_redirects_fails_no_hidden():
    calls = []

    def t(url, method, timeout):
        calls.append((url, method))
        return TransportOutcome(status=301, location="http://example.com/r%d" % len(calls))

    assert check_url_with_transport("http://example.com/r0", t) is False
    assert len(calls) == 4, f"initial + 3 hops then fail, no hidden extra requests, got {len(calls)}"
    assert all(m == "HEAD" for _, m in calls), "method preserved across redirect hops"


def test_d057_outer_parity_with_frozen_state_machine():
    def scripted(head_seq, get_seq):
        h, g = list(head_seq), list(get_seq)

        def t(url, method, timeout):
            assert timeout == (5, 10)
            seq = h if method == "HEAD" else g
            assert seq, "mock exhaustion must fail closed"
            kind = seq.pop(0)
            if kind[0] == "status":
                return TransportOutcome(status=kind[1], location=kind[2] if len(kind) > 2 else None)
            return TransportOutcome(error=kind[1])

        return t

    def mock_resp(kind):
        if kind[0] == "status":
            return MockHttpResponse(status=kind[1], redirect_location=kind[2] if len(kind) > 2 else None)
        flag = kind[1]
        return MockHttpResponse(status=None, is_network_error=flag == "network",
                                is_tls_error=flag == "tls", is_timeout=flag == "timeout")

    R1 = "https://apply.example/a"
    R2 = "https://apply.example/b"
    scenarios = [
        ([("status", 200)], [], True),
        ([("status", 405)], [("status", 200)], True),
        ([("status", 501)], [("status", 200)], True),
        ([("status", 404)], [], False),
        ([("status", 500), ("status", 200)], [], True),
        ([("status", 500), ("status", 500)], [], False),
        ([("error", "timeout"), ("error", "timeout")], [("status", 200)], False),
        ([("error", "timeout"), ("status", 200)], [], True),
        ([("error", "network"), ("error", "network")], [("status", 200)], True),
        ([("error", "tls"), ("error", "tls")], [("status", 200)], True),
        ([("status", 301, R1), ("status", 200)], [], True),
        ([("status", 301, R1)] * 4, [], False),
        ([("status", 405)], [("status", 405)], False),
        ([("status", 301, R1), ("status", 500), ("status", 200)], [], True),
        ([("status", 301, R1), ("status", 301, R2), ("status", 200)], [], True),
    ]
    for head, get, expected in scenarios:
        got = check_url_with_transport(R1, scripted(list(head), list(get)))
        want = check_single_url_with_mock(R1, [mock_resp(k) for k in head], [mock_resp(k) for k in get])
        assert got == want == expected, f"parity failed for {head}/{get}: {got} vs {want}"
    assert check_url_with_transport("  ", scripted([], [])) is False


def test_d057_outer_rejects_non_http_redirect_target():
    def t(url, method, timeout):
        if url == "http://example.com/start":
            return TransportOutcome(status=301, location="ftp://example.com/x")
        raise AssertionError("must not request non-http target")

    assert check_url_with_transport("http://example.com/start", t) is False


# ---- B) REPEATABLE READ consistent-snapshot session ----

def test_d057_session_config_exact_before_first_statement():
    conn = FakeConn(corpus_rows=_corpus_rows([(1, "youth", "p0", 1, None)]))
    session, seen = _session(conn)
    session.capture_executor("SHOW TimeZone")
    assert conn.set_session_calls == [{"readonly": True, "autocommit": False, "isolation_level": "REPEATABLE READ"}], \
        f"exact session config required, got {conn.set_session_calls}"
    assert conn.events[0] == "set_session" and conn.events[1] == "cursor", \
        f"config must precede the first cursor/statement, got {conn.events[:4]}"
    assert seen["calls"] == 1
    session.capture_executor("SELECT CURRENT_DATE")
    assert len(conn.set_session_calls) == 1, "config exactly once per governing connection"
    session.close()


def test_d057_session_config_rejects_autocommit_regression_static():
    import pathlib as _p
    src = (_p.Path(__file__).resolve().parent / "retrieval-v3" / "real_adapters.py").read_text(encoding="utf-8")
    assert 'autocommit=False' in src, "autocommit FALSE is the frozen D-057 contract"
    assert 'isolation_level="REPEATABLE READ"' in src or "isolation_level='REPEATABLE READ'" in src
    assert "readonly=True" in src
    assert "conn.set_session(readonly=True, autocommit=True)" not in src, "READ COMMITTED/autocommit regression forbidden"


def test_d057_same_connection_for_capture_corpus_d003():
    specs = [(1, "youth", "p0", 1, None), (2, "gov24", "g1", 1, None)]
    conn = FakeConn(corpus_rows=_corpus_rows(specs))
    session, seen = _session(conn)
    session.capture_executor("SHOW TimeZone")
    session.capture_executor("SELECT CURRENT_DATE")
    session.load_corpus_policies()
    d003_statements_before = list(conn.statements)
    session.execute_readonly("WITH nearest AS (SELECT 1) SELECT 1", {"as_of": SYN_DATE})
    assert seen["calls"] == 1, "no reconnect during evaluation: one governing connection"
    assert session._conn is conn, "same connection object for capture, corpus, and D-003"
    assert conn.statements[0] == "SHOW TimeZone" and conn.statements[1] == "SELECT CURRENT_DATE"
    assert any("FROM policy p LEFT JOIN" in s for s in conn.statements), "corpus load on the same connection"
    assert d003_statements_before[:2] == ["SHOW TimeZone", "SELECT CURRENT_DATE"]
    session.close()


def test_d057_no_post_capture_current_date_no_timezone_set():
    conn = FakeConn(corpus_rows=_corpus_rows([(1, "youth", "p0", 1, None)]))
    session, _ = _session(conn)
    session.capture_executor("SHOW TimeZone")
    session.capture_executor("SELECT CURRENT_DATE")
    session.load_corpus_policies()
    session.execute_readonly("WITH nearest AS (SELECT 1) SELECT 1", {"as_of": SYN_DATE})
    post = [s for s in conn.statements if s not in ("SHOW TimeZone", "SELECT CURRENT_DATE")]
    assert post, "corpus + D-003 run post-capture"
    assert all("CURRENT_DATE" not in s for s in post), "no second CURRENT_DATE after pinning"
    flat_all = " ".join(conn.statements).upper()
    assert "SET TIME ZONE" not in flat_all and "SET SESSION" not in flat_all and "SET LOCAL" not in flat_all
    session.close()


def test_d057_close_exact_once_success_and_failures():
    # Success path: full capture -> corpus -> query, then exact-once close.
    conn = FakeConn(corpus_rows=_corpus_rows([(1, "youth", "p0", 1, None)]))
    session, _ = _session(conn)
    session.capture_executor("SHOW TimeZone")
    session.capture_executor("SELECT CURRENT_DATE")
    session.load_corpus_policies()
    session.execute_readonly("WITH nearest AS (SELECT 1) SELECT 1", {"as_of": SYN_DATE})
    session.close()
    assert session.is_closed is True and conn.closed is True
    try:
        session.close()
        assert False, "second close must raise"
    except RuntimeError:
        pass
    # Failure paths still own exact-once close (session closes, second raises).
    for failing_sql in ("SELECT 1", "DELETE FROM policy", "DROP TABLE policy"):
        c2 = FakeConn(corpus_rows=_corpus_rows([(1, "youth", "p0", 1, None)]))
        s2, _ = _session(c2)
        s2.capture_executor("SHOW TimeZone")
        s2.capture_executor("SELECT CURRENT_DATE")
        try:
            if failing_sql.startswith("SELECT 1"):
                s2.capture_executor(failing_sql)
            else:
                s2.execute_readonly(failing_sql)
            assert False, f"must fail for {failing_sql}"
        except (ValueError, RuntimeError, AssertionError):
            pass
        s2.close()
        assert s2.is_closed is True
        try:
            s2.close()
            assert False, "second close must raise"
        except RuntimeError:
            pass


def test_d057_injected_path_same_contract_as_real_psycopg2():
    import sys as _sys
    real_calls = {}

    class FakeDriverConn(FakeConn):
        pass

    driver_conn = FakeDriverConn()
    fake_mod = type(_sys)("psycopg2")
    fake_mod.connect = lambda dsn: (real_calls.setdefault("dsn", dsn), driver_conn)[1]
    _sys.modules["psycopg2"] = fake_mod
    try:
        session = RealEvaluationSession(env={"DATABASE_URL": "postgres://db"})
        session.capture_executor("SHOW TimeZone")
    finally:
        del _sys.modules["psycopg2"]
    assert driver_conn.set_session_calls == [{"readonly": True, "autocommit": False, "isolation_level": "REPEATABLE READ"}]
    # Injected path must match exactly.
    conn2 = FakeConn()
    session2, _ = _session(conn2)
    session2.capture_executor("SHOW TimeZone")
    assert conn2.set_session_calls == driver_conn.set_session_calls
    session.close()
    session2.close()


def test_d057_ordering_session_config_before_show_before_date_before_corpus():
    conn = FakeConn(corpus_rows=_corpus_rows([(1, "youth", "p0", 1, None)]))
    session, _ = _session(conn)
    session.capture_executor("SHOW TimeZone")
    session.capture_executor("SELECT CURRENT_DATE")
    session.load_corpus_policies()
    assert conn.events[0] == "set_session"
    assert conn.statements[:2] == ["SHOW TimeZone", "SELECT CURRENT_DATE"]
    corpus_idx = next(i for i, s in enumerate(conn.statements) if "FROM policy p LEFT JOIN" in s)
    assert corpus_idx == 2, f"corpus immediately after capture on the same snapshot, got {corpus_idx}"
    session.close()


def test_d057_d003_sql_parity_modulo_pinned_date():
    import re
    repo = pathlib.Path(__file__).resolve().parents[1]
    src = (repo / "ml-service" / "app.py").read_text(encoding="utf-8")
    prod = re.search(r"SQL = \"\"\"(.*?)\"\"\"", src, re.S).group(1)

    def norm(s):
        s = "\n".join(line.split("--")[0] for line in s.splitlines())
        return re.sub(r"\s+", " ", s).strip()

    assert norm(D003_SQL.replace("%(as_of)s", "CURRENT_DATE")) == norm(prod), "D-003 SQL must equal production modulo the pinned date"
    assert "CURRENT_DATE" not in D003_SQL, "pinned %(as_of)s replaces both CURRENT_DATE predicates"
    assert D003_SQL.count("%(as_of)s") == 2, "both expiry predicates carry the pinned date"
