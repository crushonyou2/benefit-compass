"""Eval-only candidate: semantic-core embedding (cycle2 Phase2 Exp3).

Contract per user instruction (2026-08-30 Exp3):
- lexical terms: EXACTLY candidate-v2 — lexical_overlap_terms_rewrite(strip_region(raw))
  (unchanged, no new dictionary, no region hint, no hardcode)
- youth_source_bias: stripped query basis (production parity, unchanged)
- embedding input ONLY: " ".join(lexical_overlap_terms_rewrite(strip_region(raw)))
  — semantic-core title-like terms join; fallback to strip_region(raw) iff terms == []
- production parity invariants (frozen):
  SQL / CANDIDATES=30 / COSINE_MIN=0.78 / LEXICAL_OVERLAP_BIAS=0.01 /
  RERANK=0 / rp=None / region_filter(None) — all unchanged; candidate-v2 parity
- NO new dictionary, NO region hint, NO raw region re-add,
  NO lower-level 시/군/구/동 logic, NO per-case hardcode (c2d-*),
  NO extra model encode, NO extra DB retrieval, NO dual-vector/blend.
  Each variant must use exactly 1 embedding encode + 1 production-parity DB retrieval per query.
- Purpose: isolated test whether question-form particles/조사/boilerplate
  dilute qvec after Exp2 evidence (persistent miss 6 all outside candidate-v2 top30,
  4 with SIDO still outside after hint, 2 without SIDO).

This module provides ONLY pure functions for the above transform;
runner must use them to keep per-query encode/retrieval count at 1.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "ml-service"))
sys.path.insert(0, str(ROOT / "eval"))

import app as ml_app  # type: ignore
from retrieval_v2.candidate_lexical_rewrite import lexical_overlap_terms_rewrite  # type: ignore


def lexical_terms_for_candidate(raw_query: str) -> list[str]:
    """Lexical terms identical to candidate-v2: rewrite on stripped query."""
    stripped = ml_app.strip_region(raw_query)
    return lexical_overlap_terms_rewrite(stripped)


def semantic_core_embedding_query(raw_query: str) -> str:
    """Embedding input = join(lexical terms) or fallback to stripped if empty.

    - stripped = strip_region(raw)
    - terms = lexical_overlap_terms_rewrite(stripped)
    - if terms: " ".join(terms)  (title-like semantic core)
    - else: stripped  (fallback, preserves non-empty query for encoding)
    """
    stripped = ml_app.strip_region(raw_query)
    terms = lexical_overlap_terms_rewrite(stripped)
    if terms:
        return " ".join(terms)
    return stripped


# Runner-friendly aliases
embedding_query = semantic_core_embedding_query
embedding_query_semantic_core = semantic_core_embedding_query
