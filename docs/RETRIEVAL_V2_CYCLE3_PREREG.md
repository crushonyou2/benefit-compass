# Retrieval v2 Cycle3 — Pre-registration v1 (BOOTSTRAPPED)

> **Status:** BOOTSTRAPPED — spec frozen before any Cycle3 dev/holdout creation, before any retrieval/DB/model/embedding/benchmark execution, before any candidate implementation. No retrieval has been run in this cycle.
> **Branch:** `codex/retrieval-v2-cycle3-start` from `5cabd2eecd78923da4751c5e60fa316e74f563fc` (`codex/retrieval-v2-cycle2-candidate`)
> **Tag (bootstrap):** `retrieval-v2-cycle3-start-v1` (annotated, immutable) → this commit
> **Decision:** D-011 (2026-08-30, user-confirmed standing decision, Q-005 closed → D-011)
> **Contracts unchanged:** D-003 / D-004 / D-007 / D-008 / D-009 / D-010 — gate/threshold 완화 없음. Cycle1 HOLD 불변.
> **Max experiments:** 정확히 3개. dev 결과를 본 뒤 후보/파라미터/수치 추가·변경·재실행 금지.

This document + `eval/retrieval-v2/cycle3/prereg-v1.json` jointly constitute the Cycle3 pre-registration. Human-readable narrative here, machine-readable manifest in JSON. Conflicts → JSON is authoritative for candidate ids, K values, and selection predicates; this markdown is authoritative for SQL semantics description.

## 1. Purpose

Cycle1의 실제 blocker는 warm paired latency (`candidate p95 480.55 ms > baseline p95 476.51 ms`, D-008)였다. candidate-v2 계열(`lexical_overlap_terms_rewrite(strip_region(raw))`)의 lexical quality 이득은 확인됐으나, lexical CTE가 eligible 전체(≈13k policies)에 대해 `count(DISTINCT term)`를 계산하면서 SQL 비용이 컸다. Cycle3의 목적은 **warm paired latency를 직접 줄이면서 lexical quality 이득을 보존**하는 것이며, 그 유일한 탐색 경로는 **vector-distance 기반 bounded pre-pool 내에서만 lexical overlap을 계산하는 SQL 구조**로 한정한다.

## 2. Scope & prohibitions (D-004, D-011 compliance)

- **Embedding model:** `intfloat/multilingual-e5-base` — D-003 유지. 변경 없음.
- **Production contract retained:** `RERANK=0`, `CANDIDATES=30` (final), `COSINE_MIN=0.78`, `LEXICAL_BIAS=0.01`, `strip_region`, expired-policy exclusion, `youth_source_bias(strip_region(raw))` (Gov24 org query 시 0, youth intent 시 0.015) 모두 유지.
- **Public region search 없음** — `region`은 400, `rp` 바인딩은 항상 `NULL`. 하드코딩 검증은 runner/test에서 fail-closed.
- **Cross-encoder reranking 없음**, **global similarity/abstention threshold 없음** — D-004 준수.
- **No retrieval/DB/model/embedding/benchmark execution in this bootstrap.** Spec only.
- **No fresh dev/holdout plaintext generation or access in this bootstrap.** No existing cycle1/2 dev/holdout plaintext 열람.
- **No production/ml-service modification.** No existing eval result artifact modification.

## 3. Fresh data pre-registration (D-011 §4)

- **fresh dev 36** (Youth 18 / Gov24 18, 6-category balanced 6 each) — candidate tuning 전에 독립 생성·동결. P0 / cycle1 dev+holdout / cycle2 dev+disqualified holdout / hard-negative 및 서로 간 query+gold overlap 0을 fail-closed 검증. Holdout builder와 dev builder 세션은 candidate-tuning 세션과 분리.
- **fresh holdout 40** (Youth 20 / Gov24 20) — candidate tuning 전에 독립 생성·동결. 동일 overlap 0 검증.
- 두 세트는 서로 간 overlap 0. builder는 자신이 생성한 데이터의 fingerprint manifest만 기록하며, 과거 protected sets는 plaintext를 다시 열어 fingerprint를 새로 만들지 않고, 이미 안전하게 노출 가능한 aggregate/fingerprint 자료가 있을 때만 재사용하고 없으면 별도 isolated audit plan을 세운다.
- dev에서 선택된 **하나만 freeze** 가능. P0/hard-negative/final holdout 평가는 candidate freeze + independent review + user explicit approval 전까지 실행 금지.

