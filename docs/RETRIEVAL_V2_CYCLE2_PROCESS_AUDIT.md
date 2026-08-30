# Retrieval v2 Cycle2 PROCESS AUDIT — durable evidence only (read-only) + Web cross-validation addendum (2026-08-30)

> **Scope (v1 2026-08-30 durable-only):** Web이 Exp2~Exp4 작업 중 Paseo 완료 전에 여러 차례 중간 검증/steering/프로세스 중단을 수행하여 candidate-search 신뢰도가 훼손됐을 가능성을, **durable repo 증거만으로** 독립 감사. canonical 숫자를 재실행하거나 무효화하지 않고, 증명되는 범위와 증명되지 않는 범위를 분리.
> **Scope (v2 addendum 2026-08-30 Web cross-validation):** v1 이후 Web이 session recording을 독립 검증하여, durable repo만으로는 `UNKNOWN`이던 일부 사실이 `Web cross-validation evidence (session recording)` provenance로 추가 확정됨. 본 addendum은 repo 추론이 아닌 Web 기록을 별도 provenance로 명시하여 per-exp process status를 보정한다. 수치 재실행/artifact 재생성 없음.
> **HARD GATE:** `Muse Spark 1.2 Contributor / 매우 높음(xhigh)` — 본 세션 시작 시 verified. 아니면 즉시 중단 보고해야 하나 통과.
> **금지 준수 (v1/v2 공통):** retrieval/DB/model/embedding/benchmark/holdout plaintext/`git show` holdout/`checkout` holdout/final holdout 실행 전부 금지. production/ml-service, frozen dev/holdout, eval artifact 재생성/수정 금지. 본 감사는 기존 artifact/runner/docs/memory/Git metadata read-only 감사만 수행(이번 보정도 동일).

**감사 기준 (v1):** `codex/retrieval-v2-cycle2-candidate` branch, reconciled HEAD `3caa6729efd5437994afa7ab5392ad8bb5227eb3` at 2026-08-30, `local == origin == actual remote (https://github.com/crushonyou2/benefit-compass.git)`, `git status --porcelain` clean, `git diff --check` PASS.
**감사 기준 (v2 addendum):** 동일 branch reconciled HEAD `88c25146f57b678c4f4a526c9dc5a8a6f87b97ff` (v1 audit commit) at 2026-08-30, `local == origin == actual remote`, `git status clean`, `git diff --check PASS` — v1 audit 이후 Web 독립 검증 결과를 반영하는 문서 보정만 수행.

**감사 일자:** 2026-08-30 (Asia/Seoul). **감사 주체:** Paseo (independent read-only audit). **Web cross-validation:** 2026-08-30 Web session recording (별도 provenance, 아래 §0.1).

## 0.1 Web cross-validation evidence provenance (v2 addendum — repo 추론 아님)

> **Provenance 구분:** 본 addendum에서 `Web cross-validation evidence (session recording)`로 표시된 사실은, durable repo만으로는 `UNKNOWN`이던 항목이 Web의 실제 session recording으로 추가 확정된 것이다. 이는 repo 추론이 아니라 별도 provenance이며, 아래 per-exp 표의 `(c)`와 `(e)` process status 보정에만 사용하고, canonical metric 수치 자체는 재실행 없이 보존한다.

- **Exp2 (Web recording):** Paseo가 최초 denoised-embedding 방향을 작성했고 Web이 완료 전 중단·폐기 후 SIDO semantic-preservation 방향으로 steering. 그 후 Exp2 dev runner가 canonical 전 최소 2회 조기 시작되어 Web이 중단, 최소 1회 premature artifact가 생성됐다가 폐기. Web은 canonical 전 `fail-closed assert`/`selected_sido_code` 기록/`vector_only` 제거/latency timed-scope 등을 추가 steering. 최종 canonical artifact 수치는 이후 fail-closed로 일관되나 PROCESS는 contaminated.
- **Exp3 (Web recording):** Web이 Exp2 결과를 본 뒤 semantic-core 후보를 직접 선정. Paseo 완료 전 runner/코드를 반복 검토·steering, `raw rank_top30` semantics가 잘못된 runner가 실제 시작되어 Web이 Python 프로세스를 종료한 뒤 수정본으로 canonical 실행. Holdout plaintext incident/`44ce287`는 별도 존재. 최종 dev metric은 canonical로 유효하되 PROCESS contaminated.
- **Exp4 (Web recording):** Web이 Exp3 결과 후 후보를 설계, Paseo 완료 전 runner를 읽고 개입. 잘못된 runner가 실제 시작된 뒤 Web이 종료, 당시 SQL param contract(`limit/n`, `lexical_bias`), corpus table, baseline/candidate encode 공유, latency `age=None` 등 문제를 발견해 수정 steering 후 canonical 실행. 최종 metric은 canonical로 유효하되 PROCESS contaminated.
- **Exp1 (Web recording):** canonical REJECTED 확정 뒤 추가 case diagnostic retrieval이 시작되어 Web이 중단. canonical metric 자체는 유효하나 결과 확정 후 추가 retrieval 금지 절차 위반, 다음 후보 설계에 관찰 편향 가능성.
- **Docs-only (Web recording):** Paseo 8개 작업 완료 전 Web이 '정체'로 오판하여 중간 검증/새 workspace를 만들었으나 retrieval metric에는 영향 없음. 운영 절차 문제의 직접 증거로만 기록.

