# Retrieval v3 D-148 — generation-v9r23 Phase-C PRE-EXECUTION PASS

Date: 2026-09-09
Stage: post-freeze Phase-C/source-truth pre-execution gate
Generation: `retrieval-v3-dev-generation-v9r23`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r23`
D-147 real-freeze base commit: `f7c4698a062a615105dfb25a65936967642c85f1`

## Verdict

**D-148 / v9r23 Phase-C PRE-EXECUTION: PASS.** D-147 immutable freeze evidence remains exact, the current Phase-C/source-truth/execute zero-state is fresh, and the frozen v9r23 coordinator/driver path implements the standing D-122 one-shot execution contract plus the D-123 no-resume failure boundary. The D-141 C-packet-delivery and final-stop/deadline defects are visibly repaired in the frozen bytes.

D-148 itself executes **no Phase C**. It authorizes only the next separately-approved stage to launch exactly one frozen execute coordinator on these exact immutable bytes. No manual helper/driver invocation, duplicate execute coordinator, retry, run-lock removal, frozen-byte patch, same-generation repair, manual role launch, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append is authorized.

## Reconciled canonical state

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `f7c4698a062a615105dfb25a65936967642c85f1`
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- canonical `eval/retrieval-v3/audit/events.jsonl` = 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/dev-v2/`, and `eval/retrieval-v3/holdout/` absent

Immutable D-147 freeze evidence remains exact:

- `PLAN_LOCK.json`: 26,634 bytes, SHA256 `b8c1fa42e23c3ef085b30e54fd08a5e68d8895219328e4415764caf574468c3f`
- `FROZEN_HASHES.json`: 7,541 bytes, SHA256 `bda5f88c3d89d60ff79c38144fafa300139f41a55ff6182ad1231a44fb18aeb2`
- frozen entries: 77; current independent rehash = 77/77 exact, missing 0, mismatch 0
- frozen driver `verify_frozen_hashes()` returned `PHASEC_FROZEN_EXACT_PASS` on the actual post-freeze builder
- builder cache dirs 0 / `.pyc` 0 at final gate closure
- immutable v9r22 `phasec_driver.run.lock` remains present as prior failure evidence

No v9r23 Phase-C runtime has been consumed:

- `phasec_driver.run.lock` absent
- `source_truth.jsonl` and `source_truth_meta.json` absent
- anchors/slots/author outputs/candidate pool/raw A/B/agreement/C/adjudication/final evalset runtime artifacts absent
- `C:\Users\joji\bc-v3-v9r23-phaseC` absent
- intended execute root `C:\Users\joji\bc-v3-v9r23-coord-execute-20260909` absent
- intended execute cwd `C:\Users\joji\bc-v3-v9r23-coord-execute-20260909\cwd` absent
- corresponding exact OMP session directory absent
- complete local Paseo registry: 340 JSON records, parse errors 0; exact intended D-149 title matches 0, execute-cwd matches 0, Phase-C-cwd matches 0
- matching v9r23 execute/Phase-C/driver Python/OMP/Paseo processes 0

## Runtime readiness

