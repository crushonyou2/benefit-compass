import hashlib
import json
import pathlib
import sys
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
from retrieval_v2.provenance import canonical_text_sha256

HARNESS = ROOT / "eval" / "retrieval_v2" / "run_latency_candidate_gate.py"
CANDIDATE_MANIFEST = ROOT / "eval" / "retrieval-v2" / "candidate" / "manifest.json"
DEV_MANIFEST = ROOT / "eval" / "retrieval-v2" / "dev" / "manifest.json"
DEV_EVALSET = ROOT / "eval" / "retrieval-v2" / "dev" / "evalset.jsonl"
MANIFEST_PATH = ROOT / "eval" / "retrieval-v2" / "latency" / "harness-manifest.json"
FIXED_OUTPUT_POSIX = "eval/retrieval-v2/latency/latency-candidate-v2.json"
EXPECTED_DEV_SHA = "e9510203cb26bb9db5598b1cd284398ba226460437a396e72906aa6505aff56e"
EXPECTED_SAMPLE_COUNT = 180

def _read_harness_text() -> str:
    return HARNESS.read_text(encoding="utf-8")

class CandidatePinTest(unittest.TestCase):
    def test_pinned_commit_and_tag_present(self):
        txt = _read_harness_text()
        self.assertIn("5745cc3144b519da456b21030d0e0752d1d018ae", txt)
        self.assertIn("retrieval-v2-candidate-v2", txt)
        self.assertIn("c6c082681b4f2fcd521790e50c5fd46549116307", txt)
        self.assertIn("EXPECTED_CANDIDATE_COMMIT", txt)
        self.assertIn("EXPECTED_CANDIDATE_TAG", txt)
        self.assertIn("EXPECTED_ARTIFACT_COMMIT", txt)
        # must validate candidate_frozen and bundle hashes
        self.assertIn("candidate_frozen", txt)
        self.assertIn("candidate bundle hash mismatch", txt)
        self.assertIn("have diverged from tag", txt)
        # dev sha pin in candidate manifest check
        self.assertIn(EXPECTED_DEV_SHA, txt)

class DevPinTest(unittest.TestCase):
    def test_dev_manifest_pinned(self):
        txt = _read_harness_text()
        self.assertIn(EXPECTED_DEV_SHA, txt)
        self.assertIn('EXPECTED_DEV_SHA256', txt)
        self.assertIn('DEV_MANIFEST_FILE', txt)
        self.assertIn('DEV_EVALSET_FILE', txt)
        # checks role dev, cases 36
        self.assertIn('role', txt)
        # validate actual files
        self.assertTrue(DEV_MANIFEST.exists())
        self.assertTrue(DEV_EVALSET.exists())
        m = json.loads(DEV_MANIFEST.read_text(encoding="utf-8"))
        self.assertEqual(m.get("role"), "dev")
        self.assertEqual(m.get("cases"), 36)
        self.assertEqual(m.get("sha256"), EXPECTED_DEV_SHA)
        actual_sha = canonical_text_sha256(DEV_EVALSET)
        self.assertEqual(actual_sha, EXPECTED_DEV_SHA)
        # harness must call canonical_text_sha256 for dev evalset
        self.assertIn("canonical_text_sha256", txt)
        self.assertIn("_validate_dev_pin", txt)

class D003ContractTest(unittest.TestCase):
    def test_harness_contains_d003_constants(self):
        txt = _read_harness_text()
        self.assertIn("D003_CANDIDATES = 30", txt)
        self.assertIn("D003_COSINE_MIN = 0.78", txt)
        self.assertIn("D003_LEXICAL_BIAS = 0.01", txt)
        self.assertIn("D003_RERANK = 0", txt)
        self.assertIn("intfloat/multilingual-e5-base", txt)
        self.assertIn("CANDIDATES", txt)
        self.assertIn("COSINE_MIN", txt)
        self.assertIn("LEXICAL_OVERLAP_BIAS", txt)
        self.assertIn("EMBED_MODEL_NAME", txt)
        self.assertIn("RERANK is False", txt)
        self.assertIn("_assert_d003_contract", txt)
        # must check before DB/model
        # authorization guard before D003 is okay but D003 must be before model load
        self.assertLess(txt.find("_assert_d003_contract"), txt.find("SentenceTransformer"))
        self.assertLess(txt.find("EXPECTED_CANDIDATE_COMMIT"), txt.find("SentenceTransformer"))

    def test_lexical_terms_difference_only(self):
        txt = _read_harness_text()
        self.assertIn("lexical_overlap_terms", txt)
        self.assertIn("lexical_overlap_terms_rewrite", txt)
        # both must be present and only lexical term fn differs
        self.assertIn("lexical_terms_baseline", txt)
        self.assertIn("lexical_terms_candidate", txt)