**보정 기준:** Phase1은 `VALID_CANONICAL_RESULT` 유지. Exp1~Exp4의 canonical metric/REJECTED는 `VALID_CANONICAL_RESULT`로 보존하되, process status를 별도 열/결론에서 모두 `VALID_RESULT_PROCESS_CONTAMINATED`로 명시(Exp1은 post-result extra retrieval, Exp2~4는 intermediate steering/premature runs). Cycle2 candidate-search 전체는 `PROCESS_CONTAMINATED`이며 “충분히 탐색/더 좋은 후보 없음” 결론은 무효. `single execution`은 계속 `canonical accepted execution 1회`로만 해석.

---

## 0. 방법론과 한계 (증거 분리 원칙)

- **durable evidence로 간주:** `git log`/`git show`로 재현 가능한 commit/tag/object, `eval/retrieval-v2/cycle2/`에 커밋된 artifact JSON/MD의 `git_commit`/`git_dirty`/`diagnostic_only`/`not_final_gate`/`dev_sha`/`corpus`/`per_case` 필드, `memory/DECISIONS.md`·`docs/RETRIEVAL_V2.md`·`memory/SESSION-LOG.md`에 기록된 aggregate-only 서술, `evalset.jsonl`/`manifest.json`의 LF SHA256. **v2 addendum에서는 여기에 `Web cross-validation evidence (session recording)` provenance가 별도로 추가됨 — 상기 §0.1이 그 출처를 명시하며, repo 추론과 구분한다.**
- **durable evidence로 간주하지 않음 (v1 기준):** Web 브라우저에서 수행된 read-only preflight, 화면에 표시된 중간 검증, 구두 steering, 프로세스 중단 여부, Paseo 세션 이전 메모리상의 `git show` 호출 횟수 — 이들은 commit/tag로 남지 않으면 repo만으로는 증명 불가. 본 감사는 이들을 `UNKNOWN / NOT PROVABLE (durable repo alone)`로 분류. **v2에서는 이 중 일부가 Web recording으로 확정되어 §0.1 및 per-exp 표의 `(c)`에 반영됨.**
- **용어 정정 (전역):** 기존 문서·SESSION-LOG의 “single execution at <commit> dirty” 표현은, repo가 프로세스 실행 1회를 증명하지 못하므로 **`canonical accepted execution 1회`** — 즉 해당 commit에 canonical으로 채택·커밋된 artifact가 1개 존재한다는 뜻으로만 해석한다. 실행 카운터, run log, append-only counter가 repo에 없으므로 “프로세스가 정확히 1회만 실행됐다”는 주장은 durable 증거 없음. **v2에서도 이 정정은 유지되며, Web recording이 보여준 premature 실행들은 canonical accepted 1회와 별도로 process contamination으로 분류한다.**

**Evidence status 정의:**

| status | 의미 |
|---|---|
| `VALID_CANONICAL_RESULT` | 수치 자체가 fail-closed sanity를 통과하고, dev SHA·corpus·production diff 일치가 durable로 검증되며, holdout 오염 없이 diagnostic_only로 보존된 REJECTED/PASS. 이 실험의 수치 결론은 기술적으로 유효. |
| `VALID_RESULT_PROCESS_CONTAMINATED` | 수치는 기술적으로 유효하나, 인간-in-the-loop steering/selection bias/premature runs 등 프로세스 오염이 Web recording 또는 durable로 확인돼, 그 수치를 근거로 한 “충분히 탐색했다” 같은 상위 결론은 무효. |
| `INVALID_FOR_SELECTION` | 해당 set/artifact가 final gate evidence로 사용 금지 (D-010 holdout 등). |
| `UNKNOWN` | durable repo만으로는 판정 불가 (v2에서는 Web recording으로 확정된 항목은 UNKNOWN에서 제외). |

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
| **(c) known premature/noncanonical execution 증거** | **durable 1건 + Web cross-validation 1건.** Durable: canonical accepted artifact 1개만 repo에 존재(`git_dirty True` 외 실행 카운터 없음). `53bd190` docs 패치는 사전 합의된 parity 정정. **Web cross-validation (session recording) provenance:** canonical REJECTED 확정 뒤 **추가 case diagnostic retrieval이 실제 시작**되어 Web이 중단. 이는 결과 확정 후 추가 retrieval 금지 절차 위반으로, 다음 후보 설계에 관찰 편향 가능성을 남김. durable repo만으로는 보이지 않던 절차 위반이 Web 기록으로 확정. |
| **(d) 결과를 본 뒤 코드 변경 가능성** | **부분 증명 — 메타데이터 패치는 결과 관찰 후 발생(재실행 없음, diff 증명).** lexical/embedding 로직은 Exp1 커밋 이전 고정. 다만 Web recording이 보여준 post-result extra retrieval 시도는 “결과를 본 뒤 추가 관찰을 시도했다”는 절차 위반으로, 코드는 바꾸지 않았으나 관찰 편향 위험을 남김. “결과를 보고 후보를 고쳐 재실행했다”는 durable 증거는 없음. |
| **(e) evidence status** | **Metric `VALID_CANONICAL_RESULT` / Process `VALID_RESULT_PROCESS_CONTAMINATED`.** REJECTED 수치 자체는 dev SHA·corpus·fail-closed로 유효하나, **process는 Web이 증명한 post-result extra retrieval 시도로 contaminated** — “이 후보 하나가 lexical hint 공간을 대표한다”는 상위 결론은 무효. 보정 기준에 따라 process status는 `VALID_RESULT_PROCESS_CONTAMINATED`로 명시. |
| **(f) 안전하게 결론 / 결론내면 안 되는 것** | ✅ 안전: bounded lexical hint 1개 설계는 `30→30`으로 개선 없음 — 이 후보 REJECTED는 정당(수치 유효). ✅ 안전: 6 persistent miss가 vector top30 밖임은 기술적으로 유효. ❌ 불가: “lexical hint 전체 무의미” 일반화 불가 — 1개 설계만 테스트. ❌ 불가: “절차가 깨끗했다” — Web recording이 post-result extra retrieval 시도를 증명하므로 process contaminated. ❌ 불가: “single execution” 횟수 단정 — `canonical accepted 1회`로만 해석. |

