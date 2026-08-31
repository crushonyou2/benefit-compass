# DECISIONS — append-only ledger

Rules: only user-confirmed decisions are recorded. Nothing is edited or deleted. A changed decision gets a **new** entry that `supersedes D-xxx`, and the old entry receives exactly one added line: `→ superseded by D-yyy (date)`. Sequential ids, never reused. (Full protocol: ballast decision-ledger skill.)

---

## D-001 · Adopt the ballast memory structure — 2026-08-30 (user, project setup)

This project uses `memory/` as its durable brain: decisions in this ledger, unresolved items in OPEN-QUESTIONS, per-session notes in SESSION-LOG. Standing decisions are followed without relitigating; changes go through the supersede protocol.

<!-- Append new entries below. Example of a superseded pair:

## D-002 · Weekly report goes out Fridays — 2026-01-10 (user, chat)

→ superseded by D-005 (2026-02-01)

## D-005 · Weekly report moves to Mondays — 2026-02-01 (user, chat)

Supersedes D-002. Fridays kept slipping into the weekend; Monday forces the week to start closed-loop.
-->
## D-002 · Keep the P0 canonical evaluation baseline frozen — 2026-08-30 (historical backfill recorded 2026-08-30; user-confirmed during P0 work)

The P0 production-parity canonical artifacts remain the historical evaluation baseline.

Evaluation SSOT: `eval/canonical_manifest.json`.

Do not overwrite or silently regenerate the P0 canonical artifacts as a new baseline. Future Retrieval v2 evaluation artifacts must remain separate from the frozen P0 artifacts.

## D-003 · Keep the current production retrieval contract — 2026-08-30 (historical backfill recorded 2026-08-30; user-confirmed during P0-P3 work)

The standing production retrieval contract is:

- `RERANK=0`
- `CANDIDATES=30`
- `COSINE_MIN=0.78`
- `LEXICAL_OVERLAP_BIAS=0.01`
- `strip_region`
- expired-policy exclusion
- embedding model `intfloat/multilingual-e5-base`
- source-aware youth intent bias remains enabled for explicit youth-intent queries and is suppressed for known Gov24 organization queries

Evaluation numbers and provenance: `eval/canonical_manifest.json`.

Implementation truth: `ml-service/app.py` and `ml-service/source_ranking.py`.

## D-004 · Keep rejected retrieval alternatives out of the current scope — 2026-08-30 (historical backfill recorded 2026-08-30; user-confirmed during P0 work)

The following remain not adopted unless materially new evidence justifies reconsideration:

- cross-encoder reranking
- a global similarity / abstention threshold
- public region search

Public region search is disabled until trustworthy applicability-region data is available; it is not permanently excluded.

Evidence and experiment interpretation: `docs/CUSTOM_SEARCH_MVP.md` and the frozen P0 evaluation artifacts.

A future change must be recorded as a new decision that supersedes this entry rather than editing this entry.

## D-005 · Keep production topology Choice A — 2026-08-30 (historical backfill recorded 2026-08-30; user-confirmed during P3)

The current public request path is:

Public Web
 -> generic API service
 -> promoted P2 API revision
 -> tagged P2 ML revision

The generic ML service remains on the old ML rollback path and is not used by the promoted public API path.

Exact revisions, tags, traffic percentages, rollout evidence, and rollback commands are owned by `docs/P3_PUBLIC_ROLLOUT.md`.

Generic ML normalization is deferred and is a separate future production-routing change.

## D-006 · Follow the post-baseline work order — 2026-08-30 (historical backfill recorded 2026-08-30; user-confirmed)

The agreed work order is:

1. Public baseline freeze — complete.
2. Retrieval v2 — define the evaluation contract first, separate development from final holdout evaluation, then use offline/staging/no-traffic verification before any adoption.
3. Min instances — consider only if real public evidence shows cold starts materially affect users.
4. Generic ML normalization — defer until the final ML revision is settled.

Retrieval v2 does not automatically reopen cross-encoder reranking, a global threshold, or region search. Materially new evidence requires a new decision.

## D-007 · Adopt the Retrieval v2 evaluation contract — 2026-08-30 (AI-proposed, user-confirmed)

Retrieval v2 uses source-macro Recall@5 as the primary quality metric, with Recall@1, Recall@10, MRR@10, per-source Recall@5, and category slices as secondary or diagnostic measures.

The frozen P0 canonical sets remain historical regression gates, not tuning data:

- Youth Recall@5: `>= 28/60` PASS, `27/60` HOLD, `<= 26/60` NO-GO.
- Gov24 Recall@5: `>= 15/21` PASS, `14/21` HOLD, `<= 13/21` NO-GO.

Retrieval v2 uses a separate source-balanced development set of 30–40 new queries and a source-balanced final holdout of at least 40 new queries. The final holdout is frozen before tuning and is never used during development. P0 canonical artifacts remain frozen and the `canonical_*` namespace is not reused for Retrieval v2 artifacts.

On the final holdout, the current D-003 production retrieval baseline and the Retrieval v2 candidate are evaluated on the same queries. A quality PASS requires:

- candidate source-macro Recall@5 greater than the same-set baseline;
- at least `+2` net hit@5 cases;
- no Youth hit@5 regression;
- no Gov24 hit@5 regression.

Hard-negative evaluation is a paired safety check. Blocking conditions are only:

