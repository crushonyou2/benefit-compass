"""Eval-only candidate: region-attached residue cleanup embedding (cycle2 Phase2 Exp4).

Contract per user instruction (2026-08-30 Exp4, D-010 bounded):
- lexical terms: EXACTLY candidate-v2 — lexical_overlap_terms_rewrite(strip_region(raw))
  (unchanged, no new dictionary, no region hint, no hardcode)
- youth_source_bias: stripped query basis (production parity, unchanged) — caller uses youth_source_bias(strip_region(raw))
- embedding input ONLY: region-attached residue cleanup on raw
  * Uses ONLY existing ml_app.SIDO alias table, longest-first deterministic match
  * New region dictionary / 시군구 detection / region hint re-add / hardcode forbidden
  * Grammar: alias directly-attached optional admin suffix (max 1) + optional particle (max 1)
    - suffix set (max 1, longest-first): 특별자치도, 특별자치시, 특별시, 광역시, 자치도, 도, 시
    - particle set (max 1, longest-first): 으로부터, 에게서, 에서, 으로, 에게, 한테, 부터, 까지, 은, 는, 이, 가, 을, 를, 의, 에, 와, 과, 로, 도, 만, 께
    - Only directly adjacent (no space) characters after alias are removed together with alias
    - General 조사/단어 not attached directly are NOT removed
    - Examples (norm):
      부산에 ... -> ... (부산+에)
      충남에서 ... -> ... (충남+에서)
      경기도 청년 -> 청년 (경기+도)
      경기도에서 -> empty -> fallback to strip_region(raw) (경기+도+에서)
      서울특별시에서 -> ... (서울+특별시+에서), 부산광역시로 -> ... (부산+광역시+로)
      강원 삼척시 -> 삼척시 (강원 only, 삼척시 preserved)
      region 없는 query unchanged
  * If cleanup result is empty/whitespace -> fallback to strip_region(raw)
  * Lexical is NEVER changed to cleanup query
- production parity invariants (frozen):
  SQL / CANDIDATES=30 / COSINE_MIN=0.78 / LEXICAL_OVERLAP_BIAS=0.01 /
  RERANK=0 / rp=None / region_filter(None) — all unchanged; candidate-v2 parity
- NO new dictionary beyond suffix/particle grammar, NO 시군구, NO region hint, NO hardcode (c2d-*),
  NO extra model encode, NO extra DB retrieval. Each variant exactly 1 encode + 1 retrieval per query.

This module provides ONLY pure functions; runner must enforce per-query encode/retrieval count.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "ml-service"))
sys.path.insert(0, str(ROOT / "eval"))

import app as ml_app  # type: ignore
from retrieval_v2.candidate_lexical_rewrite import lexical_overlap_terms_rewrite  # type: ignore

# Grammar — only these beyond SIDO aliases; no new region dict
_ADMIN_SUFFIXES_RAW = ["특별자치도", "특별자치시", "특별시", "광역시", "자치도", "도", "시"]
_PARTICLES_RAW = [
    "으로부터",
    "에게서",
    "에서",
    "으로",
    "에게",
    "한테",
    "부터",
    "까지",
    "은",
    "는",
    "이",
    "가",
    "을",
    "를",
    "의",
    "에",
    "와",
    "과",
    "로",
    "도",
    "만",
    "께",
]

# Deterministic longest-first ordering
_ADMIN_SUFFIXES = sorted(_ADMIN_SUFFIXES_RAW, key=lambda x: (-len(x), x))
_PARTICLES = sorted(_PARTICLES_RAW, key=lambda x: (-len(x), x))

# SIDO aliases — existing table only, longest-first deterministic
_raw_aliases: list[str] = []
for _kws in ml_app.SIDO.values():
    _raw_aliases.extend(_kws)
# unique, longest-first, tie lexical
_SIDO_ALIASES = sorted(set(_raw_aliases), key=lambda x: (-len(x), x))


def _region_attached_cleanup(raw_query: str) -> str:
    """Remove alias + optional directly-attached suffix (max1) + particle (max1) as a unit.

    - Scans left-to-right, longest alias first at each position.
    - Only characters directly adjacent after alias (no space) are considered for suffix/particle.
    - Result whitespace-normalized; empty -> fallback outside.
    """
    if not raw_query:
        return raw_query
    n = len(raw_query)
    i = 0
    out_chars: list[str] = []
    while i < n:
        matched = None
        mlen = 0
        for alias in _SIDO_ALIASES:
            if raw_query.startswith(alias, i):
                matched = alias
                mlen = len(alias)
                break
        if matched is None:
            out_chars.append(raw_query[i])
            i += 1
        else:
            suffix_matched = ""
            for s in _ADMIN_SUFFIXES:
                if raw_query.startswith(s, i + mlen):
                    suffix_matched = s
                    break
            particle_start = i + mlen + len(suffix_matched)
            particle_matched = ""
            for p in _PARTICLES:
                if raw_query.startswith(p, particle_start):
                    particle_matched = p
                    break
            total = mlen + len(suffix_matched) + len(particle_matched)
            i += total
            # removed unit — do not append, continue
    cleaned = "".join(out_chars)
    normalized = " ".join(cleaned.split())
    return normalized


def cleanup_embedding_query(raw_query: str) -> str:
    """Embedding input for Exp4: region-attached residue cleanup with fallback.

    - primary: _region_attached_cleanup(raw_query) normalized
    - fallback: ml_app.strip_region(raw_query) if primary empty
    - if no region alias present, _region_attached_cleanup returns raw unchanged (via character copy)
    """
    # Use stripped as fallback basis
    fallback = ml_app.strip_region(raw_query)
    primary = _region_attached_cleanup(raw_query)
    if not primary:
        return fallback
    return primary


def lexical_terms_for_candidate(raw_query: str) -> list[str]:
    """Lexical terms identical to candidate-v2: rewrite on stripped query."""
    stripped = ml_app.strip_region(raw_query)
    return lexical_overlap_terms_rewrite(stripped)


# Runner-friendly aliases
embedding_query = cleanup_embedding_query
embedding_query_with_cleanup = cleanup_embedding_query
region_attached_cleanup = _region_attached_cleanup
