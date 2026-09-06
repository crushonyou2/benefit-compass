# Retrieval v3 D-105 — generation-v9r14 pre-freeze CONTRACT_INVALID_GENERATION

Date: 2026-09-07
Stage: pre-freeze independent gate / docs-only durable closure
Generation: `retrieval-v3-dev-generation-v9r14`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260906-v9r14`

## Verdict

**v9r14 = HARD HOLD / CONTRACT_INVALID_GENERATION / NON-RESUMABLE / NON-REPAIRABLE.**

D-104 remains true that the exact D-103 bytes consumed one Smoke A and one Smoke B and both frozen smoke auditors PASS. The failure discovered here is later and independent: the frozen real-freeze CLI cannot bind the required Smoke-B cwd because `freeze_plan_v9r14.py` references `args.lifesmoke_cwd` but never registers a `--lifesmoke-cwd` argparse option.

No real freeze body was executed. No `PLAN_LOCK.json`, `FROZEN_HASHES.json`, run lock, source truth, evalset, Phase C, protected evaluation, holdout evaluation, production change, audit append, branch, tag, or worktree was created.

Because both one-shot smokes are already consumed and D-104 requires the real freeze to bind those exact proofs to the exact D-103 bytes, this defect cannot be repaired in place. Any successor must use a fresh generation/private builder and fresh one-shot smokes.

## Reconciled base

Before the pre-freeze review:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD/local/upstream/direct remote `22189f1e01c8e5cdb3d15a5ff544ec8b182538b9` (D-104)
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from the standing base: 0 files
- audit exactly 4 events, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- canonical `eval/retrieval-v3/result`, `dev`, `holdout`, `dev-v2` absent
- OMP `18.1.5`; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`
- v9r14 final builder 65 source/support files; D-103 key hashes exact; no real freeze/runtime artifacts
- Smoke A exact session SHA256 `f6b0859ae06b2bfc6b11e75def452b0c7808064a9d33dbfa1862d68190019de0`
- Smoke B exact session SHA256 `4307a8d737cf84636db72c946d5d61607c86786fa883734cb361e6b2b52057c3`
- both smoke wrapper logs present; Smoke-B access log present

## Frozen-byte defect

Actual final `freeze_plan_v9r14.py` SHA256 remains D-103/D-104 exact:

`543020bd584604cba27fbe4acf0b7825060b2229b106bfaa18eb9e7691868144`

Its argparse registration is:

- `--builder`
- `--frozen-at`
- `--smoke-agent`
- `--smoke-session`
- `--smoke-wrapper-log`
- `--smoke-cwd`
- `--lifesmoke-agent`
- `--lifesmoke-session`
- `--lifesmoke-wrapper-log`

There is **no `--lifesmoke-cwd`** registration before `parse_args()`.

The same frozen script nevertheless requires that missing Namespace field:

- line 690: `... or not args.lifesmoke_cwd`
- line 762: passes `args.lifesmoke_cwd` into `audit_lifecycle_smoke.py`
- line 805: records `lifesmoke_cwd` into the lock proof

The Smoke-B cwd is therefore a required freeze-proof input with no legal frozen CLI path.

## Reproduction

Read-only/parser-level checks on the final frozen bytes proved the defect without entering the real freeze body:

1. `python freeze_plan_v9r14.py --help` omits `--lifesmoke-cwd`.
2. Supplying the required actual Smoke-B cwd explicitly:

   `--lifesmoke-cwd C:\Users\joji\bc-v3-v9r14-lifecyclesmoke`

   is rejected by argparse with rc 2: `unrecognized arguments: --lifesmoke-cwd ...`.
3. Omitting the option cannot solve the contract because later frozen code dereferences the absent `args.lifesmoke_cwd` attribute.

The rc2 parser reproduction terminated before `parse_args()` returned and before any builder write. Post-checks still showed `PLAN_LOCK.json`, `FROZEN_HASHES.json`, run lock, source truth/meta, and evalset absent.

## Why this is generation-invalid

D-104 authorized the next gate only as a real freeze that binds the **exact** D-103 builder bytes and the **exact** consumed Smoke A/B proofs. The missing Smoke-B cwd argument means that required binding cannot be produced by the frozen mechanics.

Changing `freeze_plan_v9r14.py` now would change post-smoke generation bytes after both one-shot smokes were consumed. That is a same-generation post-smoke repair and is forbidden. Monkeypatching/injecting an argparse Namespace attribute or otherwise bypassing the frozen CLI would also violate the frozen execution contract.

Therefore:

- no v9r14 real freeze
- no same-generation patch/retry
- no additional v9r14 Smoke A/B
- no Phase C
- no source-truth snapshot
- no Author/Reviewer/C/selector execution
- no protected dev/holdout evaluation

## Successor requirement

A successor may proceed only as a **fresh generation/private builder**. At minimum its frozen pre-smoke mechanics must repair the real-freeze CLI so Smoke-B cwd is explicitly registered and bound, and its non-model regression/dry-freeze contract must prove that the exact real-freeze invocation accepts and revalidates both Smoke A and Smoke B cwd/session/wrapper inputs before any one-shot smokes are consumed.

v9r14 builder and both smoke roots/sessions remain immutable failure evidence.

## Stop

D-105 is a docs-only durable closure of the v9r14 pre-freeze hard gate. Do not start a successor generation inside this closure action.
