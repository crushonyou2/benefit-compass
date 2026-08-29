import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
from retrieval_v2.provenance import canonical_text_sha256


MANIFEST = ROOT / "eval" / "retrieval-v2" / "candidate" / "manifest.json"
ARTIFACT = ROOT / "eval" / "retrieval-v2" / "experiments" / "lexical-rewrite-v1.json"
CANDIDATE_MODULE = ROOT / "eval" / "retrieval_v2" / "candidate_lexical_rewrite.py"
RUNNER = ROOT / "eval" / "retrieval_v2" / "run_candidate_lexical_rewrite.py"
UNIT_TEST = ROOT / "eval" / "test_candidate_lexical_rewrite.py"


class CandidateFreezeTest(unittest.TestCase):
    def test_manifest_role_and_flags(self):
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(m["role"], "candidate")
        self.assertEqual(m["name"], "lexical-rewrite-v1")
        self.assertEqual(m["contract"], "D-007")
        self.assertEqual(m["base_commit"], "9048347caed1074619763c51bcbc4e35e7e60363")
        self.assertTrue(m["candidate_frozen"])
        self.assertFalse(m["holdout_observed"])
        self.assertFalse(m["p0_used_for_tuning"])
        self.assertFalse(m["challenge_used_for_tuning"])
        self.assertFalse(m["production_modified"])
        # precise admin residue semantics must be documented
        self.assertIn("admin_residue_particles", m["candidate_config"])
        self.assertEqual(m["candidate_config"]["admin_residue_particles"], ["에서", "에", "의", "으로", "로"])
        # runner description must be precise: pre-strip only
        self.assertIn("checked only before particle strip", m["candidate_config"]["normalization_rule"])

    def test_manifest_dev_sha(self):
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(m["dev_sha256"], "e9510203cb26bb9db5598b1cd284398ba226460437a396e72906aa6505aff56e")
        self.assertEqual(m["dev_eval_file"], "eval/retrieval-v2/dev/evalset.jsonl")
        actual = canonical_text_sha256(ROOT / m["dev_eval_file"])
        self.assertEqual(actual, m["dev_sha256"])
        self.assertEqual(m["sha256_basis"], "utf8_text_lf_normalized")

    def test_artifact_metrics_exact_match(self):
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        j = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        self.assertEqual(j["candidate_metrics"]["hit@5"], 35)
        self.assertAlmostEqual(j["candidate_metrics"]["recall@5"], 0.9722, places=4)
        self.assertAlmostEqual(j["candidate_metrics"]["recall@1"], 0.75, places=4)
        self.assertAlmostEqual(j["candidate_metrics"]["mrr@10"], 0.8452, places=4)
        self.assertEqual(j["candidate_metrics"]["recall@10"], 1.0)
        self.assertEqual(j["candidate_metrics"]["source_macro_recall@5"], 0.9722)
        self.assertEqual(j["candidate_metrics"]["by_source"]["gov24"]["hit@5"], 18)
        self.assertEqual(j["candidate_metrics"]["by_source"]["youth"]["hit@5"], 17)
        self.assertEqual(j["baseline"]["hit@5"], 33)
        self.assertEqual(j["net_hit@5"], 2)
        self.assertEqual(len(j["losses"]), 0)
        self.assertEqual(j["target_ranks"]["dev-009"]["candidate_rank"], 7)
        self.assertEqual(j["target_ranks"]["dev-015"]["candidate_rank"], 5)
        self.assertEqual(j["target_ranks"]["dev-034"]["candidate_rank"], 4)
        self.assertEqual(m["dev_metrics"]["R@5"], 0.9722)
        self.assertEqual(m["dev_metrics"]["hit@5"], "35/36")
        self.assertEqual(m["dev_metrics"]["R@1"], 0.75)
        self.assertEqual(m["dev_metrics"]["MRR@10"], 0.8452)
        self.assertEqual(m["dev_metrics"]["Gov24"], "18/18")
        self.assertEqual(m["dev_metrics"]["Youth"], "17/18")
        self.assertEqual(m["dev_metrics"]["net_hit@5"], 2)
        self.assertEqual(m["dev_metrics"]["losses"], 0)

    def test_artifact_config_equals_module(self):
        sys.path.insert(0, str(ROOT / "ml-service"))
        from retrieval_v2.candidate_lexical_rewrite import ADMIN_RESIDUE_PARTICLES, ADMIN_UNITS, MIN_STEM_LEN, PARTICLES, RESIDUE_PURE
        j = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        cfg = j["candidate_config"]
        self.assertEqual(cfg["particles"], PARTICLES)
        self.assertEqual(cfg["min_stem_len"], MIN_STEM_LEN)
        self.assertEqual(sorted(cfg["residue_pure"]), sorted(RESIDUE_PURE))
        self.assertEqual(cfg["admin_units"], ADMIN_UNITS)
        self.assertEqual(cfg["admin_residue_particles"], ADMIN_RESIDUE_PARTICLES)
        self.assertEqual(cfg["lexical_terms"], "lexical_overlap_terms_rewrite")
        self.assertEqual(cfg["strip_region"], "unchanged")
        self.assertFalse(cfg["verb_expansion"])
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(m["candidate_config"], cfg)
        # production contract must include youth/gov24 and rerank 0
        pc = j["production_contract"]
        self.assertEqual(pc["rerank"], 0)
        self.assertEqual(pc["candidates"], 30)
        self.assertAlmostEqual(pc["bi_encoder_min_score"], 0.78)
        self.assertEqual(pc["gov24_org_suppression"], True)
        self.assertAlmostEqual(pc["youth_intent_bias"], 0.015)
        # also check provenance clean
        self.assertEqual(j["git_dirty"], False)
        # manifest artifact_provenance must match artifact
        self.assertEqual(m["artifact_provenance"]["git_commit"], j["git_commit"])
        self.assertEqual(m["artifact_provenance"]["git_dirty"], False)

    def test_file_hashes_match(self):
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(canonical_text_sha256(CANDIDATE_MODULE), m["sha256"]["candidate_module"])
        self.assertEqual(canonical_text_sha256(RUNNER), m["sha256"]["runner"])
        self.assertEqual(canonical_text_sha256(UNIT_TEST), m["sha256"]["unit_test"])
        self.assertEqual(canonical_text_sha256(ARTIFACT), m["sha256"]["dev_result"])
        # also check dev_result hash matches clean generation commit
        j = json.loads(ARTIFACT.read_text(encoding="utf-8"))
        self.assertEqual(j["git_commit"], "c6c082681b4f2fcd521790e50c5fd46549116307")
        self.assertFalse(j["git_dirty"])

    def test_rejected_not_in_manifest(self):
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        text = json.dumps(m, ensure_ascii=False)
        for bad in ["candidate_rrf", "run_candidate_rrf", "candidate_lexical_normalization", "lexical-normalization-v1", "rrf-v1"]:
            self.assertNotIn(bad, text, f"rejected {bad} should not be in manifest")
        self.assertEqual(m["candidate_module"], "eval/retrieval_v2/candidate_lexical_rewrite.py")
        self.assertEqual(m["runner"], "eval/retrieval_v2/run_candidate_lexical_rewrite.py")
        self.assertEqual(m["unit_test"], "eval/test_candidate_lexical_rewrite.py")
        self.assertEqual(m["dev_result"], "eval/retrieval-v2/experiments/lexical-rewrite-v1.json")

    def test_production_namespace_intact(self):
        m = json.loads(MANIFEST.read_text(encoding="utf-8"))
        self.assertFalse(m["production_modified"])
        dump = json.dumps(m)
        # manifest should not reference canonical artifact path (lowercase canonical)
        # but normalization_rule may contain no canonical; check no canonical path like eval/canonical
        self.assertNotIn("eval/canonical", dump)
        self.assertFalse(m["holdout_observed"])
        self.assertFalse((ROOT / "eval" / "retrieval-v2" / "holdout" / "evalset.jsonl").exists())
        self.assertEqual(m["corpus"]["total_policies"], 13589)
        self.assertEqual(m["corpus"]["total_chunks"], 17609)


if __name__ == "__main__":
    unittest.main()