- candidate pure-positive gold hit@5 count lower than baseline; or
- candidate ineligible/excluded-policy top-5 intrusion count higher than baseline.

Absolute score distributions, score gaps, lexical overlap, and no-answer score separation remain diagnostics only and must not reintroduce a global abstention threshold.

Latency is judged by warm paired non-regression. Baseline and candidate are measured with the same environment, database/corpus, benchmark queries, and timed sample count, interleaved in the same run/window after warm-up. Cold/model-load samples are excluded. The primary latency gate is:

`candidate retrieval/search p95 <= paired D-003 baseline p95`.

The timed sample count must be fixed before results are inspected. p50 and sample count are recorded as diagnostics.

Final Retrieval v2 adoption is GO only when all mandatory checks pass:

1. final-holdout quality improvement;
2. `>= +2` net hit@5;
3. no Youth or Gov24 hit@5 regression;
4. both P0 regression gates PASS;
5. hard-negative paired safety PASS;
6. warm paired retrieval latency non-regression;
7. final holdout integrity preserved.

A fixable mandatory failure is HOLD. Clear quality regression or failure to improve on the final holdout is NO-GO.

A Retrieval v2 evaluation GO does not itself authorize production rollout. A passing candidate still proceeds through staging / no-traffic verification and a separate rollout decision.

This decision does not reopen cross-encoder reranking, a global similarity/abstention threshold, or public region search. Those remain governed by D-004.

## D-008 · Close Retrieval v2 evaluation cycle 1 as HOLD — 2026-08-30 (user-confirmed, recorded 2026-08-30)

Retrieval v2 evaluation cycle 1 closes as **HOLD** under D-007 because mandatory warm paired latency non-regression (D-007 §6) failed, despite quality / P0 / hard-negative PASS. Evaluation GO is therefore not granted and production rollout is not authorized.

Cycle-1 gate summary (re-execution prohibited; artifact/tag cross-verified only):

- Final holdout quality **PASS** — baseline 33/40 → candidate 36/40, source-macro 0.825 → 0.900, net +3, Youth 18/20 → 20/20, Gov24 15/20 → 16/20, losses 0. Tag `retrieval-v2-final-holdout-result-v1` (commit `d86e0119f9ac5cf3028364df24d898ff638d3b76`, candidate `retrieval-v2-candidate-v2` `5745cc3144b519da456b21030d0e0752d1d018ae`).
- P0 regression **PASS** — Youth 28/60, Gov24 16/21. Tag `retrieval-v2-p0-result-v1` (commit `3373da294b73705861b7a0e494ba802f9e9f6786`).
- Hard-negative paired safety **PASS** — pure-positive 15/21 → 16/21, excluded-policy intrusion 0/3 → 0/3. Tag `retrieval-v2-hard-negative-result-v1` (commit `34ca5a537f0a537b9217e3b2fffd005b80a5fe19`).
- Warm paired latency **HOLD** — baseline p95 476.51 ms, candidate p95 480.55 ms, delta +4.04 ms; D-007 requires `candidate p95 <= paired baseline p95`. Result tag `retrieval-v2-latency-result-v1` (commit `b04556f9251d6cabadd32c7c39c85dee690c8b48`). Measurement provenance blocker resolved via `retrieval-v2-latency-provenance-v3` (tag object `c0d2a9321114144b5ab4235a66c80faf6f112c57` → commit `3ac62181de9c343511adfb2db82cb0cc64b36009`); reviewer verdict APPROVE means provenance blocker resolved, not latency PASS. Latency numerical gate remains HOLD.

Consequences:

- `retrieval-v2-candidate-v2` and all frozen cycle-1 artifacts remain **immutable evidence**; no retuning, no threshold/gate relaxation, no rerun to manufacture PASS.
- The same cycle-1 holdout / P0 / hard-negative / warm paired latency benchmark is **not rerun or retuned** to seek PASS. D-007 is unchanged.
- No production rollout is authorized from cycle 1.
- A future cycle 2, if chosen (Q-004), is a **separate evaluation cycle** with a separately designed holdout frozen before tuning. It must not reuse the cycle-1 holdout to claim a new PASS and must not retroactively change the cycle-1 HOLD verdict. This HOLD record branch `codex/retrieval-v2-cycle1-hold-record` and tag `retrieval-v2-cycle1-hold-v1` are the durable closure marker.

Reconciled at `3ac62181de9c343511adfb2db82cb0cc64b36009` on branch `codex/retrieval-v2-latency-provenance-recovery`; provenance v3 peeled HEAD verified against remote. No benchmark/DB/model/embedding rerun was performed to produce this record.

## D-009 · Start Retrieval v2 evaluation cycle 2 — 2026-08-30 (user-confirmed)

User explicitly approved starting Retrieval v2 evaluation cycle 2. Q-004 resolved to start.

Contract continuity:

- D-003 (production retrieval contract), D-004 (rejected alternatives), and D-007 (evaluation contract) remain **unchanged and in force**.
- D-008 cycle-1 HOLD is **immutable**; no retroactive modification of verdict, gates, or artifacts.
- No threshold or gate relaxation.

Cycle-2 evaluation structure:

- Cycle 2 is a **separate evaluation cycle** with a **new independent holdout frozen before any candidate tuning**. Candidate tuning must not begin before holdout freeze.
- Cycle-1 final holdout, P0/hard-negative/latency results, and latency measurements are **not reused** to claim a new cycle-2 PASS.
- Latency gate remains `candidate retrieval/search p95 <= paired D-003 baseline p95` per D-007. Cycle 2 will perform a **fresh paired warm measurement** using the same D-007 methodology (same environment/DB/corpus/query set/timed sample count, interleaved in same run/window after warm-up, cold/model-load excluded, count fixed before inspection). Cycle-1 latency result is not re-measured or reinterpreted.
- Cycle-2 candidate must have its own separate freeze and ref (`retrieval-v2-candidate-*` independent of cycle-1).

Scope for this cycle-2 start session (holdout-builder only): create and freeze cycle-2 holdout before tuning; do not run benchmark/retrieval/search/DB ranking, do not load embedding/model, do not modify cycle-1 artifacts, do not tune candidate, do not relax D-003/D-004/D-007/D-008. This holdout-builder session is not reused for candidate tuning.

## D-010 · Disqualify Cycle2 holdout after HARD SEAL violation; bound Cycle2 to Exp4; defer future evaluation to new Cycle3 holdout — 2026-08-30 (Web/user-confirmed, standing decision)

Web/user 확정. Standing decision.

Reconciled base: branch `codex/retrieval-v2-cycle2-candidate` HEAD `13ba60c8872c6225dcaa8335293dd8c422083853` clean, `origin/codex/retrieval-v2-cycle2-candidate` 일치, actual remote `https://github.com/crushonyou2/benefit-compass.git` 일치. No retrieval/DB/model/embedding/holdout plaintext/`git show`/`checkout` executed in this decision-record session. Model `Muse Spark 1.2 Contributor / 매우 높음` verified.

(1) Cycle2 holdout (`retrieval-v2-cycle2-holdout-v1` tag object `03da4cc28d1bb324f5176efb500dfeaa1684b3fa` → commit `9e2cd6ea4b8203b474d7d6a6a69a088763284043`, evalset `eval/retrieval-v2/cycle2/holdout/evalset.jsonl` LF SHA256 `cf003bab7713138fbd9c4622addeeb886c01f401aeab3d43b1144ae6e4c79727`) is **disqualified for final evaluation**. Post-tuning candidate session에서 HARD SEAL이 금지한 process-level plaintext read (`eval/test_retrieval_v2_cycle2_devset.py::_load_holdout_items()`의 고정 ref `git show`)가 실제 발생했으므로, 화면/agent-visible 노출이나 retrieval/rank/score가 0이었더라도 final evaluation에 사용하지 않는다. `44ce287 fix(test): gate holdout plaintext audit behind explicit opt-in (HARD SEAL)` repair는 **재발 방지**이며 과거 seal 위반을 **소급 무효화하지 않는다**.

(2) Cycle2 frozen dev (`retrieval-v2-cycle2-dev-v1` tag object `500beadae11ddb423cc2ea4d46494c0a9f2b1173` → commit `372ed686579b4e8e2b9854d297e44fee18775352`, evalset `eval/retrieval-v2/cycle2/dev/evalset.jsonl` LF SHA256 `c8b66fef69bdfd0db053ac7cac0fb027fc3271c6072ab992b622cacdc71ace5e`, 36 cases Youth 18 / Gov24 18)는 **정상 tuning set으로 유지**하며 후보 개발에 계속 사용할 수 있다. Holdout disqualification은 dev의 tuning set 자격에 영향을 주지 않는다.

(3) Cycle2 candidate search는 **Exp4를 마지막 bounded experiment로 제한**한다. Exp4 **REJECTED면 Cycle2 candidate search 종료** (추가 Exp 없이). Exp4가 dev selection 조건을 통과하면 해당 candidate를 **고정**하고, 별도 **Cycle3에서 완전히 새로운 holdout을 tuning 전에 생성/봉인**한 뒤 그 candidate에 **추가 tuning 없이 평가**한다. Cycle3 holdout은 Cycle2 holdout과 독립적으로 설계·동결되며, tuning 시작 전 봉인 원칙을 준수한다.

(4) **D-003/D-004/D-007/D-008/D-009는 그대로 유지**; Cycle1 HOLD 불변; gate/threshold 완화 없음; 기존 Cycle2 holdout artifacts/tag는 **immutable history로 보존하되 final gate evidence로 사용 금지**. Cycle2 holdout 관련 tag/branch/commit(`retrieval-v2-cycle2-holdout-v1`, `codex/retrieval-v2-cycle2-holdout-freeze`, `9e2cd6e` commit)는 이력 보존이며, Cycle2/Cycle3 final holdout gate의 evidence가 될 수 없다.

No production/ml-service, eval data/artifacts/test code 수정 없음. No retrieval/DB/model/embedding/holdout plaintext access in this session. No new holdout 생성·봉인·평가가 본 결정 세션에서 수행되지 않음.
## D-011 · Adopt Retrieval v2 Cycle3 clean evaluation/candidate-search — fresh dev+holdout, pre-registration, isolation, audit log — close Q-005 — 2026-08-30 (user-confirmed standing decision)

사용자가 직전 Web 제안에 대해 '진행해라'라고 명시적으로 승인했다. 이를 Q-005 해결 및 D-011 사용자-confirmed standing decision으로 기록한다. Web cross-validation addendum(Exp1 post-result extra retrieval, Exp2 2회 premature+steering·폐기, Exp3/Exp4 premature+steering 확정, Cycle2 전체 `PROCESS_CONTAMINATED`)을 근거로 Cycle3를 clean cycle로 시작한다.

