# Retrieval v3 D-140 — generation-v9r22 Phase-C PRE-EXECUTION PASS

Date: 2026-09-08
Stage: post-freeze Phase-C/source-truth pre-execution gate
Generation: `retrieval-v3-dev-generation-v9r22`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r22`
D-139 real-freeze base commit: `705660774ea8e165cf8d27c2e6f1d5371becac2d`

## Verdict

**D-140 / v9r22 Phase-C PRE-EXECUTION: PASS.** D-139 frozen bytes and the Smoke-A/Smoke-B bindings remain exact. The current Phase-C zero-state is fresh and the frozen coordinator/driver path still implements the standing D-122 one-shot execution contract and the D-123 no-resume failure boundary.

D-140 itself executes **no Phase C**. It authorizes only the next separately-approved stage to launch exactly one frozen execute coordinator on these exact bytes. No manual helper/driver path, duplicate execute coordinator, retry, run-lock removal, frozen-byte patch, same-generation repair, manual role launch, protected dev-v2 evaluation, or holdout evaluation is authorized.

## Reconciled canonical state

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `705660774ea8e165cf8d27c2e6f1d5371becac2d`
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- canonical `eval/retrieval-v3/audit/events.jsonl` = 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/dev-v2/`, `eval/retrieval-v3/holdout/` absent

Immutable freeze evidence remains exact:

- `PLAN_LOCK.json` SHA256 `0a1c5ac8e706829fd0de2189c3cc02f2d6ffc3c4159189e8bf1bd67ee1bed24c`
- `FROZEN_HASHES.json` SHA256 `e65156efbe71427f93887408e8a78ee164992cdd45d7a345dfbbea8863615ebb`
- exactly 75 pinned files; current Phase-C exact-set check = 75 actual / 75 pinned / missing0 / extra0
- independent SHA rehash = 75/75 exact, mismatch0
- plan `GENERATION_PLAN.json` SHA256 `58c862958dc2167b3a2ca7dab9ddb94af8f0c8a57fff307cd6cd89d354a821f3`
- builder cache/pyc = 0

No Phase-C runtime has been consumed:

- `phasec_driver.run.lock` absent
- `source_truth.jsonl` and `source_truth_meta.json` absent
- anchors/slots/author chunks/candidate pool/raw A/B/agreement/C/adjudication/evalset runtime artifacts absent
- `C:\Users\joji\bc-v3-v9r22-phaseC` absent
- intended execute-coordinator cwd `C:\Users\joji\bc-v3-v9r22-coord-execute-20260908\cwd` absent
- corresponding OMP session directory absent
- complete local Paseo registry: 328 parseable records, parse errors 0, matching v9r22 execute/Phase-C records 0
- matching Phase-C/driver/execute Python/OMP/Paseo processes 0

## Runtime readiness

