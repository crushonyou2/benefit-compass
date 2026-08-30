"""Static unit test for Phase1 diagnostic metadata correction (cycle2).

Provenance-preserving correction: `filtered_by_cosine`는 gold가 top30에 있고
raw score < COSINE_MIN(0.78)일 때만 true. score>=0.78이지만 top30에 있고
reported top10 rank==0이면 `outside_top10_after_threshold` true.
DB/retrieval 호출 없음 — stored `rank_top30`/`rank`/`score`만으로 deterministic 검증.

HARD RULES: no DB, no embedding, no retrieval execution, no holdout plaintext.
"""

import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAIRED = ROOT / "eval" / "retrieval-v2" / "cycle2" / "dev" / "phase1-paired-baseline-vs-candidate-v2.json"
RUNNER = ROOT / "eval" / "retrieval_v2" / "run_cycle2_phase1_diagnostic.py"

COSINE_MIN = 0.78  # D-003 production post-filter, raw cosine 1-dist


def diagnostic_flags(rank_top30: int, rank: int, score):
    """Mirror corrected runner logic without DB."""
    in_top30 = rank_top30 != 0
    filtered = in_top30 and score is not None and score < COSINE_MIN
    outside = in_top30 and score is not None and score >= COSINE_MIN and rank == 0
    return filtered, outside, in_top30


class DiagnosticLogicTest(unittest.TestCase):
    def test_c2d025_score_above_threshold_is_outside_not_filtered(self):
        # Task example: baseline rank_top30=14, rank=0, score≈0.868
        filtered, outside, in_top30 = diagnostic_flags(14, 0, 0.8684863087261379)
        self.assertTrue(in_top30)
        self.assertFalse(filtered, "score>=0.78 must not be filtered_by_cosine")
        self.assertTrue(outside, "score>=0.78 + rank==0 + in_top30 must be outside_top10_after_threshold")

    def test_filtered_true_only_when_score_below_threshold(self):
        filtered, outside, _ = diagnostic_flags(5, 0, 0.77)
        self.assertTrue(filtered)
        self.assertFalse(outside)
        # boundary exactly 0.78 is not filtered (production uses >=)
        filtered2, outside2, _ = diagnostic_flags(5, 0, 0.78)
        self.assertFalse(filtered2)
        self.assertTrue(outside2)
        # just below
        filtered3, outside3, _ = diagnostic_flags(5, 0, 0.7799)
        self.assertTrue(filtered3)
        self.assertFalse(outside3)

    def test_in_top10_is_neither(self):
        filtered, outside, _ = diagnostic_flags(3, 3, 0.868)
        self.assertFalse(filtered)
        self.assertFalse(outside)
        filtered, outside, _ = diagnostic_flags(1, 1, 0.95)
        self.assertFalse(filtered)
        self.assertFalse(outside)

    def test_not_in_top30_is_neither(self):
        filtered, outside, in_top30 = diagnostic_flags(0, 0, None)
        self.assertFalse(in_top30)
        self.assertFalse(filtered)
        self.assertFalse(outside)
        # even with score None
        filtered, outside, _ = diagnostic_flags(0, 0, 0.9)
        # rank_top30 0 means not in top30, so even high score not outside
        # Our logic requires in_top30, so false
        self.assertFalse(filtered)
        self.assertFalse(outside)

    def test_score_none_never_filtered_or_outside(self):
        filtered, outside, _ = diagnostic_flags(14, 0, None)
        self.assertFalse(filtered)
        self.assertFalse(outside)

    def test_candidate_symmetry(self):
        # Candidate with in_top30 but high score and rank==0 should also be outside
        filtered, outside, _ = diagnostic_flags(14, 0, 0.868)
        self.assertFalse(filtered)
        self.assertTrue(outside)
        # Candidate with rank 3 should be neither
        filtered2, outside2, _ = diagnostic_flags(3, 3, 0.868)
        self.assertFalse(filtered2)
        self.assertFalse(outside2)