## 4. Candidate search space — exactly 3 (pre-registered, immutable)

단일 canonical dev batch에서 baseline(D-003)과 함께 3 후보를 모두 평가. dev 결과를 본 뒤 후보/파라미터/수치 추가·변경·재실행 금지. 세 후보는 한 번의 canonical dev batch에서 baseline과 함께 모두 평가하도록 pre-register.

| candidate_id | base | lexical terms | youth bias | LEXICAL_BIAS | COSINE_MIN | RERANK | final CANDIDATES | variable |
|---|---|---|---|---|---|---|---|---|
| `c3e1-vector-pool-128` | candidate-v2 | `lexical_overlap_terms_rewrite(strip_region(raw))` | `youth_source_bias(strip_region(raw))` (suppressed for Gov24) | 0.01 | 0.78 | 0 | 30 | vector-pool K=128 |
| `c3e2-vector-pool-256` | candidate-v2 | 동일 | 동일 | 0.01 | 0.78 | 0 | 30 | K=256 |
| `c3e3-vector-pool-512` | candidate-v2 | 동일 | 동일 | 0.01 | 0.78 | 0 | 30 | K=512 |

- `strip_region`은 `ml-service/app.py:strip_region` (SIDO 키워드 제거) 그대로.
- `lexical_overlap_terms_rewrite`는 `eval/retrieval_v2/candidate_lexical_rewrite.py:lexical_overlap_terms_rewrite` (particle-stripped stem replacement, MIN_STEM_LEN 2, residue dropped) 그대로.
- region search 없음: `%(rp)s` 바인딩 항상 `NULL`, runner/test에서 `rp IS NULL` path만 허용.
- `LEXICAL_BIAS`, `COSINE_MIN`, `CANDIDATES` 등 수치 변경 없음.

### 4.1 Why only these three

Cycle2는 embedding 힌트(Exp2 earliest-alias, Exp3 semantic-core, Exp4 region-attached cleanup) 4개를 모두 REJECTED했으나 Web session recording으로 PROCESS_CONTAMINATED가 확정되어 탐색 완전성 주장은 무효다. Cycle3는 D-011 hygiene로 fresh dev+holdout에서만 판정하되, 탐색 차원을 **latency 병목 직접 해소**로 좁혀 **vector-pool** 단일 축으로 한정한다. K=128/256/512는 candidate-v2가 30개까지 lexical을 결합하던 기존 동작에서 128(aggressive), 256(moderate), 512(conservative) 세 점으로 latency-quality 트레이드오프를 사전에 고정하는 값이다.

## 5. SQL semantics (normative)

모든 후보가 준수해야 하는 정확한 SQL 구조를 below로 명시한다. 이 bootstrap에서는 구현/실행하지 않고 spec만 고정한다.

### 5.1 Invariants

- `%(age)s` / `%(rp)s` / `%(vec)s` / `%(lexical_terms)s` / `%(youth_bias)s` / `%(lexical_bias)s` 바인딩은 baseline과 동일 시그니처.
- Eligible 조건: `( %(age)s IS NULL OR p.age_limit_yn IS NOT TRUE OR %(age)s BETWEEN p.age_min AND p.age_max ) AND ( %(rp)s IS NULL OR EXISTS (SELECT 1 FROM unnest(p.region_codes) rc WHERE rc LIKE %(rp)s) ) AND ( p.biz_end IS NULL OR p.biz_end >= CURRENT_DATE )` — 만료 정책 제외 포함.
- Per-policy nearest chunk: `SELECT DISTINCT ON (p.id) ... FROM policy_chunk c JOIN policy p ON p.id=c.policy_id WHERE <eligible> ORDER BY p.id, c.embedding <=> %(vec)s::vector` — policy당 가장 가까운 chunk 1개.
- Vector-pool은 **오직 vector distance**로 정렬한 뒤 K개로 자른다. lexical 점수는 pool 결정에 관여하지 않는다.
- Lexical CTE는 **그 K policy에만** 계산한다. eligible 전체에 대한 lexical 계산 금지.
- 최종 순서는 기존과 동일: `ORDER BY t.dist - CASE WHEN t.source='youth' THEN %(youth_bias)s ELSE 0 END - %(lexical_bias)s * coalesce(l.lexical_overlap,0), t.dist, t.source, t.source_id` 후 `LIMIT %(n)s` where `n=30`.
- 최종 `CANDIDATES=30`은 변하지 않는다. pool K는 내부 pre-filter일 뿐 반환 개수는 30.

