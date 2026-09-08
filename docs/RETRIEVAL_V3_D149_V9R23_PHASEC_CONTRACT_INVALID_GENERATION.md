# Retrieval v3 D-149 — generation-v9r23 Phase-C CONTRACT_INVALID_GENERATION

Date: 2026-09-09
Stage: exactly-once Phase-C execution closure
Generation: `retrieval-v3-dev-generation-v9r23`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r23`
D-148 pre-execution base commit: `ebda9235d59df5556fc21ce2304cb85534b2ab77`

## Verdict

**v9r23 = HARD HOLD / CONTRACT_INVALID_GENERATION / NON-RESUMABLE / NON-REPAIRABLE.** The D-148-authorized frozen Phase-C execute was consumed exactly once. The fresh source-truth snapshot, anchors/slots, both Author roles, all twelve final Author chunks, and the 180+180 Author candidate collections completed. The frozen mandatory pool merge + THIRTEEN validation then failed with seven structural failures before `candidates_merged.json` was written and before Reviewer A/B, Adjudicator C, selector, protected evaluation, holdout, production, or canonical audit append.

The canonical frozen coordinator result is:

`phasec_execute: driver nonzero exit rc=3 ... {"verdict":"CONTRACT_INVALID_GENERATION","error":"pool merge + THIRTEEN validation: rc=1 ... STRUCTURAL_FAIL"}`

No retry, resume, run-lock removal, frozen-byte patch, manual pool repair, manual Reviewer/C launch, second coordinator, or same-generation repair is permitted.

## Fresh execution base

Immediately before the sole execute launch:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `ebda9235d59df5556fc21ce2304cb85534b2ab77`
- working tree clean; `git diff --check` PASS; production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- canonical audit 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/dev-v2/`, `eval/retrieval-v3/holdout/` absent
- immutable `PLAN_LOCK.json` SHA256 `b8c1fa42e23c3ef085b30e54fd08a5e68d8895219328e4415764caf574468c3f`
- immutable `FROZEN_HASHES.json` SHA256 `bda5f88c3d89d60ff79c38144fafa300139f41a55ff6182ad1231a44fb18aeb2`
- frozen current rehash exactly 77/77, missing 0 / mismatch 0
- v9r23 run lock/source truth/Phase-C root/execute root/session/registry/process all absent at the freshness gate

## Sole D-149 stage executor and exactly-one coordinator launch

A fresh top-level execution-only Paseo/OMP stage agent owned the one-shot launch:

- stage executor `981cddcc-06e0-48c7-9559-f161e70e1f9f`
- title `D149 v9r23 Phase-C stage executor`
- ParentAgentId null, repo cwd, provider/model `omp` / `opencode-go/muse-spark-1.3-contributor`, thinking `xhigh`, mode `full`
- exact OMP session 12 lines / 21,971 bytes / SHA256 `54f2ffc51d4dc46ec2edc33f503b047b171e07036645c4c25af1bed50798f0d2`
- structural transcript: `bash` tool call exactly 1, matching `bash` result exactly 1, no other tool calls in the execution instruction
- exact bash command SHA256 `9b2f2479b9fc5a1fe08ec91984dc389b726339dbd49d8bea59b91ee7770444bc`, equal to the pre-recorded one-shot command; it used Python `-B`, `PYTHONDONTWRITEBYTECODE=1`, and `PYTHONUTF8=1`
- single bash result: `{"agent_id":"f9a3d375-2612-490b-b5dd-dc989fefad66","verified":true}`

The sole frozen execute coordinator is:

- agent `f9a3d375-2612-490b-b5dd-dc989fefad66`
- title `D149 v9r23 Phase-C execute`
- cwd `C:\Users\joji\bc-v3-v9r23-coord-execute-20260909\cwd`
- ParentAgentId null, provider/model `omp` / `opencode-go/muse-spark-1.3-contributor`, thinking `xhigh`, mode `full`, final idle
- registry count for the exact title/cwd = 1
- wrapper invocation exactly one row, SHA256 `ef6ca67946b0c7b00e1c8ba0ed3b3080ccaf4db17784e89fa773717e0fb80098`, mode `execute`, custom tool `phasec_execute`, built-in tools `todo`, frozen extension SHA256 `08d615b9d2547049d5a6039cb6d2306f15c2a7fb5a2612b76f2d5453900049a3`
- exact OMP session `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r23-coord-execute-20260909-cwd\2026-09-08T23-24-53-980Z_01a08356-b95b-7770-97e8-b18a777fc6d4.jsonl`
- shared-read structural proof: 10 lines / 9,820 bytes / SHA256 `aaa73db070650ca44b382bc4f3d46445a311c6eed80b18dcb993ba47cab38520`
- `phasec_execute` tool call exactly 1 and matching result exactly 1; no second execute call/coordinator