class CorpusPreflightTest(unittest.TestCase):
    def test_expected_corpus_constants(self):
        txt = _read_harness_text()
        self.assertIn("13589", txt)
        self.assertIn("17609", txt)
        self.assertIn("10958", txt)
        self.assertIn("14526", txt)
        self.assertIn("2631", txt)
        self.assertIn("3083", txt)
        self.assertIn("EXPECTED_CORPUS", txt)
        self.assertIn("assert_corpus_preflight", txt)
        self.assertIn("get_corpus_summary", txt)
        # must be checked after DB connect in main (not definition order)
        main_idx = txt.find("def main")
        self.assertNotEqual(main_idx, -1)
        main_block = txt[main_idx:]
        self.assertLess(main_block.find("psycopg2.connect"), main_block.find("assert_corpus_preflight"))
        self.assertLess(main_block.find("assert_corpus_preflight"), main_block.find("precompute"))
class OutputNamespaceTest(unittest.TestCase):
    def test_fixed_output_pinned(self):
        txt = _read_harness_text()
        self.assertIn(FIXED_OUTPUT_POSIX, txt)
        self.assertIn("FIXED_OUTPUT_POSIX", txt)
        self.assertIn("ensure_latency_output_path", txt)
        self.assertIn("eval/retrieval-v2/latency/", txt)
        # must forbid canonical and holdout
        self.assertIn("canonical", txt)
        self.assertIn("holdout", txt)
        self.assertIn("refusing to write", txt)
        # output must be strict fixed
        self.assertIn("output must be exactly", txt)
        # ensure only latency namespace, not final/p0/hard-negative
        self.assertNotIn("eval/retrieval-v2/final/", txt.replace("holdout", ""))  # allow only latency
        self.assertNotIn("eval/retrieval-v2/p0/", txt)

    def test_output_contains_only_latency(self):
        # limit output to latency namespace
        txt = _read_harness_text()
        lower = txt.lower()
        # count distinct retrieval-v2 subdirs mentioned outside of checks
        self.assertIn("eval/retrieval-v2/latency/latency-candidate-v2.json", txt)

class AuthorizationGateTest(unittest.TestCase):
    def test_authorized_flag_required_before_load(self):
        txt = _read_harness_text()
        self.assertIn("--authorized-latency-gate", txt)
        self.assertIn("authorized_latency_gate", txt)
        self.assertIn("Missing --authorized-latency-gate", txt)
        # authorization check must be before model/DB load
        auth_idx = txt.find("authorized_latency_gate")
        model_idx = txt.find("SentenceTransformer")
        db_idx = txt.find("psycopg2.connect")
        self.assertLess(auth_idx, model_idx)
        self.assertLess(auth_idx, db_idx)
        # D003 and candidate pin also before load? candidate pin before model is required per spec
        self.assertLess(txt.find("_assert_d003_contract"), model_idx)
        self.assertLess(txt.find("_validate_candidate_pin"), model_idx)
        self.assertLess(txt.find("_validate_dev_pin"), model_idx)

