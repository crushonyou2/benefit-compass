import hashlib
import json
import pathlib
import re
import sys
from collections import Counter


ROOT = pathlib.Path(__file__).resolve().parent.parent
EVAL_DIR = ROOT / "eval"
DEV_DIR = EVAL_DIR / "retrieval-v2" / "cycle3" / "dev"
CATALOG_PATH = EVAL_DIR / "retrieval-v2" / "cycle3" / "catalog" / "catalog.json"

sys.path.insert(0, str(EVAL_DIR))

from retrieval_v2.cycle3_fingerprint import (  # noqa: E402
    check_overlap,
    gold_fingerprint,
    query_fingerprint,
    validate_fingerprint_manifest,
)


EXPECTED_EVALSET_SHA = "3791368f4722b612058b7a005e17bf5f1caae4ac0437daa9d44ff28f28ca260c"
EXPECTED_HOLDOUT_FINGERPRINTS_SHA = "93be481e3c4fee700615b8f66c0c9289472ea3315c46287a91174d278c625a89"
EXPECTED_SOURCE = {"youth": 18, "gov24": 18}
EXPECTED_CATEGORY = {
    "housing_finance": 6,
    "family_care": 6,
    "employment_education": 6,
    "welfare_health": 6,
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
        for line in (DEV_DIR / "evalset.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def test_dev_evalset_identity_and_shape():
    p = DEV_DIR / "evalset.jsonl"
    assert _sha(p) == EXPECTED_EVALSET_SHA
    cases = _cases()
    assert len(cases) == 36
    assert [c["case_id"] for c in cases] == [f"c3d-{i:03d}" for i in range(1, 37)]
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
    fp = _json(DEV_DIR / "fingerprints.json")
    validate_fingerprint_manifest(fp)
    assert fp["role"] == "dev"
    assert fp["cycle"] == 3
    assert fp["cases"] == 36
    q = [query_fingerprint(c["query"]) for c in cases]
    g = [gold_fingerprint(c["gold_source"], str(c["gold_source_id"])) for c in cases]
    assert sorted(fp["query_fingerprints"]) == sorted(q)
    assert sorted(fp["gold_fingerprints"]) == sorted(g)
    assert len(set(q)) == 36
    assert len(set(g)) == 36


def test_historical_overlap_zero_fail_closed():
    fresh = _json(DEV_DIR / "fingerprints.json")
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


def test_holdout_overlap_proof_is_pinned_without_holdout_plaintext():
    manifest = _json(DEV_DIR / "manifest.json")
    report = _json(DEV_DIR / "builder_report.json")
    assert manifest["holdout_fingerprints_sha256"] == EXPECTED_HOLDOUT_FINGERPRINTS_SHA
    assert report["validation"]["holdout_overlap"] == {"query": 0, "gold": 0}


def test_annotation_and_generation_contract():
    annotation = _json(DEV_DIR / "annotation_audit.json")
    plan = _json(DEV_DIR / "generation_plan.json")
    assert annotation["cases"] == 36
    assert annotation["well_posed"] == 36
    assert annotation["ambiguous"] == 0
    assert len(annotation["items"]) == 36
    assert plan["cases"] == 36
    assert plan["source_totals"] == EXPECTED_SOURCE
    assert plan["category_totals"] == EXPECTED_CATEGORY
    assert plan["stable_order"] == "sha256(seed + NUL + source + NUL + source_id), ascending"
    assert "retrieval/ranking" in plan["forbidden"]
    assert "historical eval plaintext" in plan["forbidden"]
    assert "fresh holdout plaintext" in plan["forbidden"]


def test_provenance_hash_dag_is_exact():
    manifest = _json(DEV_DIR / "manifest.json")
    report = _json(DEV_DIR / "builder_report.json")
    core = {
        "evalset.jsonl": "evalset_sha256",
        "fingerprints.json": "fingerprints_sha256",
        "annotation_audit.json": "annotation_sha256",
    }
    assert set(manifest["hashes"]) == set(core)
    for name, key in core.items():
        actual = _sha(DEV_DIR / name)
        assert manifest["hashes"][name].lower() == actual
        assert manifest["core"][key].lower() == actual

    manifest_sha = _sha(DEV_DIR / "manifest.json")
    assert report["hashes"]["manifest.json"].lower() == manifest_sha
    assert report["provenance"]["manifest_sha256"].lower() == manifest_sha
    for name, key in core.items():
        actual = _sha(DEV_DIR / name)
        assert report["hashes"][name].lower() == actual
        assert report["provenance"]["core"][key].lower() == actual

    sealed = (DEV_DIR / "SEALED.md").read_text(encoding="utf-8")
    expected = {
        "evalset.jsonl": _sha(DEV_DIR / "evalset.jsonl"),
        "fingerprints.json": _sha(DEV_DIR / "fingerprints.json"),
        "annotation_audit.json": _sha(DEV_DIR / "annotation_audit.json"),
        "manifest.json": manifest_sha,
        "builder_report.json": _sha(DEV_DIR / "builder_report.json"),
    }
    found = {
        m.group(1): m.group(2).lower()
        for m in re.finditer(r"^- ([^:]+): ([0-9a-fA-F]{64})$", sealed, flags=re.MULTILINE)
    }
    assert found == expected
    assert _sha(DEV_DIR / "SEALED.md") not in sealed


def test_builder_report_is_plaintext_free_of_case_queries_and_ids():
    cases = _cases()
    text = (DEV_DIR / "builder_report.json").read_text(encoding="utf-8")
    for c in cases:
        assert c["query"] not in text
        assert str(c["gold_source_id"]) not in text
