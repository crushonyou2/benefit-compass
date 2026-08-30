# Retrieval v2 Cycle2 PROCESS AUDIT — durable evidence only (read-only)

> **Scope:** Web이 Exp2~Exp4 작업 중 Paseo 완료 전에 여러 차례 중간 검증/steering/프로세스 중단을 수행하여 candidate-search 신뢰도가 훼손됐을 가능성을, **durable repo 증거만으로** 독립 감사. canonical 숫자를 재실행하거나 무효화하지 않고, 증명되는 범위와 증명되지 않는 범위를 분리.
> **HARD GATE:** `Muse Spark 1.2 Contributor / 매우 높음(xhigh)` — 본 세션 시작 시 verified. 아니면 즉시 중단 보고해야 하나 통과.
> **금지 준수:** retrieval/DB/model/embedding/benchmark/holdout plaintext/`git show` holdout/`checkout` holdout/final holdout 실행 전부 금지. production/ml-service, frozen dev/holdout, eval artifact 재생성/수정 금지. 본 감사는 기존 artifact/runner/docs/memory/Git metadata read-only 감사만 수행.

**감사 기준:** `codex/retrieval-v2-cycle2-candidate` branch, reconciled HEAD `3caa6729efd5437994afa7ab5392ad8bb5227eb3` at 2026-08-30, `local == origin == actual remote (https://github.com/crushonyou2/benefit-compass.git)`, `git status --porcelain` clean, `git diff --check` PASS. 모든 SHA/경로는 LF normalized 기준.

**감사 일자:** 2026-08-30 (Asia/Seoul). **감사 주체:** Paseo (independent read-only audit). **결재 전 Web 교차검증 대기.**

---

## 0. 방법론과 한계 (증거 분리 원칙)

- **durable evidence로 간주:** `git log`/`git show`로 재현 가능한 commit/tag/object, `eval/retrieval-v2/cycle2/`에 커밋된 artifact JSON/MD의 `git_commit`/`git_dirty`/`diagnostic_only`/`not_final_gate`/`dev_sha`/`corpus`/`per_case` 필드, `memory/DECISIONS.md`·`docs/RETRIEVAL_V2.md`·`memory/SESSION-LOG.md`에 기록된 aggregate-only 서술, `evalset.jsonl`/`manifest.json`의 LF SHA256.
- **durable evidence로 간주하지 않음:** Web 브라우저에서 수행된 read-only preflight, 화면에 표시된 중간 검증, 구두 steering, 프로세스 중단 여부, Paseo 세션 이전 메모리상의 `git show` 호출 횟수 — 이들은 commit/tag로 남지 않으면 repo만으로는 증명 불가. 본 감사는 이들을 `UNKNOWN / NOT PROVABLE (durable repo alone)`로 분류.
- **용어 정정 (전역):** 기존 문서·SESSION-LOG의 “single execution at <commit> dirty” 표현은, repo가 프로세스 실행 1회를 증명하지 못하므로 **`canonical accepted execution 1회`** — 즉 해당 commit에 canonical으로 채택·커밋된 artifact가 1개 존재한다는 뜻으로만 해석한다. 실행 카운터, run log, append-only counter가 repo에 없으므로 “프로세스가 정확히 1회만 실행됐다”는 주장은 durable 증거 없음.

**Evidence status 정의:**

| status | 의미 |
|---|---|
| `VALID_CANONICAL_RESULT` | 수치 자체가 fail-closed sanity를 통과하고, dev SHA·corpus·production diff 일치가 durable로 검증되며, holdout 오염 없이 diagnostic_only로 보존된 REJECTED/PASS. 이 실험의 수치 결론은 기술적으로 유효. |
| `VALID_RESULT_PROCESS_CONTAMINATED` | 수치는 기술적으로 유효하나, 인간-in-the-loop steering/selection bias 등 프로세스 오염이 durable로 확인돼, 그 수치를 근거로 한 “충분히 탐색했다” 같은 상위 결론은 무효. |
| `INVALID_FOR_SELECTION` | 해당 set/artifact가 final gate evidence로 사용 금지 (D-010 holdout 등). |
| `UNKNOWN` | durable repo만으로는 판정 불가. |

---

## 1. Phase1 — Diagnostic baseline vs candidate-v2 on frozen dev 36

