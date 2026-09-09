# Retrieval v3 D-159 — generation-v9r25 real-freeze CONTRACT_INVALID_GENERATION

Date: 2026-09-09
Stage: exactly-once real-freeze closure
Generation: `retrieval-v3-dev-generation-v9r25`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260909-v9r25`
D-158 Smoke-B closure base commit: `38838c009d4d7ffbb3f2da042059d84fab3b27ae`

## Verdict

**v9r25 = CONTRACT_INVALID_GENERATION / HARD HOLD / NON-RESUMABLE.** Web independent FINAL VERDICT. v9r25 cannot proceed to Phase C. Preserve Smoke A, Smoke B, and both freeze artifacts byte-for-byte. No same-generation retry, repair, delete, or recreate.

## Pre-freeze gate (PASS, read-only)

Immediately before any freeze process (read-only reconcile):

- repo base `38838c009d4d7ffbb3f2da042059d84fab3b27ae`, local/upstream/origin equal, clean
- `ml-service/` diff 0
- canonical audit exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/dev-v2/`, `eval/retrieval-v3/holdout/` absent
- OMP `18.1.13`, default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`, Paseo `0.7.2`
- plan 76168B `c017d6578bf4a81c73c7960fd62d8b11c25d899e0330a293314d2a219ec9383c`
- rubric `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- exclusion `d917de37e2c0b0cd761f9ff72d81906df31546cab6e4af15a5c89f36dd91b857`
- mechanics 65/65, cache 0 dirs / 0 pyc
- Smoke A `SMOKE_PASS`, exact 10-line session SHA `5fea1aa75b1d1f0f419bfaccf5c2d3ce84f9d036e8b1040ccd99d2ead4c7032b`
- Smoke B `LIFECYCLE_SMOKE_PASS`, exact 21-line session SHA `3c76474133eb9b32e026a57f909132a5954c543b06f3b5e943ca101dbcadbf8b`
- regressions binding87 / rerun66 / Paseo64 / reach87 / registry37 PASS
- real-freeze artifacts zero-state (`PLAN_LOCK.json` / `FROZEN_HASHES.json` absent)

## Sole stage executor

- executor `3063da4a-6768-44b0-88d0-092e860fbe1b`, Parent null
- provider/model `omp` / `opencode-go/muse-spark-1.3-contributor`, thinking `xhigh`, mode `full`, repo cwd
- no subagent/worker/second executor for this stage

## Causal chain — two actual freeze processes

1. The executor's first provider turn was initially observed via Paseo as idle/finished, with partial logs showing thoughts only. At that observation `PLAN_LOCK.json` / `FROZEN_HASHES.json` were still absent. Web incorrectly concluded no freeze would occur and sent a correction to the same executor.
2. The original provider turn was in fact still progressing. It later executed one Shell call performing precheck plus the FIRST real `freeze_plan_v9r25.py` process plus a post-hash helper. That freeze process itself succeeded and printed plan `c017d6578...`, rubric `08e598a4...`, lock SHA `8da1860e492be673ca69cc327e0378d3fabe5069e4b95541db6a90c3acf7a652`, `frozen_at 2026-09-09T13:16:41+00:00`, hold_base `6e3b3584ece725f716fadeda32f5133365cef0fb`, `frozen_files 84`. The shell overall exited 1 only because the AFTER-freeze post-hash helper raised `ImportError` (bad `hashlib` import); that did not undo the successful freeze publication.
3. The correction message then caused a SECOND actual `freeze_plan_v9r25.py` process after the first freeze was consumed. It returned rc3 `CONTRACT_INVALID_GENERATION: must be absent at freeze: PLAN_LOCK.json`. The O_EXCL/absence gate prevented any overwrite.

## Immutable artifacts after both calls

- `PLAN_LOCK.json` 28102 bytes, SHA256 `8da1860e492be673ca69cc327e0378d3fabe5069e4b95541db6a90c3acf7a652`
- `FROZEN_HASHES.json` 8296 bytes, SHA256 `075bc3d7820a22693ae3740d29bd743dc8317260213ddbc1694977aa53bd4ed5`
- manifest 84 entries; rehash missing 0 / mismatch 0; exact eligible 84, manifest_only 0, eligible_only 0
- `frozen_at` 13:16:41Z; `PLAN_LOCK.json` creation 13:16:45.0252259Z (+4.025226s); `FROZEN_HASHES.json` creation 13:16:45.0979095Z (+4.097910s)
- lock binds Smoke A agent `7989e333-d302-4d8b-886c-0d230c4b9f3c` (session SHA `5fea1aa7...`, 10 lines) and Smoke B agent `73e51095-c187-48e3-a6b4-e6d387455248` (session SHA `3c764741...`, 21 lines)

## Post-event repo boundary

- repo remains at `38838c0`, local/upstream/origin equal; audit unchanged 4 rows `90cfb54d...`; `ml-service/` diff 0
- protected `dev` / `dev-v2` / `holdout` absent
- Phase-C runlock / source / meta / anchors / slots / authors / merged pool / phaseC root / execute root all absent

## Classification

Mechanics fail-closed protection worked (second process rejected, no overwrite), but the standing workflow required the real freeze exactly once and prohibited any invocation after consumption. The second actual Python freeze process is an irreversible one-shot provenance violation. The orchestration error is Web-side early/partial status interpretation, not a v9r25 freeze-mechanics defect; recorded accurately without blaming the generation code.

## Closure / successor boundary

v9r25 is permanently closed. Do not retry or resume the freeze, delete/recreate the lock or hashes, patch frozen bytes, or launch Phase C, protected dev-v2, holdout, production, or canonical audit work for v9r25. A successor, if ever authorized by a separate user `진행해`, is a fresh logical stage with a fresh generation identity only. This closure starts no successor.