## Atomic run boundary and frozen-byte preservation

The driver consumed the atomic one-shot boundary exactly once:

- `phasec_driver.run.lock` present, SHA256 `6f8ff2f719fa3d117ed51e95f81edd639aaa9eb35ddf26c996010c21add47db2`
- content: `{"started": "2026-09-08T23:24:56Z", "pid": 70732}`
- PID 70732 is no longer alive after the canonical rc3 termination
- post-failure frozen rehash remains 77/77 exact, missing 0 / mismatch 0

Runtime imports left two builder-local `__pycache__` directories / three `.pyc` files (`phasec_driver`, `launch_top_level_paseo`, `role_completion_gate`). Unlike pre-execution cache hygiene, these are left untouched as consumed-run evidence. They are outside the frozen 77-pin payload and do not change the 77/77 exact result.

## Completed runtime before pool failure

Fresh generation inputs are preserved:

- `source_truth.jsonl`: 75,207,689 bytes / 13,589 rows / SHA256 `9fe194653a4b5c9c688364aa9ae686996cb7cabfebd446a6b9a7e8895374c1a5`
- `source_truth_meta.json`: 789 bytes / SHA256 `9f6a3a99f8c9060072f390871d30e7be4550245a19a4e015a68c3e3b4f089189`
- `anchors.json`: 45,835 bytes / SHA256 `38ef33e8e90317e6b57bd6a44edecb303c6e132ca420b5c6e34291ecca414485`
- `slots_1.json`: 20,074 bytes / SHA256 `64172dae13a8af7ba278a87bf811b58e67de8477d1208ee7119ca253cfeaba43`
- `slots_2.json`: 20,364 bytes / SHA256 `baa2ce070bc28c4ad47ee79410def1d8dd89e0987a107d1f59599a0b526c0222`

Author-1:

- agent `88ca8935-29e5-440e-88ee-1c63b08653e3`, final idle
- session 1,266,268 bytes / 612 lines / SHA256 `b3136a9a2c0693b4ba7d5e30584953e66e240302e0cc9d02d41360b32f1f9a4d`
- exact final assistant stop with no later trigger
- six final 30-row chunks; `role_write_chunk` calls 6
- wrapper SHA256 `a1d4b376dc813f352a5b32feecd340fa878d155342ba34ef664f08bf95888299`
- role tool-access log 256 rows / SHA256 `16c6ea1afad7baff64796bf19914317b97db2609c1fafb4640e63a3be1fb7ca2`
- collected `author1_candidates.jsonl`: 53,101 bytes / 180 rows / SHA256 `8f217b6ebd78de9beccdf903ba0a6e613b1e1c86acb957f9aa6060f71ff10d81`

Author-2:

- agent `397526e1-fc7c-4940-b8e6-4f57ea82568d`, final idle
- session 1,615,005 bytes / 563 lines / SHA256 `7594e2dbe3ba267e7ebc1beb6d03475c6cab8b578c32a017a3234c9d65b73e8b`
- exact final assistant stop with no later trigger
- six final 30-row chunks; transcript contains 7 `role_write_chunk` calls because one chunk was rewritten before the final stable state; the frozen completion/audit path accepted the final exact six-file output and the driver proceeded to collect it
- wrapper SHA256 `125d590a7da980cd35c4dc00f5b8462be0f5e0a82f041066deb442754d8a2884`
- role tool-access log 241 rows / SHA256 `5570d4271a7e4b765662b8a216bc52d9f5878605fc520dc293ffaea52132ccbd`
- collected `author2_candidates.jsonl`: 93,252 bytes / 180 rows / SHA256 `4326625e8453646a6253433f4aa3f368d41116178f108f129a60c029593ecdbd`

