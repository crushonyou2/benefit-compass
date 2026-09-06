# Retrieval v3 D-103 — generation-v9r14 PRE-SMOKE Web PASS

Date: 2026-09-06
Stage: fresh successor PRE-SMOKE build + independent Web review only
Generation: `retrieval-v3-dev-generation-v9r14`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260906-v9r14`

## Verdict

**WEB PRE-SMOKE PASS.** Generation-v9r14 is the fresh successor to D-102/v9r13. It repairs only the lifecycle-smoke output-completion dependency that invalidated v9r13. No model smoke, real freeze, Phase C, source-truth snapshot, semantic role, selector, protected evaluation, holdout evaluation, or production change occurred in this stage.

The next logical gate is exactly one Smoke A on these exact final bytes. Only if Smoke A passes may exactly one Smoke B run. Either smoke failure closes v9r14 as CONTRACT_INVALID_GENERATION with no retry or same-generation repair.

## Reconciled base

Before executor launch, actual repo state was independently reconciled:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD/local/upstream/direct remote `8de5cd65eb42113dd1337f474ca20002ea300472` (D-102), commit time `2026-09-06T23:47:18+09:00`
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing production base = 0 files
- audit `eval/retrieval-v3/audit/events.jsonl`: 4 events, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- canonical `eval/retrieval-v3/result`, `dev`, `holdout`, `dev-v2` absent
- OMP `18.1.5`; effective modelRoles default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`
- latest durable decision D-102
- v9r14 destination absent before write

No `git show`, `git cat-file`, checkout/restore, sparse protected-data recovery, or protected plaintext reconstruction was used in this stage.

## Executor provenance

Single Paseo/OMP root:

- agent `6fa4404e-dbb2-4939-8697-6c0dcf7f80e9`
- title `D103-v9r14-presmoke-builder`
- provider/model `omp` / `opencode-go/muse-spark-1.3-contributor`
- thinking `xhigh`
- cwd exact repo root
- ParentAgentId null
- final status idle
- no subagents
- executor instruction file SHA256 `6b572d611448c8b962c61c3120649324c036755fd122a5e9c61e0d7efd3a910b`

Independent transcript inspection counted 196 executor tool calls and found zero actual `paseo run` commands, zero direct `run_lifecycle_smoke.py` executions, and zero Phase-C execute commands. Paseo daemon listing after completion had exactly one v9r14-related agent: this PRE-SMOKE builder root. No v9r14 Smoke-A/B staging roots exist.

## Fresh identity and preserved evaluation contract

- builder: `bc-v3-dev-v2-builder-20260906-v9r14`
- final source/support files: 65
- generation `retrieval-v3-dev-generation-v9r14`
- seed `benefit-compass-retrieval-v3-dev-v2-generation-v9r14-2026-09-06`
- candidate IDs `v3g9r14-001..360`
- C IDs `v9r14c-001..360`
- scripts `freeze_plan_v9r14.py`, `carry_exclusions_v9r14.py`
- hold/base provenance is D-102 `8de5cd65eb42113dd1337f474ca20002ea300472`, with freeze chronology required to be later than the base commit
- same TEN exclusion sets exactly; D-102 produced zero candidate/query rows, so no eleventh set
- rubric, retrieval/evaluation semantics, counts, A/B/C annotation authority, candidate-plan values and selector semantics remain unchanged

Normalized v9r13→v9r14 comparison paired all 65 files with no unpaired file. Fifteen files remained non-identical after generation-token normalization, all confined to authorized lifecycle proof, lineage/SHA pinning, old-generation deny lists and tests:

