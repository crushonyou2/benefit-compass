import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

PREREG_JSON = pathlib.Path(__file__).with_name("retrieval-v2") / "cycle3" / "prereg-v1.json"
PREREG_MD = pathlib.Path(__file__).parent.parent / "docs" / "RETRIEVAL_V2_CYCLE3_PREREG.md"

class Cycle3PreregTest(unittest.TestCase):
    def setUp(self):
        self.assertTrue(PREREG_JSON.exists(), f"missing {PREREG_JSON}")
        self.data = json.loads(PREREG_JSON.read_text(encoding="utf-8"))
        self.md = PREREG_MD.read_text(encoding="utf-8") if PREREG_MD.exists() else ""

    def test_schema_and_version(self):
        self.assertEqual(1, self.data["schema_version"])
        self.assertEqual("v1", self.data["prereg_version"])
        self.assertEqual(3, self.data["cycle"])
        self.assertEqual("BOOTSTRAPPED", self.data["status"])

    def test_base_commit_and_tag(self):
        self.assertEqual("5cabd2eecd78923da4751c5e60fa316e74f563fc", self.data["base_commit"])
        self.assertEqual("codex/retrieval-v2-cycle2-candidate", self.data["base_branch"])
        self.assertEqual("codex/retrieval-v2-cycle3-start", self.data["bootstrap_branch"])
        self.assertEqual("retrieval-v2-cycle3-start-v1", self.data["bootstrap_tag"])

    def test_max_experiments_exactly_3(self):
        self.assertEqual(3, self.data["max_candidate_experiments"])
        self.assertTrue(self.data["immutable_after_dev_inspection"])
        self.assertTrue(self.data["single_canonical_dev_batch"])
        cands = self.data["candidates"]
        self.assertEqual(3, len(cands))
        ids = [c["candidate_id"] for c in cands]
        self.assertEqual(["c3e1-vector-pool-128", "c3e2-vector-pool-256", "c3e3-vector-pool-512"], ids)
        ks = [c["pool_k"] for c in cands]
        self.assertEqual([128, 256, 512], ks)
        for c in cands:
            self.assertEqual(30, c["final_n"])
            self.assertEqual(False, c["region_search"])
            self.assertEqual(0, c["rerank"])
            self.assertEqual(0.78, c["cosine_min"])
            self.assertEqual(0.01, c["lexical_bias"])
            self.assertIn("lexical_overlap_terms_rewrite", c["lexical_terms"])
            self.assertIn("strip_region", c["lexical_terms"])

    def test_sql_semantics_spec(self):
        sql = self.data["sql_semantics"]
        self.assertIn("eligible", sql["description"])
        self.assertIn("vector-pool", sql["description"])
        self.assertEqual([128, 256, 512], sql["candidate_pool_ks"])
        self.assertEqual(30, sql["final_n"])
        self.assertIsNone(sql["rp_binding"])
        self.assertIn("nearest_cte", sql)
        self.assertIn("vector_pool_cte", sql)
        self.assertIn("lexical_cte", sql)
        self.assertIn("template_sql", sql)
        tmpl = sql["template_sql"]
        self.assertIn("WITH nearest AS", tmpl)
        self.assertIn("vector_pool AS", tmpl)
        self.assertIn("lexical AS", tmpl)
        self.assertIn("LIMIT %(pool_k)s", tmpl)
        self.assertIn("LIMIT %(n)s", tmpl)
        self.assertIn("lexical_overlap", tmpl)
        self.assertIn("youth_bias", tmpl)
        self.assertIn("lexical_bias", tmpl)
        # Must exclude public region search / rerank / global threshold
        self.assertIn("cross-encoder", str(sql["rejected_alternatives"]))
        self.assertNotIn("RERANK=1", tmpl)

    def test_dev_selection_rule(self):
        rule = self.data["dev_selection_rule"]
        self.assertEqual(36, rule["same_fresh_dev"])
        self.assertTrue(rule["same_query_set_for_latency"])
        qsel = rule["quality_selectable_all_required"]
        self.assertEqual(4, len(qsel))
        self.assertTrue(any("source-macro" in s for s in qsel))
        self.assertTrue(any("net hit@5" in s for s in qsel))
        self.assertTrue(any("Youth" in s for s in qsel))
        self.assertTrue(any("Gov24" in s for s in qsel))
        lg = rule["latency_gate"]
        self.assertIn("p95", lg["metric"])
        self.assertIn("candidate p95 <= paired baseline p95", lg["required"])
        self.assertIn("same-process", lg["methodology"])
        self.assertEqual(["higher net hit@5", "higher source-macro R@5", "lower candidate-baseline p95 delta", "smaller pre-pool K (128 < 256 < 512)"], rule["tie_break"])
        self.assertIn("without holdout evaluation", rule["if_none_dev_selectable"])
        self.assertIn("independent review", rule["holdout_gating"])

    def test_production_contract_unchanged(self):
        pc = self.data["production_contract"]
        self.assertEqual(0, pc["RERANK"])
        self.assertEqual(30, pc["CANDIDATES"])
        self.assertEqual(0.78, pc["COSINE_MIN"])
        self.assertEqual(0.01, pc["LEXICAL_BIAS"])
        self.assertEqual(False, pc["public_region_search"])
        self.assertEqual(False, pc["rerank"])
        self.assertIsNone(pc["global_threshold"])

    def test_audit_and_fingerprint_spec_present(self):
        self.assertIn("audit_log", self.data)
        self.assertIn("fingerprint", self.data)
        self.assertEqual("eval/retrieval_v2/cycle3_audit.py", self.data["audit_log"]["module"])
        self.assertEqual("eval/retrieval_v2/cycle3_fingerprint.py", self.data["fingerprint"]["module"])
        self.assertIn("SHA256", self.data["fingerprint"]["query_fingerprint"])
        self.assertIn("NUL", self.data["fingerprint"]["gold_fingerprint"])

    def test_markdown_contains_required_sections(self):
        self.assertTrue(PREREG_MD.exists())
        md_low = self.md.lower()
        for needle in [
            "c3e1-vector-pool-128",
            "c3e2-vector-pool-256",
            "c3e3-vector-pool-512",
            "vector_pool",
            "lexical",
            "candidates=30",
            "public region search",
            "d-004",
            "d-007",
            "dev_selectable",
            "tie-break",
            "bootstrapped",
        ]:
            self.assertIn(needle.lower(), md_low, f"markdown missing {needle!r}")

    def test_no_retrieval_execution_in_prereg(self):
        # Prereg must not claim any retrieval result numeric counts; spec names like hit@5 are allowed
        # Ensure no dev/holdout SHA is filled (pending) and no actual hit counts
        self.assertEqual("PENDING_FRESH_CREATION", self.data["dev_set"]["status"])
        self.assertEqual("PENDING_FRESH_CREATION", self.data["holdout_set"]["status"])
        # Ensure no numeric hit result like "33/40" or "30/36" appears as a claimed result (spec may mention generic net+2)
        blob = json.dumps(self.data)
        # If a real dev holdout result were embedded, it would contain R@5 numeric metrics with hit counts; forbid those patterns
        self.assertNotIn("33/40", blob)
        self.assertNotIn("36/40", blob)

    def test_decision_and_contract(self):
        self.assertEqual("D-011", self.data["decision"])
        self.assertEqual("D-007", self.data["contract"])
