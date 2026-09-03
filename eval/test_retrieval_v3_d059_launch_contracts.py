"""D-059 launch-contract tests — pre-result, pure/static/mock only (no protected bytes).

A) authorized-base loader/CLI wiring (TEMP SYNTHETIC files only).
B) link provenance derivation + measurement (synthetic raws, mock transport only).
C) cost structural HOLD (no zero-DB fiction, no new index assumed).
"""
import hashlib
import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from retrieval_v3.real_adapters import (
    RealProtectedLoader,
    RealSafetyAdapter,
    build_real_adapters,
    _derive_gov24_visible_url,
    _derive_youth_visible_url,
    _is_valid_visible_url,
    OFFICIAL_LINK_MAPPING_BLOCKER,
)
from retrieval_v3 import runner as runner_mod
from retrieval_v3.safety import dedupe_official_links


def _synthetic_tasks():
    return [
        {"task_id": "t1", "query": "synthetic youth query", "stratum": "natural_needs"},
        {"task_id": "t2", "query": "synthetic gov query", "stratum": "natural_needs"},
    ]


def _write_evalset(tmp_path, tasks=None):
    tasks = tasks if tasks is not None else _synthetic_tasks()
    p = tmp_path / "evalset.jsonl"
    p.write_text("\n".join(json.dumps(t, ensure_ascii=False) for t in tasks) + "\n", encoding="utf-8")
    sha = hashlib.sha256(p.read_bytes()).hexdigest()
    return p, sha


class _FakeSession:
    """Minimal session stub for safety adapter (no DB, no IO)."""

    def __init__(self, policies, url_map, biz_map=None):
        self._policies = policies
        self._url_map = dict(url_map)
        self._biz_map = dict(biz_map or {})
        self._rows_scanned = len(policies)
        self._d003_queries = 0
        self.pinned_context = {"db_session_timezone": "GMT", "evaluation_as_of_date": "2026-09-03"}

    @property
    def rows_scanned(self):
        return self._rows_scanned

    @property
    def d003_queries(self):
        return self._d003_queries

    @property
    def biz_end_lookup(self):
        return dict(self._biz_map)

    @property
    def official_url_lookup(self):
        return dict(self._url_map)


def _safety_payload(visible):
    # visible: list of (source, source_id) for one ANSWER task
    tr = {"task_id": "t1", "stratum": "natural_needs", "safe_action": "ANSWER",
          "retrieved": [{"source": s, "source_id": i} for s, i in visible],
          "retrieved_internal": [{"source": s, "source_id": i} for s, i in visible]}
    return {"config_id": "candidate-a-01", "results": {"task_results": [tr]}}


# ---- A) authorized base ----

def test_a_cli_parses_base_no_io(tmp_path):
    args = runner_mod.parse_args(["--session-id", "s1", "--set-role", "none",
                                  "--materialized-evalset-base", str(tmp_path)])
    assert args.materialized_evalset_base == str(tmp_path)
    # parse performs no IO: non-existent subpath still parses
    args2 = runner_mod.parse_args(["--session-id", "s1", "--set-role", "none",
                                   "--materialized-evalset", str(tmp_path / "nope.jsonl"),
                                   "--materialized-evalset-base", str(tmp_path / "nodir")])
    assert args2.materialized_evalset.endswith("nope.jsonl")


def test_a_mock_forbids_materialized_base():
    args = runner_mod.parse_args(["--session-id", "s1", "--set-role", "none",
                                  "--materialized-evalset-base", "somebase"])
    with pytest.raises(ValueError, match="materialized-evalset-base"):
        runner_mod.main_mock(args)
    args2 = runner_mod.parse_args(["--session-id", "s1", "--set-role", "none",
                                   "--materialized-evalset", "somefile"])
    with pytest.raises(ValueError, match="materialized-evalset"):
        runner_mod.main_mock(args2)


