"""Cycle3 INFRA REPAIR regression tests — fail-closed coverage.

Proves directly that bootstrap infra fail-opens are repaired:
- missing fingerprint keys FAIL
- wrong version/spec FAIL
- invalid hash FAIL
- duplicate/count mismatch FAIL
- stale wrong set_sha FAIL
- wrong session FAIL
- access_end behind stale grant FAIL
- outcome None/failure FAIL
- non-v4 UUID FAIL
- invalid timestamp FAIL
- git provenance command failure FAIL

And Cycle3 NARROW INFRA REPAIR (this session) additional gates:
- audit latest-start fail-open: success→failure / success→None DENY (latest outcome strict)
- protected-set fingerprint builder gate: cases mandatory + exact count + 0 forbidden, empty manifest cannot PASS overlap 0
- audit durability: os.fsync failure propagates as AuditError, no success token returned

All tests are pure/static, no DB/retrieval/model/embedding/holdout plaintext.
"""

import hashlib
import pathlib
import subprocess
import tempfile
import unittest
import uuid

import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from retrieval_v2.cycle3_audit import (
    AuditError,
    AuditSchemaError,
    append_event,
    verify_holdout_access_allowed,
    read_and_verify_chain,
)
from retrieval_v2.cycle3_fingerprint import (
    FINGERPRINT_VERSION,
    NORMALIZATION_SPEC,
    check_overlap,
    manifest_with_fingerprints,
    query_fingerprint,
    gold_fingerprint,
    validate_fingerprint_manifest,
)


def _valid_manifest(qfps, gfps, cases=None):
    d = {
        "fingerprint_version": FINGERPRINT_VERSION,
        "normalization_spec": NORMALIZATION_SPEC,
        "query_fingerprints": qfps,
        "gold_fingerprints": gfps,
    }
    if cases is not None:
        d["cases"] = cases
    elif len(qfps) == len(gfps) and len(qfps) > 0:
        # Auto-infer cases for valid non-empty manifests to reduce boilerplate in older tests
        d["cases"] = len(qfps)
    return d


