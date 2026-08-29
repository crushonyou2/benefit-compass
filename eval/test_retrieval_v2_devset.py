import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from retrieval_v2.schema import validate_file, validate_role_contract


class DevSetTest(unittest.TestCase):
    def setUp(self):
        self.path = pathlib.Path(__file__).with_name("retrieval-v2") / "dev" / "evalset.jsonl"
        self.items = [json.loads(l) for l in self.path.read_text(encoding="utf-8").splitlines() if l.strip()]

    def test_36_cases(self):
        self.assertEqual(36, len(self.items))

    def test_18_youth_18_gov24(self):
        youth = sum(1 for x in self.items if x["gold_source"] == "youth")
        gov24 = sum(1 for x in self.items if x["gold_source"] == "gov24")
        self.assertEqual(18, youth)
        self.assertEqual(18, gov24)

    def test_case_id_sequential(self):
        expected = [f"dev-{i:03d}" for i in range(1, 37)]
        actual = [x["case_id"] for x in self.items]
        self.assertEqual(expected, actual)

    def test_case_id_unique(self):
        ids = [x["case_id"] for x in self.items]
        self.assertEqual(len(ids), len(set(ids)))

    def test_query_unique(self):
        qs = [x["query"].strip() for x in self.items]
        self.assertEqual(len(qs), len(set(qs)))

    def test_schema_validation(self):
        errs = validate_file(self.items, "dev")
        self.assertEqual([], errs, "\n".join(errs))

    def test_role_contract(self):
        errs = validate_role_contract(self.items, "dev")
        self.assertEqual([], errs, "\n".join(errs))

    def test_no_query_overlap_with_canonical(self):
        p0_q = set()
        for p in [pathlib.Path("eval/evalset.jsonl"), pathlib.Path("eval/expansion_evalset.jsonl"), pathlib.Path("eval/expansion_api_evalset.jsonl")]:
            if p.exists():
                p0_q |= set(json.loads(l)["query"].strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip() and json.loads(l).get("query"))
        dev_q = set(x["query"].strip() for x in self.items)
        self.assertEqual(set(), dev_q & p0_q)

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
                        p0_gold.add(gid)
        dev_gold = set(x["gold_source_id"] for x in self.items)
        self.assertEqual(set(), dev_gold & p0_gold)

    def test_annotation_audit_consistency(self):
        audit_path = pathlib.Path(__file__).with_name("retrieval-v2") / "dev" / "annotation_audit.json"
        self.assertTrue(audit_path.exists(), "annotation_audit.json must exist")
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
        self.assertEqual(36, audit["cases"])
        self.assertEqual(36, audit["well_posed_gold"])
        self.assertEqual(0, audit["ambiguous_gold"])
        self.assertEqual(0, audit["p0_query_overlap"])
        self.assertEqual(0, audit["p0_gold_overlap"])
        self.assertEqual(36, len(audit["per_case"]))
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
        # explicit regression for 4 corrected cases
        by_id = {c["case_id"]: c for c in audit["per_case"]}
        self.assertIn("부여군", next(x["query"] for x in self.items if x["case_id"]=="dev-003"))
        self.assertEqual(["부여군", "셰어하우스"], by_id["dev-003"]["required_query_terms"])
        self.assertIn("광주", next(x["query"] for x in self.items if x["case_id"]=="dev-033"))
        self.assertIn("서구", next(x["query"] for x in self.items if x["case_id"]=="dev-033"))
        self.assertEqual(["광주", "서구", "웰컴박스"], by_id["dev-033"]["required_query_terms"])
        self.assertIn("광주", next(x["query"] for x in self.items if x["case_id"]=="dev-034"))
        self.assertEqual(["광주", "학자금"], by_id["dev-034"]["required_query_terms"])
        self.assertEqual("welfare_health", by_id["dev-030"]["category"])
        self.assertEqual(["용인", "시민안전보험"], by_id["dev-030"]["required_query_terms"])
