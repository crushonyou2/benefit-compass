# Retrieval v3 D-121 — generation-v9r18 REAL FREEZE PASS + Smoke-A lock-note correction

Date: 2026-09-07
Stage: real-freeze closure + append-only descriptive correction
Generation: `retrieval-v3-dev-generation-v9r18`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260907-v9r18`

## Verdict

**v9r18 REAL FREEZE: PASS.** The D-119 corrected final bytes were frozen once, after D-120 exact one-shot Smoke A/B PASS. `PLAN_LOCK.json` binds the exact smoke agents/cwds/sessions/wrapper evidence; all 71 `FROZEN_HASHES.json` entries independently rehash with missing 0 / mismatch 0.

No Phase C, source-truth snapshot, Author/Reviewer/C, selector, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append occurred in D-121.

## Reconciled base

Immediately before freeze, repo branch was clean at D-120 `3aa1e1301f8119726d4a1c17c2c878063191c974`, local/upstream/direct remote equal; production `ml-service` diff zero; canonical audit exactly 4 events SHA `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`.

Real builder before freeze: 70 source/support files/cache0, plan SHA `848b586235653737210d78424baa00935c86665aff2a7542d71ffa2b6807c532`, no locks/run lock/source truth/evalset/runtime output.

## Real freeze

Freeze executed once under Windows Python UTF-8 mode with no bytecode writes and exact D-120 Smoke A/B bindings.

- UTC `frozen_at`: `2026-09-06T20:52:30+00:00`
- plan SHA256 `848b586235653737210d78424baa00935c86665aff2a7542d71ffa2b6807c532`
- plan bytes 66,253
- rubric SHA256 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- exclusion manifest SHA256 `168105ac49d357f4c05d4ac999b0d01aaa60b6db5c9c88b91cb0374503a72f44`
- `PLAN_LOCK.json` SHA256 `20d8a14518d57d28ad66ec65da627db300ad0180de402180675af4d4132a868c`
- `FROZEN_HASHES.json` SHA256 `7f3f4903c387d05a20e71ae5a6bc493e1264f234512a3509708e0f1b7fb01955`
- frozen entries 71; independent rehash missing 0 / mismatch 0
- hold base commit D-117 `ecd2893d9e97ae3aca94e454b6ba36da747a6990`.

After freeze: builder 72 files/cache0; run lock/source truth/meta/anchors/slots/candidates/evalset/out all absent.

## Exact lock-bound smoke evidence

Smoke A lock fields bind:
- agent `69a090c5-5352-4fa2-aeb4-7dfad7857dea`
- cwd `C:\Users\joji\bc-v3-v9r18-coord-smoke-20260907\cwd`
- session 10 lines SHA `81aaddc5c560c350913e0302b780c2fe90fb921dc359f4935d82bb714c252b35`
- `phasec_probe=1`, descendants0, audit `SMOKE_PASS`.

Smoke B lock fields bind:
- agent `4b5789ff-ce4d-4f89-ac6a-f8d830d10cae`
- cwd `C:\Users\joji\bc-v3-v9r18-lifecyclesmoke`
- session 21 lines SHA `c0d7dc43155b66db7c8075276817330dc0a3720d1c54b1e07d18c005557b8c58`
- `role_smoke_probe=1`, exact deny triple and six allowed 1-row writes, descendants0, audit `LIFECYCLE_SMOKE_PASS`.

## Append-only correction — stale Smoke-A lock `note`

Post-freeze independent inspection found one descriptive sentence in `PLAN_LOCK.smoke_top_level_verification.note` inherited from older generations: it calls Smoke A “neutral adversarial” and says its prompt requested forbidden accesses then `phasec_probe` fallback. The actual D-120 Smoke-A prompt directly requested the neutral structural `phasec_probe` once.

This is **descriptive drift, not an operative smoke-contract failure**, and the frozen bytes are not mutated:
- frozen `GENERATION_PLAN.coordinator_confinement.smoke_rule` requires exactly one **neutral deterministic** coordinator Smoke A on final bytes;
- frozen `audit_coord_smoke.py` gates exact top-level provenance, exact-one wrapper, tool-call subset `{todo, phasec_probe}`, `phasec_probe >=1`, descendants0; it does not gate prompt wording or require forbidden-access attempts;
- D-120 evidence satisfies those operative gates and freeze revalidated the same evidence to `SMOKE_PASS`.

Therefore this D-121 record supersedes only that stale lock-note description. The lock's actual audit-bound fields and all frozen hashes remain authoritative and unchanged.

## Next

**NEXT:** separate v9r18 Phase-C/source-truth pre-execution gate on these exact frozen bytes. No new smoke and no post-freeze source mutation are permitted. Exactly one execute coordinator may later be authorized only after that gate.
