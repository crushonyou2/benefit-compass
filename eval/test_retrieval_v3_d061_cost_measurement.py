"""D-061 cost measurement — pure/static/mock only (no protected, no model, no HTTP/DB writes)."""
import hashlib
import json
import math
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from retrieval_v3.cost import (
    ALL_INDEXES_SQL,
    CANDIDATE_DENSE_SHADOW_SQL,
    CANDIDATE_SPARSE_SHADOW_SQL,
    EXPLAIN_PREFIX,
    FROZEN_BASELINE_INDEXES,
    INDEX_FOOTPRINT_SQL,
    aggregate_task_ratios,
    assert_lexical_terms_safe,
    compute_index_ratio,
    count_base_scanned_rows,
    parse_explain_rows,
)
from retrieval_v3.real_adapters import (
    D003_SQL,
    RAW_EVIDENCE_SQL,
    RealEvaluationSession,
    RealSafetyAdapter,
    build_real_adapters,
)
from retrieval_v3.normalization import lexical_overlap_terms


def _plan_seq(policy_rows=100, filt=20, loops=1, chunk_rows=50):
    return [{
        "Plan": {
            "Node Type": "Nested Loop",
            "Actual Rows": 10, "Actual Loops": 1,
            "Plans": [
                {"Node Type": "Seq Scan", "Relation Name": "policy",
                 "Actual Rows": policy_rows, "Actual Loops": loops,
                 "Rows Removed by Filter": filt},
                {"Node Type": "Index Scan", "Relation Name": "policy_chunk",
                 "Actual Rows": chunk_rows, "Actual Loops": 1},
            ],
        }
    }]


def test_parser_loop_filter_recheck_math():
    # (100+20)*1 + 50 = 170
    assert count_base_scanned_rows(_plan_seq()) == 170
    # loops multiply: (100+20)*2 + 50 = 290
    assert count_base_scanned_rows(_plan_seq(loops=2)) == 290
    # recheck added
    plan = [{
        "Plan": {"Node Type": "Bitmap Heap Scan", "Relation Name": "policy",
                 "Actual Rows": 30, "Actual Loops": 2,
                 "Rows Removed by Filter": 5, "Rows Removed by Index Recheck": 3,
                 "Plans": [{"Node Type": "Bitmap Index Scan", "Index Name": "idx_policy_age",
                            "Actual Rows": 10, "Actual Loops": 2}]}
    }]
    # heap only: (30+5+3)*2=76; bitmap index child not double-counted
    assert count_base_scanned_rows(plan) == 76


def test_parser_ignores_cte_function_sort_join():
    plan = [{
        "Plan": {"Node Type": "Limit", "Actual Rows": 5, "Actual Loops": 1,
                 "Plans": [
                     {"Node Type": "Sort", "Actual Rows": 5, "Actual Loops": 1,
                      "Plans": [
                          {"Node Type": "CTE Scan", "CTE Name": "nearest",
                           "Actual Rows": 5, "Actual Loops": 1},
                          {"Node Type": "Seq Scan", "Relation Name": "policy",
                           "Actual Rows": 40, "Actual Loops": 1},
                      ]},
                     {"Node Type": "Function Scan", "Function Name": "unnest",
                      "Actual Rows": 10, "Actual Loops": 1},
                 ]}
    }]
    assert count_base_scanned_rows(plan) == 40


