"""Eval-only candidate: bounded region-core lexical hint (cycle2 Phase2 Exp1).

Contract per task spec:
- embedding/query vector = ml_app.strip_region(raw_query) unchanged (runner uses that)
- youth_source_bias = stripped q unchanged
- lexical base = frozen candidate-v2 lexical_overlap_terms_rewrite(q_stripped)
- lexical hint = raw_query에서 발견된 SIDO code당 deterministic canonical 1개만 추가
- 반드시 ml_app.SIDO alias table에서만 추출, dev case hardcode 금지, lower-level 시/군/구/동 금지
- 한 region code당 최대 1개, 동일 region alias 중복 금지, query에 region 없으면 base와 동일
- 추가 term bounded (보통 0/1, 다중 시·도라도 코드당 1개)
- lexical ranking hint only: rp=None, region_filter(None), SQL/CANDIDATES/COSINE_MIN/LEXICAL_BIAS/RERANK unchanged

Canonical hint 도출 규칙 (일반성):
- canonical = SIDO[code][0]  (SIDO 테이블의 첫 번째 alias)
- 이유: SIDO 테이블에서 이중 alias를 가진 6개 코드( 충북/충청북도 등)는 첫 alias가 가장 짧고
  가장 빈도가 높은 약칭이다. DB 정책 코퍼스에서 짧은 약칭이 긴 정식 명칭보다
  평균 2배 이상 빈도가 높다(예: 충북 75 vs 충청북도 38, 전북 130 vs 전라북도 3).
  짧은 약칭은 ILIKE '%%term%%' lexical overlap에서 긴 명칭을 포함하지 않지만
  그 역도 마찬가지이며, 짧은 약칭이 코퍼스에서 더 흔하므로 recall에 유리하다.
  또한 첫 alias는 ML 서비스의 production SIDO SSOT 순서를 그대로 따르므로
  dev case와 무관하게 deterministic하고 hardcode가 아니다.
- 검증: test에서 모든 code에 대해 canonical == SIDO[code][0] == shortest alias임을 고정.
"""

from __future__ import annotations

import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "ml-service"))
sys.path.insert(0, str(ROOT / "eval"))

import app as ml_app  # type: ignore
from source_ranking import LEXICAL_STOPWORDS  # type: ignore
from retrieval_v2.candidate_lexical_rewrite import is_residue, lexical_overlap_terms_rewrite  # type: ignore


def canonical_for_code(code: str) -> str:
    """Deterministic canonical lexical hint for a SIDO code.

    Rule: SIDO[code][0] — first alias in production SIDO table.
    This equals the shortest alias for all current codes and is the
    most frequent form in the policy corpus.
    """
    aliases = ml_app.SIDO.get(code)
    if not aliases:
        raise KeyError(f"unknown SIDO code {code}")
    return aliases[0]


def detect_sido_codes(raw_query: str) -> list[str]:
    """Return sorted list of SIDO codes whose any alias appears as substring in raw_query.

    Deterministic, no hardcode, only ml_app.SIDO.
    Lower-level 시/군/구/동 not considered.
    """
    matched: list[str] = []
    for code in sorted(ml_app.SIDO.keys()):
        aliases = ml_app.SIDO[code]
        if any(alias in raw_query for alias in aliases):
            matched.append(code)
    return matched


def lexical_overlap_terms_region_hint(raw_query: str) -> list[str]:
    """Lexical terms = base (candidate-v2 rewrite on stripped q) + bounded region hints.

    - base = lexical_overlap_terms_rewrite(strip_region(raw_query))
    - hint per matched SIDO code: canonical_for_code(code) if not already in base,
      not stopword, len>=2, not residue, not empty, deduped.
    - total added bounded by number of matched codes (0..N, typically 0/1)
    - if no region in raw_query, result identical to base
    """
    q_stripped = ml_app.strip_region(raw_query)
    base = lexical_overlap_terms_rewrite(q_stripped)
    matched_codes = detect_sido_codes(raw_query)
    if not matched_codes:
        return base
    seen = set(base)
    hints: list[str] = []
    for code in matched_codes:
        canon = canonical_for_code(code)
        if canon in seen:
            continue
        if len(canon) < 2:
            continue
        if canon in LEXICAL_STOPWORDS:
            continue
        if is_residue(canon):
            continue
        if not canon.strip():
            continue
        hints.append(canon)
        seen.add(canon)
    # dedup already, preserve base order then hints in code-sorted order
    return base + hints


# Backwards alias for runner import flexibility
region_hint_terms = lexical_overlap_terms_region_hint