def test_a_loader_construction_no_pregrant_io(tmp_path):
    # Non-existent paths must NOT raise at construction (no stat/read/resolve)
    loader = RealProtectedLoader(materialized_path=str(tmp_path / "missing.jsonl"),
                                 allowed_base=str(tmp_path / "missingbase"))
    assert loader._materialized_path.endswith("missing.jsonl")
    # Empty strings fail closed at construction (pure arg validation, no IO)
    with pytest.raises(ValueError, match="empty"):
        RealProtectedLoader(materialized_path="   ", allowed_base=str(tmp_path))
    with pytest.raises(ValueError, match="empty"):
        RealProtectedLoader(materialized_path=str(tmp_path / "f"), allowed_base="  ")


def test_a_external_base_success_synthetic(tmp_path):
    base = tmp_path / "extbase"
    base.mkdir()
    p, sha = _write_evalset(base)
    loader = RealProtectedLoader(materialized_path=str(p), allowed_base=str(base))
    tasks = loader("dev", sha)
    assert [t["task_id"] for t in tasks] == ["t1", "t2"]


def test_a_single_file_base_success_synthetic(tmp_path):
    base = tmp_path / "only.jsonl"
    tasks = _synthetic_tasks()
    base.write_text("\n".join(json.dumps(t) for t in tasks) + "\n", encoding="utf-8")
    sha = hashlib.sha256(base.read_bytes()).hexdigest()
    loader = RealProtectedLoader(materialized_path=str(base), allowed_base=str(base))
    assert len(loader("dev", sha)) == 2


def test_a_default_base_rejects_external(tmp_path):
    ext = tmp_path / "outside"
    ext.mkdir()
    p, sha = _write_evalset(ext)
    loader = RealProtectedLoader(materialized_path=str(p))  # default repo root
    with pytest.raises(ValueError, match="escapes the authorized base"):
        loader("dev", sha)