def test_parser_hold_on_unknown_missing_incomplete():
    # unknown scan node with target relation => HOLD
    bad = [{"Plan": {"Node Type": "Sample Scan", "Relation Name": "policy",
                     "Actual Rows": 10, "Actual Loops": 1}}]
    with pytest.raises(ValueError):
        count_base_scanned_rows(bad)
    # missing actuals => HOLD
    missing = [{"Plan": {"Node Type": "Seq Scan", "Relation Name": "policy",
                         "Actual Loops": 1}}]
    with pytest.raises(ValueError):
        count_base_scanned_rows(missing)
    missing2 = [{"Plan": {"Node Type": "Seq Scan", "Relation Name": "policy",
                          "Actual Rows": 10}}]
    with pytest.raises(ValueError):
        count_base_scanned_rows(missing2)
    # incomplete/empty => HOLD
    with pytest.raises(ValueError):
        count_base_scanned_rows([])
    with pytest.raises(ValueError):
        count_base_scanned_rows({})
    with pytest.raises(ValueError):
        count_base_scanned_rows([{"NoPlan": 1}])
    # Tid scans recognized (no HOLD)
    tid = [{"Plan": {"Node Type": "Tid Scan", "Relation Name": "policy",
                     "Actual Rows": 7, "Actual Loops": 1}}]
    assert count_base_scanned_rows(tid) == 7
    tidr = [{"Plan": {"Node Type": "Tid Range Scan", "Relation Name": "policy_chunk",
                      "Actual Rows": 9, "Actual Loops": 1}}]
    assert count_base_scanned_rows(tidr) == 9


def test_index_exactness_and_ratios():
    expected = {"idx_chunk_embedding", "idx_policy_age", "idx_policy_income",
                "idx_policy_region", "policy_chunk_pkey",
                "policy_chunk_policy_id_chunk_index_key", "policy_pkey",
                "policy_source_source_id_key"}
    assert set(FROZEN_BASELINE_INDEXES) == expected
    base = [(n, 100) for n in sorted(expected)]
    allr = list(base)
    info = compute_index_ratio(base, allr)
    assert info["baseline_bytes"] == 800
    assert info["aux_bytes"] == 0
    assert info["aux_indexes"] == []
    assert info["index_ratio"] == pytest.approx(1.0)
    # aux extra counted truthfully
    all2 = list(base) + [("idx_aux_candidate", 800)]
    info2 = compute_index_ratio(base, all2)
    assert info2["aux_bytes"] == 800
    assert info2["index_ratio"] == pytest.approx(2.0)
    # drift/missing/duplicate/zero => HOLD
    with pytest.raises(ValueError):
        compute_index_ratio([(n, 100) for n in sorted(expected)[:-1]], allr)
    with pytest.raises(ValueError):
        compute_index_ratio(base + [("idx_chunk_embedding", 100)], allr + [("idx_chunk_embedding", 100)])
    with pytest.raises(ValueError):
        compute_index_ratio([(n, 0) for n in sorted(expected)], [(n, 0) for n in sorted(expected)])
    drift = [(n if n != "idx_policy_age" else "idx_drift", 100) for n in sorted(expected)]
    with pytest.raises(ValueError):
        compute_index_ratio(drift, drift)
    # mismatch across queries => HOLD
    all_mismatch = [(n, 200 if n == "idx_policy_age" else 100) for n in sorted(expected)]
    with pytest.raises(ValueError):
        compute_index_ratio(base, all_mismatch)


def test_aggregate_max_ratio_and_completeness():
    per = [{"baseline_scan": 100, "candidate_scan": 200},
           {"baseline_scan": 100, "candidate_scan": 300}]
    agg = aggregate_task_ratios(per, 2)
    assert agg["rows_ratio"] == pytest.approx(3.0)
    assert agg["measured_count"] == 2 and agg["task_count"] == 2
    # missing task => HOLD
    with pytest.raises(ValueError):
        aggregate_task_ratios(per[:1], 2)
    # baseline<=0 => HOLD (DB=0 forbidden)
    with pytest.raises(ValueError):
        aggregate_task_ratios([{"baseline_scan": 0, "candidate_scan": 0}], 1)
    with pytest.raises(ValueError):
        aggregate_task_ratios([{"baseline_scan": -5, "candidate_scan": 10}], 1)


