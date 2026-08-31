import hashlib
import json
import pathlib
import re
import sys
from collections import Counter


ROOT = pathlib.Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "eval"
HOLDOUT_DIR = EVAL_DIR / "retrieval-v2" / "cycle3" / "holdout"
CATALOG_PATH = EVAL_DIR / "retrieval-v2" / "cycle3" / "catalog" / "catalog.json"

sys.path.insert(0, str(EVAL_DIR))

from retrieval_v2.cycle3_fingerprint import (  # noqa: E402
    check_overlap,
    gold_fingerprint,
    query_fingerprint,
    validate_fingerprint_manifest,
)


EXPECTED_EVALSET_SHA = "4c631ce7cdcc03374bb1861d0a27e0ebbacf35a691fb6f54543b96c7f051c350"
EXPECTED_SOURCE = {"youth": 20, "gov24": 20}
EXPECTED_CATEGORY = {
    "housing_finance": 7,
    "family_care": 7,
    "employment_education": 7,
    "welfare_health": 7,
    "culture_community": 6,
    "business_agriculture": 6,
}


def _sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: pathlib.Path):
    return json.loads(path.read_text(encoding="utf-8"))


def _cases():
    return [
        json.loads(line)
        for line in (HOLDOUT_DIR / "evalset.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_holdout_evalset_identity_and_shape():
    p = HOLDOUT_DIR / "evalset.jsonl"
    assert _sha(p) == EXPECTED_EVALSET_SHA
    cases = _cases()
    assert len(cases) == 40
    assert [c["case_id"] for c in cases] == [f"c3h-{i:03d}" for i in range(1, 41)]
    assert Counter(c["gold_source"] for c in cases) == Counter(EXPECTED_SOURCE)
    assert Counter(c["category"] for c in cases) == Counter(EXPECTED_CATEGORY)
    required = {"case_id", "query", "gold_source", "gold_source_id", "category"}
    for c in cases:
        assert required <= set(c)
        assert c["query"].strip()
        assert c["gold_source"] in {"youth", "gov24"}
        assert str(c["gold_source_id"]).strip()


def test_fingerprints_match_evalset_and_are_unique():
    cases = _cases()
    fp = _json(HOLDOUT_DIR / "fingerprints.json")
    validate_fingerprint_manifest(fp)
    assert fp["role"] == "holdout"
    assert fp["cycle"] == 3
    assert fp["cases"] == 40
    q = [query_fingerprint(c["query"]) for c in cases]
    g = [gold_fingerprint(c["gold_source"], str(c["gold_source_id"])) for c in cases]
    assert sorted(fp["query_fingerprints"]) == sorted(q)
    assert sorted(fp["gold_fingerprints"]) == sorted(g)
    assert len(set(q)) == 40
    assert len(set(g)) == 40


def test_historical_overlap_zero_fail_closed():
    fresh = _json(HOLDOUT_DIR / "fingerprints.json")
    catalog = _json(CATALOG_PATH)
    union = {
        "fingerprint_version": catalog["fingerprint_version"],
        "normalization_spec": catalog["normalization_spec"],
        "cases": catalog["union"]["query_count"],
        "query_fingerprints": catalog["union"]["query_fingerprints"],
        "gold_fingerprints": catalog["union"]["gold_fingerprints"],
    }
    validate_fingerprint_manifest(union)
    result = check_overlap(fresh, union, strict=True)
    assert result["query_overlap"] == 0
    assert result["gold_overlap"] == 0


def test_annotation_and_generation_contract():
    annotation = _json(HOLDOUT_DIR / "annotation_audit.json")
    plan = _json(HOLDOUT_DIR / "generation_plan.json")
    assert annotation["cases"] == 40
    assert annotation["well_posed"] == 40
    assert annotation["ambiguous"] == 0
    assert len(annotation["cases_audit"]) == 40
    assert plan["cases"] == 40
    assert plan["source_totals"] == EXPECTED_SOURCE
    assert plan["category_totals"] == EXPECTED_CATEGORY
    assert plan["stable_order"] == "sha256(seed + NUL + source + NUL + source_id), ascending"
    assert "retrieval/ranking" in plan["forbidden"]
    assert "fresh dev" in plan["forbidden"]


def test_provenance_hash_dag_is_exact():
    manifest = _json(HOLDOUT_DIR / "manifest.json")
    report = _json(HOLDOUT_DIR / "builder_report.json")
    core = {"evalset.jsonl", "fingerprints.json", "annotation_audit.json"}
    assert set(manifest["files"]) == core
    for name in core:
        assert manifest["files"][name]["sha256"].lower() == _sha(HOLDOUT_DIR / name)
        assert manifest["files"][name]["cases"] == 40

    report_expected = core | {"manifest.json"}
    assert set(report["files"]) == report_expected
    assert set(report["hashes"]) == report_expected
    for name in report_expected:
        actual = _sha(HOLDOUT_DIR / name)
        assert report["files"][name]["sha256"].lower() == actual
        assert report["hashes"][name].lower() == actual

    sealed = (HOLDOUT_DIR / "SEALED.md").read_text(encoding="utf-8")
    found = {
        m.group(1): m.group(2).lower()
        for m in re.finditer(r"output/(\S+?)`.*?SHA256\s*`([0-9a-fA-F]{64})`", sealed)
    }
    sealed_expected = report_expected | {"builder_report.json"}
    assert set(found) == sealed_expected
    for name in sealed_expected:
        assert found[name] == _sha(HOLDOUT_DIR / name)
    assert _sha(HOLDOUT_DIR / "SEALED.md") not in sealed


def test_builder_report_is_plaintext_free_of_case_queries_and_ids():
    cases = _cases()
    text = (HOLDOUT_DIR / "builder_report.json").read_text(encoding="utf-8")
    for c in cases:
        assert c["query"] not in text
        assert str(c["gold_source_id"]) not in text