class FingerprintInfraRepairTest(unittest.TestCase):
    def test_missing_keys_fail(self):
        with self.assertRaises((ValueError, TypeError)):
            check_overlap({}, {}, strict=True)
        with self.assertRaises(ValueError):
            validate_fingerprint_manifest({})
        with self.assertRaises(ValueError):
            validate_fingerprint_manifest({"fingerprint_version": FINGERPRINT_VERSION, "normalization_spec": NORMALIZATION_SPEC})
        with self.assertRaises(ValueError):
            validate_fingerprint_manifest({"fingerprint_version": FINGERPRINT_VERSION, "normalization_spec": NORMALIZATION_SPEC, "query_fingerprints": []})
        with self.assertRaises(ValueError):
            validate_fingerprint_manifest({"fingerprint_version": FINGERPRINT_VERSION, "normalization_spec": NORMALIZATION_SPEC, "gold_fingerprints": []})
        with self.assertRaises((ValueError, TypeError)):
            validate_fingerprint_manifest({"fingerprint_version": FINGERPRINT_VERSION, "normalization_spec": NORMALIZATION_SPEC, "query_fingerprints": None, "gold_fingerprints": []})

    def test_wrong_version_spec_fail(self):
        q = query_fingerprint("hello")
        g = gold_fingerprint("youth", "123")
        with self.assertRaises(ValueError):
            validate_fingerprint_manifest({"fingerprint_version": "v2", "normalization_spec": NORMALIZATION_SPEC, "query_fingerprints": [q], "gold_fingerprints": [g], "cases": 1})
        with self.assertRaises(ValueError):
            validate_fingerprint_manifest({"fingerprint_version": FINGERPRINT_VERSION, "normalization_spec": "WRONG", "query_fingerprints": [q], "gold_fingerprints": [g], "cases": 1})
        bad_a = {"fingerprint_version": "v2", "normalization_spec": NORMALIZATION_SPEC, "query_fingerprints": [q], "gold_fingerprints": [g], "cases": 1}
        good_b = _valid_manifest([query_fingerprint("other")], [gold_fingerprint("gov24", "999")])
        with self.assertRaises(ValueError):
            check_overlap(bad_a, good_b, strict=False)

    def test_invalid_hash_fail(self):
        q_good = query_fingerprint("valid")
        g_good = gold_fingerprint("youth", "1")
        with self.assertRaises(ValueError):
            validate_fingerprint_manifest(_valid_manifest(["not-a-hex"], [g_good]))
        with self.assertRaises(ValueError):
            validate_fingerprint_manifest(_valid_manifest(["z" * 64], [g_good]))
        with self.assertRaises(ValueError):
            validate_fingerprint_manifest(_valid_manifest(["a" * 63], [g_good]))
        with self.assertRaises(ValueError):
            validate_fingerprint_manifest(_valid_manifest([q_good], ["a" * 64 + "extra"]))
        with self.assertRaises(ValueError):
            manifest_with_fingerprints(role="dev", cycle=3, cases=1, query_fingerprints=["invalid"], gold_fingerprints=[gold_fingerprint("youth", "1")])

    def test_duplicate_fail(self):
        q = query_fingerprint("dup")
        g = gold_fingerprint("youth", "1")
        with self.assertRaises(ValueError):
            validate_fingerprint_manifest(_valid_manifest([q, q], [g, gold_fingerprint("gov24","2")]))
        with self.assertRaises(ValueError):
            validate_fingerprint_manifest(_valid_manifest([q], [g, g]))
        with self.assertRaises(ValueError):
            manifest_with_fingerprints(role="dev", cycle=3, cases=2, query_fingerprints=[q, q], gold_fingerprints=[g, gold_fingerprint("gov24", "2")])
        dup_manifest = _valid_manifest([q, q], [g, gold_fingerprint("gov24","dup2")])
        good = _valid_manifest([query_fingerprint("other")], [gold_fingerprint("gov24", "2")])
        with self.assertRaises(ValueError):
            check_overlap(dup_manifest, good, strict=False)

    def test_count_mismatch_fail(self):
        q1 = query_fingerprint("q1")
        q2 = query_fingerprint("q2")
        g1 = gold_fingerprint("youth", "1")
        with self.assertRaises(ValueError):
            validate_fingerprint_manifest(_valid_manifest([q1], [g1], cases=2))
        with self.assertRaises(ValueError):
            validate_fingerprint_manifest(_valid_manifest([q1, q2], [g1], cases=2))
        with self.assertRaises(ValueError):
            manifest_with_fingerprints(role="dev", cycle=3, cases=5, query_fingerprints=[q1], gold_fingerprints=[g1])
        with self.assertRaises((ValueError, TypeError)):
            validate_fingerprint_manifest(_valid_manifest([q1], [g1], cases=0))
        with self.assertRaises((ValueError, TypeError)):
            validate_fingerprint_manifest(_valid_manifest([q1], [g1], cases=-1))
        with self.assertRaises((ValueError, TypeError)):
            validate_fingerprint_manifest(_valid_manifest([q1], [g1], cases="2"))

    def test_manifest_with_fingerprints_hides_nothing(self):
        q = query_fingerprint("q1")
        g = gold_fingerprint("youth", "1")
        m = manifest_with_fingerprints(role="dev", cycle=3, cases=1, query_fingerprints=[q], gold_fingerprints=[g])
        self.assertEqual(1, m["cases"])
        self.assertEqual([q], m["query_fingerprints"])
        with self.assertRaises(ValueError):
            manifest_with_fingerprints(role="dev", cycle=3, cases=1, query_fingerprints=[q, q], gold_fingerprints=[g])

    def test_check_overlap_validates_before_calc(self):
        good = _valid_manifest([query_fingerprint("a")], [gold_fingerprint("youth", "1")])
        bad = {}
        with self.assertRaises((ValueError, TypeError)):
            check_overlap(good, bad, strict=True)
        with self.assertRaises((ValueError, TypeError)):
            check_overlap(bad, good, strict=True)