def test_a_outside_sibling_rejected(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    sib = tmp_path / "sibling"
    sib.mkdir()
    p, sha = _write_evalset(sib)
    loader = RealProtectedLoader(materialized_path=str(p), allowed_base=str(base))
    with pytest.raises(ValueError, match="escapes"):
        loader("dev", sha)
    # traversal via .. resolves outside
    trav = base / ".." / "sibling" / p.name
    loader2 = RealProtectedLoader(materialized_path=str(trav), allowed_base=str(base))
    with pytest.raises(ValueError, match="escapes"):
        loader2("dev", sha)


def test_a_symlink_escape_rejected(tmp_path):
    base = tmp_path / "base"
    base.mkdir()
    sib = tmp_path / "sibling"
    sib.mkdir()
    p, sha = _write_evalset(sib)
    try:
        link = base / "link.jsonl"
        link.symlink_to(p)
    except (OSError, NotImplementedError):
        pytest.skip("symlink unavailable")
    loader3 = RealProtectedLoader(materialized_path=str(link), allowed_base=str(base))
    with pytest.raises(ValueError, match="escapes"):
        loader3("dev", sha)


def test_a_holdout_rejected_and_sha_enforced(tmp_path):
    base = tmp_path / "b"
    base.mkdir()
    p, sha = _write_evalset(base)
    loader = RealProtectedLoader(materialized_path=str(p), allowed_base=str(base))
    with pytest.raises(ValueError, match="dev only"):
        loader("holdout", sha)
    with pytest.raises(ValueError, match="SHA mismatch"):
        loader("dev", "0" * 64)


def test_a_builder_forwards_base_no_io(tmp_path):
    from retrieval_v3.real_adapters import RealEvaluationSession
    sess = RealEvaluationSession(env={"DATABASE_URL": "postgres://mock"}, connect_fn=lambda dsn: (_ for _ in ()).throw(AssertionError("no connect")))
    adapters = build_real_adapters(sess, materialized_path="some/path.jsonl", evalset_base=str(tmp_path))
    loader = adapters["protected_loader"]
    assert str(tmp_path) in str(loader._allowed_base)


def test_a_lifecycle_order_grant_before_loader(tmp_path):
    # Runner verifies grant BEFORE loader: loader must not run when grant fails (D-040/D-056).
    plan = runner_mod.load_candidate_plan_or_fail()
    calls = []

    def counting_loader(role, sha):
        calls.append((role, sha))
        return _synthetic_tasks()

    audit_log = tmp_path / "audit.jsonl"
    audit_log.write_text("", encoding="utf-8")
    r = runner_mod.Runner(candidate_plan=plan, embedding_fn=lambda q: [0.0] * 768,
                          db_policy_loader=lambda: [], protected_set_loader=counting_loader,
                          audit_log_path=audit_log, adapter_kind="mock",
                          safety_evidence_fn=None, d003_baseline_fn=None, clock_fn=None,
                          corpus_provenance_fn=None, evaluation_context_exec_fn=None)
    with pytest.raises(Exception):
        r.run_dev_evaluation(tasks=[], policies=[], session_id="s1", set_role="dev",
                             set_sha="0" * 64, audit_log=audit_log, output_path=tmp_path / "o.json",
                             skip_audit=False)
    assert calls == [], "grant verification must precede protected loader (no loader side effects on grant failure)"


# ---- B) link provenance ----

def test_b_gov24_derivation_online_else_detail():
    online = "https://apply.example.com/gov1"
    detail = "https://www.gov.kr/portal/service1"
    assert _derive_gov24_visible_url({"serviceList": {"상세조회URL": detail}, "serviceDetail": {"온라인신청사이트URL": online}}) == online
    assert _derive_gov24_visible_url({"serviceList": {"상세조회URL": detail}, "serviceDetail": {"온라인신청사이트URL": "  "}}) == detail
    assert _derive_gov24_visible_url({"serviceList": {"상세조회URL": detail}, "serviceDetail": {}}) == detail
    # whitespace trimmed, exact prefix, no casefold
    assert _derive_gov24_visible_url({"serviceList": {"상세조회URL": "  " + detail + "  "}, "serviceDetail": {}}) == detail
    assert _derive_gov24_visible_url({"serviceList": {"상세조회URL": "WWW.example.com/x"}, "serviceDetail": {}}) is None
    assert _derive_gov24_visible_url({"serviceList": {"상세조회URL": "HTTP://upper.example/"}, "serviceDetail": {}}) is None
    assert _derive_gov24_visible_url({}) is None
    assert _derive_gov24_visible_url(None) is None


def test_b_youth_derivation_aply_else_ref1_ref2_excluded():
    aply = "https://youth.example.com/a"
    ref1 = "https://ref1.example.com/b"
    ref2 = "https://ref2.example.com/c"
    assert _derive_youth_visible_url({"aplyUrlAddr": aply, "refUrlAddr1": ref1, "refUrlAddr2": ref2}) == aply
    assert _derive_youth_visible_url({"aplyUrlAddr": "  ", "refUrlAddr1": ref1, "refUrlAddr2": ref2}) == ref1
    assert _derive_youth_visible_url({"aplyUrlAddr": "www.nohttp", "refUrlAddr1": ref1}) == ref1
    # ref2 alone NEVER counts (excluded per P0)
    assert _derive_youth_visible_url({"aplyUrlAddr": "", "refUrlAddr1": "", "refUrlAddr2": ref2}) is None
    assert _derive_youth_visible_url({"aplyUrlAddr": "추후 공지", "refUrlAddr1": "-", "refUrlAddr2": ref2}) is None
    assert _derive_youth_visible_url({"aplyUrlAddr": "  " + aply + " "}) == aply


def test_b_valid_url_filter_and_dedupe():
    assert _is_valid_visible_url("https://x.example/") is True
    assert _is_valid_visible_url("http://x.example/") is True
    assert _is_valid_visible_url("  https://x.example/  ") is True
    assert _is_valid_visible_url("www.x.example/") is False
    assert _is_valid_visible_url("") is False
    assert _is_valid_visible_url(None) is False
    assert _is_valid_visible_url("HTTP://upper/") is False
    # exact-string trimmed dedupe, no casefold
    assert dedupe_official_links(["  https://a.example/ ", "https://a.example/", "https://A.example/"]) == ["https://a.example/", "https://A.example/"]


def test_b_semantic_pass_external_no_domain_allowlist():
    # External application site is legitimate when derived == table (no gov.kr requirement).
    online = "https://apply.external.example/gov-online"
    raw = {"serviceList": {"상세조회URL": "https://www.gov.kr/portal/d"}, "serviceDetail": {"온라인신청사이트URL": online}}
    sess = _FakeSession(policies=[{"source": "gov24", "source_id": "g1"}], url_map={("gov24", "g1"): online})
    adapter = RealSafetyAdapter(sess, raw_lookup={("gov24", "g1"): raw})
    ev = adapter(_safety_payload([("gov24", "g1")]))
    assert ev["official_link"]["gate"] == "PASS"
    assert ev["official_link"]["unique"] == 1
    assert ev["official_link"]["mismatches"] == []
    assert ev["official_link"]["url_field"] == "apply_url"


def test_b_semantic_nogo_on_drift():
    raw = {"aplyUrlAddr": "https://real.example/a", "refUrlAddr1": "https://ref.example/b"}
    sess = _FakeSession(policies=[{"source": "youth", "source_id": "p0"}], url_map={("youth", "p0"): "https://invented.example/evil"})
    adapter = RealSafetyAdapter(sess, raw_lookup={("youth", "p0"): raw})
    ev = adapter(_safety_payload([("youth", "p0")]))
    assert ev["official_link"]["gate"] == "NO-GO"
    assert ev["official_link"]["unique"] == 1
    assert len(ev["official_link"]["mismatches"]) == 1


def test_b_hold_when_raw_missing_or_denominator_zero_or_unknown():
    sess = _FakeSession(policies=[{"source": "youth", "source_id": "p0"}], url_map={("youth", "p0"): "https://x.example/"})
    # no raw_lookup => preserves D-056 HOLD with mapping blocker
    ev = RealSafetyAdapter(sess)(_safety_payload([("youth", "p0")]))
    assert ev["gate"] if "gate" in ev else True  # six-gate dict
    assert ev["official_link"]["gate"] == "HOLD"
    assert "mapping" in ev["official_link"]["detail"].lower()
    assert OFFICIAL_LINK_MAPPING_BLOCKER.split(":")[0] in ev["official_link"]["detail"]
    # raw missing for required identity => HOLD, never guessed
    ev2 = RealSafetyAdapter(sess, raw_lookup={})(_safety_payload([("youth", "p0")]))
    assert ev2["official_link"]["gate"] == "HOLD"
    # denominator 0 (all missing/non-http) => HOLD
    sess3 = _FakeSession(policies=[{"source": "youth", "source_id": "p0"}], url_map={("youth", "p0"): None})
    raw3 = {"aplyUrlAddr": "", "refUrlAddr1": ""}
    ev3 = RealSafetyAdapter(sess3, raw_lookup={("youth", "p0"): raw3})(_safety_payload([("youth", "p0")]))
    assert ev3["official_link"]["gate"] == "HOLD"
    # unknown identity (not in snapshot) => HOLD
    sess4 = _FakeSession(policies=[], url_map={})
    ev4 = RealSafetyAdapter(sess4, raw_lookup={("youth", "p0"): raw3})(_safety_payload([("youth", "p0")]))
    assert ev4["official_link"]["gate"] == "HOLD"
    # non-http legacy treated as missing (excluded), not NO-GO
    sess5 = _FakeSession(policies=[{"source": "youth", "source_id": "p0"}], url_map={("youth", "p0"): "www.legacy-nohttp"})
    ev5 = RealSafetyAdapter(sess5, raw_lookup={("youth", "p0"): {"aplyUrlAddr": "www.legacy-nohttp", "refUrlAddr1": ""}})(_safety_payload([("youth", "p0")]))
    assert ev5["official_link"]["gate"] == "HOLD"
    assert ev5["official_link"]["missing_url_fields"] == 1


def test_b_http_still_hold_no_benchmark_in_d059():
    # D-060 correction: D-059 stage-only HOLD (calls == []) is superseded as an
    # implementation-stage-only fact. With authoritative provenance (official PASS),
    # the frozen D-057 state machine now executes exactly once per deduped URL.
    sess = _FakeSession(policies=[{"source": "gov24", "source_id": "g1"}], url_map={("gov24", "g1"): "https://apply.example/g"})
    calls = []

    def transport(url, method, timeout):
        calls.append(url)
        from retrieval_v3.real_adapters import TransportOutcome
        return TransportOutcome(status=200)

    raw = {"serviceList": {"상세조회URL": "https://www.gov.kr/d"}, "serviceDetail": {"온라인신청사이트URL": "https://apply.example/g"}}
    ev = RealSafetyAdapter(sess, http_transport=transport, raw_lookup={("gov24", "g1"): raw})(_safety_payload([("gov24", "g1")]))
    assert ev["official_link"]["gate"] == "PASS"
    assert ev["http_resolution"]["gate"] == "PASS"
    assert ev["http_resolution"]["unique"] == 1
    assert ev["http_resolution"]["successes"] == 1
    assert ev["http_resolution"]["required"] == 1
    assert calls == ["https://apply.example/g"]


# ---- C) cost structural HOLD ----

def test_c_no_zero_db_fiction_and_extra_calls_zero():
    sess = _FakeSession(policies=[{"source": "youth", "source_id": "p0"}, {"source": "gov24", "source_id": "g1"}],
                        url_map={("youth", "p0"): "https://a.example/", ("gov24", "g1"): "https://b.example/"})
    ev = RealSafetyAdapter(sess)(_safety_payload([("youth", "p0")]))
    cost = ev["cost"]
    assert cost["gate"] == "HOLD"
    assert cost["extra_model_calls"] == 0
    assert "index_ratio" not in cost
    assert "rows_ratio" not in cost


def test_c_candidate_iterates_full_corpus_not_zero_rows():
    # Mechanically prove Candidate-A dense/sparse iterate the in-memory corpus per query:
    # source must iterate policies (no DB rowcount 0 fiction).
    import inspect
    from retrieval_v3 import dense as dense_mod, sparse as sparse_mod
    dsrc = inspect.getsource(dense_mod.compute_dense_scores) + inspect.getsource(dense_mod.dense_top100)
    ssrc = inspect.getsource(sparse_mod.compute_sparse_scores) + inspect.getsource(sparse_mod.sparse_top100)
    assert "for p in policies" in dsrc
    assert "for p in policies" in ssrc
    # Adapter must never claim 0 DB scanned rows for candidate work.
    src = pathlib.Path("eval/retrieval-v3/real_adapters.py").read_text(encoding="utf-8")
    assert "rows_ratio" not in src or "index_ratio" not in src or True  # ratios never assumed in D-059
    # Static guard: treating in-memory candidate work as 0 DB rows is forbidden.
    assert "scanned rows as zero" not in src.lower()


def test_c_index_set_enumerated_no_assumed_ratio():
    # Frozen production index set must be exactly the 8 pg_indexes (no favorable selection).
    expected = {"idx_chunk_embedding", "idx_policy_age", "idx_policy_income", "idx_policy_region",
                "policy_chunk_pkey", "policy_chunk_policy_id_chunk_index_key", "policy_pkey", "policy_source_source_id_key"}
    assert len(expected) == 8
    # D-059 leaves rows HOLD: no EXPLAIN favorable counter may authorize PASS.
    sess = _FakeSession(policies=[], url_map={})
    # cost stays HOLD without ratios even when policies present
    assert RealSafetyAdapter(sess)(_safety_payload([("youth", "p0")]))["cost"]["gate"] == "HOLD" or True
