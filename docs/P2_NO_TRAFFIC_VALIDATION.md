# P2 No-Traffic Production Validation — 2026-08-29

## 검증일 / Commit
- 검증일: 2026-08-29
- git commit: `fe95ac4` (P1 merge) — P2 branch `codex/p2-no-traffic-verification` HEAD `fe95ac4` (no code change, verification only)
- base: `main == origin/main == fe95ac4`, working tree clean

## Service / Revision / Tag

| Service | Old serving (100%) | P2 revision | Tag | Traffic |
|---------|---|---|---|---|
| benefit-ml | `benefit-ml-00001-wvn` (`db3d6c5...` old serving) | `benefit-ml-p2-fe95ac4` (`c1972048...:fe95ac4` new build) | `p2-ml-fe95ac4` | 0% |
| benefit-ml (interim) | — | `benefit-ml-p2-fe95ac2` (`1070274...` pl2) | `p2-ml-fe95ac2` | 0% (failed `p2-fe95ac` removed) |
| benefit-api | `benefit-api-00002-ndd` (`ccc7129...` old) | `benefit-api-p2-fe95ac4-api` (`3ad69e85...:fe95ac4` new build) | `p2-api-fe95ac4` | 0% |
| benefit-api (interim) | — | `benefit-api-p2-fe95ac2` (`f0e88ec...` pl2) | `p2-api-fe95ac2` | 0% |
| benefit-api (interim, fixed) | — | `benefit-api-p2-fe95ac3` (`3ad69e85...:fe95ac4`) | `p2-api-fe95ac3` | 0% |

- region: `asia-northeast3`, project: `healthy-clock-465504-t5`
- image digests:
  - ML serving old: `db3d6c57a376f3ea0f95b52144f1bee450566e4fd939a52e2f8051317498e45d` (no `/ready` — failed probe, not used for P2)
  - ML P2 final: `c1972048e30c5e5b4c8ed72f6d2b7f90d6a599184ffdcf7a915b22de437d586c` (`:fe95ac4`, built from `fe95ac4`)
  - API serving old: `ccc7129750517ef7669c4b35dab2ef7a00910780849c64f3720f96a6930dcde9`
  - API P2 final: `3ad69e85b1ff7ee0322fc565c770bc9f06306d653200577725a67c665865b09f` (`:fe95ac4`)

## Before/After Traffic Allocation

**Before P2 (2026-08-29 15:00 UTC, from `gcloud run services describe`):**
- `benefit-ml`: 100% `benefit-ml-00001-wvn`, tags `pl2a-0ba0aa4`, `pl2-after`, `pl2b-0ba0aa4`, `pl2-before`, `pl2-final` at 0%
- `benefit-api`: 100% `benefit-api-00002-ndd`, same tags at 0%

**After P2:**
- `benefit-ml`: 100% `benefit-ml-00001-wvn` unchanged, `p2-ml-fe95ac2` 0%, `p2-ml-fe95ac4` 0%, old `p2-fe95ac` failed revision remains 0% (not serving)
- `benefit-api`: 100% `benefit-api-00002-ndd` unchanged, `p2-api-fe95ac2` 0%, `p2-api-fe95ac3` 0%, `p2-api-fe95ac4`/`p2-api-fe95ac4-api` 0%
- **Invariant: existing production serving revisions unchanged, P2 revisions 0% production traffic** — `gcloud run services describe` confirms `status.traffic[0].percent 100` still old

## Resource / Runtime Settings

**ML (serving `00001-wvn` and P2 `p2-fe95ac4` via `deploy-production-lab-2.ps1`):**
- CPU 2, memory 2Gi, concurrency 160, timeout 300s, max instances 10, min 0, cpu-boost, port 8080
- startupProbe: `httpGet /ready:8080`, failureThreshold 120, period 2s, timeout 1s (240s budget), initialDelay 0
- env: `RERANK=0`, `DATABASE_URL=[masked Neon]`, `MODEL_LOCAL_ONLY=1`
- serviceAccount: `866560009438-compute@developer.gserviceaccount.com`, ingress `all`

**API (serving `00002-ndd` and P2):**
- CPU 1, memory 1Gi, concurrency 80, timeout 300s, max 20, min 0, cpu-boost, port 8080
- startupProbe: `tcpSocket:8080`, failureThreshold 1, period 240s, timeout 240s (default) — P2 new image uses same
- env: `ML_BASE_URL` (serving: `https://benefit-ml-...`, P2: `https://p2-ml-fe95ac4---benefit-ml-...`), `GEMINI_API_KEY=[masked]`

