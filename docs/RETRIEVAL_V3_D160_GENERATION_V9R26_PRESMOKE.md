# Retrieval v3 D-160 — generation-v9r26 PRE-SMOKE WEB PASS

Date: 2026-09-09
Stage: fresh successor static/PRE-SMOKE construction + same-stage Web-found repair loops + independent Web FINAL PASS (static only)
Generation: `retrieval-v3-dev-generation-v9r26`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260909-v9r26`
D-159 closure base commit: `e8e20c051f5e5a82cc7055393184a221f1131af6` (2026-09-09T13:22:19+00:00 / local 2026-09-09T22:22:19+09:00)

## Verdict

**D-160 / v9r26 PRE-SMOKE: WEB PASS for static/PRE-SMOKE only. NOT Smoke-A authorization.**

V9r26 is a fresh D-160 successor to immutable D-159/v9r25. It carries retrieval/evaluation semantics, rubric, counts/reserve/location quotas, A/B-all-360, C-every-360, agreement and exact selector unchanged with exactly the FIFTEEN failed-fingerprint exclusion sets (no sixteenth; v9r25 produced zero Phase-C Author/query rows). The narrow mechanical delta is: (a) permanent frozen one-shot raw-OMP executor-turn terminality/consumption mechanic (`audit_one_shot_turn.py`) reasoning from raw OMP session JSONL with canonical `stopReason==stop` terminality, any-toolUse consumption, narrow correction eligibility, and a permanent non-model regression suite (`test_one_shot_turn_terminality.py` 24/24); (b) current-generation identity repins v9r25->v9r26 with old-builder deny now covering v9r25 families; (c) explicit v9r26+ supersession of the older permissive transport-correction reading (after ANY tool use in a one-shot turn, no same-executor correction; D-153 remains historical). O_EXCL freeze mechanics are carried unchanged and were not the D-159 defect.

No v9r26 Smoke A/B, real freeze, source-truth snapshot, Phase C, Author/Reviewer/C generation role, selector, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append occurred in D-160.

STOP before Smoke A. A future fresh explicit user `진행해` is required for a separate Smoke-A prelaunch/execution stage.

## Reconciled base and environment

Immediately before durable D-160 closure:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `e8e20c051f5e5a82cc7055393184a221f1131af6`
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- canonical `eval/retrieval-v3/audit/events.jsonl` 4 events / 2656B / SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/dev-v2/`, `eval/retrieval-v3/holdout/` absent
- OMP `18.1.13` verified; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`, no project override
- bundled Paseo `0.7.2` per standing evidence (exact CLI pinned in builder)

## D-159 reconciliation (immutable predecessor)

D-159 closes v9r25 permanently as `CONTRACT_INVALID_GENERATION / HARD HOLD / NON-RESUMABLE`. The first one-shot real freeze succeeded and published coherent O_EXCL artifacts; a Web correction based on an early/partial Paseo idle/log snapshot caused a second actual freeze process which correctly failed closed. Key v9r25 evidence hashes reverified unchanged hash-only in this stage (no plaintext/semantic/gold reuse, no v9r25 touch):

- plan 76168B `c017d6578bf4a81c73c7960fd62d8b11c25d899e0330a293314d2a219ec9383c`
- rubric 3334B `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- exclusion 4766B `d917de37e2c0b0cd761f9ff72d81906df31546cab6e4af15a5c89f36dd91b857`
- freeze_plan 111545B `a5d7781fe1e4e84ed3b5001443dd7462d6df1f0ae85b969233af32920e71ba65`
- PLAN_LOCK 28102B `8da1860e492be673ca69cc327e0378d3fabe5069e4b95541db6a90c3acf7a652`
- FROZEN_HASHES 8296B `075bc3d7820a22693ae3740d29bd743dc8317260213ddbc1694977aa53bd4ed5`

No v9r25 Phase-C Author/query rows exist, hence no sixteenth exclusion set. Terminal v9r25 failure stays immutable/non-resumable/non-repairable.

