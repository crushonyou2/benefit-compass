import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from retrieval_v2.schema import validate_file, validate_item, validate_role_contract
from retrieval_v2.metrics import compute_metrics, macro_recall_at_5
from retrieval_v2.paired import paired_result, is_practical_improvement, holdout_quality_gate
from retrieval_v2.p0_gate import youth_gate, gov24_gate, p0_gate, p0_gate_from_metrics
from retrieval_v2.hard_negative import hard_negative_gate
from retrieval_v2.latency import p50, p95, summarize, Sample
from retrieval_v2.guard import is_canonical_path, assert_not_canonical, ensure_retrieval_v2_path


class SchemaTest(unittest.TestCase):
    def test_valid_item(self):
        self.assertEqual([], validate_item({"query": "청년 월세 지원", "gold_source": "youth", "gold_source_id": "x", "category": "household/housing"}, 1))

    def test_source_must_be_youth_gov24(self):
        self.assertTrue(validate_item({"query": "q", "gold_source": "other", "gold_source_id": "x", "category": "c"}, 1)[0].find("gold_source") != -1)

    def test_category_required(self):
        self.assertTrue(any("category" in e for e in validate_item({"query": "q", "gold_source": "youth", "gold_source_id": "x", "category": ""}, 1)))

    def test_duplicate_query(self):
        items = [
            {"query": "청년 월세 지원", "gold_source": "youth", "gold_source_id": "a", "category": "c"},
            {"query": "청년 월세 지원", "gold_source": "gov24", "gold_source_id": "b", "category": "c"},
        ]
        errs = validate_file(items, "dev")
        self.assertTrue(any("duplicate query" in e for e in errs))

    def test_duplicate_triple(self):
        items = [
            {"query": "청년 월세 지원", "gold_source": "youth", "gold_source_id": "a", "category": "c"},
            {"query": "청년 월세 지원", "gold_source": "youth", "gold_source_id": "a", "category": "c"},
        ]
        self.assertTrue(any("duplicate (source" in e for e in validate_file(items, "dev")))

    def test_role_required(self):
        self.assertTrue(any("role" in e for e in validate_file([{"query": "q", "gold_source": "youth", "gold_source_id": "x", "category": "c"}], None)))
        self.assertEqual([], validate_file([{"query": "q", "gold_source": "youth", "gold_source_id": "x", "category": "c"}], "dev"))
        self.assertEqual([], validate_file([{"query": "q", "gold_source": "youth", "gold_source_id": "x", "category": "c"}], "holdout"))


class MetricsTest(unittest.TestCase):
    def test_source_macro(self):
        by = {"youth": [1, 1, 0, 0] * 15, "gov24": [1, 0, 0] * 7}
        self.assertAlmostEqual(macro_recall_at_5(by), 0.4167, places=4)

    def test_compute_raw_hits(self):
        ranks = [1, 5, 10, 0, 3, 0]
        m = compute_metrics(ranks)
        self.assertEqual(m["hit@5"], 3)
        self.assertEqual(m["hit@1"], 1)

    def test_category_breakdown(self):
        by_cat = {"household/housing": [1, 0, 5], "welfare/health": [0, 0]}
        m = compute_metrics([1, 0, 5, 0, 0], by_category=by_cat)
        self.assertEqual(m["by_category"]["household/housing"]["hit@5"], 2)