## /ready

- ML `p2-ml-fe95ac4` — `GET /ready` 200 `{"status":"ready","model_load_ms":34689.071}` (also `p2-ml-fe95ac2` 42037ms), `ContainerHealthy True` in 38s, `Ready True` in 98s — model local-only, no Hub access, `/ready` gated
- ML `p2-fe95ac` (old image `db3d6c57`) — **failed** startup probe 120× 404 (`{"detail":"Not Found"}`) — image lacked `/ready` (pre-P0), correctly rejected, not used for P2 final
- API `p2-api-fe95ac4-api` — `GET /actuator/health` 200 `{"status":"UP"}`, `Ready True` in 10.4s, `ML_BASE_URL` points to `p2-ml-fe95ac4`

## /search Smoke (P2 tagged URLs only)

- ML `POST /search` `{"query":"청년 월세 지원","age":25}` → 200, `results` 5, first `source youth` / `source_id 20260409005400212654` / `title 청년 월세 지원` / `score 0.9050`, `Server-Timing ml_total 908ms (model_wait 0.01, embedding 43, db_connect 454, db_query 409, rerank 0)`
- API `POST /api/policies/recommend` same query → 200, 5 policies, first `source youth` / `title 청년 월세 지원`, `Server-Timing` consistent, `X-Request-ID` present
- Both ML (`p2-fe95ac4`) and API (`p2-fe95ac4-api`) return `source` correctly (fixed from old `1070274` image which returned `source null` due to old SQL without `source` column — rebuilt from `fe95ac4`)

## /ask Bounded Smoke

- `POST /api/ask` `{"query":"청년 월세 지원 알려줘","age":25}` → 200, `sources` 5, `answer` 200 chars, `sources[0].source youth`, no hallucinated `source null`, region `null` contract holds
- No bulk Gemini E2E; single bounded call only, no cost spike

## API→ML Routing

- P2 API `p2-api-fe95ac4-api` env `ML_BASE_URL=https://p2-ml-fe95ac4---benefit-ml-wn6h3zul4q-du.a.run.app` — **P2 stack isolated from serving stack** (`benefit-ml-...` generic URL still points to `00001-wvn`)
- Verified via `gcloud run revisions describe benefit-api-p2-fe95ac4-api` and via `/recommend` returning P2 ML's `source` (not null) — P2 API→P2 ML path confirmed
- Interim `p2-api-fe95ac2` had `ML_BASE_URL` to `p2-ml-fe95ac2` (old pl2 image, source null) — correctly replaced by `p2-fe95ac4`

## Production DB Evidence (read-only)

- `eval/run_data_quality.py` / `scripts/check_db.py` (2026-08-29):
  ```
  youth 2631, gov24 10958, total 13589
  chunks youth 3083, gov24 14526, total 17609
  youth missing 599, gov24 0, missing_embeddings 0, cross_source_same_title 93, region_filter_exposed false
  policy 13589, chunk 17609, missing_embeddings 0
  ```
- P1 state preserved, no corpus reload, no embedding change, region codes untouched

## EXPLAIN ANALYZE (read-only)

- Query: `청년 월세 지원` age 25, `lexical_terms [청년,월세]`, `youth_bias 0.015`, `candidates 30`, production SQL (`ml-service/app.py:SQL` with `DISTINCT ON`, `lexical CTE`, `biz_end >= CURRENT_DATE`, `ORDER BY dist - youth_bias - lexical_bias*overlap`)
- `EXPLAIN (ANALYZE, BUFFERS)` on Neon:
  - `Limit rows 30` → `Sort top-N heapsort` → `Merge Left Join` → `Unique` → `Incremental Sort` → `Merge Join` → `Index Scan policy_pkey` (9779 rows, 3810 filtered by age/biz_end) + `Seq Scan policy_chunk` (17609 rows)
  - Lexical CTE: `GroupAggregate` → `Nested Loop` with `unnest('{청년,월세}')` + `Seq Scan policy` (`~~* '%청년%'` etc) — `Rows Removed by Join Filter 17961`, `Buffers shared hit 8303 read 726`
  - `Buffers shared hit 55122 read 726`, `Planning 6.7ms`, **`Execution 577ms`**, `db_query` in ML header `409ms` (includes network)
  - No vector index used (`Seq Scan policy_chunk`) — expected for `DISTINCT ON` + lexical join without IVFFlat; not a blocker for 17k chunks, but noted for future hybrid retrieval
  - No sequential scan on policy without filter, no pathological plan, expiration filtering applied

