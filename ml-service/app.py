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
import logging
import time
from contextlib import asynccontextmanager
from typing import Annotated, Optional

from dotenv import load_dotenv
import psycopg2
from fastapi import FastAPI, Header, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from runtime_state import ModelRuntime, safe_request_id, server_timing_header
from source_ranking import youth_source_bias

# .env는 아래 모듈 상수보다 먼저 로드한다. 이전에는 load_dotenv가 이 상수들 아래에서 돌아
# RERANK·COSINE_MIN·MODEL_READY_TIMEOUT_SECONDS·MODEL_LOCAL_ONLY 네 값은 .env에 적어도
# 적용되지 않았다(실제 환경변수로만 동작). Cloud Run에는 .env 파일이 없어 배포 동작은
# 그대로고, 바뀌는 것은 로컬 개발 환경뿐이다.
ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

CANDIDATES = 30   # bi-encoder가 뽑는 후보 수 (리랭킹 대상)
RERANK = os.getenv("RERANK", "1") == "1"             # 0이면 리랭커 끔 (배포: 무료 CPU 속도/메모리)
COSINE_MIN = float(os.getenv("COSINE_MIN", "0.78"))  # 리랭커 끌 때 bi-encoder 코사인 컷
MODEL_READY_TIMEOUT_SECONDS = float(os.getenv("MODEL_READY_TIMEOUT_SECONDS", "120"))
MODEL_LOCAL_ONLY = os.getenv("MODEL_LOCAL_ONLY", "0") == "1"
EMBED_MODEL_NAME = "intfloat/multilingual-e5-base"
RERANK_MODEL_NAME = "BAAI/bge-reranker-v2-m3"
DEFAULT_RERANK_MIN_SCORE = 0.12
RERANK_TEXT_LIMIT = 400
SEARCH_RESULT_COLUMNS = (
    "source", "source_id", "title", "org", "support_content", "apply_method",
    "apply_url", "age_min", "age_max", "income_etc", "score",
)

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


def rerank_candidates(query, candidates, reranker, min_score):
    """Production cross-encoder input, ordering, and threshold contract."""
    pairs = [
        [query, ((candidate["title"] or "") + " "
                 + (candidate["support_content"] or ""))[:RERANK_TEXT_LIMIT]]
        for candidate in candidates
    ]
    for candidate, logit in zip(candidates, reranker.predict(pairs)):
        candidate["score"] = float(logit)
    candidates.sort(key=lambda candidate: candidate["score"], reverse=True)
    return [candidate for candidate in candidates if candidate["score"] >= min_score]

DB = os.getenv("DATABASE_URL", "").strip()

SQL = """
SELECT t.source, t.source_id, t.title, t.org, t.support_content, t.apply_method,
       t.apply_url, t.age_min, t.age_max, t.income_etc, 1 - t.dist AS score
FROM (
  SELECT DISTINCT ON (p.id) p.source, p.source_id, p.title, p.org, p.support_content,
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
ORDER BY t.dist - CASE WHEN t.source = 'youth' THEN %(youth_bias)s ELSE 0 END,
         t.dist, t.source, t.source_id
LIMIT %(n)s
"""

# Uvicorn config owns this logger in production, so INFO lifecycle/search events
# are emitted instead of being silently filtered by Python's WARNING root level.
log = logging.getLogger("uvicorn.error")
runtime = ModelRuntime()


def load_models():
    """Load imports and weights together so the recorded duration is complete."""
    if MODEL_LOCAL_ONLY:
        # Applies to every Hugging Face-backed loader, including the optional reranker.
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
    from sentence_transformers import SentenceTransformer

    kwargs = {"local_files_only": True} if MODEL_LOCAL_ONLY else {}
    models = {"model": SentenceTransformer(EMBED_MODEL_NAME, **kwargs)}
    if RERANK:
        from sentence_transformers import CrossEncoder
        models["reranker"] = CrossEncoder(RERANK_MODEL_NAME, **kwargs)
    return models


def load_models_with_log():
    log.info("ml_model_load event=start rerank=%s local_only=%s", RERANK, MODEL_LOCAL_ONLY)
    try:
        models = load_models()
    except BaseException as exc:
        log.error("ml_model_load event=error error_type=%s", type(exc).__name__)
        raise
    snapshot = runtime.snapshot()
    log.info("ml_model_load event=complete duration_ms=%.3f", snapshot.model_load_ms)
    return models


@asynccontextmanager
async def lifespan(app: FastAPI):
    runtime.start(load_models_with_log)
    yield


app = FastAPI(title="BenefitCompass ML Service", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


class SearchReq(BaseModel):
    query: str
    age: Optional[int] = None
    region: Optional[str] = None   # 법정동코드 앞자리 (서울=11)
    k: int = 5
    min_score: float = DEFAULT_RERANK_MIN_SCORE  # 리랭커 원시점수 임계값 — 미만은 관련 없음


@app.get("/health")
def health():
    """Liveness only: the process can respond even while models are loading."""
    return {"status": "ok"}


@app.get("/ready")
def ready():
    """Readiness is 200 only after every configured model is loaded."""
    snapshot = runtime.snapshot()
    status_code = 200 if snapshot.status == "ready" else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "status": snapshot.status,
            "model_load_ms": round(snapshot.model_load_ms, 3),
        },
    )


