import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from retrieval_v2.schema import validate_file, validate_item
from retrieval_v2.metrics import compute_metrics, macro_recall_at_5
from retrieval_v2.paired import paired_result, is_practical_improvement
from retrieval_v2.p0_gate import youth_gate, gov24_gate, p0_gate
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
        by = {"youth": [1, 1, 0, 0] * 15, "gov24": [1, 0, 0] * 7}  # youth 30/60=0.5, gov24 7/21=0.333
        # youth 30 hits, gov24 7 hits -> macro 0.4167
        self.assertAlmostEqual(macro_recall_at_5(by), 0.4167, places=4)

    def test_compute_raw_hits(self):
        ranks = [1, 5, 10, 0, 3, 0]  # 4 hits@5 (1,5,3) -> actually 1,5,3 =3, plus ? 1 is hit, 5 is hit, 3 is hit => 3? plus 1? Let's count: 1 hit,5 hit,10 not,0 not,3 hit,0 not => 3
        m = compute_metrics(ranks)
        self.assertEqual(m["hit@5"], 3)
        self.assertEqual(m["hit@1"], 1)

    def test_category_breakdown(self):
        by_cat = {"household/housing": [1, 0, 5], "welfare/health": [0, 0]}
        m = compute_metrics([1, 0, 5, 0, 0], by_category=by_cat)
        self.assertEqual(m["by_category"]["household/housing"]["hit@5"], 2)


class PairedTest(unittest.TestCase):
    def test_paired_delta(self):
        br = [1, 0, 5, 0] * 15  # 30 hits
        cr = [1, 1, 5, 0] * 15  # 45 hits? Actually 3 per 4 *15=45 -> net +15
        res = paired_result(br, cr)
        self.assertEqual(res["net_hit@5"], 15)
        self.assertTrue(res["summary"]["macro_pass"] in (True, False))

    def test_practical_effect_rule(self):
        self.assertEqual(is_practical_improvement(2, True), "PASS")
        self.assertEqual(is_practical_improvement(1, True), "HOLD")
        self.assertEqual(is_practical_improvement(0, True), "NO-GO")
        self.assertEqual(is_practical_improvement(2, False), "HOLD")  # source regression → HOLD

    def test_source_regression_detection(self):
        br_by = {"youth": [1, 0] * 30, "gov24": [1, 0] * 10 + [1]}
        cr_by = {"youth": [1, 0] * 30, "gov24": [0] * 21}  # gov24 loses
        br = br_by["youth"] + br_by["gov24"]
        cr = cr_by["youth"] + cr_by["gov24"]
        res = paired_result(br, cr, br_by, cr_by)
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
        s = summarize(samples)
        self.assertEqual(s["sample_count"], 5)
        self.assertEqual(s["gate"], "PASS")
        # candidate slower
        samples2 = [Sample("q", 1, "baseline", 100), Sample("q", 1, "candidate", 200)]
        self.assertEqual(summarize(samples2)["gate"], "HOLD")

    def test_identical_counts_required(self):
        samples = [Sample("q", 1, "baseline", 100)]
        with self.assertRaises(ValueError):
            summarize(samples)

    def test_self_comparison_passes(self):
        # baseline == candidate synthetic
        samples = []
        for i in range(10):
            samples.append(Sample(f"q{i}", 1, "baseline", 100))
            samples.append(Sample(f"q{i}", 1, "candidate", 100))
        s = summarize(samples)
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


if __name__ == "__main__":
    unittest.main()
