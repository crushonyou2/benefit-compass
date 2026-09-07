# Retrieval v3 D-124 — generation-v9r19 PRE-SMOKE Web PASS

Date: 2026-09-08
Stage: fresh-successor static / pre-smoke independent gate
Generation: `retrieval-v3-dev-generation-v9r19`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r19`
Hold base: D-123 commit `f7c93cb8cd65e48b50ad618d058d39d5bb583bfe`

## Verdict

**PRE-SMOKE PASS.** V9r19 is a fresh successor to immutable v9r18 and contains only the D-123-authorized mechanical repairs. Final-byte static/confinement/freeze-binding review passes. No v9r19 Smoke A/B, model generation, real freeze, Phase C, protected dev-v2 evaluation, holdout evaluation, production change, or protected result/audit append has occurred.

The next logical stage is a separately gated successor Smoke A duplicate/preflight check. This record does **not** authorize silently consuming Smoke A/B inside the current static-repair stage.

## Canonical repo / production boundary

Final read-only reconciliation before this verdict:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `f7c93cb8cd65e48b50ad618d058d39d5bb583bfe`
- working tree clean before this D-124 documentation write
- `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- main-tree `eval/retrieval-v3/dev/` plaintext absent
- main-tree `eval/retrieval-v3/holdout/` plaintext absent
- canonical audit remains 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`

No protected plaintext recovery path was used.

## D-123 successor identity and final plan

Final pre-smoke plan:

- plan SHA256 `a442f5641f1dbada08ce5eeb71b838746910c58c8b979e25bacc24a134420705`
- plan bytes `63,214`
- exclusion manifest SHA256 `1caffc012103abea5c85487588bd0c6daaea2766e90cc41cb113569086f56e3b`
- plan-bound manifest SHA equals actual manifest SHA
- rubric SHA256 unchanged `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- final mechanics map: 57 files, missing 0, hash/byte mismatch 0
- Python parse errors: 0

`freeze_plan_v9r19.py` can materialize the deterministic pre-smoke plan/manifest, then fail-closes at `smoke A pinning required`. In the actual builder there is still no `PLAN_LOCK.json`, no `FROZEN_HASHES.json`, and no run lock. The freeze-binding regression independently reaches the synthetic audit stage on a disposable copy and binds the D-123 hold base.

## D-123 mechanical repairs

### Exact slot binding

`validate_pool.py` now loads immutable `slots_1.json` + `slots_2.json` and binds every returned candidate ID to the exact frozen `intended_stratum` and `intended_location`. Stable fail codes include `slot_stratum_mismatch` and `slot_location_mismatch`.

The regression reproduces the v9r18 failure pattern: a slot with `intended_location=false` and returned candidate metadata `true` fails exact binding directly instead of surviving until aggregate count checks.

### Validator-exact location contract

The author-facing contract and validator now share one frozen allowed location vocabulary rather than the prior vague “real location token” promise. The narrow D-123 additions include `천안` and `아산`, while the parser handles frozen particle-attached forms such as `천안에서`, `천안에`, and `천안에살고` without opening arbitrary substring matching.

Regression coverage: 6 positive forms including `천안`/`아산`/attached particles and 5 non-place negative guards; all PASS. Location quotas and location checks were not weakened.

### Twelfth fingerprint-only freshness set

Under the standing D-087 complete-failed-generation precedent, v9r18's complete collected Author-1 180 + Author-2 180 queries are carried only as normalized SHA256 query fingerprints:

- D-123 fingerprint file SHA256 `2821c326ab28b9704d569de37379141edb5816e3fe99e394321293e10820d3ba`
- source Author-1 candidate file SHA256 `158e47639db7ee86b8a71874a1b6b582c68dea1efcbff7b5af7c59f6fad6e6c5`
- source Author-2 candidate file SHA256 `01028483c324331c2c8d23c6cb48c3eb662c9d35a72581cbb46b9e4f421a008d`
- 360 rows / 360 unique
- overlap with every prior set = 0
- exactly 12 query-fingerprint sets total
- exactly 66 pairwise overlap checks
- no v9r18 query semantic/template reuse
- no failed-generation gold set; gold exclusions remain canonical dev-v1/holdout/history only

The final generated plan's `required_query_overlap_sets` also contains exactly the same 12 sets, including D-086, D-117, and D-123.

## Preserved predecessor contracts

V9r19 preserves the prior operative contracts that were not implicated in D-123:

- D-117 Reviewer A/B and Reviewer C prepared staging exact sets; `search_snapshot.py` is not staged into reviewer/C roots
- D-112 exact bundled Paseo CLI only: `C:\Users\joji\AppData\Local\Programs\Paseo\resources\bin\paseo.cmd`; no PATH/desktop fallback
- D-110 writer-envelope/local-preflight semantics
- role filesystem/tool confinement and zero-deny helper contract
- deterministic completion gates
- one-shot smoke/freeze/Phase-C lifecycle semantics
- A/B all 360, C all 360, final selector 180
- rubric, quotas, protected-data boundaries, retrieval/release semantics unchanged

The author staging list now includes the D-123 fingerprint-only input because `role_check_anchor` enforces all twelve query sets. Reviewer/C staging remains unchanged and exact.

## OMP provenance reconciliation

Current actual OMP config still selects:

- default `opencode-go/muse-spark-1.3-contributor:xhigh`
- plan `opencode-go/muse-spark-1.3-contributor:xhigh`

The actual installed OMP binary is now `omp/18.1.13`. V9r19's wrapper/probe/test provenance text and compatibility pins were updated to that actual version. This does **not** rewrite v9r18 historical provenance: D-122/v9r18 remains historical evidence for the version observed in that generation.

No new OMP root/plan/model execution occurred in D-124.

## Final non-model test battery

Final bytes passed:

- Paseo exact-CLI gate: 64 checks
- role writer preflight: 36 checks
- launcher reachability: 87 checks
- lifecycle-smoke contract: 53 checks
- role-tool confinement/helper matrix: 172 checks
- role completion gate: PASS
- Phase-C confinement: 210 checks, including Python compile and TypeScript type gate
- freeze-binding regression: 66 checks; disposable synthetic lock binds D-123 hold base; no real lock written
- Reviewer/C staging exact-set regression: 24 checks
- TWELVE-set regression: 12 exact sets / 66 pairwise / overlap 0
- D-123 slot/location regression: PASS

Expected negative probes in the confinement/staging suites fail closed and are part of the passing test contract.

## Fresh-builder boundary at verdict

After tests, fresh test caches were removed. Current v9r19 builder state:

- `__pycache__` directories: 0
- `PLAN_LOCK.json`: absent
- `FROZEN_HASHES.json`: absent
- `phasec_driver.run.lock`: absent
- source truth/meta: absent
- anchors/slots: absent
- Author candidate files: absent
- merged pool/evalset: absent
- matching v9r19 runtime roots under user home: 0
- matching v9r19 processes: 0

Therefore no successor one-shot evidence has been consumed.

## Gate boundary

V9r19 is **static/pre-smoke ready only**. V9r18 remains immutable and permanently closed as D-123 `CONTRACT_INVALID_GENERATION`.

Next stage, if separately approved, must first re-reconcile duplicate/runtime/model provenance and may consume **one** final-byte Smoke A only. Smoke B remains conditional on a stable frozen Smoke-A PASS under the standing lifecycle contract. Any successor smoke failure closes that generation; no same-generation repair/retry. Protected dev-v2 and holdout remain prohibited.