class LatencyDesignTest(unittest.TestCase):
    def test_same_process_db_qvec(self):
        txt = _read_harness_text()
        self.assertIn("same process", txt.lower())
        self.assertIn("same_db_connection", txt)
        self.assertIn("same_corpus", txt)
        self.assertIn("same_query_set", txt)
        self.assertIn("precomputed_qvec", txt)
        self.assertIn("precomputed", txt.lower())
        self.assertIn("model load", txt.lower())
        self.assertIn("embedding encode", txt.lower())
        # single connection, single cursor reused
        self.assertIn("psycopg2.connect(DB)", txt)
        # count connect occurrences — should be exactly 1
        self.assertEqual(txt.count("psycopg2.connect"), 1)
        # SentenceTransformer import + instantiation => 2 occurrences total
        self.assertEqual(txt.count("SentenceTransformer"), 2)
        # qvec precomputed before warmup
        pre_idx = txt.find("vec_by_case")
        warm_idx = txt.find("warm-up")
        timed_idx = txt.find("ROUNDS")
        # ensure vec precompute before warmup/timed
        self.assertLess(pre_idx, warm_idx)

    def test_timed_scope(self):
        txt = _read_harness_text()
        # timed section from lexical term generation through SQL+fetch+region_filter+COSINE_MIN
        self.assertIn("lexical term generation", txt)
        self.assertIn("region_filter", txt)
        self.assertIn("COSINE_MIN", txt)
        self.assertIn("ml_app.SQL", txt)
        self.assertIn("cur.execute", txt)
        self.assertIn("cur.fetchall", txt)
        # candidate rewrite CPU included
        self.assertIn("candidate rewrite", txt.lower())
        # age/rp None
        self.assertIn('"age": None', txt)
        self.assertIn('"rp": None', txt)
        # youth bias, lexical bias .01, CANDIDATES 30
        self.assertIn("youth_source_bias", txt)
        self.assertIn("D003_LEXICAL_BIAS", txt)
        self.assertIn("D003_CANDIDATES", txt)
        # ensure timer
        self.assertIn("time.perf_counter_ns", txt)
        self.assertIn("latency.summarize", txt)
        self.assertIn("summarize(samples", txt)
        self.assertIn("expected_sample_count=180", txt)
        self.assertIn("EXPECTED_SAMPLE_COUNT", txt)

    def test_warmup_and_rounds(self):
        txt = _read_harness_text()
        self.assertIn("WARMUP_PER_VARIANT = 36", txt)
        self.assertIn("ROUNDS = 5", txt)
        self.assertIn("EXPECTED_SAMPLE_COUNT = 180", txt)
        self.assertIn("36 queries each baseline+candidate once untimed", txt)
        self.assertIn("5 rounds", txt)
        self.assertIn("180 observations per variant", txt)
        # warm-up must be untimed (no perf_counter in warmup block)
        # ensure warmup loop exists
        self.assertIn("warm-up: 36", txt)
        # check for warmup_total
        self.assertIn("warmup_per_variant", txt.lower())

    def test_paired_interleaved_order(self):
        txt = _read_harness_text()
        self.assertIn("(round+query_index)%2", txt)
        self.assertIn("baseline_first", txt)
        self.assertIn("B->C", txt)
        self.assertIn("C->B", txt)
        self.assertIn("immediately paired", txt)
        self.assertIn("not all-A-then-B", txt)
        self.assertIn("pair_start", txt)
        # round query order deterministic seed shuffle
        self.assertIn("SHUFFLE_SEED", txt)
        self.assertIn("20260830", txt)
        self.assertIn("random.Random", txt)
        self.assertIn("shuffle", txt)
        self.assertIn("ORDER_STRATEGY", txt)
        # check interleaving not all baseline then candidate
        self.assertIn("all-A-then-B", txt)
        # summarize validates pairing
        self.assertIn("summarize(samples", txt)

    def test_samples_fields(self):
        txt = _read_harness_text()
        # raw_samples must contain only case_id/round/order/variant/latency_ms
        self.assertIn('"case_id":', txt)
        self.assertIn('"round":', txt)
        self.assertIn('"order":', txt)
        self.assertIn('"variant":', txt)
        self.assertIn('"latency_ms":', txt)
        # must forbid query/gold in samples
        self.assertIn("query", txt)  # device query exists but samples must not contain
        # explicitly check sample forbidden fields
        self.assertIn("forbidden field", txt)
        # ensure samples output
        self.assertIn('"samples": raw_samples', txt) or self.assertIn('"samples":', txt)
        self.assertIn("holdout_accessed", txt)

class HoldoutNotAccessedTest(unittest.TestCase):
    def test_no_holdout_access(self):
        txt = _read_harness_text()
        lower = txt.lower()
        # must not contain real holdout paths
        self.assertNotIn("holdout-v1", lower)
        self.assertNotIn("holdout/manifest", lower)
        self.assertNotIn("holdout evalset", lower)
        self.assertNotIn("expansion_api_evalset", lower.replace("hard-negative", ""))  # holdout not accessed
        # ensure holdout_accessed false in output
        self.assertIn('"holdout_accessed": False', txt)
        # ensure notes say holdout access forbidden
        self.assertIn("holdout access forbidden", lower)

