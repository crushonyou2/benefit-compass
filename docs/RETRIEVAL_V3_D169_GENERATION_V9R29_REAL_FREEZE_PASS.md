# Retrieval v3 D-169 — generation-v9r29 exactly-once real freeze PASS

Date: 2026-09-10 (KST)
Stage: real-freeze prelaunch gate + exactly-once publication + post-freeze provenance closure
Generation: `retrieval-v3-dev-generation-v9r29`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260910-v9r29`
D-168 Smoke-B closure base: `7ca0ded0664515a35520782e029789dc833e071b`

## Verdict

**D-169 / v9r29 REAL FREEZE PASS.** The D-168 final bytes, with Smoke A and Smoke B each already consumed exactly once and PASSed, passed a fresh real-freeze prelaunch gate. Frozen `freeze_plan_v9r29.py` was then invoked exactly once against the real builder with both preserved smoke proofs fully pinned and with `--frozen-at` omitted. The sole process returned terminal rc0 and published `PLAN_LOCK.json` and `FROZEN_HASHES.json` through the frozen `O_CREAT|O_EXCL` exactly-once path.

Independent post-freeze rehash/provenance review found no blocker. `FROZEN_HASHES.json` contains exactly 88 entries and all 88 rehash exactly with mismatch 0. The complete current non-cache builder set is exactly 89 files = those 88 pinned files plus `FROZEN_HASHES.json` itself, with extra-unpinned 0 and missing-pinned 0. Raw `frozen_at=2026-09-09T19:50:05+00:00` precedes `PLAN_LOCK.json` creation by 3.9007599 seconds and `FROZEN_HASHES.json` publication by 3.9752044 seconds, so the D-135 future-provenance defect did not recur.

Real freeze is now permanently consumed and non-repeatable. `PLAN_LOCK.json` and `FROZEN_HASHES.json` are immutable evidence and must not be edited, deleted, regenerated, recreated, replaced, or produced by a second freeze invocation.

**STOP boundary:** D-169 did not execute Phase C, create `phasec_driver.run.lock`, create source truth/meta, launch Author/Reviewer/C/selector roles, access protected dev-v2/holdout plaintext, change production `ml-service/`, or append the canonical evaluation audit. The next separately authorized stage is only a fresh **Phase-C PRE-EXECUTION gate**. D-169 itself authorizes no Phase-C execute.

## Fresh pre-freeze reconciliation

Immediately before the sole real-freeze process:

- branch `codex/retrieval-v3-user-search-quality`
- local HEAD = upstream = direct origin `7ca0ded0664515a35520782e029789dc833e071b`; working tree clean; `git diff --check` PASS
- D-168 closure had been pushed first and equality reverified
- actual OMP resolved by `Get-Command omp` to `C:\Users\joji\AppData\Local\omp\omp.exe`, version `omp/18.1.13`; bundled Paseo version `0.7.2`
- global default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`; no repo-local `.omp`; no relevant ambient `PASEO_*`/`OMP_*` override
- Smoke A frozen re-audit: `SMOKE_PASS`, exact session 10 lines SHA256 `c5e29e457c6a657c951246f2056f79b4c8b5f96adc40131cc06ad30a139f8b0f`, `phasec_probe=1`, descendants 0, fallback proven
- Smoke B frozen re-audit: `LIFECYCLE_SMOKE_PASS`, exact session 15 lines SHA256 `9abc5e96090f35696a92540318d2507eaa4ff61d610cbf045ba36bc6d99a3a85`, `role_smoke_probe=1`, fixed deny triple each 1, six exact 1-row outputs, descendants 0, fallback proven
- `FREEZE_BINDING_PASS` 120; `FREEZE_RERUN_REJECTION_PASS` 66; one-shot terminality 24/24 PASS
- v9r29 primary hashes 10/10 exact; mechanics 69/69 exact; cache0/pyc0
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock` and all source/Phase-C/output artifacts absent
- canonical audit exactly 4 rows SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- protected `eval/retrieval-v3/dev`, `dev-v2`, and `holdout` absent; production `ml-service` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- immutable predecessor v9r28 key hashes 8/8 exact

A preliminary OMP version probe used a stale nonexistent path `C:\Users\joji\.omp\bin\omp.exe` and failed read-only before any freeze action. Canonical `Get-Command omp` then resolved the current executable path above and version `18.1.13`; no state change or gate relaxation resulted.

No protected plaintext recovery or prohibited Git object/history access was used.

## Preserved Smoke A/B proofs bound by the freeze

The published freeze reran and bound both frozen auditors rather than synthesizing PASS booleans.

Smoke A lock binding:

- audit verdict `SMOKE_PASS`
- agent `a810d782-bf58-49a5-b882-72178c22f08f`
- session SHA256 `c5e29e457c6a657c951246f2056f79b4c8b5f96adc40131cc06ad30a139f8b0f`
- session lines `10`
- descendants `0`

Smoke B lock binding:

- audit verdict `LIFECYCLE_SMOKE_PASS`
- agent `0e4ae1f5-8ed9-42ce-9a3a-ced18817e2c1`
- session SHA256 `9abc5e96090f35696a92540318d2507eaa4ff61d610cbf045ba36bc6d99a3a85`
- session lines `15`
- descendants `0`

## Sole real-freeze execution

The one and only real-freeze process call used builder workdir `/programming/bc-v3-dev-v2-builder-20260910-v9r29` and scalar command:

`python -B freeze_plan_v9r29.py --smoke-agent "a810d782-bf58-49a5-b882-72178c22f08f" --smoke-session "C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r29-coord-smoke-20260910-cwd\2026-09-09T19-24-51-432Z_01a087a1-5168-74ff-8aa9-2dcd79f56e88.jsonl" --smoke-wrapper-log "C:\Users\joji\bc-v3-v9r29-coord-smoke-20260910\cwd\wrapper_invocation.log" --smoke-cwd "C:\Users\joji\bc-v3-v9r29-coord-smoke-20260910\cwd" --lifesmoke-agent "0e4ae1f5-8ed9-42ce-9a3a-ced18817e2c1" --lifesmoke-session "C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r29-lifecyclesmoke\2026-09-09T19-36-54-940Z_01a087ac-5b9c-7430-8dc1-6efaa3904fb0.jsonl" --lifesmoke-wrapper-log "C:\Users\joji\bc-v3-v9r29-lifecyclesmoke\wrapper_invocation.log" --lifesmoke-cwd "C:\Users\joji\bc-v3-v9r29-lifecyclesmoke"`

`--frozen-at` was intentionally omitted. No precheck, post-hash helper, retry, correction, or second freeze process was bundled into this one-shot call.

Terminal result:

- process rc `0`
- plan SHA256 `d1ed3eda0f64a1570d71423604499d90f5af690dbde39590bbeb19883efd751a`
- plan bytes `85020`
- rubric SHA256 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- lock SHA256 `875aa8c3a54fbb8c93c475d35ac70390e4383ac4fd5a7d060f5ec8ca1e050d4b`
- exclusion manifest SHA256 `b3c4f23793ef7b8693ff72c8388fd93727e81db39e0959a7417a16b6ca97b7e2`
- `frozen_at=2026-09-09T19:50:05+00:00`
- hold base `4fe7df60ef4c829d4024c35218d8f7c37a2b80ad`
- frozen files `88`

No second real-freeze invocation occurred.

## Published freeze evidence

`PLAN_LOCK.json`:

- bytes `29669`
- SHA256 `875aa8c3a54fbb8c93c475d35ac70390e4383ac4fd5a7d060f5ec8ca1e050d4b`
- creation/mtime UTC `2026-09-09T19:50:08.9007599Z`
- raw `frozen_at=2026-09-09T19:50:05+00:00`
- publication minus observed freeze instant `+3.9007599s`

`FROZEN_HASHES.json`:

- bytes `8689`
- SHA256 `9c5ef0da8259969f71b2717350bec78f85fbf3642bc9e42feb087f32bd095dec`
- creation/mtime UTC `2026-09-09T19:50:08.9752044Z`
- publication minus observed freeze instant `+3.9752044s`
- entries `88`
- independent rehash `88/88`, mismatch `0`
- exact-set proof: 89 current non-cache builder files = 88 manifest keys + manifest self; extra-unpinned `0`, missing-pinned `0`

Freeze/auditor imports created exactly two builder-local `__pycache__` directories / four `.pyc` files. Their exact resolved paths were verified inside the v9r29 builder and only those two cache directories were removed. No frozen/source/runtime evidence was touched. PowerShell/.NET-only post-cleanup verification returned cache0/pyc0, frozen 88/88, mechanics69/69.

## Post-freeze boundary

Final reconciliation before durable closure:

- plan remains SHA256 `d1ed3eda0f64a1570d71423604499d90f5af690dbde39590bbeb19883efd751a`; rubric and exclusion manifest unchanged; mechanics69/69
- `PLAN_LOCK.json` and `FROZEN_HASHES.json` remain byte-identical to the SHAs above; frozen manifest 88/88 exact
- no `phasec_driver.run.lock`, source truth/meta, anchors/slots, author candidates/chunks, A/B/C artifacts, selector output, or `evalset.jsonl`
- Phase-C root `C:\Users\joji\bc-v3-v9r29-phaseC` absent
- canonical audit remains exactly 4 rows / SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- protected dev/dev-v2/holdout remain absent
- production `ml-service` diff remains 0
- repo remains clean and local/upstream/direct-origin equal at D-168 base `7ca0ded0664515a35520782e029789dc833e071b` before this durable record
- immutable v9r28 predecessor key hashes remain 8/8 exact

## Gate boundary

V9r29 now has immutable exactly-once PASS evidence for Smoke A, Smoke B, and real freeze. None of these three one-shot stages may be rerun.

**D-169 REAL FREEZE PASS. STOP before Phase-C PRE-EXECUTION.** A next separately explicit continuation may authorize only a fresh Phase-C pre-execution gate. Source-truth snapshot, Phase-C execution, semantic roles, protected dev-v2/holdout evaluation, production, and canonical audit append remain prohibited until their own later gates.
