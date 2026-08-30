# Cycle2 Phase1 Diagnostic Summary (baseline vs candidate-v2 reference on cycle2 dev)

**Status:** diagnostic_only, not_final_gate, no new candidate tuning, no holdout access, production untouched.
**Branch:** `codex/retrieval-v2-cycle2-candidate` at `5c5c5d933346a5a63e7878177bf15e0de46782eb` (dirty due to diagnostic runner/artifacts, record in artifacts)
**Dev:** `eval/retrieval-v2/cycle2/dev/evalset.jsonl` SHA `c8b66fef69bdfd0db053ac7cac0fb027fc3271c6072ab992b622cacdc71ace5e` (36 cases Youth 18/Gov24 18, 6 categories ×6)
**Model:** `intfloat/multilingual-e5-base`, `strip_region`, expired exclusion, `CANDIDATES=30`, `COSINE_MIN=0.78`, `LEXICAL_OVERLAP_BIAS=0.01`, youth bias suppressed for Gov24 orgs — D-003 parity verified.
**Candidate reference:** `retrieval-v2-candidate-v2` `5745cc3144b519da456b21030d0e0752d1d018ae` — only diff is `lexical_overlap_terms_rewrite` (particle-stripped stem, residue drop, MIN_STEM_LEN 2). Verified `qvec/DB/corpus/SQL/params` shared.

## A. Baseline (D-003) metrics on cycle2 dev

- `n=36` **R@1 0.5833 (21/36), R@5 0.7778 (28/36), R@10 0.8056 (29/36), MRR@10 0.6577, source-macro R@5 0.7778**
- `Youth R@5 0.5556 (10/18)`, `Gov24 R@5 1.0 (18/18)` — Gov24 perfect, Youth bottleneck
- by_category R@5: housing_finance 0.8333 (5/6), family_care 1.0 (6/6), employment_education 0.6667 (4/6), welfare_health 0.6667 (4/6), culture_community 0.6667 (4/6), business_agriculture 0.8333 (5/6)
- Artifact: `eval/retrieval-v2/cycle2/dev/baseline-d003-phase1.json` (git `5c5c5d9` dirty true, dev SHA pinned)

## B. Candidate-v2 reference (same qvec/DB/SQL)

- `R@1 0.5833 (21), R@5 0.8333 (30/36), R@10 0.8333 (30), MRR 0.6884, macro 0.8333`
- `Youth 0.6667 (12/18) +2`, `Gov24 1.0 (18/18) 0`, **net +2, losses 0**
- by_category deltas: culture_community 0.6667→0.8333 (+1, c2d-025), business_agriculture 0.8333→1.0 (+1, c2d-031), others unchanged
- Gains:
  - `c2d-025` 세종 청년센터: baseline rank 0 (rank_top30 14, score 0.868 >=0.78 threshold 통과, production top10 밖) → candidate rank 3 (rank_top30 3). `lex_b ['시에서','청년이','청년센터를',…]` overlap 0 → `lex_c ['청년','청년센터',…]` overlap 2. Vector-only rank 6 → **threshold가 아니라 ranking/top10 miss**로 재분류, lexical rewrite가 14→3으로 올린 사례. **Correction:** 기존 `filtered_by_cosine=true`는 오분류 — 정정 `filtered_by_cosine=false`, `outside_top10_after_threshold=true` (score>=0.78, rank_top30>10, rank==0, raw cosine `1-dist` >=0.78).
  - `c2d-031` 광주 청년 후계농업경영인: baseline rank 7 → candidate rank 2. Particles stripped `후계농업경영인이→후계농업경영인`, `영농정착지원금을→영농정착지원금` gave +1 bias-like overlap and vector rank 13→ improved.
- Losses: 0 (no regression, matches D-007 no regression property on dev)
- Artifact: `eval/retrieval-v2/cycle2/dev/phase1-paired-baseline-vs-candidate-v2.json`

Vector-only `R@5 0.75 (27/36)` < baseline, confirming lexical + youth bias together add value on this dev (+0.027 macro). Youth vector-only `10/18` = baseline Youth, Gov24 vector-only `17/18` vs baseline `18/18` (one Gov24 case needs lexical/youth to clear threshold).

## C. Failure diagnostic (only baseline misses matter; candidate misses are subset)

Baseline misses 8, all Youth (Gov24 0 miss). Persistent after candidate: 6, gains 2 fixed.

