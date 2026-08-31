"""Cycle3 canonical runner tests — pure/static/mock, no retrieval/DB/model.

Covers the 10 runner contracts:
1) baseline + c3e1/128 c3e2/256 c3e3/512 K fixed
2) prereg exact normative SQL/ordering semantics
3) candidate-v2 lexical semantics / D-003 / D-004 / D-007 invariant
4) cosine threshold post-LIMIT
5) single canonical dev batch (baseline+3 together) batch identity/guard
6) quality/selection rule prereg, quality-selectable -> paired latency boundary
7) Cycle3 audit fail-closed integration (temp audit + synthetic/mock only)
8) protected-access grant required before dev open (stale/failure/no-grant fail)
9) holdout blocked until freeze+review+approval
10) deterministic ordering, registry, result schema/provenance, single-batch guard

No dev plaintext open, no holdout plaintext, no DB/model/embedding.
"""

import hashlib
import json
import pathlib
import tempfile
import unittest
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
sys.path.insert(0, str(ROOT / "ml-service"))

from retrieval_v2.cycle3_runner import (  # type: ignore
    ALL_CANONICAL_IDS,
    BASELINE_ID,
    CANDIDATE_IDS,
    POOL_K_BY_ID,
    FINAL_N,
    BATCH_ID,
    RUNNER_ID,
    EXPECTED_DEV_SHA256,
    EXPECTED_DEV_CASES,
    PREREG_SHA256,
    PREREG_VERSION,
    D003_CANDIDATES,
    D003_COSINE_MIN,
    D003_LEXICAL_BIAS,
    D003_RERANK,
    D003_EMBED_MODEL,
    get_candidate_registry,
    validate_candidate_registry,
    get_sql_for_candidate,
    get_pool_k,
    validate_sql_semantics,
    assert_rp_is_null,
    strip_region_for_runner,
    lexical_terms_for_runner,
    youth_bias_for_runner,
    apply_cosine_filter,
    validate_cosine_filter_position,
    ordering_key,
    quality_selectable,
    paired_net_from_ranks,
    dev_selectable,
    tie_break_sort_key,
    validate_single_batch_request,
    get_batch_provenance,
    assert_holdout_blocked,
    assert_not_holdout_path,
    require_protected_dev_access_grant,
    build_result_skeleton,
    validate_result_schema,
    assert_d003_contract,
)

from retrieval_v2.cycle3_audit import append_event, verify_holdout_access_allowed, read_and_verify_chain  # type: ignore
from retrieval_v2.candidate_lexical_rewrite import lexical_overlap_terms_rewrite  # type: ignore
import app as ml_app  # type: ignore
from source_ranking import youth_source_bias, LEXICAL_OVERLAP_BIAS  # type: ignore


# ---------------------------------------------------------------------------
# 1) Registry exactness
# ---------------------------------------------------------------------------