class PairedTest(unittest.TestCase):
    def test_paired_delta(self):
        br = [1, 0, 5, 0] * 15
        cr = [1, 1, 5, 0] * 15
        ids = [f"q{i}" for i in range(60)]
        srcs = ["youth"] * 30 + ["gov24"] * 30
        # need gov24 also 30 to make total 60, but we will use 30/30 for simplicity (not 60/21, but our paired now derives by_source from case_sources, so counts will be 30/30)
        # For this test, we use youth 30 gov24 30 to keep simple and not hit P0 gate
        res = paired_result(br, cr, ids, ids, srcs, srcs)
        self.assertEqual(res["net_hit@5"], 15)

    def test_practical_effect_rule(self):
        self.assertEqual(is_practical_improvement(2, True), "PASS")
        self.assertEqual(is_practical_improvement(1, True), "HOLD")
        self.assertEqual(is_practical_improvement(0, True), "NO-GO")
        self.assertEqual(is_practical_improvement(2, False), "HOLD")

    def test_source_regression_detection(self):
        br = [1, 0] * 30 + [1, 0] * 10 + [1]
        cr = [1, 0] * 30 + [0] * 21
        ids = [f"q{i}" for i in range(len(br))]
        srcs = ["youth"] * 60 + ["gov24"] * 21
        # br has youth 30 hits, gov24 11 hits; cr has youth 30, gov24 0
        # But we need lengths to match: br len 81 (60+21), cr len 81
        br = [1, 0] * 30 + [1, 0] * 10 + [1]  # 60 +21 =81? Actually [1,0]*30 =60, plus [1,0]*10=20 +1=21 =>81
        cr = [1, 0] * 30 + [0] * 21
        ids = [f"q{i}" for i in range(81)]
        srcs = ["youth"] * 60 + ["gov24"] * 21
        res = paired_result(br, cr, ids, ids, srcs, srcs)
        self.assertTrue(res["per_source_delta"]["gov24"]["regression"])
        self.assertFalse(res["summary"]["no_source_regression"])


class P0GateTest(unittest.TestCase):
    def test_youth_boundaries(self):
        self.assertEqual(youth_gate(28), "PASS")
        self.assertEqual(youth_gate(27), "HOLD")
        self.assertEqual(youth_gate(26), "NO-GO")
        self.assertEqual(youth_gate(60), "PASS")
        self.assertEqual(youth_gate(0), "NO-GO")

    def test_gov24_boundaries(self):
        self.assertEqual(gov24_gate(15), "PASS")
        self.assertEqual(gov24_gate(14), "HOLD")
        self.assertEqual(gov24_gate(13), "NO-GO")

    def test_p0_overall(self):
        self.assertEqual(p0_gate({"youth": [1]*28 + [0]*32, "gov24": [1]*15 + [0]*6})["overall"], "PASS")
        self.assertEqual(p0_gate({"youth": [1]*27 + [0]*33, "gov24": [1]*15 + [0]*6})["overall"], "HOLD")
        self.assertEqual(p0_gate({"youth": [1]*28 + [0]*32, "gov24": [1]*14 + [0]*7})["overall"], "HOLD")
        self.assertEqual(p0_gate({"youth": [1]*26 + [0]*34, "gov24": [1]*15 + [0]*6})["overall"], "NO-GO")


class HardNegativeTest(unittest.TestCase):
    def test_pass(self):
        self.assertEqual(hard_negative_gate(10, 10, 2, 2)["gate"], "PASS")
        self.assertEqual(hard_negative_gate(10, 11, 2, 1)["gate"], "PASS")

    def test_pure_fail(self):
        self.assertEqual(hard_negative_gate(10, 9, 2, 2)["gate"], "FAIL")

    def test_intrusion_fail(self):
        self.assertEqual(hard_negative_gate(10, 10, 2, 3)["gate"], "FAIL")


class LatencyTest(unittest.TestCase):
    def test_p50_p95(self):
        self.assertEqual(p50([1, 2, 3, 4, 5]), 3)
        self.assertEqual(p95([1, 2, 3, 4, 5]), 5)
        self.assertEqual(p95([10, 20, 30, 40, 50, 60, 70, 80, 90, 100]), 100)
        self.assertEqual(p95([10]*10), 10)

    def test_summarize_and_gate(self):
        samples = []
        for i in range(5):
            samples.append(Sample(f"q{i}", 1, "baseline", 100 + i*10))
            samples.append(Sample(f"q{i}", 1, "candidate", 90 + i*10))
        s = summarize(samples, expected_sample_count=5)
        self.assertEqual(s["sample_count"], 5)
        self.assertEqual(s["gate"], "PASS")
        samples2 = [Sample("q", 1, "baseline", 100), Sample("q", 1, "candidate", 200)]
        self.assertEqual(summarize(samples2, expected_sample_count=1)["gate"], "HOLD")

    def test_identical_counts_required(self):
        samples = [Sample("q", 1, "baseline", 100)]
        with self.assertRaises(ValueError):
            summarize(samples, expected_sample_count=1)

    def test_self_comparison_passes(self):
        samples = []
        for i in range(10):
            samples.append(Sample(f"q{i}", 1, "baseline", 100))
            samples.append(Sample(f"q{i}", 1, "candidate", 100))
        s = summarize(samples, expected_sample_count=10)
        self.assertEqual(s["gate"], "PASS")
        self.assertEqual(s["delta_p95"], 0)


