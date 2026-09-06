# Retrieval v3 D-115 — generation-v9r17 real freeze PASS

Date: 2026-09-07
Stage: real-freeze closure
Generation: `retrieval-v3-dev-generation-v9r17`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260907-v9r17`

## Verdict

**v9r17 REAL FREEZE: PASS.** The unchanged D-113 final bytes were frozen only after D-114 one-shot Smoke A/B evidence passed the frozen auditors. `PLAN_LOCK.json` binds the exact A/B agent/cwd/session/wrapper evidence and auditor verdicts; all 69 entries in `FROZEN_HASHES.json` independently rehash with zero mismatch.

No Phase C, source-truth snapshot, Author/Reviewer/C, selector, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append occurred in this stage.

## Reconciled base

Immediately before freeze, repo branch `codex/retrieval-v3-user-search-quality` was at D-114 commit `5792ef5cc063b69442c252c2d59ad838316fc9b5`, local/upstream/direct remote equal and clean; production `ml-service/` diff zero; canonical audit exactly 4 events SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`.

Builder was 68 source/support files/cache0 with no lock/frozen hashes/run lock/source truth/evalset/runtime outputs. Smoke A/B session SHAs remained stable and both agents remained idle.

## Successful freeze

Freeze was executed once under `PYTHONUTF8=1` and the exact frozen bundled Paseo CLI environment. No preliminary failed freeze attempt and no smoke rerun occurred.

- CLI UTC `frozen_at`: `2026-09-06T18:30:47+00:00`
- lock local representation: `2026-09-07T03:30:47+09:00`
- plan SHA256: `6b879951ce0921d655ee09d7d74f10f39afad703031684788dca35b2a4d51600`
- plan bytes: 63,784
- rubric SHA256: `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- exclusion manifest SHA256: `bda24abb1e0a663c990449b65616f4175c4c1dfc439fec80058917c09e7fcbd4`
- `PLAN_LOCK.json` SHA256: `71196c83c512c1d9ef06c5118b1e971e57f6ba5992113b2320ebfb5648d01bc1`
- `FROZEN_HASHES.json` SHA256: `7e11179db6a836941f2c37bc1cc8c4bb76fa13b26c28ff97d08c9f3455a6d080`
- frozen entries: 69
- hold base commit: `8a0a2b687e7394dc57c97ad532a3af4bd6b06e4f` (D-112)

## Exact lock-bound Smoke A

`smoke_top_level_verification` binds:
- agent `28ff4ba5-6b00-42dd-862c-5bc603e9a486`
- cwd `C:\Users\joji\bc-v3-v9r17-coord-smoke-20260907\cwd`
- session `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r17-coord-smoke-20260907-cwd\2026-09-06T18-25-53-818Z_01a077f8-429a-77d4-8b5f-823245970895.jsonl`
- session lines 10
- session SHA256 `de1b5c9230e97eddcd4c45c83de502e5cbc1648a2f9de66c73ccd0c88a1a8a1c`
- wrapper `C:\Users\joji\bc-v3-v9r17-coord-smoke-20260907\cwd\wrapper_invocation.log`
- tool calls `phasec_probe=1`
- descendants 0
- auditor verdict `SMOKE_PASS`

## Exact lock-bound Smoke B

`lifesmoke_top_level_verification` binds:
- agent `769f2ca9-2778-45df-8e35-85783b0613db`
- cwd `C:\Users\joji\bc-v3-v9r17-lifecyclesmoke`
- session `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r17-lifecyclesmoke\2026-09-06T18-27-34-373Z_01a077f9-cb65-7270-bc1c-06af2281df15.jsonl`
- session lines 18
- session SHA256 `2837be1a7b529c770c8db78e6477bb991a99f8e946217f9b9411e4b6aadf5eac`
- wrapper `C:\Users\joji\bc-v3-v9r17-lifecyclesmoke\wrapper_invocation.log`
- tool calls `role_smoke_probe=1`, `todo=3`
- expected denies exactly once each: cross-role / unknown-resource / bad-target
- exact six allowed 1-row chunk writes
- descendants 0
- auditor verdict `LIFECYCLE_SMOKE_PASS`

## Independent frozen-hash verification

Web independently loaded `FROZEN_HASHES.json` and rehashed every listed path:
- entries 69
- missing 0
- mismatches 0

Freeze-time auditor imports created only five `.pyc` files under two builder-local `__pycache__` directories. Every cache file was proven absent from the frozen-key set and inside the v9r17 builder before exact-path removal. After cleanup:
- builder files 70 (= 68 source/support + `PLAN_LOCK.json` + `FROZEN_HASHES.json`)
- cache 0
- frozen mismatches 0

## Boundary / next

Absent after freeze: `phasec_driver.run.lock`, source truth/meta, anchors/slots, semantic role output, `evalset.jsonl`, protected dev-v2 result, holdout result.

**NEXT:** separate Phase-C/source-truth pre-execution gate on these exact frozen bytes. No new smoke and no post-freeze source mutation are permitted.