| case | cat | baseline rank/top30 | candidate rank/top30 | vector rank/top30 | threshold cause? | lexical cause? | vector cause? |
|---|---|---|---|---|---|---|---|
| c2d-003 부산 청년 월세 | housing | 0/0 null | 0/0 null | 0/0 null | no (not in 30) | 부산 stripped to `에`, both lex lack 부산; gold not retrieved lexically | **vector**: gold outside 30 among many 청년월세 variants; many near-duplicates rank higher (e.g., 20260409005400212654 score 0.88). Regional disambiguation fails after strip. |
| c2d-013 삼척 청년인턴 | employ | 0/0 null | 0/0 null | 0/0 | no | `삼척시에서→삼척시` candidate overlap 4 vs 0 but still outside 30; `삼척시` vs gold `삼척형` substring mismatch leaves effective overlap sensitive to exact admin form. | **vector**: gold far; competitor `행정 체험형 청년인턴` closer. |
| c2d-015 삼척 대학생 아르바이트 | employ | 0/0 | 0/0 | 0/0 | no | `대학생이→대학생`, `아르바이트를→아르바이트`; gold overlap 1→4 but still miss | **vector**: gold not in 30; query contains generic `프로그램이` noise, vector embedding buries gold among other 아르바이트 policies. |
| c2d-019 충남 청년 자살예방 | welfare | 0/0 | 0/0 | 0/0 | no | strip `에서` drops 충남; lex 0→2 but vector misses; gold title exactly matches many tokens yet vector rank 0 suggests embedding underrates `정신건강 검진` phrase? Yet candidate gold text overlap 2 should help but still outside 30. | **vector** dominant; lexical insufficient distance. |
| c2d-021 보호종료 청년 자립지원전담기관 | welfare | 0/0 | 0/0 | 0/0 | no | `청년이→청년`, `자립지원전담기관을→자립지원전담기관`, `사례관리를→사례관리`; gold overlap improves but still miss. | **vector**: very long composite entity `자립지원전담기관` rare; embedding may split; gold not in 30. |
| c2d-026 경기도 청년참여기구 | culture | 0/0 | 0/0 | 0/0 | no | `청년이→청년`, `청년참여기구를→청년참여기구`, `모니터링에→모니터링`; still miss. | **vector** |
| c2d-025 세종 청년센터 | culture | 0/14 outside_top10 (score 0.868 >=0.78, `filtered_by_cosine=false`, `outside_top10_after_threshold=true`) | 3/3 | 6/6 | **no** (threshold 통과: 0.868>=0.78, top30에 있으나 production top10 밖 ranking miss — 기존 `filtered` 오분류 정정) | **lexical**: `시에서` 등 noise 제거 + particle strip으로 rank 14→3 개선, score 자체는 동일 0.868으로 threshold 무관 |
| c2d-031 광주 청년 후계농업 | business | 7/7 | 2/2 | 0/13 | no threshold (in top30) | **lexical**: particle strip 7→2 | vector rank 13 shows vector alone worse than production |

**Decomposition pattern (corrected 2026-08-30: `filtered_by_cosine` 재계산, threshold cause 0건):**

1. **Threshold/top30**: 0 of 8 misses were threshold-induced (`score <0.78` → `filtered_by_cosine=true`는 baseline/candidate 모두 0건으로 재계산, artifact `phase1-paired-baseline-vs-candidate-v2.json`의 저장된 `rank_top30`/`rank`/`score`만으로 deterministic 정정). 1건(c2d-025)은 threshold 통과(score 0.868>=0.78)했으나 `outside_top10_after_threshold=true` (rank_top30 14, rank 0, raw cosine `1-dist` >=0.78)로 production top10 밖 ranking miss였고 candidate가 lexical로 3위까지 복구. 나머지 6 persistent misses는 **not in top30 at all**, so COSINE_MIN and top10 cutoff are innocent — root cause is **vector retrieval** not returning gold within 30, regardless of lexical. Only `c2d-031` was in top30 (7) and lexical moved it.

2. **Lexical terms/overlap**: Baseline lex includes noisy particles (`청년이`, `에서`, `을`, `를`, `시에서` generic) that dilute overlap count; candidate drops pure josa/admin residue and strips particles, reducing terms (e.g., 7→5, 5→4) and increasing true overlap (0→2,0→4). For 2 gains this mattered; for 6 persistent misses, candidate also increased gold overlap (0→4,1→4 etc.) but still not enough — indicating **lexical signal magnitude 0.01 per term** is too small to bridge vector gaps when gold is beyond 30. Competitors also benefit similarly from lexical, so relative gap stays.

3. **Raw vector rank**: 6 persistent misses have vector rank 0 and not in top30 — pure embedding failure. These queries are all **Youth + specific regional or compound-entity** (부산 월세 vs generic 월세, 삼척 vs other regions, 충남 정신건강, 보호종료 자립지원전담기관, 경기도 청년참여기구). Embedding likely over-weights generic `월세 지원`, `청년`, `인턴` and under-weights disambiguating tokens that were stripped or are rare compounds. Stripping region (`부산→에`) exacerbates for c2d-003; for others, region retained but compound variants (`삼척시` vs `삼척형`) still mismatch lexically and vectorially.

No case shows Gov24 miss, so youth-biased queries suffer disproportionately when youth intent is present but gold is region-specific or rare-entity.

**Hardcode prohibition**: No per-case exception; patterns are general.

## D. Latency diagnostic (NON-GATE, diagnostic_only=true)

