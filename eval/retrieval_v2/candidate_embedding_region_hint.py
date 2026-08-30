"""Eval-only candidate: embedding input preserves at most one SIDO 시도 hint (cycle2 Phase2 Exp2).

Contract per user instruction (2026-08-30):
- lexical terms: unchanged vs candidate-v2 — lexical_overlap_terms_rewrite(strip_region(raw))
  (no change, no hardcode, no new dictionary)
- embedding query: strip_region(raw) plus at most ONE SIDO canonical term derived from raw.
  * detection uses only ml_app.SIDO table (no si/gun/gu dictionary, no 별도 필터)
  * canonical = SIDO[code][0] for the single selected code
  * bounded: 0 or 1 hint per query, never per-alias nor per-code unbounded
  * selection: earliest alias occurrence in raw_query (raw.find), not sorted code; tie deterministic by code sort
  * lexical ranking hint only 0.01 unchanged, SQL/CANDIDATES/COSINE_MIN/RERANK unchanged
  * youth_source_bias remains on stripped (parity)

No per-case hardcode, no lower-level 행정단위 사전.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "ml-service"))
sys.path.insert(0, str(ROOT / "eval"))

import app as ml_app  # type: ignore
from retrieval_v2.candidate_lexical_rewrite import lexical_overlap_terms_rewrite  # type: ignore


def _detect_sido_codes(raw_query: str) -> list[str]:
    """Return sorted list of SIDO codes whose any alias appears as substring in raw_query."""
    matched: list[str] = []
    for code, aliases in ml_app.SIDO.items():
        for alias in aliases:
            if alias in raw_query:
                matched.append(code)
                break
    matched.sort()
    return matched


def _earliest_sido_code(raw_query: str) -> str | None:
    """Select earliest SIDO code by first alias occurrence in raw_query; tie-break by code sort."""
    best_code = None
    best_pos = None
    for code, aliases in ml_app.SIDO.items():
        # earliest pos for this code among its aliases
        pos_for_code = None
        for alias in aliases:
            idx = raw_query.find(alias)
            if idx != -1:
                if pos_for_code is None or idx < pos_for_code:
                    pos_for_code = idx
        if pos_for_code is not None:
            if best_pos is None or pos_for_code < best_pos or (pos_for_code == best_pos and code < best_code):
                best_pos = pos_for_code
                best_code = code
    return best_code


def canonical_for_code(code: str) -> str:
    """Deterministic canonical = SIDO[code][0] (shortest/most frequent, per SIDO SSOT)."""
    aliases = ml_app.SIDO.get(code)
    if not aliases:
        raise KeyError(f"unknown SIDO code {code}")
    return aliases[0]


def embedding_query_with_region_hint(raw_query: str) -> str:
    """Embedding query: stripped plus at most one canonical SIDO hint from raw (earliest)."""
    stripped = ml_app.strip_region(raw_query)
    code = _earliest_sido_code(raw_query)
    if code is None:
        return stripped
    canonical = canonical_for_code(code)
    if not stripped:
        return canonical
    return f"{stripped} {canonical}"


def lexical_terms_for_candidate(raw_query: str) -> list[str]:
    """Lexical terms identical to candidate-v2 (rewrite on stripped)."""
    stripped = ml_app.strip_region(raw_query)
    return lexical_overlap_terms_rewrite(stripped)


# Aliases for runner flexibility
embedding_query = embedding_query_with_region_hint