`GENERATION_PLAN.json`, `audit_lifecycle_smoke.py`, `carry_exclusions_v9r14.py`, `coord_wrapper_tpl/coord_omp_wrapper.py`, `coord_wrapper_tpl/phasec_role_ext.ts`, `freeze_plan_v9r14.py`, `input/EXCLUSION_INPUTS.json`, `probe/role_tools_probe.mjs`, `role_fs_helper.py`, `role_omp_wrapper.py`, `run_lifecycle_smoke.py`, `smoke_lifecycle_prompt.txt`, `test_lifecycle_smoke_contract.py`, `test_phasec_confinement.py`, `test_role_tools.py`.

No retrieval/evaluation semantic implementation file entered that delta set.

## Authorized lifecycle-smoke repair

D-101/v9r13 made the deny triple deterministic, but D-102 Smoke B still depended on the model performing six separate `role_write_chunk` calls; the model called `role_smoke_probe`, proved all three denies, then final-stopped with zero chunks.

v9r14 removes that six-step model dependency only:

1. `lifecycle_smoke` custom surface is narrowed to built-in `todo` plus lifecycle-only `role_smoke_probe`. Authors retain five real role tools; reviewers/C retain four. Real roles do not receive the smoke probe, and their `role_write_chunk` behavior is unchanged.
2. `role_smoke_probe {}` has an empty schema and no model-supplied path/resource/line arguments. In one model tool call it executes the fixed helper sequence:
   - deny cross-role read `packet`
   - deny unknown-resource `../outside.json`
   - deny bad-target write `out/evil.jsonl`
   - exactly six allowed helper writes `out/chunk_0.jsonl` … `out/chunk_5.jsonl`, each exactly one canonical `smoke-i` row, using the same frozen helper write path/schema/ID validation used by real `role_write_chunk`
   - any unexpected success/deny, malformed receipt, duplicate, wrong row count, or helper failure fails closed
   - success returns `EXPECTED_DENIES_AND_OUTPUTS_PROVEN` with the fixed deny list and six receipts.
3. The lifecycle prompt is reduced to: call the deterministic probe exactly once, verify six receipts, then emit `LIFECYCLE_SMOKE_DONE`; no model-directed read/write sequence and no retry.
4. The frozen lifecycle auditor permits transcript tools only `{todo, role_smoke_probe}`, requires probe exactly once and model `role_write_chunk=0`, requires exactly nine access-log rows (three expected denies exactly once each + exactly one allowed helper write for each six chunk targets), exact 6x1 outputs, terminal stop, descendants zero and fallback proof. Extras/unknowns fail closed.
5. `role_completion_gate.py` remains responsible for exact outputs + final stop + stable quiescence. Real role output shapes are not weakened.
6. v9r12 PATH + `OMP_WRAPPER_LOG` generic-launcher reachability repair remains preserved.

## Independent Web validation on final bytes

Web did not rely on executor self-report. It re-read final mechanics and independently reran the non-model battery:

- lifecycle contract: `LIFECYCLE_CONTRACT_PASS`, 53 checks
- launcher reachability: `REACHABILITY_PASS`, 87 checks
- role tools: `ROLE_TESTS_PASS`, 166 checks; live Bun probe showed authors five tools, reviewers/C four, lifecycle exactly `role_smoke_probe`
- role completion: `GATE_TESTS_PASS`
- TEN gates: 45 pairwise comparisons, overlap 0; counts 180/250/248/273/273/360/360/365/360/360
- confinement: `CONFINEMENT_TESTS_PASS`, 182 checks; printed CONTRACT_INVALID rows were intended negative-case fail-closed tests
- `compileall` PASS
- Bun role-tools probe PASS
- Bun coordinator/Phase-C probe PASS
- TypeScript `tsc --noEmit` PASS
- final plan mechanics map: 52/52 exact SHA+byte matches

One Web TEN-test invocation initially failed before semantic checks because the caller shell's Windows default cp949 decoder could not decode `history_catalog.json`. The test was rerun with standing Windows Python UTF-8 mode `PYTHONUTF8=1` and passed all 45 overlap gates/exact counts. `test_ten_set_gates.py` is semantically unchanged from v9r13: after v9r14→v9r13 identity normalization its full text is identical (158 lines). This was an execution-environment decode issue, not a gate/semantic failure.

