# Retrieval v3 D-117 — generation-v9r17 Phase-C CONTRACT_INVALID_GENERATION

Date: 2026-09-07
Stage: one-shot Phase-C execution closure
Generation: `retrieval-v3-dev-generation-v9r17`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260907-v9r17`

## Verdict

**v9r17 = HARD HOLD / CONTRACT_INVALID_GENERATION / NON-RESUMABLE / NON-REPAIRABLE.** The single D-116 authorized Phase-C execute coordinator was consumed exactly once. The frozen driver successfully completed the fresh source-truth snapshot, both top-level Authors, both frozen Author audits, author collection/merge, and the 360-row mechanical pool validation. It then prepared Reviewer-A/B packet roots but failed closed before launching any reviewer because `build_packets_ab.py` staged `search_snapshot.py`, while the frozen driver and frozen generation plan require reviewer roots to contain no helper script and permit exactly `packet.jsonl`, `RUBRIC.json`, `source_truth.jsonl`, `reviewer_brief.md`, and empty `out/`.

Frozen driver terminal error:

`CONTRACT_INVALID_GENERATION: reviewerA: prepared staging contents unexpected: ['RUBRIC.json', 'packet.jsonl', 'reviewer_brief.md', 'search_snapshot.py', 'source_truth.jsonl']`

No retry, run-lock removal, driver resume, second execute coordinator, reviewer manual launch, or same-generation frozen-byte repair is permitted. Preserve all v9r17 runtime/staging/session bytes as failure evidence.

## Reconciled D-116 base

Before execute, repo branch `codex/retrieval-v3-user-search-quality` was at D-116 commit `6e8b935765a9fea8497a1e6fd8f8d0d5e5da2691`, local/upstream/direct remote equal and clean. Production `ml-service/` diff zero; canonical audit 4 events SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`.

D-115 freeze remained exact throughout and after execution:
- `PLAN_LOCK.json` SHA `71196c83c512c1d9ef06c5118b1e971e57f6ba5992113b2320ebfb5648d01bc1`
- `FROZEN_HASHES.json` SHA `7e11179db6a836941f2c37bc1cc8c4bb76fa13b26c28ff97d08c9f3455a6d080`
- 69/69 frozen entries rehash exact, mismatch 0

## Single execute coordinator

Final duplicate gate proved execute root/session, Phase-C root, run lock, and matching execute/Phase-C agents all absent/0. Exactly one coordinator was then launched:
- agent `baebbabf-5356-4a60-a916-7125e68fce28`
- cwd `C:\Users\joji\bc-v3-v9r17-coord-execute-20260907\cwd`
- top-level / Parent null / Muse Spark 1.3 contributor / xhigh
- wrapper mode `execute`, custom tool `phasec_execute`, built-in tools `todo`, frozen controls
- execute session `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r17-coord-execute-20260907-cwd\2026-09-06T18-34-17-650Z_01a077ff-f2b2-75ea-9278-a961ae622c89.jsonl`
- final observed session 23 lines, SHA `f972ed3de525d4c77528cc96cb407985c287e02da26c1ad439872160cd24193f`
- tool calls `phasec_execute=1`, `todo=4`
- frozen coordinator auditor in execute mode: rc0 `SMOKE_PASS`, descendants 0, fallback proven

The execute coordinator reported the frozen driver's rc3 error and stopped. No second execute occurred.

## Frozen driver progress

Atomic run lock:
`{"started": "2026-09-06T18:34:26Z", "pid": 67468}`

Fresh read-only source truth:
- 13,589 policy rows
- gov24 10,958 / youth 2,631
- SHA256 `9fe194653a4b5c9c688364aa9ae686996cb7cabfebd446a6b9a7e8895374c1a5`
- no vector/chunk/ranking query

