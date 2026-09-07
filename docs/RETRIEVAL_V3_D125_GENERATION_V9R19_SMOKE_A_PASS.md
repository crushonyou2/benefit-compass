# Retrieval v3 D-125 — generation-v9r19 one-shot Smoke A PASS

Date: 2026-09-08
Stage: Smoke A pre-gate / exactly-one execution closure
Generation: `retrieval-v3-dev-generation-v9r19`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r19`
D-124 base commit: `4e7a2a9b13e03b33c8a9d3c11265936af728a3dc`

## Verdict

**SMOKE A PASS.** The D-124 final bytes consumed exactly one actual v9r19 coordinator model Smoke A. Frozen `audit_coord_smoke.py` returned `SMOKE_PASS` twice on the same evidence with a 12-second stability interval; session bytes and line count were unchanged. No second Smoke A was launched.

**STOP boundary:** Smoke B has not been executed and is not authorized by this record. No real freeze, Phase C, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append occurred in this stage. The next logical stage is a separate Smoke-B duplicate/preflight gate.

## Prelaunch reconciliation

Immediately before the actual frozen launch:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `4e7a2a9b13e03b33c8a9d3c11265936af728a3dc`
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- main-tree protected dev/holdout plaintext paths absent
- canonical audit exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- plan SHA256 `a442f5641f1dbada08ce5eeb71b838746910c58c8b979e25bacc24a134420705`
- exclusion manifest SHA256 `1caffc012103abea5c85487588bd0c6daaea2766e90cc41cb113569086f56e3b`
- rubric SHA256 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- mechanics 57/57 exact by bytes + SHA
- exact TWELVE query-fingerprint sets; required overlap 0
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock` absent
- actual OMP `omp/18.1.13`; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`
- exact bundled Paseo CLI only: `C:\Users\joji\AppData\Local\Programs\Paseo\resources\bin\paseo.cmd`, version `0.7.2`; daemon `running/reachable`
- all-global/all-status v9r19 Paseo agents 0
- v9r19 OMP session directories 0
- v9r19 matching processes 0
- Smoke-A staging root absent before reservation

No protected plaintext recovery or prohibited git-object access was used.

## Pre-model harness incident — not a Smoke consumption

After the final duplicate gate, the root procedure reserved `C:\Users\joji\bc-v3-v9r19-coord-smoke-20260908\cwd`, then a caller-side Python `-c` import harness failed with `ModuleNotFoundError: No module named 'launch_phasec_coordinator'` **before the frozen launcher was invoked**.

Immediate read-only recovery proof showed:

- reserved cwd existed and contained 0 items
- `wrapper_invocation.log` absent
- all-global v9r19 Paseo agents 0
- v9r19 OMP session directories 0
- v9r19 matching processes 0

Therefore no Paseo/model/agent/session/wrapper invocation occurred and Smoke A remained unconsumed. This is the same lifecycle distinction already recorded in D-112 for a pre-agent/session/wrapper transport failure. No frozen byte was repaired or changed. The same still-empty reserved cwd was then used for the one actual frozen launch below.

## Smoke A — exactly one actual model launch

Frozen `launch_phasec_coordinator.py` was invoked once in `smoke` mode on the D-124 final bytes with the exact bundled Paseo CLI and a neutral deterministic prompt requiring one `phasec_probe` call.

Evidence:

- agent: `5c235429-3a47-43a1-b4a9-596dec662c7d`
- cwd: `C:\Users\joji\bc-v3-v9r19-coord-smoke-20260908\cwd`
- created: `2026-09-07T19:56:25.431Z`
- ParentAgentId: null
- provider/model: `omp` / `opencode-go/muse-spark-1.3-contributor`
- thinking: `xhigh`
- mode: `full`
- final observed status: `idle`
- OMP fallback provenance: `resolvedModelIsFallback=false`
- exact session: `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r19-coord-smoke-20260908-cwd\2026-09-07T19-56-24-840Z_01a07d71-7d88-7764-adea-3e4a24ba218e.jsonl`
- stable session lines: 10
- stable session SHA256: `86bc67edfd674daae98df4be119c3022ecd000c08b2fd00f6ab0350cd8e3d313`
- transcript tool calls: `phasec_probe=1`
- frozen wrapper: tools `todo`, mode `smoke`, custom tool `phasec_probe`
- exact wrapper controls: `--tools=todo`, `-e`, `--no-extensions`, `--no-skills`, `--no-rules`
- coordinator extension SHA256: `bf2e37c1b69ed6c168fdce085c300f1fd418f22d05279197e57e1d368d019254`
- descendants: 0
- fallback proven: true
- frozen auditor: rc0 `SMOKE_PASS`

The frozen auditor was re-run after 12 seconds against the same agent/cwd/session/wrapper evidence. Verdict remained `SMOKE_PASS`; session remained exactly 10 lines with SHA256 `86bc67edfd674daae98df4be119c3022ecd000c08b2fd00f6ab0350cd8e3d313`.

No second Smoke A launch occurred.

## Post-Smoke-A boundary

Post-audit revalidation:

- D-124 plan / manifest / rubric SHAs unchanged
- mechanics still 57/57 exact
- `PLAN_LOCK.json`: absent
- `FROZEN_HASHES.json`: absent
- `phasec_driver.run.lock`: absent
- Smoke-B staging root: absent
- Smoke-B OMP session directories: 0
- Smoke-A agent remains idle and preserved
- canonical audit remains 4 rows with SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- production `ml-service/` unchanged
- protected dev/holdout untouched

Auditor imports created two builder-local `__pycache__` directories only. Their resolved absolute paths were proven inside the v9r19 builder and only those two cache directories were removed. Final cache count is 0; frozen/source/support bytes were not changed.

## Gate boundary

V9r19 has now consumed **Smoke A exactly once and PASSed**. Smoke A is permanently non-repeatable for this generation.

Next, if separately approved, is **Smoke B duplicate/preflight + exactly-one execution only**. Smoke B must not be silently consumed in this D-125 stage. Real freeze, Phase C, protected dev-v2, holdout, and production remain prohibited until their own later gates.