class GuardTest(unittest.TestCase):
    def test_canonical_rejected(self):
        self.assertTrue(is_canonical_path("eval/canonical_youth_production_parity.json"))
        self.assertTrue(is_canonical_path("eval/canonical_manifest.json"))
        self.assertTrue(is_canonical_path("eval/canonical_hard_negative_36_production_parity.json"))
        with self.assertRaises(ValueError):
            assert_not_canonical("eval/canonical_youth_production_parity.json")
        with self.assertRaises(ValueError):
            ensure_retrieval_v2_path("eval/canonical_youth_production_parity.json")

    def test_retrieval_v2_allowed(self):
        self.assertFalse(is_canonical_path("eval/retrieval-v2/dev.json"))
        self.assertFalse(is_canonical_path("eval/retrieval-v2/holdout.json"))
        assert_not_canonical("eval/retrieval-v2/dev.json")
        ensure_retrieval_v2_path("eval/retrieval-v2/dev.json")
        ensure_retrieval_v2_path("eval/retrieval-v2/holdout.json")
        ensure_retrieval_v2_path("eval/retrieval-v2/paired.json")

    def test_must_be_under_retrieval_v2(self):
        with self.assertRaises(ValueError):
            ensure_retrieval_v2_path("eval/other.json")
        with self.assertRaises(ValueError):
            ensure_retrieval_v2_path("eval/retrieval-v2-dev.json")

    def test_traversal_rejected(self):
        with self.assertRaises(ValueError):
            ensure_retrieval_v2_path("eval/retrieval-v2/../../foo.json")
        with self.assertRaises(ValueError):
            ensure_retrieval_v2_path("eval/retrieval-v2/dev/../../../eval/results.json")
        with self.assertRaises(ValueError):
            ensure_retrieval_v2_path("eval/retrieval-v2\\..\\..\\foo.json")
        ensure_retrieval_v2_path("eval/retrieval-v2/nested/dev.json")


class P0GateExtraTest(unittest.TestCase):
    def test_youth26_gov14_is_no_go(self):
        self.assertEqual(p0_gate({"youth": [1]*26 + [0]*34, "gov24": [1]*14 + [0]*7})["overall"], "NO-GO")

    def test_youth27_gov13_is_no_go(self):
        self.assertEqual(p0_gate({"youth": [1]*27 + [0]*33, "gov24": [1]*13 + [0]*8})["overall"], "NO-GO")

    def test_wrong_lengths_raise(self):
        with self.assertRaises(ValueError):
            p0_gate({"youth": [1]*59, "gov24": [1]*21})
        with self.assertRaises(ValueError):
            p0_gate({"youth": [1]*60, "gov24": [1]*20})

    def test_hit_out_of_range(self):
        with self.assertRaises(ValueError):
            youth_gate(-1)
        with self.assertRaises(ValueError):
            youth_gate(61)
        with self.assertRaises(ValueError):
            gov24_gate(-1)
        with self.assertRaises(ValueError):
            gov24_gate(22)
        with self.assertRaises(ValueError):
            p0_gate_from_metrics({"by_source": {"youth": {"hit@5": -1, "n": 60}, "gov24": {"hit@5": 15, "n": 21}}})


