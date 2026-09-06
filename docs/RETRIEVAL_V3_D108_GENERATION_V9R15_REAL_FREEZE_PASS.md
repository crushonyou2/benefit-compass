# Retrieval v3 D-108 — generation-v9r15 real freeze PASS

Date: 2026-09-07
Stage: real-freeze gate durable record only
Generation: `retrieval-v3-dev-generation-v9r15`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260907-v9r15`

## Verdict

**v9r15 REAL FREEZE: PASS.** The unchanged D-106 final bytes were frozen only after D-107 preserved one-shot Smoke A/B evidence independently passed the frozen auditors. The resulting `PLAN_LOCK.json` binds the exact Smoke A/B agent/cwd/session/wrapper evidence, and all 67 entries in `FROZEN_HASHES.json` independently rehash to the recorded values with zero mismatch.

This record does not run Phase C, source-truth snapshotting, semantic roles, selector, protected evaluation, or holdout evaluation.

## Reconciled base

Immediately before successful freeze, repo branch `codex/retrieval-v3-user-search-quality` was at D-107 commit `46d0779d8eab5afcc2ec22d142fb40a6935c42ef`, local/upstream/direct remote equal, clean, `git diff --check` PASS, production `ml-service/` diff zero. Canonical audit remained exactly 4 events SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`.

The v9r15 builder was 66 source/support files, pycache 0, with D-106 key bytes exact and no `PLAN_LOCK.json`, `FROZEN_HASHES.json`, run lock, source truth, evalset, or `out/`.

## Freeze invocation and transport correction

The first real-freeze invocation used the correct eight Smoke binding arguments and unchanged source bytes, but the freeze process's child `audit_coord_smoke.py` inherited Windows locale text decoding and returned `CONTRACT_INVALID_GENERATION: descendant listing unparseable` after a `cp949` decode failure. This occurred before `PLAN_LOCK.json` or `FROZEN_HASHES.json` was written. Immediate reconciliation proved:

- `PLAN_LOCK.json` absent
- `FROZEN_HASHES.json` absent
- builder still exactly 66 files / cache 0
- `GENERATION_PLAN.json` SHA unchanged `83307b659b53b4340aecc68b259de63c311288b0f6fa7064dfe3799c1b02f6e3`
- `input/EXCLUSION_INPUTS.json` SHA unchanged `62913a9a94337f23860e0bde18c717c349ecb9869f9a46ba52f4323853775fb2`
- `freeze_plan_v9r15.py` SHA unchanged `81197047e943801edd744c0baebbf8103f0ed6dbb911df1b1354d0135630cbdf`
- both Smoke session bytes unchanged

No smoke/model launch or source mutation occurred in that failed pre-write attempt. The unchanged frozen auditors were then separately verified under the exact child environment needed for Windows (`PYTHONUTF8=1` with Paseo on PATH), and both returned their existing PASS verdicts on the same evidence. The unchanged freeze CLI was then rerun once under that verified environment.

## Successful real freeze

Successful freeze time:

- CLI UTC `frozen_at`: `2026-09-06T16:27:59+00:00`
- lock representation: `2026-09-07T01:27:59+09:00`

Freeze output:

- plan SHA256: `83307b659b53b4340aecc68b259de63c311288b0f6fa7064dfe3799c1b02f6e3`
- plan bytes: 58513
- rubric SHA256: `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- lock SHA256: `8c94ff00e5f4833e645472da1f176bf9c0792f57dac39a31a99751d5b5fb8d70`
- exclusion manifest SHA256: `62913a9a94337f23860e0bde18c717c349ecb9869f9a46ba52f4323853775fb2`
- `FROZEN_HASHES.json` SHA256: `e9e9df7ac1f2452b663541961497e7f554bb5f0fd3b9403372aee89e94c97df7`
- frozen file entries: 67
- hold base commit: `821d72727e502fa17a4fa7d33df5267e8a61d4de`

## Exact Smoke bindings in PLAN_LOCK

Smoke A:

- agent `d7424247-c7fe-4d60-b2f9-69effe362c31`
- cwd `C:\Users\joji\bc-v3-v9r15-coord-smoke-20260907\cwd`
- session `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r15-coord-smoke-20260907-cwd\2026-09-06T16-15-40-621Z_01a07781-0a4c-70f4-80ad-a2403efc90e7.jsonl`
- session SHA `440409af7a6c74aacf8834d186779b79253154c2dc137d0d7089141a2c8a02bf`
- wrapper `C:\Users\joji\bc-v3-v9r15-coord-smoke-20260907\cwd\wrapper_invocation.log`
- audit verdict `SMOKE_PASS`

Smoke B:

- agent `79114e77-92c7-4a9b-aae8-232e65b35237`
- cwd `C:\Users\joji\bc-v3-v9r15-lifecyclesmoke`
- session `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r15-lifecyclesmoke\2026-09-06T16-16-42-020Z_01a07781-fa24-7739-a8c6-fe19ffa316d2.jsonl`
- session SHA `0a7b32dc8a63bb2f485b2ab6a75812aa9452846d9043802b87773fe60e1870d3`
- wrapper `C:\Users\joji\bc-v3-v9r15-lifecyclesmoke\wrapper_invocation.log`
- audit verdict `LIFECYCLE_SMOKE_PASS`

The two current session files were rehashed after freeze and still match those lock-bound SHAs.

## Independent frozen-hash verification

Web independently loaded `FROZEN_HASHES.json`, resolved every listed path under the v9r15 builder, rehashed each file, and compared it to the stored value:

- entries: 67
- missing: 0
- mismatches: 0

Auditor preflight had created five `.pyc` files in two builder-local `__pycache__` directories. Each was proven absent from the 67 frozen keys and its resolved path proven strictly inside the v9r15 builder. Only those cache directories were removed. After cleanup:

- builder files: 68 = 66 source/support + `PLAN_LOCK.json` + `FROZEN_HASHES.json`
- pycache/pyc: 0
- frozen hash mismatches: 0

## Boundary after freeze

Still absent:

- `phasec_driver.run.lock`
- `source_truth.jsonl`
- `source_truth_meta.json`
- `evalset.jsonl`
- `out/`

No Phase C, source-truth snapshot, Author/Reviewer/C/selector run, protected dev evaluation, holdout evaluation, production change, or canonical audit append occurred in D-108.

## Next logical stage

**NEXT: Phase-C/source-truth pre-execution gate on this exact frozen v9r15 builder.** Before any model execution, reconcile repo/remote, OMP effective config, `PLAN_LOCK.json`/`FROZEN_HASHES.json`, frozen-file integrity, no run lock/runtime outputs, and the exact source-truth authorization/inputs required by the standing prereg.

Do not mutate frozen source bytes. Do not run holdout/final protected evaluation. Phase C may begin only as a separate logical stage using this exact freeze evidence.