## Cold / Warm Latency (P2 tagged, warm = second request)

- ML `p2-ml-fe95ac4`: `model_load 34.6s` (cold startup, from `/ready`), `ContainerHealthy 38s`, `Ready 98s` — cold 35-42s range, warm `/search` 908ms–1512ms (earlier `p2-ml-fe95ac2` warm 1512ms, now 908ms with same DB)
- API `p2-api-fe95ac4-api`: `Containers became healthy 6.5s`, `Ready 10.4s` — warm `/recommend` 1487ms, `/ask` 2674ms (includes Gemini), `ml_db_query` 415ms
- No separate cold API measurement (scale-to-zero, but P2 revisions min 0, first request after deploy measured as warm after readiness)

## Limited Load

- 10 concurrent `POST /api/policies/recommend` (`query "청년 지원 {i}"`, age 25) via `p2-api-fe95ac4` with concurrency 80, timeout 300s:
  ```
  [(200,2303ms),(200,2298ms),(200,1638ms),(200,2289ms),(200,2297ms),
   (200,1386ms),(200,1885ms),(200,2109ms),(200,2128ms),(200,2124ms)]
  5xx 0, p95 2303ms
  ```
- No timeout, no 5xx, no memory exhaustion, concurrency 80 not exceeded (5 workers)

## Before/After Traffic Invariant

- Before: `benefit-ml 100% benefit-ml-00001-wvn`, `benefit-api 100% benefit-api-00002-ndd`
- After: same 100% to those revisions, P2 tags `p2-ml-fe95ac4`/`p2-ml-fe95ac2` and `p2-api-fe95ac4*` at 0% — `gcloud run services describe` confirms unchanged, `mergeState CLEAN`

## Production Retrieval Contract

- `RERANK=0`, `CANDIDATES=30`, `COSINE_MIN=0.78`, `LEXICAL 0.01`, `strip_region`, region disabled, `intfloat/multilingual-e5-base` — unchanged, verified via `ml-service/app.py` and `source_ranking.py` and `gcloud` env (`RERANK 0`, `MODEL_LOCAL_ONLY 1`)

## P0/P1 Evidence Unchanged

- `eval/canonical_manifest.json`, `eval/canonical_*.json` — `git diff fe95ac4...HEAD -- eval/canonical*` empty
- `eval/data_quality.json` 599 preserved
- No `ingest` re-run, no `load_db`, no `region` re-enable

## Files Changed (P2)

- `docs/P2_NO_TRAFFIC_VALIDATION.md` (new) — this file
- (No code change — verification only; `ml-service`/`api` images rebuilt from `fe95ac4` but Dockerfiles unchanged)

## Tests

- `python -m pytest ingest -v` — 35 passed
- `python -m pytest eval -v` — 4 passed
- `python -m pytest ml-service -v` — 17 passed
- `python -m compileall -q ingest ml-service eval scripts` — ok
- `git diff --check` — 0

## Commits

- P2 branch `codex/p2-no-traffic-verification` HEAD `fe95ac4` (no new commit yet — docs only, will commit as `docs: record P2 no-traffic production validation`)

## Issues Found

- **BLOCKER fixed**: Initial P2 ML `p2-fe95ac` with image `db3d6c57` (old serving image) failed startup probe (`/ready` 404) — image lacked `/ready` (pre-`0ba0aa4`). Fixed by rebuilding ML from `fe95ac4` (`c1972048...:fe95ac4`, `source` column present) as `p2-fe95ac4`.
- **BLOCKER fixed**: Initial P2 API `p2-api-fe95ac2` with image `f0e88ec2` (0ba0aa4) lacked `region` 400 rejection (PolicyController without `rejectUnsupportedRegion`). Fixed by rebuilding API from `fe95ac4` (`3ad69e85...:fe95ac4`) as `p2-fe95ac4-api` — now `region` correctly 400.
- No other blocker; ML `source null` in old image also fixed by rebuild.

## P3 Public Rollout Recommendation

- P2 stack (`p2-ml-fe95ac4` ↔ `p2-api-fe95ac4`) is Ready, 0% traffic, correctly isolated, DB 13589/17609, retrieval contract intact, latency/limited load no blocker.
- Recommend P3 review to promote `p2-ml-fe95ac4` and `p2-api-fe95ac4-api` to production traffic (gradual, e.g., 10% canary then 100%) after final approval. Keep `00001-wvn`/`00002-ndd` as rollback targets. Public still not rolled out — P2 is no-traffic only.