## Final v9r26 identity and artifacts (static-verified)

- plan version `retrieval-v3-dev-generation-v9r26`, seed `benefit-compass-retrieval-v3-dev-v2-generation-v9r26-2026-09-09`
- candidate IDs `v3g9r26-001..360`, C opaque IDs `v9r26c-001..360`
- hold base D-159 `e8e20c051f5e5a82cc7055393184a221f1131af6`, time `2026-09-09T13:22:19+00:00` / local `2026-09-09T22:22:19+09:00`
- `GENERATION_PLAN.json` 79260 bytes, SHA256 `b762c772d212a9c558cd74e4124c26ea05ea7014e4e07095cea4256a19b692f4`
- `RUBRIC.json` 3334 bytes, SHA256 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- `input/EXCLUSION_INPUTS.json` 4766 bytes, SHA256 `10aea62bd65c1348061ae9941df9111b1481ede34fa1a8657fe46eb3e5146e22`
- `freeze_plan_v9r26.py` 115794 bytes, SHA256 `dd6696df2a885f389ca3c70ed21bd7c85ef1af2e82f2e95bc9ed60bae1eb597e`
- `carry_exclusions_v9r26.py` 9529 bytes, SHA256 `acc723f1c9780023aa5fc7e958b24e02cf6849601f5d68433cb50f5f62b3d879`
- `audit_one_shot_turn.py` 16743 bytes, SHA256 `3d2cc4fd96d20ecbd75244998d74bc48f29acafd80830fdbccce7f108883cdad`
- `test_one_shot_turn_terminality.py` 14942 bytes, SHA256 `aeb76700517aa8b037e5d7ccd524080fc9ef057608231ac161908f34737f3650`
- `GENERATION_PLAN.author_isolation.mechanics_shas` 67/67 exact disk bytes/SHA, missing 0, mismatch 0
- exact query exclusion sets 15 (prior 14 inputs byte-identical to v9r25; D155 still 360 unique); pairwise comparisons 105; overlap 0; no D159/v9r25 set; gold exclusions stay dev-v1/holdout/history only
- old-token provenance deny lists include v9r25 in every family (v9r25, v3g9r25, v9r25c, 20260909-v9r25, bc-v9r25, bc-v3-v9r25, bc-v3-dev-v2-builder-20260909-v9r25)

## D-159 repair contract (frozen)

- Raw OMP session JSONL only; unique opaque authorized-turn token; actual envelope `{type:message,message:{...}}` unwrapped so role/token/`stopReason`/tool evidence comes from the nested payload; outer metadata never counts.
- Terminal only on a later actual assistant payload with `message.stopReason == "stop"`; Paseo idle/finished, partial logs, and artifact absence are non-evidence.
- Partial/malformed/unreadable/duplicate-token/later-user-before-terminal => `INCOMPLETE_NO_SEND` (rc2).
- Terminal + ANY structured tool use => `CONSUMED_NO_RETRY` (rc1) regardless of rc/result/helper failure/artifact presence/process inference.
- Terminal zero-tool + all supplied artifacts absent is the only `CORRECTION_ELIGIBLE` case (rc0); terminal zero-tool + any artifact present is consumed.
- Text mentions are never tool; the auditor never sends.
- One-shot executor contract is exactly one tool call containing only the target process; post-hash/helpers are Web read-only work outside the turn, never bundled.
- v9r26+ supersedes the permissive transport-correction reading after any tool use; historical D-153 remains historical.

## Sole implementation executor

Approved private-builder implementation and all same-stage repairs were performed end-to-end by the sole D-160 executor `66311bc3-753e-436b-8d9a-68561a2bb7bf`, Parent null, `omp/opencode-go/muse-spark-1.3-contributor` xhigh/full, repo cwd. No second implementation executor or semantic generation role was created or delegated. Raw OMP session `C:\Users\joji\.omp\agent\sessions\-Documents-취준자료-project-repos-benefit-compass\2026-09-09T14-00-01-803Z_01a08677-ee0b-7474-8961-83c0595f3746.jsonl`: after final cache-hygiene turn 553 physical lines, SHA256 `16ca53028434920dbe3a87c6c6ff1581f991222ab4012e6eb7ef7656dd735663`; latest user line 534; assistant tool-use records followed; canonical terminal assistant `stopReason=stop` line 553; no later user.

