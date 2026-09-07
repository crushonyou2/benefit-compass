# Retrieval v3 D-131 — generation-v9r20 pre-freeze CONTRACT_INVALID_GENERATION

Date: 2026-09-08
Stage: real-freeze independent pre-gate / docs-only durable closure
Generation: `retrieval-v3-dev-generation-v9r20`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r20`
D-130 base commit: `3d53ac82a62a00297660515276977b0e7794ba6b`

## Verdict

**v9r20 = HARD HOLD / CONTRACT_INVALID_GENERATION / NON-RESUMABLE / NON-REPAIRABLE.**

D-129 and D-130 remain true: the exact corrected v9r20 final bytes consumed exactly one Smoke A and exactly one Smoke B, and both frozen auditors continue to PASS on the preserved evidence. The failure discovered here is later and independent: the frozen real-freeze mechanics do not enforce the authorized **exactly-once real freeze** lifecycle.

No v9r20 real freeze was executed. No `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, source truth, Phase C runtime, protected evaluation, holdout evaluation, production change, canonical audit append, branch, tag, or worktree was created in this gate.

Because both one-shot smokes are already consumed on the exact final bytes, repairing `freeze_plan_v9r20.py` now would be a same-generation post-smoke byte change. As in D-105/v9r14, the generation cannot be repaired in place; any successor must use a fresh generation/private builder and fresh one-shot smokes.

## Reconciled base

Immediately before the pre-freeze verdict:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `3d53ac82a62a00297660515276977b0e7794ba6b` (D-130)
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- canonical audit exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- main-tree protected `eval/retrieval-v3/dev/` and `eval/retrieval-v3/holdout/` plaintext paths absent
- OMP `18.1.13`; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`
- exact bundled Paseo CLI/daemon `0.7.2`, daemon running/reachable
- final plan SHA256 `4baf17f208db63a27948cf1b11ac88f87b052f0f8db7f0f5468a1267023be542`, 64,375 bytes
- exclusion manifest SHA256 `822f39b80831f580df5f3e1e82b9a22c93e047381a8512a53536e1e941daf28b`
- rubric SHA256 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- mechanics 58/58 exact, mismatch 0
- frozen real-freeze mechanic `freeze_plan_v9r20.py` SHA256 `ac1460d6229686901828458ac7a7274be98babfc46ca7b39f6adb853b5dc3336`
- `ABSENT_AT_FREEZE` violations 0; staging dirs 0; `author_chunks` 0
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock` absent
- builder `__pycache__` cleaned to 0 after read-only regression/auditor checks

## Preserved one-shot smoke evidence

Smoke A remains exact D-129 evidence:

- agent `073260d6-9987-4ae9-9e1d-15594ae25b44`, Parent null, exact cwd/model/xhigh/full, idle
- session exactly 10 lines, SHA256 `bebcc3da0155b01be4d31167c4b0f81a141b0449ea039ebf14035c0aba305b73`
- wrapper SHA256 `a79a70d05e7ac22b6335a9db51aeb54091fb7f3385c3735658b363883f1b5455`
- frozen auditor re-run in this gate: `SMOKE_PASS`, `phasec_probe=1`, descendants 0, fallback proven

Smoke B remains exact D-130 evidence:

- agent `ac7d9e2d-e17a-4e98-9b70-d63f41105ca7`, Parent null, exact cwd/model/xhigh/full, idle
- session exactly 21 lines, SHA256 `d10ab9f559fbc49e10b2ee0775b04fb72b680abdc339be4206f4d517942791dd`
- wrapper SHA256 `becfb02f5db7c6995470d3cc605ff22cf75e17b1dc3eaf2e8d39873ed61132b5`
- frozen auditor re-run in this gate: `LIFECYCLE_SMOKE_PASS`, `role_smoke_probe=1`, exact deny triple, six 59-byte/1-row writes, descendants 0, fallback proven

`test_freeze_binding_regression.py` also re-passed 66 checks against final bytes, proving the A/B argument binding path. That regression does not test successful-freeze rerun rejection and therefore does not cover the defect below.

## Hard blocker — real-freeze rerun prevention is absent

The authorized D-130 successor stage requires a **real-freeze pre-gate + exactly-once real freeze**. The frozen v9r20 freeze mechanics cannot enforce that lifecycle:

1. `ABSENT_AT_FREEZE` does not include `PLAN_LOCK.json` or `FROZEN_HASHES.json`.
2. There is no preexisting-freeze guard before the successful write path.
3. The production path unconditionally writes `PLAN_LOCK.json` with `write_bytes` at line 963 and `FROZEN_HASHES.json` with `write_bytes` at line 976.
4. The script docstring explicitly states: `Re-running with the same --frozen-at reproduces identical bytes.`
5. `test_freeze_binding_regression.py` contains no successful-freeze rerun-rejection contract.

Therefore a second or concurrent successful invocation can reach the same write path and replace the freeze artifacts instead of failing closed. Operational intent to call the command once is not a mechanical exactly-once/rerun-prevention guarantee.

This directly conflicts with the v9r20 frozen `post_freeze_rule`, which says never to mutate the v9r20 plan/rubric/lock after freeze, and with D-130's authorized exactly-once freeze boundary.

## Secondary provenance drift

The lock note that the current freeze script would write for Smoke A also contains stale descriptive text: it calls the smoke "neutral adversarial" and says the prompt requested forbidden accesses before a `phasec_probe` fallback. D-129 records the actual v9r20 Smoke A as a neutral deterministic prompt requiring exactly one `phasec_probe` and no other tool call, with forbidden tool calls 0.

Under the D-121 precedent, this wording drift is descriptive rather than a separate operative smoke failure because all actual audit-bound Smoke-A fields are independently revalidated. It nevertheless should be corrected in any fresh successor before its smokes; this gate does not patch v9r20.

## Why v9r20 cannot be repaired

D-130 permits the next stage only against the exact bytes that consumed the one-shot Smoke A/B proofs. `freeze_plan_v9r20.py` is itself one of the 58 SHA-pinned mechanics. Adding an exclusive-create/preexisting-lock guard or correcting its lock-note text would change those final bytes after both smokes were consumed.

That would be the same class of forbidden post-smoke repair recorded in D-105/v9r14: the mechanics defect is discovered after the one-shot smoke budget is exhausted and before a valid real freeze exists.

Therefore:

- no v9r20 real freeze
- no same-generation freeze-mechanics patch or bypass
- no additional v9r20 Smoke A or Smoke B
- no Phase C
- no source-truth snapshot
- no Author/Reviewer/C/selector execution
- no protected dev-v2 or holdout evaluation
- no production change or canonical audit append

## Successor requirement

A successor may proceed only as a **fresh generation/private builder** with fresh one-shot smokes. At minimum, before any smoke it must:

- add fail-closed real-freeze rerun prevention that rejects any preexisting freeze artifacts and is safe against concurrent invocation (exclusive/atomic creation rather than overwrite semantics);
- add permanent non-model regression proving a second successful-freeze attempt is rejected without mutating the first freeze artifacts;
- correct the stale Smoke-A lock-note description;
- preserve all v9r20 retrieval/evaluation semantics, rubric, quotas, exclusions, selector rules, and protected-data boundaries unless separately authorized.

The v9r20 builder and both smoke roots/sessions remain immutable failure evidence apart from exact builder-local test-cache cleanup already recorded.

## Stop

D-131 is a docs-only durable closure of the v9r20 pre-freeze hard gate. **Do not start a successor generation inside this closure action.**
