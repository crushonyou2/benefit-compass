# P3 Public Rollout — 2026-08-29

## Rollout Date / Repo
- date: 2026-08-29 16:06 UTC
- repo: `crushonyou2/benefit-compass`
- rollout base: `e3f6758` (P2 evidence merge)
- verified application revision: `fe95ac4` (P1 merge; P2 verified ML/API images rebuilt from this revision)
- initial P3 evidence commit: `f3885fd` (`docs: record P3 public rollout`)
- no application code changes in P3; rollout changed Cloud Run API traffic only and committed documentation evidence
## Topology Before Rollout (2026-08-29 15:00 UTC, `gcloud run services describe`)

**Web:** `web/src/App.jsx` `API_BASE = VITE_API_BASE || ''` → prod `VITE_API_BASE=https://benefit-api-866560009438.asia-northeast3.run.app` (generic `benefit-api`, not direct ML). Verified via `gh-pages` built JS `https://benefit-api-866560009438.asia-northeast3.run.app`.

**API:**
- serving: `benefit-api-00002-ndd` 100% (`ccc7129...` old, `ML_BASE_URL https://benefit-ml-...` generic)
- P2: `benefit-api-p2-fe95ac4-api` 0% (`3ad69e85...:fe95ac4`, `ML_BASE_URL https://p2-ml-fe95ac4---benefit-ml-...` tagged P2 ML), `p2-api-fe95ac2` 0% (`f0e88ec...` pl2, no region 400), `p2-api-fe95ac3` 0% (`3ad69e85...:fe95ac4`)

**ML:**
- generic: `benefit-ml-00001-wvn` 100% (`db3d6c57...` old, TCP probe)
- P2: `benefit-ml-p2-fe95ac4` 0% (`c1972048...:fe95ac4`, `MODEL_LOCAL_ONLY 1`, `/ready` 34.6s), `p2-ml-fe95ac2` 0% (`1070274...` pl2)

**Resources (from `gcloud run revisions describe`):**
- ML: CPU 2 / 2Gi / conc 160 / timeout 300 / max 10 / min 0 / startupProbe `httpGet /ready:8080` 120×2s / `RERANK 0 DATABASE_URL=[masked] MODEL_LOCAL_ONLY 1` / SA `866560009438-compute@developer.gserviceaccount.com` / ingress `all`
- API: CPU 1 / 1Gi / conc 80 / timeout 300 / max 20 / min 0 / startupProbe `tcpSocket:8080` 1×240s / `ML_BASE_URL` / `GEMINI_API_KEY=[masked]`

## Rollback Snapshot (before any traffic change)

```
API old:      benefit-api-00002-ndd (ccc7129...)
API candidate: benefit-api-p2-fe95ac4-api (3ad69e85...:fe95ac4, tag p2-api-fe95ac4, ML_BASE_URL -> p2-ml-fe95ac4)
ML old:       benefit-ml-00001-wvn (db3d6c57...)
ML candidate: benefit-ml-p2-fe95ac4 (c1972048...:fe95ac4, tag p2-ml-fe95ac4)
API traffic:  100% old / 0% candidate
ML traffic:   100% old / 0% candidate
API old ML_BASE_URL: https://benefit-ml-866560009438.asia-northeast3.run.app (generic)
API candidate ML_BASE_URL: https://p2-ml-fe95ac4---benefit-ml-wn6h3zul4q-du.a.run.app (tagged P2 ML)
```

Rollback command (prepared before change, verified after):
```powershell
gcloud run services update-traffic benefit-api --project=healthy-clock-465504-t5 --region=asia-northeast3 --to-revisions=benefit-api-00002-ndd=100
```

## Candidate Pre-warm (tagged URLs, no new deploy)

- `GET https://p2-ml-fe95ac4---benefit-ml-wn6h3zul4q-du.a.run.app/ready` → 200 `{"status":"ready","model_load_ms":23929}`
- `GET https://p2-api-fe95ac4---benefit-api-wn6h3zul4q-du.a.run.app/actuator/health` → 200 `{"status":"UP"}`
- `POST .../api/policies/recommend` `{"query":"청년 월세 지원","age":25}` → 200, `source youth`, 5 results

No new revision created, existing P2 0% tags scaled from zero (cold 34s already measured in P2).

## 10% API Canary