def error_response(status_code: int, detail: str, timings: dict[str, float]) -> JSONResponse:
    """Return fixed error content with the same privacy-safe timing contract as success."""
    return JSONResponse(
        status_code=status_code,
        content={"detail": detail},
        headers={
            "Server-Timing": server_timing_header(timings),
            "X-ML-Model-Load-Ms": f"{runtime.snapshot().model_load_ms:.3f}",
        },
    )


@app.post("/search")
def search(
    req: SearchReq,
    response: Response,
    x_request_id: Annotated[str | None, Header()] = None,
):
    request_started_ns = time.perf_counter_ns()
    request_id = safe_request_id(x_request_id)
    timings = {name: 0.0 for name in
               ("model_wait", "embedding", "db_connect", "db_query", "rerank")}
    conn = None
    if req.region is not None:
        timings["ml_total"] = (time.perf_counter_ns() - request_started_ns) / 1_000_000.0
        log.warning(
            "ml_search request_id=%s outcome=invalid_request reason=region_unavailable "
            "total_ms=%.3f",
            request_id, timings["ml_total"],
        )
        return error_response(400, "Region filter is currently unavailable", timings)
    try:
        started_ns = time.perf_counter_ns()
        try:
            models = runtime.wait(MODEL_READY_TIMEOUT_SECONDS)
        finally:
            timings["model_wait"] = (time.perf_counter_ns() - started_ns) / 1_000_000.0

        q = strip_region(req.query)   # 지역어 제거 (지역 필터 미지원, 잡음 방지)
        started_ns = time.perf_counter_ns()
        try:
            qvec = models["model"].encode([f"query: {q}"], normalize_embeddings=True)[0]
        finally:
            timings["embedding"] = (time.perf_counter_ns() - started_ns) / 1_000_000.0
        vec = "[" + ",".join(f"{x:.6f}" for x in qvec) + "]"

        # Neon 등 서버리스 DB는 유휴 시 잠들어 풀의 커넥션이 죽으므로 요청마다 새 연결.
        started_ns = time.perf_counter_ns()
        try:
            conn = psycopg2.connect(DB)
        finally:
            timings["db_connect"] = (time.perf_counter_ns() - started_ns) / 1_000_000.0
        started_ns = time.perf_counter_ns()
        try:
            cur = conn.cursor()
            try:
                cur.execute(SQL, {
                    "vec": vec,
                    "age": req.age,
                    "rp": (f"{req.region}%" if req.region else None),
                    "youth_bias": youth_source_bias(q),
                    "n": CANDIDATES,
                })
                rows = cur.fetchall()
            finally:
                cur.close()
        finally:
            timings["db_query"] = (time.perf_counter_ns() - started_ns) / 1_000_000.0

        cands = [dict(zip(SEARCH_RESULT_COLUMNS, row)) for row in rows]
        cands = region_filter(cands, req.region)   # 기관명 기반 지역 보강 필터

        if cands and RERANK:
            started_ns = time.perf_counter_ns()
            try:
                # cross-encoder 리랭킹: 질의↔정책을 직접 비교해 관련성 재산정
                cands = rerank_candidates(
                    q, cands, models["reranker"], req.min_score)
            finally:
                timings["rerank"] = (time.perf_counter_ns() - started_ns) / 1_000_000.0
        elif cands:
            cands = [cand for cand in cands if cand["score"] >= COSINE_MIN]

        result = {"results": cands[:req.k]}
        timings["ml_total"] = (time.perf_counter_ns() - request_started_ns) / 1_000_000.0
        response.headers["Server-Timing"] = server_timing_header(timings)
        response.headers["X-ML-Model-Load-Ms"] = f"{runtime.snapshot().model_load_ms:.3f}"
        log.info(
            "ml_search request_id=%s outcome=success result_count=%d "
            "model_wait_ms=%.3f embedding_ms=%.3f db_connect_ms=%.3f "
            "db_query_ms=%.3f rerank_ms=%.3f total_ms=%.3f",
            request_id, len(result["results"]), timings["model_wait"],
            timings["embedding"], timings["db_connect"], timings["db_query"],
            timings["rerank"], timings["ml_total"],
        )
        return result
    except (TimeoutError, RuntimeError) as exc:
        timings["ml_total"] = (time.perf_counter_ns() - request_started_ns) / 1_000_000.0
        log.error(
            "ml_search request_id=%s outcome=not_ready error_type=%s "
            "model_wait_ms=%.3f total_ms=%.3f",
            request_id, type(exc).__name__, timings["model_wait"], timings["ml_total"],
        )
        return error_response(503, "ML models are not ready", timings)
    except Exception as exc:
        timings["ml_total"] = (time.perf_counter_ns() - request_started_ns) / 1_000_000.0
        log.error(
            "ml_search request_id=%s outcome=error error_type=%s "
            "model_wait_ms=%.3f embedding_ms=%.3f db_connect_ms=%.3f "
            "db_query_ms=%.3f rerank_ms=%.3f total_ms=%.3f",
            request_id, type(exc).__name__, timings["model_wait"],
            timings["embedding"], timings["db_connect"], timings["db_query"],
            timings["rerank"], timings["ml_total"],
        )
        return error_response(500, "ML search failed", timings)
    finally:
        if conn is not None:
            try:
                conn.close()
            except Exception as exc:
                log.error("ml_connection_close request_id=%s error_type=%s",
                          request_id, type(exc).__name__)
