import json
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
from retrieval_v2.provenance import canonical_text_sha256

HARNESS = ROOT / "eval" / "retrieval_v2" / "run_p0_candidate_gate.py"
CANDIDATE_MANIFEST = ROOT / "eval" / "retrieval-v2" / "candidate" / "manifest.json"
MANIFEST_PATH = ROOT / "eval" / "retrieval-v2" / "p0" / "harness-manifest.json"
FIXED_OUTPUT_POSIX = "eval/retrieval-v2/p0/p0-candidate-v2.json"


def _read_harness_text() -> str:
    return HARNESS.read_text(encoding="utf-8")


class CandidatePinTest(unittest.TestCase):
    def test_pinned_commit_and_tag_present(self):
        txt = _read_harness_text()
        self.assertIn("5745cc3144b519da456b21030d0e0752d1d018ae", txt)
        self.assertIn("retrieval-v2-candidate-v2", txt)
        self.assertIn("c6c082681b4f2fcd521790e50c5fd46549116307", txt)

    def test_candidate_frozen_and_hash_check_present(self):
        txt = _read_harness_text()
        self.assertIn("candidate_frozen", txt)
        self.assertIn("candidate bundle hash mismatch", txt)
        self.assertIn("git diff --quiet", txt)
        self.assertIn("CANDIDATE_BUNDLE_PATHS", txt)

    def test_candidate_module_no_semantics_change(self):
        # harness must import candidate lexical rewrite, not modify semantics
        txt = _read_harness_text()
        self.assertIn("lexical_overlap_terms_rewrite", txt)
        # should not contain baseline lexical terms override
        # harness is candidate-only, should not compute baseline_ranks with lexical_overlap_terms (baseline import would imply baseline DB)
        # It may import youth_source_bias etc but baseline lexical_overlap_terms should not be used for DB scoring
        # Check that baseline retrieval not present
        self.assertNotIn("lexical_overlap_terms(q)", txt)  # baseline helper should not appear; candidate rewrite should be lex_canon only
        self.assertIn("lexical_overlap_terms_rewrite(q)", txt)

    def test_validate_candidate_pin_synthetic(self):
        # synthetic manifest test without git dependency (mock git)
        from retrieval_v2.run_p0_candidate_gate import _validate_candidate_pin

        with tempfile.TemporaryDirectory() as td:
            td_path = pathlib.Path(td)
            # copy real manifest to temp and validate with mocked git rev-parse
            real = json.loads(CANDIDATE_MANIFEST.read_text(encoding="utf-8"))
            tmp_manifest = td_path / "manifest.json"
            tmp_manifest.write_text(json.dumps(real, ensure_ascii=False), encoding="utf-8")
            with mock.patch("retrieval_v2.run_p0_candidate_gate.subprocess.check_output", return_value=b"5745cc3144b519da456b21030d0e0752d1d018ae\n"):
                with mock.patch("retrieval_v2.run_p0_candidate_gate.subprocess.check_call", return_value=0):
                    res = _validate_candidate_pin(
                        candidate_manifest_path=tmp_manifest,
                        expected_artifact_commit="c6c082681b4f2fcd521790e50c5fd46549116307",
                        expected_candidate_commit="5745cc3144b519da456b21030d0e0752d1d018ae",
                        expected_tag="retrieval-v2-candidate-v2",
                    )
                    self.assertEqual(res["candidate_frozen"], True)
            # tampered artifact commit should fail
            tampered = dict(real)
            tampered["artifact_provenance"] = dict(real["artifact_provenance"])
            tampered["artifact_provenance"]["git_commit"] = "0000000000000000000000000000000000000000"
            tmp_tampered = td_path / "tampered.json"
            tmp_tampered.write_text(json.dumps(tampered, ensure_ascii=False), encoding="utf-8")
            with mock.patch("retrieval_v2.run_p0_candidate_gate.subprocess.check_output", return_value=b"5745cc3144b519da456b21030d0e0752d1d018ae\n"):
                with self.assertRaises(SystemExit):
                    _validate_candidate_pin(
                        candidate_manifest_path=tmp_tampered,
                        expected_artifact_commit="c6c082681b4f2fcd521790e50c5fd46549116307",
                        expected_candidate_commit="5745cc3144b519da456b21030d0e0752d1d018ae",
                        expected_tag="retrieval-v2-candidate-v2",
                    )


