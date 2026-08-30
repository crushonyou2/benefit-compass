import hashlib
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from retrieval_v2.cycle3_fingerprint import (
    FINGERPRINT_VERSION,
    NORMALIZATION_SPEC,
    check_overlap,
    fingerprints_for_items,
    gold_fingerprint,
    normalize_query,
    query_fingerprint,
    validate_fingerprint_manifest,
    manifest_with_fingerprints,
)

def _m(qfps, gfps, cases=None):
    # Helper for tests: if cases not supplied, infer from lengths when they match and >0;
    # empty manifests intentionally left without cases to test gate failure, caller must pass cases explicitly for valid manifests.
    d = {
        "fingerprint_version": FINGERPRINT_VERSION,
        "normalization_spec": NORMALIZATION_SPEC,
        "query_fingerprints": qfps,
        "gold_fingerprints": gfps,
    }
    if cases is not None:
        d["cases"] = cases
    elif len(qfps) == len(gfps) and len(qfps) > 0:
        # Auto-infer cases for valid non-empty manifests to reduce test boilerplate
        d["cases"] = len(qfps)
    return d

class Cycle3FingerprintTest(unittest.TestCase):
    def test_normalize_query_deterministic(self):
        self.assertEqual("hello world", normalize_query("  hello   world  "))
        self.assertEqual("hello world", normalize_query("hello\tworld\n"))
        self.assertEqual("청년 지원", normalize_query(" 청년  지원 "))
        # NFC: composed vs decomposed same
        self.assertEqual(normalize_query("가"), normalize_query("가"))
        # casefold
        self.assertEqual("hello", normalize_query("Hello"))
        self.assertEqual("hello", normalize_query("HELLO"))

    def test_query_fingerprint_stable(self):
        # Known vector: SHA256 of normalized "hello world"
        expected = hashlib.sha256("hello world".encode("utf-8")).hexdigest()
        self.assertEqual(expected, query_fingerprint("  hello   world "))
        self.assertEqual(expected, query_fingerprint("HELLO   WORLD"))
        # Korean unchanged by casefold
        q = "청년 정책 지원"
        self.assertEqual(query_fingerprint(q), query_fingerprint(" 청년  정책   지원 "))

    def test_gold_fingerprint_with_nul(self):
        # SHA256("youth\x00policy-123")
        expected = hashlib.sha256("youth\x00policy-123".encode("utf-8")).hexdigest()
        self.assertEqual(expected, gold_fingerprint("youth", "policy-123"))
        expected2 = hashlib.sha256("gov24\x00GOV-999".encode("utf-8")).hexdigest()
        self.assertEqual(expected2, gold_fingerprint("gov24", "GOV-999"))
        # Different source same id -> different
        self.assertNotEqual(gold_fingerprint("youth", "123"), gold_fingerprint("gov24", "123"))
        # NUL in source_id rejected
        with self.assertRaises(ValueError):
            gold_fingerprint("youth", "a\x00b")

    def test_fingerprints_for_items(self):
        items = [
            {"query": "청년 지원 정책", "gold_source": "youth", "gold_source_id": "Y-001"},
            {"query": "고용 지원", "gold_source": "gov24", "gold_source_id": "G-002"},
        ]
        frag = fingerprints_for_items(items)
        self.assertEqual(FINGERPRINT_VERSION, frag["fingerprint_version"])
        self.assertEqual(NORMALIZATION_SPEC, frag["normalization_spec"])
        self.assertEqual(2, len(frag["query_fingerprints"]))
        self.assertEqual(2, len(frag["gold_fingerprints"]))
        # Deterministic
        self.assertEqual(query_fingerprint("청년 지원 정책"), frag["query_fingerprints"][0])
        self.assertEqual(gold_fingerprint("youth", "Y-001"), frag["gold_fingerprints"][0])
        # Alternative keys source/source_id also accepted
        items2 = [{"query": "q", "source": "youth", "source_id": "S-1"}]
        frag2 = fingerprints_for_items(items2)
        self.assertEqual(1, len(frag2["query_fingerprints"]))

    def test_check_overlap_zero(self):
        a = _m([query_fingerprint("q1"), query_fingerprint("q2")], [gold_fingerprint("youth","1"), gold_fingerprint("gov24","2")])
        b = _m([query_fingerprint("q3")], [gold_fingerprint("youth","3")])
        res = check_overlap(a, b, strict=False)
        self.assertEqual(0, res["query_overlap"])
        self.assertEqual(0, res["gold_overlap"])
        # strict should not raise
        check_overlap(a, b, strict=True)

    def test_check_overlap_detects_query(self):
        q = query_fingerprint("동일 쿼리")
        a = _m([q], [gold_fingerprint("youth","1")])
        b = _m([q], [gold_fingerprint("gov24","2")])
        res = check_overlap(a, b, strict=False)
        self.assertEqual(1, res["query_overlap"])
        self.assertEqual(0, res["gold_overlap"])
        with self.assertRaises(ValueError):
            check_overlap(a, b, strict=True)

    def test_check_overlap_detects_gold(self):
        g = gold_fingerprint("youth", "SAME")
        a = _m([query_fingerprint("q1")], [g])
        b = _m([query_fingerprint("q2")], [g])
        res = check_overlap(a, b, strict=False)
        self.assertEqual(0, res["query_overlap"])
        self.assertEqual(1, res["gold_overlap"])
        with self.assertRaises(ValueError):
            check_overlap(a, b, strict=True)

    def test_check_overlap_normalized(self):
        # "Hello   World" and "hello world" should collide after normalization, gold distinct to keep gold overlap 0
        a = _m([query_fingerprint("Hello   World")], [gold_fingerprint("youth","n1")])
        b = _m([query_fingerprint("hello world")], [gold_fingerprint("youth","n2")])
        res = check_overlap(a, b, strict=False)
        self.assertEqual(1, res["query_overlap"])

    def test_check_overlap_pure_no_file_access(self):
        # Pure helper: empty manifests must NOT certify as overlap 0 PASS — fail-closed (builder gate)
        a = _m([], [])
        b = _m([], [])
        with self.assertRaises((ValueError, TypeError)):
            check_overlap(a, b, strict=True)
        # Valid non-empty distinct manifests should PASS with overlap 0
        a2 = _m([query_fingerprint("pure-a")], [gold_fingerprint("youth","pa1")])
        b2 = _m([query_fingerprint("pure-b")], [gold_fingerprint("gov24","pb1")])
        check_overlap(a2, b2, strict=True)

    def test_no_protected_plaintext_read_in_this_test(self):
        # This test itself must not read cycle1/2 holdout plaintext; we just verify helpers operate on synthetic data
        # If helpers accidentally read files, this would fail via HOLDOUT_AUDIT_ENV gate, but we simply ensure synthetic path works
        # fingerprints_for_items returns fragment without cases; wrap into protected manifest via manifest_with_fingerprints
        frag_a = fingerprints_for_items([{"query":"synthetic query 1", "gold_source":"youth","gold_source_id":"syn-1"}])
        frag_b = fingerprints_for_items([{"query":"synthetic query 2", "gold_source":"gov24","gold_source_id":"syn-2"}])
        a = manifest_with_fingerprints(role="dev", cycle=3, cases=1, query_fingerprints=frag_a["query_fingerprints"], gold_fingerprints=frag_a["gold_fingerprints"])
        b = manifest_with_fingerprints(role="holdout", cycle=3, cases=1, query_fingerprints=frag_b["query_fingerprints"], gold_fingerprints=frag_b["gold_fingerprints"])
        check_overlap(a, b, strict=True)

    def test_fingerprint_version_present(self):
        self.assertEqual("v1", FINGERPRINT_VERSION)
        self.assertIn("casefold", NORMALIZATION_SPEC)

    def test_validate_manifest_requires_version_and_spec(self):
        # Missing version/spec should fail
        with self.assertRaises(ValueError):
            validate_fingerprint_manifest({"query_fingerprints": [], "gold_fingerprints": []})
        with self.assertRaises(ValueError):
            validate_fingerprint_manifest({"fingerprint_version": "v1", "query_fingerprints": [], "gold_fingerprints": []})
        with self.assertRaises(ValueError):
            validate_fingerprint_manifest({"fingerprint_version": "v1", "normalization_spec": NORMALIZATION_SPEC, "gold_fingerprints": []})
