# Retrieval v3 D-120 — generation-v9r18 one-shot Smoke A/B PASS

Date: 2026-09-07
Stage: one-shot smoke verdict closure
Generation: `retrieval-v3-dev-generation-v9r18`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260907-v9r18`

## Verdict

**v9r18 Smoke A PASS / Smoke B PASS.** Both authorized one-shot smokes were consumed exactly once on the D-119 corrected final bytes, plan SHA `848b586235653737210d78424baa00935c86665aff2a7542d71ffa2b6807c532`. No smoke retry or same-generation repair occurred after either launch.

No real freeze, Phase C, source-truth snapshot, semantic role, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append occurred in D-120.

## Base

Immediately before Smoke A, repo HEAD/local/upstream/direct remote was D-119 `d0132e2ba752f425892c94b7bd8ef5511bb7b149`, clean; production `ml-service` diff zero; canonical audit remained 4 events SHA `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`. Builder was 70 files/cache0/runtime0; no v9r18 smoke roots/sessions/agents; bundled Paseo daemon running/reachable.

## Smoke A — coordinator confinement

Exactly one model launch:
- agent `69a090c5-5352-4fa2-aeb4-7dfad7857dea`
- cwd `C:\Users\joji\bc-v3-v9r18-coord-smoke-20260907\cwd`
- top-level Parent null; model `opencode-go/muse-spark-1.3-contributor`; thinking xhigh; final idle
- session `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r18-coord-smoke-20260907-cwd\2026-09-06T20-48-20-183Z_01a0787a-aad7-7191-9982-5894141f0035.jsonl`
- stable lines 10
- stable SHA256 `81aaddc5c560c350913e0302b780c2fe90fb921dc359f4935d82bb714c252b35`
- tool calls `phasec_probe=1`
- exact-one coordinator wrapper: tools `todo`, mode `smoke`, frozen controls
- frozen `audit_coord_smoke.py`: `SMOKE_PASS`, descendants 0, fallback proven true.

The frozen auditor was repeated after a 12-second stability interval; line count/SHA/verdict were unchanged. No second Smoke A was launched.

## Smoke B — deterministic lifecycle

Only after stable Smoke-A PASS, duplicate gate proved lifecycle staging/session/agent 0 and daemon still running/reachable; Smoke-A SHA was reverified unchanged.

Exactly one frozen lifecycle runner invocation launched:
- agent `4b5789ff-ce4d-4f89-ac6a-f8d830d10cae`
- staging/cwd `C:\Users\joji\bc-v3-v9r18-lifecyclesmoke`
- top-level Parent null; model `opencode-go/muse-spark-1.3-contributor`; thinking xhigh; final idle
- session `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r18-lifecyclesmoke\2026-09-06T20-49-53-773Z_01a0787c-186d-7281-98fa-1018e838dd07.jsonl`
- stable lines 21
- stable SHA256 `c0d7dc43155b66db7c8075276817330dc0a3720d1c54b1e07d18c005557b8c58`
- transcript `role_smoke_probe=1`, `todo=4`, model `role_write_chunk=0`
- helper access log exactly 9 rows: expected denies cross-role/unknown-resource/bad-target exactly once each + six allowed writes exactly once each
- output chunks 0..5 each 59 bytes / 1 row with standing deterministic hashes
- frozen `audit_lifecycle_smoke.py`: `LIFECYCLE_SMOKE_PASS`, descendants 0, fallback proven true.

The frozen auditor was repeated after stability delay on the same evidence and returned the same 21-line/SHA PASS proof. No second Smoke B was launched.

## Final boundary

Auditor imports created only two builder-local Python cache directories. Their resolved paths were proven inside the v9r18 builder and only those cache directories were removed. Final builder: 70 files/cache0; plan SHA remains `848b586235653737210d78424baa00935c86665aff2a7542d71ffa2b6807c532`.

Absent: `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, source truth/meta, semantic runtime, `evalset.jsonl`, protected dev-v2 evaluation, holdout evaluation, production change, canonical audit append.

**NEXT:** separate v9r18 real-freeze pre-gate. Real freeze must bind the exact Smoke-A and Smoke-B evidence above. No new smoke is permitted.
