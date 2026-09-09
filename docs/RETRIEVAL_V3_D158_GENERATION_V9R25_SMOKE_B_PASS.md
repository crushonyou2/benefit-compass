# Retrieval v3 D-158 — generation-v9r25 one-shot Smoke B PASS

Date: 2026-09-09
Stage: Smoke B duplicate/runtime/provenance pre-gate / exactly-one execution closure
Generation: `retrieval-v3-dev-generation-v9r25`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260909-v9r25`
D-157 Smoke-A closure base commit: `8c5b5f7d40c11f8a0505d9dc5f51948bb52f4af0`

## Verdict

**D-158 / v9r25 SMOKE B PASS.** The D-157 Smoke-A-passed final v9r25 bytes passed a fresh Smoke-B duplicate/runtime/provenance pre-gate and then consumed exactly one actual lifecycle Smoke B through frozen `run_lifecycle_smoke.py`. The runner returned `LIFECYCLE_SMOKE_PASS`, and frozen `audit_lifecycle_smoke.py` re-audited the same preserved evidence after a 15-second stability interval and again returned `LIFECYCLE_SMOKE_PASS` with the identical 21-line session SHA256 `3c76474133eb9b32e026a57f909132a5954c543b06f3b5e943ca101dbcadbf8b`.

Smoke A remains permanently consumed exactly once and unchanged. Smoke B is now also permanently consumed exactly once. No second Smoke A or Smoke B was launched, and neither smoke may be rerun for v9r25.

**STOP boundary:** this stage did not execute the real freeze, Phase C, source-truth snapshot, Author/Reviewer/C generation, selector, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append. The next separate logical stage is only a fresh real-freeze pre-gate and, if that gate passes, exactly-once real freeze against these preserved Smoke-A and Smoke-B proofs.

## Prelaunch reconciliation

Immediately before the one actual Smoke-B runner invocation:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin-branch `8c5b5f7d40c11f8a0505d9dc5f51948bb52f4af0`
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/dev-v2/`, and `eval/retrieval-v3/holdout/` absent
- canonical audit exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- final `GENERATION_PLAN.json`: 76168 bytes, SHA256 `c017d6578bf4a81c73c7960fd62d8b11c25d899e0330a293314d2a219ec9383c`
- `RUBRIC.json` 3334 bytes `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`; `EXCLUSION_INPUTS.json` 4766 bytes `d917de37e2c0b0cd761f9ff72d81906df31546cab6e4af15a5c89f36dd91b857`; `failed_d155_query_fingerprints.json` 24931 bytes `4e1f980dfe48317201941503202f8130bae64ffff13b547e666ce1b7cab551da` (360 unique, duplicate groups 0)
- `author_isolation.mechanics_shas`: 65/65 exact, missing 0, mismatch 0
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, source truth/meta, anchors, slots, author candidates, candidates_merged all absent
- actual OMP `omp/18.1.13`; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh` (executor and Smoke-A registry records: provider `omp`, model `opencode-go/muse-spark-1.3-contributor`, thinking `xhigh`, mode `full`)
- bundled Paseo `0.7.2`; frozen exact Paseo CLI `C:\Users\joji\AppData\Local\Programs\Paseo\resources\bin\paseo.cmd` (CLI gate 64 PASS)
- D-157 Smoke A re-audited unchanged via frozen `audit_coord_smoke.py`: rc0 `SMOKE_PASS`, 10 lines, SHA256 `5fea1aa75b1d1f0f419bfaccf5c2d3ce84f9d036e8b1040ccd99d2ead4c7032b`, `phasec_probe=1`, descendants 0, fallback proven
- Smoke-B root `C:\Users\joji\bc-v3-v9r25-lifecyclesmoke` absent
- exact Smoke-B OMP session directory `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r25-lifecyclesmoke` absent
- complete local registry 362 parseable JSON records, parse errors 0, unique ids 362, dup 0; exact lifecycle title 0 / cwd 0; Smoke-A id/title/cwd 1/1/1 (362 vs D-157 closure 361: the +1 is the newly-created D-158 repo-cwd executor record `0076e894-6e12-47d9-966a-7b3b1d2f62c5` itself; lifecycle zero-state — Smoke-B root absent, session dir absent, title/cwd 0 — held under the strict stem==id/labels/dup rules)
- Phase-C and execute roots absent (`bc-v3-v9r25-phaseC`, `bc-v3-v9r25-coord-execute-20260909`)
- v9r24 builder evidence untouched (read-only listing only; its 2-dir/3-pyc cache state preserved as-is, never cleaned or written)

Fresh non-model Smoke-B preflight on these exact bytes passed: lifecycle 53 `LIFECYCLE_CONTRACT_PASS`, role-tools 250 `ROLE_TESTS_PASS`, completion `GATE_TESTS_PASS`, confinement 251 `CONFINEMENT_TESTS_PASS`, launcher reachability 87 `REACHABILITY_PASS`, exact Paseo CLI 64 `PASEO_CLI_GATE_PASS`, registry-descendant 37 `REGISTRY_SCAN_PASS`, writer preflight 36 `PREFLIGHT_PASS`, staging exact-set 41 `STAGING_EXACT_SET_PASS`, freeze binding 87 `FREEZE_BINDING_PASS` (frozen_files 88), strict rerun/timestamp 66 `FREEZE_RERUN_REJECTION_PASS`, FIFTEEN 15 sets / 105 pairs / overlap 0 (rc0), D149 carry 358/360/2 `D149_CARRY_PASS`, D150 retryable 7 `D150_RETRYABLE_PASS`, D156 reviewer retryable 9 `D156_REVIEWER_RESOURCE_RETRYABLE_PASS`, and D-123 slot/location 6 positive / 5 negative (rc0). Intentional negative-case `CONTRACT_INVALID_GENERATION` rows inside the regression suites were expected and every suite's final verdict was PASS.

The preflight battery created 2 dirs / 47 pyc inside the exact v9r25 builder only (despite `-B`/`PYTHONDONTWRITEBYTECODE=1`, inner harnesses wrote them); each target was verified resolved-under-builder and removed, then plan SHA and mechanics 65/65 were reverified unchanged with cache back to 0 dirs / 0 pyc. Smoke-B zero-state (root/session/registry) and Smoke-A preservation were reverified immediately before the one-shot launch.

No protected plaintext recovery or prohibited Git-object/history access was used.

## Smoke B — exactly one actual lifecycle model launch

Frozen `run_lifecycle_smoke.py` was invoked exactly once with no script arguments. `PYTHONDONTWRITEBYTECODE=1` / Python `-B` were used only for cache hygiene and did not alter the frozen lifecycle procedure. The runner created the fresh neutral staging root and launched exactly one genuine top-level lifecycle agent.

Observed provenance:

- agent: `73e51095-c187-48e3-a6b4-e6d387455248`
- name: `v9r25-lifecyclesmoke`
- cwd/staging: `C:\Users\joji\bc-v3-v9r25-lifecyclesmoke`
- ParentAgentId: null
- provider/model: `omp` / `opencode-go/muse-spark-1.3-contributor`
- thinking: `xhigh`
- mode: `full`
- final observed status: `idle`
- fallback provenance proven by frozen auditor: true
- exact OMP session: `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r25-lifecyclesmoke\2026-09-09T09-29-38-526Z_01a08580-61de-7442-8de3-e80d6b329ae6.jsonl`
- stable session lines: 21 (44189 bytes)
- stable session SHA256: `3c76474133eb9b32e026a57f909132a5954c543b06f3b5e943ca101dbcadbf8b`
- transcript tool calls: `role_smoke_probe=1`, `todo=4`; forbidden tool calls 0
- helper denies: `cross-role=1`, `unknown-resource=1`, `bad-target=1`
- role access log: exactly 9 rows / 2792 bytes / SHA256 `a9c57e61cc842b053be959ee60d8869104b793d082a25f2a447140026b975c6a`
- frozen wrapper log: exactly 1 row / 471 bytes / SHA256 `acba3c926614c00bc4e7d4496c5c9b9f417c56b3368a8a76b0d0ca2d07572736`
- wrapper tools/mode/kind: `todo` / `role` / `lifecycle_smoke`
- wrapper extension: SHA256 `59cd5eb477784607263369306d88da50e4124a32f4062a196f8de103532ecdde`
- exact wrapper controls: `--tools=todo`, `-e`, `--no-extensions`, `--no-skills`, `--no-rules`
- descendants: 0

Deterministic outputs were exactly one row / 59 bytes each:

- `chunk_0.jsonl` SHA256 `e7d2aecdf462de9a8918695e7adb70032f80c50205ce849b42664fe3877f24e9`
- `chunk_1.jsonl` SHA256 `1e942823dc343829cab4c491ceee21ef4a6f8a54337ae32c5564bf5920b8d2f7`
- `chunk_2.jsonl` SHA256 `90bdd8c64714150816c00c9ef40c6102d451dbf0102d3a3a698b204e7bfd090d`
- `chunk_3.jsonl` SHA256 `c695e51a11fa40103355a84f95f15396616465d391bdeade92ec03db24244e1a`
- `chunk_4.jsonl` SHA256 `d72b87b5d2fabbfd43d2b9b999bcd3cfcd4a6cfe251b44e21e5f97ce2f82de0f`
- `chunk_5.jsonl` SHA256 `4d14e6c3ee466e96ff1daf257dbe26e3205070c197e97757e9f5e9fc90d953ff`

The six output SHAs are byte-identical to the frozen v9r24 deterministic outputs, as expected for the unchanged lifecycle-smoke contract.

The runner's embedded frozen lifecycle audit returned rc0 `LIFECYCLE_SMOKE_PASS`.

After 15 seconds, frozen `audit_lifecycle_smoke.py` was run against the same agent/cwd/session/wrapper/access/output evidence only. It again returned rc0 `LIFECYCLE_SMOKE_PASS`; session path, 21-line count, SHA256, tool-call counts, deny counts, six output hashes, wrapper surface, access-log shape, descendants 0, and fallback proof were unchanged. No second Smoke-B runner or model launch occurred.

Sole execution owner: executor `0076e894-6e12-47d9-966a-7b3b1d2f62c5` (`D158 v9r25 Smoke B executor`, exact repo cwd, top-level, `omp`/`muse-spark-1.3-contributor`/`xhigh`/`full`) performed every step end-to-end with no second executor/worker/subagent spawned. Exactly-one Smoke B rests on observed evidence only: one runner execution in executor activity, the fresh root yielding exactly one lifecycle agent, exact-cwd registry count 1, exact session-dir count 1, and no second launch/rerun observed.

## Independent post-Smoke review (Web FINAL PASS)

Web independently reran frozen `audit_lifecycle_smoke.py` against the exact consumed Smoke-B evidence and returned rc0 `LIFECYCLE_SMOKE_PASS` with identical facts: agent `73e51095-c187-48e3-a6b4-e6d387455248`, exact session 21 lines SHA256 `3c76474133eb9b32e026a57f909132a5954c543b06f3b5e943ca101dbcadbf8b`, `role_smoke_probe=1`/`todo=4`, deny triple each 1, six writes each 1, descendants 0, fallback proven. Output/wrapper/access-log/extension SHAs unchanged from the Smoke B section above (wrapper `acba3c92…`, access-log `a9c57e61…`, role ext `59cd5eb4…`). D-157 Smoke A independently re-audited unchanged `SMOKE_PASS` (10 lines `5fea1aa75b1d1f0f419bfaccf5c2d3ce84f9d036e8b1040ccd99d2ead4c7032b`). Registry: 363 parseable / 0 errors / 0 dup with lifecycle title/cwd exactly one; plan `c017d6578…`, mechanics 65 exact, cache 0, downstream runtime absent, audit4/protected/ml-service unchanged, v9r24 evidence unchanged.

Observer note: a separate observer `Get-FileHash` on the live session file hit a Windows sharing violation only after the frozen auditor had successfully read and hash-verified it. Recorded as observer file-handle contention, not a generation failure — auditor evidence above is unaffected.

Scope note: Web's independent pass is the frozen-auditor rerun on the exact evidence above, not a full-transcript read. The exactly-one claim above rests on the observed evidence stated there.

## Post-Smoke-B boundary

Final reconciliation before durable closure:

- final v9r25 plan remains SHA256 `c017d6578bf4a81c73c7960fd62d8b11c25d899e0330a293314d2a219ec9383c`, 76168 bytes
- mechanics remain 65/65 exact; builder cache dirs 0 / `.pyc` 0 (`-B` / `PYTHONDONTWRITEBYTECODE=1` left no post-run cache; no cleaning needed, Smoke evidence untouched)
- complete local registry now has 363 JSON records, parse errors 0, dup 0, exactly one Smoke-A id (`7989e333-d302-4d8b-886c-0d230c4b9f3c`) and exactly one Smoke-B id (`73e51095-c187-48e3-a6b4-e6d387455248`), each title/cwd exactly one, children 0 both
- exact Smoke-B session directory contains exactly one `.jsonl` session
- Smoke-B agent remains idle and preserved; no stop/kill issued
- D-157 Smoke A re-audited after Smoke B and remained rc0 `SMOKE_PASS` on identical 10-line SHA `5fea1aa75b1d1f0f419bfaccf5c2d3ce84f9d036e8b1040ccd99d2ead4c7032b`
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, source truth/meta, anchors, slots, author candidates, candidates_merged remain absent
- real-freeze, Phase-C, and execute roots remain absent (only the consumed `bc-v3-v9r25-lifecyclesmoke` staging exists)
- canonical audit remains exactly 4 rows with unchanged SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- production `ml-service/` remains unchanged
- protected dev/dev-v2/holdout plaintext paths remain absent
- v9r24 evidence untouched

## Gate boundary

V9r25 has now consumed **Smoke A exactly once and PASSed** and **Smoke B exactly once and PASSed**. Both are permanently non-repeatable for this generation — no rerun of either smoke is authorized regardless of any future stage result.

The next separate logical stage, only after another user `진행해`, is **real-freeze pre-gate + exactly-once real freeze** using these preserved exact Smoke-A and Smoke-B proofs. Phase C, protected dev-v2 evaluation, holdout evaluation, production changes, and canonical audit append remain prohibited until later gates.
