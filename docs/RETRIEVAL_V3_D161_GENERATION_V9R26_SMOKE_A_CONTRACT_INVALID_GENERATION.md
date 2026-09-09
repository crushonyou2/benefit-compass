# Retrieval v3 D-161 — generation-v9r26 Smoke A CONTRACT_INVALID_GENERATION

Date: 2026-09-09
Stage: exactly-one authorized Smoke-A one-shot execution (consumed, target rc1) + closure recording (no retry, no correction)
Generation: `retrieval-v3-dev-generation-v9r26`
D-160 closure base commit: `9d1a331ba956e0f42106ce9cabc4283d947321f3`

## Verdict

**D-161 / v9r26 = CONTRACT_INVALID_GENERATION / HARD HOLD / NON-RESUMABLE.**

The authorized Smoke-A one-shot was consumed by actual tool use plus terminal stop and target rc1. Absence of coordinator launch does NOT permit retry under the frozen v9r26 contract. No same-generation correction/retry/second smoke or root delete/recreate. No Smoke B, real freeze, source snapshot, Phase C, semantic roles, selector, protected evaluation, holdout, production change, or canonical audit append occurred in D-161.

STOP. A future separate user `진행해` may only start a fresh successor generation; this closure starts none.

## Reconciled base and environment

Immediately before D-161 execution, Web-verified:

- base `9d1a331ba956e0f42106ce9cabc4283d947321f3`, repo/upstream/origin clean/equal
- production `ml-service/` diff from standing baseline = 0
- canonical `eval/retrieval-v3/audit/events.jsonl` 4 rows / SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/dev-v2/`, `eval/retrieval-v3/holdout/` absent

## Pre-gate (static, no runtime)

- v9r26 mechanics 67/67 exact; cache dirs 0 / pyc 0
- one-shot terminality regression 24/24; Paseo CLI gate 64; reachability 87; registry scan 37 — all PASS
- downstream artifacts absent: no PLAN_LOCK / FROZEN_HASHES / run lock / source truth (+meta) / anchors / slots / authors / `candidates_merged`

## Execution (exactly one authorized one-shot, consumed)

- Execution executor `804d7142-be0c-4951-81e9-6f64e0d13efc`, Parent null, `omp/opencode-go/muse-spark-1.3-contributor` xhigh/full, repo cwd; init READY, no tools at init
- Authorized token `D161-9R26-SMOKEA-AUTH-7f4c91b2e6a34d7d` required exactly one Shell/Python target and no retry/correction
- Exactly one target process was invoked; no second launch, no retry, no correction. This closure recorder did not contact the executor and launched no agent/smoke.

## Raw OMP session evidence

- Raw session `2026-09-09T14-44-52-098Z_01a086a0-fb02-7250-a156-883a5ef346fc.jsonl`: 12 lines, 101987 bytes, SHA256 `42084c8772fc26f5e901979cb751cb61797e14a845f4d73c99741e80d0dba402`
- Authorized user line 8; assistant toolUse line 9; toolResult line 11 rc1 `IndexError: list index out of range`; assistant terminal stop line 12; no later user

## Cause (target defect, pre-launcher)

- The target process created `C:\Users\joji\bc-v3-v9r26-coord-smoke-20260909\cwd` and then incorrectly searched repo `Path.cwd().rglob('launch_phasec_coordinator.py')`; the v9r26 builder lives outside the repo, so the candidate list was empty and `cands[0]` raised before the frozen launcher import/call.
- A wrong positional launcher call was also present in the target but was non-causal/unreached (the failure precedes it).

## Frozen one-shot auditor

- Verdict `CONSUMED_NO_RETRY`: consumed true, correction_eligible false, authorized_index 7, terminal_index 11, tool_use_count 2 structured records, rc1.
- Same-executor correction is forbidden under the frozen v9r26 contract; none was attempted or performed.

## Post-failure state (preserved, no repair)

- Smoke cwd `C:\Users\joji\bc-v3-v9r26-coord-smoke-20260909\cwd` exists and is empty (0 items); wrapper log/bin absent; expected smoke OMP session dir absent. Preserve the empty cwd; no delete/recreate.
- Registry 366 parseable / 0 errors with exact Smoke-A title 0 / cwd 0 / both 0 and executor children 0: no coordinator agent launched; the frozen launcher was never reached.
- Final v9r26: mechanics 67/67, cache 0 / pyc 0; PLAN_LOCK / FROZEN_HASHES / run lock / source truth (+meta) / anchors / slots / authors / merged absent.
- Repo remains `9d1a331` equal clean; immutable v9r25 evidence unchanged; no Smoke B, freeze, source snapshot, Phase C, semantic Author/Reviewer/C, selector, protected evaluation, holdout, production, or audit append.

## Boundaries

D-161 closes v9r26 permanently as CONTRACT_INVALID_GENERATION / HARD HOLD / NON-RESUMABLE. No same-generation correction, retry, second smoke, or smoke-root delete/recreate. No Smoke B, real freeze, source-truth snapshot, Phase C, semantic generation roles, selector, protected dev-v2/holdout evaluation, production change, or canonical audit append. A future separate user `진행해` may only authorize a fresh successor generation with fresh identity; this closure starts none.
