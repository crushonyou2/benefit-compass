# Retrieval v3 D-104 — generation-v9r14 one-shot Smoke A/B PASS

Date: 2026-09-06
Stage: one-shot smoke gate durable record only
Generation: `retrieval-v3-dev-generation-v9r14`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260906-v9r14`

## Verdict

**v9r14 ONE-SHOT SMOKE GATE: PASS.** The D-103 final bytes consumed exactly one Smoke A and, only after A passed, exactly one Smoke B. Both frozen auditors independently return PASS on the preserved evidence. No retry or second launch occurred.

This record does **not** real-freeze v9r14 and does not authorize or run Phase C. The next logical stage is a read-only pre-freeze reconciliation and real-freeze gate that binds these exact Smoke A/B proofs to the exact D-103 builder bytes. Phase C remains forbidden until the real freeze itself is completed and independently approved.

## Reconciled D-103 base

Before Smoke A, actual repo state was clean with branch `codex/retrieval-v3-user-search-quality`, HEAD/local/upstream/direct remote `0e791fb4b4b9720b536df4256040ab044bf88321` (D-103). `git diff --check` passed, production `ml-service/` diff remained zero, audit remained exactly 4 events SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`, and canonical `eval/retrieval-v3/result`, `dev`, `holdout`, `dev-v2` were absent.