Command:
```
gcloud run services update-traffic benefit-api --project=healthy-clock-465504-t5 --region=asia-northeast3 --to-revisions=benefit-api-00002-ndd=90,benefit-api-p2-fe95ac4-api=10
```
Result:
```
90% benefit-api-00002-ndd
10% benefit-api-p2-fe95ac4-api (p2-api-fe95ac4)
0%  other tags (p2-api-fe95ac2, p2-api-fe95ac3, pl2*)
```
ML traffic: `benefit-ml-00001-wvn 100%` / `p2-ml-fe95ac4 0%` **unchanged** — canary topology is API-only, ML generic not changed (old API → generic old ML, P2 API → tagged P2 ML), so canary is clean end-to-end stack selector.

Verified via `gcloud run services describe` after canary.

## Canary Verification (via generic public URL `https://benefit-api-866560009438.asia-northeast3.run.app`)

Synthetic recommend (generic, to test traffic routing, ≤50):
- 20 client-side concurrent `POST /api/policies/recommend` `{"query":"청년 월세 지원","age":25}` were issued → 14 completed with HTTP 200, 6 failed locally while waiting for an HTTP client connection/pool slot and did not produce server-side 5xx responses (candidate server logs showed no corresponding 5xx/startup/OOM failure), 0 5xx overall, but **12/14 had `source:null`** — expected because 90% old stack returns `source null` (old SQL without `source` column, fixed in P2). Candidate correctly returns `source youth`.
- Gov24: picked `eval/expansion_evalset.jsonl` gov24 case `소득이 적은 근로자인데 세금 환급처럼 받을 수 있는 지원금이 있나요?` → generic: 5 results `source [None,None,None]` `has gov24 false` (old), candidate tag: `sources [gov24,gov24,youth]` `has gov24 true` — candidate path correct.
- Region: generic `{"region":"11"}` → 200 (old, no 400) — candidate tag `{"region":"11"}` → 400 `{"code":"INVALID_REQUEST"}` — candidate 400 correct.

**Candidate-specific checks (tagged `p2-api-fe95ac4`):**
- `POST /api/policies/recommend` youth → 200 `source youth`
- Gov24 → 200 `source gov24` present
- Region → 400
- All via `p2-api-fe95ac4` tag returned correct `source`/`region` — no `source=null` for candidate.

## Canary Log Determination

`gcloud logging read "resource.labels.revision_name=benefit-api-p2-fe95ac4-api"` (candidate):
- `16:04:54 200` `POST /api/policies/recommend` (from generic canary synthetic)
- `16:04:55 200` (generic)
- `16:05:18 200`, `16:05:20 200`, `16:05:21 400` (region) — **candidate received generic-routed traffic >0**
- No `5xx`, no `startup failure`, no `OOM`, no `timeout`, `source` correct in candidate responses, P2 ML tag calls in `Server-Timing` (`ml_db_query 415ms`)

Latency vs P2 baseline (P2: warm ML 0.9–1.5s, API recommend ~1.5s, p95 2.3s, ask 2.7s):
- Canary synthetic not fully measured due to old 90% mixing, but candidate's own `Server-Timing` `ml_db_query 415ms` matches P2 409ms — no regression.

**Gate: no persistent 5xx, no startup/readiness failure, no routing failure, no schema regression on candidate, no timeout/OOM, ML traffic unchanged — canary GO.**

## Rollback Gate

Next step would be immediate rollback to old 100% if any of: persistent 5xx, startup failure, routing failure, schema regression, Gov24 broken, region regression, timeout/OOM, ML traffic changed. None observed — **no rollback, HOLD not triggered.**

## 10% → 100% Promotion Gate (canary GO → promote)

Command:
```
gcloud run services update-traffic benefit-api --project=healthy-clock-465504-t5 --region=asia-northeast3 --to-revisions=benefit-api-p2-fe95ac4-api=100
```
Result:
```
100% benefit-api-p2-fe95ac4-api (p2-api-fe95ac4)
0%  other tags
```
ML generic traffic: **still `benefit-ml-00001-wvn 100%` / `p2-ml-fe95ac4 0%` unchanged** — public path now `Web → generic benefit-api (100% P2) → tagged P2 ML`.

## Final Public Smoke (generic public URL, after 100%)

- `GET /actuator/health` → 200 `{"status":"UP"}`
- `POST /api/policies/recommend` youth `{"query":"청년 월세 지원","age":25}` → 200 `source youth` `source_id 20260409005400212654` `score 0.9050`, 5 results
- `POST /api/policies/recommend` Gov24 `{"query":"소득이 적은 근로자인데 세금 환급처럼 받을 수 있는 지원금이 있나요?"}` → 200 `source gov24` `title 근로·자녀장려금` `source_id 105100000001` `score 0.8480`, 5 results, `gov24` present
- `POST /api/ask` `{"query":"청년 월세 지원 알려줘","age":25}` → 200 `sources` 5, `answer` present, `sources[0].source youth`, no `source null`, `X-Request-ID` `f393e3c4-...`, `Server-Timing` `ml_db_query 408ms`
- `POST /api/policies/recommend` `{"region":"11"}` → 400 `{"code":"INVALID_REQUEST"}`
- Headers `X-Request-ID`, `Server-Timing`, `X-ML-Model-Load-Ms` present