class AuditInfraRepairTest(unittest.TestCase):
    def test_stale_wrong_set_sha_fail(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            sha_a = "a" * 64
            sha_b = "b" * 64
            append_event(log, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="holdout", set_sha=sha_a, git_head="0"*40, git_dirty=False, session_id="sess-1", outcome="success")
            with self.assertRaises(AuditError):
                verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha_b, session_id="sess-1")
            verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha_a, session_id="sess-1")

    def test_wrong_session_fail(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            sha = "c" * 64
            append_event(log, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id="sess-actual", outcome="success")
            with self.assertRaises(AuditError):
                verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha, session_id="sess-wrong")
            verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha, session_id="sess-actual")

    def test_access_end_closes_grant_fail(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            sha = "d" * 64
            sess = "sess-1"
            ev_start = append_event(log, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id=sess, outcome="success")
            verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha, session_id=sess)
            verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha, session_id=sess, expected_event_hash=ev_start["event_hash"])
            append_event(log, action="protected_access_end", candidate_id="c3e1-vector-pool-128", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id=sess, outcome="closed")
            with self.assertRaises(AuditError):
                verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha, session_id=sess)
            with self.assertRaises(AuditError):
                verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha, session_id=sess, expected_event_hash=ev_start["event_hash"])
            ev2 = append_event(log, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id=sess, outcome="allowed")
            verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha, session_id=sess, expected_event_hash=ev2["event_hash"])
            with self.assertRaises(AuditError):
                verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha, session_id=sess, expected_event_hash=ev_start["event_hash"])

    def test_outcome_none_and_failure_fail(self):
        sha = "e" * 64
        for outcome in [None, "failure", "failed", "error", ""]:
            with tempfile.TemporaryDirectory() as td2:
                log2 = pathlib.Path(td2) / "events.jsonl"
                append_event(log2, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id="s1", outcome=outcome)
                with self.assertRaises(AuditError):
                    verify_holdout_access_allowed(log2, set_role="holdout", set_sha=sha, session_id="s1")
        with tempfile.TemporaryDirectory() as td3:
            log3 = pathlib.Path(td3) / "events.jsonl"
            append_event(log3, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id="s1", outcome="success")
            verify_holdout_access_allowed(log3, set_role="holdout", set_sha=sha, session_id="s1")
        with tempfile.TemporaryDirectory() as td4:
            log4 = pathlib.Path(td4) / "events.jsonl"
            append_event(log4, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id="s1", outcome="allowed")
            verify_holdout_access_allowed(log4, set_role="holdout", set_sha=sha, session_id="s1")

    def test_non_v4_uuid_fail(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            # uuid1
            u1 = str(uuid.uuid1())
            with self.assertRaises(AuditSchemaError):
                append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="none", git_head="0"*40, git_dirty=False, session_id="s1", event_id=u1)
            u3 = str(uuid.uuid3(uuid.NAMESPACE_DNS, "example"))
            with self.assertRaises(AuditSchemaError):
                append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="none", git_head="0"*40, git_dirty=False, session_id="s1", event_id=u3)
            with self.assertRaises(AuditSchemaError):
                append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="none", git_head="0"*40, git_dirty=False, session_id="s1", event_id="not-a-uuid")
            valid_v4 = str(uuid.uuid4())
            ev = append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="none", git_head="0"*40, git_dirty=False, session_id="s1", event_id=valid_v4)
            self.assertEqual(valid_v4.lower(), ev["event_id"].lower())
            fresh_v4 = str(uuid.uuid4())
            upper_v4 = fresh_v4.upper()
            ev2 = append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="none", git_head="0"*40, git_dirty=False, session_id="s1", event_id=upper_v4)
            self.assertEqual(fresh_v4.lower(), ev2["event_id"].lower())

    def test_invalid_timestamp_fail(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            bad_timestamps = [
                "2026-08-30 09:34:01Z",
                "2026-08-30T09:34:01",
                "2026-08-30T09:34:01+09:00",
                "2026/08/30T09:34:01Z",
                "not-a-timestamp",
                "2026-13-01T00:00:00Z",
                "",
            ]
            for ts in bad_timestamps:
                with self.assertRaises(AuditSchemaError, msg=f"should fail for {ts!r}"):
                    append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="none", git_head="0"*40, git_dirty=False, session_id="s1", utc_timestamp=ts)
            ev = append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="none", git_head="0"*40, git_dirty=False, session_id="s1", utc_timestamp="2026-08-30T09:34:01Z")
            self.assertEqual("2026-08-30T09:34:01Z", ev["utc_timestamp"])
            ev2 = append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="none", git_head="0"*40, git_dirty=False, session_id="s1", utc_timestamp="2026-08-30T09:34:01.123456Z")
            self.assertIn("2026-08-30T09:34:01.123456Z", ev2["utc_timestamp"])

    def test_strict_field_validations(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            sha = "a" * 64
            with self.assertRaises(AuditSchemaError):
                append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="none", git_head="0"*40, git_dirty=1, session_id="s1")  # type: ignore
            with self.assertRaises(AuditSchemaError):
                append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="none", git_head="0"*40, git_dirty="false", session_id="s1")  # type: ignore
            with self.assertRaises(AuditSchemaError):
                append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="none", git_head="0"*40, git_dirty=False, session_id="s1", process_id=0)
            with self.assertRaises(AuditSchemaError):
                append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="none", git_head="0"*40, git_dirty=False, session_id="s1", process_id=-1)
            with self.assertRaises(AuditSchemaError):
                append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="none", git_head="0"*40, git_dirty=False, session_id="s1", process_id=True)  # type: ignore
            with self.assertRaises(AuditSchemaError):
                append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="none", git_head="0"*40, git_dirty=False, session_id="")
            with self.assertRaises(AuditSchemaError):
                append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="none", git_head="0"*40, git_dirty=False, session_id="   ")
            with self.assertRaises(AuditSchemaError):
                append_event(log, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="dev", set_sha="short", git_head="0"*40, git_dirty=False, session_id="s1", outcome="success")
            with self.assertRaises(AuditSchemaError):
                append_event(log, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="dev", set_sha=None, git_head="0"*40, git_dirty=False, session_id="s1", outcome="success")
            with self.assertRaises(AuditSchemaError):
                append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="none", set_sha="a"*64, git_head="0"*40, git_dirty=False, session_id="s1")
            with self.assertRaises(AuditSchemaError):
                append_event(log, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="none", set_sha="a"*64, git_head="0"*40, git_dirty=False, session_id="s1", outcome="success")
            with self.assertRaises(AuditSchemaError):
                append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="none", git_head="unknown", git_dirty=False, session_id="s1")
            with self.assertRaises(AuditSchemaError):
                append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="none", git_head="short", git_dirty=False, session_id="s1")

    def test_git_provenance_failure_fails(self):
        orig_run = subprocess.run

        def fake_fail(*args, **kwargs):
            class R:
                returncode = 1
                stdout = ""
                stderr = "fatal: not a git repo"
            return R()

        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            import retrieval_v2.cycle3_audit as audit_mod
            old = audit_mod.subprocess.run
            audit_mod.subprocess.run = fake_fail  # type: ignore
            try:
                with self.assertRaises(AuditError):
                    append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="none", session_id="s1")
                audit_mod.subprocess.run = fake_fail
                ev = append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="none", git_head="0"*40, git_dirty=False, session_id="s1")
                self.assertEqual("0"*40, ev["git_head"])
            finally:
                audit_mod.subprocess.run = old

    def test_token_stale_grant_structurally_blocked(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            sha = "f" * 64
            sess = "sess-token"
            ev1 = append_event(log, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id=sess, outcome="success")
            token1 = ev1["event_hash"]
            ev2 = append_event(log, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id=sess, outcome="success")
            token2 = ev2["event_hash"]
            with self.assertRaises(AuditError):
                verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha, session_id=sess, expected_event_hash=token1)
            verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha, session_id=sess, expected_event_hash=token2)
            verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha, session_id=sess)