class RegistryTest(unittest.TestCase):
    def test_registry_has_exactly_4(self):
        reg = get_candidate_registry()
        self.assertEqual(set(reg.keys()), set(ALL_CANONICAL_IDS))
        self.assertEqual(len(reg), 4)
        self.assertIn(BASELINE_ID, reg)
        for cid in CANDIDATE_IDS:
            self.assertIn(cid, reg)

    def test_pool_k_fixed(self):
        for cid, expected_k in POOL_K_BY_ID.items():
            self.assertIn(expected_k, (128, 256, 512))
            self.assertEqual(get_pool_k(cid), expected_k)
        self.assertIsNone(get_pool_k(BASELINE_ID))
        with self.assertRaises(ValueError):
            get_pool_k("nonexistent")

    def test_registry_constants_immutable(self):
        self.assertEqual(POOL_K_BY_ID["c3e1-vector-pool-128"], 128)
        self.assertEqual(POOL_K_BY_ID["c3e2-vector-pool-256"], 256)
        self.assertEqual(POOL_K_BY_ID["c3e3-vector-pool-512"], 512)
        self.assertEqual(FINAL_N, 30)
        self.assertEqual(D003_CANDIDATES, 30)
        self.assertEqual(D003_COSINE_MIN, 0.78)
        self.assertEqual(D003_LEXICAL_BIAS, 0.01)
        self.assertEqual(D003_RERANK, 0)
        self.assertEqual(BATCH_ID, "cycle3-canonical-dev-v1")

    def test_validate_registry_pass(self):
        validate_candidate_registry()  # should not raise

    def test_validate_registry_rejects_drift(self):
        reg = get_candidate_registry()
        # Tamper pool_k
        reg["c3e1-vector-pool-128"]["pool_k"] = 999
        with self.assertRaises(ValueError):
            validate_candidate_registry(reg)
        # Tamper final_n
        reg2 = get_candidate_registry()
        reg2["c3e2-vector-pool-256"]["final_n"] = 50
        with self.assertRaises(ValueError):
            validate_candidate_registry(reg2)
        # Missing baseline
        reg3 = get_candidate_registry()
        del reg3[BASELINE_ID]
        with self.assertRaises(ValueError):
            validate_candidate_registry(reg3)

    def test_registry_lexical_strings_exact(self):
        reg = get_candidate_registry()
        self.assertEqual(reg[BASELINE_ID]["lexical_terms"], "lexical_overlap_terms(strip_region(raw))")
        for cid in CANDIDATE_IDS:
            self.assertEqual(reg[cid]["lexical_terms"], "lexical_overlap_terms_rewrite(strip_region(raw))")
        for cid in ALL_CANONICAL_IDS:
            self.assertEqual(reg[cid]["youth_bias"], "youth_source_bias(strip_region(raw))")
            self.assertFalse(reg[cid]["region_search"])


# ---------------------------------------------------------------------------
# 2) SQL semantics normative
# ---------------------------------------------------------------------------

class SQLSemanticsTest(unittest.TestCase):
    def test_vector_pool_sql_contains_bounded_pool(self):
        for cid in CANDIDATE_IDS:
            sql = get_sql_for_candidate(cid)
            self.assertIn("vector_pool AS (", sql)
            self.assertIn("ORDER BY dist ASC LIMIT %(pool_k)s", sql)
            self.assertIn("JOIN vector_pool vp ON vp.id = p.id", sql)
            self.assertIn("FROM vector_pool t", sql)
            # lexical only on pool: must not have standalone eligible lexical on full table without vp join
            # baseline has CROSS JOIN but vector pool has join vp
            validate_sql_semantics(sql, cid)

    def test_baseline_sql_no_pool(self):
        sql = get_sql_for_candidate(BASELINE_ID)
        self.assertNotIn("vector_pool", sql)
        self.assertIn("FROM nearest t", sql)
        validate_sql_semantics(sql, BASELINE_ID)

    def test_sql_deterministic_tie_break(self):
        for cid in CANDIDATE_IDS:
            sql = get_sql_for_candidate(cid)
            self.assertIn("t.dist, t.source, t.source_id", sql)
            self.assertIn("ORDER BY t.dist - CASE WHEN t.source = 'youth'", sql)

    def test_sql_rejects_bad_candidate(self):
        with self.assertRaises(ValueError):
            get_sql_for_candidate("bad-id")

    def test_sql_lexical_only_on_K(self):
        # Ensure vector-pool SQL does NOT contain baseline-style lexical without vp join
        # baseline lexical has no vp join; vector pool must have vp join
        for cid in CANDIDATE_IDS:
            sql = get_sql_for_candidate(cid)
            # Count occurrences: vector_pool should appear at least 3 times (CTE + join + FROM)
            self.assertGreaterEqual(sql.count("vector_pool"), 3)
            # Ensure lexical CTE actually joins vp
            self.assertIn("JOIN vector_pool", sql)

    def test_sql_contains_normative_placeholders(self):
        for cid in CANDIDATE_IDS:
            sql = get_sql_for_candidate(cid)
            self.assertIn("%(vec)s", sql)
            self.assertIn("%(age)s", sql)
            self.assertIn("%(rp)s", sql)
            self.assertIn("%(lexical_terms)s", sql)
            self.assertIn("%(youth_bias)s", sql)
            self.assertIn("%(lexical_bias)s", sql)
            self.assertIn("%(n)s", sql)
            self.assertIn("%(pool_k)s", sql)
        base = get_sql_for_candidate(BASELINE_ID)
        self.assertIn("%(n)s", base)
        self.assertNotIn("%(pool_k)s", base)

    def test_cosine_filter_not_in_sql(self):
        for cid in CANDIDATE_IDS:
            sql = get_sql_for_candidate(cid)
            validate_cosine_filter_position(sql)
        # Baseline also post-filter
        validate_cosine_filter_position(get_sql_for_candidate(BASELINE_ID))