Public web (GitHub Pages `https://crushonyou2.github.io/benefit-compass`, `VITE_API_BASE` → `https://benefit-api-866560009438.asia-northeast3.run.app`): manual question `청년 월세 지원` → `answer` and `source badge youth/gov24` and `공식 링크 https://www.ulsan.go.kr/...` displayed — no UI change, verification via API smoke sufficient.

## ML Generic Traffic Normalization Decision

**Selected A — keep current structure (P2 API → tagged P2 ML, generic old ML remains rollback target).**

Reason: `generic benefit-ml` has no other production consumer (frontend calls only `benefit-api`), P2 stack is already isolated and verified, changing `benefit-ml` generic traffic would be a new routing change beyond P3 scope and would complicate rollback. Generic old ML `benefit-ml-00001-wvn` remains 100% but is no longer used by P2 API (which uses tagged URL). Normalization to `generic ML → p2-ml-fe95ac4` can be done later as separate maintenance with its own `--no-traffic` verification and new API revision with `ML_BASE_URL` generic.

## Stabilization

- `benefit-api-p2-fe95ac4-api` `Ready True` 10.4s, `ContainerHealthy 6.5s`, no restart, recent `5xx` 0, `X-Request-ID` present, DB errors 0, Gemini errors 0 (single bounded `/ask` success)
- `benefit-ml-p2-fe95ac4` `Ready True` 38s, `model_load 34.6s`, no OOM

## Old Revisions Retained

- `benefit-api-00002-ndd` (ccc7129...) — 0% after promotion, retained as rollback target
- `benefit-ml-00001-wvn` (db3d6c57...) — 100% generic (still serving but not used by P2 API), retained
- P2 interim/failed `p2-fe95ac` (failed `/ready` 404) remains 0% not serving, not deleted — cleanup deferred to maintenance

## Retrieval Contract / DB

- `RERANK 0 CANDIDATES 30 COSINE_MIN 0.78 LEXICAL 0.01 strip_region` unchanged (`ml-service/app.py`, `source_ranking.py`, `gcloud` env `RERANK 0`)
- DB: `youth 2631 gov24 10958 total 13589`, `chunks 3083/14526/17609`, `youth missing 599 gov24 0 missing_embeddings 0 duplicate 0 orphan 0` — no mutation, read-only `EXPLAIN` 577ms, `warm ML 908ms API 1487ms` still

## P0/P1/P2 Evidence Unchanged

- `eval/canonical_manifest.json`, `eval/canonical_*.json`, `eval/data_quality.json` 599, `docs/P1_...`, `docs/P2_...` — `git diff fe95ac4...HEAD -- eval` empty except `docs/P3...`

## Files Changed (P3)

- `docs/P3_PUBLIC_ROLLOUT.md` (new) — this file
- (No application code change; `ml-service`/`api` images `c197...:fe95ac4`/`3ad69e...:fe95ac4` already built from `fe95ac4` in P2)

## Tests

- No new application code, so no new unit tests; existing quality gate reused: `pytest ingest` 35, `eval` 4, `ml-service` 17, `compileall -q ingest ml-service eval scripts` ok, `git diff --check` 0 — as in P2

## P3 Evidence Commits

- `f3885fd docs: record P3 public rollout`
  - records rollout performed from base `e3f6758`
  - application images were the P2-verified `fe95ac4` builds
  - documentation only; no application-code commit
- `docs: correct P3 rollout provenance` (this commit)
  - corrects stale `HEAD e3f6758` wording to distinguish `rollout base` vs `verified application revision` vs `initial P3 evidence commit`
  - corrects `P3 branch c15d1ae -> new` to `f3885fd` and removes `Will be committed` stale phrasing
  - unifies rollout traffic to `API candidate 0% -> 10% -> 100%` and `ML generic 100/0 invariant`
  - clarifies 20 concurrent client pool timeouts vs server 5xx

## Rollout Evidence Commit

- Already committed as `f3885fd docs: record P3 public rollout` on `codex/p3-public-rollout` — this follow-up corrects provenance wording only, public traffic already at 100% P2 API
- None blocker after promotion; initial canary's generic `source null`/`region 200` were from old 90% stack, not candidate — candidate itself was correct, promotion fixed public path.

