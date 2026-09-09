# Retrieval v3 D-153 — generation-v9r24 exactly-once real freeze PASS

Date: 2026-09-09
Stage: real-freeze pre-gate / exactly-once publication / post-freeze provenance closure
Generation: `retrieval-v3-dev-generation-v9r24`
Private builder: `C:/Users/joji/Documents/programming/bc-v3-dev-v2-builder-20260909-v9r24`
D-152 Smoke-B base commit: `1e6b54faaa3c6c308e6e37e6bae205806a1a3eaa`

## Verdict

**D-153 / v9r24 REAL FREEZE: PASS.** The D-152 final bytes, with Smoke A and Smoke B each already consumed exactly once and PASSed, passed a fresh real-freeze pre-gate. Frozen `freeze_plan_v9r24.py` was then invoked exactly once against the real builder with both preserved smoke proofs fully pinned and with `--frozen-at` omitted. The invocation succeeded and published `PLAN_LOCK.json` and `FROZEN_HASHES.json` through the frozen O_EXCL exactly-once path.

Independent post-freeze rehash and provenance review found no operative blocker. `FROZEN_HASHES.json` contains exactly 81 entries; all 81 currently rehash exactly with missing 0 / mismatch 0, and the manifest exact set equals the complete current freeze-eligible builder file set (current freeze-eligible set 81; manifest_only 0; eligible_unfrozen 0). Raw `frozen_at=2026-09-09T04:05:15+00:00` precedes lock creation by 3.9718900 seconds and frozen-hash publication by 4.0364064 seconds. The D-135 future-time provenance defect did not recur.

Real freeze is now permanently consumed and non-repeatable. `PLAN_LOCK.json` and `FROZEN_HASHES.json` are immutable evidence and must not be edited, deleted, recreated, regenerated, or replaced.

**STOP boundary:** D-153 did not execute Phase C, create a v9r24 Phase-C run lock or source-truth snapshot, launch Author/Reviewer/C/selector roles, access protected dev-v2/holdout plaintext, change production `ml-service/`, or append the canonical evaluation audit. The next separately authorized logical stage is only a fresh **Phase-C PRE-EXECUTION gate**. D-153 authorizes no Phase-C execute.

## Fresh pre-freeze reconciliation

