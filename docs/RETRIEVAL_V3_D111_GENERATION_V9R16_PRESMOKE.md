# Retrieval v3 D-111 — generation-v9r16 PRE-SMOKE Web PASS

Date: 2026-09-07
Stage: fresh successor construction + independent final-byte PRE-SMOKE review
Generation: `retrieval-v3-dev-generation-v9r16`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260907-v9r16`

## Verdict

**v9r16 PRE-SMOKE: PASS.** v9r16 is a fresh successor after D-110 closed v9r15 `CONTRACT_INVALID_GENERATION`. The D-110 repair is limited to the model-facing writer envelope: semantic roles still call `role_write_chunk`, but the model supplies `{chunk, lines}` rather than a filesystem-shaped name. The extension validates exact chunk identity and role-bound row count before any helper spawn, derives the exact `out/chunk_<chunk>.jsonl` target internally, and then invokes the same fail-closed helper exactly once.

No model smoke, real freeze, Phase C, source-truth snapshot, semantic role, protected evaluation, holdout evaluation, production change, or canonical audit append occurred in D-111.

## Reconciled base / predecessor preservation

Before construction and again after final review, repo branch `codex/retrieval-v3-user-search-quality` was clean at D-110 commit `7091d7c053c413b583381639bcaefb3089834e74`, with local/upstream/direct remote equal, `git diff --check` PASS, production `ml-service/` diff zero, and canonical audit exactly 4 events SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`.

OMP remained `18.1.5`; effective default/plan remained `opencode-go/muse-spark-1.3-contributor:xhigh`.

v9r15 remains immutable failure evidence. Its D-108 `FROZEN_HASHES.json` still contains 67 pinned entries and independent rehash found **67/67 exact, mismatch 0**. v9r15 runtime/source-truth/Author-1 row bodies were not copied or reused as v9r16 semantic material.

The fresh v9r16 builder was created only from the 66 v9r15 pinned source/support files excluding `PLAN_LOCK.json`, then given fresh v9r16 identity plus one new permanent D-110 regression. Final v9r16 source/support count is 67.

## D-110 writer-envelope repair

The standing helper/filesystem security boundary is not relaxed.

For real Author/Reviewer/C roles, `role_write_chunk` now exposes model schema `{chunk, lines}`:

- `chunk` must be a string exactly one of `"0"` through `"5"`.
- The model never supplies a path/name.
- Before any `pi.exec` or helper call, the extension checks exact chunk identity, that `lines` is an array, and exact role-bound row count: Author-1/2 = 30; Reviewer-A/B/C = 60.
- Invalid/missing chunk or wrong row count is a **LOCAL TOOL PARAMETER/ENVELOPE ERROR**: zero helper spawn, zero filesystem access, zero `role_tool_access` row. It is not a helper/filesystem DENY and is not by itself `CONTRACT_INVALID_GENERATION`; the same role session may correct the call and continue.
- There is no normalization, coercion, path repair, buffering, semantic auto-repair, or coordinator-authored content.
- Only after local preflight passes does the extension derive byte-exact `out/chunk_<chunk>.jsonl` and invoke `role_fs_helper.py write` once.
- The helper remains authoritative for exact target, staging confinement, symlink/reparse/escape rejection, exact rows, JSON/schema, and ID/order. **Any helper DENY / `allowed:false` access-log row remains fatal** under the unchanged zero-deny `audit_role_access.py` contract.
- Lifecycle smoke remains `role_smoke_probe` only; its deterministic deny triple + six 1-row allowed helper writes is unchanged except generation identity/SHA pins.

This closes the exact D-110 failure mode without weakening real-role filesystem authorization.

## Permanent D-110 regression

New `test_role_write_preflight.py` executes the real v9r16 role extension with a hermetic mock ExtensionAPI and direct helper negatives. Final result: **`PREFLIGHT_PASS`, 36 checks**.

It proves, among other cases:

- D-110 legacy/path-shaped call with no valid `chunk` -> local throw, `pi.exec=0`.
- Author chunk `"0"` with 2 rows -> local throw, `pi.exec=0`.
- strict invalid chunks `"6"`, `"../0"`, `"0\\evil"`, and `/out/chunk_0.jsonl` -> local throw, `pi.exec=0`.
- valid Author-1/2 30-row calls and Reviewer-A/B/C 60-row calls each derive the exact fixed target and spawn the helper exactly once.
- wrong Reviewer/C row counts -> local throw, `pi.exec=0`.
- direct helper bad-target and wrong-row-count calls still return DENY/rc3.
- the final generation plan contains the explicit local-preflight-vs-helper-DENY contract.

## Independent final-byte validation

Web independently reran the final post-blocker battery on the final bytes:

- D-110 writer preflight: `PREFLIGHT_PASS` — 36 checks
- lifecycle contract: `LIFECYCLE_CONTRACT_PASS` — 53 checks
- launcher reachability: `REACHABILITY_PASS` — 87 checks
- role tools: `ROLE_TESTS_PASS` — 170 checks
- role completion: `GATE_TESTS_PASS`
- TEN gates: 45 pairwise comparisons, overlap 0; exact counts `180/250/248/273/273/360/360/365/360/360`
- Phase-C confinement: `CONFINEMENT_TESTS_PASS` — 198 checks
- freeze-binding production-main regression: `FREEZE_BINDING_PASS` — 66 checks
- Bun role-tools probe: `PROBE_PASS`
- Bun coordinator probe: `PROBE_PASS`
- TypeScript `tsc --noEmit`: PASS
- Python compileall: PASS
- generation-plan mechanics SHA map: **54/54 exact**

The disposable freeze traversal used by the freeze-binding regression produced current plan SHA `729597182ba7ac646ee859b3b8a05baee448794d2aa7d84a27b60189c70d3105` only inside its disposable copy; the real v9r16 builder remains unfrozen and runtime-empty.

Independent normalized predecessor review found all of the following semantic core files identical to v9r15 after v9r16→v9r15 identity normalization: `RUBRIC.json`, `search_snapshot.py`, `check_anchor.py`, `validate_pool.py`, `merge_chunks.py`, `build_packets_ab.py`, `freeze_raw_ab.py`, `reconstruct_keymaps.py`, `merge_raw_ab.py`, `build_agreement.py`, `build_packets_c.py`, `merge_c.py`, `run_selector.py`, `role_completion_gate.py`.

## Final key SHA256

- `GENERATION_PLAN.json` `729597182ba7ac646ee859b3b8a05baee448794d2aa7d84a27b60189c70d3105`
- `freeze_plan_v9r16.py` `9741d4a01fec5d5141ea2061969d54c92d261c75a8e615642a1f99d02431a3e1`
- `carry_exclusions_v9r16.py` `d49c1cb1c6a5cb88dac714b7ea2dba8b629ec3e5c0cbcd0abecb4e2e8d16e669`
- `test_role_write_preflight.py` `d1313f41501d9642c22224d9a5c34f1f92cd08608e9dab3a65f354cbf969f257`
- `coord_wrapper_tpl/phasec_role_ext.ts` `408ce7edff2b9af6abd3690a5648cb668517a453f4c06116c7de4350a3429509`
- `role_fs_helper.py` `e6f2ece44dc4b56cc1dad0190a7657e082ea7b561cf6059872cb4a25596ed8be`
- `role_omp_wrapper.py` `d502bc998dd2ea4a8059f7a906a2586e9630f837d976bb4171fd8daf016e750e`
- `coord_wrapper_tpl/coord_omp_wrapper.py` `e38284af70d0e41481aaa29675540ef6484806ce51f05a8abfc60cad9976f6c6`
- `run_lifecycle_smoke.py` `d641f0f76baedf368e1a6408dd3571a1e0463e9271f3f19f7560a8b53650c151`
- `audit_lifecycle_smoke.py` `661e1b9f1169cd4c530e245d4d34803765e268956351ea2d8be6a11b5845f509`
- `smoke_lifecycle_prompt.txt` `1e557ab9bfb55695f46da5379e908b425a966b1c29fa51b748b14bd1e8c65e9d`
- `audit_coord_smoke.py` `0337593c39199f4ef518a662885801c9651b6afb74fdff8b4b45981e33033227`
- `launch_phasec_coordinator.py` `7db1d581072de4fb8221c3db65f61a3c6cd290c416a12e8abfb4dae4837eddd2`
- `launch_top_level_paseo.py` `2a64a95a4de55f1d72d8d8ba5c677714be0842999e7eb2db019c34eb12c2e8f4`
- `role_completion_gate.py` `5f1bd6c49293ad57dfb64ff4f8bc558f00c81cf1b0f5e67289cc99c8e50e2ae1`
- `probe/role_tools_probe.mjs` `248dad3d36426ad600771254bd4d5fc6eec3b22053ea83a94948c9a3b57e8ff3`
- `RUBRIC.json` `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- `input/EXCLUSION_INPUTS.json` `e5816242684be45479818d0379c44a5ff5402ea2d182045808cd45c9101cf0e7`

Single implementation executor OMP session: `C:\Users\joji\.omp\agent\sessions\-Documents-programming\2026-09-06T17-03-36-729Z_01a077ac-ed19-702b-96d9-c0a0f7c0455c.jsonl`, final 549 lines, SHA256 `c7922ca23c3a31f9ac482141dce23268ada55aa1c081efd182274a105e571fc7`. The same session was resumed for the same PRE-SMOKE Web blocker repair; no second implementation executor or subagent modified the builder.

## Final boundary / next gate

Final real builder: **67 source/support files, zero Python cache**, and none of `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, source truth, anchors/slots, semantic runtime outputs, or `evalset.jsonl` exists.

No v9r16 Smoke-A/B staging root or session directory exists and no matching v9r16 Paseo agent exists at D-111 review time.

**NEXT: exactly one v9r16 Smoke A on these exact final bytes. Only if its frozen auditor returns PASS may exactly one v9r16 Smoke B run.** Any smoke failure closes v9r16 with no retry/same-generation repair. Real freeze and Phase C remain forbidden until both one-shot smokes pass and a later gate authorizes freeze.
