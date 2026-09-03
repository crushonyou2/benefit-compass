"""Safe-action policy v1 — exact frozen implementation (D-049/D-054).

Frozen contract: eval/retrieval-v3/candidate-plan/safe-action-policy-v1.json
(policy_id retrieval-v3-safe-action-policy-v1, norm-v1, lexicons u-v1/g-v1/r-v1,
precedence blank=>ABSTAIN, P_U=>ABSTAIN, P_C=>CLARIFY, else ANSWER).

Query-only by construction: the classifier accepts ONLY raw query_text. It must
not receive/read stratum, golds, task id, protected metadata, retrieval
scores/results, embeddings, config, corpus, filenames/order, or result-derived
statistics. Mechanically computed BEFORE any retrieval, once per task/session,
shared identically across all 18 configs.

Pure: no IO, no clock, no randomness. Total function: every input maps to an
action (blank/non-string input fails closed to ABSTAIN).
"""

from __future__ import annotations

import re
import unicodedata

POLICY_ID = "retrieval-v3-safe-action-policy-v1"
POLICY_SHA256 = "c512fb5627179697a987b05a2431b8f7e30d1153af2ff6dca37995f6b232a35d"
POLICY_ARTIFACT = "eval/retrieval-v3/candidate-plan/safe-action-policy-v1.json"
NORM_ID = "norm-v1"

# Frozen lexicon u-v1: out-of-domain luxury/speculative/foreign-tourist markers.
U_ABSTAIN = (
    "외국인 관광객",
    "해외 유학",
    "비행기표",
    "주식 투자",
    "손실 보전",
    "명품",
    "사치",
    "골프",
    "회원권",
    "암호화폐",
    "가상자산",
    "외제차",
    "게임기",
    "유튜브",
    "콘서트",
    "레스토랑",
    "반려동물 미용",
    "헬스장",
)

# Frozen lexicon g-v1: generic benefit nouns (never trigger alone).
G_BENEFIT = (
    "지원금",
    "혜택",
    "지원",
    "복지",
    "대출",
    "교육",
    "보육",
    "문화",
    "의료비",
    "창업",
    "주거",
    "이사",
    "포인트",
)

# Frozen lexicon r-v1: vague existence/request frames (never trigger alone).
R_FRAME = (
    "받고 싶어요",
    "뭐 있",
    "알려줘",
    "알려주세요",
    "받을 수 있을",
    "궁금해",
    "있나요",
    "있죠",
    "되나요",
    "있을까",
    "신청하고 싶어요",
)

SAFE_ACTIONS = ("ANSWER", "ABSTAIN", "CLARIFY")

_WS_RUN_RE = re.compile(r"\s+")


def normalize_query_v1(query_text: str) -> str:
    """Frozen norm-v1: NFC -> strip -> collapse internal whitespace -> casefold.

    Restricted to the query operand (identical to candidate-plan-v1 step_4 exact
    normalization). Non-string input fails closed to "" (classifies ABSTAIN).
    """
    if not isinstance(query_text, str):
        return ""
    t = unicodedata.normalize("NFC", query_text)
    t = t.strip()
    t = _WS_RUN_RE.sub(" ", t)
    t = t.casefold()
    return t


def classify_safe_action(query_text: str) -> str:
    """Frozen safe-action decision. Query-only: single raw-query parameter.

    N = norm_v1(query_text); blank => ABSTAIN; P_U => ABSTAIN; P_C => CLARIFY;
    else ANSWER. P_U = any U_ABSTAIN substring of N. P_C = (any G_BENEFIT
    substring of N) AND (any R_FRAME substring of N). Existential
    (order-independent) substring predicates; deterministic pure function.
    """
    n = normalize_query_v1(query_text)
    if n == "":
        return "ABSTAIN"
    for u in U_ABSTAIN:
        if u in n:
            return "ABSTAIN"
    has_g = False
    for g in G_BENEFIT:
        if g in n:
            has_g = True
            break
    if has_g:
        for r in R_FRAME:
            if r in n:
                return "CLARIFY"
    return "ANSWER"


def action_correct_for_role(action: str, role: str) -> bool:
    """Frozen scoring semantics: unsupported correct iff ABSTAIN; ambiguous
    correct iff ABSTAIN or CLARIFY. role in {"unsupported", "ambiguous"}."""
    if role == "unsupported":
        return action == "ABSTAIN"
    if role == "ambiguous":
        return action in ("ABSTAIN", "CLARIFY")
    raise ValueError(f"role must be unsupported/ambiguous, got {role!r}")