class _FakeCursor:
    def __init__(self, conn):
        self._conn = conn
        self._rows: list = []

    def execute(self, sql, params=None):
        self._conn.statements.append(str(sql))
        flat = " ".join(str(sql).split())
        if flat == "SHOW TimeZone":
            self._rows = [("GMT",)]
        elif flat == "SELECT CURRENT_DATE":
            self._rows = [("2026-09-03",)]
        elif flat.startswith(EXPLAIN_PREFIX):
            # dispatch by shadow identity
            if "DISTINCT ON" in flat:
                payload = self._conn.base_plan
            elif "MIN(c.embedding" in flat:
                payload = self._conn.dense_plan
            elif "COUNT(DISTINCT CASE" in flat:
                payload = self._conn.sparse_plan
            else:
                raise AssertionError("unexpected EXPLAIN body")
            self._rows = [(payload,)]
        elif "pg_relation_size" in flat and "IN ('idx_chunk" in flat:
            self._rows = list(self._conn.foot_base)
        elif "pg_relation_size" in flat and "indrelid IN" in flat:
            self._rows = list(self._conn.foot_all)
        elif "FROM policy p LEFT JOIN" in flat:
            self._rows = list(self._conn.corpus_rows)
        elif "SELECT p.source, p.source_id, p.raw" in flat:
            self._rows = list(self._conn.raw_rows)
        else:
            raise AssertionError(f"unexpected SQL: {flat[:120]}")

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)

    def close(self):
        pass


class _FakeConn:
    def __init__(self):
        self.statements: list = []
        self.set_session_calls: list = []
        self.closed = False
        self.corpus_rows: list = []
        self.raw_rows: list = []
        self.base_plan = _plan_seq(policy_rows=100, filt=0, chunk_rows=70)
        self.dense_plan = [{"Plan": {"Node Type": "Seq Scan", "Relation Name": "policy_chunk",
                                     "Actual Rows": 60, "Actual Loops": 1}}]
        # sparse single policy scan 30
        self.sparse_plan = [{"Plan": {"Node Type": "Seq Scan", "Relation Name": "policy",
                                      "Actual Rows": 30, "Actual Loops": 1}}]
        names = sorted(FROZEN_BASELINE_INDEXES)
        self.foot_base = [(n, 100) for n in names]
        self.foot_all = [(n, 100) for n in names]

    def set_session(self, readonly=None, autocommit=None, isolation_level=None):
        self.set_session_calls.append((readonly, autocommit, isolation_level))

    def cursor(self):
        return _FakeCursor(self)

    def close(self):
        self.closed = True


def _make_real_session(conn):
    seen = {"calls": 0}

    def connect(dsn):
        seen["calls"] += 1
        assert seen["calls"] == 1, "second DB connection opened"
        return conn

    sess = RealEvaluationSession(env={"DATABASE_URL": "postgres://mock"}, connect_fn=connect)
    sess.capture_executor("SHOW TimeZone")
    sess.capture_executor("SELECT CURRENT_DATE")
    return sess, seen


def test_no_second_connection_and_cached_footprint():
    conn = _FakeConn()
    sess, seen = _make_real_session(conn)
    qvec = [0.01] * 768
    # normalize-ish finite (probe only checks finite, not unit)
    out1 = sess.probe_task_cost("t1", qvec, ["alpha", "beta"], "2026-09-03", 0.0)
    assert out1["baseline_scan"] == 170  # 100+70
    assert out1["candidate_scan"] == 90  # 60+30
    # cached second call issues no new EXPLAIN
    n_before = len(conn.statements)
    out2 = sess.probe_task_cost("t1", qvec, ["alpha", "beta"], "2026-09-03", 0.0)
    assert out2 == out1
    assert len(conn.statements) == n_before
    # index bytes cached once (2 statements first time, 0 second)
    fp1 = sess.get_index_bytes()
    assert fp1["index_ratio"] == pytest.approx(1.0)
    m_before = len(conn.statements)
    fp2 = sess.get_index_bytes()
    assert fp2 == fp1
    assert len(conn.statements) == m_before
    assert seen["calls"] == 1
    # all statements on same conn, no SET
    for s in conn.statements:
        assert "SET TIME ZONE" not in s and "SET SESSION" not in s


