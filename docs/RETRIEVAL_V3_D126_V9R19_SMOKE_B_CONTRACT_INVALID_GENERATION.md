# Retrieval v3 D-126 — generation-v9r19 Smoke B CONTRACT_INVALID_GENERATION

Date: 2026-09-08
Stage: Smoke-B duplicate/preflight + exactly-one execution closure
Generation: `retrieval-v3-dev-generation-v9r19`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r19`
D-125 base commit: `e4462db102937041cf943a4f468c8367d3f5f69b`

## Verdict

**CONTRACT_INVALID_GENERATION / NON-RESUMABLE / NON-REPAIRABLE.** V9r19 consumed Smoke B exactly once. The frozen `run_lifecycle_smoke.py` reached its frozen `audit_lifecycle_smoke.py`, which fail-closed rc3 with:

`agent listing unparseable; descendants unprovable`

Per the frozen v9r19 one-shot lifecycle contract, any Smoke-B failure closes the generation. No second Smoke B, auditor-bypass pass, same-generation repair, real freeze, Phase C, protected dev-v2 evaluation, holdout evaluation, or production change is authorized.

Smoke A remains the D-125 immutable PASS evidence and must not be repeated.

## Prelaunch reconciliation

Before the only Smoke-B runner invocation:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `e4462db102937041cf943a4f468c8367d3f5f69b`
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- protected dev/holdout plaintext paths absent
- canonical audit exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- final plan SHA256 `a442f5641f1dbada08ce5eeb71b838746910c58c8b979e25bacc24a134420705`
- exclusion manifest SHA256 `1caffc012103abea5c85487588bd0c6daaea2766e90cc41cb113569086f56e3b`
- rubric SHA256 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- mechanics 57/57 exact by bytes + SHA
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock` absent
- OMP `18.1.13`; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`
- exact bundled Paseo CLI `C:\Users\joji\AppData\Local\Programs\Paseo\resources\bin\paseo.cmd`, version `0.7.2`, daemon running/reachable
- D-125 Smoke A re-audited PASS with stable session SHA256 `86bc67edfd674daae98df4be119c3022ecd000c08b2fd00f6ab0350cd8e3d313`
- Smoke-B staging root 0, Paseo agents 0, OMP session directories 0, matching processes 0

One preliminary process-name gate stopped before any launch because the gate command itself transiently matched its own `v9r19-lifecyclesmoke` literal. Immediate read-only reconciliation showed root/agent/session/process all 0; a corrected self-match-safe final gate then passed. No model execution was consumed by that false-positive gate.

## Exactly-one Smoke B execution

The frozen no-argv runner was invoked exactly once:

`python -X utf8 C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r19\run_lifecycle_smoke.py`

It created exactly one Smoke-B agent:

- agent `e9cbcb94-e2cf-4bb6-be5f-95c5743e0d55`
- name `v9r19-lifecyclesmoke`
- cwd `C:\Users\joji\bc-v3-v9r19-lifecyclesmoke`
- provider/model `omp` / `opencode-go/muse-spark-1.3-contributor`
- thinking `xhigh`
- mode `full`
- ParentAgentId null
- final observed status `idle`
- created `2026-09-07T20:01:35.355Z`

Exactly one OMP session directory exists for that cwd, containing exactly one JSONL session file:

`C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r19-lifecyclesmoke\2026-09-07T20-01-34-876Z_01a07d76-389c-76db-9a8b-2a4608ff0674.jsonl`

Observed file metadata after failure: 39,730 bytes; last write `2026-09-07T20:01:59.7144637Z`. A later post-failure hash attempt was denied because another process still held the file; the session was not stopped, copied, repaired, or otherwise disturbed.

## Frozen auditor failure boundary

The runner's own frozen auditor returned rc3 and the runner exited nonzero with:

`CONTRACT_INVALID_GENERATION: lifecycle audit FAIL rc=3 ... agent listing unparseable; descendants unprovable`

Source-order review of the unchanged frozen auditor proves that this failure occurs only after all preceding checks return successfully. Therefore, in this exact failed invocation, the following frozen gates had already passed before the mandatory daemon-listing parse failure:

- top-level provenance + idle state
- exact-one role wrapper with tools `todo`, mode `role`, kind `lifecycle_smoke`, frozen extension SHA/controls/staging
- session JSONL readable by the auditor at that time
- transcript tool-call set confined to `{todo, role_smoke_probe}`
- `role_smoke_probe == 1`
- `role_write_chunk == 0`
- exact helper access-log shape: 9 rows total = 3 expected denies + 6 allowed chunk writes
- every allowed resolved path confined to staging
- exactly one write to each `out/chunk_0..5.jsonl`
- dedicated Smoke-B 6x1 output validation PASS
- final `LIFECYCLE_SMOKE_DONE` session stop validation PASS
- the first `inspect_children_zero` check returned without failing

The next mandatory `paseo ls --json` descendant scan produced stdout that the frozen auditor could not parse as JSON, so it fail-closed rather than assuming zero descendants. No causal claim beyond that observed frozen failure is made here.

## Preserved Smoke-B artifacts

The failed generation evidence remains in place. Read-only hashes/counts observed after failure:

- `role_tool_access.log`: 9 rows, SHA256 `02421b498cd9029e095b8aa4bed475fb7ff5aefde8bdcf3c0f45cc7ad52016d7`
- `wrapper_invocation.log`: 1 row, SHA256 `3e9c9ca9ac1c72366e5afd38ec79de038b54b55526320af5f68ec2dedf1cfe4a`
- `out/chunk_0.jsonl`: 59 bytes / 1 row, SHA256 `e7d2aecdf462de9a8918695e7adb70032f80c50205ce849b42664fe3877f24e9`
- `out/chunk_1.jsonl`: 59 bytes / 1 row, SHA256 `1e942823dc343829cab4c491ceee21ef4a6f8a54337ae32c5564bf5920b8d2f7`
- `out/chunk_2.jsonl`: 59 bytes / 1 row, SHA256 `90bdd8c64714150816c00c9ef40c6102d451dbf0102d3a3a698b204e7bfd090d`
- `out/chunk_3.jsonl`: 59 bytes / 1 row, SHA256 `c695e51a11fa40103355a84f95f15396616465d391bdeade92ec03db24244e1a`
- `out/chunk_4.jsonl`: 59 bytes / 1 row, SHA256 `d72b87b5d2fabbfd43d2b9b999bcd3cfcd4a6cfe251b44e21e5f97ce2f82de0f`
- `out/chunk_5.jsonl`: 59 bytes / 1 row, SHA256 `4d14e6c3ee466e96ff1daf257dbe26e3205070c197e97757e9f5e9fc90d953ff`
- staged `RUBRIC.json`: SHA256 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- staged `smoke_task.json`: SHA256 `be91a285ae085ce82bf73531dbe11dd2347fbaf0b62e21c3ffe4b229608faaf5`
- staged wrapper bytes match the frozen builder wrapper hashes

The runner/auditor imports also left two builder-local `__pycache__` directories. Because v9r19 is now failed immutable evidence, they were not cleaned or otherwise mutated in this closure.

## Final boundary

Post-failure reconciliation before this durable write:

- repo still at clean D-125 base `e4462db102937041cf943a4f468c8367d3f5f69b`
- final plan / manifest / rubric SHAs unchanged
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock` absent
- canonical audit remains 4 rows / SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- production `ml-service/` diff remains 0
- protected dev-v2 and holdout untouched
- Smoke A not repeated
- Smoke B not repeated
- no real freeze
- no Phase C

**V9r19 is permanently closed.** The only permitted continuation is a separately approved fresh successor generation/identity. Do not repair, rerun, freeze, or resume v9r19.
