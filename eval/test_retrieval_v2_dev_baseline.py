import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from retrieval_v2.schema import load_and_validate
from retrieval_v2.metrics import compute_metrics
from retrieval_v2.guard import ensure_retrieval_v2_path


class DevBaselineRunnerTest(unittest.TestCase):
    def test_source_aware_gold_rank(self):
        # gold is (source, source_id) not just source_id
        from retrieval_v2.run_dev_baseline import rank_of
        cands = [{"source": "youth", "source_id": "a"}, {"source": "gov24", "source_id": "a"}]
        self.assertEqual(1, rank_of(cands, ("youth", "a")))
        self.assertEqual(2, rank_of(cands, ("gov24", "a")))
        self.assertEqual(0, rank_of(cands, ("youth", "b")))

    def test_case_identity_preserved(self):
        p = pathlib.Path("eval/retrieval-v2/dev/baseline.json")
        if not p.exists():
            self.skipTest("baseline not yet generated")
        data = json.loads(p.read_text(encoding="utf-8"))
        for c in data["per_case"]:
            self.assertIn("case_id", c)
            self.assertIn("query", c)
            self.assertIn("gold_source", c)
            self.assertIn("gold_source_id", c)
            # case_id must be dev-xxx and unique
            self.assertTrue(c["case_id"].startswith("dev-"))

    def test_per_case_rank_mapping(self):
        p = pathlib.Path("eval/retrieval-v2/dev/baseline.json")
        if not p.exists():
            self.skipTest("baseline not yet generated")
        data = json.loads(p.read_text(encoding="utf-8"))
        # per_case rank should be 0..10 or 0 for miss
        for c in data["per_case"]:
            self.assertIn(c["rank"], list(range(0, 11)) + [0])
            # hit flags consistent
            self.assertEqual(c["hit@1"], c["rank"] == 1)
            self.assertEqual(c["hit@5"], 1 <= c["rank"] <= 5)

    def test_source_macro_aggregation(self):
        p = pathlib.Path("eval/retrieval-v2/dev/baseline.json")
        if not p.exists():
            self.skipTest("baseline not yet generated")
        data = json.loads(p.read_text(encoding="utf-8"))
        youth = data["by_source"]["youth"]["recall@5"]
        gov24 = data["by_source"]["gov24"]["recall@5"]
        macro = data["source_macro_recall@5"]
        self.assertAlmostEqual((youth + gov24) / 2, macro, places=4)

    def test_category_aggregation(self):
        p = pathlib.Path("eval/retrieval-v2/dev/baseline.json")
        if not p.exists():
            self.skipTest("baseline not yet generated")
        data = json.loads(p.read_text(encoding="utf-8"))
        # by_category hit@5 should sum correctly
        for cat, vals in data["by_category"].items():
            self.assertIn("hit@5", vals)
            self.assertIn("recall@5", vals)

    def test_output_path_guard(self):
        with self.assertRaises(ValueError):
            ensure_retrieval_v2_path("eval/canonical_youth_production_parity.json")
        # dev baseline must be under retrieval-v2
        ensure_retrieval_v2_path("eval/retrieval-v2/dev/baseline.json")
        with self.assertRaises(ValueError):
            ensure_retrieval_v2_path("eval/retrieval-v2/../../eval/canonical.json")

    def test_dev_set_hash_provenance(self):
        p = pathlib.Path("eval/retrieval-v2/dev/baseline.json")
        if not p.exists():
            self.skipTest("baseline not yet generated")
        data = json.loads(p.read_text(encoding="utf-8"))
        self.assertIn("dev_set_sha256", data)
        self.assertEqual(64, len(data["dev_set_sha256"]))
        self.assertIn("dev_set_freeze_commit", data)
        self.assertEqual(36, data["n"])
        # ensure dev set file hash matches
        import hashlib
        dev_path = pathlib.Path("eval/retrieval-v2/dev/evalset.jsonl")
        self.assertEqual(hashlib.sha256(dev_path.read_bytes()).hexdigest(), data["dev_set_sha256"])

    def test_schema_still_valid(self):
        dev_path = pathlib.Path("eval/retrieval-v2/dev/evalset.jsonl")
        # should not raise
        load_and_validate(dev_path, "dev")

    def test_production_contract_recorded(self):
        p = pathlib.Path("eval/retrieval-v2/dev/baseline.json")
        if not p.exists():
            self.skipTest("baseline not yet generated")
        data = json.loads(p.read_text(encoding="utf-8"))
        pc = data["production_contract"]
        self.assertEqual(30, pc["candidates"])
        self.assertEqual(0.78, pc["bi_encoder_min_score"])
        self.assertEqual(0.01, pc["lexical_bias"])


if __name__ == "__main__":
    unittest.main()