Reconciled base: branch `codex/retrieval-v2-cycle2-candidate` HEAD `d21c838b0cbd7da44dec3142d1de10a304e8c781` clean, `origin/codex/retrieval-v2-cycle2-candidate` 일치, actual remote `https://github.com/crushonyou2/benefit-compass.git` 일치, `git status --porcelain` clean, `git diff --check` PASS, working tree clean, local==origin==actual remote. No retrieval/DB/model/embedding/benchmark/holdout plaintext/`git show`/`checkout`/final holdout 실행 0 in this decision-record session. Model `Muse Spark 1.2 Contributor / 매우 높음(xhigh)` verified — HARD GATE 통과. decision/docs-only, no branch/tag/dev/holdout creation, no eval artifact/production/ml-service modification in this session.

(1) Retrieval v2 Cycle3를 **clean evaluation/candidate-search cycle**로 시작한다.

(2) Cycle2의 canonical metric/artifact(Phase1 28→30, Exp1~Exp4 30/36 REJECTED, `VALID_CANONICAL_RESULT`, 각 dev SHA `c8b66fef…`, holdout SHA `cf003bab…`, corpus `13589/17609`, production diff 0)는 **immutable historical diagnostic evidence로 보존**하되, Cycle2 candidate-search는 `PROCESS_CONTAMINATED`였으므로 **Cycle3의 candidate selection/final evaluation 근거로 재사용하지 않는다**. "충분히 탐색했다/더 좋은 후보 없음" 결론은 무효.

(3) D-010의 'Cycle2 dev 36(SHA `c8b66fef…`)를 tuning set으로 유지 가능'은 **역사적 결정으로 불변이나**, Cycle3에서는 더 보수적인 hygiene 경로를 채택하여 **Cycle2 dev 36을 재사용하지 않는다**. Cycle3에는 **fresh dev 36과 fresh holdout 40을 모두 새로 생성·동결**한다. Cycle2 dev/holdout artifacts/tag는 immutable history로만 보존.

(4) fresh dev와 fresh holdout은 모두 **candidate tuning 전에 독립적으로 생성·동결**하고, P0/cycle1 dev+holdout/cycle2 dev+disqualified holdout/hard-negative 및 서로 간 query+gold overlap 0을 **fail-closed 검증**한다. Holdout builder와 dev builder 세션은 candidate-tuning 세션과 분리한다. 본 결정 세션에서는 fresh dev/holdout 생성·봉인·평가·plaintext 접근을 수행하지 않는다.

(5) candidate 개발 전에 **후보 설계 공간과 최대 실험 수를 pre-register**한다. 이후 Web은 Paseo 작업 중 중간 steering/검증을 하지 않고 **Paseo의 체크리스트와 최종 보고가 모두 완료된 뒤에만 독립 교차검증**한다. **HARD GATE/보안·seal 위반만 예외적으로 즉시 중단 가능**하다.

(6) Cycle3부터 retrieval 실행 및 protected-set 접근에 대해 **append-only run/access audit log**를 도입하여 프로세스 실행 횟수, 시작/종료, candidate id, dev/holdout access 여부를 durable하게 남긴다. **final holdout plaintext는 candidate freeze + independent review + 사용자 명시 승인 전 접근 금지**한다.

(7) **dev에서 사전등록 selection 조건을 통과한 후보만 freeze**하고 independent review 후 **fresh holdout에서 추가 tuning 없이 D-007의 7 mandatory gates**(quality improvement, +2 net, no Youth/Gov24 regression, P0 PASS, hard-negative PASS, latency non-regression, holdout integrity)를 평가한다.

(8) **D-003/D-004/D-007/D-008/D-009/D-010 및 Cycle1 HOLD는 역사/계약으로 유지**한다. gate/threshold 완화 없음. production rollout은 별도 결정이다.

No production/ml-service, eval data/artifacts/test code 수정 없음. No retrieval/DB/model/embedding/benchmark/holdout plaintext 생성·접근·`git show`/`checkout` in this session. No new branch/tag/dev/holdout 생성·봉인·평가가 본 결정 세션에서 수행되지 않음. Q-005 closed → D-011.
## D-012 · Record Retrieval v2 Cycle3 closure without holdout — zero DEV_SELECTABLE (canonical one-shot count=1) — 2026-09-01 (user-confirmed, Web independent result/provenance review PASS; mechanical closure before Git hygiene)

User explicitly said '진행해라' after Web proposed D-012 + archival closure tag before cleanup. This records the mechanical Cycle3 closure as append-only (no branch/tag deletion, no rerun, no holdout access).

Reconciled base: branch `codex/retrieval-v2-cycle3-candidate` HEAD `a6a232c93115647c0716a6ccd97a7d8e2a2ef4be` clean, `origin/codex/retrieval-v2-cycle3-candidate` identical, actual remote `https://github.com/crushonyou2/benefit-compass.git` identical, `git status --porcelain` clean, `git diff --check` PASS; `main`/`origin/main` `9048347caed1074619763c51bcbc4e35e7e60363`; ROOT HARD GATE `Muse Spark 1.2 Contributor / xhigh (very high)` verified; configured delegated roles preserved. No canonical dev rerun, retrieval, DB/model/embedding/benchmark/latency execution, no final holdout access/evaluation/plaintext, no production `ml-service` behavior change, no prereg/candidate/K/threshold/selection change, no history rewrite/amend/rebase/squash/reset, no `git show`/`cat-file` of protected plaintext in this decision-record stage. Canonical result and audit bytes/SHA/event count verified unchanged before/after this stage (see validations).

