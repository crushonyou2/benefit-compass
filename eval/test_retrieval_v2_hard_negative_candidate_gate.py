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

HARNESS = ROOT / "eval" / "retrieval_v2" / "run_hard_negative_candidate_gate.py"
CANDIDATE_MANIFEST = ROOT / "eval" / "retrieval-v2" / "candidate" / "manifest.json"
MANIFEST_PATH = ROOT / "eval" / "retrieval-v2" / "hard-negative" / "harness-manifest.json"
FIXED_OUTPUT_POSIX = "eval/retrieval-v2/hard-negative/paired-candidate-v2.json"
EXPECTED_INPUT_POSIX = "eval/expansion_api_evalset.jsonl"
EXPECTED_LF_SHA = "2b56dcfd79b14b91f719a65e3eef836cee5dff9a242277fa4148ada215521da5"


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
        self.assertIn("CANDIDATE_BUNDLE_PATHS", txt)
        self.assertIn('"diff"', txt)
        self.assertIn('"--quiet"', txt)
        self.assertIn("check_call", txt)

    def test_candidate_module_imports_rewrite(self):
        txt = _read_harness_text()
        self.assertIn("lexical_overlap_terms_rewrite", txt)
        self.assertIn("lexical_overlap_terms", txt)
        self.assertIn("from retrieval_v2.candidate_lexical_rewrite import lexical_overlap_terms_rewrite", txt)

    def test_validate_candidate_pin_synthetic(self):
        from retrieval_v2.run_hard_negative_candidate_gate import _validate_candidate_pin

        with tempfile.TemporaryDirectory() as td:
            td_path = pathlib.Path(td)
            real = json.loads(CANDIDATE_MANIFEST.read_text(encoding="utf-8"))
            tmp_manifest = td_path / "manifest.json"
            tmp_manifest.write_text(json.dumps(real, ensure_ascii=False), encoding="utf-8")
            with mock.patch("retrieval_v2.run_hard_negative_candidate_gate.subprocess.check_output", return_value=b"5745cc3144b519da456b21030d0e0752d1d018ae\n"):
                with mock.patch("retrieval_v2.run_hard_negative_candidate_gate.subprocess.check_call", return_value=0):
                    res = _validate_candidate_pin(
                        candidate_manifest_path=tmp_manifest,
                        expected_artifact_commit="c6c082681b4f2fcd521790e50c5fd46549116307",
                        expected_candidate_commit="5745cc3144b519da456b21030d0e0752d1d018ae",
                        expected_tag="retrieval-v2-candidate-v2",
                    )
                    self.assertEqual(res["candidate_frozen"], True)
            tampered = dict(real)
            tampered["artifact_provenance"] = dict(real["artifact_provenance"])
            tampered["artifact_provenance"]["git_commit"] = "0000000000000000000000000000000000000000"
            tmp_tampered = td_path / "tampered.json"
            tmp_tampered.write_text(json.dumps(tampered, ensure_ascii=False), encoding="utf-8")
            with mock.patch("retrieval_v2.run_hard_negative_candidate_gate.subprocess.check_output", return_value=b"5745cc3144b519da456b21030d0e0752d1d018ae\n"):
                with self.assertRaises(SystemExit):
                    _validate_candidate_pin(
                        candidate_manifest_path=tmp_tampered,
                        expected_artifact_commit="c6c082681b4f2fcd521790e50c5fd46549116307",
                        expected_candidate_commit="5745cc3144b519da456b21030d0e0752d1d018ae",
                        expected_tag="retrieval-v2-candidate-v2",
                    )


