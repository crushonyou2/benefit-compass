# Retrieval v3 D-129 — generation-v9r20 one-shot Smoke A PASS

Date: 2026-09-08
Stage: Smoke A duplicate/provenance gate / exactly-one execution closure
Generation: `retrieval-v3-dev-generation-v9r20`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r20`
D-128 corrected pre-smoke base commit: `c95dee0bcb033b63025ce60bc60a93da8d6a7261`

## Verdict

**SMOKE A PASS.** The D-128 corrected final bytes consumed exactly one actual v9r20 coordinator model Smoke A. Frozen `audit_coord_smoke.py` returned `SMOKE_PASS` twice on the same evidence with a 12-second stability interval; the session remained exactly 10 lines with the same SHA256. No second Smoke A was launched.

**STOP boundary:** Smoke B has not been executed and is not authorized by this record. No real freeze, Phase C, source-truth snapshot, Author/Reviewer/C generation, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append occurred in this stage. The next logical stage is a separate Smoke-B duplicate/preflight gate.

## Prelaunch reconciliation

Immediately before the single frozen launch:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `c95dee0bcb033b63025ce60bc60a93da8d6a7261`
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- main-tree protected `eval/retrieval-v3/dev/` and `eval/retrieval-v3/holdout/` plaintext paths absent
- canonical audit exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- corrected plan SHA256 `4baf17f208db63a27948cf1b11ac88f87b052f0f8db7f0f5468a1267023be542`, 64,375 bytes
- exclusion manifest SHA256 `822f39b80831f580df5f3e1e82b9a22c93e047381a8512a53536e1e941daf28b`
- rubric SHA256 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- mechanics 58/58 exact, mismatch 0
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock` absent
- builder `__pycache__` count 0
- actual OMP `omp/18.1.13`; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`
- exact bundled Paseo CLI `C:\Users\joji\AppData\Local\Programs\Paseo\resources\bin\paseo.cmd`, CLI/daemon version `0.7.2`, daemon running/reachable
- complete local registry: 316 parseable records, v9r20 title/cwd matches 0
- v9r20 matching processes 0
- Smoke-A root `C:\Users\joji\bc-v3-v9r20-coord-smoke-20260908` absent
- exact expected Smoke-A OMP session directory absent

No protected plaintext recovery or prohibited git-object access was used.

## Smoke A — exactly one actual model launch

A brand-new empty staging cwd was reserved at:

`C:\Users\joji\bc-v3-v9r20-coord-smoke-20260908\cwd`

Frozen `launch_phasec_coordinator.py` was invoked exactly once in `smoke` mode with the exact bundled Paseo CLI and a neutral deterministic prompt requiring exactly one `phasec_probe` call and no other tool call.

Observed evidence:

- agent: `073260d6-9987-4ae9-9e1d-15594ae25b44`
- title: `D129 v9r20 Smoke A`
- created: `2026-09-07T21:02:16.424Z`
- cwd: `C:\Users\joji\bc-v3-v9r20-coord-smoke-20260908\cwd`
- ParentAgentId: null
- provider/model: `omp` / `opencode-go/muse-spark-1.3-contributor`
- thinking: `xhigh`
- mode: `full`
- final observed status: `idle`
- OMP fallback provenance: `resolvedModelIsFallback=false`
- exact session: `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r20-coord-smoke-20260908-cwd\2026-09-07T21-02-15-911Z_01a07dad-c767-7176-88ab-b08967c6a7c2.jsonl`
- stable session lines: 10
- stable session SHA256: `bebcc3da0155b01be4d31167c4b0f81a141b0449ea039ebf14035c0aba305b73`
- transcript tool calls: `phasec_probe=1`
- forbidden tool calls: 0
- frozen wrapper log: exactly 1 row; SHA256 `a79a70d05e7ac22b6335a9db51aeb54091fb7f3385c3735658b363883f1b5455`
- wrapper tools/mode: `todo` / `smoke`
- exact wrapper controls: `--tools=todo`, `-e`, `--no-extensions`, `--no-skills`, `--no-rules`
- descendants: 0 by inspect strict-if-present plus complete repaired local-registry scan
- fallback proven by frozen auditor: true
- frozen auditor: rc0 `SMOKE_PASS`

The frozen auditor was re-run after 12 seconds against the same agent/cwd/session/wrapper evidence. Verdict remained `SMOKE_PASS`; session remained exactly 10 lines with SHA256 `bebcc3da0155b01be4d31167c4b0f81a141b0449ea039ebf14035c0aba305b73`, `phasec_probe=1`, descendants 0, and the same frozen wrapper surface.

No second Smoke A launch occurred.

## Post-Smoke-A boundary

Post-audit reconciliation:

- corrected D-128 plan remains `4baf17f208db63a27948cf1b11ac88f87b052f0f8db7f0f5468a1267023be542`
- mechanics remain 58/58 exact
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock` remain absent
- complete registry now contains 317 parseable records and exactly one v9r20 title/cwd match: the Smoke-A agent above
- v9r20 lifecycle-Smoke registry matches: 0
- Smoke-B root `C:\Users\joji\bc-v3-v9r20-lifecyclesmoke` absent
- Smoke-B OMP session directory absent
- v9r20 lifecycle-Smoke matching processes: 0
- Smoke-A OMP session directory exists with exactly one `.jsonl` file
- Smoke-A agent remains idle and preserved
- canonical audit remains 4 rows with unchanged SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- production `ml-service/` unchanged
- protected dev/holdout plaintext paths remain absent

Frozen-auditor imports created two builder-local `__pycache__` directories. Their resolved paths were verified inside the v9r20 builder and only those cache directories were removed; final builder cache count is 0.

## Gate boundary

V9r20 has now consumed **Smoke A exactly once and PASSed**. Smoke A is permanently non-repeatable for this generation.

Next, if separately approved, is **Smoke B duplicate/preflight + exactly-one execution only**. Smoke B must not be silently consumed in D-129. Real freeze, Phase C, protected dev-v2, holdout, and production remain prohibited until their later gates.