class D003ContractTest(unittest.TestCase):
    def test_harness_contains_d003_constants(self):
        txt = _read_harness_text()
        self.assertIn("D003_CANDIDATES = 30", txt)
        self.assertIn("D003_COSINE_MIN = 0.78", txt)
        self.assertIn("D003_LEXICAL_BIAS = 0.01", txt)
        self.assertIn("D003_RERANK = 0", txt)
        self.assertIn("intfloat/multilingual-e5-base", txt)
        self.assertIn("ml_app.RERANK is False", txt)
        self.assertIn("ml_app.CANDIDATES == D003_CANDIDATES", txt)

    def test_assert_d003_fails_on_rerank_true(self):
        from retrieval_v2.run_p0_candidate_gate import _assert_d003_contract
        import app as ml_app

        orig_rerank = ml_app.RERANK
        try:
            ml_app.RERANK = True  # simulate local default
            with self.assertRaises(AssertionError):
                _assert_d003_contract()
        finally:
            ml_app.RERANK = orig_rerank
        # should pass with correct values (RERANK False, etc.)
        # we assume current env is prod-like; if not, just check logic without asserting pass
        # Instead mock to correct values and ensure no raise
        with mock.patch.object(ml_app, "RERANK", False):
            with mock.patch.object(ml_app, "CANDIDATES", 30):
                with mock.patch.object(ml_app, "COSINE_MIN", 0.78):
                    with mock.patch.object(ml_app, "LEXICAL_OVERLAP_BIAS", 0.01):
                        with mock.patch.object(ml_app, "EMBED_MODEL_NAME", "intfloat/multilingual-e5-base"):
                            _assert_d003_contract()  # should not raise

    def test_harness_production_parity_path_pins(self):
        txt = _read_harness_text()
        # must contain same embedding, SQL, strip_region, youth_source_bias, lexical rewrite, bias .01, candidates 30, region_filter None, COSINE_MIN .78
        self.assertIn("strip_region", txt)
        self.assertIn("ml_app.SQL", txt)
        self.assertIn("youth_source_bias", txt)
        self.assertIn("lexical_overlap_terms_rewrite", txt)
        self.assertIn("LEXICAL_OVERLAP_BIAS", txt)
        self.assertIn("CANDIDATES", txt)
        self.assertIn("region_filter", txt)
        self.assertIn("COSINE_MIN", txt)
        self.assertIn('rp": None', txt)
        # must NOT contain RRF implementation / cross-encoder runtime / new threshold
        # Docstring may mention "no rank fusion / no cross-encoder" as absence note; check no functional code
        self.assertNotIn("CrossEncoder", txt)
        self.assertNotIn("from sentence_transformers import CrossEncoder", txt)
        lower = txt.lower()
        self.assertNotIn("def rrf", lower)
        self.assertNotIn("rrf_score", lower)
        # public region may be mentioned as "no public region" in docs; ensure no actual region-specific logic beyond rp=None
        # count occurrences, allow one documentation mention
        self.assertLessEqual(lower.count("public region"), 1)