| 항목 | 내용 |
|---|---|
| **(a) canonical artifact/commit/ref** | Commit `6d743bb366530cb34d03a3efd0a7860e221421c5` (candidate `5c5c5d933...` dirty True) + correction `c2dfd87bf6602e78bef5ecbc09d297bfbf2a6f74`. Artifacts: `eval/retrieval-v2/cycle2/dev/phase1-paired-baseline-vs-candidate-v2.json` (`diagnostic_only true, not_final_gate true, git_commit 5c5c5d9 dirty True, dev SHA `c8b66fef69bdfd0db053ac7cac0fb027fc3271c6072ab992b622cacdc71ace5e`, `qvec/DB/corpus/SQL shared, youth_intent_bias 0.015`), `baseline-d003-phase1.json`, `latency-diagnostic-phase1.json`, `phase1-summary.md`. Dev freeze `retrieval-v2-cycle2-dev-v1` `500beadae11ddb423cc2ea4d46494c0a9f2b1173` → `372ed686579b4e8e2b9854d297e44fee18775352`, holdout absent on candidate branch. |
| **(b) 최종 metric 재현성·fail-closed sanity** | **PASS.** Baseline R@5 `28/36` (Youth 10/18 Gov24 18/18, R@1 21/36 R@10 29/36 MRR 0.6577 macro 0.7778), candidate-v2 R@5 `30/36` (Youth 12/18 Gov24 18/18, R@1 21/36 R@10 30/36 MRR 0.6884 macro 0.8333), net +2 gains `c2d-025` `c2d-031` loss0. 수치는 이후 Exp1~Exp4의 fail-closed assert (`baseline 28, candidate 30, Gov24 18/18`, dev SHA `c8b66fef…`, corpus `13589/17609`, production diff 0)와 전 구간 일치하여 재현성 확보. Latency `baseline p95 487.31ms vs candidate 546.50ms (Δ+59.18ms) n=180/variant`는 `diagnostic_only` 표기, final D-007 gate 아님. |
| **(c) known premature/noncanonical execution 증거 (durable)** | **없음 → UNKNOWN / NOT PROVABLE.** Repo에 canonical accepted artifact 1개만 존재. `git_dirty True`는 runner가 untracked 상태에서 실행됐음을 보일 뿐, 실행 횟수(1회 vs n회)나 Web의 중간 검증 여부를 증명하지 못함. `git log --follow`상 해당 JSON은 1개 버전만 커밋됨. |
| **(d) 결과를 본 뒤 코드 변경 가능성 (repo만으로)** | **증명됨 — correction은 결과 관찰 후 메타데이터 정정.** `c2dfd87`은 저장된 `rank_top30/rank/score`로 `filtered_by_cosine`을 threshold-only로 재계산하고 `outside_top10_after_threshold`를 추가. 품질/랭크/지연 수치는 불변, 재실행 없음이 commit diff로 증명됨. 이는 후보 튜닝이 아닌 진단 재해석이며, Phase1의 진단적 성격을 바꾸지 않음. |
| **(e) evidence status** | **`VALID_CANONICAL_RESULT` (diagnostic reference).** D-003 parity, dev SHA 고정, production diff 0, holdout 미접근. Latency는 `NOT_FINAL_GATE`로 분리 관리. |
| **(f) 안전하게 결론 / 결론내면 안 되는 것** | ✅ 안전: frozen dev 36에서 D-003 baseline vs candidate-v2의 품질 차이(+2, loss0, Gov24 perfect, Youth 병목 6 persistent misses)는 기술적으로 유효한 진단. 6 persistent miss의 원인 분해(threshold 0건, vector top30 밖)는 후속 Exp 설계의 근거로 사용 가능. ❌ 불가: 이 진단만으로 “candidate-v2가 최적” 또는 “Phase1 latency가 final gate 실패”를 결론내면 안 됨 — Phase1 latency는 `diagnostic_only`이며 final D-007 gate는 fresh paired holdout 측정으로만 판정. 또한 “단 1회 실행됐다”는 프로세스 횟수 단정은 repo만으로는 불가. |

---

## 2. Exp1 — Bounded region-core lexical hint (lexical-only)

| 항목 | 내용 |
|---|---|
| **(a) canonical artifact/commit/ref** | Commit `22d6e6c32b9a443d963d2db67698e779ec07a42d` (dirty True, `git_commit c2dfd87`) + 후속 메타패치 `53bd190cd716cce8a81a1ff3979483098f78471d` (docs sync, `youth_intent_bias 0.01 → 0.015` deterministic patch, 품질/랭크 불변). Artifacts: `eval/retrieval-v2/cycle2/phase2-exp1-region-hint/phase2-exp1-paired.json` (`diagnostic_only true, not_final_gate true, dev SHA c8b66fef…, corpus 13589/17609, qvec/DB/corpus/SQL shared, region hinted 23/36 avg 1.0 max1 canonical `SIDO[code][0]`), `phase2-exp1-summary.md`, runner `candidate_region_hint.py` / `run_cycle2_phase2_exp1_region_hint.py`. |
| **(b) 최종 metric 재현성·fail-closed sanity** | **PASS.** Baseline 28/36, candidate-v2 30/36, new 30/36 (R@1 22/36 vs 21/36, MRR 0.7069 vs 0.6884), Youth 12/18 Gov24 18/18, baseline vs new net +2 (이미 candidate에 포함된 `c2d-025` `c2d-031`), candidate vs new net 0 loss0, `new 30 not >30` → REJECTED, latency `NOT_RUN_EARLY_STOP`. 수치는 Phase1 및 후속 Exp의 fail-closed 기준과 일치. `53bd190` 패치는 `phase2-exp1-paired.json`의 `production_contract.youth_intent_bias` 필드만 정정하고 per_case rank/score를 바꾸지 않음이 diff로 검증됨. |
| **(c) known premature/noncanonical execution 증거 (durable)** | **없음 → UNKNOWN / NOT PROVABLE.** Canonical accepted artifact 1개만 repo에 존재. `git_dirty True` 외 실행 횟수 증거 없음. Web의 중간 검증/steering이 있었는지는 read-only 행위이므로 durable에 남지 않음. `53bd190`의 docs 패치는 사전에 합의된 D-003 parity 정정으로, 후보 탐색을 위한 사전 검증이 아님. |
| **(d) 결과를 본 뒤 코드 변경 가능성 (repo만으로)** | **부분 증명 — 메타데이터 패치는 결과 관찰 후 발생, 재실행 없이 일어난 것이 diff로 증명됨.** 그러나 lexical/embedding 로직 변경은 Exp1 커밋 이전에 고정됐고, Exp1 결과를 근거로 한 추가 튜닝(재실행)은 repo에 없음. 따라서 “결과를 보고 후보를 고쳐 재실행했다”는 durable 증거 없음. |
| **(e) evidence status** | **`VALID_CANONICAL_RESULT`.** REJECTED verdict는 기술적으로 유효하고, final holdout과 무관한 dev-only 실험이므로 selection bias로 무효화할 근거 없음. |
| **(f) 안전하게 결론 / 결론내면 안 되는 것** | ✅ 안전: bounded lexical hint(1 SIDO canonical/code, 23/36 hinted)만으로는 `30→>30` 개선이 없으며, 6 persistent Youth miss는 vector top30 밖이어서 lexical 0.01만으로는 구제 불가 — 이 한 후보군은 REJECTED가 정당. ❌ 불가: “lexical hint 전체가 무의미” 또는 “다른 lexical 변형도 모두 실패”를 일반화하면 안 됨 — Exp1이 테스트한 것은 정확히 1개 bounded 설계일 뿐, 탐색 공간을 소진했다는 결론은 불가. “single execution” 횟수 단정도 불가. |

