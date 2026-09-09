# Retrieval v3 D-165 - generation-v9r28 Smoke A CONTRACT_INVALID_GENERATION

Date: 2026-09-10 (KST)

## Verdict

**D-165 / v9r28 Smoke A = CONTRACT_INVALID_GENERATION / HARD HOLD / NON-RESUMABLE.**

The single authorized Smoke-A executor attempt was consumed by one process/tool use and failed before Python could open the frozen runner. The same v9r28 Smoke A MUST NOT be retried, corrected, wrapped, re-issued, or resumed.

## Prelaunch gate

Immediately before the authorized one-shot attempt, Web reconciled current canonical state read-only:

- branch `codex/retrieval-v3-user-search-quality`;
- local HEAD = upstream = direct origin = `34a2b3fc567870c45569c62dd161de16df0f4297`;
- working tree clean; `git diff --check` PASS;
- `eval/retrieval-v3/audit/events.jsonl` = 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`;
- protected `eval/retrieval-v3/dev`, `eval/retrieval-v3/dev-v2`, `eval/retrieval-v3/holdout` absent;
- `ml-service/` diff from the standing D-163 base empty;
- immutable v9r27 predecessor key files reverified 8/8 exact;
- all eight final D-164 v9r28 key files reverified exact against the recorded hashes;
- frozen `GENERATION_PLAN.author_isolation.mechanics_shas` = 69/69 exact, missing 0, mismatch 0;
- all v9r28 runtime roots absent; builder runtime/freeze/source artifacts absent; cache0/pyc0;
- fixed real OMP exists and reports `omp/18.1.13`;
- fixed bundled Paseo CLI exists and reports `0.7.2`;
- actual global OMP `default` and `plan` roles are `opencode-go/muse-spark-1.3-contributor:xhigh`, matching the frozen launcher binding; no project-local `.omp` overlay exists and relevant ambient `PASEO_CLI` / `OMP_MODEL` / `OMP_PROVIDER` overrides were empty.

Therefore no pre-existing repo, byte, protected-data, runtime, or model/provenance blocker existed before the one-shot launch attempt.

## Authorized one-shot outcome

The sole D-165 executor was instructed to perform exactly one process/tool execution containing only the frozen D-164 target command:

`python -B C:/Users/joji/Documents/programming/bc-v3-dev-v2-builder-20260910-v9r28/run_smoke_a_once.py`

The executor reported one attempted execution with:

- return code: `2`;
- stdout: empty;
- stderr: `python: can't open file '//C:/Users/joji/Documents/programming/bc-v3-dev-v2-builder-20260910-v9r28/run_smoke_a_once.py': [Errno 2] No such file or directory`.

The executor transport/environment therefore prefixed the already-forward-slash Windows drive path with `//` before Python path resolution. Python never opened `run_smoke_a_once.py`.

No correction, alternate shell/path form, second process call, retry, helper, cleanup, or second executor instruction was issued after that consumed attempt.

This is an executor transport/environment failure, not evidence of a defect inside `run_smoke_a_once.py`: because Python never opened the runner, the runner never created the v9r28 Smoke root/cwd, imported `launch_phasec_coordinator`, launched Paseo/OMP coordinator work, or invoked `phasec_probe`.

The D-164 harmless non-runtime `C:/` transport probe remains historical evidence of that probe only. D-165 proves it was not sufficient to guarantee the exact frozen one-shot target would survive the actual D-165 executor transport unchanged; it does not create retry eligibility.

## One-shot disposition

The standing v9r26+ one-shot rule is fail-closed: after **any tool/process use** in the authorized one-shot turn, same-generation correction/retry is forbidden regardless of return code, apparent transport cause, artifact absence, or whether the target process reached the runner.

Accordingly:

- the authorized D-165 one-shot is consumed for disposition purposes;
- no path normalization repair, shell change, direct Windows retry, second worker, or second Smoke A is permitted under v9r28;
- absence of a Smoke root/coordinator/session/probe is non-evidence of retry eligibility;
- v9r28 is closed as `CONTRACT_INVALID_GENERATION / HARD HOLD / NON-RESUMABLE`.

## Post-failure preservation check

Independent read-only checks after the failed executor attempt proved:

- `C:\Users\joji\bc-v3-v9r28-coord-smoke-20260910` remains absent;
- repo remains at `34a2b3fc567870c45569c62dd161de16df0f4297`, local = upstream = direct origin, clean before this durable-record change;
- canonical audit remains 4 rows with SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`;
- protected dev/dev-v2/holdout remain absent;
- `ml-service/` diff remains empty;
- builder runtime/freeze/source artifacts remain absent; cache0/pyc0;
- all eight v9r28 key hashes remain exactly the D-164 final values:
  - plan `bd3cb2312c4cd72b6fa5e99e36112d1c2f41fc83e98b96d642defd8d6f471811`;
  - rubric `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`;
  - exclusion manifest `0ed656a3cf5e4fd2b65b67f67270f8d17c8344908aa7891bd2383ffd65142438`;
  - freeze `7fa795804b4f11eeda7e72a65ef46b920e06903d10b5e7abf9c0a4a394efbc78`;
  - carry `0cabc3c478d348a03b531e63458b6a225452f4e4b39a23ec158345ce937028dc`;
  - runner `9a2b9682886ecc6502ba369ee5cad0d942b5e3c44bc38e2e7458303ffba0fdbf`;
  - runner regression `32fada728e02fbec6dc3027f6ae1302ad4764020b756bfbc6a19ebdafd06feba`;
  - binding regression `47c13b95721ab15e4dc2a6d085b43b457da20f040130cafef7a63d356df11476`.

No protected data, Phase-C work, canonical audit event, production state, builder byte, or predecessor evidence was mutated by the failed Smoke-A attempt.

## STOP boundary

Do not retry or repair v9r28 Smoke A. Do not run Smoke B, real freeze, source truth, Phase C, semantic generation roles, protected dev-v2, holdout, production, or canonical evaluation audit append. A future continuation requires a separately authorized fresh-successor generation/stage; this D-165 closure starts none.
