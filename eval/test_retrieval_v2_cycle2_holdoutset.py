import json
import pathlib
import sys
import hashlib
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from retrieval_v2.schema import validate_file, validate_role_contract


class Cycle2HoldoutSetTest(unittest.TestCase):
    def setUp(self):
        self.path = pathlib.Path(__file__).with_name("retrieval-v2") / "cycle2" / "holdout" / "evalset.jsonl"
        self.items = [json.loads(l) for l in self.path.read_text(encoding="utf-8").splitlines() if l.strip()]
        self.manifest_path = pathlib.Path(__file__).with_name("retrieval-v2") / "cycle2" / "holdout" / "manifest.json"
        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.audit_path = pathlib.Path(__file__).with_name("retrieval-v2") / "cycle2" / "holdout" / "annotation_audit.json"

    def test_40_cases(self):
        self.assertEqual(40, len(self.items))

    def test_20_youth_20_gov24(self):
        youth = sum(1 for x in self.items if x["gold_source"] == "youth")
        gov24 = sum(1 for x in self.items if x["gold_source"] == "gov24")
        self.assertEqual(20, youth)
        self.assertEqual(20, gov24)

    def test_case_id_sequential(self):
        expected = [f"c2h-{i:03d}" for i in range(1, 41)]
        actual = [x["case_id"] for x in self.items]
        self.assertEqual(expected, actual)

    def test_case_id_unique(self):
        ids = [x["case_id"] for x in self.items]
        self.assertEqual(len(ids), len(set(ids)))

    def test_query_unique(self):
        qs = [x["query"].strip() for x in self.items]
        self.assertEqual(len(qs), len(set(qs)))

    def test_gold_unique_pairs(self):
        triples = [(x["gold_source"], x["gold_source_id"], x["query"].strip()) for x in self.items]
        self.assertEqual(len(triples), len(set(triples)))

    def test_schema_validation(self):
        errs = validate_file(self.items, "holdout")
        self.assertEqual([], errs, "\n".join(errs))

    def test_role_contract(self):
        errs = validate_role_contract(self.items, "holdout")
        self.assertEqual([], errs, "\n".join(errs))

    def test_no_query_overlap_with_canonical(self):
        p0_q = set()
        for p in [pathlib.Path("eval/evalset.jsonl"), pathlib.Path("eval/expansion_evalset.jsonl"), pathlib.Path("eval/expansion_api_evalset.jsonl")]:
            if p.exists():
                p0_q |= set(json.loads(l)["query"].strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip() and json.loads(l).get("query"))
        holdout_q = set(x["query"].strip() for x in self.items)
        self.assertEqual(set(), holdout_q & p0_q)

    def test_no_gold_overlap_with_p0(self):
        p0_gold = set()
        for p in [pathlib.Path("eval/evalset.jsonl"), pathlib.Path("eval/expansion_evalset.jsonl"), pathlib.Path("eval/expansion_api_evalset.jsonl")]:
            if p.exists():
                for l in p.read_text(encoding="utf-8").splitlines():
                    if not l.strip():
                        continue
                    j = json.loads(l)
                    gid = j.get("gold_source_id")
                    if gid:
                        p0_gold.add(j.get("gold_source_id"))
                        # also consider pair
        holdout_gold = set(x["gold_source_id"] for x in self.items)
        self.assertEqual(set(), holdout_gold & p0_gold)

    def test_no_query_overlap_with_dev(self):
        dev_path = pathlib.Path("eval/retrieval-v2/dev/evalset.jsonl")
        if dev_path.exists():
            dev_q = set(json.loads(l)["query"].strip() for l in dev_path.read_text(encoding="utf-8").splitlines() if l.strip() and json.loads(l).get("query"))
            holdout_q = set(x["query"].strip() for x in self.items)
            self.assertEqual(set(), holdout_q & dev_q)

    def test_no_gold_overlap_with_dev(self):
        dev_path = pathlib.Path("eval/retrieval-v2/dev/evalset.jsonl")
        if dev_path.exists():
            dev_gold = set(json.loads(l)["gold_source_id"] for l in dev_path.read_text(encoding="utf-8").splitlines() if l.strip())
            holdout_gold = set(x["gold_source_id"] for x in self.items)
            self.assertEqual(set(), holdout_gold & dev_gold)

    def test_manifest_exists_and_valid(self):
        self.assertTrue(self.manifest_path.exists())
        self.assertEqual("holdout", self.manifest["role"])
        self.assertEqual(2, self.manifest["cycle"])
        self.assertEqual("D-007", self.manifest["contract"])
        self.assertEqual(40, self.manifest["cases"])
        self.assertEqual(20, self.manifest["youth"])
        self.assertEqual(20, self.manifest["gov24"])
        self.assertEqual(40, self.manifest["by_source"]["youth"] + self.manifest["by_source"]["gov24"])
        # category counts
        cat_counts = self.manifest["category_counts"]
        self.assertEqual(40, sum(cat_counts.values()))
        # each of six categories present
        expected_cats = {"housing_finance", "family_care", "employment_education", "culture_community", "welfare_health", "business_agriculture"}
        self.assertEqual(expected_cats, set(cat_counts.keys()))
        for v in cat_counts.values():
            self.assertTrue(5 <= v <= 9, f"category count {v} should be balanced 5-9")
        # sha
        self.assertIn("sha256", self.manifest)
        self.assertEqual("utf8_text_lf_normalized", self.manifest["sha256_basis"])
        # compute actual sha
        data = self.path.read_bytes().decode("utf-8").replace("\r\n", "\n").encode("utf-8")
        actual_sha = hashlib.sha256(data).hexdigest()
        self.assertEqual(actual_sha, self.manifest["sha256"])
        # base commit
        self.assertEqual("434b798d60bf15433590362aaad4a021846094d4", self.manifest["base_commit"])
        # provenance flags
        self.assertFalse(self.manifest["retrieval_observed"])
        self.assertFalse(self.manifest["candidate_tuning_started"])
        self.assertFalse(self.manifest["cycle1_candidate_results_used_for_case_selection"])
        self.assertTrue(self.manifest["cycle1_holdout_accessed_for_collision_audit"])
        self.assertEqual(0, self.manifest["p0_query_overlap"])
        self.assertEqual(0, self.manifest["p0_gold_overlap"])
        self.assertEqual(0, self.manifest["dev_query_overlap"])
        self.assertEqual(0, self.manifest["dev_gold_overlap"])
        self.assertEqual(0, self.manifest["cycle1_holdout_query_overlap"])
        self.assertEqual(0, self.manifest["cycle1_holdout_gold_overlap"])
        self.assertTrue(self.manifest["frozen_before_tuning"])

    def test_annotation_audit_consistency(self):
        self.assertTrue(self.audit_path.exists(), "annotation_audit.json must exist")
        audit = json.loads(self.audit_path.read_text(encoding="utf-8"))
        self.assertEqual(40, audit["cases"])
        self.assertEqual(40, audit["well_posed_gold"])
        self.assertEqual(0, audit["ambiguous_gold"])
        self.assertEqual(0, audit["p0_query_overlap"])
        self.assertEqual(0, audit["p0_gold_overlap"])
        self.assertEqual(0, audit["dev_query_overlap"])
        self.assertEqual(0, audit["dev_gold_overlap"])
        self.assertEqual(0, audit["cycle1_holdout_query_overlap"])
        self.assertEqual(0, audit["cycle1_holdout_gold_overlap"])
        self.assertEqual(40, len(audit["per_case"]))
        audit_ids = [c["case_id"] for c in audit["per_case"]]
        eval_ids = [x["case_id"] for x in self.items]
        self.assertEqual(eval_ids, audit_ids)
        for a, e in zip(audit["per_case"], self.items):
            self.assertEqual(a["source"], e["gold_source"])
            self.assertEqual(a["source_id"], e["gold_source_id"])
            self.assertEqual(a["category"], e["category"])
            self.assertTrue(a["jurisdiction_or_scope"].strip(), f"{a['case_id']} jurisdiction empty")
            self.assertTrue(a["distinguishing_basis"].strip(), f"{a['case_id']} distinguishing_basis empty")
            self.assertIn("required_query_terms", a, f"{a['case_id']} missing required_query_terms")
            self.assertTrue(a["required_query_terms"], f"{a['case_id']} required_query_terms empty")
            for term in a["required_query_terms"]:
                self.assertIn(term, e["query"], f"{a['case_id']} required term {term!r} not in query {e['query']!r}")
            self.assertIn("competing_policy_count", a)

    def test_sealed_exists(self):
        sealed = pathlib.Path(__file__).with_name("retrieval-v2") / "cycle2" / "holdout" / "SEALED.md"
        self.assertTrue(sealed.exists())
        text = sealed.read_text(encoding="utf-8")
        self.assertIn("candidate tuning", text.lower())
        self.assertIn("retrieval", text.lower())
        self.assertIn("frozen before", text.lower())

    def test_lf_normalized(self):
        raw = self.path.read_bytes()
        self.assertNotIn(b"\r\n", raw, "evalset must be LF normalized, no CRLF")
        self.assertNotIn(b"\r", raw, "evalset must be LF normalized")

    def test_gold_source_valid(self):
        for x in self.items:
            self.assertIn(x["gold_source"], ["youth", "gov24"])
            self.assertTrue(x["gold_source_id"].strip())
            self.assertTrue(x["category"].strip())
            self.assertTrue(x["query"].strip())
            self.assertTrue(x.get("gold_title", "").strip() if "gold_title" in x else True)


if __name__ == "__main__":
    unittest.main()
