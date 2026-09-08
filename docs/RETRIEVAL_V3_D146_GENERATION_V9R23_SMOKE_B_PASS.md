# Retrieval v3 D-146 — generation-v9r23 one-shot Smoke B PASS

Date: 2026-09-09
Stage: Smoke B duplicate/runtime/provenance pre-gate / exactly-one execution closure
Generation: `retrieval-v3-dev-generation-v9r23`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r23`
D-145 Smoke-A base commit: `dda856936823f9b92d41a0efd6d5efcd60419d61`

## Verdict

**D-146 / v9r23 SMOKE B PASS.** The D-145 Smoke-A-passed final v9r23 bytes passed a fresh Smoke-B duplicate/runtime/provenance pre-gate and then consumed exactly one actual lifecycle Smoke B through frozen `run_lifecycle_smoke.py`. The runner returned `LIFECYCLE_SMOKE_PASS`, and frozen `audit_lifecycle_smoke.py` re-audited the same preserved evidence after a 12-second stability interval and again returned `LIFECYCLE_SMOKE_PASS` with the identical 21-line session SHA256 `45eeab8558e4fb4dd97b7365d4a2861d176131e9f4c672931076df54d4ac8158`.

Smoke A remains permanently consumed exactly once and unchanged. Smoke B is now also permanently consumed exactly once. No second Smoke A or Smoke B was launched, and neither smoke may be rerun for v9r23.

**STOP boundary:** this stage did not execute the real freeze, Phase C, source-truth snapshot, Author/Reviewer/C generation, selector, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append. The next separate logical stage is only a fresh real-freeze pre-gate and, if that gate passes, exactly-once real freeze against these preserved Smoke-A and Smoke-B proofs.

## Prelaunch reconciliation

Immediately before the one actual Smoke-B runner invocation:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `dda856936823f9b92d41a0efd6d5efcd60419d61`
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/dev-v2/`, and `eval/retrieval-v3/holdout/` absent
- canonical audit exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- final `GENERATION_PLAN.json`: 69,469 bytes, SHA256 `6bddf1fe4661819b9cb7029f2694194298a91c99ba6d5d491e8634eae4b67eae`
- `author_isolation.mechanics_shas`: 60/60 exact, missing 0, mismatch 0
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, source truth/meta, and final evalset absent
- actual OMP `omp/18.1.13`; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`
- bundled Paseo `0.7.2`; frozen exact Paseo CLI unchanged
- D-145 Smoke A re-audited unchanged via frozen `audit_coord_smoke.py`: rc0 `SMOKE_PASS`, 10 lines, SHA256 `0c72127e7d224259bd269e290809efb6d15cb3d5002a22031e3ab1ca23efa53e`, `phasec_probe=1`, descendants 0, fallback proven
- Smoke-B root `C:\Users\joji\bc-v3-v9r23-lifecyclesmoke` absent
- exact Smoke-B OMP session directory `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r23-lifecyclesmoke` absent
- complete local registry 338 parseable JSON records, parse errors 0; exact Smoke-A record count 1; Smoke-B title/cwd count 0
- matching Smoke-B processes 0
- Phase-C and execute roots absent
- immutable v9r22 `phasec_driver.run.lock` remained present

Fresh non-model Smoke-B preflight on these exact bytes passed: lifecycle 53, role-tools 220, completion fail-fast matrix, confinement 251, launcher reachability 87, exact Paseo CLI 64, registry-descendant 37, writer preflight 36, staging exact-set 41, freeze binding 87, strict rerun/timestamp 66, thirteen-set 78 pairwise / overlap 0, and D-123 slot/location 6 positive / 5 negative. Intentional negative-case `CONTRACT_INVALID_GENERATION` rows inside the regression suites were expected and every suite's final verdict was PASS.

The preflight battery left two builder-local `__pycache__` directories and 42 `.pyc` files. This was not one-shot evidence or a generation-contract failure. The same sole v9r23 implementation executor `3526a9e5-dabd-498d-9c67-3df795c5650a` removed only resolved cache artifacts strictly inside the exact v9r23 builder via `paseo send --prompt-file`. Prime then independently verified cache dirs 0 / `.pyc` 0, plan SHA unchanged, mechanics 60/60 exact, and Smoke-B root/session/registry/process still zero immediately before the one-shot launch.

No protected plaintext recovery or prohibited Git-object/history access was used.

## Smoke B — exactly one actual lifecycle model launch

Frozen `run_lifecycle_smoke.py` was invoked exactly once with no script arguments. `PYTHONDONTWRITEBYTECODE=1` / Python `-B` were used only for cache hygiene and did not alter the frozen lifecycle procedure. The runner created the fresh neutral staging root and launched exactly one genuine top-level lifecycle agent.

Observed provenance:

- agent: `a280775e-b7e8-4081-b8da-acf3b82f182c`
- title: `v9r23-lifecyclesmoke`
- created: `2026-09-08T22:03:01.557Z` (`2026-09-09T07:03:01.557+09:00`)
- cwd/staging: `C:\Users\joji\bc-v3-v9r23-lifecyclesmoke`
- ParentAgentId: null
- provider/model: `omp` / `opencode-go/muse-spark-1.3-contributor`
- thinking: `xhigh`
- mode: `full`
- final observed status: `idle`
- fallback provenance proven by frozen auditor: true
- exact OMP session: `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r23-lifecyclesmoke\2026-09-08T22-03-00-884Z_01a0830b-c194-7384-9d1f-ebcc52a0468c.jsonl`
- stable session lines: 21
- stable session SHA256: `45eeab8558e4fb4dd97b7365d4a2861d176131e9f4c672931076df54d4ac8158`
- transcript tool calls: `role_smoke_probe=1`, `todo=5`, `role_write_chunk=0`; forbidden tool calls 0
- helper denies: `cross-role=1`, `unknown-resource=1`, `bad-target=1`
- role access log: exactly 9 rows / 2,576 bytes / SHA256 `8697653b0f17c5ab58104b7ba3b784481af2444184e6878ccbf06a6db4e11172`
- frozen wrapper log: exactly 1 row / 471 bytes / SHA256 `e0fec99c73daf2e7ea63fda5ff23b979e68b1714a8c3b3f50ffd3bbadcd32426`
- wrapper tools/mode/kind: `todo` / `role` / `lifecycle_smoke`
- wrapper extension SHA256: `d03009f97100fc0995093f4f89db9cba45f809db43b50abf3d24c91fa8cddab7`
- exact wrapper controls: `--tools=todo`, `-e`, `--no-extensions`, `--no-skills`, `--no-rules`
- descendants: 0

Deterministic outputs were exactly one row / 59 bytes each:

- `chunk_0.jsonl` SHA256 `e7d2aecdf462de9a8918695e7adb70032f80c50205ce849b42664fe3877f24e9`
- `chunk_1.jsonl` SHA256 `1e942823dc343829cab4c491ceee21ef4a6f8a54337ae32c5564bf5920b8d2f7`
- `chunk_2.jsonl` SHA256 `90bdd8c64714150816c00c9ef40c6102d451dbf0102d3a3a698b204e7bfd090d`
- `chunk_3.jsonl` SHA256 `c695e51a11fa40103355a84f95f15396616465d391bdeade92ec03db24244e1a`
- `chunk_4.jsonl` SHA256 `d72b87b5d2fabbfd43d2b9b999bcd3cfcd4a6cfe251b44e21e5f97ce2f82de0f`
- `chunk_5.jsonl` SHA256 `4d14e6c3ee466e96ff1daf257dbe26e3205070c197e97757e9f5e9fc90d953ff`

The runner's embedded frozen lifecycle audit returned rc0 `LIFECYCLE_SMOKE_PASS`.

After 12 seconds, frozen `audit_lifecycle_smoke.py` was run against the same agent/cwd/session/wrapper/access/output evidence only. It again returned rc0 `LIFECYCLE_SMOKE_PASS`; session path, 21-line count, SHA256, tool-call counts, deny counts, six output hashes, wrapper surface, access-log shape, descendants 0, and fallback proof were unchanged. No second Smoke-B runner or model launch occurred.

## Independent post-Smoke review

A separate read-only worker independently ran frozen `audit_lifecycle_smoke.py` against the exact same Smoke-B agent/session/staging/wrapper evidence and reproduced `LIFECYCLE_SMOKE_PASS` with the same 21-line session SHA, `role_smoke_probe=1`, deny triple, six writes, descendants 0, and fallback proof. The worker also independently rechecked current plan/mechanics/cache and local registry accounting; it found the exact Smoke-A record once and exact Smoke-B record once. No operative contract blocker surfaced in this independent same-evidence review.

## Post-Smoke-B boundary

Final reconciliation before durable closure:

- final D-144/D-145 plan remains SHA256 `6bddf1fe4661819b9cb7029f2694194298a91c99ba6d5d491e8634eae4b67eae`, 69,469 bytes
- mechanics remain 60/60 exact; builder cache dirs 0 / `.pyc` 0
- complete local registry now has 339 JSON records, parse errors 0, exactly one dedicated Smoke-A record and exactly one Smoke-B record
- exact Smoke-B session directory contains exactly one `.jsonl` session
- Smoke-B agent remains idle and preserved; no stop/kill issued
- D-145 Smoke A re-audited after Smoke B and remained rc0 `SMOKE_PASS` on identical 10-line SHA `0c72127e7d224259bd269e290809efb6d15cb3d5002a22031e3ab1ca23efa53e`
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, source truth/meta, and final evalset remain absent
- real-freeze, Phase-C, and execute roots remain absent
- canonical audit remains exactly 4 rows with unchanged SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- production `ml-service/` remains unchanged
- protected dev/dev-v2/holdout plaintext paths remain absent
- immutable v9r22 run lock remains present

## Gate boundary

V9r23 has now consumed **Smoke A exactly once and PASSed** and **Smoke B exactly once and PASSed**. Both are permanently non-repeatable for this generation.

The next separate logical stage, only after another user `진행해`, is **real-freeze pre-gate + exactly-once real freeze** using these preserved exact Smoke-A and Smoke-B proofs. Phase C, protected dev-v2 evaluation, holdout evaluation, production changes, and canonical audit append remain prohibited until later gates.
