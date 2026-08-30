import json
import pathlib
import sys
import hashlib
import subprocess
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from retrieval_v2.schema import validate_file, validate_role_contract


def _load_holdout_items(ref):
    """Load holdout items via git show without leaking plaintext to stdout beyond test assertions."""
    try:
        r = subprocess.run(["git", "show", ref], capture_output=True, text=True, check=False)
        if r.returncode != 0 or not r.stdout.strip():
            return []
        return [json.loads(l) for l in r.stdout.splitlines() if l.strip()]
    except Exception:
        return []


class Cycle2DevSetTest(unittest.TestCase):
    def setUp(self):
        self.path = pathlib.Path(__file__).with_name("retrieval-v2") / "cycle2" / "dev" / "evalset.jsonl"
        self.items = [json.loads(l) for l in self.path.read_text(encoding="utf-8").splitlines() if l.strip()]
        self.manifest_path = pathlib.Path(__file__).with_name("retrieval-v2") / "cycle2" / "dev" / "manifest.json"
        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))
        self.audit_path = pathlib.Path(__file__).with_name("retrieval-v2") / "cycle2" / "dev" / "annotation_audit.json"

    def test_36_cases(self):
        self.assertEqual(36, len(self.items))

    def test_18_youth_18_gov24(self):
        youth = sum(1 for x in self.items if x["gold_source"] == "youth")
        gov24 = sum(1 for x in self.items if x["gold_source"] == "gov24")
        self.assertEqual(18, youth)
        self.assertEqual(18, gov24)

    def test_case_id_sequential(self):
        expected = [f"c2d-{i:03d}" for i in range(1, 37)]
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
                        p0_gold.add(str(gid))
        dev_gold = set(str(x["gold_source_id"]) for x in self.items)
        self.assertEqual(set(), dev_gold & p0_gold)

    def test_no_query_overlap_with_cycle1_dev(self):
        dev_path = pathlib.Path("eval/retrieval-v2/dev/evalset.jsonl")
        if dev_path.exists():
            dev_q = set(json.loads(l)["query"].strip() for l in dev_path.read_text(encoding="utf-8").splitlines() if l.strip() and json.loads(l).get("query"))
            cur_q = set(x["query"].strip() for x in self.items)
            self.assertEqual(set(), cur_q & dev_q)

    def test_no_gold_overlap_with_cycle1_dev(self):
        dev_path = pathlib.Path("eval/retrieval-v2/dev/evalset.jsonl")
        if dev_path.exists():
            dev_gold = set(str(json.loads(l)["gold_source_id"]) for l in dev_path.read_text(encoding="utf-8").splitlines() if l.strip())
            cur_gold = set(str(x["gold_source_id"]) for x in self.items)
            self.assertEqual(set(), cur_gold & dev_gold)

    def test_no_query_overlap_with_cycle1_holdout(self):
        # try filesystem first, then git
        c1h_items = []
        p = pathlib.Path("eval/retrieval-v2/holdout/evalset.jsonl")
        if p.exists():
            c1h_items = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        else:
            c1h_items = _load_holdout_items("12515a20758265b0b5a5f52acef5aa40de3b6253:eval/retrieval-v2/holdout/evalset.jsonl")
            if not c1h_items:
                c1h_items = _load_holdout_items("HEAD:eval/retrieval-v2/holdout/evalset.jsonl")
        if c1h_items:
            c1h_q = set(x["query"].strip() for x in c1h_items)
            cur_q = set(x["query"].strip() for x in self.items)
            self.assertEqual(set(), cur_q & c1h_q)

    def test_no_gold_overlap_with_cycle1_holdout(self):
        c1h_items = []
        p = pathlib.Path("eval/retrieval-v2/holdout/evalset.jsonl")
        if p.exists():
            c1h_items = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        else:
            c1h_items = _load_holdout_items("12515a20758265b0b5a5f52acef5aa40de3b6253:eval/retrieval-v2/holdout/evalset.jsonl")
        if c1h_items:
            c1h_gold = set(str(x["gold_source_id"]) for x in c1h_items)
            cur_gold = set(str(x["gold_source_id"]) for x in self.items)
            self.assertEqual(set(), cur_gold & c1h_gold)

    def test_no_query_overlap_with_cycle2_holdout(self):
        # filesystem absent on candidate branch; use git
        c2h_items = []
        p = pathlib.Path("eval/retrieval-v2/cycle2/holdout/evalset.jsonl")
        if p.exists():
            c2h_items = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        else:
            c2h_items = _load_holdout_items("9e2cd6ea4b8203b474d7d6a6a69a088763284043:eval/retrieval-v2/cycle2/holdout/evalset.jsonl")
            if not c2h_items:
                c2h_items = _load_holdout_items("origin/codex/retrieval-v2-cycle2-holdout-freeze:eval/retrieval-v2/cycle2/holdout/evalset.jsonl")
        if c2h_items:
            c2h_q = set(x["query"].strip() for x in c2h_items)
            cur_q = set(x["query"].strip() for x in self.items)
            self.assertEqual(set(), cur_q & c2h_q)

    def test_no_gold_overlap_with_cycle2_holdout(self):
        c2h_items = []
        p = pathlib.Path("eval/retrieval-v2/cycle2/holdout/evalset.jsonl")
        if p.exists():
            c2h_items = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]
        else:
            c2h_items = _load_holdout_items("9e2cd6ea4b8203b474d7d6a6a69a088763284043:eval/retrieval-v2/cycle2/holdout/evalset.jsonl")
        if c2h_items:
            c2h_gold = set(str(x["gold_source_id"]) for x in c2h_items)
            cur_gold = set(str(x["gold_source_id"]) for x in self.items)
            self.assertEqual(set(), cur_gold & c2h_gold)

    def test_no_query_overlap_with_hard_negative(self):
        hn_q = set()
        for p in [pathlib.Path("eval/expansion_api_evalset.jsonl")]:
            if p.exists():
                hn_q |= set(json.loads(l)["query"].strip() for l in p.read_text(encoding="utf-8").splitlines() if l.strip() and json.loads(l).get("query"))
        # also canonical hard-negative json
        hn_json_path = pathlib.Path("eval/canonical_hard_negative_36_production_parity.json")
        if hn_json_path.exists():
            hn_json = json.loads(hn_json_path.read_text(encoding="utf-8"))
            for c in hn_json.get("cases", []):
                if c.get("query"):
                    hn_q.add(c["query"].strip())
        cur_q = set(x["query"].strip() for x in self.items)
        self.assertEqual(set(), cur_q & hn_q)

    def test_no_gold_overlap_with_hard_negative(self):
        hn_gold = set()
        for p in [pathlib.Path("eval/expansion_api_evalset.jsonl")]:
            if p.exists():
                for l in p.read_text(encoding="utf-8").splitlines():
                    if not l.strip():
                        continue
                    j = json.loads(l)
                    if j.get("gold_source_id"):
                        hn_gold.add(str(j["gold_source_id"]))
        hn_json_path = pathlib.Path("eval/canonical_hard_negative_36_production_parity.json")
        if hn_json_path.exists():
            hn_json = json.loads(hn_json_path.read_text(encoding="utf-8"))
            for c in hn_json.get("cases", []):
                if c.get("gold_source_id"):
                    hn_gold.add(str(c["gold_source_id"]))
        cur_gold = set(str(x["gold_source_id"]) for x in self.items)
        self.assertEqual(set(), cur_gold & hn_gold)

    def test_manifest_exists_and_valid(self):
        self.assertTrue(self.manifest_path.exists())
        self.assertEqual("dev", self.manifest["role"])
        self.assertEqual(2, self.manifest["cycle"])
        self.assertEqual("D-007", self.manifest["contract"])
        self.assertEqual(36, self.manifest["cases"])
        self.assertEqual(18, self.manifest["youth"])
        self.assertEqual(18, self.manifest["gov24"])
        self.assertEqual(36, self.manifest["by_source"]["youth"] + self.manifest["by_source"]["gov24"])
        cat_counts = self.manifest["category_counts"]
        self.assertEqual(36, sum(cat_counts.values()))
        expected_cats = {"housing_finance", "family_care", "employment_education", "culture_community", "welfare_health", "business_agriculture"}
        self.assertEqual(expected_cats, set(cat_counts.keys()))
        for k, v in cat_counts.items():
            self.assertEqual(6, v, f"category {k} must be exactly 6 for balanced dev")
        # per-category youth/gov balance 3/3
        from collections import Counter
        cat_youth = Counter()
        cat_gov = Counter()
        for x in self.items:
            if x["gold_source"] == "youth":
                cat_youth[x["category"]] += 1
            else:
                cat_gov[x["category"]] += 1
        for cat in expected_cats:
            self.assertEqual(3, cat_youth[cat], f"category {cat} youth must be 3")
            self.assertEqual(3, cat_gov[cat], f"category {cat} gov24 must be 3")
        self.assertIn("sha256", self.manifest)
        self.assertEqual("utf8_text_lf_normalized", self.manifest["sha256_basis"])
        data = self.path.read_bytes().decode("utf-8").replace("\r\n", "\n").encode("utf-8")
        actual_sha = hashlib.sha256(data).hexdigest()
        self.assertEqual(actual_sha, self.manifest["sha256"])
        self.assertEqual("2fb6627cfbac431ad4175cc383a88c8621d1dd2c", self.manifest["base_commit"])
        self.assertFalse(self.manifest["retrieval_observed"])
        self.assertFalse(self.manifest["candidate_tuning_started"])
        self.assertFalse(self.manifest["cycle1_candidate_results_used_for_case_selection"])
        self.assertTrue(self.manifest["cycle1_holdout_accessed_for_collision_audit"])
        self.assertTrue(self.manifest["cycle2_holdout_accessed_for_collision_audit"])
        self.assertEqual(0, self.manifest["p0_query_overlap"])
        self.assertEqual(0, self.manifest["p0_gold_overlap"])
        self.assertEqual(0, self.manifest["dev_query_overlap"])
        self.assertEqual(0, self.manifest["dev_gold_overlap"])
        self.assertEqual(0, self.manifest["cycle1_holdout_query_overlap"])
        self.assertEqual(0, self.manifest["cycle1_holdout_gold_overlap"])
        self.assertEqual(0, self.manifest["cycle2_holdout_query_overlap"])
        self.assertEqual(0, self.manifest["cycle2_holdout_gold_overlap"])
        self.assertEqual(0, self.manifest["hard_negative_query_overlap"])
        self.assertEqual(0, self.manifest["hard_negative_gold_overlap"])
        self.assertTrue(self.manifest["frozen_before_tuning"])
        self.assertTrue(self.manifest["frozen_before_tuning_verified"])
        self.assertEqual("pass", self.manifest["annotation_audit_status"])

    def test_annotation_audit_consistency(self):
        self.assertTrue(self.audit_path.exists(), "annotation_audit.json must exist")
        audit = json.loads(self.audit_path.read_text(encoding="utf-8"))
        self.assertEqual(36, audit["cases"])
        self.assertEqual(36, audit["well_posed_gold"])
        self.assertEqual(0, audit["ambiguous_gold"])
        self.assertEqual(0, audit["p0_query_overlap"])
        self.assertEqual(0, audit["p0_gold_overlap"])
        self.assertEqual(0, audit["dev_query_overlap"])
        self.assertEqual(0, audit["dev_gold_overlap"])
        self.assertEqual(0, audit["cycle1_holdout_query_overlap"])
        self.assertEqual(0, audit["cycle1_holdout_gold_overlap"])
        self.assertEqual(0, audit["cycle2_holdout_query_overlap"])
        self.assertEqual(0, audit["cycle2_holdout_gold_overlap"])
        self.assertEqual(0, audit["hard_negative_query_overlap"])
        self.assertEqual(0, audit["hard_negative_gold_overlap"])
        self.assertTrue(audit["cycle1_holdout_accessed_for_collision_audit"])
        self.assertTrue(audit["cycle2_holdout_accessed_for_collision_audit"])
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
            self.assertIn("competing_policy_count", a)

    def test_lf_normalized(self):
        raw = self.path.read_bytes()
        self.assertNotIn(b"\r\n", raw, "evalset must be LF normalized, no CRLF")
        self.assertNotIn(b"\r", raw, "evalset must be LF normalized")

    def test_gold_source_valid(self):
        for x in self.items:
            self.assertIn(x["gold_source"], ["youth", "gov24"])
            self.assertTrue(str(x["gold_source_id"]).strip())
            self.assertTrue(x["category"].strip())
            self.assertTrue(x["query"].strip())
            self.assertTrue(x.get("gold_title", "").strip() if "gold_title" in x else True)


if __name__ == "__main__":
    unittest.main()