Only these two Phase-C role agents exist. Reviewer A, Reviewer B, and Adjudicator C registry counts are all zero.

## Exact pool-validation failure boundary

The frozen validator returned `fail_count=7` and `STRUCTURAL_FAIL`:

1. `v3g9r23-168` — `slot_location_mismatch`
2. `POOL` — `loc_multi_constraint_17_!=_16`
3. `POOL` — `internal_query_fp_not_unique`
4. `v3g9r23-181` — `constraints_lt2`
5. `v3g9r23-182` — `constraints_lt2`
6. `v3g9r23-183` — `constraints_lt2`
7. `v3g9r23-184` — `constraints_lt2`

Prime independently reconciled the existing Author outputs and immutable slots without rerunning the validator and without printing query plaintext:

- all 360 expected candidate IDs and stratum aggregate counts are present
- `v3g9r23-168` is the only slot metadata mismatch: immutable slot `intended_stratum=multi_constraint`, `intended_location=false`; returned row preserves the stratum but changes `intended_location=true`
- this single false→true mutation mechanically produces the multi-constraint location count 17 instead of frozen expected 16
- normalized NFC + strip + whitespace-collapse + casefold + SHA256 query fingerprints are 358 unique across 360 rows
- duplicate fingerprint group 1: `v3g9r23-009` and `v3g9r23-198`, SHA256 `e07f21b2c6c6bcec0eb157e4eddc431f17b0fa26468bd19072a1786363ce524e`
- duplicate fingerprint group 2: `v3g9r23-010` and `v3g9r23-202`, SHA256 `fe1f193e0b6fc11595b12f47b32e9a86db771047ff4288e85aec400907b5703f`
- current 358 unique fingerprints have zero overlap against every frozen prior query-fingerprint set: dev-v1, holdout, history, d070, d071, d072, d074, d076, d082, d086, d117, d123, d141
- `v3g9r23-181..184` are `multi_constraint` rows whose `ledger.constraints` value is absent (`None`), proving each `constraints_lt2` mechanically

This closure does not reinterpret these failures as a validator bug or authorize a same-generation repair. The frozen validator is the mandatory contract authority and failed closed before writing the merged pool.

## Downstream zero-state after failure

Because `validate_pool.py` writes `candidates_merged.json` only after the complete failure list is empty, the failed validation left:

- `candidates_merged.json` absent
- Reviewer A/B roots, agents, sessions, raw outputs, and raw freeze absent
- transcript audit attestation / packet keymaps / merged A/B / agreement / disagreement artifacts absent
- C root, agent, session, keymap, adjudicated pool absent
- selector/final evalset absent
- protected dev-v2 evaluation absent
- holdout evaluation absent
- production `ml-service/` change 0
- canonical audit remains 4 rows / SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`

## Independent post-failure review

A separate read-only reviewer returned **FINAL CONTRACT_INVALID / HARD HOLD**. It independently verified repo/freeze integrity, exact one coordinator and one `phasec_execute` call/result, the rc3 `STRUCTURAL_FAIL` with the seven failures, preserved run lock with dead driver PID, completed Author 180+180 boundary, zero Reviewer/C/downstream execution, and unchanged audit/production/protected boundaries. It performed no rerun, mutation, protected access, or agent messaging.

## Closure / successor boundary

V9r23 is permanently closed as `CONTRACT_INVALID_GENERATION`. Preserve the immutable freeze artifacts, run lock, source-truth snapshot, anchors/slots, Phase-C roots, both Author sessions/wrappers/access logs/chunks, collected candidate files, coordinator/stage-executor sessions, runtime caches, and every current failure artifact in place.

Do not retry or resume the driver, delete/recreate the run lock, patch frozen bytes, edit failed Author rows, manually merge the pool, launch Reviewers/C, run selector, or launch a second execute coordinator for v9r23.

A future successor, if authorized by a separate user `진행해`, is a **fresh logical stage and fresh generation identity only** after reconciling standing failed-generation freshness/provenance rules. This D-149 closure does not yet decide successor repairs, query-fingerprint carry disposition, rubric/quota/selector changes, or any protected evaluation. Protected dev-v2, holdout, production change, and canonical audit append remain prohibited.