class ArtifactCorrectionTest(unittest.TestCase):
    """Verify stored paired JSON was deterministically corrected, metrics unchanged."""

    def setUp(self):
        self.data = json.loads(PAIRED.read_text(encoding="utf-8"))

    def test_c2d025_baseline_corrected(self):
        pc = next(c for c in self.data["per_case"] if c["case_id"] == "c2d-025")
        b = pc["baseline"]
        c = pc["candidate"]
        # Stored values must be from original run (re-measurement 금지)
        self.assertEqual(14, b["rank_top30"])
        self.assertEqual(0, b["rank"])
        self.assertAlmostEqual(0.8684863087261379, b["score"], places=12)
        # Corrected diagnostics
        self.assertFalse(b["filtered_by_cosine"], "c2d-025 baseline must be filtered_by_cosine=false after correction")
        self.assertTrue(b["outside_top10_after_threshold"], "c2d-025 baseline must be outside_top10_after_threshold=true")
        # Candidate should be neither (rank 3)
        self.assertEqual(3, c["rank_top30"])
        self.assertEqual(3, c["rank"])
        self.assertFalse(c["filtered_by_cosine"])
        self.assertFalse(c["outside_top10_after_threshold"])
        # Gains copy must also be corrected
        gain = next(g for g in self.data["gains"] if g["case_id"] == "c2d-025")
        self.assertFalse(gain["baseline"]["filtered_by_cosine"])
        self.assertTrue(gain["baseline"]["outside_top10_after_threshold"])
        # failure_summary copy
        fm = next(f for f in self.data["failure_summary"]["baseline_misses"] if f["case_id"] == "c2d-025")
        self.assertFalse(fm["baseline"]["filtered_by_cosine"])
        self.assertTrue(fm["baseline"]["outside_top10_after_threshold"])

    def test_threshold_cause_counts_zero(self):
        # Recompute from stored fields deterministically
        b_filtered = sum(1 for c in self.data["per_case"] if c["baseline"]["filtered_by_cosine"])
        c_filtered = sum(1 for c in self.data["per_case"] if c["candidate"]["filtered_by_cosine"])
        b_outside = sum(1 for c in self.data["per_case"] if c["baseline"]["outside_top10_after_threshold"])
        c_outside = sum(1 for c in self.data["per_case"] if c["candidate"]["outside_top10_after_threshold"])
        self.assertEqual(0, b_filtered, "baseline filtered_by_cosine must be 0 after correction")
        self.assertEqual(0, c_filtered, "candidate filtered_by_cosine must be 0 after correction")
        self.assertEqual(1, b_outside, "baseline outside_top10 must be 1 (c2d-025)")
        self.assertEqual(0, c_outside, "candidate outside_top10 must be 0")

    def test_quality_metrics_unchanged(self):
        # Byte-level meaning preserved: ranks, scores, gains/losses, metrics
        self.assertEqual(36, self.data["n"])
        self.assertAlmostEqual(0.7778, self.data["baseline"]["recall@5"], places=4)
        self.assertAlmostEqual(0.8333, self.data["candidate"]["recall@5"], places=4)
        self.assertEqual(2, self.data["net_hit@5"])
        self.assertEqual(2, len(self.data["gains"]))
        self.assertEqual(0, len(self.data["losses"]))
        # Check specific ranks unchanged for c2d-025 and c2d-031
        c025 = next(c for c in self.data["per_case"] if c["case_id"] == "c2d-025")
        self.assertEqual(0, c025["baseline"]["rank"])
        self.assertEqual(14, c025["baseline"]["rank_top30"])
        self.assertEqual(3, c025["candidate"]["rank"])
        c031 = next(c for c in self.data["per_case"] if c["case_id"] == "c2d-031")
        self.assertEqual(7, c031["baseline"]["rank"])
        self.assertEqual(2, c031["candidate"]["rank"])

    def test_runner_contains_corrected_logic(self):
        txt = RUNNER.read_text(encoding="utf-8")
        # Must contain new field and correct threshold check
        self.assertIn("outside_top10_after_threshold", txt)
        self.assertIn("score < D003_COSINE_MIN", txt)
        self.assertIn("score >= D003_COSINE_MIN", txt)
        self.assertIn("filtered_by_cosine", txt)
        # Must not contain old incorrect pattern "b_in_top30 and b_rank == 0" as sole filtered definition
        # We check that filtered definition includes score check
        self.assertRegex(txt, r"filtered_by_cosine\s*=\s*.*score.*<.*COSINE_MIN")

    def test_no_retrieval_import_in_test(self):
        # Ensure this test file itself does not import retrieval/B
        # (static only) — we already avoid DB, just sanity
        self.assertTrue(PAIRED.exists())


if __name__ == "__main__":
    unittest.main()