Author-1:
- agent `bf4bdd50-cf85-4e81-95d7-0b8d5fe90bf2`, top-level, Parent null, exact cwd, Muse Spark xhigh, idle after completion
- exact six 30-row chunks = 180 rows
- helper access log 266 rows, zero DENY
- session 609 lines, SHA `0b556ce2d8579250760e5ff296cc6a92c37da6bda422f2f61b1906700e0705d6`
- independent frozen `audit_role_access.py`: `ROLE_ACCESS_PASS`, six exact writes, descendants 0, fallback proven

Author-2:
- agent `ab5130cd-170a-4326-9b1c-805fa0c580cb`, top-level, Parent null, exact cwd, Muse Spark xhigh, idle after completion
- exact six 30-row chunks = 180 rows
- helper access log 224 rows, zero DENY
- session 527 lines, SHA `bfb54d65c2f739be199b53d0624c3496c187c68106cd85e38b6645598287f7dc`
- independent frozen `audit_role_access.py`: `ROLE_ACCESS_PASS`, six exact writes, descendants 0, fallback proven

Mechanical pre-review artifacts created before the failure:
- `author1_candidates.jsonl`: 180 rows, SHA `6c668b3488beab7ef34ff6934d036be49e4e09d7582aeffb3b06ca5c7cbeebde`
- `author2_candidates.jsonl`: 180 rows, SHA `485b22a9c411f9ef22e2dad261a6c365217bf11e9683fe143c35a0f69f506ad0`
- `candidates_merged.json`: 360 rows, SHA `96c31fe332faf2cc098f8d01e079d97f3f7ab01c74ab28aa0e8e7e812617c26d`
- Reviewer-A packet: 360 rows, SHA `ee54c74d03b040df69dd088c76d769595f559a9a3bfd01a2e1e3e595b79737d2`
- Reviewer-B packet: 360 rows, SHA `b1dc2e8d263ab76d70bae27dddc1c0c9191576c186d2363f455650f481e71249`

These v9r17 authored/query/candidate rows are failure evidence only. They must not be reused as semantic templates in a successor.

## Frozen static defect

The frozen generation plan's `reviewer_filesystem_confinement` contract says each reviewer staging root contains exactly its own `packet.jsonl`, `RUBRIC.json`, a `source_truth.jsonl` copy, `reviewer_brief.md`, and `out/`, explicitly **“no helper scripts staged”**.

The frozen driver enforces the same exact prepared set at `phasec_driver.py` reviewer launch. However frozen `build_packets_ab.py` explicitly copies all of:
- `RUBRIC.json`
- `source_truth.jsonl`
- **`search_snapshot.py`**
- `reviewer_brief.md`

Thus the driver deterministically rejects the staging before Reviewer-A launch. This is a static internal contract inconsistency on frozen bytes, not a model judgment failure or infrastructure failure.

The correct fresh-successor repair direction is to preserve the no-helper-script reviewer contract and remove the obsolete `search_snapshot.py` staging copy (and add a permanent regression proving exact prepared-root equality), rather than weaken the driver allowlist. v9r17 itself remains immutable.

## Exact stop boundary

Present:
- run lock
- source truth/meta + anchors/slots
- Author-1/2 staging/session/access/output
- `author_chunks`
- author1/2 candidate files
- 360-row merged candidate pool
- prepared reviewer_a / reviewer_b staging roots and packets

Absent / never reached:
- Reviewer-A/B agents/sessions/output (reviewer agent count 0)
- `raw_A.jsonl`, `raw_B.jsonl`
- `frozen_raw_A/B`, raw freeze manifest
- transcript audit attestation
- packet keymaps
- A/B agreement/disagreement artifacts
- C agent/staging/output
- adjudicated pool
- selector final output / `evalset.jsonl`
- protected dev-v2 evaluation
- holdout evaluation
- production change
- canonical audit append

## Closure

Do not remove the v9r17 run lock, resume the driver, patch v9r17, launch reviewers manually, or launch another execute coordinator. A continuation requires a fresh successor generation, with v9r17 preserved byte-for-byte as failure evidence and with the A/B staging exact-set inconsistency repaired before any new smoke/freeze/Phase-C execution.