class InputPinTest(unittest.TestCase):
    def test_input_path_pinned_and_hash(self):
        txt = _read_harness_text()
        self.assertIn(EXPECTED_INPUT_POSIX, txt)
        self.assertIn(EXPECTED_LF_SHA, txt)
        self.assertIn("EXPECTED_N = 36", txt)
        self.assertIn("EXPECTED_PURE = 21", txt)
        self.assertIn("EXPECTED_INELIGIBLE = 3", txt)
        self.assertIn("EXPECTED_NO_ANSWER = 12", txt)
        self.assertIn("canonical_text_sha256", txt)

    def test_no_cli_override_for_input(self):
        txt = _read_harness_text()
        self.assertNotIn("--eval-file", txt)
        self.assertNotIn("--input", txt)
        self.assertIn("EXPECTED_INPUT_FILE", txt)
        self.assertIn("_validate_input_pin", txt)
        self.assertIn("slice mismatch", txt)

    def test_validate_input_pin_real_file(self):
        from retrieval_v2.run_hard_negative_candidate_gate import _validate_input_pin

        items = _validate_input_pin()
        self.assertEqual(len(items), 36)
        pure = sum(1 for it in items if it.get("gold_source_id") and not it.get("excluded_source_id") and not it.get("expected_no_results"))
        inelig = sum(1 for it in items if it.get("excluded_source_id"))
        noans = sum(1 for it in items if it.get("expected_no_results"))
        self.assertEqual(pure, 21)
        self.assertEqual(inelig, 3)
        self.assertEqual(noans, 12)

    def test_input_lf_sha_exact(self):
        sha = canonical_text_sha256(ROOT / EXPECTED_INPUT_POSIX)
        self.assertEqual(sha, EXPECTED_LF_SHA)


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
        from retrieval_v2.run_hard_negative_candidate_gate import _assert_d003_contract
        import app as ml_app

        orig = ml_app.RERANK
        try:
            ml_app.RERANK = True
            with self.assertRaises(AssertionError):
                _assert_d003_contract()
        finally:
            ml_app.RERANK = orig
        with mock.patch.object(ml_app, "RERANK", False):
            with mock.patch.object(ml_app, "CANDIDATES", 30):
                with mock.patch.object(ml_app, "COSINE_MIN", 0.78):
                    with mock.patch.object(ml_app, "LEXICAL_OVERLAP_BIAS", 0.01):
                        with mock.patch.object(ml_app, "EMBED_MODEL_NAME", "intfloat/multilingual-e5-base"):
                            _assert_d003_contract()

    def test_production_parity_pins(self):
        txt = _read_harness_text()
        self.assertIn("strip_region", txt)
        self.assertIn("ml_app.SQL", txt)
        self.assertIn("youth_source_bias", txt)
        self.assertIn("lexical_overlap_terms", txt)
        self.assertIn("lexical_overlap_terms_rewrite", txt)
        self.assertIn("LEXICAL_OVERLAP_BIAS", txt)
        self.assertIn("CANDIDATES", txt)
        self.assertIn("region_filter", txt)
        self.assertIn("COSINE_MIN", txt)
        self.assertIn('"rp": None', txt)
        self.assertNotIn("CrossEncoder", txt)
        self.assertNotIn("from sentence_transformers import CrossEncoder", txt)
        lower = txt.lower()
        self.assertNotIn("def rrf", lower)
        self.assertNotIn("rrf_score", lower)


class CorpusPreflightTest(unittest.TestCase):
    def test_expected_corpus_constants(self):
        txt = _read_harness_text()
        self.assertIn("13589", txt)
        self.assertIn("17609", txt)
        self.assertIn("10958", txt)
        self.assertIn("14526", txt)
        self.assertIn("2631", txt)
        self.assertIn("3083", txt)
        self.assertIn("assert_corpus_preflight", txt)
        self.assertIn("get_corpus_summary", txt)

    def test_assert_corpus_helper(self):
        from retrieval_v2.run_hard_negative_candidate_gate import assert_corpus_preflight

        good = {
            "total_policies": 13589,
            "total_chunks": 17609,
            "by_source": {
                "gov24": {"policies": 10958, "chunks": 14526},
                "youth": {"policies": 2631, "chunks": 3083},
            },
        }
        assert_corpus_preflight(good)
        bad = dict(good)
        bad["total_policies"] = 13588
        with self.assertRaises(SystemExit):
            assert_corpus_preflight(bad)
        bad2 = {
            "total_policies": 13589,
            "total_chunks": 17609,
            "by_source": {
                "gov24": {"policies": 10958, "chunks": 9999},
                "youth": {"policies": 2631, "chunks": 3083},
            },
        }
        with self.assertRaises(SystemExit):
            assert_corpus_preflight(bad2)

    def test_corpus_preflight_before_retrieval(self):
        txt = _read_harness_text()
        corpus_idx = txt.index("get_corpus_summary")
        preflight_idx = txt.index("assert_corpus_preflight")
        loop_idx = txt.index("for idx, it in enumerate(items")
        self.assertLess(corpus_idx, preflight_idx)
        self.assertLess(preflight_idx, loop_idx)


