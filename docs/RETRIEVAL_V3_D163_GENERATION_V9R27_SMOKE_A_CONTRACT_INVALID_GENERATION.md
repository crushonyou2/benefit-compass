# Retrieval v3 D-163 - generation-v9r27 Smoke A CONTRACT_INVALID_GENERATION

Date: 2026-09-10 (KST)

## Verdict

**D-163 / v9r27 Smoke A = CONTRACT_INVALID_GENERATION / HARD HOLD / NON-RESUMABLE.**

The single authorized Smoke-A executor turn was consumed by one shell tool use and failed before the frozen Windows runner could start. The same v9r27 Smoke A MUST NOT be retried, corrected, wrapped, re-issued, or resumed.

## Pre-gate evidence

Immediately before the authorized turn, Web reconciled the current canonical state read-only:

- branch `codex/retrieval-v3-user-search-quality`;
- local HEAD = upstream = direct origin = `6ffa2d5d2010460c4387e7ff6a17dc263d69d57f`;
- working tree clean; `git diff --check` PASS;
- `eval/retrieval-v3/audit/events.jsonl` = 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`;
- protected `eval/retrieval-v3/dev`, `eval/retrieval-v3/dev-v2`, `eval/retrieval-v3/holdout` absent;
- `ml-service` diff empty;
- all v9r27 runtime roots absent; v9r26 failed cwd still exists with 0 items;
- v9r27 `GENERATION_PLAN.json` 82447 bytes SHA256 `f0caf41ea6c846f5176b8e641be08c638e62ac97c67ff221e5b35b88d0ab1a0e`;
- `run_smoke_a_once.py` 2259 bytes SHA256 `23c1f86de4ead0bdd9ee687860100b6200e1694a778ba6f8c4fbf67b4e0516a8`;
- frozen mechanics 69/69 exact; builder cache0/pyc0;
- fixed real OMP `C:\Users\joji\AppData\Local\omp\omp.exe` reports `omp/18.1.13`;
- fixed bundled Paseo CLI reports `0.7.2`;
- no project-local OMP overlay and no relevant ambient OMP/Paseo/model override was found;
- frozen launcher explicitly binds `omp/opencode-go/muse-spark-1.3-contributor`, thinking `xhigh`, and the frozen wrapper path/tool surface.

Therefore there was no pre-existing generation/provenance blocker before the one-shot launch attempt.

## Authorized one-shot outcome

The sole D-163 executor was instructed to issue exactly one shell call containing only the frozen target command:

`python -B C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260910-v9r27\run_smoke_a_once.py`

It issued one shell tool call. That execution environment interpreted the Windows absolute path as a POSIX-style path and returned:

- return code: `2`;
- stdout: empty;
- stderr: `python: can't open file '//C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260910-v9r27\run_smoke_a_once.py': [Errno 2] No such file or directory`.

The executor then reported that raw outcome and entered sleeping/finished state. No second shell call was issued and no correction/retry was sent.

This is an executor transport/environment failure, not evidence of a defect in `run_smoke_a_once.py`: the frozen runner was never opened by Python and therefore never created the Smoke-A root, imported the launcher, or launched Paseo/OMP coordinator work.

## One-shot terminality / disposition

The standing v9r26+ rule is fail-closed: after **any tool use** in an authorized one-shot turn, same-generation correction/retry is forbidden regardless of whether the target process actually started. Canonical raw-OMP terminality evidence for this worker turn was not available as a v9r27 Smoke runtime artifact; uncertainty is itself fail-closed and cannot create correction eligibility.

Accordingly:

- the authorized D-163 one-shot is consumed for disposition purposes;
- no path-quoting repair, shell change, direct Windows retry, second worker, or second Smoke A is permitted under v9r27;
- no Smoke-A coordinator exists and no Smoke-A session/auditor PASS can be claimed;
- v9r27 is closed as `CONTRACT_INVALID_GENERATION / HARD HOLD / NON-RESUMABLE`.

## Post-failure preservation check

After the failed executor turn, Web rechecked current local state read-only:

- repo remained at `6ffa2d5d2010460c4387e7ff6a17dc263d69d57f`, local = upstream = direct origin, clean, diff-check PASS;
- audit remained 4 rows with SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`;
- protected dev/dev-v2/holdout remained absent;
- `ml-service` diff remained empty;
- `C:\Users\joji\bc-v3-v9r27-coord-smoke-20260910` remained absent;
- all other v9r27 runtime roots remained absent;
- v9r26 failure cwd remained present and empty.

No builder bytes, runtime evidence, protected data, canonical audit, production state, or predecessor evidence were mutated by the failed Smoke-A attempt.

## STOP boundary

Do not retry or repair v9r27 Smoke A. Do not run Smoke B, real freeze, source truth, Phase C, semantic generation, protected dev-v2, holdout, production, or canonical audit append. A future continuation requires a separately authorized fresh-successor generation/stage; this D-163 closure starts none.