def test_no_extra_model_call_reuse_qvec():
    # probe_task_cost never touches embedding_fn: pass raising loader, still works
    conn = _FakeConn()
    sess, _ = _make_real_session(conn)
    qvec = [0.02] * 768

    def _raising_embed(q):
        raise AssertionError("extra model call during cost probe")

    # runner wiring reuses cached qvec: simulate runner cache (first config qvec)
    cached = list(qvec)
    out = sess.probe_task_cost("t9", cached, ["gamma", "delta"], "2026-09-03", 0.015)
    assert out["baseline_scan"] > 0
    # raising embed never called by construction (no reference in probe path)
    import pathlib as _pl
    src = (_pl.Path(__file__).resolve().parent / "retrieval-v3" / "real_adapters.py").read_text(encoding="utf-8")
    seg = src[src.index("def probe_task_cost"):src.index("def probe_task_cost") + 3000]
    assert "embedding_fn" not in seg and "encode" not in seg


def _safety_task(tid, stratum="natural_needs"):
    return {"task_id": tid, "stratum": stratum, "safe_action": "ANSWER",
            "retrieved": [{"source": "youth", "source_id": "p0"}],
            "retrieved_internal": [{"source": "youth", "source_id": "p0"}]}


class _StubSession:
    """Minimal adapter session: corpus lookups + pre-populated cost caches (no DB)."""

    def __init__(self, probe_map, foot):
        self._policies = [{"source": "youth", "source_id": "p0"}]
        self._cost_probe_cache = dict(probe_map)
        self._foot = dict(foot)
        self._pinned = {"db_session_timezone": "GMT", "evaluation_as_of_date": "2026-09-03"}

    @property
    def pinned_context(self):
        return dict(self._pinned)

    @property
    def rows_scanned(self):
        return 1

    @property
    def d003_queries(self):
        return 1

    @property
    def biz_end_lookup(self):
        return {("youth", "p0"): None}

    @property
    def official_url_lookup(self):
        return {("youth", "p0"): "https://apply.example/x"}

    def get_index_bytes(self):
        if isinstance(self._foot, Exception):
            raise self._foot
        return dict(self._foot)


def _raw_lookup_ok(source, source_id):
    if (source, source_id) == ("youth", "p0"):
        return {"aplyUrlAddr": "https://apply.example/x", "refUrlAddr1": ""}
    return None