# --- NARROW INFRA REPAIR v3 additional gates (Sol/High + Luna Max 합의 3개) ---

class AuditLatestStartFailOpenTest(unittest.TestCase):
    """Blocker 1: verify_holdout_access_allowed latest-start fail-open repair.

    Must pick latest protected_access_start among ALL (not just success) for same
    set_role+set_sha+session_id, then check outcome success/allowed. Success->failure
    and success->None must DENY.
    """

    def test_success_then_failure_denies(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            sha = "a" * 64
            sess = "sess-latest"
            append_event(log, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id=sess, outcome="success")
            append_event(log, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id=sess, outcome="failure")
            with self.assertRaises(AuditError):
                verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha, session_id=sess)

    def test_success_then_none_denies(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            sha = "b" * 64
            sess = "sess-latest-none"
            append_event(log, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id=sess, outcome="success")
            append_event(log, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id=sess, outcome=None)
            with self.assertRaises(AuditError):
                verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha, session_id=sess)

    def test_success_then_allowed_grants(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            sha = "c" * 64
            sess = "sess-grant"
            append_event(log, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id=sess, outcome="success")
            ev2 = append_event(log, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id=sess, outcome="allowed")
            # latest is allowed -> grant
            result = verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha, session_id=sess)
            self.assertEqual(ev2["event_hash"], result["event_hash"])

    def test_failure_then_success_grants(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            sha = "d" * 64
            sess = "sess-fail-then-success"
            append_event(log, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id=sess, outcome="failure")
            ev2 = append_event(log, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id=sess, outcome="success")
            result = verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha, session_id=sess)
            self.assertEqual(ev2["event_hash"], result["event_hash"])
            # token must match latest, not earlier success (there was none earlier success, but now latest success)
            with self.assertRaises(AuditError):
                # token from non-existent earlier would be invalid; use mismatched token
                verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha, session_id=sess, expected_event_hash="0"*64)

    def test_single_failure_denies(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            sha = "e" * 64
            sess = "sess-single-fail"
            append_event(log, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id=sess, outcome="failure")
            with self.assertRaises(AuditError):
                verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha, session_id=sess)

    def test_success_then_empty_string_denies(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            sha = "f" * 64
            sess = "sess-empty"
            append_event(log, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id=sess, outcome="success")
            append_event(log, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id=sess, outcome="")
            with self.assertRaises(AuditError):
                verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha, session_id=sess)


