import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from retrieval_v2.candidate_lexical_rewrite import (
    ADMIN_UNITS,
    MIN_STEM_LEN,
    PARTICLES,
    RESIDUE_PURE,
    lexical_overlap_terms_rewrite,
)


class LexicalRewriteTest(unittest.TestCase):
    def test_particle_replacement_not_additive(self):
        # "학교에서" should become "학교" only, not both
        terms = lexical_overlap_terms_rewrite("학교에서 공부")
        self.assertIn("학교", terms)
        self.assertNotIn("학교에서", terms)
        self.assertEqual(len(terms), len(set(terms)))

    def test_stopword_stem_dropped(self):
        # "지원을" -> stem "지원" is stopword, so whole term dropped
        terms = lexical_overlap_terms_rewrite("지원을 받기")
        self.assertNotIn("지원을", terms)
        self.assertNotIn("지원", terms)

    def test_residue_dropped(self):
        terms = lexical_overlap_terms_rewrite("에서 혜택을")
        self.assertNotIn("에서", terms)
        self.assertNotIn("에", terms)
        # "혜택을" -> "혜택" should remain
        self.assertIn("혜택", terms)

    def test_admin_unit_residue(self):
        terms = lexical_overlap_terms_rewrite("시에서 혜택")
        self.assertNotIn("시에서", terms)
        self.assertNotIn("시", terms)
        terms2 = lexical_overlap_terms_rewrite("광역시 혜택")
        self.assertNotIn("광역시", terms2)

    def test_proper_noun_preserved(self):
        terms = lexical_overlap_terms_rewrite("태안군에서 혜택")
        self.assertIn("태안군", terms)
        self.assertNotIn("태안군에서", terms)

    def test_no_double_counting(self):
        q = "직업계고를 졸업하고"
        terms = lexical_overlap_terms_rewrite(q)
        # Check no duplicate via set
        self.assertEqual(len(terms), len(set(terms)))
        # If stripping happened, original+suffix not both present
        if "직업계고" in terms:
            self.assertNotIn("직업계고를", terms)

    def test_short_token_handling(self):
        terms = lexical_overlap_terms_rewrite("AI 가")
        self.assertNotIn("가", terms)
        self.assertIn("AI", terms)  # "AI" len 2, not stopword, kept
        self.assertEqual([], [t for t in terms if len(t) < 2])

    def test_no_additive(self):
        q = "출생축하금을 지원"
        terms = lexical_overlap_terms_rewrite(q)
        # Should not contain both original and stem
        self.assertNotIn("출생축하금을", terms)
        self.assertIn("출생축하금", terms)


class LexicalRewriteProvenanceTest(unittest.TestCase):
    ARTIFACT = pathlib.Path(__file__).resolve().parent / "retrieval-v2" / "experiments" / "lexical-rewrite-v1.json"

    def test_artifact_particles_match_module(self):
        cfg = json.loads(self.ARTIFACT.read_text(encoding="utf-8"))["candidate_config"]
        self.assertEqual(cfg["particles"], PARTICLES, "artifact particles must equal candidate module PARTICLES (22)")
        self.assertEqual(len(cfg["particles"]), 22)
        self.assertIn("에게서", cfg["particles"])
        self.assertIn("으로부터", cfg["particles"])
        self.assertIn("한테", cfg["particles"])

    def test_artifact_min_stem_and_residue_match_module(self):
        cfg = json.loads(self.ARTIFACT.read_text(encoding="utf-8"))["candidate_config"]
        self.assertEqual(cfg["min_stem_len"], MIN_STEM_LEN)
        self.assertEqual(sorted(cfg["residue_pure"]), sorted(RESIDUE_PURE))
        self.assertEqual(cfg["admin_units"], ADMIN_UNITS)
        self.assertEqual(cfg["lexical_terms"], "lexical_overlap_terms_rewrite")
        self.assertEqual(cfg["strip_region"], "unchanged")
        self.assertFalse(cfg["verb_expansion"])

    def test_artifact_metrics_unchanged(self):
        j = json.loads(self.ARTIFACT.read_text(encoding="utf-8"))
        # metrics provenance fix must not change retrieval results
        self.assertEqual(j["candidate_metrics"]["hit@5"], 35)
        self.assertAlmostEqual(j["candidate_metrics"]["recall@5"], 0.9722, places=4)
        self.assertEqual(j["candidate_metrics"]["hit@10"], 36)
        self.assertAlmostEqual(j["candidate_metrics"]["mrr@10"], 0.8452, places=4)
        self.assertEqual(j["baseline"]["hit@5"], 33)
        self.assertEqual(j["net_hit@5"], 2)
        self.assertEqual(len(j["losses"]), 0)
        self.assertEqual(len(j["gains"]), 2)
        self.assertEqual(j["candidate_metrics"]["by_source"]["gov24"]["hit@5"], 18)
        self.assertEqual(j["candidate_metrics"]["by_source"]["youth"]["hit@5"], 17)
        self.assertEqual(j["target_ranks"]["dev-009"]["candidate_rank"], 7)
        self.assertEqual(j["target_ranks"]["dev-015"]["candidate_rank"], 5)
        self.assertEqual(j["target_ranks"]["dev-034"]["candidate_rank"], 4)

    def test_runner_has_no_duplicated_config(self):
        runner = pathlib.Path(__file__).resolve().parent / "retrieval_v2" / "run_candidate_lexical_rewrite.py"
        txt = runner.read_text(encoding="utf-8")
        self.assertNotIn("ALLOWED_SUFFIXES", txt, "runner must not contain duplicated ALLOWED_SUFFIXES")
        # must import actual constants
        self.assertIn("from retrieval_v2.candidate_lexical_rewrite import", txt)
        self.assertIn("PARTICLES", txt)
        self.assertIn("MIN_STEM_LEN", txt)
        self.assertIn("RESIDUE_PURE", txt)
        self.assertIn("ADMIN_UNITS", txt)


if __name__ == "__main__":
    unittest.main()