- Fixed before run: `WARMUP_PER_VARIANT 18`, `ROUNDS 5`, `sample_count 180 per variant (360 total)`, seed `20260830`, order `(round+qi)%2` interleaved, timed scope = lexical_term generation + SQL execute/fetch + region_filter + COSINE_MIN filter (model/embedding excluded), same process/DB/qvec.
- Results (cycle2 dev 36 queries ×5):
  - baseline `p50 410.14 ms, p95 487.31 ms` (n=180)
  - candidate `p50 386.01 ms, p95 546.50 ms` (n=180)
  - delta `p50 -24.13 ms, p95 +59.18 ms` → **p95 FAIL** diagnostic impression (candidate slower), p50 PASS.
- Artifact: `eval/retrieval-v2/cycle2/dev/latency-diagnostic-phase1.json` with `diagnostic_only true, not_final_gate true`.
- This is NOT the final D-007 gate. Final gate will be re-measured on same holdout query set after candidate freeze, not dev.

## E. Reconcile / Safety

- Dev SHA verified `c8b66fef…` matches manifest, frozen_before_tuning true, retrieval_observed false.
- Holdout `eval/retrieval-v2/cycle2/holdout/` absent on candidate branch (verified `ls` no such directory, holdout branch is `codex/retrieval-v2-cycle2-holdout-freeze` at `9e2cd6ea...`).
- Production files `ml-service/app.py`, `source_ranking.py` diff 0 vs `372ed68` (verified `git diff --stat` only new diagnostic files).
- Cycle1 candidate reference commit `5745cc31…` local file identical to frozen (diff 0).
- Only `lexical_overlap_terms_rewrite` intended diff, confirmed `qvec/DB/corpus/SQL shared`.
- No candidate freeze, no tag created; commit provenance recorded with `git_commit 5c5c5d9` dirty true.

## F. Proposed next candidate directions (1–3, generalizable, not implemented)

**Option 1 — Region-aware lexical & embedding preservation (highest expected gain on persistent misses)**

- Evidence: `c2d-003` loses `부산` entirely after `strip_region` → `에`; `삼척` cases suffer `시/군` suffix variance. All 6 persistent misses are region or compound-entity specific; vector alone fails when disambiguating token is stripped or lexically strict.
- Direction: Keep a lightweight region signal for lexical/retrieval without reintroducing D-004-rejected public region search: e.g., preserve core region stem (부산, 삼척, 세종, 충남, 경기도) as an extra lexical term even after strip, or make lexical overlap use character 2-gram/substring not exact term equality to tolerate `삼척시` vs `삼척형`, `청년센터를` vs `청년센터`. Do **not** hardcode case IDs; generalize to suffix-stripped region core + n-gram fallback, still 0.01 bias compatible. Must verify latency: n-gram adds SQL ILIKE cost but possibly small; measure.

**Option 2 — Compound-entity aware lexical normalization (query side only, no DB mutation)**

- Evidence: `자립지원전담기관을→자립지원전담기관` already helps but gold `자립지원` variants still not bridged; `청년참여기구` etc. Baseline particles hide stems.
- Direction: Extend particle stripping to handle longer agglutinative tails (`으로`, `를`, `을`, `에서`) already done, but add **light compound split** for long nouns: e.g., `후계농업경영인` keep as is already, but `자립지원전담기관을` → `자립지원전담기관` is done; next step is to also consider decomposing very long entities into constituent morphemes for overlap (`자립`, `지원`, `전담`) — but must avoid over-fragmenting and latency blowup. Alternative: keep existing rewrite but increase lexical bias weight from 0.01 to 0.015–0.02 for Youth queries where vector is weak, or add secondary exact-phrase bonus for 2+ term co-occurrence. Any bias increase must be evaluated for hard-negative intrusion risk (currently 0). Recommend testing bias 0.015 with hard-negative check before final.

**Option 3 — Vector-failure fallback: modest candidate count expansion with latency budget**

- Evidence: 6 misses are outside top30 even with lexical. Lexical alone cannot rescue if vector rank >30. Increasing `CANDIDATES` 30→50 would include gold for some misses (check: for c2d-025 gold 14 needed 30 was enough but filtered; for others gold >30, might need >30). However D-003 fixes 30; changing it is not purely lexical and impacts latency (more DB work, higher p95). Cycle1 latency already HOLD at +4ms; dev diagnostic shows candidate `p95 +59ms` already regression, so count expansion likely worsens latency.
- Direction: Only if Options 1–2 insufficient: test `CANDIDATES 40` with same lexical rewrite on dev and measure p95 delta vs latency budget; accept only if p95 stays within ~10ms of baseline (D-007 requires `candidate p95 <= baseline p95`). Likely not viable given current latency regression, so defer unless Option1 shows that larger candidate set plus lexical still PASS quality.

**Recommendation ordering:** Try **Option 1** first (region core preservation + substring-tolerant lexical), as it directly addresses the strongest pattern (region loss + strict substring) and explains 4/6 persistent misses without increasing latency much; then evaluate Option 2 if still >2 misses remain.

---
Generated by `eval/retrieval_v2/run_cycle2_phase1_diagnostic.py` at 2026-08-30. Artifacts: `baseline-d003-phase1.json`, `phase1-paired-baseline-vs-candidate-v2.json`, `latency-diagnostic-phase1.json`.
