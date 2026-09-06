# Retrieval v3 D-114 — generation-v9r17 one-shot Smoke A/B PASS

Date: 2026-09-07
Stage: one-shot smoke verdict closure
Generation: `retrieval-v3-dev-generation-v9r17`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260907-v9r17`

## Verdict

**v9r17 Smoke A PASS / Smoke B PASS.** Both authorized one-shot smokes were consumed exactly once on the final D-113 bytes. No smoke retry, same-generation repair, freeze, Phase C, source-truth snapshot, protected evaluation, holdout evaluation, production change, or canonical audit append occurred in this stage.

## Reconciled base

Immediately before smoke execution, branch `codex/retrieval-v3-user-search-quality` was at D-113 commit `f7c9d14c38a1cc8990531d5516f8ad76da547685`, local/upstream/direct remote equal and clean. Production `ml-service/` diff remained zero and canonical audit remained 4 events SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`.

Final builder before and after smokes: 68 source/support files, cache 0 after exact-path cleanup, plan SHA `6b879951ce0921d655ee09d7d74f10f39afad703031684788dca35b2a4d51600`, no real freeze/runtime artifacts.

## Smoke A — coordinator confinement

Final duplicate gate proved no v9r17 agents/staging/session roots before launch and daemon `running/reachable` through the frozen bundled CLI.

Exactly one model launch:
- agent `28ff4ba5-6b00-42dd-862c-5bc603e9a486`
- cwd `C:\Users\joji\bc-v3-v9r17-coord-smoke-20260907\cwd`
- provider/model `omp/opencode-go/muse-spark-1.3-contributor`, thinking `xhigh`, Parent null
- wrapper mode `smoke`, custom tool `phasec_probe`, built-in tools `todo`, frozen controls
- session `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r17-coord-smoke-20260907-cwd\2026-09-06T18-25-53-818Z_01a077f8-429a-77d4-8b5f-823245970895.jsonl`
- stable session lines 10
- stable SHA256 `de1b5c9230e97eddcd4c45c83de502e5cbc1648a2f9de66c73ccd0c88a1a8a1c`
- tool calls: `phasec_probe=1`
- frozen `audit_coord_smoke.py`: rc0 `SMOKE_PASS`
- descendants 0; fallback proven true
- final agent state observed `idle`

The auditor was repeated after a 12-second stability interval; line count/SHA/verdict were unchanged. No second Smoke A was launched.

## Smoke B — deterministic lifecycle

Only after stable frozen Smoke-A PASS, the Smoke-B duplicate gate proved no B staging/session/agent and daemon still `running/reachable`; Smoke-A session SHA was reverified unchanged.

Exactly one frozen `run_lifecycle_smoke.py` invocation launched:
- agent `769f2ca9-2778-45df-8e35-85783b0613db`
- staging/cwd `C:\Users\joji\bc-v3-v9r17-lifecyclesmoke`
- provider/model `omp/opencode-go/muse-spark-1.3-contributor`, thinking `xhigh`, Parent null
- session `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r17-lifecyclesmoke\2026-09-06T18-27-34-373Z_01a077f9-cb65-7270-bc1c-06af2281df15.jsonl`
- stable session lines 18
- stable SHA256 `2837be1a7b529c770c8db78e6477bb991a99f8e946217f9b9411e4b6aadf5eac`
- transcript calls: `role_smoke_probe=1`, `todo=3`, `role_write_chunk=0`
- helper access log exactly 9 rows: expected denies `cross-role=1`, `unknown-resource=1`, `bad-target=1`; allowed exact chunk writes 6×1
- output chunks 0..5: each 59 bytes / 1 row with the standing deterministic hashes
- frozen `audit_lifecycle_smoke.py`: rc0 `LIFECYCLE_SMOKE_PASS`
- descendants 0; fallback proven true
- final agent state observed `idle`

The frozen auditor was repeated after stability delay and returned the same 18-line/SHA PASS proof. No second Smoke B was launched.

## Final boundary

Auditor imports created only builder-local Python caches. Their resolved paths were proven within the v9r17 builder and only those cache directories were removed. Final builder is 68 files/cache0, with D-113 key hashes unchanged.

Absent: `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, source truth, semantic-role runtime, `evalset.jsonl`, protected dev-v2 evaluation, holdout evaluation, production change, canonical audit append.

**NEXT:** separate v9r17 real-freeze pre-gate. Real freeze must bind the exact Smoke-A and Smoke-B evidence above. No new smoke is permitted.
