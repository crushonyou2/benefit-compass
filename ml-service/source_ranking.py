"""복수 출처 벡터 검색의 작은 질의 의도 보정 규칙."""

YOUTH_INTENT_BIAS = 0.015
YOUTH_INTENT_TERMS = ("청년", "대학생", "사회초년생")
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
    }
