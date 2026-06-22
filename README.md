# 혜택나침반 (BenefitCompass)

> 청년이 자기 상황을 자연어로 물으면, **받을 수 있는 청년 정책을 근거와 함께** 찾아주는 RAG 기반 검색·질의응답 서비스.
>
> 흩어진 공공 청년정책 데이터를 직접 수집·정제하고, **RAG 파이프라인을 컴포넌트 단위로 직접 구축**한 뒤, **평가셋으로 검색 품질을 측정·개선**한 풀스택 프로젝트입니다.

---

## 한눈에 보기

- **문제:** 청년정책 수천 개가 흩어져 있어 "내가 받을 수 있는 게 뭔지" 찾기 어렵다.
- **해결:** 상황(나이 등) + 자연어 질문 → 의미 검색 + 리랭킹으로 관련 정책을 찾아, Gemini가 **근거 정책을 인용**해 답한다(환각 방지).
- **데이터:** 온통청년 청년정책 API에서 수집한 **2,631개 정책 → 3,083개 청크**.
- **차별점:** LLM API를 부르는 래퍼가 아니라, **임베딩·벡터검색·리랭킹·생성·평가**를 직접 구성하고 **수치로 개선을 입증**했다.

## 아키텍처 (폴리글랏 3-서비스)

```
[React / Vite]                 사용자 입력 (질문 + 나이)
      │  POST /api/ask
      ▼
[Spring Boot API]  ── 요청 검증 · 오케스트레이션 · Gemini 답변 생성 (gemini-3.1-flash-lite)
      │  POST /search
      ▼
[Python FastAPI · ML]  ── e5 질의 임베딩 → pgvector 검색(30) → bge 리랭킹 → 임계값 컷
      │
      ▼
[Postgres + pgvector (Neon)]   정책 메타(구조화) + 본문 청크 벡터(768d)
```

- **주력 백엔드는 Spring Boot(Java 17)**, ML(임베딩·리랭킹)은 Python으로 분리한 **마이크로서비스 구조**.
- 임베딩/리랭킹은 **온디바이스 모델**(무료·무제한), 답변 생성만 Gemini 무료 티어.

## 검색 품질 — 측정하고 개선했다

합성 평가셋 **60문항**(각 질문의 정답 정책을 라벨링)으로 검색 품질을 측정:

| 지표 | bi-encoder (baseline) | + 리랭킹 (bge-reranker-v2-m3) |
|---|---|---|
| recall@1 | 0.400 | **0.517 (+0.117)** |
| recall@5 | 0.733 | 0.717 |
| recall@10 | 0.800 | 0.783 |
| MRR@10 | 0.535 | **0.614 (+0.079)** |

→ **리랭킹으로 1순위 정답률 +12%p, MRR +8%p.** (recall@5/10의 −0.017은 n=60에서 1문항 = 노이즈.)
재현: `eval/make_evalset.py`로 평가셋 생성 → `eval/run_eval.py`(baseline) / `eval/run_eval_rerank.py`(리랭킹).

## 기술 스택

| 영역 | 사용 기술 |
|---|---|
| 프론트 | React 18, Vite |
| API | Spring Boot 3.3 (Java 17), RestClient(Apache HttpClient5) |
| ML | Python, FastAPI, sentence-transformers |
| 임베딩 | `intfloat/multilingual-e5-base` (768d, 온디바이스) |
| 리랭커 | `BAAI/bge-reranker-v2-m3` (cross-encoder) |
| 생성 | Google Gemini (`gemini-3.1-flash-lite`) |
| 저장소 | PostgreSQL + pgvector (Neon) |
| 데이터 | data.go.kr 온통청년 청년정책 OpenAPI |

## 설계 결정 (왜 이렇게 했나)

- **RAG를 직접 구축:** LLM에 검색결과를 통째로 던지지 않고, 임베딩→벡터검색→**리랭킹**→근거기반 생성을 단계별로 소유. 리랭킹 효과를 평가셋으로 정량 측정.
- **온디바이스 임베딩:** Gemini 임베딩 무료 티어가 분당·일일 한도로 막혀, 한국어에 강한 e5 모델을 로컬로 전환 → 비용 0·한도 없음.
- **폴리글랏 분리:** ML 생태계는 Python, 비즈니스 API는 주력인 Spring Boot로 분리해 각 강점을 살림.
- **환각 방지:** 답변은 검색된 정책만 근거로, 정책명을 인용. 못 찾으면 단정하지 않고 안내.
- **서버리스 DB 대응:** Neon이 유휴 시 일시중지되므로 요청마다 새 커넥션으로 견고화.

## 알려진 한계 (정직하게)

- **지역 필터 미지원:** 공공데이터의 지역코드(zipCd)가 부정확(지자체 정책에 타지역 코드가 섞이는 등)하고 기관명도 부서명만 있는 경우가 많아, 신뢰할 수 있는 지역 필터를 만들 수 없었다. → **토픽(지원내용) 검색으로 포지셔닝**, 지역 필터는 데이터 정제 후 과제로 보류.
- **스코프 = 청년정책:** 전국민 혜택(행정안전부 gov24)은 odcloud 게이트웨이 인증 권한 이슈로 적재 보류(향후 확장).

## 실행 (로컬)

```bash
# 1) 데이터 수집 + 임베딩 + 적재 (Neon 등 pgvector Postgres 필요)
cd ingest && python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt -r ../ml-service/requirements.txt
python ingest_youth.py && python embed.py && python load_db.py

# 2) ML 서비스
cd ../ml-service && uvicorn app:app --port 8000

# 3) API (Spring Boot) — 다른 터미널
cd ../api && set GEMINI_API_KEY=... && gradlew bootRun

# 4) 프론트 — 다른 터미널
cd ../web && npm install && npm run dev   # http://localhost:5173
```

`.env`: `DATABASE_URL`(Neon), `YOUTH_API_KEY`(data.go.kr), `GEMINI_API_KEY`(AI Studio).

---

*비영리 학습·포트폴리오 프로젝트. 데이터 출처: 온통청년(공공데이터포털).*
