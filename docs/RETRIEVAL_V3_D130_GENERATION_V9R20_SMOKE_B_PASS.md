# Retrieval v3 D-130 — generation-v9r20 one-shot Smoke B PASS

Date: 2026-09-08
Stage: Smoke B duplicate/preflight gate / exactly-one execution closure
Generation: `retrieval-v3-dev-generation-v9r20`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r20`
D-129 Smoke-A base commit: `f84aa03bbec223391493b57e0d392bd0fc234a48`

## Verdict

**SMOKE B PASS.** D-129's Smoke-A-passed final bytes consumed exactly one actual v9r20 lifecycle Smoke B through frozen `run_lifecycle_smoke.py`. The runner exited 0 with frozen `audit_lifecycle_smoke.py` verdict `LIFECYCLE_SMOKE_PASS`. The same evidence was re-audited after a stability interval and remained byte-stable with the same 21-line session SHA256.

Smoke A remains permanently consumed exactly once; no second Smoke A occurred. Smoke B is now also permanently consumed exactly once; no second Smoke B occurred and none is permitted for v9r20.

**STOP boundary:** this record does not perform the real freeze, Phase C, source-truth snapshot, Author/Reviewer/C generation, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append. The next logical stage is a separate real-freeze pre-gate against the preserved Smoke-A and Smoke-B evidence.

## Prelaunch reconciliation

Immediately before the one actual Smoke-B runner invocation:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `f84aa03bbec223391493b57e0d392bd0fc234a48`
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- main-tree protected `eval/retrieval-v3/dev/` and `eval/retrieval-v3/holdout/` plaintext paths absent
- canonical audit exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- final plan SHA256 `4baf17f208db63a27948cf1b11ac88f87b052f0f8db7f0f5468a1267023be542`, 64,375 bytes
- mechanics 58/58 exact, mismatch 0
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock` absent
- builder `__pycache__` count 0 after preflight cleanup
- actual OMP `omp/18.1.13`; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`
- exact bundled Paseo CLI/daemon `0.7.2`, daemon running/reachable, `omp` provider available
- D-129 Smoke A preserved and frozen auditor still returned `SMOKE_PASS` on session SHA `bebcc3da0155b01be4d31167c4b0f81a141b0449ea039ebf14035c0aba305b73`, 10 lines, `phasec_probe=1`, descendants 0
- complete local Paseo registry: 317 parseable records, Smoke-B lifecycle matches 0
- Smoke-B staging root `C:\Users\joji\bc-v3-v9r20-lifecyclesmoke` absent
- exact expected Smoke-B OMP session directory absent
- Smoke-B matching processes 0 after excluding the process-inspection harness and its ancestors

A first process probe during this stage self-matched its own literal-bearing inspection command. The corrected probe excluded its own process tree and hid the assembled target literal from the command line; it proved zero real Smoke-B matching processes before launch. No model/Paseo launch occurred during the false-positive probe.

Relevant final-byte non-model preflight regressions also passed before launch:

- `LIFECYCLE_CONTRACT_PASS` — 53 checks
- `ROLE_TESTS_PASS` — 172 checks
- `REGISTRY_SCAN_PASS` — 37 checks
- `REACHABILITY_PASS` — 87 checks
- `STAGING_EXACT_SET_PASS` — 24 checks
- `FREEZE_BINDING_PASS` — 66 checks
- role completion gate tests PASS

No protected plaintext recovery or prohibited git-object access was used.

## Smoke B — exactly one actual lifecycle model launch

Frozen `run_lifecycle_smoke.py` was invoked exactly once, with no argv. It created the fresh neutral staging root and launched exactly one top-level lifecycle agent through the frozen role launcher/wrapper.

Observed evidence:

- agent: `ac7d9e2d-e17a-4e98-9b70-d63f41105ca7`
- title: `v9r20-lifecyclesmoke`
- created: `2026-09-07T21:27:16.546Z`
- cwd/staging: `C:\Users\joji\bc-v3-v9r20-lifecyclesmoke`
- ParentAgentId: null
- provider/model: `omp` / `opencode-go/muse-spark-1.3-contributor`
- thinking: `xhigh`
- mode: `full`
- final observed status: `idle`
- fallback provenance: proven false / `fallback_proven=true`
- exact session: `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r20-lifecyclesmoke\2026-09-07T21-27-16-038Z_01a07dc4-ab45-71cc-a54f-cbc0e7b871be.jsonl`
- stable session lines: 21
- stable session SHA256: `d10ab9f559fbc49e10b2ee0775b04fb72b680abdc339be4206f4d517942791dd`
- frozen wrapper log SHA256: `becfb02f5db7c6995470d3cc605ff22cf75e17b1dc3eaf2e8d39873ed61132b5`
- transcript tool calls: `role_smoke_probe=1`, `todo=4`; no forbidden tool call
- role helper access log: exactly 9 rows
- deterministic deny proof: `cross-role=1`, `unknown-resource=1`, `bad-target=1`
- deterministic allowed writes: exactly one write to each `out/chunk_0.jsonl` through `out/chunk_5.jsonl`
- each chunk: exactly 1 row, 59 bytes
- descendants: 0 by inspect strict-if-present plus complete repaired local-registry scan
- runner final exit: 0
- frozen auditor verdict: `LIFECYCLE_SMOKE_PASS`

Exact output chunk SHA256 values:

- `chunk_0.jsonl` — `e7d2aecdf462de9a8918695e7adb70032f80c50205ce849b42664fe3877f24e9`
- `chunk_1.jsonl` — `1e942823dc343829cab4c491ceee21ef4a6f8a54337ae32c5564bf5920b8d2f7`
- `chunk_2.jsonl` — `90bdd8c64714150816c00c9ef40c6102d451dbf0102d3a3a698b204e7bfd090d`
- `chunk_3.jsonl` — `c695e51a11fa40103355a84f95f15396616465d391bdeade92ec03db24244e1a`
- `chunk_4.jsonl` — `d72b87b5d2fabbfd43d2b9b999bcd3cfcd4a6cfe251b44e21e5f97ce2f82de0f`
- `chunk_5.jsonl` — `4d14e6c3ee466e96ff1daf257dbe26e3205070c197e97757e9f5e9fc90d953ff`

The frozen auditor was re-run after a 12-second stability interval against the same agent, staging root, session, and wrapper log. It returned the same `LIFECYCLE_SMOKE_PASS`; the session remained exactly 21 lines with SHA256 `d10ab9f559fbc49e10b2ee0775b04fb72b680abdc339be4206f4d517942791dd`, with the same tool-call counts, deny triple, six writes, and descendants 0.

No second Smoke B launch occurred.

## Post-Smoke-B boundary

Post-run reconciliation:

- final plan remains `4baf17f208db63a27948cf1b11ac88f87b052f0f8db7f0f5468a1267023be542`; mechanics remain 58/58 exact
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock` remain absent
- complete registry now contains 318 parseable records and exactly one Smoke-B lifecycle match: agent `ac7d9e2d-e17a-4e98-9b70-d63f41105ca7`
- exact Smoke-B OMP session directory contains exactly one `.jsonl` session file
- Smoke-B agent remains idle and preserved; no stop was issued, matching the frozen runner contract
- the idle Smoke-A and Smoke-B agents each retain their provider wrapper process; these are expected preserved evidence, not duplicate launches, and are not stopped here
- canonical audit remains 4 rows with SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- production `ml-service/` unchanged
- protected dev/holdout plaintext paths remain absent
- no real freeze or Phase C was executed

Two independent read-only post-run reviews separately rehashed/re-audited the same Smoke-B evidence and returned PASS with no lifecycle-contract blocker. Both also confirmed that the remaining lifecycle wrapper process belongs to the intentionally preserved idle agent rather than a second runner/launch.

Frozen-auditor/test imports created two builder-local `__pycache__` directories. Their resolved paths were verified inside the v9r20 builder and only those cache directories were removed; final builder cache count is 0. Smoke staging, wrapper/access logs, session, output chunks, agent metadata, and other one-shot evidence were preserved untouched.

## Gate boundary

V9r20 has now consumed **Smoke A exactly once and PASSed** and **Smoke B exactly once and PASSed**. Neither smoke may ever be rerun for v9r20.

The next separate logical stage, if approved, is **real-freeze pre-gate + exactly-once real freeze only** using the preserved Smoke-A and Smoke-B evidence. Phase C, protected dev-v2 evaluation, holdout, and production remain prohibited until later gates.