Web tests created only Python cache files inside the private v9r14 builder. Exact-path cleanup removed two `__pycache__` directories / 34 `.pyc` files; final counts are zero. No home synthetic test temp remained.

## Final key SHA256

- `GENERATION_PLAN.json` `418c6d875523a9c2753ba946a52bd0bc5ab7e88f473c15641d988b3158dce404`
- `launch_top_level_paseo.py` `42508cfddea9b413fef18c3df9f45e6c73110fbf69ccf85444e06e222a441b46`
- `role_omp_wrapper.py` `a4b43e220d0ee11754a5f766a71ed68af3e02f224a5bbb839a85a7de7cf761c0`
- `role_fs_helper.py` `094d1479a7d345d888991e143e5be4f3525042f8821eddc9acd7d494d01ccada`
- `coord_wrapper_tpl/phasec_role_ext.ts` `a9f14e4f9f972d14268e94bf563cb7d77528b81d9a0cec3d8daf9539576a7dd6`
- `run_lifecycle_smoke.py` `967eb103caf970d9874ca31313a0532fa0c7af45d3b6050ada5c4b40f2f15610`
- `audit_lifecycle_smoke.py` `35b085568e5a210ee9139669102c96c3452c10a822affd9b21785531654d333e`
- `smoke_lifecycle_prompt.txt` `7948fc4245a7604fa0e8f52c46e1f37cd5216b11cf230dd32497f2bd0d7508ca`
- `role_completion_gate.py` `2608dd9edb84b6b5ba32f29a207f18e3a882bad4387fc00db0724e714fb91a8e`
- `test_launcher_reachability.py` `f197e10e7c069c82509775a503bddc084b3c997e438233f5dbc819cac1083627`
- `test_lifecycle_smoke_contract.py` `34bfae893bdea36234ae18659dc436c37b3522be1af7413a71d3dce242da1445`
- `freeze_plan_v9r14.py` `543020bd584604cba27fbe4acf0b7825060b2229b106bfaa18eb9e7691868144`
- `carry_exclusions_v9r14.py` `10f88069f759cc19d7827f7344427d729e08bd7fc38958f650a4f020543049de`
- `input/EXCLUSION_INPUTS.json` `d3dc464db16667c5da0ae51767f92f1aec2d98324b2feb3bafe21abd337202bd`
- `coord_wrapper_tpl/phasec_coordinator_ext.ts` `2e8b2478fd78204b00ed51a8f43d32c2405a30c5ad97510b14d126f6c19067ca`

## Predecessor immutability and no-real-freeze boundary

All eight checked v9r13 key hashes remain exactly D-101 values. Both consumed v9r13 smoke sessions were rehashed with shared read access and remain exact:

- Smoke A `4ba535423aaf9255d5c7aa26469a15577c4b9b9540ce2e661239d0bbbdad66bb`
- Smoke B `442a96b077c01c7dbb23b521ad0105dcef25be6578ab1776a79300bdb327062d`

Real v9r14 builder final state:

- no `PLAN_LOCK.json`
- no `FROZEN_HASHES.json`
- no `phasec_driver.run.lock`
- no `source_truth.jsonl` / `source_truth_meta.json`
- no `evalset.jsonl`
- no builder `out/`
- no candidate/reviewer/C/selector runtime outputs
- no v9r14 Smoke A/B staging roots
- no v9r14 branch, tag, or worktree
- repo remained clean and unchanged at D-102 throughout executor/review

## Next gate

D-103 authorizes only the next smoke stage on these exact bytes:

1. exactly one Smoke A;
2. only if A independently passes, exactly one Smoke B;
3. no retry, no same-generation repair;
4. no real freeze or Phase C until both one-shot smokes pass and a subsequent Web gate authorizes the transition.
