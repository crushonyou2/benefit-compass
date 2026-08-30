import hashlib
import json
import math
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
RESULT = ROOT / "eval" / "retrieval-v2" / "latency" / "latency-candidate-v2.json"
ATTESTATION = ROOT / "eval" / "retrieval-v2" / "latency" / "provenance-attestation-v1.json"
HARNESS = ROOT / "eval" / "retrieval_v2" / "run_latency_candidate_gate.py"

EXPECTED_BYTE = "41f8cbc9d4003b06c3ecd84370811355de4aee2f9074cec571f2fa422e5d5cef"
EXPECTED_LF = "054719b84bde760f2eabc950bbe8c2a52a2f1af6d8810349c32f3ed84c7bddcb"
EXPECTED_CORE = "b1beb8c797ce22c4559ddb6618260effb646301ab9236a5ca4946be2aa2fb1c4"
EXPECTED_SAMPLES = "e33ebc910bf3b1aed3a6aaf616af3ed45a83653ba22ef651066fa6a919b89c33"
EXPECTED_SUMMARY = "eff268e268117de8a2983b12feacd78caf365aeb591bc02ec824d5a511ce9f8e"

def canonical_hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()

def percentile_nearest_rank(values, p):
    s = sorted(values)
    k = math.ceil(p / 100 * len(s))
    return s[k - 1]

class ResultHashPinTest(unittest.TestCase):
    def test_byte_and_lf_hash(self):
        b = RESULT.read_bytes()
        self.assertEqual(hashlib.sha256(b).hexdigest(), EXPECTED_BYTE)
        self.assertEqual(hashlib.sha256(b.replace(b"\r\n", b"\n")).hexdigest(), EXPECTED_LF)

    def test_reconstructed_core_hash(self):
        b = RESULT.read_bytes()
        j = json.loads(b.decode("utf-8"))
        j2 = {k: v for k, v in j.items() if k not in ("candidate_provenance", "candidate_tag", "candidate_commit")}
        core = json.dumps(j2, ensure_ascii=False, indent=2).encode("utf-8") + b"\n"
        self.assertEqual(hashlib.sha256(core).hexdigest(), EXPECTED_CORE)
        # core candidate must be summary stats, not provenance object
        self.assertEqual(j2["candidate"], j2["summary"]["candidate"])
        self.assertIn("p95", j2["candidate"])

    def test_samples_and_summary_hash(self):
        j = json.loads(RESULT.read_text(encoding="utf-8"))
        self.assertEqual(canonical_hash(j["samples"]), EXPECTED_SAMPLES)
        self.assertEqual(canonical_hash(j["summary"]), EXPECTED_SUMMARY)

    def test_three_annotation_keys_are_only_extra(self):
        j = json.loads(RESULT.read_text(encoding="utf-8"))
        j2 = {k: v for k, v in j.items() if k not in ("candidate_provenance", "candidate_tag", "candidate_commit")}
        extra = set(j.keys()) - set(j2.keys())
        self.assertEqual(extra, {"candidate_provenance", "candidate_tag", "candidate_commit"})
        self.assertEqual(j["candidate_provenance"], {
            "tag": "retrieval-v2-candidate-v2",
            "commit": "5745cc3144b519da456b21030d0e0752d1d018ae",
            "artifact_commit": "c6c082681b4f2fcd521790e50c5fd46549116307",
            "manifest": "eval/retrieval-v2/candidate/manifest.json",
            "manifest_sha256": "86f80ff6389ede4673e3c8d819cfab2ceefc79b8979a68b7b2bb5d64cc8eccff",
        })
        self.assertEqual(j["candidate_tag"], "retrieval-v2-candidate-v2")
        self.assertEqual(j["candidate_commit"], "5745cc3144b519da456b21030d0e0752d1d018ae")

class SampleIntegrityTest(unittest.TestCase):
    def test_count_pairing_and_gate(self):
        j = json.loads(RESULT.read_text(encoding="utf-8"))
        samples = j["samples"]
        self.assertEqual(len(samples), 360)
        # per variant 180
        baseline = [s for s in samples if s["variant"] == "baseline"]
        candidate = [s for s in samples if s["variant"] == "candidate"]
        self.assertEqual(len(baseline), 180)
        self.assertEqual(len(candidate), 180)
        # keys only
        allowed = {"case_id", "round", "order", "variant", "latency_ms"}
        for s in samples:
            self.assertEqual(set(s.keys()), allowed)
            self.assertNotIn("query", s)
            self.assertNotIn("gold", s)
        # immediate pairing: every adjacent pair same case_id+round, opposite variants
        for i in range(0, len(samples), 2):
            a, b = samples[i], samples[i + 1]
            self.assertEqual(a["case_id"], b["case_id"])
            self.assertEqual(a["round"], b["round"])
            self.assertEqual({a["variant"], b["variant"]}, {"baseline", "candidate"})
            self.assertEqual({a["order"], b["order"]}, {1, 2})
        # order strategy counts
        bf = sum(1 for i in range(0, len(samples), 2) if samples[i]["variant"] == "baseline")
        cf = sum(1 for i in range(0, len(samples), 2) if samples[i]["variant"] == "candidate")
        self.assertEqual(bf, 90)
        self.assertEqual(cf, 90)
        # rounds
        self.assertEqual(sorted(set(s["round"] for s in samples)), [0, 1, 2, 3, 4])
        self.assertEqual(len(set(s["case_id"] for s in samples)), 36)
        # recompute HOLD via nearest-rank
        baseline_p95_raw = percentile_nearest_rank([s["latency_ms"] for s in baseline], 95)
        candidate_p95_raw = percentile_nearest_rank([s["latency_ms"] for s in candidate], 95)
        baseline_p50_raw = percentile_nearest_rank([s["latency_ms"] for s in baseline], 50)
        candidate_p50_raw = percentile_nearest_rank([s["latency_ms"] for s in candidate], 50)
        self.assertAlmostEqual(baseline_p95_raw, 476.509, places=3)
        self.assertAlmostEqual(candidate_p95_raw, 480.548, places=3)
        self.assertEqual(round(baseline_p95_raw, 2), j["baseline_p95"])
        self.assertEqual(round(candidate_p95_raw, 2), j["candidate_p95"])
        self.assertEqual(round(baseline_p50_raw, 2), j["baseline_p50"])
        self.assertEqual(round(candidate_p50_raw, 2), j["candidate_p50"])
        self.assertEqual(j["gate"], "HOLD")
        self.assertEqual(j["summary"]["gate"], "HOLD")
        delta = round(candidate_p95_raw - baseline_p95_raw, 2)
        self.assertEqual(delta, j["delta_p95"])
        self.assertEqual(j["summary"]["delta_p95"], 4.04)

    def test_no_db_or_model_import(self):
        txt = pathlib.Path(__file__).read_text(encoding="utf-8")
        # Ensure this static test does not itself trigger DB/model/retrieval execution.
        # Only actual import statements matter; constant paths/comments are allowed.
        import_lines = [l.strip() for l in txt.splitlines() if l.strip().startswith("import ") or l.strip().startswith("from ")]
        joined = "\n".join(import_lines)
        self.assertNotIn("psycopg2", joined)
        self.assertNotIn("sentence_transformers", joined)
        self.assertNotIn("retrieval_v2.run_latency", joined)

