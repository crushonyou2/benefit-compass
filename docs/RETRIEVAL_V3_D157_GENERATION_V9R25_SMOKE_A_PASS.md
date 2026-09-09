# Retrieval v3 D-157 — generation-v9r25 one-shot Smoke A PASS

Date: 2026-09-09
Stage: Smoke A exactly-one execution + stability re-audit + durable closure
Generation: `retrieval-v3-dev-generation-v9r25`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260909-v9r25`
D-156 closure base commit: `4d0bfa151493cc5e7560063e2ff660b227e7470a`

## Verdict

**D-157 / v9r25 SMOKE A PASS (sole-executor audits).** The D-156 final bytes consumed exactly one actual v9r25 coordinator model Smoke A. Frozen `audit_coord_smoke.py` returned `SMOKE_PASS` on the first audit and again identically twice more (third after a 13 s stability gap) on the same agent/cwd/session/wrapper evidence. Independent review is **pending**: this stage ran under a sole-execution contract (no subagents/workers/second executor), so no independent auditor rerun occurred here; the next authorized party may rerun the same frozen auditor on the same exact evidence before Smoke B.

**STOP boundary:** Smoke A is permanently consumed/non-repeatable for v9r25. Smoke B has not been executed. No real freeze, PLAN_LOCK/FROZEN_HASHES creation, source-truth snapshot, Phase C, Author/Reviewer/C generation, selector, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append occurred in this stage.

## Fresh prelaunch reconciliation

Immediately before the single frozen launch, the same sole stage executor verified:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `4d0bfa151493cc5e7560063e2ff660b227e7470a`
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- canonical `eval/retrieval-v3/audit/events.jsonl` exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/dev-v2/`, `eval/retrieval-v3/holdout/` paths absent
- D-156 final `GENERATION_PLAN.json`: 76168 bytes, SHA256 `c017d6578bf4a81c73c7960fd62d8b11c25d899e0330a293314d2a219ec9383c`
- `RUBRIC.json` 3334 bytes `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`; `EXCLUSION_INPUTS.json` 4766 bytes `d917de37e2c0b0cd761f9ff72d81906df31546cab6e4af15a5c89f36dd91b857`; `failed_d155_query_fingerprints.json` 24931 bytes `4e1f980dfe48317201941503202f8130bae64ffff13b547e666ce1b7cab551da`
- `author_isolation.mechanics_shas`: 65/65 exact, missing 0, mismatch 0
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, source truth/meta, anchors, slots, author candidates, candidates_merged all absent in the real builder
- one builder-local `__pycache__/role_fs_helper.cpython-311.pyc` created by this stage's own read-only `test_role_tools.py` probe run was removed (only that resolved target; dir removed); plan SHA and mechanics 65/65 reverified unchanged, cache 0 dirs / 0 pyc
- Smoke-A root/cwd absent; exact expected Smoke-A OMP session directory absent
- complete local registry: 360 parseable records, parse errors 0, exact title `D157 v9r25 Smoke A` matches 0, exact dedicated-cwd matches 0
- OMP `18.1.13`; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`
- exact bundled Paseo CLI `C:\Users\joji\AppData\Local\Programs\Paseo\resources\bin\paseo.cmd`, version `0.7.2`
- v9r24 freeze evidence re-verified read-only (hashes only, no plaintext): lock `d084914f...1730b`, hashes `056e789c...85e62d`, run lock `39ab7c47...17c56`, source truth `9fe19465...c1a5`, meta `4c8d3631...da`, anchors `5d264416...ef`, slots `6ba5d97f...52a52` / `2548fcf7...9a`, author1 `4b8bbcc7...0f` / author2 `3ac7af94...66` — all match D-156 §; untouched

No protected plaintext recovery or prohibited git-object/history access was used.

## Smoke A — exactly one actual model launch

A brand-new empty staging cwd was reserved at:

`C:\Users\joji\bc-v3-v9r25-coord-smoke-20260909\cwd`

Frozen `launch_phasec_coordinator.py` was invoked exactly once in `smoke` mode with the exact bundled Paseo CLI and the exact neutral prompt `Call phasec_probe exactly once with {}. Do not call phasec_execute. After the phasec_probe result, stop. Do not use any other tool except todo if needed.` `PYTHONUTF8=1` remained in the frozen launch environment.

Sole stage executor: current repo-cwd session (`muse-spark-1.3-contributor`/`xhigh`/`full`), Parent null, repo cwd `C:\Users\joji\Documents\취준자료\project-repos\benefit-compass`. No second executor/worker/subagent was spawned for this stage.

Observed provenance for the exactly-one coordinator:

- agent: `7989e333-d302-4d8b-886c-0d230c4b9f3c`
- title: `D157 v9r25 Smoke A`
- cwd: `C:\Users\joji\bc-v3-v9r25-coord-smoke-20260909\cwd`
- ParentAgentId: null
- provider/model: `omp` / `opencode-go/muse-spark-1.3-contributor`
- final observed status: `idle` (frozen `verify_coordinator` PASS plus bundled-CLI `wait --timeout 600 --json` rc0)
- OMP fallback provenance: `resolvedModelIsFallback=false` (delta 0.711 s)
- exact OMP session: `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r25-coord-smoke-20260909-cwd\2026-09-09T07-48-18-308Z_01a08523-9b04-77dd-afdd-2de330ce19bf.jsonl`
- stable session lines: 10 (20109 bytes)
- stable session SHA256: `5fea1aa75b1d1f0f419bfaccf5c2d3ce84f9d036e8b1040ccd99d2ead4c7032b`
- transcript tool calls: `phasec_probe=1`, `todo=0`
- forbidden tool calls: 0
- frozen wrapper log: exactly 1 row, 547 bytes, SHA256 `36cd121f5dff17a474258e27557899d9c5657282f2439ae5c577a2bcf429c44d`
- wrapper tools/mode: `todo` / `smoke`
- wrapper controls: `--tools=todo`, `-e`, `--no-extensions`, `--no-skills`, `--no-rules`
- wrapper extension: 5013 bytes, SHA256 `037db26c8dbc6b89f381135a60e1c835460941eb8ce9e456a7b689a584bf6c88`
- descendants: 0
- fallback proven by frozen auditor: true

First frozen auditor result: rc0 `SMOKE_PASS`.

The exact same frozen auditor was run twice more against the same agent/cwd/session/wrapper evidence (third after a 13 s stability sleep). All three returned rc0 `SMOKE_PASS` with the session path, 10-line count, SHA256, `phasec_probe=1`, `todo=0`, descendants 0, fallback proof, and wrapper surface unchanged.

No second v9r25 Smoke A launcher invocation occurred. No stop/abort/repair was performed.

## Post-Smoke-A boundary

Post-audit reconciliation:

- final v9r25 plan remains SHA256 `c017d6578bf4a81c73c7960fd62d8b11c25d899e0330a293314d2a219ec9383c`, 76168 bytes
- mechanics remain 65/65 exact; builder cache 0 dirs / 0 pyc (`python -B`, no bytecode)
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, source truth/meta, anchors, slots, author candidates, candidates_merged remain absent
- complete registry now has 361 parseable records, parse errors 0, and exactly one D-157 dedicated Smoke-A title/cwd record: `7989e333-d302-4d8b-886c-0d230c4b9f3c` (exact title=1, exact cwd=1, exact both=1)
- Smoke-A OMP session directory exists with the exact one `.jsonl` session file above
- Smoke-A agent remains idle and its frozen wrapper process/evidence is preserved
- later-stage roots absent: `C:\Users\joji\bc-v3-v9r25-lifecyclesmoke`, `C:\Users\joji\bc-v3-v9r25-phaseC`, `C:\Users\joji\bc-v3-v9r25-coord-execute-20260909`
- canonical audit remains exactly 4 rows with unchanged SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- production `ml-service/` remains unchanged (diff0)
- protected dev/dev-v2/holdout plaintext paths remain absent
- v9r24 runtime/freeze evidence untouched (read-only hash verification only)
- repo HEAD/upstream/direct-origin remained D-156 base `4d0bfa1` and clean through closure except the three authorized durable D-157 files (this doc + append-only DECISIONS/SESSION-LOG)

## Gate boundary

V9r25 has now consumed **Smoke A exactly once and PASSed (sole-executor audits; independent rerun pending)**. Smoke A is permanently non-repeatable for this generation, regardless of any future stage result.

Next, only after another separate fresh user `진행해` (and preferably after an independent rerun of the frozen auditor on the exact evidence above), is **Smoke B duplicate/preflight + exactly-one lifecycle Smoke B**. Smoke B must not be silently consumed in D-157. Real freeze, Phase C, protected dev-v2, holdout, production, and canonical audit append remain prohibited until their later gates.

## D-157 CORRECTION — executor provenance pin (no runtime)

- Initial closure described the sole stage executor generically. Pinned read-only from the executor's own process environment plus its exact local-registry record (no model/Paseo launch, no session-plaintext read): executor `ad48ef61-1877-45db-b4e5-ee48511c3c54`, registry title `D157 v9r25 Smoke A executor`, cwd exactly the repo path, labels `{}` (top-level, no parent binding), `PASEO_CLI` env exactly the frozen bundled pin `C:\Users\joji\AppData\Local\Programs\Paseo\resources\bin\paseo.cmd`.
- Sole-executorship proof from the complete registry at correction time: 361 parseable records / 0 errors (unchanged since post-run), records with `paseo.parent-agent-id` equal to the executor exactly 0 (no subagent/worker/child spawned), and still exactly one `D157 v9r25 Smoke A` title record (`7989e333-d302-4d8b-886c-0d230c4b9f3c`). No second launcher invocation exists.
- Verdict unchanged. **D-157 SMOKE A PASS stands on final bytes. STOP before Smoke B.**