(1) Cycle3 canonical dev one-shot was executed **exactly once**; durable execution/result commit `a6a232c93115647c0716a6ccd97a7d8e2a2ef4be` on `codex/retrieval-v2-cycle3-candidate`; **Web independent result/provenance review PASS** on that commit. Canonical execution count remains **exactly 1 forever** (no rerun under any circumstance).

(2) Frozen dev identity SHA `3791368f4722b612058b7a005e17bf5f1caae4ac0437daa9d44ff28f28ca260c` (`eval/retrieval-v2/cycle3/dev/evalset.jsonl` canonical LF, `retrieval-v2-cycle3-dev-v1`); canonical result SHA `de5d46ae600668f610b5453d52396bafdbf0b8fa1946cfdff0710ab3c3921433` (`eval/retrieval-v2/cycle3/canonical-dev/canonical-dev-result.json`, schema 1, batch `cycle3-canonical-dev-v1`, `prereg v1` `18b6c997eb71a8cdff36d84ff46b5bbb6b699874ff6d0fccd18636f00268e156`, `git a7a8b93 dirty True`, `corpus 13589/17609`); audit chain `16 -> 20` with **exactly one** canonical `run_start` (`1d9cdbe917253ab79b68cb51eda712d5225891067d5e19559f801139326a4d0b`) / `run_end` (`9339790a9731487fd3208955342ee252fa1a601b063a54d4f222918075c0f21a`) and **exactly one** dev `protected_access_start` (`74c35e23fe2f91e323ecf6171fa0994cac31f4332663e498d98e6eafe1bec77b`) / `protected_access_end` (`ea7fd2dcf0690812aaae3851f4277891e3c38a7a8892b2c6bd5da451eee3432d`) for execution session `cycle3-canonical-dev-9ee016db7048-20260901`; **no holdout access** in canonical execution (holdout plaintext absent/unread, holdout access events 0, `verify_holdout_access_allowed` not invoked for holdout).

(3) Baseline and all candidates on same fresh dev 36 (Youth 18 / Gov24 18): `baseline hit@5 36/36 recall@5 1.0 source-macro 1.0 Youth18/18 Gov24 18/18 mrr@10 1.0`; `c3e1-vector-pool-128 hit@5 36 macro 1.0 Youth18 Gov2418 net 0`; `c3e2 K256 hit@5 36 macro 1.0 net 0`; `c3e3 K512 hit@5 36 macro 1.0 net 0`; per-candidate checks `macro_gt false` (1.0 not >1.0), `net_ge_2 false` (0), `youth_no_regression true`, `gov24_no_regression true` -> `quality_selectable false` each -> `quality_selectable set = []`; prereg boundary `latency {baseline:null,c3e1:null,c3e2:null,c3e3:null} latency_diagnostics quality_only true, timed_count_fixed_before_inspection true` — latency applies only to quality-selectable, therefore **not measured** (boundary, not failure); `DEV_SELECTABLE = []` (quality-selectable [] intersect latency PASS [] = []); `selected_candidate = None`; tie-break not used.

(4) By frozen prereg (`docs/RETRIEVAL_V2_CYCLE3_PREREG.md` section 8, `prereg-v1.json` `18b6c997...`) / D-011 rule, **zero `DEV_SELECTABLE` closes Cycle3 WITHOUT holdout**. No candidate freeze, **no holdout evaluation/access**, no further Cycle3 experiment/rerun. Final holdout (`retrieval-v2-cycle3-holdout-v1`, `4c631ce7cdcc03374bb1861d0a27e0ebbacf35a691fb6f54543b96c7f051c350`, 40 Youth20/Gov2420, catalog union 248) **remains sealed/unused historical evidence** — not accessed, not evaluated, not used for selection; holdout integrity preserved.

(5) Production retrieval/adoption is **NOT changed** by this closure; `D-003`/`D-004`/`D-007`/`D-008`/`D-010`/`D-011` history/contracts remain in force as applicable (no threshold/gate relaxation, no production rollout authorized, no candidate adoption). **D-012 does not authorize deletion of provenance refs**; Git cleanup (branch deletion, remote ref deletion, worktree deletion/prune, baseline archive tags) is a **separate** future stage and requires fresh Git-metadata-only CAS checks. No canonical result or audit events are modified (bytes/SHA/event count immutable).

No production/`ml-service`, eval data/artifacts, prereg, test code modified beyond this decision record + docs/SESSION-LOG durability entries and the archival closure tag `retrieval-v2-cycle3-closure-v1` (separate step, points to D-012 closure commit, not to `a6a232c`). No new branch/tag/dev/holdout creation, no eval execution, no holdout plaintext `git show`/`cat-file`/`checkout`/`restore` in this stage.

## D-013 · Start Retrieval v3 User Search Quality — user-satisfying search program — 2026-09-01 (user-confirmed)