The v9r14 final PRE-SMOKE bytes matched D-103 hashes and both smoke staging roots were absent before their respective one-shot launches. OMP was `18.1.5` with effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`.

## Smoke A — exactly once, PASS

Smoke A was launched exactly once through the frozen v9r14 coordinator launcher on the unchanged D-103 bytes.

- agent: `6546b6e9-e5de-4478-a623-e30930516987`
- cwd: `C:\Users\joji\bc-v3-v9r14-coord-smoke-20260906\cwd`
- model: `opencode-go/muse-spark-1.3-contributor`
- thinking: `xhigh`
- ParentAgentId: null
- final status: idle
- descendants: 0
- fallback: proven false
- exact session: `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r14-coord-smoke-20260906-cwd\2026-09-06T15-21-39-988Z_01a0774f-9794-71c6-91ec-7cc768692a77.jsonl`
- session lines: 10
- session SHA256: `f6b0859ae06b2bfc6b11e75def452b0c7808064a9d33dbfa1862d68190019de0`
- transcript tool calls: `phasec_probe=1`, no forbidden calls
- wrapper: exact-one coordinator wrapper invocation; tools `todo`, mode `smoke`, frozen controls, coordinator extension SHA `2e8b2478fd78204b00ed51a8f43d32c2405a30c5ad97510b14d126f6c19067ca`
- frozen `audit_coord_smoke.py`: rc 0, `SMOKE_PASS`

The exact same evidence was re-audited after Smoke B and again returned rc 0 `SMOKE_PASS`. No second Smoke A launch occurred.

## Smoke B — exactly once, PASS

Only after Smoke A passed, the frozen `run_lifecycle_smoke.py` was run exactly once on the unchanged v9r14 bytes.

- agent: `14f00fa1-f157-4d54-a4d3-b6b3d7917208`
- cwd: `C:\Users\joji\bc-v3-v9r14-lifecyclesmoke`
- model: `opencode-go/muse-spark-1.3-contributor`
- thinking: `xhigh`
- ParentAgentId: null
- final status: idle
- descendants: 0
- fallback: proven false
- exact session: `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r14-lifecyclesmoke\2026-09-06T15-22-46-929Z_01a07750-9d11-75dd-bc03-20de2bb76eae.jsonl`
- session lines: 19
- session SHA256: `4307a8d737cf84636db72c946d5d61607c86786fa883734cb361e6b2b52057c3`
- transcript tool calls: `role_smoke_probe=1`, `todo=4`; no model `role_write_chunk` call and no forbidden built-in/role tool call
- wrapper: exact-one role wrapper invocation, tools `todo`, mode `role`, kind `lifecycle_smoke`, frozen role extension SHA `a9f14e4f9f972d14268e94bf563cb7d77528b81d9a0cec3d8daf9539576a7dd6`
- access log: exactly 9 rows
  - deny `cross-role`: exactly 1
  - deny `unknown-resource`: exactly 1
  - deny `bad-target`: exactly 1
  - allowed write for each `out/chunk_0.jsonl` … `out/chunk_5.jsonl`: exactly 1 each
- outputs: exactly six files, exactly one row each
- frozen `audit_lifecycle_smoke.py`: rc 0, `LIFECYCLE_SMOKE_PASS`

Exact output SHA256 values:

- `chunk_0.jsonl` `e7d2aecdf462de9a8918695e7adb70032f80c50205ce849b42664fe3877f24e9`
- `chunk_1.jsonl` `1e942823dc343829cab4c491ceee21ef4a6f8a54337ae32c5564bf5920b8d2f7`
- `chunk_2.jsonl` `90bdd8c64714150816c00c9ef40c6102d451dbf0102d3a3a698b204e7bfd090d`
- `chunk_3.jsonl` `c695e51a11fa40103355a84f95f15396616465d391bdeade92ec03db24244e1a`
- `chunk_4.jsonl` `d72b87b5d2fabbfd43d2b9b999bcd3cfcd4a6cfe251b44e21e5f97ce2f82de0f`
- `chunk_5.jsonl` `4d14e6c3ee466e96ff1daf257dbe26e3205070c197e97757e9f5e9fc90d953ff`

Each file is 59 bytes / 1 row. The frozen runner itself returned `LIFECYCLE_SMOKE_PASS` and exited 0. Web then independently reran the frozen lifecycle auditor on the same session/wrapper/access/output evidence; it again returned rc 0 with the same session SHA, exact deny triple, exact six writes, descendants 0 and fallback proof. No second Smoke B launch occurred.

## Final builder immutability after smokes

After both smokes and independent re-audits, the v9r14 source bytes remained the D-103 final bytes. Rechecked hashes include:

- `GENERATION_PLAN.json` `418c6d875523a9c2753ba946a52bd0bc5ab7e88f473c15641d988b3158dce404`
- `launch_top_level_paseo.py` `42508cfddea9b413fef18c3df9f45e6c73110fbf69ccf85444e06e222a441b46`
- `role_omp_wrapper.py` `a4b43e220d0ee11754a5f766a71ed68af3e02f224a5bbb839a85a7de7cf761c0`
- `role_fs_helper.py` `094d1479a7d345d888991e143e5be4f3525042f8821eddc9acd7d494d01ccada`
- `coord_wrapper_tpl/phasec_role_ext.ts` `a9f14e4f9f972d14268e94bf563cb7d77528b81d9a0cec3d8daf9539576a7dd6`
- `run_lifecycle_smoke.py` `967eb103caf970d9874ca31313a0532fa0c7af45d3b6050ada5c4b40f2f15610`
- `audit_lifecycle_smoke.py` `35b085568e5a210ee9139669102c96c3452c10a822affd9b21785531654d333e`
- `smoke_lifecycle_prompt.txt` `7948fc4245a7604fa0e8f52c46e1f37cd5216b11cf230dd32497f2bd0d7508ca`
- `role_completion_gate.py` `2608dd9edb84b6b5ba32f29a207f18e3a882bad4387fc00db0724e714fb91a8e`

Auditor imports created Python cache artifacts only. Web removed exactly the v9r14-builder `__pycache__`/`.pyc` artifacts after verifying their resolved paths were below that builder. Final builder has 65 files and zero pycache/pyc.

No real `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, `source_truth.jsonl`, `source_truth_meta.json`, `evalset.jsonl`, candidate/reviewer/C/selector runtime artifact exists. No Phase C, protected evaluation, holdout evaluation, production change, audit append, branch, tag or worktree was created by the smoke stage.

## Next logical stage

**NEXT LOGICAL STAGE: read-only pre-freeze reconciliation and generation-v9r14 real-freeze gate, binding the exact D-103 builder bytes plus the exact one-shot Smoke A/B evidence above.**

Do not run Phase C in D-104. Phase C remains blocked until real freeze is completed, durably recorded, and independently reviewed/approved.
