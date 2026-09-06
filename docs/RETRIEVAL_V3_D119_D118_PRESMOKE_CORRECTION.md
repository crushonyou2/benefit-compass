# Retrieval v3 D-119 — D-118 PRE-SMOKE correction / generation-v9r18 final-byte PASS

Date: 2026-09-07
Stage: append-only correction before any v9r18 smoke
Generation: `retrieval-v3-dev-generation-v9r18`

## Verdict

**D-118 final-byte claim is corrected by D-119; v9r18 PRE-SMOKE remains PASS on the corrected bytes below.** No v9r18 model smoke, real freeze, Phase C, source-truth snapshot, semantic role, protected evaluation, holdout evaluation, production change, or canonical audit append occurred before this correction.

## What D-118 missed

After D-118 was committed, the final duplicate/prelaunch grep found a stale contradictory paragraph in `carry_exclusions_v9r18.py`: operative code and all final gates required the approved D-117 fingerprint-only ELEVENTH exclusion, but one docstring paragraph still said there was no failed-D117 set and that the manifest kept TEN. This was a real provenance/contract-description drift and therefore Smoke A remained blocked.

D-118's recorded `GENERATION_PLAN.json` and `carry_exclusions_v9r18.py` SHAs are superseded by this correction. D-118 history is not rewritten.

## Narrow same-stage repair

The same v9r18 OMP implementation executor changed only the stale carry docstring so it consistently states:
- failed-D117 exists as the eleventh query-fingerprint exclusion;
- it is mechanically normalized SHA256 fingerprint-only freshness evidence from the already established D-117 360-row merged pool;
- no semantic/template reuse;
- gold exclusions unchanged;
- v9r18 manifest carries ELEVEN query sets.

No v9r17 query plaintext was re-read in this correction. Operative exclusion code/inputs were unchanged. The normal generation-plan mechanics map was regenerated only to repin the changed carry source.

## Corrected final identities

- `GENERATION_PLAN.json` SHA256 `848b586235653737210d78424baa00935c86665aff2a7542d71ffa2b6807c532`
- `carry_exclusions_v9r18.py` SHA256 `91a097fcb759c75faf84c0838ad17b93c1adfa14517230ededa38dd88b24dcab`
- `freeze_plan_v9r18.py` SHA256 `f0a3bd4d2add0d52e9bd15a7718d6b7cae3e02799d08c81ec26ae45ae6ce1c79`
- `input/EXCLUSION_INPUTS.json` SHA256 `168105ac49d357f4c05d4ac999b0d01aaa60b6db5c9c88b91cb0374503a72f44`
- `input/failed_d117_query_fingerprints.json` SHA256 `fc681a835e41b85317eb257250d47b3b74ec201d218dfef561ae91db625ab5e4`
- `RUBRIC.json` SHA256 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- mechanics map 56/56 exact, mismatch 0.

Single v9r18 implementation executor remains the same OMP session `C:\Users\joji\.omp\agent\sessions\-Documents-programming\2026-09-06T19-08-22-606Z_01a0781f-26ce-740e-b1eb-f28bdff3556a.jsonl`; final observed 1274 lines, SHA256 `c04a7c1640f0f143820f895b1f2b5a8b5f1050ec361ffd5c24914c7643fc8295`, Muse Spark 1.3 contributor, fallback false.

## Final validation after correction

Independent Web rerun on the corrected bytes:
- ELEVEN query-fingerprint gates: 55 pairwise comparisons, overlap 0; D117 probe bound correctly
- staging exact set: PASS 24
- bundled Paseo CLI gate: PASS 64
- writer preflight: PASS 36
- launcher reachability: PASS 87
- lifecycle contract: PASS 53
- role tools: PASS 171
- role completion: PASS
- Phase-C confinement: PASS 210
- freeze-binding regression: PASS 66, disposable plan SHA equals corrected `848b5862...`
- mechanics 56/56 exact
- compile/Bun/tsc PASS.

Tests created only two builder-local Python cache directories; after proving both resolved inside the v9r18 builder, only those caches were removed. Final real builder: 70 files, cache0, no `PLAN_LOCK.json`, `FROZEN_HASHES.json`, run lock, source truth/meta, anchors/slots, candidates, evalset, or out.

## Next

**Corrected v9r18 PRE-SMOKE PASS.** A fresh duplicate/daemon/final-hash gate must still run immediately before consuming Smoke A. Exactly one Smoke A may then run on plan SHA `848b586235653737210d78424baa00935c86665aff2a7542d71ffa2b6807c532`; Smoke B remains conditional on stable frozen Smoke-A auditor PASS. Any smoke failure closes v9r18 with no retry/same-generation repair.