class FingerprintBuilderGateTest(unittest.TestCase):
    """Blocker 2: protected-set fingerprint builder gate.

    Builder/protected-set validation boundary must require cases mandatory,
    exact count match, and 0 forbidden. Empty manifest cannot certify overlap 0 PASS.
    """

    def test_missing_cases_fails(self):
        q = query_fingerprint("hello")
        g = gold_fingerprint("youth", "1")
        with self.assertRaises(ValueError):
            validate_fingerprint_manifest({"fingerprint_version": FINGERPRINT_VERSION, "normalization_spec": NORMALIZATION_SPEC, "query_fingerprints": [q], "gold_fingerprints": [g]})
        with self.assertRaises((ValueError, TypeError)):
            check_overlap({"fingerprint_version": FINGERPRINT_VERSION, "normalization_spec": NORMALIZATION_SPEC, "query_fingerprints": [q], "gold_fingerprints": [g]},
                          {"fingerprint_version": FINGERPRINT_VERSION, "normalization_spec": NORMALIZATION_SPEC, "query_fingerprints": [q], "gold_fingerprints": [g]}, strict=False)

    def test_zero_cases_forbidden(self):
        q = query_fingerprint("q")
        g = gold_fingerprint("youth", "1")
        with self.assertRaises(ValueError):
            validate_fingerprint_manifest({"fingerprint_version": FINGERPRINT_VERSION, "normalization_spec": NORMALIZATION_SPEC, "query_fingerprints": [], "gold_fingerprints": [], "cases": 0})
        with self.assertRaises(ValueError):
            manifest_with_fingerprints(role="dev", cycle=3, cases=0, query_fingerprints=[], gold_fingerprints=[])
        # empty manifest overlap must not PASS
        empty_a = {"fingerprint_version": FINGERPRINT_VERSION, "normalization_spec": NORMALIZATION_SPEC, "query_fingerprints": [], "gold_fingerprints": [], "cases": 0}
        empty_b = {"fingerprint_version": FINGERPRINT_VERSION, "normalization_spec": NORMALIZATION_SPEC, "query_fingerprints": [], "gold_fingerprints": [], "cases": 0}
        with self.assertRaises(ValueError):
            check_overlap(empty_a, empty_b, strict=True)
        with self.assertRaises(ValueError):
            check_overlap(empty_a, empty_b, strict=False)

    def test_empty_manifest_no_cases_cannot_pass_overlap(self):
        # Historical catalog / fresh holdout / fresh dev builder cannot certify empty as PASS
        empty_no_cases_a = {"fingerprint_version": FINGERPRINT_VERSION, "normalization_spec": NORMALIZATION_SPEC, "query_fingerprints": [], "gold_fingerprints": []}
        empty_no_cases_b = {"fingerprint_version": FINGERPRINT_VERSION, "normalization_spec": NORMALIZATION_SPEC, "query_fingerprints": [], "gold_fingerprints": []}
        with self.assertRaises((ValueError, TypeError)):
            check_overlap(empty_no_cases_a, empty_no_cases_b, strict=True)
        with self.assertRaises((ValueError, TypeError)):
            check_overlap(empty_no_cases_a, empty_no_cases_b, strict=False)
        # Even with manifest_with_fingerprints building empty must fail
        with self.assertRaises(ValueError):
            manifest_with_fingerprints(role="historical", cycle=1, cases=1, query_fingerprints=[], gold_fingerprints=[])

    def test_cases_exact_count_required(self):
        q1 = query_fingerprint("q1")
        q2 = query_fingerprint("q2")
        g1 = gold_fingerprint("youth", "1")
        g2 = gold_fingerprint("gov24", "2")
        # cases 1 but 2 fingerprints -> mismatch
        with self.assertRaises(ValueError):
            validate_fingerprint_manifest({"fingerprint_version": FINGERPRINT_VERSION, "normalization_spec": NORMALIZATION_SPEC, "query_fingerprints": [q1, q2], "gold_fingerprints": [g1, g2], "cases": 1})
        with self.assertRaises(ValueError):
            validate_fingerprint_manifest({"fingerprint_version": FINGERPRINT_VERSION, "normalization_spec": NORMALIZATION_SPEC, "query_fingerprints": [q1], "gold_fingerprints": [g1, g2], "cases": 1})
        with self.assertRaises(ValueError):
            manifest_with_fingerprints(role="dev", cycle=3, cases=2, query_fingerprints=[q1], gold_fingerprints=[g1])
        # correct exact match passes
        m = manifest_with_fingerprints(role="dev", cycle=3, cases=2, query_fingerprints=[q1, q2], gold_fingerprints=[g1, g2])
        self.assertEqual(2, m["cases"])
        # overlap with correct cases passes when distinct
        a = manifest_with_fingerprints(role="dev", cycle=3, cases=1, query_fingerprints=[q1], gold_fingerprints=[g1])
        b = manifest_with_fingerprints(role="holdout", cycle=3, cases=1, query_fingerprints=[q2], gold_fingerprints=[g2])
        result = check_overlap(a, b, strict=False)
        self.assertEqual(0, result["query_overlap"])

    def test_builder_empty_fingerprint_lists_fail(self):
        # Builder with expected count vs actual fingerprint lists mismatch
        q = query_fingerprint("q1")
        g = gold_fingerprint("youth", "1")
        with self.assertRaises(ValueError):
            manifest_with_fingerprints(role="fresh-dev", cycle=3, cases=2, query_fingerprints=[q], gold_fingerprints=[g])
        with self.assertRaises(ValueError):
            manifest_with_fingerprints(role="fresh-holdout", cycle=3, cases=1, query_fingerprints=[], gold_fingerprints=[g])


