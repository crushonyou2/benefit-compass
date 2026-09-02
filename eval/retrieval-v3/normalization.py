"""Normalization helpers — frozen semantics, no additions."""
from __future__ import annotations
import re
import unicodedata

# SIDO mapping exact from ml-service/app.py
SIDO = {
    "11": ["서울"], "26": ["부산"], "27": ["대구"], "28": ["인천"], "29": ["광주"],
    "30": ["대전"], "31": ["울산"], "36": ["세종"], "41": ["경기"],
    "43": ["충북", "충청북도"], "44": ["충남", "충청남도"], "46": ["전남", "전라남도"],
    "47": ["경북", "경상북도"], "48": ["경남", "경상남도"], "50": ["제주"],
    "51": ["강원"], "52": ["전북", "전라북도"],
}

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

YOUTH_INTENT_TERMS = ("청년", "대학생", "사회초년생")
YOUTH_INTENT_BIAS = 0.015
GOV24_INTENT_TERMS = (
    "국토교통부", "중소벤처기업부", "고용노동부", "보건복지부", "교육부",
    "행정안전부", "문화체육관광부", "농림축산식품부", "산업통상자원부",
    "과학기술정보통신부", "국가보훈부", "해양수산부", "통일부", "법무부",
    "국방부", "기획재정부", "여성가족부", "환경부", "국세청", "산림청",
    "국민연금공단", "한국장학재단", "한국주택금융공사", "주택도시보증공사",
    "근로복지공단", "소상공인시장진흥공단",
)
LEXICAL_OVERLAP_BIAS = 0.01
COSINE_MIN = 0.78
CANDIDATES = 30
RERANK = 0
EMBED_MODEL = "intfloat/multilingual-e5-base"

def strip_region(q: str) -> str:
    """Exact from ml-service/app.py."""
    out = q
    for kws in SIDO.values():
        for kw in kws:
            out = out.replace(kw, " ")
    cleaned = " ".join(out.split())
    return cleaned or q

def lexical_overlap_terms(query: str) -> list[str]:
    """Frozen source_ranking lexical_overlap_terms."""
    terms = re.findall(r"[0-9A-Za-z가-힣]+", query)
    return list(dict.fromkeys(term for term in terms if len(term) >= 2 and term not in LEXICAL_STOPWORDS))

def youth_source_bias(query: str) -> float:
    if any(term in query for term in GOV24_INTENT_TERMS):
        return 0.0
    if any(term in query for term in YOUTH_INTENT_TERMS):
        return YOUTH_INTENT_BIAS
    return 0.0

def normalize_exact(s: str) -> str:
    """One exact normalization: NFC -> strip -> collapse whitespace -> casefold."""
    t = unicodedata.normalize("NFC", s)
    t = t.strip()
    t = re.sub(r"\s+", " ", t)
    t = t.casefold()
    return t

def is_alnum_hangul(ch: str) -> bool:
    return ("0" <= ch <= "9") or ("A" <= ch <= "Z") or ("a" <= ch <= "z") or ("\uAC00" <= ch <= "\uD7A3")

def format_qvec(vec) -> str:
    """Format vector as pgvector string with 6 decimals (production)."""
    return "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
