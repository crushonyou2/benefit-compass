# Retrieval v3 D-167 — generation-v9r29 one-shot Smoke A PASS

Date: 2026-09-10 (KST)
Stage: Smoke A prelaunch reconcile + exactly-one frozen execution + stability re-audit + durable closure
Generation: `retrieval-v3-dev-generation-v9r29`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260910-v9r29`
D-166 closure base commit: `886e394972556aecf9adb7b7ad3b24b477628cfc`

## Verdict

**D-167 / v9r29 SMOKE A PASS.** The D-166 final bytes consumed exactly one actual v9r29 coordinator-model Smoke A through the frozen Core executor transport. The sole Core call terminated normally with process rc0 and returned agent `a810d782-bf58-49a5-b882-72178c22f08f`. Frozen `audit_coord_smoke.py` then returned rc0 `SMOKE_PASS` twice on the same exact agent/cwd/session/wrapper evidence with identical session path, 10-line count, SHA256, `phasec_probe=1`, descendants 0, wrapper surface, and fallback proof.

**STOP boundary:** Smoke A is permanently consumed/non-repeatable for v9r29. Smoke B has not been executed. No real freeze, `PLAN_LOCK.json`/`FROZEN_HASHES.json`, source-truth snapshot, Phase C, semantic Author/Reviewer/C generation, selector, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append occurred in D-167.

## Fresh D-167 prelaunch reconciliation

Immediately before the frozen one-shot:

- branch `codex/retrieval-v3-user-search-quality`
- local HEAD = upstream = direct origin `886e394972556aecf9adb7b7ad3b24b477628cfc`; working tree clean; `git diff --check` PASS
- D-166 closure had been pushed and local/upstream/direct-origin equality reverified
- actual global OMP config `C:\Users\joji\.omp\agent\config.yml`: `default` and `plan` both `opencode-go/muse-spark-1.3-contributor:xhigh`; no repo-local `.omp` overlay
- fixed OMP binary reports `omp/18.1.13`; bundled Paseo reports `0.7.2`
- ambient `PASEO_CLI`, `OMP_MODEL`, `OMP_PROVIDER`, `OMP_THINKING`, `OMP_ROLE`, and `OMP_CONFIG` overrides were empty; fixed OMP/Paseo paths existed
- v9r29 primary hashes 10/10 exact; mechanics 69/69 exact
- builder freeze/runtime artifacts absent; cache 0 dirs / 0 pyc; Smoke-A root absent
- canonical `eval/retrieval-v3/audit/events.jsonl` remained exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/dev-v2/`, `eval/retrieval-v3/holdout/` absent
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- immutable v9r28 predecessor key hashes 8/8 exact

No protected plaintext recovery, prohibited git-object access, retrieval/benchmark/model evaluation, or production mutation was performed by the prelaunch gate.

## Frozen one-shot execution

The exact D-167 process call was issued once and only once:

- tool: `Chat_On_Steroids_Core.exec_command`
- executor workdir: `/programming/bc-v3-dev-v2-builder-20260910-v9r29`
- scalar `cmd`: `python -B run_smoke_a_once.py`
- `yield_time_ms=30000`
- no `cmds` field, absolute/mapped script path, `./` qualification, shell `cd`/composition, wrapper, or extra runner argument

The call returned a terminal process result, not a live/nonterminal session:

- process rc: `0`
- output agent: `a810d782-bf58-49a5-b882-72178c22f08f`
- runtime cwd: `C:\Users\joji\bc-v3-v9r29-coord-smoke-20260910\cwd`
- title: `D167 v9r29 Smoke A`

No retry, correction, second Smoke-A launcher invocation, or `write_stdin` occurred.

## Smoke-A provenance and frozen audits

Read-only bundled-Paseo inspect after launch showed:

- agent `a810d782-bf58-49a5-b882-72178c22f08f`
- title `D167 v9r29 Smoke A`
- ParentAgentId `null`
- provider/model `omp` / `opencode-go/muse-spark-1.3-contributor`
- thinking `xhigh`; mode `full`; final observed status `idle`
- exact cwd `C:\Users\joji\bc-v3-v9r29-coord-smoke-20260910\cwd`
- CreatedAt `2026-09-09T19:24:52.004Z`

Frozen `audit_coord_smoke.py` was run read-only twice against the same agent/cwd in `smoke` mode. Both runs returned the same rc0 evidence:

- verdict `SMOKE_PASS`
- exact OMP session `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r29-coord-smoke-20260910-cwd\2026-09-09T19-24-51-432Z_01a087a1-5168-74ff-8aa9-2dcd79f56e88.jsonl`
- session lines `10`
- session SHA256 `c5e29e457c6a657c951246f2056f79b4c8b5f96adc40131cc06ad30a139f8b0f`
- tool calls `{phasec_probe: 1}`; required calls `1`; no forbidden tool call reported
- wrapper tools/mode `todo` / `smoke`
- wrapper controls exactly `--tools=todo`, `-e`, `--no-extensions`, `--no-skills`, `--no-rules`
- descendants `0`
- OMP fallback provenance proven `true` (`resolvedModelIsFallback=false`)

The frozen wrapper log exists at `C:\Users\joji\bc-v3-v9r29-coord-smoke-20260910\cwd\wrapper_invocation.log`, 546 bytes, SHA256 `0e4794b0e81e7a7a3e00773c3276313fadaf25a61128f44737802bb1d5ff71ae`.

A later direct PowerShell `Get-FileHash` attempt on the live OMP session file hit a Windows sharing violation. This is not a generation blocker: both prior frozen-auditor passes had already directly read and SHA-verified the same session bytes as 10 lines with the identical `c5e29e45...` SHA. No session/runtime repair or mutation followed.

## Post-Smoke-A boundary

Post-audit read-only reconciliation proved:

- v9r29 primary hashes remain 10/10 exact
- `GENERATION_PLAN.author_isolation.mechanics_shas` remains 69/69 exact, mismatch 0
- builder cache remains 0 dirs / 0 pyc
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, source truth/meta, anchors, slots, author candidates, candidates merged, raw/keymap/agreement/C/final artifacts remain absent
- Smoke-B root `C:\Users\joji\bc-v3-v9r29-lifecyclesmoke` absent
- Phase-C root `C:\Users\joji\bc-v3-v9r29-phaseC` absent
- Smoke-A agent remains idle and its runtime/session/wrapper evidence is preserved
- repo remained local/upstream/direct-origin equal at D-166 base `886e394...` and clean before this durable record
- canonical audit remains 4 rows / SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- protected dev/dev-v2/holdout paths remain absent
- production `ml-service/` diff remains 0
- immutable v9r28 predecessor key hashes remain 8/8 exact

## Gate boundary

V9r29 has now consumed **Smoke A exactly once and PASSed**. Smoke A is permanently non-repeatable for this generation regardless of any future-stage result.

**D-167 SMOKE A PASS. STOP before Smoke B.** A next separately explicit user continuation may authorize only a fresh Smoke-B duplicate/preflight gate and, if that gate passes, exactly-one lifecycle Smoke B. Real freeze, source truth, Phase C, semantic roles, protected dev-v2, holdout, production, and canonical audit append remain prohibited until their own later gates.