def test_cost_pass_no_go_hold_matrix():
    foot = {"baseline_bytes": 800, "aux_bytes": 0, "aux_indexes": [],
            "candidate_bytes": 800, "index_ratio": 1.0}
    # max 3.0 PASS
    sess = _StubSession({"t1": {"baseline_scan": 100, "candidate_scan": 300}}, foot)
    ad = RealSafetyAdapter(sess, http_transport=lambda u, m, t: None,
                           raw_lookup=_raw_lookup_ok)
    # official/link needs valid denominator; use single youth URL with PASS
    # (raw matches table) but http HOLD (transport returns None->False? adapter
    # catches exception->False, successes 0 <1 => NO-GO). To isolate cost, check
    # cost subdict only (overall http may be NO-GO, cost PASS still asserted).
    payload = {"config_id": "candidate-a-01",
               "results": {"task_results": [_safety_task("t1")]},
               "config": {}}
    # stub http to PASS: return True via mock transport object? adapter expects
    # TransportOutcome via check_url_with_transport; inject transport returning success
    from retrieval_v3.real_adapters import TransportOutcome
    sess2 = _StubSession({"t1": {"baseline_scan": 100, "candidate_scan": 300}}, foot)
    ad2 = RealSafetyAdapter(sess2, http_transport=lambda u, m, t: TransportOutcome(status=200),
                            raw_lookup=_raw_lookup_ok)
    ev = ad2(payload)
    assert ev["cost"]["gate"] == "PASS"
    assert ev["cost"]["index_ratio"] == pytest.approx(1.0)
    assert ev["cost"]["rows_ratio"] == pytest.approx(3.0)
    assert ev["cost"]["extra_model_calls"] == 0
    assert ev["cost"]["task_count"] == 1 and ev["cost"]["measured_count"] == 1
    assert "index_ratio" in ev["cost"] and "rows_ratio" in ev["cost"]
    # >3 NO-GO
    sess3 = _StubSession({"t1": {"baseline_scan": 100, "candidate_scan": 301}}, foot)
    ad3 = RealSafetyAdapter(sess3, http_transport=lambda u, m, t: TransportOutcome(status=200),
                            raw_lookup=_raw_lookup_ok)
    ev3 = ad3(payload)
    assert ev3["cost"]["gate"] == "NO-GO"
    assert ev3["cost"]["rows_ratio"] == pytest.approx(3.01)
    # missing task => HOLD with no ratios
    sess4 = _StubSession({}, foot)
    ad4 = RealSafetyAdapter(sess4, http_transport=lambda u, m, t: TransportOutcome(status=200),
                            raw_lookup=_raw_lookup_ok)
    ev4 = ad4(payload)
    assert ev4["cost"]["gate"] == "HOLD"
    assert "index_ratio" not in ev4["cost"] and "rows_ratio" not in ev4["cost"]
    assert ev4["cost"]["extra_model_calls"] == 0
    # index>2 => NO-GO
    foot_bad = dict(foot, index_ratio=2.5, candidate_bytes=2000, aux_bytes=1200,
                    aux_indexes=["idx_aux_candidate"])
    sess5 = _StubSession({"t1": {"baseline_scan": 100, "candidate_scan": 100}}, foot_bad)
    ad5 = RealSafetyAdapter(sess5, http_transport=lambda u, m, t: TransportOutcome(status=200),
                            raw_lookup=_raw_lookup_ok)
    ev5 = ad5(payload)
    assert ev5["cost"]["gate"] == "NO-GO"


def test_lexical_equivalence_explicit():
    terms = lexical_overlap_terms("synthetic alpha beta gamma 123 test")
    assert terms == assert_lexical_terms_safe(terms)
    for t in terms:
        assert len(t) >= 2 and "%" not in t and "_" not in t and "\\" not in t
    # case behavior for alphabet: casefold substring == lower substring (ASCII+Han)
    from retrieval_v3.sparse import _count_distinct_terms_in_field
    field = "Synthetic ALPHA beta GAMMA"
    assert _count_distinct_terms_in_field(["synthetic", "alpha"], field) == 2
    # ILIKE simulation via casefold matches lower for this alphabet
    assert "alpha".casefold() in field.casefold()
    assert "ALPHA".lower() in field.lower()


def test_config_independence_weights_only_order():
    # weights appear only in SELECT/ORDER, never in FROM/WHERE/JOIN/GROUP
    where_part = CANDIDATE_SPARSE_SHADOW_SQL.split("WHERE")[1].split("GROUP BY")[0]
    assert "fw_title" not in where_part and "fw_support" not in where_part and "fw_elig" not in where_part
    from_join = CANDIDATE_SPARSE_SHADOW_SQL.split("WHERE")[0]
    assert "fw_title" not in from_join
    assert "fw_title" in CANDIDATE_SPARSE_SHADOW_SQL.split("ORDER BY")[1]
    assert "fw_" not in CANDIDATE_DENSE_SHADOW_SQL
    # fusion/MMR post-DB: no DB imports in fusion/dedup
    import pathlib as _pl
    repo = _pl.Path(__file__).resolve().parents[1]
    fusion_src = (repo / "eval" / "retrieval-v3" / "fusion.py").read_text(encoding="utf-8")
    assert "execute_readonly" not in fusion_src and "EXPLAIN" not in fusion_src
    dedup_src = (repo / "eval" / "retrieval-v3" / "dedup.py").read_text(encoding="utf-8")
    assert "execute_readonly" not in dedup_src