class PathCountGuardTest(unittest.TestCase):
    def test_pinned_paths_no_cli_override(self):
        txt = _read_harness_text()
        self.assertIn("YOUTH_EVAL_FILE", txt)
        self.assertIn("GOV24_EVAL_FILE", txt)
        self.assertIn('eval/evalset.jsonl', txt)
        self.assertIn('eval/expansion_evalset.jsonl', txt)
        self.assertIn("EXPECTED_YOUTH_N = 60", txt)
        self.assertIn("EXPECTED_GOV24_N = 21", txt)
        # must not expose CLI override for other files
        self.assertNotIn("--youth-eval", txt)
        self.assertNotIn("--gov24-eval", txt)
        self.assertNotIn("--eval-file", txt)
        self.assertNotIn("argparse", txt)  # harness should not parse args for eval files

    def test_load_p0_items_count_guard_synthetic(self):
        from retrieval_v2.run_p0_candidate_gate import _load_p0_items

        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td) / "youth.jsonl"
            # 60 correct
            items = [{"query": f"q{i}", "gold_source_id": f"id{i}"} for i in range(60)]
            p.write_text("\n".join(json.dumps(it, ensure_ascii=False) for it in items), encoding="utf-8")
            loaded = _load_p0_items(p, 60, "youth", "youth")
            self.assertEqual(len(loaded), 60)
            self.assertTrue(all(it["gold_source"] == "youth" for it in loaded))
            # 59 should fail
            p2 = pathlib.Path(td) / "youth59.jsonl"
            p2.write_text("\n".join(json.dumps(it, ensure_ascii=False) for it in items[:59]), encoding="utf-8")
            with self.assertRaises(SystemExit):
                _load_p0_items(p2, 60, "youth", "youth")
            # mismatched gold_source should fail
            bad = [{"query": "q", "gold_source_id": "id", "gold_source": "gov24"}]
            p3 = pathlib.Path(td) / "bad.jsonl"
            p3.write_text(json.dumps(bad[0]), encoding="utf-8")
            with self.assertRaises(SystemExit):
                _load_p0_items(p3, 1, "youth", "youth")

    def test_load_p0_items_preserves_gov24_explicit(self):
        from retrieval_v2.run_p0_candidate_gate import _load_p0_items

        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td) / "gov24.jsonl"
            items = [{"query": f"q{i}", "gold_source_id": f"id{i}", "gold_source": "gov24"} for i in range(21)]
            p.write_text("\n".join(json.dumps(it, ensure_ascii=False) for it in items), encoding="utf-8")
            loaded = _load_p0_items(p, 21, "gov24", "gov24")
            self.assertEqual(len(loaded), 21)

    def test_harness_counts_exact(self):
        txt = _read_harness_text()
        # ensure harness asserts exactly 60 and 21 via _load_p0_items calls
        self.assertIn("EXPECTED_YOUTH_N", txt)
        self.assertIn("EXPECTED_GOV24_N", txt)
        self.assertIn("_load_p0_items(YOUTH_EVAL_FILE", txt)
        self.assertIn("_load_p0_items(GOV24_EVAL_FILE", txt)


class OutputNamespaceTest(unittest.TestCase):
    def test_fixed_output_pinned(self):
        txt = _read_harness_text()
        self.assertIn(FIXED_OUTPUT_POSIX, txt)
        self.assertIn("FIXED_OUTPUT", txt)
        self.assertIn("eval/retrieval-v2/p0/p0-candidate-v2.json", txt)

    def test_guard_rejects_canonical_and_wrong_paths(self):
        from retrieval_v2.run_p0_candidate_gate import ensure_p0_output_path

        # correct fixed path should pass
        ensure_p0_output_path(FIXED_OUTPUT_POSIX)
        # canonical should be rejected
        with self.assertRaises(ValueError):
            ensure_p0_output_path("eval/canonical_youth_production_parity.json")
        with self.assertRaises(ValueError):
            ensure_p0_output_path("eval/canonical_manifest.json")
        # non-p0 should be rejected
        with self.assertRaises(ValueError):
            ensure_p0_output_path("eval/retrieval-v2/final/p0-candidate-v2.json")
        with self.assertRaises(ValueError):
            ensure_p0_output_path("eval/retrieval-v2/experiments/p0-candidate-v2.json")
        # wrong file under p0 should be rejected (must be exactly fixed)
        with self.assertRaises(ValueError):
            ensure_p0_output_path("eval/retrieval-v2/p0/other.json")
        # absolute should be rejected
        with self.assertRaises(ValueError):
            ensure_p0_output_path(str(ROOT / FIXED_OUTPUT_POSIX))
        # traversal should be rejected
        with self.assertRaises(ValueError):
            ensure_p0_output_path("eval/retrieval-v2/p0/../p0-candidate-v2.json")

    def test_harness_no_query_gold_title_in_output(self):
        txt = _read_harness_text()
        # per_case should not store query or gold_title
        self.assertIn("per_case", txt)
        self.assertIn("case_index", txt)
        self.assertIn('"gold_source"', txt)
        import re
        blocks = re.findall(r"per_case\.append\(\s*\{([^}]+)\}", txt, flags=re.DOTALL)
        self.assertTrue(len(blocks) >= 1, "no per_case.append blocks found")
        for block in blocks:
            self.assertNotIn('"query"', block)
            self.assertNotIn("'query'", block)
            self.assertNotIn("gold_title", block)


