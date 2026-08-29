"""복수 출처 검색의 질의 의도·어휘 보정 규칙."""

import re


YOUTH_INTENT_BIAS = 0.015
YOUTH_INTENT_TERMS = ("청년", "대학생", "사회초년생")
LEXICAL_OVERLAP_BIAS = 0.01
LEXICAL_STOPWORDS = frozenset(
    (
        "있나요", "있습니까", "있을까요", "있을까", "궁금해요", "궁금한데",
        "알려주세요", "받을", "수", "있는", "있다", "있으면", "지원",
        "방법", "어디", "어디서", "어디에", "어떤", "프로그램", "정책",
        "도움", "도움받을", "도와주는", "가능", "하는", "하는데",
        "하려면", "어떻게", "것", "게", "싶어요", "해주세요",
        "지원받을", "지원하는", "지원해주는",
    )
)
GOV24_INTENT_TERMS = (
    "국토교통부",
    "중소벤처기업부",
    "고용노동부",
    "보건복지부",
    "교육부",
    "행정안전부",
    "문화체육관광부",
    "농림축산식품부",
    "산업통상자원부",
    "과학기술정보통신부",
    "국가보훈부",
    "해양수산부",
    "통일부",
    "법무부",
    "국방부",
    "기획재정부",
    "여성가족부",
    "환경부",
    "국세청",
    "산림청",
    "국민연금공단",
    "한국장학재단",
    "한국주택금융공사",
    "주택도시보증공사",
    "근로복지공단",
    "소상공인시장진흥공단",
)


def lexical_overlap_terms(query: str) -> list[str]:
    """검색 본문과 비교할 질의 핵심어를 추출한다."""
    terms = re.findall(r"[0-9A-Za-z가-힣]+", query)
    return list(dict.fromkeys(
        term for term in terms
        if len(term) >= 2 and term not in LEXICAL_STOPWORDS
    ))


def youth_source_bias(query: str) -> float:
    """명시 기관 질의는 존중하고, 그 외 명시적 청년 의도만 youth에 소폭 반영한다."""
    if any(term in query for term in GOV24_INTENT_TERMS):
        return 0.0
    if any(term in query for term in YOUTH_INTENT_TERMS):
        return YOUTH_INTENT_BIAS
    return 0.0


def ranking_metadata() -> dict:
    return {
        "youth_intent_bias": YOUTH_INTENT_BIAS,
        "youth_intent_terms": list(YOUTH_INTENT_TERMS),
        "gov24_intent_terms": list(GOV24_INTENT_TERMS),
        "lexical_overlap_bias": LEXICAL_OVERLAP_BIAS,
        "lexical_stopwords": sorted(LEXICAL_STOPWORDS),
    }