class PairedExtraTest(unittest.TestCase):
    def test_missing_by_source_fails(self):
        br = [1]*10
        cr = [1]*10
        ids = [f"q{i}" for i in range(10)]
        srcs = ["youth"]*5 + ["gov24"]*5
        # missing by_source is now not allowed because we derive, but we test missing case_ids
        with self.assertRaises(ValueError):
            paired_result(br, cr, None, None, None, None)

    def test_case_ids_mismatch(self):
        br = [1]*3
        cr = [1]*3
        with self.assertRaises(ValueError):
            paired_result(br, cr, ["a","b","c"], ["a","b","d"], ["youth","youth","gov24"], ["youth","youth","gov24"])
        with self.assertRaises(ValueError):
            paired_result(br, cr, ["a","b","c"], ["c","b","a"], ["youth","youth","gov24"], ["youth","youth","gov24"])

    def test_source_membership_mismatch(self):
        br = [1]*3
        cr = [1]*3
        with self.assertRaises(ValueError):
            paired_result(br, cr, ["a","b","c"], ["a","b","c"], ["youth","youth","gov24"], ["youth","gov24","gov24"])

    def test_holdout_gate_precedence(self):
        self.assertEqual(holdout_quality_gate(False, 2, True), "NO-GO")
        self.assertEqual(holdout_quality_gate(True, 0, True), "NO-GO")
        self.assertEqual(holdout_quality_gate(True, -1, True), "NO-GO")
        self.assertEqual(holdout_quality_gate(True, 0, False), "NO-GO")
        self.assertEqual(holdout_quality_gate(True, 1, True), "HOLD")
        self.assertEqual(holdout_quality_gate(True, 2, False), "HOLD")
        self.assertEqual(holdout_quality_gate(True, 3, False), "HOLD")
        self.assertEqual(holdout_quality_gate(True, 2, True), "PASS")
        self.assertEqual(holdout_quality_gate(True, 5, True), "PASS")

    def test_is_practical_fixed(self):
        self.assertEqual(is_practical_improvement(0, False), "NO-GO")
        self.assertEqual(is_practical_improvement(-5, False), "NO-GO")
        self.assertEqual(is_practical_improvement(0, True), "NO-GO")

    def test_case_ids_omitted(self):
        br = [1]*5
        cr = [1]*5
        with self.assertRaises(ValueError):
            paired_result(br, cr, None, None, ["youth"]*3+["gov24"]*2, ["youth"]*3+["gov24"]*2)

    def test_duplicate_case_id(self):
        br = [1]*3
        cr = [1]*3
        with self.assertRaises(ValueError):
            paired_result(br, cr, ["a","a","c"], ["a","a","c"], ["youth","youth","gov24"], ["youth","youth","gov24"])

    def test_empty_case_id(self):
        br = [1]*3
        cr = [1]*3
        with self.assertRaises(ValueError):
            paired_result(br, cr, ["a","","c"], ["a","","c"], ["youth","youth","gov24"], ["youth","youth","gov24"])

    def test_invalid_source(self):
        br = [1]*3
        cr = [1]*3
        with self.assertRaises(ValueError):
            paired_result(br, cr, ["a","b","c"], ["a","b","c"], ["youth","other","gov24"], ["youth","other","gov24"])

    def test_same_counts_but_different_order(self):
        br = [1]*3
        cr = [1]*3
        with self.assertRaises(ValueError):
            paired_result(br, cr, ["a","b","c"], ["a","b","c"], ["youth","gov24","youth"], ["youth","youth","gov24"])

    def test_provided_by_source_inconsistent(self):
        br = [1,0,1]
        cr = [1,0,1]
        ids = ["a","b","c"]
        srcs = ["youth","youth","gov24"]
        # provide by_source that is inconsistent with derived
        bad_by = {"youth": [1,1], "gov24": [1]}  # derived would be youth [1,0] gov24 [1]
        with self.assertRaises(ValueError):
            paired_result(br, cr, ids, ids, srcs, srcs, baseline_by_source=bad_by, candidate_by_source=bad_by)