---

## 3. Exp2 — Embedding preserves at most one SIDO via earliest alias (lexical unchanged)

| 항목 | 내용 |
|---|---|
| **(a) canonical artifact/commit/ref** | Commit `b1faabec2a0210070f565a918c18d3c4d762f37e` (dirty True, `git_commit 53bd190cd716cce8a81a1ff3979483098f78471d`). Artifacts: `eval/retrieval-v2/cycle2/phase2-exp2-embedding-region/phase2-exp2-paired.json` (`diagnostic_only true, not_final_gate true, dev SHA c8b66fef…, model intfloat/multilingual-e5-base, lexical identical to candidate-v2, embedding `strip_region(raw)+at most one SIDO[code][0] via earliest alias tie code sort`, per_case `new.selected_sido_code` 기록, `rank_top30`은 vector 효과만의 차이로 명시, `vector_only` 2×/case 제거), `phase2-exp2-summary.md`, runner `candidate_embedding_region_hint.py` / `run_cycle2_phase2_exp2_embedding_region.py`, test `test_retrieval_v2_cycle2_phase2_embedding_region.py` (fail-closed `baseline 28/30, Gov24 18/18` assert). |
| **(b) 최종 metric 재현성·fail-closed sanity** | **PASS.** Baseline R@1 21/36 R@5 28/36 R@10 29/36 MRR 0.6577, candidate-v2 21/30/30 MRR 0.6884, new R@1 25/36 R@5 30/36 R@10 30/36 MRR 0.7509 macro 0.8333, Youth12/Gov24 18, baseline vs new net +2 (c2d-025/031) loss0, candidate vs new net 0 loss0, `new 30 not >=31` → REJECTED, latency `NOT_RUN_EARLY_STOP`. Runner가 quality 산출 직후 `assert baseline 28/36, candidate 30/36, Gov24 18/18`을 통과한 것이 SESSION-LOG와 artifact `code_diff_verification.production_diff_zero true`로 기록됨. 이후 Exp3/Exp4도 동일 baseline/candidate를 재확인하여 수치 일관성 확보. |
| **(c) known premature/noncanonical execution 증거** | **durable 1건 + Web cross-validation (session recording) 5건 확정.** Durable: `git_dirty True` 외 canonical accepted 1개만 repo에 존재. **Web provenance:** (1) Paseo 최초 denoised-embedding 방향을 Web이 완료 전 중단·폐기 후 SIDO 방향으로 steering, (2) canonical 전 dev runner가 **최소 2회 조기 시작**되어 Web이 중단, (3) **최소 1회 premature artifact가 생성됐다가 폐기**, (4) canonical 전 `fail-closed assert`/`selected_sido_code`/`vector_only` 제거/latency timed-scope 등 추가 steering이 Web에 의해 canonical 실행 전에 개입. durably 보이지 않던 premature 실행/steering이 Web 기록으로 확정. |
| **(d) 결과를 본 뒤 코드 변경 가능성** | **확정 — Web steering으로 canonical 전 코드가 수정됨.** Web이 fail-closed assert, per-case `selected_sido_code` 기록, `vector_only` 2× 제거, latency timed-scope 등을 canonical 전 추가했으며, denoised 방향 폐기 후 SIDO 방향으로 재시작. “결과를 보고 후보를 고쳐 재실행했다”는 durable 증거 없었으나, **canonical 전 steering/조기 실행은 Web recording으로 확정**. 최종 canonical 수치는 이후 fail-closed 일관되나 process 오염은 분리. |
| **(e) evidence status** | **Metric `VALID_CANONICAL_RESULT` / Process `VALID_RESULT_PROCESS_CONTAMINATED`.** REJECTED 수치 자체는 dev SHA·corpus·fail-closed·production diff 0으로 유효하나, **process는 Web이 증명한 최소 2회 premature run + artifact 폐기 + steering으로 contaminated**. 상위 “충분히 탐색/더 좋은 후보 없음” 결론은 무효. 보정 기준에 따라 process status는 `VALID_RESULT_PROCESS_CONTAMINATED`로 명시. |
| **(f) 안전하게 결론 / 결론내면 안 되는 것** | ✅ 안전: “earliest-alias 1 SIDO embedding 이 1개 설계는 `R@5 30→30`으로 개선 없음” — 이 후보 REJECTED는 정당(수치 유효). ✅ 안전: `rank_top30` 차이가 순수 embedding 효과임은 유효. ❌ 불가: “절차가 깨끗했다/단 1회 실행됐다” — Web recording이 최소 2회 premature 실행·폐기·steering을 증명하므로 process contaminated, `canonical accepted 1회`로만 해석. ❌ 불가: “이 1개 hint가 지역 힌트 공간을 대표” — steering된 단일 방향만 테스트. |
---

## 4. Exp3 — Semantic-core embedding (`" ".join(lexical_overlap_terms_rewrite(strip_region))` or fallback, lexical identical)

| 항목 | 내용 |
|---|---|
| **(a) canonical artifact/commit/ref** | Commit `3fdb06c541a3ef092b84fe23e0f96658c7865af8` (dirty True, `git_commit 44ce287d615a6131be2a2e1fd2f44d48287e0645` — HARD SEAL repair 후 clean baseline). Artifacts: `eval/retrieval-v2/cycle2/phase2-exp3-semantic-core/phase2-exp3-paired.json` (`diagnostic_only true, not_final_gate true, dev SHA c8b66fef…, corpus 13589/17609, candidate_config `semantic-core` = join rewrite terms or fallback stripped, lexical identical to candidate-v2, `single_encode_single_retrieval_per_variant` = 1 encode+1 retrieval/variant, `_fetch_cands` raw 30 반환 후 `rank_top30`은 raw, `rank@k`는 COSINE_MIN postfilter 후 계산 — Phase1/Exp2와 동일, 36×3 per_case 전체 기록), `phase2-exp3-summary.md`, runner `candidate_semantic_core.py` / `run_cycle2_phase2_exp3_semantic_core.py`, test `test_retrieval_v2_cycle2_phase2_semantic_core.py` 8 passed. Web confirmation 별도 `13ba60c8872c6225dcaa8335293dd8c422083853` docs-only. |
| **(b) 최종 metric 재현성·fail-closed sanity** | **PASS.** Baseline 21/28/29 MRR 0.6577, candidate-v2 21/30/30 MRR 0.6884, new R@1 23/36 R@5 30/36 R@10 30/36 MRR 0.7116 macro 0.8333, Youth12/Gov24 18, baseline vs new net +2 (c2d-025/031) loss0, candidate vs new net 0 loss0, `new 30 not >=31` → REJECTED, latency `NOT_RUN_EARLY_STOP`. Fail-closed `dev SHA c8b66fef…` 및 `baseline 28 Youth10 Gov24 18 / candidate 30 Youth12 Gov24 18` 통과가 SESSION-LOG와 `git_commit 44ce287 dirty True`로 기록. Runner는 `_fetch_cands`가 filtered list가 아닌 raw 30을 반환하도록 사전 보정된 뒤 실행됨이 SESSION-LOG에 명시. `HOLDOUT opt-in off` (`RETRIEVAL_V2_ALLOW_HOLDOUT_PLAINTEXT_AUDIT` unset, `git show` 0회) 유지가 검증됨 (`pytest ... 18 passed 5 skipped, git show 0`). |
| **(c) known premature/noncanonical execution 증거** | **durable 1건 + Web cross-validation (session recording) 4건 확정.** Durable: `44ce287` HARD SEAL 위반(holdout plaintext `git show`, Exp3 이전, retrieval 0) — holdout `INVALID_FOR_SELECTION`. **Web provenance:** (1) Web이 Exp2 결과 관찰 후 semantic-core 후보를 직접 선정(인간-in-the-loop steering), (2) Paseo 완료 전 runner/코드를 반복 검토·steering, (3) `raw rank_top30` semantics가 잘못된 runner가 **실제 시작**되어 Web이 Python 프로세스를 종료, (4) 수정본으로 canonical 실행. durably 보이지 않던 premature 실행/steering이 Web 기록으로 확정. 최종 dev 수치는 holdout 미접근으로 유효하되 process contaminated. |
| **(d) 결과를 본 뒤 코드 변경 가능성** | **확정 — Web steering으로 canonical 전 runner가 수정됨.** `_fetch_cands`의 raw 30 vs filtered `rank_top30` 정정은 SESSION-LOG에 기록됐으나, Web recording은 그 외 `raw rank_top30` 오류를 가진 premature runner가 실제 실행됐다가 Web에 의해 종료된 뒤 수정본이 canonical으로 실행됐음을 증명. Exp3 결과를 본 뒤 동일 Exp3 재실행 durable 증거 없으나, **canonical 전 steering/premature run은 Web recording으로 확정**. |
| **(e) evidence status** | **Metric `VALID_CANONICAL_RESULT` / Process `VALID_RESULT_PROCESS_CONTAMINATED`.** dev 수치는 dev SHA·corpus·fail-closed·holdout 미접근으로 유효하나, **process는 Web이 증명한 premature run+steering으로 contaminated**. Holdout은 별도 `INVALID_FOR_SELECTION`. 보정 기준에 따라 process status는 `VALID_RESULT_PROCESS_CONTAMINATED`로 명시. |
| **(f) 안전하게 결론 / 결론내면 안 되는 것** | ✅ 안전: “semantic-core 1개 설계는 `30→30`으로 개선 없음” — REJECTED 정당(수치 유효). ✅ 안전: 6 persistent miss가 `raw top30 0→0`임은 유효. ❌ 불가: “절차가 깨끗했다” — Web recording이 premature 실행·steering을 증명하므로 process contaminated. ❌ 불가: “시맨틱 코어 전체 무효” 일반화 — 1개 구현만 테스트. ❌ 불가: “single execution” — `canonical accepted 1회`로만 해석. |
---