### 5.2 Canonical SQL template (normative, runner must match this structure)

```sql
WITH nearest AS (
  SELECT DISTINCT ON (p.id) p.id, p.source, p.source_id, p.title, p.org,
         p.support_content, p.apply_method, p.apply_url, p.age_min, p.age_max,
         p.income_etc, (c.embedding <=> %(vec)s::vector) AS dist
  FROM policy_chunk c
  JOIN policy p ON p.id = c.policy_id
  WHERE ( %(age)s IS NULL OR p.age_limit_yn IS NOT TRUE
          OR %(age)s BETWEEN p.age_min AND p.age_max )
    AND ( %(rp)s IS NULL
          OR EXISTS (SELECT 1 FROM unnest(p.region_codes) rc WHERE rc LIKE %(rp)s) )
    AND ( p.biz_end IS NULL OR p.biz_end >= CURRENT_DATE )
  ORDER BY p.id, c.embedding <=> %(vec)s::vector
),
vector_pool AS (
  SELECT * FROM nearest ORDER BY dist ASC LIMIT %(pool_k)s  -- K ∈ {128,256,512}
),
lexical AS (
  SELECT p.id, count(DISTINCT term) AS lexical_overlap
  FROM policy p
  JOIN vector_pool vp ON vp.id = p.id
  CROSS JOIN LATERAL unnest(%(lexical_terms)s::text[]) AS term
  WHERE concat_ws(' ', p.title, p.summary, p.support_content,
                  p.add_qualify, p.keywords)
        ILIKE '%%' || term || '%%'
  GROUP BY p.id
)
SELECT t.source, t.source_id, t.title, t.org, t.support_content, t.apply_method,
       t.apply_url, t.age_min, t.age_max, t.income_etc, 1 - t.dist AS score
FROM vector_pool t
LEFT JOIN lexical l ON l.id = t.id
ORDER BY t.dist - CASE WHEN t.source = 'youth' THEN %(youth_bias)s ELSE 0 END
             - %(lexical_bias)s * coalesce(l.lexical_overlap, 0),
         t.dist, t.source, t.source_id
LIMIT %(n)s  -- n=30
```

Notes:
- `%(pool_k)s` is runner-supplied `128 / 256 / 512` per candidate. `%(n)s` is always `30`.
- `vector_pool` already satisfies eligibility, so `lexical` does not need to re-apply age/rp/biz_end filters; joining `vector_pool` is the eligibility guarantee. An equivalent formulation that re-applies `WHERE (age...) AND (rp...) AND (biz_end...)` AND `p.id IN (SELECT id FROM vector_pool)` is also acceptable if byte-identical semantics.
- The `CROSS JOIN LATERAL unnest` + `ILIKE` + `count(DISTINCT term)` is the only lexical computation; no other lexical path.
- No `region_filter` in Python, no reranker, no threshold beyond `COSINE_MIN` post-filter (if applied) — D-004.
- Runner must assert `%(rp)s IS NULL` and `%(lexical_terms)s` derived from `lexical_overlap_terms_rewrite(strip_region(raw))`; any `rp` non-NULL or different lexical helper is fail-closed REJECT.

## 6. Evaluation protocol (single canonical dev batch)

- **Same fresh dev 36**에서 4-way paired: `baseline(D-003)`, `c3e1`, `c3e2`, `c3e3`를 동일한 DB/corpus/SQL/embedding 호출로 평가. corpus provenance(`total_policies/total_chunks`, gov24/youth split)는 4-way 동일해야 하고 production diff는 0이어야 fail-closed PASS.
- Timed sample count는 결과 보기 전에 고정 — D-007 latency 계약 준수.
- dev 결과를 본 뒤 후보/파라미터/수치 추가·변경·재실행 금지. 3 후보 중 dev-selectable이 하나도 없으면 Cycle3 candidate search는 holdout 평가 없이 종료.

## 7. Fresh dev selection rule (quality + latency, fail-closed)

각 후보는 **동일한 fresh dev 36**에서 아래를 **모두** 만족해야 `quality-selectable`:

1. `candidate source-macro Recall@5 > baseline source-macro Recall@5`
2. `candidate net hit@5 >= +2` (baseline 대비 gains - losses)
3. `Youth hit@5 regression 0` — candidate Youth hit@5 ≥ baseline Youth hit@5 (동일 dev, 동일 18 Youth cases)
4. `Gov24 hit@5 regression 0` — candidate Gov24 hit@5 ≥ baseline Gov24 hit@5 (동일 18 Gov24 cases)

