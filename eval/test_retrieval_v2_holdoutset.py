import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from retrieval_v2.schema import validate_file, validate_role_contract
from retrieval_v2.provenance import canonical_text_sha256


class HoldoutSetTest(unittest.TestCase):
    def setUp(self):
        self.path = pathlib.Path(__file__).with_name("retrieval-v2") / "holdout" / "evalset.jsonl"
        self.manifest_path = pathlib.Path(__file__).with_name("retrieval-v2") / "holdout" / "manifest.json"
        self.audit_path = pathlib.Path(__file__).with_name("retrieval-v2") / "holdout" / "annotation_audit.json"
        self.items = [json.loads(l) for l in self.path.read_text(encoding="utf-8").splitlines() if l.strip()]
        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.audit = json.loads(self.audit_path.read_text(encoding="utf-8"))

    def test_exactly_40(self):
        self.assertEqual(40, len(self.items))
        self.assertEqual(40, self.manifest["cases"])

    def test_20_youth_20_gov24(self):
        youth = sum(1 for x in self.items if x["gold_source"] == "youth")
        gov24 = sum(1 for x in self.items if x["gold_source"] == "gov24")
        self.assertEqual(20, youth)
        self.assertEqual(20, gov24)
        self.assertEqual(20, self.manifest["youth"])
        self.assertEqual(20, self.manifest["gov24"])

    def test_case_ids_holdout_001_040(self):
        expected = [f"holdout-{i:03d}" for i in range(1, 41)]
        actual = [x["case_id"] for x in self.items]
        self.assertEqual(expected, actual)

    def test_case_id_unique(self):
        ids = [x["case_id"] for x in self.items]
        self.assertEqual(len(ids), len(set(ids)))

    def test_query_unique(self):
        qs = [x["query"].strip() for x in self.items]
        self.assertEqual(len(qs), len(set(qs)))

    def test_schema_validation(self):
        errs = validate_file(self.items, "holdout")
        self.assertEqual([], errs, "\n".join(errs))

    def test_role_contract(self):
        errs = validate_role_contract(self.items, "holdout")
        self.assertEqual([], errs, "\n".join(errs))

    def test_p0_query_overlap(self):
        p0_q = set()
        for p in [pathlib.Path("eval/evalset.jsonl"), pathlib.Path("eval/expansion_evalset.jsonl"), pathlib.Path("eval/expansion_api_evalset.jsonl")]:
            if p.exists():
                p0_q |= set(json.loads(l)["query"].strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip() and json.loads(l).get("query"))
        holdout_q = set(x["query"].strip() for x in self.items)
        self.assertEqual(set(), holdout_q & p0_q)
        self.assertEqual(0, self.manifest["p0_query_overlap"])
        self.assertEqual(0, self.audit["p0_query_overlap"])

    def test_p0_gold_overlap(self):
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
        holdout_gold = set(x["gold_source_id"] for x in self.items)
        self.assertEqual(set(), holdout_gold & p0_gold)
        self.assertEqual(0, self.manifest["p0_gold_overlap"])
        self.assertEqual(0, self.audit["p0_gold_overlap"])

    def test_dev_query_overlap(self):
        dev_path = pathlib.Path(__file__).with_name("retrieval-v2") / "dev" / "evalset.jsonl"
        if not dev_path.exists():
            # dev may be on different branch, try via git show
            import subprocess
            try:
                dev_content = subprocess.check_output(["git","show","40c0b42:eval/retrieval-v2/dev/evalset.jsonl"], text=True)
                dev_q = set(json.loads(l)["query"].strip() for l in dev_content.splitlines() if l.strip())
            except:
                dev_q = set()
        else:
            dev_q = set(json.loads(l)["query"].strip() for l in dev_path.read_text(encoding="utf-8").splitlines() if l.strip())
        holdout_q = set(x["query"].strip() for x in self.items)
        self.assertEqual(set(), holdout_q & dev_q)
        self.assertEqual(0, self.manifest["dev_query_overlap"])
        self.assertEqual(0, self.audit["dev_query_overlap"])

    def test_dev_gold_overlap(self):
        dev_path = pathlib.Path(__file__).with_name("retrieval-v2") / "dev" / "evalset.jsonl"
        if not dev_path.exists():
            import subprocess
            try:
                dev_content = subprocess.check_output(["git","show","40c0b42:eval/retrieval-v2/dev/evalset.jsonl"], text=True)
                dev_gold = set(json.loads(l)["gold_source_id"] for l in dev_content.splitlines() if l.strip())
            except:
                dev_gold = set()
        else:
            dev_gold = set(json.loads(l)["gold_source_id"] for l in dev_path.read_text(encoding="utf-8").splitlines() if l.strip())
        holdout_gold = set(x["gold_source_id"] for x in self.items)
        self.assertEqual(set(), holdout_gold & dev_gold)
        self.assertEqual(0, self.manifest["dev_gold_overlap"])
        self.assertEqual(0, self.audit["dev_gold_overlap"])

    def test_annotation_ids_match(self):
        self.assertEqual(40, len(self.audit["per_case"]))
        audit_ids = [c["case_id"] for c in self.audit["per_case"]]
        eval_ids = [x["case_id"] for x in self.items]
        self.assertEqual(eval_ids, audit_ids)

    def test_annotation_source_category_match(self):
        for a, e in zip(self.audit["per_case"], self.items):
            self.assertEqual(a["source"], e["gold_source"])
            self.assertEqual(a["source_id"], e["gold_source_id"])
            self.assertEqual(a["category"], e["category"])

    def test_well_posed_and_ambiguous(self):
        self.assertEqual(40, self.audit["cases"])
        self.assertEqual(40, self.audit["well_posed_gold"])
        self.assertEqual(0, self.audit["ambiguous_gold"])

    def test_jurisdiction_and_basis_non_empty(self):
        for c in self.audit["per_case"]:
            self.assertTrue(c["jurisdiction_or_scope"].strip(), f"{c['case_id']} jurisdiction empty")
            self.assertTrue(c["distinguishing_basis"].strip(), f"{c['case_id']} distinguishing_basis empty")
            self.assertIn("required_query_terms", c)
            self.assertTrue(c["required_query_terms"], f"{c['case_id']} required_query_terms empty")
            for term in c["required_query_terms"]:
                self.assertIn(term, next(x["query"] for x in self.items if x["case_id"] == c["case_id"]), f"{c['case_id']} term {term!r} not in query")

    def test_manifest_hash(self):
        self.assertEqual("holdout", self.manifest["role"])
        self.assertEqual(canonical_text_sha256(self.path), self.manifest["sha256"])
        self.assertEqual("utf8_text_lf_normalized", self.manifest["sha256_basis"])
        self.assertEqual(40, self.manifest["cases"])
        self.assertFalse(self.manifest["retrieval_observed"])
        self.assertFalse(self.manifest["candidate_tuning_started"])
        self.assertFalse(self.manifest["challenge_slice_included"])

    def test_retrieval_observation_guard(self):
        holdout_dir = pathlib.Path(__file__).with_name("retrieval-v2") / "holdout"
        allowed = {"evalset.jsonl", "annotation_audit.json", "manifest.json", "SEALED.md"}
        for p in holdout_dir.iterdir():
            if p.is_file():
                self.assertIn(p.name, allowed, f"holdout result artifact {p.name} not allowed before tuning")

    def test_no_copy_error_in_basis(self):
        titles = {x["gold_title"]: x["case_id"] for x in self.items}
        for a in self.audit["per_case"]:
            basis = a["distinguishing_basis"]
            for title, cid in titles.items():
                if cid != a["case_id"] and title in basis:
                    self.fail(f"{a['case_id']} basis contains other case {cid} title {title!r}: {basis!r}")


if __name__ == "__main__":
    unittest.main()