User explicitly confirmed start of Retrieval v3 User Search Quality on branch `codex/retrieval-v3-user-search-quality` from base `5327661445c37191a3fd61db195f3af4d2cf893a` / tag `retrieval-v2-cycle3-closure-v1` (D-012 closure). This is a user-satisfying search program bootstrapped from the durable v2/Cycle3 closure. V3 evaluation contract was open at bootstrap and is now defined as a standing decision via this D-013 plus bootstrap prereg `docs/RETRIEVAL_V3_PREREG.md`.

Reconciled base for this decision: branch `codex/retrieval-v3-user-search-quality` HEAD `257183f106c39ffee4aae1e52b8587c1d9db97c0` clean (prior HOLD commit), base `5327661`, remote v3 branch absent, Web HOLD for wrong file scope and omitted D-013/Q-006/prereg verified; this repair is append-only (no rewrite/amend/reset/rebase/squash of `257183f`).

Goal: user-satisfying search — representative answerable user-intent Success@5.

Release gates:

- Headline (answerable tasks on representative user intent): **Success@5 >=85% is the release floor; >=90% is a strong/stretch target, not promised.** Both thresholds apply to headline answerable Success@5 (grade>=2) on a representative held-out benchmark.
- Supporting gates (diagnostic / required before release, not headline): Top1 / Top3 / MRR / NDCG; no-answer / ambiguity safety; ineligible / expired intrusion; official-link validity; latency / cost.

Evaluation design / pilot before implementation: no candidate tuning or protected evaluation begins before evaluation design is fixed and a retrieval-blind pilot validates labelability/answerability/ambiguity/strata/annotation disagreement (see prereg). Final benchmark frozen before tuning.

Primary candidate family (fielded): **sparse+dense hybrid + exact title/org/entity + field weighting + duplicate/diversity**. This is the primary family to be fielded and tuned (sparse+dense union/hybrid — Postgres FTS / BM25-equivalent as feasible — plus exact title/org/entity plus field weighting plus duplicate/diversification). No v2 K/threshold/source-bias sweep continuation.

Optional lightweight reranking: **only after materially new v3 evidence shows high first-stage recall yet ranking still limits, not an old cross-encoder re-enable.** Candidate B — optional lightweight ranker — is permitted only if first-stage oracle Recall@100 >=95–97% and ranking still limits. Embedding replacement / LLM rewrite / judge is last resort / out of initial scope.

Decision scope and supersession:

- D-013 supersedes D-004 **only for conditional reranking reconsideration** (lightweight reranking may be reconsidered only under the high-recall condition above); global abstention / public region search remain not adopted (D-004 otherwise in force).
- No rollout is authorized by D-013.
- v2 / Cycle3 sets/results (frozen devs/holdouts, canonical results, tags, audit chains) are **immutable history / regression only, not v3 tuning data**. They must not be reused as v3 tuning/selection evidence. D-003 / D-007 / D-008 / D-010 / D-011 / D-012 remain history/contracts as applicable; D-007 is historical v2 contract, v3 latency budget pending Q-006.

No production/`ml-service`, eval data/artifacts, retrieval/DB/model/embedding/benchmark/latency execution, or protected dev/holdout/canonical plaintext per-case access in this decision session. No branch/tag deletion, no history rewrite.
## D-014 · Close Q-006 — Retrieval v3 final benchmark sizes, CI/precision rule, paired latency budget, final pilot/annotation protocol — 2026-09-01 (user-authorized, retrieval-blind pilot evidence only)

User-authorized closure of Q-006 **before any Candidate A/B implementation**, based **only** on retrieval-blind pilot `retrieval-v3-pilot-100-v1` evidence and statistical/design reasoning. No retrieval/DB/model/embedding/benchmark/latency execution, no protected dev/holdout/canonical plaintext via `git show`/`cat-file`/`checkout`/`restore`/`sparse`/`worktree`/path traversal, no system retrieval output inspection, no candidate implementation or production `ml-service` behavior change in this closure session. Pilot 100 provenance: `eval/retrieval-v3/pilot/pilot_tasks.jsonl` SHA256 `b3250e592d4c80099e29d20d1bf87594f2bac11a59907ac8067d3e1ddbd65da3`, `pilot_report.md` SHA256 `f3a01a5f286705df9e9ca6cc8cf6d5fd320a427093649072bc1d5f559e6c669f`, `pilot_provenance.json` SHA256 `64f2dbecb49cf624e0e6b05d84f4c3e1db8876406b473b18ed7526078920b2d2` — single annotator + independent reviewer (prereg-permitted pilot alternative, no fabricated second human annotator), 99% labelable / 85% answerable raw (84/99 84.8% among labelable) / 13% ambiguous / 30% location-bearing / 7% disagreement (93% agreement) with adjudication residual 0, strata all ≥10, instruction revisions durable in pilot report §6.

### (1) Final benchmark sizes (frozen before tuning; exact, inclusive of unsupported)