class LatencyExtraTest(unittest.TestCase):
    def test_different_key_sets(self):
        samples = [Sample("q1", 1, "baseline", 100), Sample("q2", 1, "candidate", 100)]
        with self.assertRaises(ValueError):
            summarize(samples, expected_sample_count=1)

    def test_duplicate_sample(self):
        samples = [Sample("q1", 1, "baseline", 100), Sample("q1", 1, "baseline", 101), Sample("q1", 1, "candidate", 100), Sample("q1", 1, "candidate", 101)]
        with self.assertRaises(ValueError):
            summarize(samples, expected_sample_count=1)

    def test_all_baseline_then_all_candidate_rejected(self):
        samples = [Sample("q1", 1, "baseline", 100), Sample("q2", 1, "baseline", 100), Sample("q1", 1, "candidate", 100), Sample("q2", 1, "candidate", 100)]
        with self.assertRaises(ValueError):
            summarize(samples, expected_sample_count=2)

    def test_proper_interleaving_accepted(self):
        samples = [Sample("q1", 1, "baseline", 100), Sample("q1", 1, "candidate", 100), Sample("q2", 1, "baseline", 100), Sample("q2", 1, "candidate", 100)]
        s = summarize(samples, expected_sample_count=2)
        self.assertEqual(s["sample_count"], 2)

    def test_negative_latency(self):
        samples = [Sample("q1", 1, "baseline", -5), Sample("q1", 1, "candidate", 100)]
        with self.assertRaises(ValueError):
            summarize(samples, expected_sample_count=1)

    def test_nan_inf(self):
        samples = [Sample("q1", 1, "baseline", float("nan")), Sample("q1", 1, "candidate", 100)]
        with self.assertRaises(ValueError):
            summarize(samples, expected_sample_count=1)
        samples = [Sample("q1", 1, "baseline", float("inf")), Sample("q1", 1, "candidate", 100)]
        with self.assertRaises(ValueError):
            summarize(samples, expected_sample_count=1)

    def test_expected_missing(self):
        samples = [Sample("q1", 1, "baseline", 100), Sample("q1", 1, "candidate", 100)]
        with self.assertRaises(TypeError):
            summarize(samples)  # missing expected_sample_count
        with self.assertRaises(ValueError):
            summarize(samples, expected_sample_count=0)
        with self.assertRaises(ValueError):
            summarize(samples, expected_sample_count=-1)
        with self.assertRaises(ValueError):
            summarize(samples, expected_sample_count="10")

    def test_expected_mismatch(self):
        samples = [Sample("q1", 1, "baseline", 100), Sample("q1", 1, "candidate", 100), Sample("q2", 1, "baseline", 100), Sample("q2", 1, "candidate", 100)]
        with self.assertRaises(ValueError):
            summarize(samples, expected_sample_count=1)
        with self.assertRaises(ValueError):
            summarize(samples, expected_sample_count=10)


class SchemaExtraTest(unittest.TestCase):
    def test_dev_29_fails(self):
        items = [{"query": f"q{i}", "gold_source": "youth" if i < 15 else "gov24", "gold_source_id": f"id{i}", "category": "c"} for i in range(29)]
        self.assertTrue(any("30..40" in e for e in validate_role_contract(items, "dev")))

    def test_dev_30_balanced_pass(self):
        items = [{"query": f"q{i}", "gold_source": "youth" if i < 15 else "gov24", "gold_source_id": f"id{i}", "category": "c"} for i in range(30)]
        self.assertEqual([], validate_role_contract(items, "dev"))

    def test_dev_40_balanced_pass(self):
        items = [{"query": f"q{i}", "gold_source": "youth" if i < 20 else "gov24", "gold_source_id": f"id{i}", "category": "c"} for i in range(40)]
        self.assertEqual([], validate_role_contract(items, "dev"))

    def test_dev_41_fails(self):
        items = [{"query": f"q{i}", "gold_source": "youth" if i < 21 else "gov24", "gold_source_id": f"id{i}", "category": "c"} for i in range(41)]
        self.assertTrue(any("30..40" in e for e in validate_role_contract(items, "dev")))

    def test_holdout_39_fails(self):
        items = [{"query": f"q{i}", "gold_source": "youth" if i < 20 else "gov24", "gold_source_id": f"id{i}", "category": "c"} for i in range(39)]
        self.assertTrue(any(">=40" in e for e in validate_role_contract(items, "holdout")))

    def test_holdout_40_balanced_pass(self):
        items = [{"query": f"q{i}", "gold_source": "youth" if i < 20 else "gov24", "gold_source_id": f"id{i}", "category": "c"} for i in range(40)]
        self.assertEqual([], validate_role_contract(items, "holdout"))

    def test_holdout_41_20_21_pass(self):
        items = [{"query": f"q{i}", "gold_source": "youth" if i < 20 else "gov24", "gold_source_id": f"id{i}", "category": "c"} for i in range(41)]
        self.assertEqual([], validate_role_contract(items, "holdout"))

    def test_holdout_40_unbalanced_fails(self):
        items = [{"query": f"q{i}", "gold_source": "youth" if i < 30 else "gov24", "gold_source_id": f"id{i}", "category": "c"} for i in range(40)]
        self.assertTrue(any("abs" in e for e in validate_role_contract(items, "holdout")))


if __name__ == "__main__":
    unittest.main()
