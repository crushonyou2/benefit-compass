import hashlib
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from retrieval_v2.cycle3_fingerprint import (
    FINGERPRINT_VERSION,
    NORMALIZATION_SPEC,
    check_overlap,
    gold_fingerprint,
    query_fingerprint,
    validate_fingerprint_manifest,
    manifest_with_fingerprints,
)
from retrieval_v2.cycle3_historical_catalog import (
    load_historical_catalog,
    get_union_manifest,
    get_union_sets,
    check_fresh_no_overlap,
    load_per_set_manifests,
)
from retrieval_v2.cycle3_audit import read_and_verify_chain

ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG_DIR = ROOT / "eval" / "retrieval-v2" / "cycle3" / "catalog"
AUDIT_LOG = ROOT / "eval" / "retrieval-v2" / "cycle3" / "audit" / "events.jsonl"

class HistoricalCatalogManifestTest(unittest.TestCase):
    def test_catalog_exists_and_single_file_entrypoint(self):
        self.assertTrue((CATALOG_DIR / "catalog.json").exists(), "entrypoint catalog.json missing")
        cat = load_historical_catalog()
        self.assertEqual("v1", cat["fingerprint_version"])
        self.assertEqual(NORMALIZATION_SPEC, cat["normalization_spec"])
        self.assertEqual("v1", cat["catalog_version"])

    def test_six_historical_sets_present(self):
        cat = load_historical_catalog()
        ids = {s["id"] for s in cat["historical_sets"]}
        expected = {"p0", "cycle1_dev", "cycle1_holdout", "cycle2_dev", "cycle2_holdout_disqualified", "hard_negative"}
        self.assertEqual(expected, ids)

    def test_per_set_manifests_valid_and_counts(self):
        cat = load_historical_catalog()
        expected_counts = {"p0": 81, "cycle1_dev": 36, "cycle1_holdout": 40, "cycle2_dev": 36, "cycle2_holdout_disqualified": 40, "hard_negative": 36}
        for entry in cat["historical_sets"]:
            sid = entry["id"]
            path = CATALOG_DIR / f"{sid}.json"
            self.assertTrue(path.exists(), f"{sid}.json missing")
            m = json.loads(path.read_text(encoding="utf-8"))
            validate_fingerprint_manifest(m)
            self.assertEqual(FINGERPRINT_VERSION, m["fingerprint_version"])
            self.assertEqual(NORMALIZATION_SPEC, m["normalization_spec"])
            self.assertEqual(expected_counts[sid], m["cases"], f"{sid} cases mismatch")
            self.assertEqual(m["cases"], len(m["query_fingerprints"]), f"{sid} query count != cases")
            self.assertEqual(m["cases"], len(m["gold_fingerprints"]), f"{sid} gold count != cases")
            # each 64-hex
            for fp in m["query_fingerprints"]:
                self.assertRegex(fp, r"^[0-9a-f]{64}$", f"{sid} query fp not 64-hex")
            for fp in m["gold_fingerprints"]:
                self.assertRegex(fp, r"^[0-9a-f]{64}$", f"{sid} gold fp not 64-hex")
            # no duplicate (validate already checks, but explicit)
            self.assertEqual(len(m["query_fingerprints"]), len(set(s.lower() for s in m["query_fingerprints"])), f"{sid} query duplicate")
            self.assertEqual(len(m["gold_fingerprints"]), len(set(s.lower() for s in m["gold_fingerprints"])), f"{sid} gold duplicate")
            # provenance present, plaintext-free
            self.assertIn("provenance", m)
            self.assertNotIn("query", json.dumps(m).lower()[:5000] if "의성군" in json.dumps(m) else "")

    def test_catalog_counts_detail(self):
        cat = load_historical_catalog()
        self.assertEqual(81, cat["counts_detail"]["p0"])
        self.assertEqual(36, cat["counts_detail"]["cycle1_dev"])
        self.assertEqual(40, cat["counts_detail"]["cycle1_holdout"])
        self.assertEqual(36, cat["counts_detail"]["cycle2_dev"])
        self.assertEqual(40, cat["counts_detail"]["cycle2_holdout_disqualified"])
        self.assertEqual(36, cat["counts_detail"]["hard_negative"])
        self.assertEqual(248, cat["counts_detail"]["union_query"])
        self.assertEqual(248, cat["counts_detail"]["union_gold"])
        self.assertEqual(269, cat["counts_detail"]["sum_cases_query"])

    def test_union_single_file_load(self):
        cat = load_historical_catalog()
        union = cat["union"]
        self.assertEqual(248, union["query_count"])
        self.assertEqual(248, union["gold_count"])
        self.assertEqual(248, len(union["query_fingerprints"]))
        self.assertEqual(248, len(union["gold_fingerprints"]))
        # union manifest valid
        um = get_union_manifest(cat)
        validate_fingerprint_manifest(um)

    def test_no_plaintext_reversible_identifiers(self):
        # Ensure catalog files contain no raw query substrings or reversible gold titles
        for p in CATALOG_DIR.iterdir():
            if p.suffix != ".json":
                continue
            txt = p.read_text(encoding="utf-8")
            # Check for obvious Korean query fragments that would indicate leak
            for leaked in ["의성군", "청년키움", "신혼부부", "주거비", "기초연금", "아동수당"]:
                self.assertNotIn(leaked, txt, f"plaintext leak {leaked} in {p.name}")
            # Ensure no raw policy title leaked as plaintext beyond provenance (provenance has no titles)
            # We just ensure file doesn't contain long raw query (heuristic: no "지원받을 수 있나요" raw)
            self.assertNotIn("지원받을 수 있나요", txt, f"plaintext query leak in {p.name}")

    def test_historical_inter_overlap_expected(self):
        cat = load_historical_catalog()
        pairs = { (d["a"], d["b"]): d for d in cat["inter_overlap"]["pairs"] }
        # Build normalized pair keys (unordered)
        def get_pair(a,b):
            if (a,b) in pairs: return pairs[(a,b)]
            if (b,a) in pairs: return pairs[(b,a)]
            return None
        # P0 vs hard_negative expected 21/21
        p = get_pair("p0", "hard_negative")
        self.assertIsNotNone(p)
        self.assertEqual(21, p["query_overlap"])
        self.assertEqual(21, p["gold_overlap"])
        self.assertEqual("expected_allowed", p["status"])
        # All other pairs must be 0
        for d in cat["inter_overlap"]["pairs"]:
            if {d["a"], d["b"]} == {"p0", "hard_negative"}:
                continue
            self.assertEqual(0, d["query_overlap"], f"{d['a']} vs {d['b']} query overlap must be 0")
            self.assertEqual(0, d["gold_overlap"], f"{d['a']} vs {d['b']} gold overlap must be 0")
            self.assertEqual("pass", d["status"])
        self.assertTrue(cat["inter_overlap"]["overall_pass"])

    def test_overlap_detection_fail_closed(self):
        cat = load_historical_catalog()
        # Synthesize fresh manifest overlapping with p0 query
        p0_manifest = json.loads((CATALOG_DIR / "p0.json").read_text(encoding="utf-8"))
        # Take one query fingerprint from p0
        overlapping_q = p0_manifest["query_fingerprints"][0]
        overlapping_g = p0_manifest["gold_fingerprints"][0]
        # Fresh with 1 overlapping query should be detected
        fresh_overlap_q = manifest_with_fingerprints(role="holdout", cycle=3, cases=1, query_fingerprints=[overlapping_q], gold_fingerprints=[gold_fingerprint("youth", "unique-fresh-id-12345")])
        res = check_fresh_no_overlap(fresh_overlap_q, cat)
        self.assertEqual(1, res["query_overlap"])
        # strict should raise
        union = get_union_manifest(cat)
        with self.assertRaises(ValueError):
            check_overlap(fresh_overlap_q, union, strict=True)
        # Fresh with no overlap should pass
        fresh_clean = manifest_with_fingerprints(role="holdout", cycle=3, cases=2, query_fingerprints=[query_fingerprint("completely fresh query one 2026"), query_fingerprint("completely fresh query two 2026 different")], gold_fingerprints=[gold_fingerprint("youth","fresh-unique-1"), gold_fingerprint("gov24","fresh-unique-2")])
        res2 = check_fresh_no_overlap(fresh_clean, cat)
        self.assertEqual(0, res2["query_overlap"])
        self.assertEqual(0, res2["gold_overlap"])
        # And strict passes
        check_overlap(fresh_clean, union, strict=True)

    def test_gold_overlap_detection(self):
        cat = load_historical_catalog()
        p0_manifest = json.loads((CATALOG_DIR / "p0.json").read_text(encoding="utf-8"))
        overlapping_g = p0_manifest["gold_fingerprints"][0]
        fresh_g_overlap = manifest_with_fingerprints(role="dev", cycle=3, cases=1, query_fingerprints=[query_fingerprint("fresh query gold overlap test")], gold_fingerprints=[overlapping_g])
        res = check_fresh_no_overlap(fresh_g_overlap, cat)
        self.assertEqual(1, res["gold_overlap"])

    def test_per_set_manifests_loadable_via_helper(self):
        per = load_per_set_manifests()
        self.assertEqual(6, len(per))
        for sid, m in per.items():
            validate_fingerprint_manifest(m)

    def test_catalog_union_via_helper(self):
        qset, gset = get_union_sets()
        self.assertEqual(248, len(qset))
        self.assertEqual(248, len(gset))

    def test_audit_chain_and_schema_limitation(self):
        self.assertTrue(AUDIT_LOG.exists(), "audit log missing")
        events = read_and_verify_chain(AUDIT_LOG)
        # At least 10 events from this freeze
        self.assertGreaterEqual(len(events), 10)
        # Check that P0/hard_negative were not logged as protected_access with false role
        for ev in events:
            if ev.get("command") in ("build_historical_catalog:p0", "build_historical_catalog:hard_negative"):
                self.assertEqual("none", ev["set_role"])
                self.assertIsNone(ev["set_sha"])
        # Protected sets must have dev/holdout role and 64-hex sha
        for ev in events:
            if ev.get("command") == "build_historical_catalog" and ev.get("action") in ("protected_access_start", "protected_access_end"):
                self.assertIn(ev["set_role"], ("dev", "holdout"))
                self.assertRegex(ev["set_sha"], r"^[0-9a-f]{64}$")
        # Catalog documents schema limitation
        cat = load_historical_catalog()
        self.assertIn("schema_limitation", cat["audit"])
        self.assertIn("P0/hard-negative", cat["audit"]["schema_limitation"])

    def test_provenance_hashes_present(self):
        cat = load_historical_catalog()
        for entry in cat["historical_sets"]:
            prov = entry["provenance"]
            self.assertIsNotNone(prov)
            # Each has sha256 fields
            # P0 has youth_sha256/gov24_sha256, others have sha256
            has_sha = "sha256" in prov or "youth_sha256" in prov
            self.assertTrue(has_sha, f"{entry['id']} missing sha256")

    def test_fingerprint_version_and_spec_consistent(self):
        cat = load_historical_catalog()
        self.assertEqual("v1", cat["fingerprint_version"])
        self.assertEqual(NORMALIZATION_SPEC, cat["normalization_spec"])
        # per-set also
        for p in CATALOG_DIR.iterdir():
            if p.suffix != ".json" or p.name == "catalog.json":
                continue
            m = json.loads(p.read_text(encoding="utf-8"))
            self.assertEqual("v1", m["fingerprint_version"])
            self.assertEqual(NORMALIZATION_SPEC, m["normalization_spec"])