---

## 3. Exp2 — Embedding preserves at most one SIDO via earliest alias (lexical unchanged)

| 항목 | 내용 |
|---|---|
| **(a) canonical artifact/commit/ref** | Commit `b1faabec2a0210070f565a918c18d3c4d762f37e` (dirty True, `git_commit 53bd190cd716cce8a81a1ff3979483098f78471d`). Artifacts: `eval/retrieval-v2/cycle2/phase2-exp2-embedding-region/phase2-exp2-paired.json` (`diagnostic_only true, not_final_gate true, dev SHA c8b66fef…, model intfloat/multilingual-e5-base, lexical identical to candidate-v2, embedding `strip_region(raw)+at most one SIDO[code][0] via earliest alias tie code sort`, per_case `new.selected_sido_code` 기록, `rank_top30`은 vector 효과만의 차이로 명시, `vector_only` 2×/case 제거), `phase2-exp2-summary.md`, runner `candidate_embedding_region_hint.py` / `run_cycle2_phase2_exp2_embedding_region.py`, test `test_retrieval_v2_cycle2_phase2_embedding_region.py` (fail-closed `baseline 28/30, Gov24 18/18` assert). |
| **(b) 최종 metric 재현성·fail-closed sanity** | **PASS.** Baseline R@1 21/36 R@5 28/36 R@10 29/36 MRR 0.6577, candidate-v2 21/30/30 MRR 0.6884, new R@1 25/36 R@5 30/36 R@10 30/36 MRR 0.7509 macro 0.8333, Youth12/Gov24 18, baseline vs new net +2 (c2d-025/031) loss0, candidate vs new net 0 loss0, `new 30 not >=31` → REJECTED, latency `NOT_RUN_EARLY_STOP`. Runner가 quality 산출 직후 `assert baseline 28/36, candidate 30/36, Gov24 18/18`을 통과한 것이 SESSION-LOG와 artifact `code_diff_verification.production_diff_zero true`로 기록됨. 이후 Exp3/Exp4도 동일 baseline/candidate를 재확인하여 수치 일관성 확보. |
| **(c) known premature/noncanonical execution 증거 (durable)** | **없음 → UNKNOWN / NOT PROVABLE (durable repo alone).** Repo는 canonical accepted artifact 1개만 보존. `git_dirty True` 외 실행 카운터 없음. Web이 Paseo 완료 전에 중간 검증을 했는지는 read-only 행위이므로 commit/tag에 남지 않음. 본 감사 범위는 Web read-only preflight를 금지하므로, 그 행위의 부재/존재를 repo만으로 증명할 수 없음. Durable에 남은 유일한 process interruption은 Exp2 이후의 docs sync `53bd190`(youth bias 패치)이며, 이는 Exp2와 무관한 문서 정정임. |
| **(d) 결과를 본 뒤 코드 변경 가능성 (repo만으로)** | **판정 불가 (UNKNOWN) in durable, but no evidence of post-result retune.** `b1faabe` 이전의 `53bd190` 커밋에 Exp2 runner 3파일은 untracked로 존재했고, `b1faabe`에서 처음 커밋됨. Exp2 결과를 본 뒤 동일 Exp2를 고쳐 재실행한 durable 흔적 없음. 다만 Exp2 결과를 보고 Exp3 설계를 steered했는지는 인간 설계 판단으로, repo diff만으로는 “steering이 있었다/없었다”를 증명 불가 — 설계가 Phase1 제안 Option1의 연장인지, dev 관찰 후 즉석 수정인지는 commit message만으로 구분 불가. |
| **(e) evidence status** | **`VALID_CANONICAL_RESULT` (수치 결론), 상위 “충분히 탐색했다” 결론에 대해서는 `UNKNOWN` (process 오염 durable 미증명).** 수치 자체는 dev SHA·corpus·fail-closed·production diff 0으로 유효. 그러나 “이 1개 embedding hint가 지역 힌트 공간을 대표한다”거나 “더 좋은 지역 힌트가 없다”는 탐색 완전성 주장은, repo만으로는 증명되지 않으며 Web steering 가능성을 배제할 수 없으므로 성립하지 않음. 본 표의 status는 수치 유효성에 한정하고, 프로세스 신뢰도는 §5에서 별도 분리 서술. |
| **(f) 안전하게 결론 / 결론내면 안 되는 것** | ✅ 안전: “earliest-alias 1 SIDO를 embedding에 붙이는 이 1개 설계는 `R@5 30→30`으로 candidate-v2 대비 개선 없음, R@1/MRR만 개선” — 이 후보는 REJECTED가 정당. ✅ 안전: lexical identical 조건에서 `rank_top30` 차이가 순수 embedding 효과임이 per_case로 기록됨. ❌ 불가: “embedding에 지역 힌트를 주는 모든 방법은 무의미” 또는 “Exp2가 지역 힌트 탐색을 소진했다” — Exp2는 1개 deterministic hint(earliest occurrence, tie code sort)만 테스트. ❌ 불가: “프로세스가 정확히 1회 실행됐다” — repo는 canonical accepted 1회를 증명할 뿐. ❌ 불가: “Web steering이 없었다” — durable 증거 없음. |

---

## 4. Exp3 — Semantic-core embedding (`" ".join(lexical_overlap_terms_rewrite(strip_region))` or fallback, lexical identical)

| 항목 | 내용 |
|---|---|
| **(a) canonical artifact/commit/ref** | Commit `3fdb06c541a3ef092b84fe23e0f96658c7865af8` (dirty True, `git_commit 44ce287d615a6131be2a2e1fd2f44d48287e0645` — HARD SEAL repair 후 clean baseline). Artifacts: `eval/retrieval-v2/cycle2/phase2-exp3-semantic-core/phase2-exp3-paired.json` (`diagnostic_only true, not_final_gate true, dev SHA c8b66fef…, corpus 13589/17609, candidate_config `semantic-core` = join rewrite terms or fallback stripped, lexical identical to candidate-v2, `single_encode_single_retrieval_per_variant` = 1 encode+1 retrieval/variant, `_fetch_cands` raw 30 반환 후 `rank_top30`은 raw, `rank@k`는 COSINE_MIN postfilter 후 계산 — Phase1/Exp2와 동일, 36×3 per_case 전체 기록), `phase2-exp3-summary.md`, runner `candidate_semantic_core.py` / `run_cycle2_phase2_exp3_semantic_core.py`, test `test_retrieval_v2_cycle2_phase2_semantic_core.py` 8 passed. Web confirmation 별도 `13ba60c8872c6225dcaa8335293dd8c422083853` docs-only. |
| **(b) 최종 metric 재현성·fail-closed sanity** | **PASS.** Baseline 21/28/29 MRR 0.6577, candidate-v2 21/30/30 MRR 0.6884, new R@1 23/36 R@5 30/36 R@10 30/36 MRR 0.7116 macro 0.8333, Youth12/Gov24 18, baseline vs new net +2 (c2d-025/031) loss0, candidate vs new net 0 loss0, `new 30 not >=31` → REJECTED, latency `NOT_RUN_EARLY_STOP`. Fail-closed `dev SHA c8b66fef…` 및 `baseline 28 Youth10 Gov24 18 / candidate 30 Youth12 Gov24 18` 통과가 SESSION-LOG와 `git_commit 44ce287 dirty True`로 기록. Runner는 `_fetch_cands`가 filtered list가 아닌 raw 30을 반환하도록 사전 보정된 뒤 실행됨이 SESSION-LOG에 명시. `HOLDOUT opt-in off` (`RETRIEVAL_V2_ALLOW_HOLDOUT_PLAINTEXT_AUDIT` unset, `git show` 0회) 유지가 검증됨 (`pytest ... 18 passed 5 skipped, git show 0`). |
| **(c) known premature/noncanonical execution 증거 (durable)** | **없음 → UNKNOWN / NOT PROVABLE for Web intermediate steering. 다만 process-level 오염은 1건 durable로 확인:** Exp3 직전 `44ce287`은 post-tuning candidate session에서 `_load_holdout_items()`가 고정 ref `git show`로 holdout plaintext를 process 메모리에 읽은 HARD SEAL 위반을 repair한 commit. 이 위반은 **Exp3 retrieval 이전, diagnostic 0회 상태에서 발생**하며 `stdout`/agent-visible 노출·retrieval/rank/score 0으로 기록됨. 그러나 D-010에 따라 이 위반 자체는 holdout을 `INVALID_FOR_SELECTION`으로 만든다. Exp3의 dev 수치가 이 holdout read에 오염됐다는 durable 증거는 없음 — Exp3는 holdout 미접근으로 실행됨. Web이 Exp3 Paseo 완료 전 중간 검증을 했는지는 repo만으로는 증명 불가. |
| **(d) 결과를 본 뒤 코드 변경 가능성 (repo만으로)** | **Exp3 내부 재실행 증거 없음.** Runner의 `_fetch_cands` 보정은 실행 직전 1곳 수정으로 기록됐으나, 품질/랭크를 바꾸는 튜닝이 아니라 raw vs filtered `rank_top30` 정의 정정이며 재실행 없이 artifact를 오염시키지 않음이 diff로 증명. Exp3 결과를 본 뒤 Exp3 자체를 고쳐 재실행한 흔적 없음. Exp3 결과를 보고 Exp4 설계를 바꾼 것은 인간 설계 판단으로 repo만으로 steering vs 사전 계획 구분 불가. |
| **(e) evidence status** | **`VALID_CANONICAL_RESULT` (dev 수치).** Exp3는 dev-only, holdout 미접근, fail-closed 통과, dev SHA·corpus·production diff 0으로 수치 유효. Holdout 오염은 Exp3 수치의 유효성을 무효화하지 않으나, holdout 자체는 D-010에 따라 `INVALID_FOR_SELECTION`. 프로세스 레벨에서는 `44ce287` 위반이 durable로 확인되므로, Cycle2 전체의 최종 평가 프로세스는 `VALID_RESULT_PROCESS_CONTAMINATED` 관점에서 봐야 하나, Exp3 dev 수치 단독으로는 `VALID_CANONICAL_RESULT`. |
| **(f) 안전하게 결론 / 결론내면 안 되는 것** | ✅ 안전: “semantic-core embedding 이 1개 설계는 `30→30`으로 개선 없음, R@1 23→21·MRR 0.7116→0.6884 소폭 상승” — REJECTED 정당. ✅ 안전: persistent miss 6개가 모두 candidate/new `raw top30 0→0` (postfilter 전 동일)으로, lexical 이전의 vector top30 밖임이 per_case `rank_top30`으로 증명됨. ❌ 불가: “시맨틱 코어를 쓰는 모든 방법 무효” 일반화 불가 — 1개 구현만 테스트. ❌ 불가: “Web이 중간에 결과를 보지 않았다” 또는 “봤다” — durable 증거 없음. ❌ 불가: “holdout이 오염됐으므로 dev도 오염” — dev는 holdout과 독립적으로 증명됨. |

