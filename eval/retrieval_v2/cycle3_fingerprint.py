"""Cycle3 protected-set collision fingerprint helper (D-011) — INFRA REPAIR v2.

Generic helper to verify dev/holdout/P0 overlap without reopening holdout plaintext.
- query fingerprint: SHA256(normalized_query)
  normalized = NFC → strip → collapse internal whitespace to single space → casefold (lower)
  (deterministic; manifest stores normalization spec)
- gold fingerprint: SHA256(source + NUL + source_id)  source ∈ {youth,gov24}
- Manifest can store query_fingerprints / gold_fingerprints arrays (hex strings) + version/spec.
- check_overlap(manifest_a, manifest_b) is pure, fail-closed: returns counts, raises on overlap>0 if strict.
- validate_fingerprint_manifest ensures fail-closed semantics (version/spec, lists, hex, duplicates, cases)

No dev/holdout data is generated here. Existing cycle1/2 protected plaintext is not read.
Next builders record fingerprints for the data they create; past protected sets are referenced only via
already-exposed aggregate/fingerprint artifacts, otherwise an isolated audit plan is required.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from typing import Any

FINGERPRINT_VERSION = "v1"
NORMALIZATION_SPEC = "NFC + strip + collapse_whitespace + casefold(lower)"

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


def _is_hex64(s: str) -> bool:
    return isinstance(s, str) and bool(_HEX64_RE.match(s.lower()))


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


def validate_fingerprint_manifest(manifest: dict[str, Any]) -> None:
    """Fail-closed validator for fingerprint manifests.

    Checks (all fail-closed, raise ValueError/TypeError):
    - fingerprint_version == v1 required
    - normalization_spec == NORMALIZATION_SPEC required
    - query_fingerprints and gold_fingerprints keys required, must be lists (not None), type mismatch forbidden
    - each fingerprint must be 64-hex (case-insensitive, but stored lower)
    - duplicate fingerprint inside same manifest => error (no silent set dedup)
    - if manifest contains 'cases', it must be positive int and query/gold counts must exactly equal cases

    Raises:
        TypeError / ValueError on any violation.
    """
    if not isinstance(manifest, dict):
        raise TypeError("manifest must be dict")
    # fingerprint_version
    if "fingerprint_version" not in manifest:
        raise ValueError("missing fingerprint_version")
    if manifest["fingerprint_version"] != FINGERPRINT_VERSION:
        raise ValueError(f"fingerprint_version must be {FINGERPRINT_VERSION!r}, got {manifest['fingerprint_version']!r}")
    # normalization_spec
    if "normalization_spec" not in manifest:
        raise ValueError("missing normalization_spec")
    if manifest["normalization_spec"] != NORMALIZATION_SPEC:
        raise ValueError(f"normalization_spec must be {NORMALIZATION_SPEC!r}, got {manifest['normalization_spec']!r}")
    # query_fingerprints
    if "query_fingerprints" not in manifest:
        raise ValueError("missing query_fingerprints")
    qfps = manifest["query_fingerprints"]
    if qfps is None:
        raise ValueError("query_fingerprints must not be None")
    if not isinstance(qfps, list):
        raise TypeError(f"query_fingerprints must be list, got {type(qfps).__name__}")
    # gold_fingerprints
    if "gold_fingerprints" not in manifest:
        raise ValueError("missing gold_fingerprints")
    gfps = manifest["gold_fingerprints"]
    if gfps is None:
        raise ValueError("gold_fingerprints must not be None")
    if not isinstance(gfps, list):
        raise TypeError(f"gold_fingerprints must be list, got {type(gfps).__name__}")
    # each fingerprint 64-hex
    for idx, fp in enumerate(qfps):
        if not isinstance(fp, str) or not _HEX64_RE.match(fp.lower()):
            raise ValueError(f"query_fingerprints[{idx}] must be 64-hex, got {fp!r}")
    for idx, fp in enumerate(gfps):
        if not isinstance(fp, str) or not _HEX64_RE.match(fp.lower()):
            raise ValueError(f"gold_fingerprints[{idx}] must be 64-hex, got {fp!r}")
    # duplicate detection (no silent dedup)
    if len(qfps) != len(set(q.lower() for q in qfps)):
        # Use lowercased set to catch case-insensitive duplicates as well (hex is case-insensitive)
        raise ValueError(f"query_fingerprints contains duplicate entries (len {len(qfps)} vs unique {len(set(q.lower() for q in qfps))})")
    if len(gfps) != len(set(g.lower() for g in gfps)):
        raise ValueError(f"gold_fingerprints contains duplicate entries (len {len(gfps)} vs unique {len(set(g.lower() for g in gfps))})")
    # cases check
    if "cases" in manifest:
        cases = manifest["cases"]
        if not isinstance(cases, int) or isinstance(cases, bool):
            raise TypeError(f"cases must be int, got {type(cases).__name__}: {cases!r}")
        if cases <= 0:
            raise ValueError(f"cases must be positive int, got {cases!r}")
        if len(qfps) != cases:
            raise ValueError(f"query_fingerprints count {len(qfps)} != cases {cases}")
        if len(gfps) != cases:
            raise ValueError(f"gold_fingerprints count {len(gfps)} != cases {cases}")


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


def _as_set_strict(lst: list[str]) -> set[str]:
    # lower-case normalization for hex comparison
    return set(s.lower() for s in lst)


def check_overlap(
    manifest_a: dict[str, Any],
    manifest_b: dict[str, Any],
    *,
    strict: bool = True,
) -> dict[str, Any]:
    """Pure helper: check overlap between two fingerprint manifests.

    Validates both manifests fail-closed via validate_fingerprint_manifest before overlap calculation.
    Inputs are dicts containing at least query_fingerprints and gold_fingerprints (lists of hex) + version/spec.
    Returns {"query_overlap": int, "gold_overlap": int, "query_overlap_examples": [...], "gold_overlap_examples": [...]}
    If strict=True and any overlap >0, raises ValueError (fail-closed).
    Never touches filesystem or protected plaintext; operates only on fingerprint arrays.

    Example:
      a = {"query_fingerprints": [...], "gold_fingerprints": [...], "fingerprint_version": "v1", "normalization_spec": "..."}
      b = {"query_fingerprints": [...], "gold_fingerprints": [...], "fingerprint_version": "v1", "normalization_spec": "..."}
      check_overlap(a, b)  # raises if overlap
    """
    if not isinstance(manifest_a, dict) or not isinstance(manifest_b, dict):
        raise TypeError("manifests must be dict")
    # Strict validation before any overlap calc (fail-closed)
    validate_fingerprint_manifest(manifest_a)
    validate_fingerprint_manifest(manifest_b)

    qa = _as_set_strict(manifest_a["query_fingerprints"])
    qb = _as_set_strict(manifest_b["query_fingerprints"])
    ga = _as_set_strict(manifest_a["gold_fingerprints"])
    gb = _as_set_strict(manifest_b["gold_fingerprints"])

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

    Fail-closed: duplicates or count mismatches raise ValueError (no silent dedup/count hide).
    Helper for builders to embed fingerprints into their manifest.json.
    """
    # Validate inputs fail-closed before dedup/hide
    if not isinstance(query_fingerprints, list):
        raise TypeError(f"query_fingerprints must be list, got {type(query_fingerprints).__name__}")
    if not isinstance(gold_fingerprints, list):
        raise TypeError(f"gold_fingerprints must be list, got {type(gold_fingerprints).__name__}")
    if query_fingerprints is None or gold_fingerprints is None:
        raise ValueError("query_fingerprints/gold_fingerprints must not be None")
    # hex validation
    for idx, fp in enumerate(query_fingerprints):
        if not isinstance(fp, str) or not _HEX64_RE.match(fp.lower()):
            raise ValueError(f"query_fingerprints[{idx}] must be 64-hex, got {fp!r}")
    for idx, fp in enumerate(gold_fingerprints):
        if not isinstance(fp, str) or not _HEX64_RE.match(fp.lower()):
            raise ValueError(f"gold_fingerprints[{idx}] must be 64-hex, got {fp!r}")
    # duplicate detection (before dedup)
    if len(query_fingerprints) != len(set(s.lower() for s in query_fingerprints)):
        raise ValueError(f"query_fingerprints contains duplicates (len {len(query_fingerprints)} vs unique {len(set(s.lower() for s in query_fingerprints))})")
    if len(gold_fingerprints) != len(set(s.lower() for s in gold_fingerprints)):
        raise ValueError(f"gold_fingerprints contains duplicates (len {len(gold_fingerprints)} vs unique {len(set(s.lower() for s in gold_fingerprints))})")
    # cases validation
    if not isinstance(cases, int) or isinstance(cases, bool) or cases <= 0:
        raise ValueError(f"cases must be positive int, got {cases!r}")
    if len(query_fingerprints) != cases:
        raise ValueError(f"query_fingerprints count {len(query_fingerprints)} != cases {cases}")
    if len(gold_fingerprints) != cases:
        raise ValueError(f"gold_fingerprints count {len(gold_fingerprints)} != cases {cases}")

    m: dict[str, Any] = {
        "fingerprint_version": FINGERPRINT_VERSION,
        "normalization_spec": NORMALIZATION_SPEC,
        "role": role,
        "cycle": cycle,
        "cases": cases,
        "query_fingerprints": sorted(set(s.lower() for s in query_fingerprints)),
        "gold_fingerprints": sorted(set(s.lower() for s in gold_fingerprints)),
    }
    if sha256 is not None:
        if not isinstance(sha256, str) or not _HEX64_RE.match(sha256.lower()):
            raise ValueError(f"sha256 must be 64-hex, got {sha256!r}")
        m["sha256"] = sha256.lower()
    if extra:
        m.update(extra)
    # Final validation to ensure manifest itself is valid
    validate_fingerprint_manifest(m)
    return m