- **Pilot 100** (this stage, retrieval-blind labelability only): already executed — `12/14/12/12/10/12/13/15` per stratum (exact/natural/exploratory/multi_constraint/short/colloquial/ambiguous/unsupported), location-bearing 30, no system results.
- **Dev (tuning/diagnostics): `160 total tasks`** inclusive of unsupported. **Holdout (final one-shot): `220 total tasks`** inclusive of unsupported. Totals are exclusive of each other and of all v2/Cycle3 history (union 248) — fingerprint overlap 0 required at freeze.
- **Per-stratum minimum allocations (exact minimum per stratum, sufficient for per-stratum diagnostics):**
  - Dev 160: `exact_navigation ≥18, natural_needs ≥22, exploratory_multi_valid ≥18, multi_constraint ≥22, short_keywords ≥15, colloquial_typo_spacing_abbrev ≥18, ambiguous ≥18, unsupported_no_answer ≥29` (sums to 160; any excess stays within these minima).
  - Holdout 220: `exact_navigation ≥25, natural_needs ≥30, exploratory_multi_valid ≥28, multi_constraint ≥32, short_keywords ≥22, colloquial_typo_spacing_abbrev ≥25, ambiguous ≥28, unsupported_no_answer ≥30` (sums to 220).
  - **Location-bearing separately:** at least **25% and at most 35%** of each benchmark (dev 40–56, holdout 55–77) must be location-bearing, distributed across strata (not isolated to one stratum), evaluated both as pooled headline and as separate location vs not slices.
  - **Diagnostics slices (not separate strata, but reported per-slice Success@5):** source (Youth/Gov24), category (6-way: housing_finance/family_care/employment_education/welfare_health/culture_community/business_agriculture), freshness (stable vs fresh), common-vs-rare (frequent vs infrequent policy). Each category/common/rare slice has ≥12 tasks in holdout for gross bias detection.
- **Answerability uplift:** pilot observed 85% raw answerable (≈84.8% among labelable). Dev expected answerable-labelable ≈136 (160×0.85), holdout expected ≈187 (220×0.85). **Holdout minimum answerable-labelable ≥180** and **dev ≥130** are required after excluding unlabelable/unsupported; if pilot unlabelable rate (1%) recurs, total tasks include that uplift (160/220 already include 1–2% labelability slack). Unsupported/no-answer tasks (≥29 dev, ≥30 holdout) have **no grade 2/3 golds** and are scored under safety gates, not headline denominator.

### (2) Confidence / precision rule for the ≥85% headline floor

- **Headline metric:** **Success@5 grade≥2 on labelable-answerable tasks only** (retrieving any grade-3 or grade-2 equivalence-group member in top-5 counts as success). Unsupported/no-answer and unlabelable are excluded from headline denominator and scored separately under safety.
- **Interval:** **95% Wilson score interval** (no continuity correction) reported for headline Success@5 on holdout answerable set; Clopper-Pearson exact as sensitivity. Wilson is primary for sizing and for the HOLD gate below.
- **Design precision (sizing rationale):** benchmark sized so that **expected Wilson half-width ≤5.5 pp when observed p=0.85** and **≤5.0 pp when answerable n≥190**. For `p=0.85`: `n=136 → half 6.0 pp`, `n=180 → 5.2 pp`, `n=187 → 5.0 pp`, `n=196 → 4.9 pp`, `n=250 → 4.4 pp` (Wilson). Holdout 220 total → expected answerable ~187 → expected half ~5.0 pp, meets `≤5.5 pp` design target; dev 160 → expected 136 → half ~6.0 pp for diagnostics.
- **Gate (no post-result tuning loophole):**
  - **PASS** iff **point estimate ≥85%** on holdout answerable set **and** **Wilson 95% lower bound ≥80%** (precision gate). Example: `n=187, p=0.85 → Wilson [79.3%, 89.4%] → lower 79.3 <80 → HOLD (not PASS)`; `n=187, p=0.86 → [80.4%, 90.3%] → PASS`. This prevents passing on lucky variance with modest n while keeping the headline floor at 85% point estimate.
  - **Strong/stretch ≥90%** is reported aspirational, not gated; if `p≥90%` and Wilson lower ≥85%, noted as **strong**.
  - **HOLD** = point ≥85% but lower <80% (insufficient precision), or marginal secondary/safety HOLD. **NO-GO** = point <85% or safety regression. No rerun or threshold relaxation after the one-shot holdout is evaluated.
- **Per-stratum diagnostic precision limitation (documented):** with holdout per-stratum n≈22–32, per-stratum Wilson half-width at `p=0.85` is **±9–14 pp** (e.g., `n=25 → ±13.8 pp`, `n=32 → ±12.2 pp`); with n=15 → ±15–17 pp. Per-stratum diagnostics therefore detect **only large gaps (>18–20 pp)** and are **not gated** as release floors. This is an explicit limitation of the chosen sizes; claiming per-stratum 85% floors would require `n≥60` per stratum and is out of scope.

### (3) User-centered paired latency / cost budget (replaces D-007 latency for v3; D-007 remains history for v2)

