# Retrieval v3 D-133 — generation-v9r21 one-shot Smoke A PASS

Date: 2026-09-08
Stage: Smoke A duplicate/runtime/provenance gate / exactly-one execution closure
Generation: `retrieval-v3-dev-generation-v9r21`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r21`
D-132 pre-smoke base commit: `605a931ad439fa98def02da1ae0b55d47be86592`

## Verdict

**SMOKE A PASS.** The D-132 final v9r21 bytes consumed exactly one actual coordinator model Smoke A. Frozen `audit_coord_smoke.py` returned `SMOKE_PASS` twice on the same preserved evidence with a 12-second stability interval. The exact OMP session remained 10 lines with SHA256 `37c536ce6fb4dcbe686c9e3f6efb70a7dc008e9192583c5f52fc6cad9b3ddae5`, with exactly one `phasec_probe` call, zero forbidden calls, zero descendants, and fallback provenance proven.

No second Smoke A was launched. Smoke A is permanently consumed and non-repeatable for v9r21.

**STOP boundary:** Smoke B was not executed in this stage. No real freeze, Phase C, source-truth snapshot, Author/Reviewer/C generation, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append occurred. The next logical stage is a separate Smoke-B duplicate/preflight gate and, only if that fresh gate passes, exactly one Smoke B.

## Prelaunch reconciliation

Immediately before the single launch:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `605a931ad439fa98def02da1ae0b55d47be86592`
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- main-tree protected `eval/retrieval-v3/dev/` and `eval/retrieval-v3/holdout/` absent
- canonical audit `eval/retrieval-v3/audit/events.jsonl` exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- plan SHA256 `9a3369a3dada669a2cd448f59ceaf41982fb94fc11029b20d2431f72430653ec`, 65,857 bytes
- exclusion manifest SHA256 `518292880dbdf24335eb2412204e62582d3abf0a73e3a2276f01dac9d3b08b59`
- rubric SHA256 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- mechanics 59/59 exact, mismatch 0
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock` absent
- builder `__pycache__` and `.pyc` count 0
- actual OMP `omp/18.1.13`; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`
- exact bundled Paseo CLI/daemon `0.7.2`, daemon running/reachable
- complete local registry: 319 parseable JSON records, v9r21 title/cwd matches 0
- v9r21 matching processes 0
- Smoke-A root `C:\Users\joji\bc-v3-v9r21-coord-smoke-20260908` absent
- expected Smoke-A OMP session directory absent

No protected plaintext recovery or prohibited git-object/history access was used.

## Smoke A — exactly one actual model launch

A brand-new empty staging cwd was created at:

`C:\Users\joji\bc-v3-v9r21-coord-smoke-20260908\cwd`

Frozen `launch_phasec_coordinator.py` was invoked exactly once in `smoke` mode. The prompt was the neutral deterministic D-132 contract: call `phasec_probe` exactly once with an empty object, call no other tool, then reply `SMOKE_DONE` and stop.

Observed evidence:

- agent: `308e7b64-1547-443e-847c-684d792477d1`
- title: `D133 v9r21 Smoke A`
- created: `2026-09-07T22:12:32.525Z`
- final update: `2026-09-07T22:12:35.424Z`
- cwd: `C:\Users\joji\bc-v3-v9r21-coord-smoke-20260908\cwd`
- ParentAgentId: null
- provider/model: `omp` / `opencode-go/muse-spark-1.3-contributor`
- thinking: `xhigh`
- mode: `full`
- final status: `idle`
- exact session: `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r21-coord-smoke-20260908-cwd\2026-09-07T22-12-31-975Z_01a07dee-1c67-77a5-a50d-5e1a34190d6c.jsonl`
- stable session lines: 10
- stable session SHA256: `37c536ce6fb4dcbe686c9e3f6efb70a7dc008e9192583c5f52fc6cad9b3ddae5`
- transcript tool calls: `phasec_probe=1`
- forbidden tool calls: 0
- frozen wrapper log: exactly 1 row; SHA256 `dc5a2145616e7bde29998517f51504d8dfd25a412e5fa3f1cd587092da735bb2`
- wrapper tools/mode: `todo` / `smoke`
- frozen coordinator extension SHA256: `b2264a5398719f8e4b72cca9e156ea0f3f6560aa7040a1d37155a2f75ea9cdfc`
- exact wrapper controls: `--tools=todo`, `-e`, `--no-extensions`, `--no-skills`, `--no-rules`
- real OMP path bound by wrapper: `C:\Users\joji\AppData\Local\omp\omp.exe`
- descendants: 0 by inspect strict-if-present plus complete local-registry parent scan
- fallback proven by frozen auditor: true
- frozen auditor verdict: rc0 `SMOKE_PASS`

The frozen auditor was re-run after 12 seconds against the same agent/cwd/session/wrapper evidence. It again returned rc0 `SMOKE_PASS` with the same exact 10-line session SHA, `phasec_probe=1`, descendants 0, and frozen wrapper surface. Independent read-only post-run review also verified the same 10-line SHA remained stable across a separate 12-second shared-read interval.

An ancillary direct `Get-FileHash` attempt against the live session file was denied by the provider's file lock. This did not alter the verdict: the frozen auditor successfully read and hashed the exact session twice, and the independent shared-read verification reproduced the same SHA without any model relaunch.

No second Smoke A launch occurred.

## Independent post-run review

Two read-only independent reviews returned PASS with no Smoke-A blocker. They independently confirmed:

- exact top-level agent/cwd/model/xhigh/full/idle provenance
- exactly one v9r21 Smoke-A session directory and one JSONL
- exact 10-line session SHA and only `phasec_probe=1`
- wrapper log exactly one frozen invocation row
- complete registry parseable and exactly one v9r21 Smoke-A record, descendants 0
- Smoke-B root/session/registry/process all zero
- no real-freeze/Phase-C/source-truth/candidate artifacts
- repo, audit, protected-data and production boundaries unchanged

## Post-Smoke-A boundary

After the stable PASS and independent reviews:

- final plan remains `9a3369a3dada669a2cd448f59ceaf41982fb94fc11029b20d2431f72430653ec`
- freeze mechanic remains `65ba9208033526052db0d77e90dd14145a7dcb3c391c9cad87b2d17ec1a2bcf4`
- freeze rerun regression remains `28f5383e9f8476604997055e048f5bfdd96a92c22e1d086769e51c74b083dd86`
- mechanics remain 59/59 exact
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock` remain absent
- complete registry now contains 320 parseable records and exactly one v9r21 generation match: the Smoke-A agent above
- Smoke-A OMP session directory contains exactly one `.jsonl` file
- Smoke-A wrapper process remains intentionally preserved with the idle agent; it is not stopped as part of successful-path evidence preservation
- Smoke-B root `C:\Users\joji\bc-v3-v9r21-lifecyclesmoke` absent
- Smoke-B OMP session directory absent
- Smoke-B matching processes 0
- canonical audit remains 4 rows with unchanged SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- production `ml-service/` remains unchanged
- protected dev/holdout plaintext paths remain absent
- v9r20 predecessor plan/freeze hashes remain `4baf17f208db63a27948cf1b11ac88f87b052f0f8db7f0f5468a1267023be542` / `ac1460d6229686901828458ac7a7274be98babfc46ca7b39f6adb853b5dc3336`

Frozen-auditor imports created exactly two builder-local `__pycache__` directories with four `.pyc` files. Their resolved paths were verified inside the exact v9r21 builder and only those cache directories were removed. Final cache/pyc count is 0.

## Gate boundary

V9r21 has consumed **Smoke A exactly once and PASSed**. Smoke A is permanently non-repeatable for this generation.

Next, only if separately approved, is **Smoke B duplicate/preflight + exactly-one execution**. Smoke B must not be silently consumed in D-133. Real freeze, Phase C, protected dev-v2, holdout, and production remain prohibited until their later gates.