---

## 5. Exp4 — Region-attached residue cleanup embedding (`cleanup_embedding_query`, lexical identical to candidate-v2)

| 항목 | 내용 |
|---|---|
| **(a) canonical artifact/commit/ref** | Commit `85b92efa52264c1878279746cf825043cca9cc4d` (dirty True, `git_commit beb9828a69432477c0cb22b8d776fc800a90dbfe` — D-010 기록 커밋). Artifacts: `eval/retrieval-v2/cycle2/phase2-exp4-region-attached/phase2-exp4-paired.json` (`diagnostic_only true, not_final_gate true, dev SHA c8b66fef…, model intfloat/multilingual-e5-base, production_contract CANDIDATES 30 COSINE_MIN 0.78 LEXICAL_BIAS 0.01 RERANK 0, candidate_config `cleanup_embedding_query` = alias+suffix(max1 longest)+particle(max1 longest) directly attached cleanup with fallback `strip_region(raw)`, lexical identical to candidate-v2, per_case 36×3 variants, `cleanup_applied 23/36, embedding_changed 8/36, corpus 13589/17609`), `phase2-exp4-summary.md`, runner `candidate_region_attached_cleanup.py` / `run_cycle2_phase2_exp4_region_attached.py`, test `test_retrieval_v2_cycle2_phase2_region_attached.py` 19 passed. 최종 reconcile `3caa6729efd5437994afa7ab5392ad8bb5227eb3`에서 `candidate branch current`를 `85b92ef`로 정정. |
| **(b) 최종 metric 재현성·fail-closed sanity** | **PASS.** Baseline 21/28/29 MRR 0.6577, candidate-v2 21/30/30 MRR 0.6884, new 21/30/30 MRR 0.6884 macro 0.8333, Youth12/Gov24 18, baseline vs new net +2 (c2d-025/031) loss0, candidate vs new net 0 loss0, `new 30 not >=31` → REJECTED, latency `NOT_RUN_EARLY_STOP`, `embedding_changed_vs_candidate 8/36` 실제 qvec 변경 있음에도 품질 동일. Fail-closed `baseline 28/30 Youth10/12 Gov24 18` 통과, `HOLDOUT opt-in off` (`RETRIEVAL_V2_ALLOW_HOLDOUT_PLAINTEXT_AUDIT` null, holdout dir absent, `git show` 0, tag/freeze 금지 준수) 및 `production diff 0` 검증됨. |
| **(c) known premature/noncanonical execution 증거 (durable)** | **없음 → UNKNOWN / NOT PROVABLE for Web intermediate steering. Durable에 남은 것은 2건의 Web/docs-only 개입뿐:** (1) `beb9828` D-010 standing decision 기록 (Exp3 후, Exp4 전) — candidate-search를 Exp4로 bounded함을 선언한 결정. (2) `3caa672` reconcile (Exp4 후) — stale HEAD `13ba60c→85b92ef` 정정 및 Next state D-010 원문 정합. 이들은 후보 탐색을 중단/경계짓는 결정/문서 행위로, 특정 Exp의 수치를 바꾸는 재실행은 아니나, **Process가 Web 판단에 의해 중단·경계지어졌음을 durable로 증명.** Exp4 실행 자체가 Web 중간 검증 후 Paseo가 재실행한 것인지는 repo만으로는 증명 불가 — canonical accepted artifact 1개만 존재. |
| **(d) 결과를 본 뒤 코드 변경 가능성 (repo만으로)** | **없음 (durable).** Exp4 runner는 `beb9828` dirty baseline에서 untracked로 존재하다 `85b92ef`에서 처음 커밋됨. Exp4 결과를 본 뒤 동일 Exp4를 고쳐 재실행한 흔적 없음. Exp4 REJECTED 이후 Cycle2는 D-010에 따라 CLOSED되어 추가 Exp 없이 종료됨이 `85b92ef`와 `3caa672`로 증명. |
| **(e) evidence status** | **`VALID_CANONICAL_RESULT` (수치), Cycle2 bounded 종료는 `D-010`에 따른 정당 종료.** Exp4 수치 자체는 fail-closed·dev SHA·corpus·holdout 미접근으로 유효. 프로세스 레벨에서는 D-010 bounded가 Web/user 확정으로 durable하므로, “Exp4 이후 추가 탐색을 하지 않은 것은 D-010을 따른 것”임이 증명됨. 그러나 “Exp4까지가 충분히 좋은 탐색이었다”는 완전성 주장은, durable이 4개 후보만 보존하므로 성립하지 않음 — status를 `VALID_RESULT_PROCESS_CONTAMINATED`로 격상할 only durable trigger는 holdout 위반(44ce287)이지만, dev 수치 자체를 contaminated로 격상할 근거 없음. |
| **(f) 안전하게 결론 / 결론내면 안 되는 것** | ✅ 안전: “region-attached residue cleanup 이 1개 설계는 8/36 qvec 변경에도 `30→30`으로 개선 없음” — REJECTED 정당, Cycle2 CLOSED 정당 (D-010 bounded). ✅ 안전: Exp4가 D-010의 마지막 bounded experiment였고, REJECTED로 Cycle2는 candidate fixation 없이 종료 — 추가 Exp 없음. ❌ 불가: “지역 잔류물 정리를 쓰는 모든 방법 무효” 일반화 불가. ❌ 불가: “4개 Exp가 Cycle2 탐색 공간을 소진했다” — 4개는 D-010이 정한 경계일 뿐, 소진 증명 아님. ❌ 불가: “Web이 Exp4 전에 중간 검증을 하지 않았다/했다” — durable 증거 없음. |

---

## 6. 종합 결론 — 4개 질문에 대한 엄격 분리 답

### 6.1 최종 28/30/30 등의 canonical metric 자체가 기술적으로 오염됐다는 증거가 있는가

**없음 (NO — durable evidence of technical contamination of the canonical dev metrics: none).**

- Phase1 28→30, Exp1~Exp4 new 30/36, Gov24 18/18, loss0, R@1/MRR 등 모든 수치는 `dev SHA c8b66fef69bdfd0db053ac7cac0fb027fc3271c6072ab992b622cacdc71ace5e` 고정, corpus `13589/17609` 고정, `ml-service/app.py`·`source_ranking.py` diff 0, `diagnostic_only`·`not_final_gate` 일관 표기, Exp2~Exp4 fail-closed assert 통과로 durable 검증됨. 재실행 없이 메타데이터만 패치한 `c2dfd87`/`53bd190`도 diff로 품질 영향 없음이 증명.
- 유일한 durable 오염은 `44ce287`의 post-tuning holdout plaintext `git show` (process-level read, 화면 노출 0, Exp3 이전). 이는 **holdout `retrieval-v2-cycle2-holdout-v1` (SHA `cf003bab…`, `03da4cc→9e2cd6e`)를 `INVALID_FOR_SELECTION`으로 만들 뿐**, dev 36의 retrieval/rank/score를 바꾸지 않음. Exp3/Exp4는 `HOLDOUT opt-in off, git show 0`으로 실행됨이 검증됨.
- 따라서 “28/30/30이 잘못 측정됐다/조작됐다”는 기술적 오염 주장은 durable 증거 없음. 이 수치들을 근거로 한 각 실험의 **REJECTED 판정 자체는 유효**.

### 6.2 “Cycle2에서 충분히 좋은 후보를 탐색했다/더 좋은 후보가 없다”는 candidate-search exhaustiveness 결론이 성립하는가

**성립하지 않음 (NOT PROVABLE — and on durable evidence, FALSE as a completeness claim).**

- Durable이 보존한 탐색은 정확히 **Phase1 진단 + 4개 유계 후보(Exp1 lexical hint, Exp2 embedding SIDO earliest, Exp3 semantic-core, Exp4 region-attached cleanup)** 뿐. D-010은 Exp4를 마지막 bounded experiment로 선언했을 뿐, “이 4개가 공간을 소진한다”는 완전성을 보장하지 않음. Phase1 summary가 제안한 3개 방향(지역 보존, 복합명사 정규화, 후보수 확장) 중 일부는 미실행 또는 1개 변형만 실행.
- Web의 read-only 중간 검증/steering이 있었는지는 **durable repo만으로 증명 불가 (UNKNOWN)** — commit/tag에 read-only 행위가 남지 않음. 따라서 “충분히 탐색했다”는 주장은 (a) 탐색 수가 4개로 유계하고, (b) 각 Exp가 1개 deterministic 변형만 다루며, (c) 인간-in-the-loop 설계 결정이 개입된 이상, **소진 증명 불가**. 반대로 “더 좋은 후보가 없다”는 부정도 증명 불가.
- **정정된 표현:** 문서의 “single execution”은 “canonical accepted execution 1회”로만 읽어야 하며, “충분히 탐색했다”는 표현은 durable 증거 없이 사용하면 안 됨. 유효한 표현은 “**이 4개 후보는 REJECTED이며, 더 넓은 공간은 미탐색으로 남았다**”.

### 6.3 Cycle2 dev가 반복 관찰/steering 때문에 앞으로 tuning set으로 계속 사용 가능한가, 아니면 selection bias 관점에서 retired해야 하는가

**D-010을 따른다: frozen dev `retrieval-v2-cycle2-dev-v1` (36 cases, SHA `c8b66fef…`)는 정상 tuning set으로 유지 가능, 그러나 엄격한 disclaimers와 함께 사용해야 함. Retired(폐기)는 불필요하나, naive reuse는 금지.**

- **D-010 근거:** “Cycle2 holdout is disqualified, dev is retained as tuning set”는 Web/user 확정 standing decision이며, 본 감사는 D-003~D-010을 수정하지 않음. Dev는 holdout과 독립적으로 동결(`frozen_before_tuning true, retrieval_observed false`)됐고, holdout 오염이 dev에 전파됐다는 durable 증거 없음.
- **Selection bias 위험 (durable로 확인된 부분):** 4개 후보가 모두 동일 dev 36에서 `30/36` 천장에 걸렸고, per_case `rank_top30 0→0` 6 persistent miss가 반복됨. 인간이 dev 결과를 반복 관찰하며 다음 후보를 설계했으므로, **dev에 대한 암묵적 overfitting 위험은 존재**. Durable repo는 관찰 횟수를 증명하지 못하나, commit 시퀀스(Phase1→Exp1→Exp2→repair→Exp3→Web confirmation→D-010→Exp4)는 dev 관찰이 설계에 영향을 줄 수 있는 구조였음을 보임.
- **권고되는 사용 조건 (retired 대신 bounded reuse):**
  - Dev를 **tuning set으로만 사용, selection set으로 재사용하지 말 것** — 최종 후보 선정은 반드시 **새로운 holdout(Cycle3, tuning 전 동결, dev와 query+gold overlap 0, D-007 재검증)** 에서만 판정.
  - Dev에서의 추가 탐색은 **사전 등록(pre-registered) 후보 수와 설계 공간을 문서화**하고, 연속 steering을 피하며, 각 후보의 `new>=31 && Gov24==18 && loss0` 판정을 dev에서만 REJECTED/CONTINUE로 사용하되, dev에서의 “최고”를 final로 격상하지 말 것.
  - Dev를 여러 번 재사용할 경우, **selection bias 보정 없이 dev 점수 상승을 최종 성능 개선으로 주장하지 말 것**.
  - 결론: **`retired 불필요, but next selection must be on a fresh holdout; dev remains a tuning set with disclaimers, not a selection set.`**

### 6.4 다음 clean 단계 후보 (새 cycle/실험 시작 없이, Q-005 open 유지)

**Q-005는 open 유지. 아래는 clean 단계에서 고려할 후보 설계 공간이며, 본 감사에서 실행하지 않음. D-003/D-004/D-007/D-008/D-009/D-010 불변.**

1. **Region-core preservation with suffix-normalized lexical (Phase1 Option1 정교화):** `strip_region`이 `부산→에`처럼 핵심 지역어를 삭제하는 부작용을 보정 — alias 매칭 시 suffix(`시/도/특별자치도` 등) longest-first 정규화 후 핵심 지역 stem을 lexical term으로 1개 보존, 또는 character 2-gram fallback으로 `삼척시 vs 삼척형` 같은 admin form variance 허용. Lexical bias `0.01` 유지, hard-negative intrusion 재검증 필요. 기대 효과: c2d-003/013/015의 vector top30 진입 지원. Latency는 SQL ILIKE n-gram 비용 측정 필요.

2. **Agglutinative particle handling extension + compound-entity over-fragmentation 방지:** 기존 `lexical_overlap_terms_rewrite`의 particle stripping을 유지하되, `에서/에게서/으로부터` 등 장-tail particle과 `특별자치도/광역시` 등 행정 suffix를 longest-first로 1회만 제거하는 현 Exp4 문법을 lexical 쪽에도 적용 — embedding만이 아니라 lexical overlap 분모를 줄여 `자립지원전담기관` 같은 장복합어의 유효 overlap을 높임. 단, 과분해를 피하고 hard-negative를 모니터링.

3. **Retrieval-depth diagnostic (CANDIDATES 30→40 bounded test, latency budget 내):** Phase1이 지적한 “6 persistent miss는 top30 밖”이므로, 30 밖 몇 위까지 gold가 분포하는지 **diagnostic_only**로 분포만 측정 (selection 아님). 후보수 증가는 D-003 변경이므로, latency `candidate p95 <= baseline p95` (D-007)를 `진단`으로만 측정하고, 10ms 이내 증가가 아니면 채택하지 않음. Cycle1 latency +59ms 진단이 이미 회귀였으므로 신중.

4. **Holdout 재생성 (Cycle3, D-010 준수):** 위 후보 중 dev에서 `new>=31`을 만족하는 것이 나오면, 그 후보를 **고정(freeze)** 한 뒤 **완전히 새로운 holdout 40 cases** (Youth 20/Gov24 20, 6 categories 균형, P0/cycle1-holdout/cycle2-dev/cycle2-holdout/hard-negative와 query+gold overlap 0, `frozen_before_tuning true`)를 **tuning 전 동결**하여, 고정된 후보에 추가 tuning 없이 D-007 7 Gates (quality +2 net, no regression, P0, hard-negative, fresh paired latency, holdout integrity)로만 평가. 이 구조가 D-010이 허용한 유일한 clean 평가 경로.

*모든 후보는 D-004의 cross-encoder/reranking, global threshold, public region search 제외를 유지하며, 구현 전 pre-registration과 hard-negative/latency 사전 검증을 전제.*

---

## 7. UNKNOWN / NOT PROVABLE 목록 (durable repo만으로 판정 불가)

1. Web이 Exp2~Exp4 각 Paseo 실행 완료 전에, read-only로 dev 결과를 몇 회 관찰했고 어떤 steering을 했는지 — commit/tag에 남지 않음.
2. 각 Exp가 프로세스 레벨에서 정확히 몇 회 실행됐는지 — repo는 canonical accepted 1회만 보존, run counter 없음.
3. Exp2~Exp4 설계가 Phase1 제안의 사전 계획이었는지, 직전 dev 관찰 후 즉석 steering이었는지 — commit message만으로 의도 구분 불가.
4. `44ce287` holdout plaintext read가 어떤 agent/세션에서 몇 회 발생했는지 — SESSION-LOG는 “post-tuning candidate session에서 발생”으로만 aggregate 기록, 횟수는 durable에 없음.
5. Web의 중간 검증이 dev 점수에 영향을 주는 코드 변경으로 이어졌는지 — Exp1~Exp4 runner diff는 각 Exp 내부에서 0~1회 보정에 그치며, dev 점수를 인위적으로 높이는 변경의 durable 증거 없음.

---

## 8. 증거 인벤토리 (감사자가 read-only로 확인한 핵심 경로)

- Branch: `codex/retrieval-v2-cycle2-candidate` HEAD `3caa6729efd5437994afa7ab5392ad8bb5227eb3` (local == origin == actual remote).
- Tags: `retrieval-v2-cycle2-dev-v1` `500beadae11ddb423cc2ea4d46494c0a9f2b1173` → `372ed686579b4e8e2b9854d297e44fee18775352`, `retrieval-v2-cycle2-holdout-v1` `03da4cc28d1bb324f5176efb500dfeaa1684b3fa` → `9e2cd6ea4b8203b474d7d6a6a69a088763284043` (DISQUALIFIED), `retrieval-v2-cycle2-start-v1` `434b798d60bf15433590362aaad4a021846094d4`.
- Dev evalset: `eval/retrieval-v2/cycle2/dev/evalset.jsonl` LF SHA256 `c8b66fef69bdfd0db053ac7cac0fb027fc3271c6072ab992b622cacdc71ace5e` (36 Youth18/Gov24 18, 6×6).
- Holdout evalset (DISQUALIFIED, history only): `eval/retrieval-v2/cycle2/holdout/evalset.jsonl` LF SHA256 `cf003bab7713138fbd9c4622addeeb886c01f401aeab3d43b1144ae6e4c79727` (40 Youth20/Gov24 20) — D-010에 따라 final gate 사용 금지.
- Cycle1 HOLD SSOT: `docs/RETRIEVAL_V2.md` §Cycle 1, tags `retrieval-v2-final-holdout-result-v1` `d86e0119…`, `retrieval-v2-p0-result-v1` `3373da2…`, `retrieval-v2-hard-negative-result-v1` `34ca5a5…`, `retrieval-v2-latency-result-v1` `b04556f…` + provenance v3 `c0d2a932…→3ac6218…`.
- Cycle2 artifacts: `dev/phase1-paired-baseline-vs-candidate-v2.json`, `dev/phase1-summary.md`, `dev/latency-diagnostic-phase1.json`, `phase2-exp1-region-hint/phase2-exp1-paired.json`, `phase2-exp2-embedding-region/phase2-exp2-paired.json`, `phase2-exp3-semantic-core/phase2-exp3-paired.json`, `phase2-exp4-region-attached/phase2-exp4-paired.json` (모두 `diagnostic_only true, not_final_gate true, git_dirty true`).
- Decisions: D-003…D-010 불변, 특히 D-010(holdout disqualified, Exp4 bounded, Cycle3 new holdout).
- Git hygiene: `git diff --check` PASS, `git status --porcelain` clean (감사 시점), changed files는 본 감사 문서 3개만 허용 (아래 검증).

---

## 9. 감사 한계와 다음 감사자를 위한 메모

- 본 감사는 **process audit**이며, retrieval 품질 재측정이나 holdout 재평가가 아님. 모든 metric은 artifact 기록을 신뢰하되, 그 기록의 provenance(`git_commit`, `dev_sha`, `corpus`, `production_diff`)를 교차 검증하는 방식으로만 검증.
- “Web steering이 있었다”는 주장과 “없었다”는 주장 모두 durable 증거 없음 — 따라서 본 감사는 두 주장 모두를 **증명하지 않음**. 다만 “충분히 탐색했다”는 완전성 주장은, 탐색 수가 4개로 유계하고 각 Exp가 1개 변형만 다루므로, **durable 증거가 부족하여 성립하지 않음**으로 판정.
- 향후 clean Cycle3를 위해서는, **사전 등록된 후보 수·설계 공간, fresh holdout의 tuning 전 동결, 그리고 holdout에 대한 read-only 접근의 append-only audit log**를 도입하면, 본 감사에서 UNKNOWN으로 남은 프로세스 횟수/steering 여부를 다음에는 durable로 증명할 수 있다.

---

*본 문서는 `docs/RETRIEVAL_V2.md` SSOT를 대체하지 않으며, 그 문서의 현재 해석에 대한 경고와 함께 링크된다. D-003~D-010은 수정/승격/폐기하지 않음. Q-005는 open 유지.*