- **Scope:** end-to-end **user search** (candidate family A: sparse+dense hybrid + exact title/org/entity + field weighting + duplicate/diversity; if Candidate B reranker is later admitted, its cost is included).
- **Method (paired, warm, non-regression design):** same environment, same DB/corpus, same benchmark query set, same timed sample count **fixed before inspection**, interleaved in same run/window after warm-up; cold/model-load samples excluded; `CANDIDATES`/`COSINE_MIN` etc per candidate definition; timed sample count = **150 queries per variant interleaved (300 total runs) + 30/variant warm-up excluded**, or the holdout answerable set if larger and feasible — count fixed before results. Interleaving eliminates host drift. Report `p50/p95/p99` and sample count.
- **Primary latency gate (paired vs D-003 production baseline `RERANK=0, CANDIDATES=30, COSINE_MIN=0.78, LEXICAL_BIAS=0.01, strip_region, youth bias suppressed for Gov24 orgs, intfloat/multilingual-e5-base`):**
  - **`candidate p95 ≤ paired baseline p95 + 80 ms` AND `candidate p95 ≤ 700 ms` absolute** — both must hold. Rationale: v2 paired baseline p95 ≈476–487 ms (warm); +80 ms ≈ +16–17% allows hybrid exact/field-weight/diversity overhead while keeping user-perceived latency <700 ms (headroom for network). If baseline p95 shifts, the relative +80 ms gate moves with it; absolute 700 ms is a user-centered ceiling.
  - **Secondary (diagnostic):** `candidate p50 ≤ baseline p50 + 50 ms` (or ≤10% regression) reported; not a hard fail unless gross.
- **Cost gate (diagnostic before release):** index size ≤2× baseline corpus index, per-query DB scanned rows ≤3× baseline `CANDIDATES` scan, no extra external model calls beyond the fielded embedding model unless Candidate B is admitted.
- **No D-007 `candidate p95 ≤ baseline p95` strict non-regression is carried to v3** — v3 hybrid family is inherently higher-cost than pure vector; D-013 authorized hybrid as primary fielded family and Q-006 now defines this paired +80 ms / 700 ms budget explicitly. D-007 remains historical contract for v2/Cycle3 only.

### (4) Final pilot / annotation protocol (explicit, retrieval-blind, before freeze)

- **Pilot (this stage, already executed):** **single annotator + independent reviewer** (prereg-permitted alternative) — no fabricated second human annotator. Reviewer re-labeled 100% for strata/answerability/ambiguity/location-bearing and **30% stratified subsample (n=30)** for grade (3/2/1/0) and equivalence-group; disagreements adjudicated by reviewer; final labels durable in `eval/retrieval-v3/pilot/pilot_tasks.jsonl`. Multi-gold graded 3/2/1/0 + equivalence-group semantics preserved; unsupported queries have no grade 2/3 golds. Forbidden actions count 0 (above). Pilot artifact/report/provenance are SSOT for this stage.
- **Final benchmark annotation (dev 160 + holdout 220, frozen before tuning):** **two independent annotators + adjudicator** for every query. Annotators independently assign: strata, location-bearing, answerable vs unsupported/no-answer, ambiguous vs unambiguous + ambiguity type, per-gold grade (3/2/1/0) and equivalence grouping (equal-acceptability groups at same grade). **Inter-annotator agreement reported** (raw agreement + Cohen's κ for strata/answerability/ambiguity and per-gold grade). **All disagreements adjudicated** by third adjudicator; residual 0 after adjudication. **Instruction version** is the revised instruction post-pilot (§6 of pilot_report.md) including contradictory-query exclusion, ambiguity handling (clarification vs safe abstention), and exploratory equivalence-group rule. No system retrieval output is shown to annotators at any time (retrieval-blind). Each benchmark is frozen before candidate tuning, with fingerprint-only overlap checks against all prior v2/Cycle3 history (union 248) and between dev↔holdout (0 required) before tuning begins.

### (5) Rationale, limitations, and next-stage boundary

- **Why 160/220:** pilot observed labelability 99%, answerability 85%, ambiguity 13%, 30% location — sizing adds 15% unsupported + 1% unlabelable slack. Holdout 220 (≈187 answerable) achieves Wilson 95% half-width ≈5.0 pp at 85% (design ≤5.5 pp) and lower-bound gate ≥80% is reachable at p≈86% (not at exactly 85% with n=187: lower 79.3% → HOLD, protecting against borderline pass on variance). Dev 160 (≈136 answerable) gives tuning diagnostics half ≈6 pp. Per-stratum holdout n≈22–32 gives per-stratum half ≈10–14 pp — sufficient for large bias detection, explicitly **not** precise per-stratum floor claims. Larger holds (e.g., 300) would achieve half <4 pp and lower-bound ≥80% at 85% exactly (n≥250) but annotation cost (510 tasks with dual annotation + adjudication ≈1020 annotations + 510 adjudications) is not justified for an 85% floor with a 5 pp tolerance. The chosen 160/220 is the **minimum defensible** that meets the `≤5.5 pp` design while keeping annotation tractable. Choosing smaller (e.g., v2's 40) would give half ≈11 pp and cannot credibly claim an 85% floor — hence v2 sizes are not reused.
- **Location, category, common/rare slices are diagnostics, not gates** — reported with Wilson CIs but no release floor; a >20 pp gap triggers investigation, not automatic NO-GO, unless coupled with safety or headline failure.
- **This D-014 does NOT authorize** candidate implementation, dataset freeze, protected-set plaintext access, retrieval/benchmark execution, or production change. Next stage is **FINAL prereg freeze** (this commit), then **isolated dataset freeze(s)** with fingerprint-only overlap checks, then **runner implementation + independent review**, then **one-shot final holdout** — each is a separate stage with the gates in §9 of the FINAL prereg.

No new branch/tag creation, no history rewrite, no protected-set `git show`/`cat-file`/`checkout`/`restore`/`sparse`/`worktree` access beyond possibly the builder sessions that will later be isolated and audited. Production `ml-service` diff remains 0.