- OMP `18.1.13`
- effective OMP default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`
- frozen coordinator/role model `opencode-go/muse-spark-1.3-contributor`, thinking `xhigh`, mode `full`
- bundled Paseo CLI/daemon `0.7.2`; fixed-CLI read-only inspect succeeded on preserved Smoke-B and D-147 executor agents
- fixed Python `C:\Users\joji\AppData\Local\Programs\Python\Python311\python.exe` = Python `3.11.9`
- repo `.env` exists
- `psycopg2` import PASS
- frozen `take_snapshot.load_dsn()` readiness returned true without printing/persisting the DSN and without opening a database connection or taking source truth in D-148

## Frozen Phase-C execution path

The published 77-pin set contains the exact current execution mechanics. The operative path is fail-closed and ordered:

1. execute coordinator exposes built-in `todo` plus exactly one modal custom tool, `phasec_execute`; every other tool call is blocked by the frozen extension interceptor;
2. `phasec_execute` takes an empty-object schema, ignores caller params, and invokes exactly one fixed Python 3.11.9 interpreter plus the frozen v9r23 driver path; nonzero driver exit fails closed;
3. frozen launcher pins the exact bundled Paseo CLI, `opencode-go/muse-spark-1.3-contributor`, `xhigh`, `full`, brand-new empty cwd, `BC_PHASEC_MODE=execute`, wrapper PATH, and `PYTHONUTF8=1`, then hard-verifies ParentAgentId null, exact cwd/model/fallback and wrapper provenance;
4. driver takes no argv/path input and calls `verify_frozen_hashes()` **before any runtime write**;
5. driver then creates `phasec_driver.run.lock` with `O_CREAT|O_EXCL`; any later or concurrent run fails closed;
6. only after the run lock does it require runtime artifacts absent and the neutral Phase-C root fresh;
7. `take_snapshot.py` takes one read-only `SELECT ... FROM policy ORDER BY source, source_id` snapshot with no vector/chunk/ranking query;
8. Author-1/2 launch as genuine top-level roles, require exact 6x30 outputs, final-stop/quiescence proof, wrapper/descendant/transcript/access audits, then merge + THIRTEEN pool validation;
9. Reviewer A/B prepared roots are exact-set staged and each judges all 360; raw+packet freeze, audits, keymap reconstruction, raw merge and agreement precede C;
10. C prepared root is exact-set staged with twelve fixed resources `c_packet_00.jsonl` through `c_packet_11.jsonl`, plus `RUBRIC.json`, `source_truth.jsonl`, `c_brief.md`, and empty `out/`; no whole 180-row packet/helper/keymap extra is staged;
11. C judges every 360 once, merge C runs only after C completion/audits;
12. exact selector runs LAST. Protected evaluation, holdout, production changes and canonical audit append are outside this driver.

## D-141 repair preservation

The consumed v9r22 D-141 failure had two proven mechanics defects: truncation-prone whole C-packet presentation and a 5400-second wait after a structurally proven final stop with incomplete C outputs. Both are repaired in the immutable v9r23 bytes.

### Fixed C delivery

- `build_packets_c.py` and the staging regression produce exactly 12 fixed C windows x 30 rows = 360.
- ordered coverage is `v9r23c-001..v9r23c-360` with no duplicate or residual ID.
- driver prepared-set names are exactly `c_packet_00..11`; the old `c_packet_1/c_packet_2` whole-resource surface is not used.
- C still writes six 60-row output chunks and remains the sole final semantic authority for all 360.

### Final-stop incomplete fail-close

Frozen `role_completion_gate.py` preserves transient-idle waiting but, at lines 271-283, proves that an idle role with exact final assistant `stop` and no later trigger plus structurally incomplete outputs raises `ContractInvalid` immediately rather than waiting the deadline.

Fresh permanent completion-gate regression PASSed with five final-stop-invalid shapes each sleeping `0.0`: missing chunk, wrong row count, malformed output, extra chunk, duplicate IDs.

## Fresh non-model validation

Applicable post-freeze checks on the immutable bytes passed:

- role completion gate: `GATE_TESTS_PASS`; D-141 fail-fast matrix 5 x `0.0s`
- staging exact-set / C 12-window contract: `STAGING_EXACT_SET_PASS` — 41 checks
- role tools/helper confinement: `ROLE_TESTS_PASS` — 220 checks
- writer-envelope preflight: `PREFLIGHT_PASS` — 36 checks
- launcher reachability: `REACHABILITY_PASS` — 87 checks
- exact bundled Paseo CLI: `PASEO_CLI_GATE_PASS` — 64 checks
- registry descendant scan: `REGISTRY_SCAN_PASS` — 37 checks
- thirteen query sets: 13 gates / 78 pairwise checks / overlap 0
- D-123 slot/location regression: 6 positive / 5 negative; slot mutation fail code `slot_location_mismatch`
- actual post-freeze frozen hash gate: `PHASEC_FROZEN_EXACT_PASS`

`test_phasec_confinement.py` itself returned rc1 on the current real builder at `freeze_repro_fail_closed`. This is **not an operative Phase-C blocker**: the frozen test declares itself a `permanent pre-smoke confinement test`, hardcodes `B` to the real v9r23 builder, and explicitly requires the real builder to have no `PLAN_LOCK.json`/`FROZEN_HASHES.json`. D-147 intentionally made that pre-freeze premise false. The observed failure is exactly `must be absent at freeze: PLAN_LOCK.json`; the suite's remaining execution-mechanics coverage is represented by the applicable focused regressions above plus the actual frozen 77/77 gate. No frozen test or source was patched to hide this stage mismatch.

The test run created one builder-local `__pycache__` / one `.pyc` byproduct. The same long-lived v9r23 implementation executor `3526a9e5-dabd-498d-9c67-3df795c5650a` removed only those resolved cache artifacts. Prime then reverified cache0/pyc0, unchanged lock/hash SHAs, `PHASEC_FROZEN_EXACT_PASS`, run-lock/source-truth/Phase-C zero-state and clean repo.

## Independent review and standing one-shot boundary

A separate read-only reviewer returned **FINAL PASS — blockers none** after independently verifying the D-147 lock/hash and 77/77 current rehash, runtime zero-state, environment readiness, frozen coordinator/driver ordering, D-141 C-window/fail-fast repairs, the post-freeze inapplicability of the pre-smoke-only confinement assertion, audit/production/protected boundaries, and the immutable v9r22 run lock.

D-122 remains the controlling positive execution precedent and D-123 the controlling consumed-failure precedent. After this PRE-EXECUTION PASS, the next separately authorized stage may create **exactly one** frozen execute coordinator only. Once `phasec_execute` / the driver consumes the boundary, any frozen driver or role failure closes v9r23 as `CONTRACT_INVALID_GENERATION`; preserve the run lock and all evidence, and do not retry, resume, delete the lock, patch frozen bytes, manually continue roles, or launch a second coordinator.

For the next stage, the intended execute coordinator cwd is:

`C:\Users\joji\bc-v3-v9r23-coord-execute-20260909\cwd`

Its neutral instruction must require `phasec_execute` exactly once with `{}`, no other tool call, no bypass and no retry under any outcome. The intended title is `D149 v9r23 Phase-C execute`; exact title/cwd/session/registry/process counts are zero at D-148 closure.

## Gate boundary

**D-148 Phase-C PRE-EXECUTION PASS.** Exactly one v9r23 Phase-C execute coordinator is eligible for the next separately authorized stage. D-148 itself performed no Phase-C execute, source-truth snapshot, Author/Reviewer/C launch, selector, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append.