- OMP `18.1.13`
- effective OMP default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`
- frozen coordinator/role model `opencode-go/muse-spark-1.3-contributor`, thinking `xhigh`, mode `full`
- bundled Paseo CLI/daemon `0.7.2`; status reports local daemon running and connected daemon reachable
- read-only fixed-CLI `inspect --json` calls on preserved Smoke-B and D-139 executor agents both returned successfully
- fixed Python `C:\Users\joji\AppData\Local\Programs\Python\Python311\python.exe` = Python `3.11.9`
- repo `.env` exists; `psycopg2` import PASS
- frozen `take_snapshot.load_dsn()` readiness check returned true without printing or persisting the DSN; no database connection or source-truth query was performed in D-140

## Frozen Phase-C execution path

The 75-pin set contains the exact current execution mechanics, including:

- coordinator driver `coord_wrapper_tpl/phasec_driver.py` SHA256 `d6d96d08fe45171990133a3ac91dc0a1126459ed2d4096d414b026c9c8a770c7`
- coordinator extension `coord_wrapper_tpl/phasec_coordinator_ext.ts` SHA256 `3871b68603e510f6b06584f1fa20a6b5ef95d06f4697787c72d6cb1c3999f4e6`
- coordinator wrapper `coord_wrapper_tpl/coord_omp_wrapper.py` SHA256 `2abc5b716efe5c0c168b73bda5b16de8cb60f6aada358d053c8ff755855a1dad`
- coordinator launcher `launch_phasec_coordinator.py` SHA256 `aef8bf7095bfa39c6e214f6a832ae221bda0202288b3273ff6fdd703d2fb5469`
- role launcher `launch_top_level_paseo.py` SHA256 `fbf82f3ba7d5f4c3ee80a7112931e84f6e032ff349a2b144152a150e2edeab18`
- read-only source snapshot helper `take_snapshot.py` SHA256 `fe4a6819629fceb8f14575f9e89eb96cca90185a980ec9c71b0241e13f4a175a`
- lifecycle completion gate `role_completion_gate.py` SHA256 `a4e25a14b0710b3fcd6ee8d0c843ff37b8ff61f6172554dfe7bc15df7c9baf5b`
- role access auditor `audit_role_access.py` SHA256 `a9460ec837f5cc43c58bd5770187d8bf92aa867387bb39883af3ea7b2a52cc1c`
- final selector `run_selector.py` SHA256 `ba116f4faf6a29236e72e799cec8e7d0a7425fed389542ec4bef83d2c7158393`

The operative path is fail-closed and remains in the standing order:

1. execute coordinator exposes only built-in `todo` plus frozen `phasec_execute`; every other tool is blocked;
2. `phasec_execute` has an empty-object schema and one fixed `pi.exec` target: the fixed Python 3.11.9 interpreter plus the frozen v9r22 driver path;
3. driver takes no argv/path input and verifies the complete frozen file set before any runtime write;
4. driver then exclusively creates `phasec_driver.run.lock` with `O_CREAT|O_EXCL`; any later or concurrent run fails closed;
5. only after the run lock does it require every runtime artifact absent and the neutral Phase-C root fresh;
6. `take_snapshot.py` performs one read-only `SELECT ... FROM policy ORDER BY source, source_id` with `conn.set_session(readonly=True, autocommit=True)` and keeps output only in the private v9r22 builder;
7. Author-1/2 launch as genuine top-level roles through the frozen role wrapper, with exact 6x30 structural completion, wrapper/access/descendant/transcript audits before collect/merge;
8. merged 360-row pool is mechanically validated before Reviewer A/B;
9. Reviewer A/B prepared roots are exactly `packet.jsonl`, `RUBRIC.json`, `source_truth.jsonl`, `reviewer_brief.md` plus empty `out/`; no helper script is staged;
10. raw A/B freeze + audits + keymap reconstruction + agreement precede C;
11. C prepared root is exactly `c_packet_1.jsonl`, `c_packet_2.jsonl`, `RUBRIC.json`, `source_truth.jsonl`, `c_brief.md` plus empty `out/`, and C sees every 360 exactly once;
12. selector runs LAST. No protected import/evaluation or production/audit append is part of this driver.

## D-123 mechanical repair preservation

The v9r18 D-123 failure boundary remains directly addressed in the frozen v9r22 bytes:

- `validate_pool.py` binds each returned row's `intended_stratum` and `intended_location` to the immutable slot metadata and emits `slot_location_mismatch` on mutation;
- the author-facing location contract and validator share the same closed vocabulary, explicitly including `천안` and `아산`;
- particle-attached forms are handled by the frozen parser rather than treating those real locations as absent.

No semantic/rubric/quota relaxation is involved; these are the already-frozen successor mechanics.

## Standing one-shot boundary

D-122 remains the controlling execution precedent: exactly one frozen execute coordinator may be launched only after this PRE-EXECUTION PASS. D-123 remains the controlling failure precedent: once `phasec_execute`/the driver consumes the run boundary, any frozen driver or role failure closes v9r22 as `CONTRACT_INVALID_GENERATION`; preserve the run lock and all evidence and do not retry, resume, patch, manually continue, or launch a second coordinator.

For the next stage, the intended neutral execute coordinator cwd is:

`C:\Users\joji\bc-v3-v9r22-coord-execute-20260908\cwd`

Its instruction must require `phasec_execute` exactly once with `{}`, no other tool, no bypass, and no retry on any failure. This restates the standing D-122 procedure; it is not an additional release criterion.

D-139's append-only correction for the descriptive `LIFECYCLE_SMOKE_DONE` lock note remains controlling; all audit-bound Smoke-B fields are unchanged and exact.

## Gate boundary

**D-140 Phase-C PRE-EXECUTION PASS.** Exactly one Phase-C execute coordinator is eligible for the next separately authorized stage. D-140 itself performed no Phase-C execute, source-truth snapshot, Author/Reviewer/C launch, selector, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append.
