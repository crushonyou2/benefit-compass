# Retrieval v3 D-135 — generation-v9r21 real-freeze CONTRACT_INVALID_GENERATION

Date: 2026-09-08
Stage: exactly-once real freeze / independent post-freeze provenance review / docs-only durable closure
Generation: `retrieval-v3-dev-generation-v9r21`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r21`
D-134 base commit: `311f8b7e866ff57dce7a0370c4c2a1f7dd9273f7`

## Verdict

**v9r21 = HARD HOLD / CONTRACT_INVALID_GENERATION / NON-RESUMABLE / NON-REPAIRABLE.**

The D-135 pre-freeze gate itself passed: D-134 repo/remote state, final plan/mechanics, preserved one-shot Smoke A/B evidence, freeze-binding regression, rerun/concurrency regression, and zero-state were revalidated. The real v9r21 freeze was then consumed once and published both immutable freeze artifacts.

The post-freeze provenance audit found a later hard defect: `PLAN_LOCK.json` records `frozen_at = 2026-09-08T05:10:00+00:00`, but the lock was physically created at `2026-09-08T05:07:24.174Z` and `FROZEN_HASHES.json` at `2026-09-08T05:07:24.236Z`. The structured freeze time is therefore about **155.826 seconds in the future relative to the actual lock publication**.

Retrieval-v3 durable provenance treats `frozen_at` as a truthful observed freeze/artifact-authoring instant, not merely as a lower-bound ordering marker. D-028 explicitly classified a future/impossible `frozen_at` as false provenance and corrected it to a truthful durable boundary; later generation records repeatedly require a `truthful observed` freeze time. Therefore the v9r21 lock's future timestamp is an operative provenance-contract failure, not descriptive wording drift.

The current frozen artifacts must remain byte-for-byte failure evidence. No second real freeze, deletion, replacement, timestamp edit, same-generation repair, Phase C, source-truth creation, protected evaluation, holdout evaluation, production change, or canonical audit append is authorized.

## Reconciled D-135 base and pre-freeze evidence

Immediately before the one-shot real-freeze attempt, the D-134/final-byte gate had revalidated:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `311f8b7e866ff57dce7a0370c4c2a1f7dd9273f7`
- working tree clean before D-135 local documentation
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- canonical audit exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- main-tree protected `eval/retrieval-v3/dev/` and `eval/retrieval-v3/holdout/` plaintext paths absent
- OMP `18.1.13`; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`; bundled Paseo `0.7.2`
- final `GENERATION_PLAN.json` 65,857 bytes, SHA256 `9a3369a3dada669a2cd448f59ceaf41982fb94fc11029b20d2431f72430653ec`
- `input/EXCLUSION_INPUTS.json` SHA256 `518292880dbdf24335eb2412204e62582d3abf0a73e3a2276f01dac9d3b08b59`
- `RUBRIC.json` SHA256 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- `freeze_plan_v9r21.py` SHA256 `65ba9208033526052db0d77e90dd14145a7dcb3c391c9cad87b2d17ec1a2bcf4`
- `test_freeze_rerun_rejection.py` SHA256 `28f5383e9f8476604997055e048f5bfdd96a92c22e1d086769e51c74b083dd86`
- mechanics 59/59 exact, mismatch 0; builder cache/pyc 0; `PLAN_LOCK.json`, `FROZEN_HASHES.json`, run lock, source truth, and staging absent
- frozen Smoke A auditor `SMOKE_PASS` on the preserved 10-line session SHA256 `37c536ce6fb4dcbe686c9e3f6efb70a7dc008e9192583c5f52fc6cad9b3ddae5`
- frozen Smoke B auditor `LIFECYCLE_SMOKE_PASS` on the preserved 21-line session SHA256 `6e7f1517bf1dac95a82d80488400d571974d113adfa6e02860d9babec60312bb`
- final-byte `FREEZE_BINDING_PASS` 66 and `FREEZE_RERUN_REJECTION_PASS` 38 on disposable copies only
- two independent read-only pre-freeze reviews found no operative blocker