class AttestationInvariantTest(unittest.TestCase):
    def test_attestation_records_no_rerun_no_mutation(self):
        a = json.loads(ATTESTATION.read_text(encoding="utf-8"))
        self.assertEqual(a["role"], "latency_provenance_attestation")
        self.assertEqual(a["contract"], "D-007")
        self.assertEqual(a["measurement_status"], "HOLD")
        inv = a["invariants"]
        self.assertTrue(inv["no_rerun_performed_in_recovery"])
        self.assertFalse(inv["candidate_modified_in_recovery"])
        self.assertFalse(inv["result_modified_in_recovery"])
        self.assertFalse(inv["threshold_gate_changed"])
        self.assertFalse(inv["production_code_modified"])
        self.assertFalse(inv["evaluator_modified"])
        # attestation must state post-run annotation was metadata-only
        self.assertFalse(a["post_run_annotation"]["mutates_measurement_fields"])
        self.assertEqual(a["post_run_annotation"]["source"], "recovered_paseo_session_transcript")
        self.assertEqual(set(a["post_run_annotation"]["exact_added_top_level_keys"]), {"candidate_provenance", "candidate_tag", "candidate_commit"})
        # external observer class must be external_observer_record
        self.assertEqual(a["external_observer_evidence"]["evidence_class"], "external_observer_record")
        # hashes pinned must match constants
        self.assertEqual(a["measurement_hashes"]["committed_result_byte_sha256"], EXPECTED_BYTE)
        self.assertEqual(a["measurement_hashes"]["committed_result_lf_sha256"], EXPECTED_LF)
        self.assertEqual(a["measurement_hashes"]["reconstructed_core_sha256"], EXPECTED_CORE)
        self.assertEqual(a["measurement_hashes"]["samples_canonical_sha256"], EXPECTED_SAMPLES)
        self.assertEqual(a["measurement_hashes"]["summary_canonical_sha256"], EXPECTED_SUMMARY)
        # result commit/tag/path
        self.assertEqual(a["result"]["commit"], "b04556f9251d6cabadd32c7c39c85dee690c8b48")
        self.assertEqual(a["result"]["tag"], "retrieval-v2-latency-result-v1")
        self.assertEqual(a["result"]["path"], "eval/retrieval-v2/latency/latency-candidate-v2.json")
        # evaluator commits
        self.assertEqual(a["evaluator"]["v2"]["commit"], "7b8c4ea868afc3eb8b4ab33f63b067bd23c087ba")
        self.assertEqual(a["candidate"]["commit"], "5745cc3144b519da456b21030d0e0752d1d018ae")

    def test_attestation_known_limitations_present(self):
        a = json.loads(ATTESTATION.read_text(encoding="utf-8"))
        lim = " ".join(a["known_limitations"])
        self.assertIn("DB snapshot", lim)
        self.assertIn("append-only", lim)
        self.assertIn("RERANK=0", lim)
        self.assertIn("external_observer_record", lim)

    def test_attestation_does_not_claim_cryptographic_proof(self):
        a = json.loads(ATTESTATION.read_text(encoding="utf-8"))
        exec_claim = a["execution_count_claim"]
        self.assertEqual(exec_claim["repo_self_attestation"]["class"], "self_attestation")
        self.assertIn("cryptographically prove", exec_claim["cryptographically_proven"].lower())
        # top-level external observer evidence must be marked as non-cryptographic
        self.assertEqual(a["external_observer_evidence"]["evidence_class"], "external_observer_record")
        self.assertIn("cannot cryptographically", exec_claim["cryptographically_proven"].lower())

class NoSideEffectsTest(unittest.TestCase):
    def test_result_file_still_byte_identical(self):
        b = RESULT.read_bytes()
        self.assertEqual(hashlib.sha256(b).hexdigest(), EXPECTED_BYTE)

    def test_harness_not_modified_in_recovery(self):
        # harness LF hash must still match frozen v2
        h = HARNESS.read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(hashlib.sha256(h).hexdigest(), "66a4e48e9c71ecd03aa389ac93ac651817d3147355cb40d64511044357ac26e0")