## Repair history (same-stage, fail-closed)

Initial implementation added the one-shot mechanic/regression, but Web's independent actual-schema probe found a real blocker: flattened synthetic JSONL passed while the actual OMP envelope returned token-not-found/`INCOMPLETE`. The same executor repaired actual-envelope parity and expanded the regression to 24/24 (15 flattened + 9 actual-envelope incl. D-159 mirror, metadata-ignored, malformed envelope, nested-stop-governs). Web replayed a D-159-shaped actual-envelope turn and independently obtained terminal `CONSUMED_NO_RETRY` with `tool_use_count` 2. This was a genuine same-stage blocker and was repaired before any smoke/model one-shot was consumed.

Second Web review found stale current provenance wording in the `freeze_plan` header (v9r24/D-155-D-156/D-149-current phrasing). The same executor repaired it to D-160 successor of immutable v9r25 after D-159 `e8e20c…`; final current plan/header/hold constants are internally aligned while historical v9r24/D-149 references remain only lineage/history.

Final battery on final bytes (disposable fixtures only for freeze): compile PASS; D149_CARRY_PASS; D150 retryable 7; D156 reviewer retryable 9; FIFTEEN 15 sets / 105 pairs / 0 overlap; FREEZE_BINDING_PASS 88; FREEZE_RERUN_REJECTION_PASS 66 including two-process race and timestamp rejection; REACHABILITY 87; LIFECYCLE 53; one-shot 24/24; PASEO_CLI_GATE 64; CONFINEMENT 251; REGISTRY_SCAN 37; GATE_TESTS_PASS; ROLE_TESTS 250; PREFLIGHT 36; slot/location 6 positive / 5 negative; STAGING_EXACT_SET 41. All rc0 with no Smoke A/B, real freeze, source snapshot, semantic roles, Phase C, selector, protected eval, audit append, or production. Mentioned transparently: the executor saw one transient `+1s` strict-timing flake during a loaded full-loop rerun, but the isolated rerun passed; Web independently reran the final gate-changing battery and `FREEZE_RERUN_REJECTION_PASS` 66 was green with no flake, so no operative blocker remained.

Web independent final-byte rerun on final source before hygiene PASS: one-shot 24/24; binding 88; rerun 66; FIFTEEN 105/0; CLI 64; confinement 251; registry 37; staging 41, all rc0. The exact actual-envelope probe classified consumed/no-retry. Web independently verified mechanics 67/67 and key hashes.

Web's Python independent regressions recreated exactly 2 v9r26-local `__pycache__` dirs / 49 pyc. The same D-160 executor removed ONLY those exact v9r26 cache byproducts, ran no Python builder tests afterward, rehashed all seven key files unchanged, and verified final cache0/pyc0. This is review-test hygiene, not a source/mechanics defect.

Final v9r26 zero-state after cleanup: cache dirs 0 / pyc 0; PLAN_LOCK / FROZEN_HASHES / `phasec_driver.run.lock` / source_truth (+meta) / anchors / slots / authors / `candidates_merged` absent. No Smoke-A root/model smoke, real freeze, source snapshot, Phase C, semantic Author/Reviewer/C, selector, protected evaluation, holdout, production, or audit append occurred.

STOP. No Smoke A/B, real freeze, source truth, Phase C, semantic generation, protected eval, holdout, audit append, or production change in D-160.

## D-160 WEB FINAL PASS

Independent Web FINAL VERDICT is D-160 / v9r26 PRE-SMOKE WEB PASS on the exact final bytes above. **WEB PASS covers static/PRE-SMOKE only. NOT Smoke-A authorization. STOP before Smoke A.**