Immediately before the one real-freeze invocation:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `1e6b54faaa3c6c308e6e37e6bae205806a1a3eaa`
- working tree clean; production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- canonical audit exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/dev-v2/`, `eval/retrieval-v3/holdout/` absent
- final plan 73,596 bytes, SHA256 `ce6b55d1044e79d95543119ce2aa916575ba56da4c59639c96d36e9a5f832c05`
- rubric SHA256 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- frozen freeze mechanic `freeze_plan_v9r24.py` 106,254 bytes, SHA256 `5a7873501528b449f12cdaf3c51bdff2eb16ec9f33d4eebc6dbab7f44b808983`
- exclusion manifest SHA256 `3549cc2a5f53dc6aeecf241be062d8249147f64f0156da68f10f673699c4c95f`
- mechanics 63/63 exact; pre-freeze file_count 80, builder cache dirs 0 / `.pyc` 0
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, source truth/meta and final evalset absent
- Phase-C root `bc-v3-v9r24-phaseC` and coord-execute roots absent

Fresh real-freeze-critical regressions PASSed on these exact bytes without invoking real freeze: `FREEZE_BINDING_PASS` 87, `FREEZE_RERUN_REJECTION_PASS` 66, exact Paseo CLI gate 64, launcher reachability 87, and registry descendant scan 37. Builder cache remained 0/0 because `PYTHONDONTWRITEBYTECODE=1` was propagated.

A fresh independent read-only pre-freeze reviewer (Web) returned **FINAL PASS — blockers none** after independently rechecking current bytes, zero-state, both preserved smoke proofs, exactly-once publication mechanics, truthful observed-now timestamp handling, and audit/production/protected boundaries.

No protected plaintext recovery or prohibited Git object/history access was used.

## Preserved Smoke A/B proofs bound at freeze

Smoke A was freshly re-audited before real freeze and remained unchanged:

- agent `8330f356-428b-4581-a2d8-a9cd1f106e91`
- exact session 10 lines, SHA256 `55271df78ed0bf46cce04ab817f904cbfad7c04cb9ca8a8df7362f6e27f37327`
- `phasec_probe=1`, descendants 0, fallback proven
- frozen verdict `SMOKE_PASS`

Smoke B was freshly re-audited before real freeze and remained unchanged:

- agent `71ac0985-5714-4b3d-a82a-0d9c8727aa66`
- exact session 19 lines, SHA256 `34d3596c8109c1d19a2d5e5c278ee7167db0d9aae143aa522b208e2e2ac0e805`
- `role_smoke_probe=1`, `todo=4`, fixed deny triple each 1
- six exact one-row/59-byte outputs, descendants 0, fallback proven
- frozen verdict `LIFECYCLE_SMOKE_PASS`

The published lock reran and bound both frozen auditors at freeze time. Its audit-bound fields carry the exact A/B agent IDs, session paths/hashes/line counts, probe/tool evidence, deny/output evidence and descendants 0.

## Sole real-freeze execution

Exactly one fresh execution-only top-level stage agent owned the one-shot real freeze:

- executor `68e85b30-a92a-4dbb-bf4d-39d555f3f0e0`
- title `D-153 v9r24 real freeze executor`
- ParentAgentId null
- provider/model `omp` / `opencode-go/muse-spark-1.3-contributor`
- thinking `xhigh`, mode `full`, main-repo cwd, final idle
- executor OMP session `C:\Users\joji\.omp\agent\sessions\-Documents-취준자료-project-repos-benefit-compass\2026-09-09T04-02-57-236Z_01a08455-4a54-726f-bb64-aa328feaf276.jsonl`
- structural session count 20 lines; SHA256 `d273dec1c1d2bead29406389906664ed0815f39ef123215bec88e8965ab284d7`

## Execution/process provenance correction

There were 3 bash calls total due transport repair, but ONLY ONE actual freeze process:

- Call1 had zero `freeze_plan` occurrences and returned `FREEZE_COMMAND_MISSING` no-op because the initial prompt lost the command body; Web rechecked `PLAN_LOCK`/`FROZEN_HASHES` absent.
- Call2 contained one `freeze_plan` string using the `/c/...` python path but exited 127 `command-not-found` before Python started; Web again rechecked `PLAN_LOCK`/`FROZEN_HASHES`/`runlock` absent.
- Call3 used `C:/Users/.../python.exe`, contained exactly one `freeze_plan_v9r24.py` occurrence, no `--frozen-at`, and successfully ran the first/only real freeze process.

Treat this as a process/transport correction, not a generation contract failure, because no earlier freeze process started and the O_EXCL one-shot artifacts were still absent before call3.

Transport correction prompt SHA1 `dffef72c741828cceb0234e3ae1288a1d7d2c431217d04d5d35171ee480b9e60`; final correction prompt SHA `95d90a4ada2a00f4f0f2f0096e2edcf805b26a08cb4e92ec59e264a3a06edb4a`.

The single successful bash result returned:

- plan SHA256 `ce6b55d1044e79d95543119ce2aa916575ba56da4c59639c96d36e9a5f832c05`
- plan bytes `73596`
- rubric SHA256 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- lock SHA256 `d084914f3e3637636b30aa88cfe68bae75840967890ba517fb688bab8901730b`
- exclusion manifest SHA256 `3549cc2a5f53dc6aeecf241be062d8249147f64f0156da68f10f673699c4c95f`
- `frozen_at=2026-09-09T04:05:15+00:00` (script-derived; `--frozen-at` omitted)
- hold base commit `56c9138ef9a1ad3db2d0dfa949d5d31764cf5d61`
- frozen files `81`

There was no second freeze process and no preliminary or follow-up freeze invocation.

## Published freeze evidence

`PLAN_LOCK.json`:

- bytes: `27,412`
- SHA256 `d084914f3e3637636b30aa88cfe68bae75840967890ba517fb688bab8901730b`
- creation/mtime UTC `2026-09-09T04:05:18.9718900Z`
- raw `frozen_at=2026-09-09T04:05:15+00:00`
- publication minus observed freeze instant `+3.9718900s`

`FROZEN_HASHES.json`:

- bytes: `7,965`
- SHA256 `056e789c4d3a5941a0e808e5e46275f1a02edf1790891ef3643e1a63b185e62d`
- creation/mtime UTC `2026-09-09T04:05:19.0364064Z`
- publication minus observed freeze instant `+4.0364064s`
- entries: `81`
- independent rehash: missing 0 / mismatch 0
- exact-set proof: 81 manifest keys = 81 current freeze-eligible builder files, manifest_only 0, eligible_unfrozen 0
- post-freeze file_count 82; cache 0 / pyc 0

The timestamps prove the structured freeze instant was observed before publication, not in the future. The exact-set rehash proves no current freeze-eligible builder byte is omitted from or inconsistent with the published manifest.

## Independent post-freeze review

A separate read-only reviewer (Web) independently returned **FINAL PASS — blockers none**. It rechecked the lock/hash SHAs and sizes, 81/81 rehash, timestamp truthfulness, exact A/B lock bindings, the execution-only agent identity, exactly one freeze process with no `--frozen-at`, and later-stage zero-state.

## Post-freeze boundary

Final reconciliation before durable closure:

- repo remained at D-152 base `1e6b54faaa3c6c308e6e37e6bae205806a1a3eaa`, clean and aligned with upstream/direct origin
- plan remains `ce6b55d1...f832c05`; mechanics 63/63; builder cache/pyc 0
- published lock/hash remain byte-identical at the SHAs above; manifest 81/81 exact
- no v9r24 `phasec_driver.run.lock`, source truth/meta, Phase-C root, execute root, candidate/adjudication/selector/eval output
- canonical audit remains 4 rows / SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- production `ml-service/` diff remains 0
- protected dev/dev-v2/holdout paths remain absent

## Gate boundary

V9r24 now has immutable one-shot PASS evidence for:

1. Smoke A exactly once,
2. Smoke B exactly once,
3. real freeze exactly once.

None of these three one-shot steps may be rerun. `PLAN_LOCK` and `FROZEN_HASHES` are immutable evidence; never edit/delete/regenerate/recreate.

The next separate logical stage, only after another user `진행해`, is **Phase-C PRE-EXECUTION**. This D-153 closure itself authorizes no Phase-C execute, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append.