class AuditDurabilityTest(unittest.TestCase):
    """Blocker 3: append_event durability — os.fsync failure must propagate as AuditError, no success token."""

    def test_fsync_failure_raises_audit_error(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            import retrieval_v2.cycle3_audit as audit_mod
            orig_fsync = audit_mod.os.fsync

            def fake_fsync(fd):
                raise OSError("simulated fsync failure")

            audit_mod.os.fsync = fake_fsync  # type: ignore
            try:
                with self.assertRaises(AuditError) as ctx:
                    append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="none", git_head="0"*40, git_dirty=False, session_id="sess-dur")
                self.assertIn("fsync", str(ctx.exception).lower())
            finally:
                audit_mod.os.fsync = orig_fsync  # type: ignore

    def test_fsync_failure_no_success_token(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            import retrieval_v2.cycle3_audit as audit_mod
            orig_fsync = audit_mod.os.fsync
            call_count = {"n": 0}

            def failing_fsync(fd):
                call_count["n"] += 1
                raise OSError("disk full")

            audit_mod.os.fsync = failing_fsync  # type: ignore
            try:
                token = None
                try:
                    token = append_event(log, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="holdout", set_sha="a"*64, git_head="0"*40, git_dirty=False, session_id="s1", outcome="success")
                except AuditError:
                    pass
                self.assertIsNone(token, "event/token must not be returned on fsync failure")
                self.assertEqual(1, call_count["n"])
            finally:
                audit_mod.os.fsync = orig_fsync  # type: ignore

    def test_fsync_success_still_works(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            ev = append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="none", git_head="0"*40, git_dirty=False, session_id="s1")
            self.assertIn("event_hash", ev)
            # verify chain readable
            chain = read_and_verify_chain(log)
            self.assertEqual(1, len(chain))
            self.assertEqual(ev["event_hash"], chain[0]["event_hash"])