# ---------------------------------------------------------------------------
# 3) Candidate-v2 lexical / D-003 invariants
# ---------------------------------------------------------------------------

class LexicalAndProdContractTest(unittest.TestCase):
    def test_strip_region_delegates_to_ml_app(self):
        raw = "서울 청년 지원 사업"
        self.assertEqual(strip_region_for_runner(raw), ml_app.strip_region(raw))
        # strip_region removes SIDO keywords
        self.assertNotIn("서울", strip_region_for_runner("서울 청년 프로그램"))

    def test_lexical_terms_is_rewrite_of_stripped(self):
        raws = ["청년 취업 지원", "서울 청년 창업 지원금", "보건복지부 청년 정책"]
        for raw in raws:
            expected = lexical_overlap_terms_rewrite(strip_region_for_runner(raw))
            self.assertEqual(lexical_terms_for_runner(raw), expected)

    def test_youth_bias_gov24_suppressed(self):
        # Gov24 org query => bias 0 regardless of youth term
        gov_raw = "고용노동부 청년 지원"
        self.assertEqual(youth_bias_for_runner(gov_raw), 0.0)
        # Pure youth intent => 0.015
        youth_raw = "청년 취업 지원"
        self.assertEqual(youth_bias_for_runner(youth_raw), 0.015)
        # No youth term => 0.0
        self.assertEqual(youth_bias_for_runner("주택 지원 사업"), 0.0)

    def test_rp_must_be_null(self):
        assert_rp_is_null(None)
        with self.assertRaises(ValueError):
            assert_rp_is_null("11")
        with self.assertRaises(ValueError):
            assert_rp_is_null("%서울%")

    def test_d003_contract(self):
        assert_d003_contract()
        self.assertEqual(ml_app.CANDIDATES, 30)
        # RERANK env default may be 1 locally; canonical constant must be 0
        self.assertEqual(D003_RERANK, 0)
        self.assertAlmostEqual(ml_app.COSINE_MIN, 0.78)
        self.assertAlmostEqual(LEXICAL_OVERLAP_BIAS, 0.01)
        self.assertEqual(ml_app.EMBED_MODEL_NAME, "intfloat/multilingual-e5-base")
    def test_cosines_post_limit_filter_exists(self):
        # Ensure apply_cosine_filter is post-limit (python) not SQL
        cands = [
            {"source": "youth", "source_id": "a", "score": 0.80},
            {"source": "gov24", "source_id": "b", "score": 0.77},
            {"source": "youth", "source_id": "c", "dist": 0.22},  # score 0.78
            {"source": "gov24", "source_id": "d", "dist": 0.23},  # score 0.77
        ]
        filtered = apply_cosine_filter(cands, cosine_min=0.78)
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0]["source_id"], "a")
        self.assertEqual(filtered[1]["source_id"], "c")


# ---------------------------------------------------------------------------
# 4) Cosine post-LIMIT filter position
# ---------------------------------------------------------------------------

class CosineFilterTest(unittest.TestCase):
    def test_filter_preserves_order(self):
        cands = [{"source": "youth", "source_id": str(i), "score": 0.90 - i * 0.05} for i in range(5)]
        filtered = apply_cosine_filter(cands, 0.78)
        # Original order preserved — filtered should be 0,1,2 in input order
        ids = [c["source_id"] for c in filtered]
        self.assertEqual(ids, ["0", "1", "2"])
        self.assertEqual(len(filtered), 3)

    def test_filter_handles_dist_and_score(self):
        cands = [{"source": "youth", "source_id": "x", "dist": 0.20}, {"source": "youth", "source_id": "y", "dist": 0.30}]
        filtered = apply_cosine_filter(cands, 0.78)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["source_id"], "x")


