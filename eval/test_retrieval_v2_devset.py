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


if __name__ == "__main__":
    unittest.main()
