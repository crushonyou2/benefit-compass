# Retrieval v3 D-137 — generation-v9r22 one-shot Smoke A PASS

Date: 2026-09-08
Stage: Smoke A duplicate/runtime/provenance gate / exactly-one execution closure
Generation: `retrieval-v3-dev-generation-v9r22`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r22`
D-136 pre-smoke base commit: `40843939170fdd6fdf041bf01d8f3f3c074286d9`

## Verdict

**D-137 / v9r22 SMOKE A: PASS.** The D-136 final bytes consumed exactly one actual coordinator model Smoke A. The frozen auditor and independent Web re-audits repeatedly returned `SMOKE_PASS` on the same preserved evidence. The exact OMP session is 10 lines with SHA256 `d44b30c60491205b387c4ae6614d53015f4f4279255a3d656f7ff7cc9fdaaf5c`, contains exactly one `phasec_probe` tool call and no other tool call, ends with assistant text `SMOKE_DONE`, has zero descendants, and proves fallback=false provenance.

No second Smoke A launch occurred. Smoke A is permanently consumed and non-repeatable for v9r22.

**STOP boundary:** Smoke B was not executed in D-137. No real freeze, Phase C, source-truth snapshot, Author/Reviewer/C generation, selector, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append occurred. The next logical stage is a separate Smoke-B duplicate/preflight gate and, only if that fresh gate passes, exactly one Smoke B.

## Prelaunch reconciliation

Before the actual Smoke launch, Web reconciled:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `40843939170fdd6fdf041bf01d8f3f3c074286d9`
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- canonical audit exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/holdout/`, and `eval/retrieval-v3/dev-v2/` absent
- plan `GENERATION_PLAN.json` 66,960 bytes SHA256 `58c862958dc2167b3a2ca7dab9ddb94af8f0c8a57fff307cd6cd89d354a821f3`
- exclusion manifest SHA256 `df59034f3d6022d7be89268d6bd642cbcd6c0b8d4fa553364801b18c85399ddc`
- rubric SHA256 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- freeze mechanic SHA256 `9d59c80e14e10c237bf2ea56e50b5bb3278160867df6efa71325aa7552c8f769`
- mechanics 59/59 exact, mismatch 0
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, `source_truth.jsonl` absent
- expected Smoke-A root and OMP session directory absent before launch
- complete local registry initially parseable with no actual Smoke-A cwd/session match
- actual OMP `18.1.13`; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`
- exact bundled Paseo `0.7.2`

The non-model pre-gate battery re-passed CLI64, preflight36, reachability87, lifecycle53, role-tools202, completion, confinement212, freeze-binding66, strict timestamp/rerun66, staging24, TWELVE66 overlap0, slot/location6+5, and registry37.

Those review tests generated builder-local Python cache files because one frozen regression explicitly calls `py_compile.compile`. The files were not source/support mechanics and are excluded from frozen hashes. Their paths were resolved inside the exact v9r22 builder; only those `__pycache__` directories were removed. Source/support SHA pins remained 59/59 exact. This was review-side hygiene, not generation execution or a contract failure.

## Sole D-137 execution machinery

The exactly-one Smoke execution was delegated to one Paseo/OMP stage-machinery agent:

- executor agent `d0d9e5c2-ed27-4d3d-ba1e-93eaa118c56b`
- title `D137 v9r22 Smoke A executor`
- cwd main repo
- provider/model `omp` / `opencode-go/muse-spark-1.3-contributor`
- thinking `xhigh`, mode `full`, final status `idle`
- execution prompt SHA256 `1d86bb4872569c39ed94bdc7e08aa7e5a97f2e2b33c9bfb4b4b85153b3ea219a`

The executor is stage machinery, not generation Smoke evidence. Its title contains the string `v9r22 Smoke A`, so a generic registry text search can see it; duplicate accounting therefore uses the actual frozen-launcher Smoke cwd/session/agent identity, not title-token matching. The actual Smoke identity below is unique on that exact cwd/session boundary.

## Smoke A — exactly one actual model launch

A brand-new empty staging cwd was used:

`C:\Users\joji\bc-v3-v9r22-coord-smoke-20260908\cwd`

Frozen `launch_phasec_coordinator.py` was invoked exactly once in `smoke` mode. The prompt instructed the model to call `phasec_probe` exactly once with `{}`, call no other tool, then reply exactly `SMOKE_DONE` and stop.

Observed evidence:

- actual Smoke agent `44e5d9f9-ddec-48f9-a9e7-5f0fc6a2e4de`
- title `D137 v9r22 Smoke A`
- created `2026-09-08T06:19:34.858Z`
- final update `2026-09-08T06:19:48.537Z`
- cwd exact `C:\Users\joji\bc-v3-v9r22-coord-smoke-20260908\cwd`
- ParentAgentId null
- provider/model `omp` / `opencode-go/muse-spark-1.3-contributor`
- thinking `xhigh`
- mode `full`
- final status `idle`
- exact session `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r22-coord-smoke-20260908-cwd\2026-09-08T06-19-34-296Z_01a07fac-0218-7361-b915-fa0926141c76.jsonl`
- stable session lines 10
- stable session SHA256 `d44b30c60491205b387c4ae6614d53015f4f4279255a3d656f7ff7cc9fdaaf5c`
- independently parsed transcript tool calls exactly `{"phasec_probe": 1}`
- final assistant text `SMOKE_DONE`
- wrapper log `C:\Users\joji\bc-v3-v9r22-coord-smoke-20260908\cwd\wrapper_invocation.log`
- wrapper exactly one row / 547 bytes / SHA256 `467a6093006eb5ef7ee9b81003f872ba883c70d3e51a1f665ae1187eb9236d9c`
- wrapper tools/mode `todo` / `smoke`
- exact controls `--tools=todo`, `-e`, `--no-extensions`, `--no-skills`, `--no-rules`
- frozen coordinator extension SHA256 `3871b68603e510f6b06584f1fa20a6b5ef95d06f4697787c72d6cb1c3999f4e6`
- descendants 0
- fallback proven true

The executor ran the frozen auditor twice with a 12-second stability interval. Web independently ran the same frozen auditor again and then repeated it after another 12-second interval. Every invocation returned rc0 `SMOKE_PASS` on the same session path, same 10 lines, same SHA, `phasec_probe=1`, same one-row wrapper evidence, descendants0, and fallback proven.

No second Smoke A launch occurred.

## Post-run contract concern and controlling precedent

A post-run review correctly observed that `audit_coord_smoke.py` mechanically permits tool-call names in `{todo, phasec_probe}` and requires `phasec_probe >= 1`; `freeze_plan_v9r22.py` reuses that frozen auditor and stores the reported tool-call counts. It therefore does not itself reject a hypothetical transcript containing multiple probes or an allowed `todo` call.

This is **not a new operative hard blocker** under the existing Retrieval-v3 contract. D-121 is the controlling durable precedent and explicitly defines the operative Smoke-A gates as exact top-level provenance, exact-one wrapper invocation, tool-call subset `{todo, phasec_probe}`, `phasec_probe >= 1`, and descendants0; it treats prompt wording as descriptive rather than a separate gate. D-131 later cites D-121 for the same distinction. Promoting the hypothetical stricter predicate to a new hard gate here would add a gate not present in the standing contract.

The current v9r22 evidence additionally satisfies the stricter prompt behavior anyway: direct parsing of the preserved/stable session shows exactly one `phasec_probe`, no `todo` or other tool call, and `SMOKE_DONE`. The frozen auditor's output truthfully binds `tool_calls={phasec_probe:1}` and `required_calls=1`; there is no actual false-positive Smoke result analogous to D-096, where the runtime itself violated filesystem confinement.

Accordingly, the earlier review suggestion to classify the auditor's hypothetical acceptance surface as `CONTRACT_INVALID_GENERATION` is superseded by the D-121 standing contract plus the actual v9r22 transcript evidence. No v9r22 source byte is changed for this interpretation.

## Post-Smoke-A boundary

After stable re-audit and cache cleanup:

- plan remains SHA256 `58c862958dc2167b3a2ca7dab9ddb94af8f0c8a57fff307cd6cd89d354a821f3`
- mechanics remain 59/59 exact, mismatch 0
- builder cache / `.pyc` count 0
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, `source_truth.jsonl` remain absent
- complete local Paseo registry contains 325 parseable JSON records, parse errors 0
- exactly one record matches the actual Smoke-A cwd/agent identity: `44e5d9f9-ddec-48f9-a9e7-5f0fc6a2e4de`
- actual Smoke-A OMP session directory exists and contains the preserved session above
- Smoke-B root `C:\Users\joji\bc-v3-v9r22-lifecyclesmoke` absent
- Smoke-B OMP session directory absent
- actual Smoke agent and stage executor are both idle; the successful Smoke agent is not stopped or mutated
- canonical audit remains 4 rows with SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- production `ml-service/` remains unchanged
- protected dev/holdout/dev-v2 paths remain absent
- repo remained clean/local=upstream=direct origin at D-136 commit before this docs-only closure

## Gate boundary

V9r22 has consumed **Smoke A exactly once and PASSed**. Smoke A is permanently non-repeatable for this generation.

Next, only in a separately authorized logical stage, is **Smoke B duplicate/preflight + exactly-one execution**. Smoke B must not be silently consumed in D-137. Real freeze, Phase C, protected dev-v2, holdout, and production remain prohibited until their later gates.
