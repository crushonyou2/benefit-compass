"""Evaluation-set schema / validation for Retrieval v2 dev & holdout.

Required fields per query:
- query: str, non-empty, UTF-8
- gold_source: "youth" | "gov24"
- gold_source_id: str, non-empty
- category: str, non-empty (e.g., household/housing, welfare/health, cross_source_similar, explicit, broad, ambiguous)

Optional (kept for compatibility with current evaluator):
- age, case_type

Invariants:
- source ∈ {youth, gov24}
- gold_source_id non-empty
- duplicate (query) detection (case-sensitive, stripped)
- duplicate (source, source_id, query) detection
- category non-empty
- UTF-8 valid (Python str is UTF-8, but we check for lone surrogates)
- role ∈ {dev, holdout} must be explicit metadata, not inferred

This module is DB/model-free and testable.
"""
from __future__ import annotations

import pathlib
from typing import Iterable

ALLOWED_SOURCES = {"youth", "gov24"}
ALLOWED_ROLES = {"dev", "holdout"}


def _is_utf8_valid(s: str) -> bool:
    try:
        s.encode("utf-8").decode("utf-8")
        # lone surrogates would have been caught as encode error on narrow builds,
        # but we also check for unpaired surrogates via encode with strict
        s.encode("utf-8", errors="strict")
        return True
    except Exception:
        return False


def validate_item(item: dict, index: int) -> list[str]:
    errs = []
    q = item.get("query")
    if not isinstance(q, str) or not q.strip():
        errs.append(f"[{index}] query missing/empty")
    elif not _is_utf8_valid(q):
        errs.append(f"[{index}] query not UTF-8 valid")

    src = item.get("gold_source")
    if src not in ALLOWED_SOURCES:
        errs.append(f"[{index}] gold_source must be youth|gov24, got {src!r}")

    gid = item.get("gold_source_id")
    if not isinstance(gid, str) or not gid.strip():
        errs.append(f"[{index}] gold_source_id missing/empty")

    cat = item.get("category")
    if not isinstance(cat, str) or not cat.strip():
        errs.append(f"[{index}] category missing/empty")

    # role is not per-item but per-file metadata; we validate separately in validate_file
    return errs

def validate_file(items: Iterable[dict], role: str | None) -> list[str]:
    errs = []
    if role not in ALLOWED_ROLES:
        errs.append(f"role must be one of {sorted(ALLOWED_ROLES)}, got {role!r} — dev/holdout must be explicit")
    items = list(items)
    if not items:
        errs.append("file is empty")
        return errs
    seen_query = {}
    seen_triple = {}
    for idx, it in enumerate(items, 1):
        errs.extend(validate_item(it, idx))
        q = it.get("query")
        if isinstance(q, str):
            key = q.strip()
            if key in seen_query:
                errs.append(f"[{idx}] duplicate query with [{seen_query[key]}] query={key!r}")
            else:
                seen_query[key] = idx
        src = it.get("gold_source")
        gid = it.get("gold_source_id")
        qraw = it.get("query")
        if isinstance(src, str) and isinstance(gid, str) and isinstance(qraw, str):
            triple = (src, gid, qraw.strip())
            if triple in seen_triple:
                errs.append(f"[{idx}] duplicate (source, source_id, query) with [{seen_triple[triple]}]")
            else:
                seen_triple[triple] = idx
    return errs


def validate_role_contract(items: Iterable[dict], role: str) -> list[str]:
    """D-007 dev/holdout cardinality and source-balance."""
    items = list(items)
    n = len(items)
    youth = sum(1 for it in items if it.get("gold_source") == "youth")
    gov24 = sum(1 for it in items if it.get("gold_source") == "gov24")
    errs = []
    if role == "dev":
        if not (30 <= n <= 40):
            errs.append(f"dev role n={n} must be 30..40 (youth {youth} gov24 {gov24})")
    elif role == "holdout":
        if n < 40:
            errs.append(f"holdout role n={n} must be >=40 (youth {youth} gov24 {gov24})")
    else:
        errs.append(f"role must be dev or holdout, got {role!r} (n={n} youth {youth} gov24 {gov24})")
    if abs(youth - gov24) > 1:
        errs.append(f"source-balanced abs(youth {youth} - gov24 {gov24}) = {abs(youth - gov24)} >1 for role {role} n={n} (youth {youth} gov24 {gov24})")
    return errs


def load_and_validate(path: pathlib.Path, role: str) -> list[dict]:
    import json
    if not path.exists():
        raise FileNotFoundError(f"evalset not found: {path}")
    items = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
    errs = validate_file(items, role)
    errs.extend(validate_role_contract(items, role))
    if errs:
        raise ValueError("validation failed:\n" + "\n".join(errs))
    return items
