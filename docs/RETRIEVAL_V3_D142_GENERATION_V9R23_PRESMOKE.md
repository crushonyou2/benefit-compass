# Retrieval v3 D-142 — generation-v9r23 PRE-SMOKE Web PASS

Date: 2026-09-08
Stage: fresh successor PRE-SMOKE construction + same-stage mechanical/parity repairs + independent Web review
Generation: `retrieval-v3-dev-generation-v9r23`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r23`
D-141 closure base commit: `d3a1b2a9c7443fc85023a3228f7bf88c330f4c85`

## Verdict

**D-142 / v9r23 PRE-SMOKE: WEB PASS.**

V9r23 is a fresh successor to immutable D-141/v9r22. It makes only the narrow mechanical repairs proven by the consumed v9r22 Phase-C failure: (1) carry v9r22's complete failed 360-query Author pool forward only as normalized SHA256 query fingerprints under the standing D-087/D-123 precedent, (2) replace C's truncation-prone whole-packet read surface with twelve fixed 30-row C-only packet resources, and (3) fail closed immediately when an exact role session proves final-stop/no-later-trigger while required outputs are structurally incomplete or invalid.

The final plan/implementation also reconciles the fresh D-141/v9r22 lineage, selector/exclusion plan-code parity, fresh v9r23 runtime titles, both Author staging inputs, and current no-helper/kind-bound confinement descriptions. Retrieval/evaluation semantics, rubric, quotas, A/B/C semantics, selector algorithm, canonical gold exclusions, D-123 slot/location repair, D-135 timestamp/O_EXCL mechanics, D-117 exact staging, D-112 bundled-Paseo provenance, D-110 writer envelope, and protected-data boundaries remain unchanged.

No v9r23 Smoke A/B, real freeze, source-truth snapshot, Phase C, Author/Reviewer/C generation role, selector, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append occurred in D-142.

The next separate gate may perform a fresh duplicate/runtime/provenance reconciliation and then consume **exactly one v9r23 Smoke A on these exact final bytes**. Smoke B, real freeze, Phase C, protected dev-v2, holdout, and production remain prohibited until later gates.

## Reconciled D-141 base and environment

Immediately before durable D-142 closure:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `d3a1b2a9c7443fc85023a3228f7bf88c330f4c85`
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- canonical `eval/retrieval-v3/audit/events.jsonl` remains exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/dev-v2/`, and `eval/retrieval-v3/holdout/` absent
- OMP `18.1.13`; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`
- bundled Paseo `0.7.2`

Immutable v9r22 failure evidence remains preserved:

- all 75 `FROZEN_HASHES.json` entries independently exact, missing 0 / mismatch 0
- v9r22 `phasec_driver.run.lock` remains present
- no v9r22 runtime/frozen evidence was edited, deleted, recreated, resumed, or reused semantically

## Sole implementation executor

Approved private-builder implementation and all same-stage repairs were performed end-to-end by one Paseo/OMP stage-machinery executor:

- agent `3526a9e5-dabd-498d-9c67-3df795c5650a`
- title `D142 v9r23 successor pre-smoke executor`
- ParentAgentId null
- cwd = main repo
- provider/model `omp` / `opencode-go/muse-spark-1.3-contributor`
- thinking `xhigh`, mode `full`, final status `idle`

This executor is implementation machinery only, not v9r23 generation/Smoke/Phase-C evidence. No second v9r23 executor or generation role was launched.

## Fresh identity and D-141 provenance

Final v9r23 identity:

- plan version `retrieval-v3-dev-generation-v9r23`
- seed `benefit-compass-retrieval-v3-dev-v2-generation-v9r23-2026-09-08`
- candidate IDs `v3g9r23-001..v3g9r23-360`
- C IDs `v9r23c-001..v9r23c-360`
- hold base commit `d3a1b2a9c7443fc85023a3228f7bf88c330f4c85`
- hold base time `2026-09-08T10:35:13+00:00`

The final plan states that v9r23 is the fresh D-141 successor to immutable v9r22. It preserves D-135/v9r21 only as historical predecessor provenance, records an explicit `v9r22_note` for the D-141 failure boundary, extends preserved-evidence and old-builder confinement through v9r22, and forbids D-141 semantic-row/label/gold/mapping/ledger reuse beyond the permitted fingerprint-only exclusion.

## Failed-D141 query-fingerprint-only carry

D-087 plus the D-123/D-124 precedent applies because v9r22 completed both Author pools before failing later at C. The two preserved candidate artifacts were consumed mechanically for hashing only; query plaintext was not used as successor semantic/template material.

Bound source artifacts:

- v9r22 `author1_candidates.jsonl`: 180 rows, SHA256 `91bbcb3faf3729658f7f3e4e7d89e880ac64d32a001df46c2a9211c9776b326d`
- v9r22 `author2_candidates.jsonl`: 180 rows, SHA256 `b22f5863be7edffa683f75877abc5dc9216e447590377e7118dc526a6d58a1be`

Final artifact:

- `input/failed_d141_query_fingerprints.json`: 24,839 bytes, SHA256 `8a78aeda8089ce8c1bb44cb36de964b3b7546b4ae9c007c119da3d50d17129a0`
- 360 rows / 360 unique normalized SHA256 query fingerprints
- artifact exactly matches independent NFC + strip + whitespace-collapse + casefold + SHA256 recomputation
- zero overlap against all previous twelve query-fingerprint sets
- final exclusion contract = exactly **13 query sets / 78 pairwise checks / overlap 0**
- no failed-generation gold exclusion added; canonical gold overlap remains dev-v1 / holdout / history only

`input/EXCLUSION_INPUTS.json` is 3,523 bytes, SHA256 `602565b7a881206a0d7a58c1ed3e2b13881f87a561bbf65dc1b842d359397a18`.

Both Author staging roots mechanically receive the D-141 fingerprint file together with the other twelve fingerprint-only inputs; the Author helper therefore checks the same thirteen-set query exclusion contract used by the selector and plan.

## D-141 repair A — fixed C packet delivery

The v9r22 failure path is removed from the C role surface. The old whole 180-row `c_packet_1` / `c_packet_2` resources are not staged or readable by C. No generic path, offset, range, or arbitrary pagination API was introduced.

C instead receives exactly twelve fixed C-only resources:

`c_packet_00.jsonl` through `c_packet_11.jsonl`, each exactly 30 rows, covering opaque C IDs in order:

- `00`: `v9r23c-001..030`
- `01`: `031..060`
- `02`: `061..090`
- `03`: `091..120`
- `04`: `121..150`
- `05`: `151..180`
- `06`: `181..210`
- `07`: `211..240`
- `08`: `241..270`
- `09`: `271..300`
- `10`: `301..330`
- `11`: `331..360`

Coverage is exactly 360 unique C IDs with the existing row schema and C ordering preserved. C remains the sole final semantic authority for all 360 and still writes six 60-row output chunks. `c_keymap` remains builder-private; A/B raw/keymap/candidate/Author data remain unavailable to C beyond the standing disagreement protocol.

Permanent staging/role/confinement tests prove the twelve-window exact set, ordered coverage, C-only reads, no whole-packet/helper/keymap extras, and fail-closed rejection of missing/extra prepared files.

## D-141 repair B — final-stop incomplete fail-close

Final `role_completion_gate.py` preserves transient-idle behavior but removes the pointless v9r22 5400-second wait after a proven non-recoverable final stop.

- `running` + incomplete => WAIT
- `idle` + incomplete without structurally proven final stop/no-later-trigger => WAIT
- later user/developer trigger after an earlier stop means that earlier stop is not final
- complete output still requires final stop + byte-stable quiescence + re-inspect
- `idle` + exact final assistant stop/no-later-trigger + incomplete/invalid required output => immediate `ContractInvalid`

The permanent matrix proves zero sleep for five final-stop invalid cases: missing chunk, wrong row count, malformed output, extra chunk, and duplicate IDs. Assistant prose is never completion authority; only structural exact-session evidence is used.

## Fresh runtime and plan/mechanics parity repairs

Web independent review found and repaired additional PRE-SMOKE blockers before any one-shot execution:

- Reviewer-A, Reviewer-B, and C runtime launch titles were corrected from stale v9r22 names to `v9r23-reviewerA`, `v9r23-reviewerB`, and `v9r23-adjudicatorC`.
- `failed_d141_query_fingerprints.json` was added to the real staging copy set for both Authors.
- current plan lineage was corrected from inherited D-135/v9r21 wording to D-141/v9r22, while keeping D-135 as historical evidence.
- `final_selector` query-overlap/no-recycle descriptions were aligned with the active thirteen-set mechanics through D-141; gold rules remain canonical-only.
- `generation_authors.contract` now truthfully states no helper script is staged, the session cwd is the staging root, and file/evidence access is through the five kind-bound role tools only.
- `isolation.staging` now truthfully states primary mechanical wrapper/tool-surface + kind-bound staging confinement + exact prepared sets, with structural transcript allowlist + zero-deny access log + descendant/session-cwd proof as secondary audit; no OS-sandbox claim.

A scan of current operative plan sections, excluding historical `supersedes` notes, finds zero obsolete-current hits for `search/check helper`, `transcript effective-path`, or `staged helper scripts`.

## Final hashes and binding

Final pre-smoke artifacts:

- `GENERATION_PLAN.json`: 69,469 bytes, SHA256 `5551e7c8049877d8f21bc51055af0470407c9607ac1f9a562c17b4fcf712996f`
- `input/EXCLUSION_INPUTS.json`: 3,523 bytes, SHA256 `602565b7a881206a0d7a58c1ed3e2b13881f87a561bbf65dc1b842d359397a18`
- `RUBRIC.json`: 3,334 bytes, SHA256 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- `input/failed_d141_query_fingerprints.json`: 24,839 bytes, SHA256 `8a78aeda8089ce8c1bb44cb36de964b3b7546b4ae9c007c119da3d50d17129a0`
- `freeze_plan_v9r23.py`: 97,441 bytes, SHA256 `a467ff8bbe8b680b60f2f5b4cc29887e33d3536e1967fceca80cde9c256d6457`
- `coord_wrapper_tpl/phasec_driver.py`: SHA256 `b87f4cf76373f02baa105ede0a3eb44917d39f040c6e4ac0b09e1e0c9e018d94`
- `role_completion_gate.py`: SHA256 `99110ea275685bc3efc6a7bf8eb412ce5396ceebb4e2b8afe9474ef7bb1225cc`
- `role_fs_helper.py`: SHA256 `6603268a20d80876d79e0f39320e850bea9d89f5eb57dcb9509472918e8076c1`

`GENERATION_PLAN.author_isolation.mechanics_shas` contains 60 entries. Independent final disk verification = **60/60 exact, missing 0, mismatch 0**.

## Independent final static/PRE-SMOKE validation

All final-byte checks returned exit 0:

- freeze binding / final plan parity: `FREEZE_BINDING_PASS` — **87 checks**
- strict timestamp + rerun/concurrency: `FREEZE_RERUN_REJECTION_PASS` — 66 checks
- thirteen query sets: 13 gates / 78 pairwise comparisons / overlap 0
- role completion gate: `GATE_TESTS_PASS`; five proven-final-stop invalid cases each sleep `0.0`
- staging exact set: `STAGING_EXACT_SET_PASS` — 41 checks
- role tools/helper confinement: `ROLE_TESTS_PASS` — 220 checks
- Phase-C confinement / compile/type gate: `CONFINEMENT_TESTS_PASS` — 216 checks
- writer preflight: `PREFLIGHT_PASS` — 36 checks
- D-123 slot/location: 6 positive / 5 negative cases
- launcher reachability: `REACHABILITY_PASS` — 87 checks
- lifecycle contract: `LIFECYCLE_CONTRACT_PASS` — 53 checks
- registry descendant scan: `REGISTRY_SCAN_PASS` — 37 checks
- exact bundled Paseo CLI: `PASEO_CLI_GATE_PASS` — 64 checks
- carry-exclusion regression: 13 sets with D-141 360 fingerprint-only carry
- mechanics pins: 60/60 exact

Successful freeze artifacts printed during freeze-binding/rerun regressions were created only in disposable fixtures. The real v9r23 builder was never frozen.

Final independent read-only reviewer verdict on exact plan SHA `5551e7c8049877d8f21bc51055af0470407c9607ac1f9a562c17b4fcf712996f`: **PASS; no remaining operative blocker.** The reviewer authorizes durable D-142 PRE-SMOKE PASS closure and only the next separately gated exactly-one Smoke A.

## Final zero-state

The real v9r23 builder contains 76 files and zero `__pycache__` directories.

Absent from the real builder/runtime:

- `PLAN_LOCK.json`
- `FROZEN_HASHES.json`
- `phasec_driver.run.lock`
- source truth / source-truth meta
- anchors / slots
- Author candidates / merged candidates
- raw A/B / C keymap / adjudicated pool
- selector/final evalset

Expected v9r23 Smoke-A, Smoke-B, Phase-C, and execute coordinator roots are absent. V9r23 generation OMP session directories are 0. Local Paseo registry has zero v9r23 generation identities excluding the single D-142 stage executor, and matching v9r23 generation processes are 0.

A transient read-only registry probe initially reported one apparent match because the PowerShell automatic `$Matches` variable was accidentally reused as an accumulator. A corrected probe using an ordinary array returned zero; no generation agent or one-shot execution existed.

## Process deviations and same-stage repairs

D-142 preserved these non-consuming process deviations for auditability:

1. The initial multiline implementation prompt and the first inline repair message were sent through Windows `paseo.cmd` in a form that delivered only the first paragraph. Session structure exposed the truncation before any v9r23 model-generation/Smoke/freeze/Phase-C boundary was consumed. The same executor was retained; full repair contracts were resent through `paseo send --prompt-file`. No replacement executor or generation agent was created.
2. Web did not accept the executor's early PRE-SMOKE reports blindly. Before any Smoke, the same executor repaired: the missing D-141 thirteenth set; the still-reachable whole C-packet surface; stale v9r22 Reviewer/C launch titles; missing D-141 Author staging input; stale D-135/v9r21 current-lineage text; partial selector failed-set descriptions; and obsolete author-helper/transcript-path confinement claims.
3. All of these changes occurred before Smoke A, real freeze, or any v9r23 generation role. They are ordinary same-stage PRE-SMOKE repairs, not one-shot retries.

## Gate boundary

**D-142 PRE-SMOKE WEB PASS.** V9r23 final bytes are eligible for the next separately authorized exactly-one Smoke A after a fresh duplicate/runtime/provenance prelaunch reconciliation.

D-142 itself authorizes no Smoke B, real freeze, Phase C, protected dev-v2, holdout, production evaluation, or canonical audit append. Any future one-shot failure is handled by the standing fail-closed/non-repair semantics for the stage consumed.