class PairedSameVectorTest(unittest.TestCase):
    def test_same_vector_reuse(self):
        txt = _read_harness_text()
        self.assertIn("model.encode", txt)
        self.assertIn("vec_str", txt)
        self.assertIn("lex_baseline = lexical_overlap_terms(q)", txt)
        self.assertIn("lex_candidate = lexical_overlap_terms_rewrite(q)", txt)
        self.assertIn('"lexical_terms": lex_baseline', txt)
        self.assertIn('"lexical_terms": lex_candidate', txt)
        self.assertIn("youth_bias = youth_source_bias(q)", txt)
        baseline_pos = txt.index('"lexical_terms": lex_baseline')
        candidate_pos = txt.index('"lexical_terms": lex_candidate')
        self.assertLess(baseline_pos, candidate_pos)
        self.assertIn("same vector", txt.lower())

    def test_no_separate_baseline_run(self):
        txt = _read_harness_text()
        self.assertEqual(txt.count("for idx, it in enumerate(items"), 1)


class GateTruthTableTest(unittest.TestCase):
    def test_hard_negative_gate_used(self):
        txt = _read_harness_text()
        self.assertIn("from retrieval_v2.hard_negative import hard_negative_gate", txt)
        self.assertIn("hard_negative_gate(", txt)
        self.assertIn("baseline_pure_hit5", txt)
        self.assertIn("candidate_pure_hit5", txt)

    def test_gate_truth_table(self):
        from retrieval_v2.hard_negative import hard_negative_gate

        g = hard_negative_gate(baseline_pure_hit5=15, candidate_pure_hit5=14, baseline_intrusion=0, candidate_intrusion=0)
        self.assertEqual(g["gate"], "FAIL")
        self.assertTrue(g["pure_fail"])
        self.assertFalse(g["intrusion_fail"])
        g2 = hard_negative_gate(baseline_pure_hit5=15, candidate_pure_hit5=15, baseline_intrusion=0, candidate_intrusion=1)
        self.assertEqual(g2["gate"], "FAIL")
        self.assertTrue(g2["intrusion_fail"])
        g3 = hard_negative_gate(baseline_pure_hit5=15, candidate_pure_hit5=15, baseline_intrusion=0, candidate_intrusion=0)
        self.assertEqual(g3["gate"], "PASS")
        g4 = hard_negative_gate(baseline_pure_hit5=15, candidate_pure_hit5=16, baseline_intrusion=1, candidate_intrusion=0)
        self.assertEqual(g4["gate"], "PASS")
        g5 = hard_negative_gate(baseline_pure_hit5=15, candidate_pure_hit5=14, baseline_intrusion=0, candidate_intrusion=1)
        self.assertEqual(g5["gate"], "FAIL")
        self.assertTrue(g5["pure_fail"] and g5["intrusion_fail"])


class IntrusionSemanticsTest(unittest.TestCase):
    def test_exact_excluded_tuple_check(self):
        txt = _read_harness_text()
        self.assertIn("intrusion_of", txt)
        self.assertIn("excluded_source", txt)
        self.assertIn("excluded_source_id", txt)
        self.assertIn("topk=5", txt)
        self.assertIn("excluded in keys", txt)

    def test_intrusion_helper_truth(self):
        from retrieval_v2.run_hard_negative_candidate_gate import intrusion_of

        cands = [
            {"source": "gov24", "source_id": "SSE000000170"},
            {"source": "gov24", "source_id": "OTHER1"},
            {"source": "youth", "source_id": "Y1"},
            {"source": "gov24", "source_id": "OTHER2"},
            {"source": "gov24", "source_id": "OTHER3"},
        ]
        self.assertTrue(intrusion_of(cands, ("gov24", "SSE000000170"), topk=5))
        self.assertFalse(intrusion_of(cands, ("gov24", "NOT_EXIST"), topk=5))
        self.assertFalse(intrusion_of(cands, ("gov24", "MISSING"), topk=5))
        cands_top6 = [{"source": "gov24", "source_id": f"ID{i}"} for i in range(5)] + [{"source": "gov24", "source_id": "SSE000000170"}]
        self.assertFalse(intrusion_of(cands_top6, ("gov24", "SSE000000170"), topk=5))
        self.assertTrue(intrusion_of(cands_top6, ("gov24", "SSE000000170"), topk=6))

    def test_pure_positive_definition(self):
        txt = _read_harness_text()
        self.assertIn("has_gold and not has_excl and not is_noans", txt)
        self.assertIn('case_type_label = "pure_positive"', txt)
        self.assertIn('case_type_label = "ineligible"', txt)
        self.assertIn("has_excl", txt)


