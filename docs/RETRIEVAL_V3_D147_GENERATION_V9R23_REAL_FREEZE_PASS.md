# Retrieval v3 D-147 — generation-v9r23 exactly-once real freeze PASS

Date: 2026-09-09
Stage: real-freeze pre-gate / exactly-once publication / post-freeze provenance closure
Generation: `retrieval-v3-dev-generation-v9r23`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r23`
D-146 Smoke-B base commit: `c7f14f9325c1554f1d53d80360cf7234268670f3`

## Verdict

**D-147 / v9r23 REAL FREEZE: PASS.** The D-146 final bytes, with Smoke A and Smoke B each already consumed exactly once and PASSed, passed a fresh real-freeze pre-gate. Frozen `freeze_plan_v9r23.py` was then invoked exactly once against the real builder with both preserved smoke proofs fully pinned and with `--frozen-at` omitted. The invocation succeeded and published `PLAN_LOCK.json` and `FROZEN_HASHES.json` through the frozen O_CREAT|O_EXCL exactly-once path.

Independent post-freeze rehash and provenance review found no operative blocker. `FROZEN_HASHES.json` contains exactly 77 entries; all 77 currently rehash exactly with missing 0 / mismatch 0, and the manifest exact set equals the complete current freeze-eligible builder file set. Raw `frozen_at=2026-09-08T22:58:55+00:00` precedes lock creation by 4.2134265 seconds and frozen-hash publication by 4.2837105 seconds. The D-135 future-time provenance defect did not recur.

Real freeze is now permanently consumed and non-repeatable. `PLAN_LOCK.json` and `FROZEN_HASHES.json` are immutable evidence and must not be edited, deleted, recreated, regenerated, or replaced.

**STOP boundary:** D-147 did not execute Phase C, create a v9r23 Phase-C run lock or source-truth snapshot, launch Author/Reviewer/C/selector roles, access protected dev-v2/holdout plaintext, change production `ml-service/`, or append the canonical evaluation audit. The next separately authorized logical stage is only a fresh **Phase-C PRE-EXECUTION gate**. D-147 authorizes no Phase-C execute.

## Fresh pre-freeze reconciliation

Immediately before the one real-freeze invocation:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `c7f14f9325c1554f1d53d80360cf7234268670f3`
- working tree clean; production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- canonical audit exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/dev-v2/`, `eval/retrieval-v3/holdout/` absent
- final plan 69,469 bytes, SHA256 `6bddf1fe4661819b9cb7029f2694194298a91c99ba6d5d491e8634eae4b67eae`
- frozen freeze mechanic `freeze_plan_v9r23.py` 97,441 bytes, SHA256 `a467ff8bbe8b680b60f2f5b4cc29887e33d3536e1967fceca80cde9c256d6457`
- rubric SHA256 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- exclusion manifest SHA256 `602565b7a881206a0d7a58c1ed3e2b13881f87a561bbf65dc1b842d359397a18`
- mechanics 60/60 exact; builder cache dirs 0 / `.pyc` 0
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, source truth/meta and final evalset absent
- Phase-C and execute roots absent; D-147 freeze-executor registry match absent before executor launch
- immutable v9r22 `phasec_driver.run.lock` remained present
- OMP `18.1.13`, bundled Paseo `0.7.2`, effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`

Fresh real-freeze-critical regressions PASSed on these exact bytes without invoking real freeze: `FREEZE_BINDING_PASS` 87, `FREEZE_RERUN_REJECTION_PASS` 66, exact Paseo CLI 64, launcher reachability 87, and registry descendant scan 37. The rerun regression proves O_CREAT|O_EXCL no-overwrite publication, strict future/naive/nonzero-offset/malformed timestamp rejection, and concurrent publication safety on disposable copies.

A fresh independent read-only pre-freeze reviewer returned **FINAL PASS — blockers none** after independently rechecking current bytes, zero-state, both preserved smoke proofs, exactly-once publication mechanics, truthful observed-now timestamp handling, audit/production/protected boundaries and the immutable v9r22 run lock.

No protected plaintext recovery or prohibited Git object/history access was used.

## Preserved Smoke A/B proofs bound at freeze

Smoke A was freshly re-audited before real freeze and remained unchanged:

- agent `3f22eda8-fae4-4f21-a4ca-ac72659cbe55`
- exact session 10 lines, SHA256 `0c72127e7d224259bd269e290809efb6d15cb3d5002a22031e3ab1ca23efa53e`
- `phasec_probe=1`, descendants 0, fallback proven
- frozen verdict `SMOKE_PASS`

Smoke B was freshly re-audited before real freeze and remained unchanged:

- agent `a280775e-b7e8-4081-b8da-acf3b82f182c`
- exact session 21 lines, SHA256 `45eeab8558e4fb4dd97b7365d4a2861d176131e9f4c672931076df54d4ac8158`
- `role_smoke_probe=1`, `todo=5`, fixed deny triple each 1
- six exact one-row/59-byte outputs, descendants 0, fallback proven
- frozen verdict `LIFECYCLE_SMOKE_PASS`

The published lock reran and bound both frozen auditors at freeze time. Its audit-bound fields carry the exact A/B agent IDs, session paths/hashes/line counts, probe/tool evidence, deny/output evidence and descendants 0.

## Sole real-freeze execution

Exactly one fresh execution-only top-level Paseo/OMP stage agent owned the one-shot real freeze:

- executor `0f6fa345-0a1c-4fde-b6c1-3970c2a3be33`
- title `D147 v9r23 real freeze executor`
- ParentAgentId null
- provider/model `omp` / `opencode-go/muse-spark-1.3-contributor`
- thinking `xhigh`, mode `full`, main-repo cwd, final idle
- executor OMP session `C:\Users\joji\.omp\agent\sessions\-Documents-취준자료-project-repos-benefit-compass\2026-09-08T22-58-17-303Z_01a0833e-5c57-7223-93db-82d646d9c5aa.jsonl`
- structural session count 19 lines; SHA256 `95628f55e9bffb1250252898fb87765eb080748e923a11b3a643f932d75842aa`

Structural parsing proves exactly one `bash` tool call and exactly one `freeze_plan_v9r23.py` occurrence in that bash command. The command used the exact Python 3.11 executable with `-B`, `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUTF8=1`, the exact frozen builder path, and exact Smoke-A/Smoke-B agent/session/wrapper/cwd pins. It contained no `--frozen-at`. There was no second freeze shell call and no preliminary or follow-up terminal command.

The single bash result was `isError=false` and returned:

- plan SHA256 `6bddf1fe4661819b9cb7029f2694194298a91c99ba6d5d491e8634eae4b67eae`
- plan bytes `69,469`
- rubric SHA256 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- lock SHA256 `b8c1fa42e23c3ef085b30e54fd08a5e68d8895219328e4415764caf574468c3f`
- exclusion manifest SHA256 `602565b7a881206a0d7a58c1ed3e2b13881f87a561bbf65dc1b842d359397a18`
- `frozen_at=2026-09-08T22:58:55+00:00`
- hold base commit `d3a1b2a9c7443fc85023a3228f7bf88c330f4c85`
- frozen files `77`

## Published freeze evidence

`PLAN_LOCK.json`:

- bytes: `26,634`
- SHA256 `b8c1fa42e23c3ef085b30e54fd08a5e68d8895219328e4415764caf574468c3f`
- creation/mtime UTC `2026-09-08T22:58:59.2134265Z`
- raw `frozen_at=2026-09-08T22:58:55+00:00`
- publication minus observed freeze instant `+4.2134265s`

`FROZEN_HASHES.json`:

- bytes: `7,541`
- SHA256 `bda5f88c3d89d60ff79c38144fafa300139f41a55ff6182ad1231a44fb18aeb2`
- creation/mtime UTC `2026-09-08T22:58:59.2837105Z`
- publication minus observed freeze instant `+4.2837105s`
- entries: `77`
- independent rehash: missing 0 / mismatch 0
- exact-set proof: 77 manifest keys = 77 current freeze-eligible builder files, unfrozen extra 0, manifest-only missing 0

The timestamps prove the structured freeze instant was observed before publication, not in the future. The exact-set rehash proves no current freeze-eligible builder byte is omitted from or inconsistent with the published manifest.

## Independent post-freeze review

A separate read-only reviewer independently returned **FINAL PASS — blockers none**. It rechecked the lock/hash SHAs and sizes, 77/77 rehash, timestamp truthfulness, exact A/B lock bindings, the execution-only agent identity, exactly one freeze bash invocation with no `--frozen-at`, and later-stage zero-state. A transient sharing lock on a direct executor-session hash read was not treated as evidence failure because the session content remained readable and the previously obtained canonical 19-line/SHA proof and structural transcript facts were unchanged.

## Post-freeze boundary

Final reconciliation before durable closure:

- repo remained at D-146 base `c7f14f9325c1554f1d53d80360cf7234268670f3`, clean and aligned with upstream/direct origin
- plan remains `6bddf1fe...b67eae`; mechanics 60/60; builder cache/pyc 0
- published lock/hash remain byte-identical at the SHAs above; manifest 77/77 exact
- no v9r23 `phasec_driver.run.lock`, source truth/meta, Phase-C root, execute root, candidate/adjudication/selector/eval output
- canonical audit remains 4 rows / SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- production `ml-service/` diff remains 0
- protected dev/dev-v2/holdout paths remain absent
- immutable v9r22 run lock remains present

## Gate boundary

V9r23 now has immutable one-shot PASS evidence for:

1. Smoke A exactly once,
2. Smoke B exactly once,
3. real freeze exactly once.

None of these three one-shot steps may be rerun.

The next separate logical stage, only after another user `진행해`, is **Phase-C PRE-EXECUTION**. This D-147 closure itself authorizes no Phase-C execute, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append.