def test_probe_placement_outside_timed_samples_and_ranking_unchanged():
    import pathlib as _pl
    repo = _pl.Path(__file__).resolve().parents[1]
    src = (repo / "eval" / "retrieval-v3" / "runner.py").read_text(encoding="utf-8")
    assert "_cost_qvec_cache" in src and "probe_task_cost" in src
    # probe call site precedes latency execution call (outside timed closures)
    assert src.index("probe_task_cost") < src.index("measure_paired_latency(task_ids_sorted")
    seg = src[src.index("def _baseline_fn"):src.index("measure_paired_latency(task_ids_sorted")]
    assert "probe_task_cost" not in seg and "EXPLAIN" not in seg
    # ranking unchanged: same retrieval before/after probes (pure pools)
    from retrieval_v3.runner import Runner
    from retrieval_v3.candidate_registry import load_and_validate
    plan = load_and_validate()
    cfg = plan["configs"][0]
    vec = [1.0] + [0.0] * 767
    pols = [
        {"id": 1, "source": "youth", "source_id": "A", "title": "alpha beta",
         "support_content": "", "summary": "", "keywords": "", "add_qualify": "",
         "income_etc": "", "apply_method": "", "org": "o",
         "chunks": [{"embedding": vec, "chunk_index": 0, "id": 1}]},
        {"id": 2, "source": "gov24", "source_id": "B", "title": "gamma delta",
         "support_content": "", "summary": "", "keywords": "", "add_qualify": "",
         "income_etc": "", "apply_method": "", "org": "o",
         "chunks": [{"embedding": [0.0] * 768, "chunk_index": 0, "id": 2}]},
    ]
    pols[1]["chunks"][0]["embedding"][0] = 0.0
    r = Runner(candidate_plan=plan, embedding_fn=lambda q: vec)
    a = r._retrieve_for_query("alpha beta", pols, cfg, qvec=vec)
    b = r._retrieve_for_query("alpha beta", pols, cfg, qvec=vec)
    assert [e["source_id"] for e in a["final_top30"]] == [e["source_id"] for e in b["final_top30"]]


def test_d057_d060_unchanged_and_mirrors_identical():
    import pathlib as _pl
    repo = _pl.Path(__file__).resolve().parents[1]
    # D003 frozen tokens intact
    assert "DISTINCT ON" in D003_SQL and "LIMIT %(n)s" in D003_SQL and "%(as_of)s" in D003_SQL
    assert "RAW_EVIDENCE_SQL" in (repo / "eval" / "retrieval-v3" / "real_adapters.py").read_text(encoding="utf-8")
    assert RAW_EVIDENCE_SQL.strip().startswith("SELECT p.source")
    # prereg-exact HTTP constants intact
    from retrieval_v3 import safety as _safety
    assert (_safety.CONNECT_TIMEOUT_S, _safety.READ_TIMEOUT_S) == (5, 10)
    # mirrors byte-identical for touched runtime files
    for name in ("real_adapters.py", "runner.py", "cost.py"):
        h1 = hashlib.sha256((repo / "eval" / "retrieval-v3" / name).read_bytes()).hexdigest()
        h2 = hashlib.sha256((repo / "eval" / "retrieval_v3" / name).read_bytes()).hexdigest()
        assert h1 == h2, name
    # frozen bytes untouched (prereg/plan/safe/prod-excl/link-v2)
    assert hashlib.sha256((repo / "docs" / "RETRIEVAL_V3_PREREG.md").read_bytes()).hexdigest() == "7842018613d66aa4570f4db2f8ae5a698ceb46757995a6b7e26873177b36160e"
    assert hashlib.sha256((repo / "eval" / "retrieval-v3" / "candidate-plan" / "candidate-plan-v4.json").read_bytes()).hexdigest() == "a25d9c482094696ff7a438593979813ac568c91a977a2543a50618ca4f5177d6"