Both v9r21 smokes remain permanently consumed and immutable.

## One-shot real-freeze evidence

The real builder now contains the two O_EXCL-published freeze artifacts and they are internally coherent:

- `PLAN_LOCK.json`: 25,208 bytes, SHA256 `82196b602eab22df4a7484484399732db39dfaffdcc839b106a580305118c19f`
- `FROZEN_HASHES.json`: 7,320 bytes, SHA256 `4d6d7e9c0218578cf9b1457cd22ea10ba8b3dde36083f57fcd75d25219c44096`
- frozen hash entries: 75
- independent rehash of all 75 entries: missing 0, mismatch 0
- lock hold base: `e93c258a314065c75120dcdbb9f165ca28ba3295`
- lock `frozen_at`: `2026-09-08T05:10:00+00:00`
- Windows `PLAN_LOCK.json` creation time: `2026-09-08T05:07:24.174Z`
- Windows `FROZEN_HASHES.json` creation time: `2026-09-08T05:07:24.236Z`
- delta from lock creation to claimed `frozen_at`: about +155.826 seconds

The lock also preserves the exact D-133/D-134 Smoke-A/B bindings and their frozen PASS verdicts. That internal coherence does not cure the false structured freeze time.

No evidence was found of Phase C, `phasec_driver.run.lock`, source truth, semantic role output, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append after the failed freeze boundary.

## Root cause in frozen mechanics

`freeze_plan_v9r21.py` permits a caller-supplied `--frozen-at` and assigns it directly:

`frozen_at = args.frozen_at or datetime.now(timezone.utc)...`

Its only timestamp gate requires `frozen_at > HOLD_BASE_TIME`. It does **not** mechanically reject a caller-supplied future timestamp or otherwise bind the structured timestamp to the observed publication instant. The stale nearby comment referring to D-126 is descriptive only; the operative defect is the missing truthfulness/upper-bound protection for `frozen_at`.

The same frozen mechanics correctly use exclusive `O_CREAT|O_EXCL` publication for `PLAN_LOCK.json` and `FROZEN_HASHES.json`, and the 75-entry frozen set is coherent. Thus this is not a rerun-prevention failure. It is a structured provenance-time failure discovered only after the one-shot freeze was consumed.

## Why v9r21 cannot be repaired

The v9r21 post-freeze contract and D-135 one-shot authorization make the first real invocation final regardless of caller-side or post-run failure. The lock/hash artifacts are also now present and are protected by the generation's absent-at-freeze and exclusive-create rules.

Therefore none of the following is permitted:

- edit `PLAN_LOCK.json` to replace `frozen_at`
- delete either freeze artifact and invoke again
- call `freeze_plan_v9r21.py` a second time
- patch `freeze_plan_v9r21.py` after both smokes and the freeze were consumed
- reuse the v9r21 Smoke A or Smoke B in a modified same-generation builder
- treat the false time as a cosmetic note and advance to Phase C

The pre-review local `D-135 REAL FREEZE PASS` documentation draft was never committed or pushed. It is discarded in this closure because the independent post-freeze review invalidated that verdict before durable publication.

## Successor requirement

A successor may proceed only as a **fresh generation/private builder** with fresh final-byte one-shot Smoke A, fresh final-byte one-shot Smoke B, and a fresh exactly-once real freeze after a new pre-gate. At minimum, before any successor smoke, its frozen mechanics must make `frozen_at` truthful by construction or fail closed on an impossible future caller timestamp while preserving the v9r21 exactly-once O_EXCL publication guarantees.

Retrieval/evaluation semantics, rubric, quotas, exclusion sets, selector rules, and protected-data boundaries must remain unchanged unless separately authorized. The v9r21 builder, both smoke evidence roots/sessions, `PLAN_LOCK.json`, and `FROZEN_HASHES.json` remain immutable failure evidence.

## Stop

D-135 closes v9r21 as a failed real-freeze generation. **Do not start the successor generation inside this closure action.** The next separately authorized logical stage, if any, is fresh-successor PRE-SMOKE construction/validation only; Phase C and all protected evaluation remain prohibited.