`quality-selectable` 후보에 한해서만 **동일한 dev query set**으로 warm paired latency diagnostic을 실행. Timed methodology는 D-007과 동일: **same-process / same-DB / interleaved / warmup-excluded** 구조. Warmup 샘플은 timed에서 제외, cold/model-load 제외, timed sample count는 결과 inspection 전 고정.

Latency gate (diagnostic, dev-selectable 판정):

- `candidate p95 <= paired baseline p95` 를 만족해야 `DEV_SELECTABLE` (D-007 warm paired non-regression).

여러 후보가 `DEV_SELECTABLE`이면 사전등록 tie-break:

1. (a) higher `net hit@5` (baseline 대비)
2. (b) higher `source-macro Recall@5`
3. (c) lower `candidate - baseline p95 delta` (더 큰 latency 개선, 더 작은 delta)
4. (d) smaller `pre-pool K` (128 < 256 < 512)

하나도 `DEV_SELECTABLE`이 없으면 **Cycle3 candidate search closes without holdout evaluation.** dev에서 선택된 하나만 freeze 가능.

## 8. Holdout gating (D-011 §6-7, D-007 7 Gates)

- P0/hard-negative/final holdout 평가는 **candidate freeze + independent review + user explicit approval 전까지 실행 금지**.
- Freeze된 하나에 대해서만 fresh holdout 40에서 **추가 tuning 없이** D-007 7 mandatory gates를 평가: quality improvement / +2 net / no Youth regression / no Gov24 regression / P0 PASS / hard-negative PASS / warm paired latency non-regression / holdout integrity (overlap 0).
- GO는 7 gates 모두 PASS일 때만. fixable mandatory failure는 HOLD, clear quality regression은 NO-GO.

## 9. Audit log & fingerprint (infrastructure only in bootstrap)

- Cycle3부터 retrieval 실행 및 protected-set 접근은 `eval/retrieval_v2/cycle3_audit.py`의 append-only JSONL event log로 durable 기록. Schema: `schema_version`, `event_id` (UUID v4), `utc_timestamp` (ISO8601 Z), `git_head`, `git_dirty` (bool), `process_id`/`session_id`, `action` (`run_start`/`run_end`/`protected_access_start`/`protected_access_end`), `candidate_id`, `set_role` (`dev`/`holdout`/`none`), `set_sha`, `command`/`runner_id`, `outcome`, `previous_event_hash`, `event_hash`. chain 위반 또는 truncate/overwrite 시 fail-closed. next builders는 retrieval/access 전에 audit event append 성공을 선행해야 함.
- Protected-set overlap 검증은 `eval/retrieval_v2/cycle3_fingerprint.py`의 deterministic fingerprint로 holdout plaintext를 다시 열지 않고 수행: `SHA256(normalized query)` + `SHA256(source + NUL + source_id)`. manifest에 `query_fingerprints`/`gold_fingerprints`를 저장하고, 두 manifest는 pure helper로 overlap 0을 fail-closed 검사. 실제 fresh dev/holdout data는 bootstrap에서 생성하지 않으며, 기존 cycle1/2 protected plaintext를 읽어 fingerprint를 새로 만들지도 않는다. 다음 builders는 자신이 생성하는 데이터의 fingerprint만 기록하고, 과거 sets는 안전하게 노출 가능한 aggregate/fingerprint 자료가 존재할 때만 재사용하고 없으면 별도 isolated audit plan을 세운다.

## 10. Provenance & versioning

- `prereg_version: v1`, `schema_version: 1`, `base_commit: 5cabd2eecd78923da4751c5e60fa316e74f563fc`, `base_branch: codex/retrieval-v2-cycle2-candidate`, `bootstrap_branch: codex/retrieval-v2-cycle3-start`, `bootstrap_tag: retrieval-v2-cycle3-start-v1`.
- 이 문서는 `retrieval-v2-cycle3-start-v1` 태그에서 고정된다. 이후 어떤 사유로든 pre-reg 추가·변경·재실행은 허용되지 않으며, 필요 시 별도 cycle로 분리한다.

## 11. Change log

- v1 (2026-08-30): initial bootstrap pre-registration. 3 candidates fixed, SQL semantics normative, dev selection + latency + tie-break fixed, warm paired methodology D-007, P0/holdout gating, audit/fingerprint spec.