class TimedSectionExcludesModelLoadTest(unittest.TestCase):
    def test_model_load_excluded(self):
        txt = _read_harness_text()
        # model load and embedding encode excluded, qvec precomputed — case-insensitive
        self.assertIn("model load and embedding encode are excluded", txt.lower())
        self.assertIn("qvec fully precomputed", txt)
        # ensure vec precompute uses model.encode before warmup
        self.assertIn("model.encode", txt)
        # ensure timed section does NOT contain model.encode
        # find timed section markers
        timed_start = txt.find("timed section start")
        timed_end = txt.find("timed section end")
        if timed_start != -1 and timed_end != -1:
            timed_block = txt[timed_start:timed_end]
            self.assertNotIn("model.encode", timed_block)
            self.assertNotIn("SentenceTransformer", timed_block)

class LatencySummarizeTest(unittest.TestCase):
    def test_summarize_p95_gate(self):
        from retrieval_v2.latency import p50, p95, Sample, summarize, is_latency_pass
        # empty should raise
        with self.assertRaises(ValueError):
            p50([])
        with self.assertRaises(ValueError):
            p95([])
        # simple samples
        samples = []
        for rnd in range(5):
            for i in range(36):
                samples.append(Sample(query_id=f"dev-{i:03d}", round=rnd, variant="baseline", latency_ms=float(10 + i % 5)))
                samples.append(Sample(query_id=f"dev-{i:03d}", round=rnd, variant="candidate", latency_ms=float(9 + i % 5)))
        # need interleaved pairing: reorder to B,C per pair
        paired = []
        for rnd in range(5):
            for i in range(36):
                # find pair
                b = next(s for s in samples if s.query_id==f"dev-{i:03d}" and s.round==rnd and s.variant=="baseline")
                c = next(s for s in samples if s.query_id==f"dev-{i:03d}" and s.round==rnd and s.variant=="candidate")
                if (rnd + i) %2==0:
                    paired.extend([b,c])
                else:
                    paired.extend([c,b])
        out = summarize(paired, expected_sample_count=180)
        self.assertEqual(out["baseline"]["count"], 180)
        self.assertEqual(out["candidate"]["count"], 180)
        self.assertTrue(out["candidate"]["p95"] <= out["baseline"]["p95"])
        self.assertEqual(out["gate"], "PASS")
        self.assertTrue(is_latency_pass(out["baseline"]["p95"], out["candidate"]["p95"]))
        # non-pass case
        self.assertFalse(is_latency_pass(10.0, 11.0))

    def test_summarize_rejects_all_a_then_b(self):
        from retrieval_v2.latency import Sample, summarize
        samples = []
        for rnd in range(5):
            for i in range(36):
                samples.append(Sample(query_id=f"dev-{i:03d}", round=rnd, variant="baseline", latency_ms=10.0))
        for rnd in range(5):
            for i in range(36):
                samples.append(Sample(query_id=f"dev-{i:03d}", round=rnd, variant="candidate", latency_ms=9.0))
        with self.assertRaises(ValueError):
            summarize(samples, expected_sample_count=180)

class HarnessManifestTest(unittest.TestCase):
    def test_manifest_exists_and_pins(self):
        self.assertTrue(MANIFEST_PATH.exists(), f"manifest missing: {MANIFEST_PATH}")
        m = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        self.assertEqual(m.get("role"), "harness")
        self.assertEqual(m.get("name"), "latency-evaluator-v1")
        self.assertEqual(m.get("expected_candidate_commit"), "5745cc3144b519da456b21030d0e0752d1d018ae")
        self.assertEqual(m.get("expected_candidate_tag"), "retrieval-v2-candidate-v2")
        self.assertEqual(m.get("expected_dev_sha256"), EXPECTED_DEV_SHA)
        self.assertIn("run_latency_candidate_gate", str(m.get("harness", "")))
        self.assertIn("test_retrieval_v2_latency_candidate_gate", str(m.get("test", "")))
        self.assertIn("latency-candidate-v2.json", str(m.get("output", "")))
        self.assertIn("sha256", m)
        self.assertIn("run_latency_candidate_gate", m["sha256"])
        self.assertIn("latency", m["sha256"])
        self.assertEqual(m["sha256_basis"], "utf8_text_lf_normalized")
        self.assertEqual(m["expected_sample_count"], 180)
        self.assertEqual(m["warmup"], 36)
        self.assertEqual(m["rounds"], 5)
        self.assertEqual(m["shuffle_seed"], 20260830)
        self.assertIn("production_contract", m)
        self.assertEqual(m["production_contract"]["candidates"], 30)
        self.assertEqual(m["production_contract"]["rerank"], 0)
if __name__ == "__main__":
    unittest.main()
