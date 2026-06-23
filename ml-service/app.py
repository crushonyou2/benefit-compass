"""
혜택나침반 ML/검색 서비스 (FastAPI).

Spring Boot API가 호출하는 내부 서비스. 질의를 e5로 임베딩하고,
구조적 자격필터 + pgvector 검색으로 후보 정책을 반환한다.
RERANK=1(기본, 로컬)이면 cross-encoder 리랭킹, RERANK=0(배포)이면 bi-encoder만 사용.

실행: uvicorn app:app --port 8000
필요(env): DATABASE_URL / 선택: RERANK, COSINE_MIN
"""
import os
import pathlib
from contextlib import asynccontextmanager
from typing import Optional

from dotenv import load_dotenv
import psycopg2
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer, CrossEncoder

CANDIDATES = 30   # bi-encoder가 뽑는 후보 수 (리랭킹 대상)
RERANK = os.getenv("RERANK", "1") == "1"             # 0이면 리랭커 끔 (배포: 무료 CPU 속도/메모리)
COSINE_MIN = float(os.getenv("COSINE_MIN", "0.78"))  # 리랭커 끌 때 bi-encoder 코사인 컷

# 지역코드(zipCd)가 부정확해 기관명으로 보강 필터링. region 코드 앞2자리 → 시도 키워드.
SIDO = {
    "11": ["서울"], "26": ["부산"], "27": ["대구"], "28": ["인천"], "29": ["광주"],
    "30": ["대전"], "31": ["울산"], "36": ["세종"], "41": ["경기"],
    "43": ["충북", "충청북도"], "44": ["충남", "충청남도"], "46": ["전남", "전라남도"],
    "47": ["경북", "경상북도"], "48": ["경남", "경상남도"], "50": ["제주"],
    "51": ["강원"], "52": ["전북", "전라북도"],
}


def strip_region(q: str) -> str:
    """질의에서 시도 키워드 제거 — 지역 필터는 데이터 한계로 미지원이라 잡음만 됨."""
    out = q
    for kws in SIDO.values():
        for kw in kws:
            out = out.replace(kw, " ")
    cleaned = " ".join(out.split())
    return cleaned or q


def region_filter(cands, region):
    """기관명에 '다른 시도'가 박혀있으면 제외. 시도 표기 없으면 전국/중앙으로 보고 통과."""
    if not region:
        return cands
    sel = SIDO.get(region, [])
    others = [kw for code, kws in SIDO.items() if code != region for kw in kws]
    out = []
    for c in cands:
        org = c.get("org") or ""
        if any(kw in org for kw in sel) or not any(kw in org for kw in others):
            out.append(c)
    return out

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
DB = os.getenv("DATABASE_URL", "").strip()

SQL = """
SELECT t.source_id, t.title, t.org, t.support_content, t.apply_method,
       t.apply_url, t.age_min, t.age_max, t.income_etc, 1 - t.dist AS score
FROM (
  SELECT DISTINCT ON (p.id) p.source_id, p.title, p.org, p.support_content,
         p.apply_method, p.apply_url, p.age_min, p.age_max, p.income_etc,
         (c.embedding <=> %(vec)s::vector) AS dist
  FROM policy_chunk c
  JOIN policy p ON p.id = c.policy_id
  WHERE ( %(age)s IS NULL OR p.age_limit_yn IS NOT TRUE
          OR %(age)s BETWEEN p.age_min AND p.age_max )
    AND ( %(rp)s IS NULL
          OR EXISTS (SELECT 1 FROM unnest(p.region_codes) rc WHERE rc LIKE %(rp)s) )
    AND ( p.biz_end IS NULL OR p.biz_end >= CURRENT_DATE )   -- 만료 정책 제외
  ORDER BY p.id, c.embedding <=> %(vec)s::vector
) t
ORDER BY t.dist
LIMIT %(n)s
"""

state = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    state["model"] = SentenceTransformer("intfloat/multilingual-e5-base")
    if RERANK:
        state["reranker"] = CrossEncoder("BAAI/bge-reranker-v2-m3")
    yield


app = FastAPI(title="BenefitCompass ML Service", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


class SearchReq(BaseModel):
    query: str
    age: Optional[int] = None
    region: Optional[str] = None   # 법정동코드 앞자리 (서울=11)
    k: int = 5
    min_score: float = 0.12        # 리랭커 원시점수 임계값 — 미만은 관련 없음(한 개 knob, 튜닝 가능)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/search")
def search(req: SearchReq):
    q = strip_region(req.query)   # 지역어 제거 (지역 필터 미지원, 잡음 방지)
    qvec = state["model"].encode([f"query: {q}"], normalize_embeddings=True)[0]
    vec = "[" + ",".join(f"{x:.6f}" for x in qvec) + "]"
    # Neon 등 서버리스 DB는 유휴 시 잠들어 풀의 커넥션이 죽으므로 요청마다 새 연결.
    conn = psycopg2.connect(DB)
    try:
        cur = conn.cursor()
        cur.execute(SQL, {"vec": vec, "age": req.age,
                          "rp": (f"{req.region}%" if req.region else None), "n": CANDIDATES})
        rows = cur.fetchall()
        cur.close()
    finally:
        conn.close()

    cols = ["source_id", "title", "org", "support_content", "apply_method",
            "apply_url", "age_min", "age_max", "income_etc", "score"]
    cands = [dict(zip(cols, r)) for r in rows]
    cands = region_filter(cands, req.region)   # 기관명 기반 지역 보강 필터
    if not cands:
        return {"results": []}

    if RERANK:
        # cross-encoder 리랭킹: 질의↔정책을 직접 비교해 관련성 재산정 (코사인보다 정확)
        pairs = [[q, ((c["title"] or "") + " " + (c["support_content"] or ""))[:400]]
                 for c in cands]
        for c, lg in zip(cands, state["reranker"].predict(pairs)):
            c["score"] = float(lg)   # cross-encoder 원시 점수
        cands.sort(key=lambda c: c["score"], reverse=True)
        cands = [c for c in cands if c["score"] >= req.min_score]
    else:
        # 리랭커 미사용(배포 등): bi-encoder 코사인 점수로 컷 (이미 거리순 정렬)
        cands = [c for c in cands if c["score"] >= COSINE_MIN]
    return {"results": cands[:req.k]}
