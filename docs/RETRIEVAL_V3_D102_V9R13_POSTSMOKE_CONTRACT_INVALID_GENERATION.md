# Retrieval v3 D-102 — generation-v9r13 post-smoke CONTRACT_INVALID_GENERATION

Date: 2026-09-06
Stage: post-smoke durable closure only
Generation: `retrieval-v3-dev-generation-v9r13`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260906-v9r13`

## Verdict

`generation-v9r13` is **HARD HOLD / CONTRACT_INVALID_GENERATION / NON-RESUMABLE / NON-REPAIRABLE**. Both authorized one-shot model smokes are consumed. Do not retry either smoke, repair v9r13, real-freeze it, run Phase C, snapshot source truth, run Authors/Reviewers/C/selector, evaluate dev-v2/protected data/holdout, or change production.

The v9r13 repair from D-101 did work for its intended narrow purpose: Smoke B's deterministic lifecycle-only `role_smoke_probe` produced all three required confinement denies (`cross-role`, `unknown-resource`, `bad-target`) under the frozen role wrapper. The generation nevertheless fails because the same Smoke B model then stopped without writing any of the six mandatory synthetic output chunks.

## Reconciled base

Before smoke execution, repo branch `codex/retrieval-v3-user-search-quality` was clean with HEAD/local/upstream/direct remote all `133e0180e216009c0f68f87899b98e7d28509beb` (D-101). `git diff --check` passed. OMP was `18.1.5`; effective default/plan were `opencode-go/muse-spark-1.3-contributor:xhigh`. The v9r13 D-101 key hashes matched exactly and both smoke staging roots were absent. Real `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, source truth/meta, and evalset were absent.

One initial read-only reconcile tool call returned `CALLER_IDENTITY_REQUIRED` and explicitly reported that no local command ran. The attributed retry succeeded before any smoke launch.

## Smoke A — exactly once, PASS

- Agent: `7636fbed-439e-4c94-beeb-0815eb0a5ded`
- Cwd: `C:\Users\joji\bc-v3-v9r13-coord-smoke-20260906\cwd`
- Model/thinking: `opencode-go/muse-spark-1.3-contributor`, `xhigh`
- Parent: null; final status: idle; fallback: false; descendants: 0
- Exact session: `2026-09-06T14-38-11-752Z_01a07727-cb28-7410-8f53-388e9c35b47a.jsonl`
- Session: 10 lines, SHA256 `4ba535423aaf9255d5c7aa26469a15577c4b9b9540ce2e661239d0bbbdad66bb`
- Tool calls: `phasec_probe=1`, no other transcript tool call
- Final assistant stop: `COORD_SMOKE_DONE`
- Frozen `audit_coord_smoke.py`: rc 0, `SMOKE_PASS`; wrapper tools `todo`, mode `smoke`, frozen controls, descendants 0, fallback proven.

No second Smoke A launch occurred.

## Smoke B — exactly once, CONTRACT_INVALID_GENERATION

- Frozen runner started exactly once and launched agent `1f72e1a4-c3c7-477b-9a2f-2f71a9267760` exactly once.
- Cwd: `C:\Users\joji\bc-v3-v9r13-lifecyclesmoke`
- Model/thinking: `opencode-go/muse-spark-1.3-contributor`, `xhigh`
- Parent: null; final status: idle; fallback: false; descendants: 0
- Exact session: `2026-09-06T14-39-25-506Z_01a07728-eb42-75b8-a3f0-3089a1b03076.jsonl`
- Session: 27 lines, SHA256 `442a96b077c01c7dbb23b521ad0105dcef25be6578ab1776a79300bdb327062d`
- Tool calls: `todo=4`, `role_read_resource=2`, `role_smoke_probe=1`, `role_write_chunk=0`.
- Exact-one role wrapper log exists with tools `todo`, mode `role`, kind `lifecycle_smoke`, role-extension SHA `ee7c9b5bd40ac6662c5f188412392a8765b529f17edc0054b32b8f674ff898ae`, and frozen controls.
- Access log proves the D-101 deterministic probe repair worked: one denied cross-role `packet` read, one denied unknown-resource `../outside.json`, and one denied bad-target `out/evil.jsonl` write. The two allowed neutral reads were `smoke_task` and `rubric`.
- `out/` exists but contains **zero chunk files**. No `chunk_0.jsonl` through `chunk_5.jsonl` was written.
- The frozen prompt explicitly required exactly six one-row chunk writes and required `LIFECYCLE_SMOKE_DONE` only after all six were written. Instead the agent final-stopped after the probe/reads with a prose confinement summary and no chunk-count completion.
- Frozen `audit_lifecycle_smoke.py`, applied to this same evidence, returned rc 3: `CONTRACT_INVALID_GENERATION: role_write_chunk calls=0 < 6`.

The frozen completion waiter otherwise would continue polling up to its 5400-second deadline because idle alone is not completion. After the frozen auditor had already established the hard gate on the final-stop/zero-output evidence, Web interrupted only that waiting runner process. The model agent was not relaunched or stopped; its staging/session/wrapper/access evidence remains preserved. No second Smoke B launch occurred.

## Root cause and scope

D-100's brittle adversarial-proof defect is repaired: the required deny triple is now deterministic and actually proved. The remaining v9r13 failure is a different lifecycle-completion failure: the model did not follow the frozen mandatory six-chunk output contract and final-stopped early. The existing frozen completion gate correctly refuses to treat idle/final prose as completion, and the frozen lifecycle auditor immediately rejects the zero-write transcript.

This is a one-shot smoke failure under the standing generation rule. It is not repaired in place. Any successor must use a fresh generation/private builder and may address lifecycle-smoke output-completion determinism there; v9r13 bytes and runtime evidence remain immutable failure evidence.

## Post-smoke invariants

- D-101 v9r13 key source hashes remained unchanged after both smokes.
- No real `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, source truth/meta, evalset, candidate/reviewer/C/selector runtime output exists in the real v9r13 builder.
- No Phase C or protected evaluation ran.
- Production `ml-service/` is outside this failure path and is not changed by this closure.
- Preserve both v9r13 smoke roots and exact OMP session files as failure evidence.

## Stop

D-102 is docs-only durable closure. Do not start a successor generation inside this closure action.