## 5. Exp4 — Region-attached residue cleanup embedding (`cleanup_embedding_query`, lexical identical to candidate-v2)

| 항목 | 내용 |
|---|---|
| **(a) canonical artifact/commit/ref** | Commit `85b92efa52264c1878279746cf825043cca9cc4d` (dirty True, `git_commit beb9828a69432477c0cb22b8d776fc800a90dbfe` — D-010 기록 커밋). Artifacts: `eval/retrieval-v2/cycle2/phase2-exp4-region-attached/phase2-exp4-paired.json` (`diagnostic_only true, not_final_gate true, dev SHA c8b66fef…, model intfloat/multilingual-e5-base, production_contract CANDIDATES 30 COSINE_MIN 0.78 LEXICAL_BIAS 0.01 RERANK 0, candidate_config `cleanup_embedding_query` = alias+suffix(max1 longest)+particle(max1 longest) directly attached cleanup with fallback `strip_region(raw)`, lexical identical to candidate-v2, per_case 36×3 variants, `cleanup_applied 23/36, embedding_changed 8/36, corpus 13589/17609`), `phase2-exp4-summary.md`, runner `candidate_region_attached_cleanup.py` / `run_cycle2_phase2_exp4_region_attached.py`, test `test_retrieval_v2_cycle2_phase2_region_attached.py` 19 passed. 최종 reconcile `3caa6729efd5437994afa7ab5392ad8bb5227eb3`에서 `candidate branch current`를 `85b92ef`로 정정. |
| **(b) 최종 metric 재현성·fail-closed sanity** | **PASS.** Baseline 21/28/29 MRR 0.6577, candidate-v2 21/30/30 MRR 0.6884, new 21/30/30 MRR 0.6884 macro 0.8333, Youth12/Gov24 18, baseline vs new net +2 (c2d-025/031) loss0, candidate vs new net 0 loss0, `new 30 not >=31` → REJECTED, latency `NOT_RUN_EARLY_STOP`, `embedding_changed_vs_candidate 8/36` 실제 qvec 변경 있음에도 품질 동일. Fail-closed `baseline 28/30 Youth10/12 Gov24 18` 통과, `HOLDOUT opt-in off` (`RETRIEVAL_V2_ALLOW_HOLDOUT_PLAINTEXT_AUDIT` null, holdout dir absent, `git show` 0, tag/freeze 금지 준수) 및 `production diff 0` 검증됨. |
| **(c) known premature/noncanonical execution 증거** | **durable 2건 + Web cross-validation (session recording) 4건 확정.** Durable: `beb9828` D-010 기록(Exp3 후·Exp4 전 bounded 선언)과 `3caa672` reconcile(Exp4 후 stale HEAD 정정) — 프로세스 경계. **Web provenance:** (1) Web이 Exp3 결과 후 후보 설계, (2) Paseo 완료 전 runner를 읽고 개입, (3) 잘못된 runner(SQL `limit/n`, `lexical_bias`, corpus table, encode 공유, latency `age=None` 등 오류 포함)가 **실제 시작**되어 Web이 종료, (4) 문제 수정 steering 후 canonical 실행. durably 보이지 않던 premature 실행/steering이 Web 기록으로 확정. 최종 canonical 수치는 `fail-closed` 일관되나 process contaminated. |
| **(d) 결과를 본 뒤 코드 변경 가능성** | **확정 — Web steering으로 canonical 전 코드가 수정됨.** Web이 SQL param contract, corpus table, baseline/candidate encode 독립, latency age 등 문제를 발견해 수정 steering. Exp4 결과를 본 뒤 동일 Exp4 재실행 durable 증거 없으나, **canonical 전 premature run+steering은 Web recording으로 확정**. |
| **(e) evidence status** | **Metric `VALID_CANONICAL_RESULT` / Process `VALID_RESULT_PROCESS_CONTAMINATED`.** 수치는 dev SHA·corpus·fail-closed·holdout 미접근으로 유효하나, **process는 Web이 증명한 premature run+steering으로 contaminated**. 상위 완전성 주장은 무효. 보정 기준에 따라 process status는 `VALID_RESULT_PROCESS_CONTAMINATED`로 명시. |
| **(f) 안전하게 결론 / 결론내면 안 되는 것** | ✅ 안전: “region-attached cleanup 1개 설계 8/36 qvec 변경에도 `30→30`” — REJECTED 정당(수치 유효), Cycle2 CLOSED는 D-010에 따라 정당. ❌ 불가: “절차가 깨끗했다/단 1회 실행” — Web recording이 premature 실행·steering을 증명하므로 process contaminated, `canonical accepted 1회`로만 해석. ❌ 불가: “지역 잔류물 정리 전체 무효” 일반화 — 1개 설계만 테스트. ❌ 불가: “4개가 공간 소진” — 경계일 뿐 소진 아님. |

---

## 6. 종합 결론 — 4개 질문에 대한 엄격 분리 답

### 6.1 최종 28/30/30 등의 canonical metric 자체가 기술적으로 오염됐다는 증거가 있는가

**없음 — canonical metric 기술 오염 증거 없음. Web cross-validation도 “수치는 유효하되 PROCESS는 contaminated”로 일치.**

- Phase1 28→30, Exp1~Exp4 new 30/36, Gov24 18/18, loss0, R@1/MRR 등 모든 수치는 `dev SHA c8b66fef69bdfd0db053ac7cac0fb027fc3271c6072ab992b622cacdc71ace5e` 고정, corpus `13589/17609` 고정, `ml-service/app.py`·`source_ranking.py` diff 0, `diagnostic_only`·`not_final_gate` 일관, Exp2~Exp4 fail-closed 통과로 durable 검증. 재실행 없이 메타데이터만 패치한 `c2dfd87`/`53bd190`도 diff로 품질 영향 없음 증명. **Web recording도 최종 canonical 수치의 기술적 유효성을 부정하지 않음 — premature 실행들은 canonical 전 폐기/steering으로 끝났고, 최종 canonical 수치는 fail-closed 일관되므로 metric `VALID_CANONICAL_RESULT`를 유지.**
- 유일한 durable 오염은 `44ce287`의 post-tuning holdout plaintext `git show` (process-level read, 화면 노출 0, Exp3 이전). 이는 **holdout `retrieval-v2-cycle2-holdout-v1` (SHA `cf003bab…`)를 `INVALID_FOR_SELECTION`으로 만들 뿐**, dev 36의 retrieval/rank/score를 바꾸지 않음. Exp3/Exp4는 `HOLDOUT opt-in off, git show 0`으로 실행됨이 검증됨. **Web이 추가로 확인한 premature run들(Exp2 2회+폐기, Exp3/Exp4 각 1회 premature+종료, Exp1 post-result extra retrieval)은 canonical 수치 자체를 오염시키지 않음 — process contamination으로 분리.**
- 따라서 “28/30/30이 잘못 측정됐다/조작됐다”는 기술적 오염 주장은 durable + Web 모두에서 증거 없음. 각 실험의 **REJECTED 판정 자체는 유효(`VALID_CANONICAL_RESULT` for metric)**.

### 6.2 “Cycle2에서 충분히 좋은 후보를 탐색했다/더 좋은 후보가 없다”는 candidate-search exhaustiveness 결론이 성립하는가

**성립하지 않음 — Web cross-validation으로 `PROCESS_CONTAMINATED`가 확정되어, 완전성 결론은 무효 (INVALID).**

- Durable이 보존한 탐색은 정확히 **Phase1 진단 + 4개 유계 후보(Exp1 lexical hint, Exp2 embedding SIDO earliest, Exp3 semantic-core, Exp4 region-attached cleanup)** 뿐. D-010은 Exp4를 마지막 bounded experiment로 선언했을 뿐, “이 4개가 공간을 소진한다”는 완전성을 보장하지 않음.
- **Web recording으로 확정된 process contamination:** Exp2는 denoised→SIDO steering + 최소 2회 premature run+폐기+steering, Exp3는 Web이 Exp2 결과 기반 후보 선정 + premature run+종료+수정, Exp4는 Web이 Exp3 결과 기반 후보 설계 + premature run+종료+SQL/corpus/encode/latency steering, Exp1은 canonical 후 extra retrieval 시도+중단, docs-only는 Paseo 8개 완료 전 오판 검증. 이들은 commit/tag에 남지 않던 read-only steering/premature 실행이 **Web 기록으로 확정**되어, Cycle2 candidate-search 전체는 `VALID_RESULT_PROCESS_CONTAMINATED` — 수치는 유효하나 “충분히 탐색했다”는 상위 결론은 무효.
- **정정된 표현:** 문서의 “single execution”은 “canonical accepted execution 1회”로만 읽어야 하며(최종 canonical 1회는 유효), “충분히 탐색했다/더 좋은 후보 없음”은 Web이 증명한 premature/steering이 있었으므로 사용하면 안 됨. 유효한 표현은 “**이 4개 후보는 각 수치가 유효하게 REJECTED이나, PROCESS는 contaminated이므로 탐색 완전성을 주장할 수 없으며 더 넓은 공간은 미탐색**”.
### 6.3 Cycle2 dev가 반복 관찰/steering 때문에 앞으로 tuning set으로 계속 사용 가능한가, 아니면 selection bias 관점에서 retired해야 하는가

**D-010은 불변 — dev retired를 새 standing decision으로 만들지 않음. 다만 Web review 관점에서 두 가지 경로를 명확히 분리한다.**

- **D-010 기준 (standing decision, 불변):** “Cycle2 holdout is disqualified, dev is retained as tuning set”는 유지. Dev는 holdout과 독립 동결(`frozen_before_tuning true, retrieval_observed false`)됐고, holdout 오염이 dev에 전파됐다는 durable 증거 없음. 본 감사는 D-010을 수정/승격/폐기하지 않고 Q-005의 선택지로 남긴다.
- **1차 audit 권고 (bounded reuse, Web contamination과 별개로 가능):** Cycle2 dev 36(`c8b66fef…`)를 **tuning set으로만 사용, selection set으로 재사용 금지** — 최종 선정은 반드시 **새로운 holdout(Cycle3, tuning 전 동결, dev와 query+gold overlap 0, D-007 재검증)** 에서만 판정. 사전 등록(pre-registered) 후보 수·설계 공간 문서화, 연속 steering 금지, dev에서의 “최고”를 final로 격상하지 말 것. 이 경로는 **process contaminated 사실을 disclaimers로 명시**하면 D-010 범위 내에서 가능하다.
- **Web review 관점의 더 보수적 대안 (clean reset, 권장):** Exp1 post-result extra retrieval, Exp2~Exp4 premature run+steering이 Web recording으로 확정되어, Cycle2 dev가 **반복 관찰/steering에 노출**됐음이 증명됐다. 완전한 clean reset을 원하면 **`fresh Cycle3 dev (new 36 cases, dev SHA 새로 생성, P0/cycle1/cycle2와 overlap 0) + fresh Cycle3 holdout (new 40, tuning 전 동결)`** 을 동시에 생성하는 것이 더 보수적이다. 이는 D-010을 변경하는 결정이 아니라, Q-005에서 선택할 수 있는 **더 엄격한 위생 경로**로 남긴다. 새 dev를 쓰면 기존 dev의 selection bias·관찰 편향 논쟁 자체를 제거할 수 있다.
- **선택 가이드:** 두 경로 모두 “최종 선정은 반드시 fresh holdout에서만”은 공통. 차이가 다음 후보 탐색에 기존 dev를 **재사용하느냐(1차 경로) vs 완전히 새 dev로 교체하느냐(보수적 경로)** 이다. 다음 단계 결정은 Q-005에서 Web/user가 선택하며, 본 감사는 어느 쪽도 standing decision으로 격상하지 않는다.

### 6.4 다음 clean 단계 후보 (새 cycle/실험 시작 없이, Q-005 open 유지)

**Q-005는 open 유지. 아래는 clean 단계에서 고려할 후보 설계 공간이며, 본 감사에서 실행하지 않음. D-003/D-004/D-007/D-008/D-009/D-010 불변. Web contamination과 무관하게 기술적으로 유효한 다음 탐색 방향이다.**

1. **Region-core preservation with suffix-normalized lexical (Phase1 Option1 정교화):** `strip_region`이 `부산→에`처럼 핵심 지역어를 삭제하는 부작용을 보정 — alias 매칭 시 suffix(`시/도/특별자치도` 등) longest-first 정규화 후 핵심 지역 stem을 lexical term으로 1개 보존, 또는 character 2-gram fallback으로 `삼척시 vs 삼척형` 같은 admin form variance 허용. Lexical bias `0.01` 유지, hard-negative intrusion 재검증 필요. 기대 효과: c2d-003/013/015의 vector top30 진입 지원. Latency는 SQL ILIKE n-gram 비용 측정 필요.

2. **Agglutinative particle handling extension + compound-entity over-fragmentation 방지:** 기존 `lexical_overlap_terms_rewrite`의 particle stripping을 유지하되, `에서/에게서/으로부터` 등 장-tail particle과 `특별자치도/광역시` 등 행정 suffix를 longest-first로 1회만 제거하는 현 Exp4 문법을 lexical 쪽에도 적용 — embedding만이 아니라 lexical overlap 분모를 줄여 `자립지원전담기관` 같은 장복합어의 유효 overlap을 높임. 단, 과분해를 피하고 hard-negative를 모니터링.

3. **Retrieval-depth diagnostic (CANDIDATES 30→40 bounded test, latency budget 내):** Phase1이 지적한 “6 persistent miss는 top30 밖”이므로, 30 밖 몇 위까지 gold가 분포하는지 **diagnostic_only**로 분포만 측정 (selection 아님). 후보수 증가는 D-003 변경이므로, latency `candidate p95 <= baseline p95` (D-007)를 `진단`으로만 측정하고, 10ms 이내 증가가 아니면 채택하지 않음. Cycle1 latency +59ms 진단이 이미 회귀였으므로 신중.

4. **Holdout 재생성 (Cycle3, D-010 준수):** 위 후보 중 dev에서 `new>=31`을 만족하는 것이 나오면, 그 후보를 **고정(freeze)** 한 뒤 **완전히 새로운 holdout 40 cases** (Youth 20/Gov24 20, 6 categories 균형, P0/cycle1-holdout/cycle2-dev/cycle2-holdout/hard-negative와 query+gold overlap 0, `frozen_before_tuning true`)를 **tuning 전 동결**하여, 고정된 후보에 추가 tuning 없이 D-007 7 Gates (quality +2 net, no regression, P0, hard-negative, fresh paired latency, holdout integrity)로만 평가. **Web 보수적 대안에서는 이 holdout과 함께 `fresh dev`도 새로 생성하여 선택 bias를 원천 차단할 수 있다.**

*모든 후보는 D-004의 cross-encoder/reranking, global threshold, public region search 제외를 유지하며, 구현 전 pre-registration과 hard-negative/latency 사전 검증을 전제. Process contaminated 사실은 다음 clean 단계의 disclaimers/문서화에 명시해야 한다.*

---

## 7. UNKNOWN / NOT PROVABLE 목록 — v1 durable-only 대비 v2 Web 확정으로 축소

**v1에서 UNKNOWN이던 다음 항목이 Web recording으로 확정되어 본 목록에서 제외됨:** Exp2의 denoised→SIDO steering + 최소 2회 premature run+폐기 + fail-closed 등 steering, Exp3의 Web 선정 + premature run+종료+수정, Exp4의 Web 설계 + premature run+종료+SQL/corpus/encode steering, Exp1의 post-result extra retrieval 시도, docs-only 오판 검증 — 이들은 이제 §0.1 및 per-exp (c)에 `Web cross-validation evidence`로 기록됨.

**여전히 durable+Web으로도 판정 불가 (잔여 UNKNOWN):**

1. `44ce287` holdout plaintext read가 어떤 agent/세션에서 정확히 몇 회 발생했는지 — SESSION-LOG는 “post-tuning candidate session에서 발생”으로만 aggregate 기록, Web recording도 횟수를 세지 않음.
2. Web이 각 Exp의 dev 결과를 몇 회 관찰했고, 그 관찰이 다음 후보 설계의 어느 세부 파라미터에 반영됐는지 — “steering 있었다”는 확정됐으나 세부 반영 정도는 기록 없음.
3. Exp2~Exp4에서 premature로 폐기된 artifact의 정확한 내용·수치가 canonical과 몇 점 차이였는지 — 폐기되어 repo에 남지 않음.
4. Docs-only 오판 검증이 만든 새 workspace가 과연 retrieval metric에 0 영향이었는지 — repo에 영향 없으나, Web의 세션 분리가 다음 단계 설계 타이밍에 미친 간접 영향은 측정 불가.
5. 향후 fresh dev/holdout를 쓸 때 기존 dev의 관찰 편향이 완전히 제거되는지 — 이는 다음 cycle 설계 시점에 다시 감사해야 할 항목.

---

## 8. 증거 인벤토리 (감사자가 read-only로 확인한 핵심 경로 + Web cross-validation provenance)

- **Branch (v1/v2):** `codex/retrieval-v2-cycle2-candidate` HEAD `88c25146f57b678c4f4a526c9dc5a8a6f87b97ff` (v2 addendum 기준, local == origin == actual remote). v1 기준 `3caa6729efd5437994afa7ab5392ad8bb5227eb3`는 이전 audit HEAD.
- **Web cross-validation provenance:** 2026-08-30 Web session recording — Exp2(directed steering + 2 premature runs + 1 premature artifact 폐기 + fail-closed/selected_sido_code/vector_only/latency steering), Exp3(Web 선정 + premature rank_top30 오류 run+종료+수정), Exp4(Web 설계 + premature SQL/corpus/encode/age 오류 run+종료+수정), Exp1(post-result extra retrieval 시도+중단), docs-only(오판 검증) — 상기 §0.1이 별도 provenance. Repo 추론 아님.
- Tags: `retrieval-v2-cycle2-dev-v1` `500beadae11ddb423cc2ea4d46494c0a9f2b1173` → `372ed686579b4e8e2b9854d297e44fee18775352`, `retrieval-v2-cycle2-holdout-v1` `03da4cc28d1bb324f5176efb500dfeaa1684b3fa` → `9e2cd6ea4b8203b474d7d6a6a69a088763284043` (DISQUALIFIED), `retrieval-v2-cycle2-start-v1` `434b798d60bf15433590362aaad4a021846094d4`.
- Dev evalset: `eval/retrieval-v2/cycle2/dev/evalset.jsonl` LF SHA256 `c8b66fef69bdfd0db053ac7cac0fb027fc3271c6072ab992b622cacdc71ace5e` (36 Youth18/Gov24 18, 6×6).
- Holdout evalset (DISQUALIFIED, history only): `eval/retrieval-v2/cycle2/holdout/evalset.jsonl` LF SHA256 `cf003bab7713138fbd9c4622addeeb886c01f401aeab3d43b1144ae6e4c79727` (40 Youth20/Gov24 20) — D-010에 따라 final gate 사용 금지.
- Cycle1 HOLD SSOT: `docs/RETRIEVAL_V2.md` §Cycle 1, tags `retrieval-v2-final-holdout-result-v1` `d86e0119…`, `retrieval-v2-p0-result-v1` `3373da2…`, `retrieval-v2-hard-negative-result-v1` `34ca5a5…`, `retrieval-v2-latency-result-v1` `b04556f…` + provenance v3 `c0d2a932…→3ac6218…`.
- Cycle2 artifacts: `dev/phase1-paired-baseline-vs-candidate-v2.json`, `dev/phase1-summary.md`, `dev/latency-diagnostic-phase1.json`, `phase2-exp1-region-hint/phase2-exp1-paired.json`, `phase2-exp2-embedding-region/phase2-exp2-paired.json`, `phase2-exp3-semantic-core/phase2-exp3-paired.json`, `phase2-exp4-region-attached/phase2-exp4-paired.json` (모두 `diagnostic_only true, not_final_gate true, git_dirty true` — metric 유효, process는 Web 기록으로 §0.1처럼 contaminated).
- Decisions: D-003…D-010 불변, 특히 D-010(holdout disqualified, Exp4 bounded, Cycle3 new holdout) — 본 addendum은 결정 변경 아님.
- Git hygiene: `git diff --check` PASS, `git status --porcelain` clean (감사 시점), changed files는 본 감사 문서 3개만 허용 (아래 검증).
---

## 9. 감사 한계와 다음 감사자를 위한 메모 — v2 Web 확정 반영

- 본 감사는 **process audit**이며, retrieval 품질 재측정이나 holdout 재평가가 아님. 모든 metric은 artifact 기록을 신뢰하되, 그 기록의 provenance(`git_commit`, `dev_sha`, `corpus`, `production_diff`)를 교차 검증하는 방식으로만 검증. **v1(v1 durable-only)에서는 Web steering 여부를 `UNKNOWN`으로 분리했으나, v2 addendum에서 Web session recording이 Exp1 post-result extra retrieval, Exp2 2회 premature+폐기+steering, Exp3/Exp4 premature+steering을 확정하여, 이제 “Web steering이 있었다”는 **증명됨** — 다만 세부 횟수/파라미터 반영 정도는 여전히 UNKNOWN 잔존(§7).**
- “충분히 탐색했다”는 완전성 주장은, 탐색 수가 4개로 유계하고 각 Exp가 1개 변형만 다루며, **Web이 증명한 premature/steering으로 PROCESS는 contaminated**이므로, **durable+Web 모두에서 성립하지 않음**으로 판정. 문서의 `single execution`은 계속 `canonical accepted 1회`로만 해석한다 — 최종 canonical 1회는 유효하나, 그 전 premature 실행들은 process contamination으로 분류.
- 향후 clean Cycle3를 위해서는, **사전 등록된 후보 수·설계 공간, fresh holdout + (보수적 대안에서는 fresh dev)의 tuning 전 동결, 그리고 holdout/dev에 대한 read-only 접근의 append-only audit log**를 도입하면, 본 감사에서 잔존 UNKNOWN(§7)을 다음에는 durable로 증명할 수 있다. 특히 fresh dev를 동시에 새로 만들면 기존 Cycle2 dev의 관찰 편향 논쟁 자체를 제거할 수 있다.
---

*본 문서는 `docs/RETRIEVAL_V2.md` SSOT를 대체하지 않으며, 그 문서의 현재 해석에 대한 경고와 함께 링크된다. D-003~D-010은 수정/승격/폐기하지 않음. Q-005는 open 유지.*
