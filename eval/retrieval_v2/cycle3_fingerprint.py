"""Cycle3 protected-set collision fingerprint helper (D-011).

Generic helper to verify dev/holdout/P0 overlap without reopening holdout plaintext.
- query fingerprint: SHA256(normalized_query)
  normalized = NFC → strip → collapse internal whitespace to single space → casefold (lower)
  (deterministic; manifest stores normalization spec)
- gold fingerprint: SHA256(source + NUL + source_id)  source ∈ {youth,gov24}
- Manifest can store query_fingerprints / gold_fingerprints arrays (hex strings) + version/spec.
- check_overlap(manifest_a, manifest_b) is pure, fail-closed: returns counts, raises on overlap>0 if strict.

No dev/holdout data is generated here. Existing cycle1/2 protected plaintext is not read.
Next builders record fingerprints for the data they create; past protected sets are referenced only via
already-exposed aggregate/fingerprint artifacts, otherwise an isolated audit plan is required.
"""

from __future__ import annotations

import hashlib
import unicodedata
import re
from typing import Any

FINGERPRINT_VERSION = "v1"
NORMALIZATION_SPEC = "NFC + strip + collapse_whitespace + casefold(lower)"


def normalize_query(q: str) -> str:
    """Deterministic query normalization for fingerprinting.

    Steps (must be identical in builders and verifiers):
    1. NFC unicode normalization
    2. strip leading/trailing whitespace
    3. collapse any run of whitespace (space, tab, newline, etc.) to single ASCII space
    4. casefold (lower) for case-insensitive match (Korean unchanged, ASCII lowered)
    """
    if not isinstance(q, str):
        raise TypeError("query must be str")
    nfc = unicodedata.normalize("NFC", q)
    stripped = nfc.strip()
    collapsed = re.sub(r"\s+", " ", stripped)
    return collapsed.casefold()


def query_fingerprint(query: str) -> str:
    """SHA256 hex of normalized query (utf-8)."""
    norm = normalize_query(query)
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def gold_fingerprint(source: str, source_id: str) -> str:
    """SHA256 hex of source + NUL + source_id (utf-8).

    NUL separator prevents e.g. source="youth", source_id="a\x00b" ambiguity.
    """
    if source not in ("youth", "gov24"):
        raise ValueError(f"source must be 'youth' or 'gov24', got {source!r}")
    if not isinstance(source_id, str) or not source_id:
        raise ValueError("source_id must be non-empty str")
    if "\x00" in source_id:
        raise ValueError("source_id must not contain NUL")
    payload = f"{source}\x00{source_id}".encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def fingerprints_for_items(
    items: list[dict[str, Any]],
    *,
    query_key: str = "query",
    source_key: str = "gold_source",
    source_id_key: str = "gold_source_id",
) -> dict[str, Any]:
    """Build fingerprint manifest fragment from in-memory items (builder helper).

    Items are dicts with query / source / source_id keys. Returns dict with:
      fingerprint_version, normalization_spec, query_fingerprints, gold_fingerprints
    Order is preserved input order; caller may sort/dedup as needed.
    Pure helper; does not touch filesystem.
    """
    qfps: list[str] = []
    gfps: list[str] = []
    for it in items:
        q = it.get(query_key)
        s = it.get(source_key)
        sid = it.get(source_id_key)
        # also accept alternative keys: "source"/"source_id" for raw policy sets
        if s is None:
            s = it.get("source")
        if sid is None:
            sid = it.get("source_id")
        if q is None or s is None or sid is None:
            raise ValueError(f"item missing keys: {it!r}")
        qfps.append(query_fingerprint(str(q)))
        gfps.append(gold_fingerprint(str(s), str(sid)))
    return {
        "fingerprint_version": FINGERPRINT_VERSION,
        "normalization_spec": NORMALIZATION_SPEC,
        "query_fingerprints": qfps,
        "gold_fingerprints": gfps,
    }


def _as_set(lst: Any) -> set[str]:
    if lst is None:
        return set()
    if not isinstance(lst, list):
        raise TypeError("fingerprints must be list")
    return set(lst)


def check_overlap(
    manifest_a: dict[str, Any],
    manifest_b: dict[str, Any],
    *,
    strict: bool = True,
) -> dict[str, Any]:
    """Pure helper: check overlap between two fingerprint manifests.

    Inputs are dicts containing at least query_fingerprints and gold_fingerprints (lists of hex).
    Returns {"query_overlap": int, "gold_overlap": int, "query_overlap_examples": [...], "gold_overlap_examples": [...]}
    If strict=True and any overlap >0, raises ValueError (fail-closed).
    Never touches filesystem or protected plaintext; operates only on fingerprint arrays.

    Example:
      a = {"query_fingerprints": [...], "gold_fingerprints": [...]}
      b = {"query_fingerprints": [...], "gold_fingerprints": [...]}
      check_overlap(a, b)  # raises if overlap
    """
    if not isinstance(manifest_a, dict) or not isinstance(manifest_b, dict):
        raise TypeError("manifests must be dict")
    qa = _as_set(manifest_a.get("query_fingerprints"))
    qb = _as_set(manifest_b.get("query_fingerprints"))
    ga = _as_set(manifest_a.get("gold_fingerprints"))
    gb = _as_set(manifest_b.get("gold_fingerprints"))

    q_overlap = qa.intersection(qb)
    g_overlap = ga.intersection(gb)

    result = {
        "query_overlap": len(q_overlap),
        "gold_overlap": len(g_overlap),
        "query_overlap_examples": sorted(q_overlap)[:3],
        "gold_overlap_examples": sorted(g_overlap)[:3],
    }
    if strict and (result["query_overlap"] != 0 or result["gold_overlap"] != 0):
        raise ValueError(
            f"fingerprint overlap detected: query_overlap={result['query_overlap']} gold_overlap={result['gold_overlap']}"
        )
    return result


def check_no_overlap_or_raise(manifest_a: dict[str, Any], manifest_b: dict[str, Any]) -> None:
    """Convenience: strict overlap 0 check, raises ValueError on any overlap, returns None on pass."""
    check_overlap(manifest_a, manifest_b, strict=True)


def manifest_with_fingerprints(
    *,
    role: str,
    cycle: int,
    cases: int,
    query_fingerprints: list[str],
    gold_fingerprints: list[str],
    sha256: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a minimal manifest snippet that stores fingerprints deterministically.

    Helper for builders to embed fingerprints into their manifest.json.
    """
    m: dict[str, Any] = {
        "fingerprint_version": FINGERPRINT_VERSION,
        "normalization_spec": NORMALIZATION_SPEC,
        "role": role,
        "cycle": cycle,
        "cases": cases,
        "query_fingerprints": sorted(set(query_fingerprints)),
        "gold_fingerprints": sorted(set(gold_fingerprints)),
    }
    if sha256 is not None:
        m["sha256"] = sha256
    if extra:
        m.update(extra)
    return m