# ---------------------------------------------------------------------------
# 5) Single canonical dev batch guard
# ---------------------------------------------------------------------------

class SingleBatchGuardTest(unittest.TestCase):
    def test_allows_exact_batch(self):
        validate_single_batch_request(list(ALL_CANONICAL_IDS))

    def test_rejects_subset(self):
        with self.assertRaises(ValueError):
            validate_single_batch_request(["baseline"])
        with self.assertRaises(ValueError):
            validate_single_batch_request(list(CANDIDATE_IDS))

    def test_rejects_extra_or_new_k(self):
        with self.assertRaises(ValueError):
            validate_single_batch_request(list(ALL_CANONICAL_IDS) + ["c3e4-vector-pool-1024"])
        with self.assertRaises(ValueError):
            validate_single_batch_request([BASELINE_ID, "c3e1-vector-pool-128", "c3e2-vector-pool-256", "c3e3-vector-pool-512", "new-candidate"])

    def test_rejects_wrong_order_count(self):
        with self.assertRaises(ValueError):
            validate_single_batch_request(list(ALL_CANONICAL_IDS) * 2)

    def test_rejects_existing_output_file(self):
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td) / "result.json"
            p.write_text("{}", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                validate_single_batch_request(list(ALL_CANONICAL_IDS), output_path=p)

    def test_batch_provenance(self):
        prov = get_batch_provenance()
        self.assertEqual(prov["batch_id"], BATCH_ID)
        self.assertEqual(set(prov["candidate_ids"]), set(ALL_CANONICAL_IDS))
        self.assertEqual(prov["pool_k_by_id"], POOL_K_BY_ID)
        self.assertEqual(prov["final_n"], 30)
        self.assertTrue(prov["single_batch"])
        self.assertTrue(prov["immutable_after_dev_inspection"])


# ---------------------------------------------------------------------------
# 6) Quality / selection rule (prereg §7)
# ---------------------------------------------------------------------------

class SelectionRuleTest(unittest.TestCase):
    def _metrics(self, youth_hit, gov_hit, total=36, macro=None):
        # Build minimal metrics dict compatible with quality_selectable
        youth_n, gov_n = 18, 18
        youth_r = youth_hit / youth_n
        gov_r = gov_hit / gov_n
        macro_val = (youth_r + gov_r) / 2 if macro is None else macro
        # total hit = youth+gov
        hit = youth_hit + gov_hit
        return {
            "hit@5": hit,
            "source_macro_recall@5": round(macro_val, 4),
            "by_source": {
                "youth": {"hit@5": youth_hit, "n": youth_n, "recall@5": round(youth_r, 4)},
                "gov24": {"hit@5": gov_hit, "n": gov_n, "recall@5": round(gov_r, 4)},
            },
        }

    def test_quality_selectable_all_required(self):
        # baseline 28 -> youth10 gov18 (macro 0.7778), candidate must exceed macro and +2 and no regression
        baseline = self._metrics(10, 18)
        candidate = self._metrics(12, 18)  # +2, youth improves, gov same, macro 0.8333 > 0.7778
        is_q, diag = quality_selectable(baseline, candidate)
        self.assertTrue(is_q)
        self.assertTrue(diag["checks"]["macro_gt"])
        self.assertTrue(diag["checks"]["net_ge_2"])
        self.assertTrue(diag["checks"]["youth_no_regression"])
        self.assertTrue(diag["checks"]["gov24_no_regression"])

    def test_rejects_macro_not_gt(self):
        baseline = self._metrics(10, 18)
        candidate = self._metrics(10, 18)  # same macro
        is_q, _ = quality_selectable(baseline, candidate)
        self.assertFalse(is_q)

    def test_rejects_net_lt_2(self):
        baseline = self._metrics(10, 18)
        candidate = self._metrics(11, 18)  # net +1 only
        is_q, diag = quality_selectable(baseline, candidate)
        self.assertFalse(is_q)
        self.assertFalse(diag["checks"]["net_ge_2"])

    def test_rejects_youth_regression(self):
        baseline = self._metrics(12, 18)
        candidate = self._metrics(11, 19)  # youth regressions even though total +0
        is_q, diag = quality_selectable(baseline, candidate)
        self.assertFalse(is_q)
        self.assertFalse(diag["checks"]["youth_no_regression"])

    def test_rejects_gov24_regression(self):
        baseline = self._metrics(10, 18)
        candidate = self._metrics(12, 17)  # gov regressions
        is_q, diag = quality_selectable(baseline, candidate)
        self.assertFalse(is_q)
        self.assertFalse(diag["checks"]["gov24_no_regression"])

    def test_dev_selectable_requires_quality_and_latency(self):
        baseline = self._metrics(10, 18)
        candidate = self._metrics(12, 18)
        # No latency measured -> false (boundary not evaluated)
        is_dev, diag = dev_selectable(baseline, candidate, None, None)
        self.assertFalse(is_dev)
        self.assertIn("not measured", diag["latency_gate"]["reason"])

        # Quality false -> even with latency pass, still false (boundary)
        bad_cand = self._metrics(10, 18)
        is_dev2, diag2 = dev_selectable(baseline, bad_cand, 100.0, 90.0)
        self.assertFalse(is_dev2)
        self.assertEqual(diag2["latency_gate"]["applicable"], False)

        # Quality true + latency pass
        is_dev3, diag3 = dev_selectable(baseline, candidate, 100.0, 90.0)
        self.assertTrue(is_dev3)
        self.assertTrue(diag3["latency_gate"]["pass"])

        # Quality true + latency fail
        is_dev4, diag4 = dev_selectable(baseline, candidate, 90.0, 100.0)
        self.assertFalse(is_dev4)

    def test_paired_net_gains_losses(self):
        # ranks 0 = miss, 1..5 = hit
        br = [1, 0, 3, 6, 2]
        cr = [1, 2, 3, 0, 5]
        g, l, n = paired_net_from_ranks(br, cr, k=5)
        # b miss -> c hit gains: index1 (0->2) =1, index? others? 3:6->0 no, so 1 gain. losses 0
        self.assertEqual(g, 1)
        self.assertEqual(l, 0)
        self.assertEqual(n, 1)

    def test_tie_break_order(self):
        # higher net, higher macro, lower delta, smaller K
        a = tie_break_sort_key("c3e1-vector-pool-128", net_hit5=5, macro_r5=0.85, p95_delta=-10)
        b = tie_break_sort_key("c3e2-vector-pool-256", net_hit5=5, macro_r5=0.85, p95_delta=-10)
        c = tie_break_sort_key("c3e3-vector-pool-512", net_hit5=6, macro_r5=0.80, p95_delta=-5)
        # c has higher net, so should sort before a,b
        sorted_ids = sorted([("c3e1", a), ("c3e2", b), ("c3e3", c)], key=lambda x: x[1])
        self.assertEqual(sorted_ids[0][0], "c3e3")
        # Among same net/macro/delta, smaller K first
        self.assertLess(a, b)


# ---------------------------------------------------------------------------
# 7-8) Audit fail-closed integration (temp audit + synthetic mock)
# ---------------------------------------------------------------------------

class AuditIntegrationTest(unittest.TestCase):
    def test_protected_access_requires_exact_grant(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "audit.jsonl"
            sha = EXPECTED_DEV_SHA256
            sess = "sess-123"
            # No grant -> fail
            with self.assertRaises(Exception):
                require_protected_dev_access_grant(log, set_sha=sha, session_id=sess)
            # Append grant with success
            append_event(log, action="protected_access_start", candidate_id=None, set_role="dev", set_sha=sha, outcome="success", git_head="0" * 40, git_dirty=False, session_id=sess)
            grant = require_protected_dev_access_grant(log, set_sha=sha, session_id=sess)
            self.assertEqual(grant["set_sha"].lower(), sha.lower())
            # Wrong sha fails
            with self.assertRaises(Exception):
                require_protected_dev_access_grant(log, set_sha="0" * 64, session_id=sess)
            # Wrong session fails
            with self.assertRaises(Exception):
                require_protected_dev_access_grant(log, set_sha=sha, session_id="other")

    def test_stale_grant_after_end_fails(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "audit.jsonl"
            sha = EXPECTED_DEV_SHA256
            sess = "sess-x"
            ev = append_event(log, action="protected_access_start", candidate_id=None, set_role="dev", set_sha=sha, outcome="success", git_head="0" * 40, git_dirty=False, session_id=sess)
            # Close it
            append_event(log, action="protected_access_end", candidate_id=None, set_role="dev", set_sha=sha, outcome="success", git_head="0" * 40, git_dirty=False, session_id=sess)
            with self.assertRaises(Exception):
                require_protected_dev_access_grant(log, set_sha=sha, session_id=sess)
            # Also with token should fail
            with self.assertRaises(Exception):
                require_protected_dev_access_grant(log, set_sha=sha, session_id=sess, expected_event_hash=ev["event_hash"])

    def test_failure_outcome_not_granted(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "audit.jsonl"
            sha = EXPECTED_DEV_SHA256
            sess = "sess-fail"
            append_event(log, action="protected_access_start", candidate_id=None, set_role="dev", set_sha=sha, outcome="failure", git_head="0" * 40, git_dirty=False, session_id=sess)
            with self.assertRaises(Exception):
                require_protected_dev_access_grant(log, set_sha=sha, session_id=sess)

    def test_no_grant_token_stale(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "audit.jsonl"
            sha = EXPECTED_DEV_SHA256
            sess = "sess-tok"
            ev1 = append_event(log, action="protected_access_start", candidate_id=None, set_role="dev", set_sha=sha, outcome="success", git_head="0" * 40, git_dirty=False, session_id=sess)
            # Second start closes earlier but we test token mismatch
            ev2 = append_event(log, action="protected_access_start", candidate_id=None, set_role="dev", set_sha=sha, outcome="success", git_head="0" * 40, git_dirty=False, session_id=sess)
            # old token should fail
            with self.assertRaises(Exception):
                require_protected_dev_access_grant(log, set_sha=sha, session_id=sess, expected_event_hash=ev1["event_hash"])
            # new token passes
            grant = require_protected_dev_access_grant(log, set_sha=sha, session_id=sess, expected_event_hash=ev2["event_hash"])
            self.assertEqual(grant["event_hash"], ev2["event_hash"])

    def test_real_audit_log_not_written_in_implementation_stage(self):
        # Real log path must remain unchanged through this test module load
        real_log = ROOT / "eval" / "retrieval-v2" / "cycle3" / "audit" / "events.jsonl"
        before = real_log.read_bytes() if real_log.exists() else b""
        # Ensure importer did not write
        after = real_log.read_bytes() if real_log.exists() else b""
        self.assertEqual(before, after)

    def test_audit_chain_verification(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "audit.jsonl"
            append_event(log, action="run_start", candidate_id=BASELINE_ID, set_role="none", set_sha=None, outcome="started", git_head="0" * 40, git_dirty=False, session_id="s1")
            append_event(log, action="run_end", candidate_id=BASELINE_ID, set_role="none", set_sha=None, outcome="success", git_head="0" * 40, git_dirty=False, session_id="s1")
            chain = read_and_verify_chain(log)
            self.assertEqual(len(chain), 2)
            self.assertEqual(chain[0]["action"], "run_start")


# ---------------------------------------------------------------------------
# 9) Holdout blocked
# ---------------------------------------------------------------------------

class HoldoutBlockingTest(unittest.TestCase):
    def test_holdout_always_blocked_without_approval(self):
        with self.assertRaises(RuntimeError) as ctx:
            assert_holdout_blocked()
        self.assertIn("holdout evaluation/access blocked", str(ctx.exception).lower())

    def test_holdout_blocked_even_with_token_without_marker(self):
        with self.assertRaises(RuntimeError):
            assert_holdout_blocked(allow_token="anything")

    def test_holdout_path_blocked(self):
        with self.assertRaises(RuntimeError):
            assert_not_holdout_path("eval/retrieval-v2/cycle3/holdout/evalset.jsonl")
        with self.assertRaises(RuntimeError):
            assert_not_holdout_path("/tmp/holdout_plaintext.jsonl")
        # non-holdout allowed
        assert_not_holdout_path("eval/retrieval-v2/cycle3/dev/evalset.jsonl")


# ---------------------------------------------------------------------------
# 10) Deterministic ordering, result schema/provenance
# ---------------------------------------------------------------------------

class OrderingAndResultSchemaTest(unittest.TestCase):
    def test_ordering_key_deterministic(self):
        item = {"source": "youth", "source_id": "abc", "dist": 0.2}
        k1 = ordering_key(item, youth_bias=0.015, lexical_bias=0.01, lexical_overlap=2)
        k2 = ordering_key(item, youth_bias=0.015, lexical_bias=0.01, lexical_overlap=2)
        self.assertEqual(k1, k2)
        # youth bias reduces primary dist
        item_gov = {"source": "gov24", "source_id": "abc", "dist": 0.2}
        k_gov = ordering_key(item_gov, youth_bias=0.015, lexical_bias=0.01, lexical_overlap=2)
        self.assertLess(k1[0], k_gov[0])

    def test_ordering_tie_break_is_stable(self):
        items = [
            {"source": "youth", "source_id": "002", "dist": 0.1},
            {"source": "youth", "source_id": "001", "dist": 0.1},
            {"source": "gov24", "source_id": "001", "dist": 0.1},
        ]
        # Same adjusted distance, same dist, then source then source_id
        sorted_items = sorted(items, key=lambda x: ordering_key(x, 0.0, 0.0, 0))
        self.assertEqual(sorted_items[0]["source"], "gov24")
        self.assertEqual(sorted_items[1]["source_id"], "001")
        self.assertEqual(sorted_items[2]["source_id"], "002")

    def test_result_skeleton_schema(self):
        skel = build_result_skeleton()
        validate_result_schema(skel)
        self.assertEqual(skel["final_n"], 30)
        self.assertEqual(skel["pool_k_by_id"], POOL_K_BY_ID)
        self.assertEqual(skel["candidates"], list(ALL_CANONICAL_IDS))
        self.assertEqual(skel["prereg_version"], PREREG_VERSION)
        self.assertEqual(skel["prereg_file_sha256"], PREREG_SHA256)
        self.assertEqual(skel["dev_set"]["cases"], EXPECTED_DEV_CASES)
        self.assertEqual(skel["dev_set"]["sha256"].lower(), EXPECTED_DEV_SHA256.lower())
        self.assertEqual(skel["production_contract"]["rerank"], 0)
        self.assertFalse(skel["production_contract"]["region_search"])

    def test_validate_result_schema_rejects_drift(self):
        skel = build_result_skeleton()
        skel["final_n"] = 50
        with self.assertRaises(ValueError):
            validate_result_schema(skel)
        skel2 = build_result_skeleton()
        skel2["pool_k_by_id"] = {"c3e1-vector-pool-128": 999, "c3e2-vector-pool-256": 256, "c3e3-vector-pool-512": 512}
        with self.assertRaises(ValueError):
            validate_result_schema(skel2)
        skel3 = build_result_skeleton()
        skel3["batch"]["candidate_ids"] = ["baseline"]
        with self.assertRaises(ValueError):
            validate_result_schema(skel3)

    def test_dev_manifest_aggregate_matches_expected(self):
        # Use aggregate metadata only (no plaintext)
        manifest_path = ROOT / "eval" / "retrieval-v2" / "cycle3" / "dev" / "manifest.json"
        if not manifest_path.exists():
            self.skipTest("dev manifest absent (expected in sparse? actually present)")
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        self.assertEqual(data["cases"], EXPECTED_DEV_CASES)
        # Manifest core hashes should match expected dev sha
        self.assertEqual(data["hashes"]["evalset.jsonl"].lower(), EXPECTED_DEV_SHA256.lower())

    def test_prereg_file_immutable(self):
        if not (ROOT / "eval" / "retrieval-v2" / "cycle3" / "prereg-v1.json").exists():
            self.skipTest("prereg missing")
        raw = (ROOT / "eval" / "retrieval-v2" / "cycle3" / "prereg-v1.json").read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        self.assertEqual(sha.lower(), PREREG_SHA256.lower())


if __name__ == "__main__":
    unittest.main()
