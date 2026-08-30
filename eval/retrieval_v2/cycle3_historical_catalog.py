"""Historical fingerprint catalog loader for fresh builders (D-011)."""
from __future__ import annotations
import json, pathlib
from typing import Any
from retrieval_v2.cycle3_fingerprint import FINGERPRINT_VERSION, NORMALIZATION_SPEC, check_overlap, validate_fingerprint_manifest
ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_CATALOG = ROOT / "eval" / "retrieval-v2" / "cycle3" / "catalog" / "catalog.json"
CATALOG_DIR = ROOT / "eval" / "retrieval-v2" / "cycle3" / "catalog"
def load_historical_catalog(path: str | pathlib.Path | None = None) -> dict[str, Any]:
    p = pathlib.Path(path) if path else DEFAULT_CATALOG
    data = json.loads(p.read_text(encoding="utf-8"))
    if data.get("fingerprint_version") != FINGERPRINT_VERSION: raise ValueError(f"fingerprint_version mismatch {data.get('fingerprint_version')!r}")
    if data.get("normalization_spec") != NORMALIZATION_SPEC: raise ValueError(f"normalization_spec mismatch {data.get('normalization_spec')!r}")
    return data
def get_union_manifest(catalog: dict[str, Any] | None = None) -> dict[str, Any]:
    cat = catalog or load_historical_catalog()
    union = cat["union"]
    qfps = union["query_fingerprints"]; gfps = union["gold_fingerprints"]
    if len(qfps) != len(gfps): raise ValueError(f"union query {len(qfps)} != gold {len(gfps)}; catalog inconsistent")
    return {"fingerprint_version": FINGERPRINT_VERSION, "normalization_spec": NORMALIZATION_SPEC, "cases": len(qfps), "query_fingerprints": qfps, "gold_fingerprints": gfps}
def get_union_sets(catalog: dict[str, Any] | None = None) -> tuple[set[str], set[str]]:
    cat = catalog or load_historical_catalog()
    u = cat["union"]
    return set(s.lower() for s in u["query_fingerprints"]), set(s.lower() for s in u["gold_fingerprints"])
def check_fresh_no_overlap(fresh_manifest: dict[str, Any], catalog: dict[str, Any] | None = None) -> dict[str, Any]:
    cat = catalog or load_historical_catalog()
    validate_fingerprint_manifest(fresh_manifest)
    union_manifest = get_union_manifest(cat)
    validate_fingerprint_manifest(union_manifest)
    return check_overlap(fresh_manifest, union_manifest, strict=False)
def check_fresh_no_overlap_or_raise(fresh_manifest: dict[str, Any], catalog: dict[str, Any] | None = None) -> None:
    res = check_fresh_no_overlap(fresh_manifest, catalog)
    if res["query_overlap"] != 0 or res["gold_overlap"] != 0: raise ValueError(f"fresh overlaps historical: {res}")
def load_per_set_manifests(catalog: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    cat = catalog or load_historical_catalog()
    out={}
    for entry in cat["historical_sets"]:
        sid=entry["id"]; path=CATALOG_DIR / f"{sid}.json"
        m=json.loads(path.read_text(encoding="utf-8")); validate_fingerprint_manifest(m); out[sid]=m
    return out