class MetricsP0ThresholdTest(unittest.TestCase):
    def test_youth_gov24_gates(self):
        from retrieval_v2.p0_gate import gov24_gate, p0_gate, youth_gate

        self.assertEqual(youth_gate(28), "PASS")
        self.assertEqual(youth_gate(27), "HOLD")
        self.assertEqual(youth_gate(26), "NO-GO")
        self.assertEqual(gov24_gate(15), "PASS")
        self.assertEqual(gov24_gate(14), "HOLD")
        self.assertEqual(gov24_gate(13), "NO-GO")
        self.assertEqual(p0_gate({"youth": [1] * 28 + [0] * 32, "gov24": [1] * 15 + [0] * 6})["overall"], "PASS")
        self.assertEqual(p0_gate({"youth": [1] * 27 + [0] * 33, "gov24": [1] * 15 + [0] * 6})["overall"], "HOLD")
        self.assertEqual(p0_gate({"youth": [1] * 28 + [0] * 32, "gov24": [1] * 14 + [0] * 7})["overall"], "HOLD")
        self.assertEqual(p0_gate({"youth": [1] * 26 + [0] * 34, "gov24": [1] * 15 + [0] * 6})["overall"], "NO-GO")

    def test_compute_metrics_synthetic(self):
        from retrieval_v2.metrics import compute_metrics

        youth_ranks = [1] * 28 + [0] * 32  # 28/60 hit@5 but need realistic ranks within 10
        gov24_ranks = [1] * 15 + [0] * 6
        # Use ranks 1..5 for hits, 0 for miss
        # For MRR test, use 1 for hit, 0 for miss => MRR = hit/1 / n
        m = compute_metrics(youth_ranks + gov24_ranks, by_source={"youth": youth_ranks, "gov24": gov24_ranks})
        self.assertEqual(m["by_source"]["youth"]["hit@5"], 28)
        self.assertEqual(m["by_source"]["gov24"]["hit@5"], 15)

    def test_harness_uses_p0_gate(self):
        txt = _read_harness_text()
        self.assertIn("p0_gate", txt)
        self.assertIn("youth_gate", txt)
        self.assertIn("gov24_gate", txt)
        self.assertIn("candidate_tuning_after_final_holdout", txt)
        self.assertIn("p0_retrieval_runs_executed", txt)


class HarnessManifestTest(unittest.TestCase):
    def test_manifest_exists_and_pins(self):
        self.assertTrue(MANIFEST_PATH.exists(), f"harness manifest missing: {MANIFEST_PATH}")
        m = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(m["expected_candidate_commit"], "5745cc3144b519da456b21030d0e0752d1d018ae")
        self.assertEqual(m["expected_candidate_tag"], "retrieval-v2-candidate-v2")
        self.assertEqual(m["expected_artifact_commit"], "c6c082681b4f2fcd521790e50c5fd46549116307")
        self.assertIn("youth_sha256", str(m))
        self.assertIn("gov24_sha256", str(m))
        self.assertIn("run_p0_candidate_gate", str(m.get("harness", "")))


if __name__ == "__main__":
    unittest.main()
