# Retrieval v3 D-113 — generation-v9r17 PRE-SMOKE Web PASS

Date: 2026-09-07
Stage: fresh D-112 lifecycle-infrastructure successor + independent final-byte PRE-SMOKE review
Generation: `retrieval-v3-dev-generation-v9r17`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260907-v9r17`

## Verdict

**v9r17 PRE-SMOKE: PASS.** v9r17 is a fresh successor after D-112 closed v9r16 `CONTRACT_INVALID_GENERATION`. It preserves the D-110 writer-envelope repair and makes a narrow D-112 transport/provenance repair: all coordinator/role Paseo launches resolve only the frozen bundled CLI `C:\Users\joji\AppData\Local\Programs\Paseo\resources\bin\paseo.cmd`; arbitrary `PASEO_CLI`, desktop `Paseo.exe`, relative/PATH fallback, and nonexistent alternates fail closed before any subprocess/model launch. The agent-specific PATH prepend remains only for OMP wrapper reachability.

No v9r17 model smoke, freeze, Phase C, source-truth snapshot, semantic role, protected evaluation, holdout evaluation, production change, or canonical audit append occurred in D-113.

## Reconciled base

Canonical repo at review: branch `codex/retrieval-v3-user-search-quality`, HEAD/local/upstream/direct remote `8a0a2b687e7394dc57c97ad532a3af4bd6b06e4f` (D-112), clean; production `ml-service/` diff zero; canonical audit exactly 4 events SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`.

OMP `18.1.5`; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`. Bundled Paseo CLI status reports local daemon running / connected daemon reachable, CLI+daemon 0.7.2.

v9r16 remains immutable D-112 failure evidence; no v9r16 smoke/runtime/semantic rows are reused as v9r17 PASS evidence.

## D-112 repair

- `launch_top_level_paseo.py` and `launch_phasec_coordinator.py` accept only the frozen bundled `paseo.cmd` (Windows case-insensitive path equality); no `shutil.which("paseo")` / PATH discovery for Paseo.
- Wrong/desktop/arbitrary/relative/nonexistent `PASEO_CLI` fails before subprocess/model launch.
- `coord_wrapper_tpl/phasec_driver.py` already uses the same fixed bundled command; v9r17 keeps path parity.
- D-110 writer envelope remains: `{chunk, lines}`, exact chunk `"0".."5"`, role row-count preflight before helper spawn, derived fixed target, helper zero-deny authorization unchanged.
- Helper old-builder/provenance deny set now includes v9r16 lineage tokens; D-112 contributes no new exclusion set/candidate rows.

## Independent final-byte validation

- Paseo CLI gate: `PASEO_CLI_GATE_PASS` — 64 checks
- D-110 writer preflight: `PREFLIGHT_PASS` — 36 checks
- launcher reachability: `REACHABILITY_PASS` — 87 checks
- lifecycle contract: `LIFECYCLE_CONTRACT_PASS` — 53 checks
- role tools: `ROLE_TESTS_PASS` — 170 checks
- completion: `GATE_TESTS_PASS`
- TEN: 45 pairs, overlap 0; counts `180/250/248/273/273/360/360/365/360/360` (UTF-8 mode; default cp949 failure is transport-only)
- confinement: `CONFINEMENT_TESTS_PASS` — 204 checks
- freeze binding: `FREEZE_BINDING_PASS` — 66 checks
- Python compileall PASS
- Bun role probe PASS
- Bun coordinator probe PASS
- TypeScript `tsc --noEmit` PASS
- generation-plan mechanics SHA map: 55 entries, mismatch 0; both `test_paseo_cli_gate.py` and `test_role_write_preflight.py` included
- 22 semantic/selection/prompt core files are byte-equivalent to v9r16 after v9r17→v9r16 identity normalization

Final builder: 68 source/support files, cache 0, no `PLAN_LOCK.json`, `FROZEN_HASHES.json`, run lock, source truth, evalset, `out/`, or smoke/session roots.

Key SHA256:
- `GENERATION_PLAN.json` `6b879951ce0921d655ee09d7d74f10f39afad703031684788dca35b2a4d51600`
- `freeze_plan_v9r17.py` `2d35b64c598a0ddc1df42192865b9255bfb07e4a2a1fcf41f6050cf4fd6928c9`
- `test_paseo_cli_gate.py` `b19b94bcb7d5724ef3319cbe023f26635a09530d6c5578928eecdc7f8e5b4381`
- `test_role_write_preflight.py` `1e87e07e6bffb2d4097e4b769685c6b94f74f16585f0549eb4d70cd59c813503`
- `launch_top_level_paseo.py` `a534a66bc0d8f9fad6edf8e4c4fa25eb1f9fd8d6897721a464a1aa0cbf5274c9`
- `launch_phasec_coordinator.py` `b5c02f907df7ee79d9e3bf2a4cbe2bce1cc76d318aa66e9b465a6a3ca713bc8a`
- `coord_wrapper_tpl/phasec_role_ext.ts` `7338595525938fa3e902113e5310156759674b43fe68e1c2c029f2c9a6b07093`
- `RUBRIC.json` `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- `input/EXCLUSION_INPUTS.json` `bda24abb1e0a663c990449b65616f4175c4c1dfc439fec80058917c09e7fcbd4`

Implementation executor provenance: OMP session `C:\Users\joji\.omp\agent\sessions\-Documents-programming\2026-09-06T17-38-59-463Z_01a077cd-5107-71a8-8c16-7881f664eae8.jsonl`, model `opencode-go/muse-spark-1.3-contributor`, fallback false, 588 lines, SHA256 `758594011a2fc2be2e7403c9e7ff7f4f53a227cdb32d3fd4c8887b29785a3970`.

## Next gate

Exactly one v9r17 Smoke A may be launched on these exact bytes only after a final duplicate-prelaunch check. Only frozen-auditor PASS permits exactly one Smoke B. Any actual smoke failure closes v9r17 with no retry/same-generation repair. Real freeze and Phase C remain forbidden until both smokes pass and their evidence is durably reviewed.