class NoAnswerNonBlockingTest(unittest.TestCase):
    def test_no_answer_not_in_gate(self):
        txt = _read_harness_text()
        self.assertIn('case_type_label = "no_answer"', txt)
        gate_section = txt[txt.index("hard_negative_gate("): txt.index("hard_negative_gate(")+500]
        self.assertNotIn("no_answer", gate_section)
        self.assertIn("no_answer_diagnostics", txt)
        self.assertIn("nonblocking", txt.lower())

    def test_no_threshold_gate(self):
        txt = _read_harness_text()
        gate_start = txt.index("hard_negative_gate(")
        gate_section = txt[gate_start: gate_start+800].lower()
        self.assertNotIn("threshold", gate_section)
        self.assertNotIn("top1_score", gate_section)


class OutputNamespaceTest(unittest.TestCase):
    def test_fixed_output_pinned(self):
        txt = _read_harness_text()
        self.assertIn(FIXED_OUTPUT_POSIX, txt)
        self.assertIn("ensure_hard_negative_output_path", txt)
        self.assertIn("FIXED_OUTPUT_POSIX", txt)
        self.assertIn("is_canonical_path", txt)
        self.assertIn("canonical", txt.lower())

    def test_output_guard_rejects_canonical(self):
        from retrieval_v2.run_hard_negative_candidate_gate import ensure_hard_negative_output_path

        with self.assertRaises(ValueError):
            ensure_hard_negative_output_path("eval/canonical_hard_negative_36_production_parity.json")
        with self.assertRaises(ValueError):
            ensure_hard_negative_output_path("eval/retrieval-v2/p0/p0-candidate-v2.json")
        with self.assertRaises(ValueError):
            ensure_hard_negative_output_path("eval/retrieval-v2/hard-negative/../p0/evil.json")
        ensure_hard_negative_output_path(FIXED_OUTPUT_POSIX)

    def test_per_case_minimal_no_plaintext(self):
        txt = _read_harness_text()
        self.assertIn('"index": idx', txt)
        self.assertIn('"case_type": case_type_label', txt)
        self.assertIn('"baseline_rank_top5"', txt)
        self.assertIn('"candidate_rank_top5"', txt)
        self.assertIn('"baseline_intrusion_top5"', txt)
        self.assertIn('"candidate_intrusion_top5"', txt)
        per_case_section = txt[txt.index("per_case.append"): txt.index("per_case.append")+800]
        self.assertNotIn('"query"', per_case_section)
        self.assertNotIn("gold_title", per_case_section)


class CanonicalParityTest(unittest.TestCase):
    def test_historical_parity_constants(self):
        txt = _read_harness_text()
        self.assertIn("HISTORICAL_PURE_HIT5 = 15", txt)
        self.assertIn("HISTORICAL_INTRUSION = 0", txt)
        self.assertIn("baseline_canonical_parity", txt)
        self.assertIn("HOLD_INVALID_BASELINE_PARITY", txt)

    def test_verify_canonical_blocking_derivation(self):
        from retrieval_v2.run_hard_negative_candidate_gate import _validate_canonical_pin

        info = _validate_canonical_pin()
        self.assertIn("manifest", info)
        self.assertIn("artifact", info)
        cases = info["artifact"]["cases"]
        pure = [c for c in cases if c.get("gold_source_id") and not c.get("excluded_source_id") and not c.get("expected_no_results")]
        pure_hits = sum(1 for c in pure if c.get("gold_rank_top5") is not None and 1 <= c.get("gold_rank_top5") <= 5)
        self.assertEqual(pure_hits, 15)


class HarnessManifestTest(unittest.TestCase):
    def test_manifest_exists_and_pins(self):
        self.assertTrue(MANIFEST_PATH.exists(), f"harness manifest missing: {MANIFEST_PATH}")
        m = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(m.get("role"), "harness")
        self.assertEqual(m.get("name"), "hard-negative-evaluator-v1")
        self.assertIn("expected_candidate_commit", m)
        self.assertEqual(m["expected_candidate_commit"], "5745cc3144b519da456b21030d0e0752d1d018ae")
        self.assertIn("expected_input", m)
        self.assertEqual(m["expected_input"]["path"], EXPECTED_INPUT_POSIX)
        self.assertEqual(m["expected_input"]["lf_sha256"], EXPECTED_LF_SHA)
        self.assertIn("run_hard_negative_candidate_gate", str(m.get("harness", "")))
        self.assertIn("test_retrieval_v2_hard_negative_candidate_gate", str(m.get("test", "")))
        self.assertEqual(m.get("output"), FIXED_OUTPUT_POSIX)
        self.assertIn("hard-negative", m.get("output", ""))


if __name__ == "__main__":
    unittest.main()
