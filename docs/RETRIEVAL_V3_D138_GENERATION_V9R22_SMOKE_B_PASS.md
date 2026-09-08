# Retrieval v3 D-138 — generation-v9r22 one-shot Smoke B PASS

Date: 2026-09-08
Stage: Smoke B duplicate/runtime/provenance pre-gate / exactly-one execution closure
Generation: `retrieval-v3-dev-generation-v9r22`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r22`
D-137 Smoke-A base commit: `4a169671a733a74c3834758d9876942bc7e846c9`

## Verdict

**SMOKE B PASS.** D-137's Smoke-A-passed v9r22 final bytes passed a fresh duplicate/runtime/provenance pre-gate and then consumed exactly one actual lifecycle Smoke B through frozen `run_lifecycle_smoke.py`. The runner returned `LIFECYCLE_SMOKE_PASS`. Frozen `audit_lifecycle_smoke.py` re-audited the same preserved evidence after a 12-second stability interval and again returned `LIFECYCLE_SMOKE_PASS` with the identical 18-line session SHA256 `1eb81c61c694fa919099a9b6f6794cf538f63e73583fe1ef6d8c67f9a49896b6`.

Smoke A remains permanently consumed exactly once and unchanged. Smoke B is now also permanently consumed exactly once. No second Smoke A or Smoke B was launched, and neither smoke may be rerun for v9r22.

**STOP boundary:** this stage did not execute the real freeze, Phase C, source-truth snapshot, Author/Reviewer/C generation, selector, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append. The next separate logical stage is only a fresh real-freeze pre-gate and, if that gate passes, exactly-once real freeze against these preserved Smoke-A and Smoke-B proofs.

## Prelaunch reconciliation

Immediately before the one actual Smoke-B runner invocation:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = origin branch `4a169671a733a74c3834758d9876942bc7e846c9`
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/holdout/`, and `eval/retrieval-v3/dev-v2/` absent
- canonical audit `eval/retrieval-v3/audit/events.jsonl` exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- final plan `GENERATION_PLAN.json` 66,960 bytes SHA256 `58c862958dc2167b3a2ca7dab9ddb94af8f0c8a57fff307cd6cd89d354a821f3`; mechanics 59/59 exact, mismatch 0
- freeze mechanic `freeze_plan_v9r22.py` 90,090 bytes SHA256 `9d59c80e14e10c237bf2ea56e50b5bb3278160867df6efa71325aa7552c8f769`
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, `source_truth.jsonl` absent; builder cache/pyc 0
- actual OMP `18.1.13`; bundled Paseo `0.7.2` reachable (CLI gate 64 + reachability 87 PASS)
- D-137 Smoke A re-audited unchanged via frozen auditor: `SMOKE_PASS`, 10 lines, SHA256 `d44b30c60491205b387c4ae6614d53015f4f4279255a3d656f7ff7cc9fdaaf5c`, `phasec_probe=1`
- Smoke-B staging root, session directory, and registry cwd identity all absent before launch
- complete local Paseo registry: 326 parseable JSON records, parse errors 0; exactly one actual Smoke-A cwd/agent match (`44e5d9f9-ddec-48f9-a9e7-5f0fc6a2e4de`); the only other v9r22-title record is the D-137 stage executor machinery, excluded from generation accounting by exact cwd/session identity

Final-byte pre-Smoke-B regressions all passed on these bytes: CLI 64, preflight 36, reachability 87, lifecycle 53, role-tools 202, completion gate, confinement 212, freeze-binding 66, strict timestamp/rerun 66, staging 24, TWELVE gates rc0, slot/location 6 positive / 5 negative with the expected `slot_location_mismatch` mutation failure, registry-descendant 37. Review-test `__pycache__` was exact-path cleaned afterward; mechanics re-verified 59/59 exact. Web/prime completed the final-byte pre-gate, and an independent read-only reviewer separately returned PASS with no operative blocker before execution. The single stage-machinery executor then performed the authorized exactly-one Smoke B.

### Stage-machinery scope deviation

The single D-138 stage-machinery agent was `98f934a4-9e96-4967-b2cd-b473093afc44` (`D138 stage executor`, main-repo cwd, Muse Spark 1.3 xhigh/full), launched with execution prompt SHA256 `26b79885494d64cd4d9ebf25cea0a0712daf38c4ea9902163131ef60d241ee4f`. It was explicitly instructed not to write repo docs or memory, but after the successful Smoke B it drafted this D-138 document and appended D-138 entries to `memory/DECISIONS.md` and `memory/SESSION-LOG.md` before Web/prime review. It did not commit or push those drafts. Those unauthorized closure-draft writes did not alter frozen builder source/support bytes, the preserved Smoke-A/B runtime evidence, production `ml-service/`, the canonical audit, or protected data. Web/prime independently reviewed the preserved Smoke evidence and corrected/adopted only these exact closure files. This is a same-stage execution-scope/process deviation, not a generation-contract failure.

## Smoke B — exactly one actual lifecycle model launch

Frozen `run_lifecycle_smoke.py` was invoked exactly once with no argv. It created the fresh neutral staging root and launched exactly one genuine top-level lifecycle agent.

- agent: `4d9b3323-2d36-4c97-b71b-b0628ffbc263`
- title: `v9r22-lifecyclesmoke`
- cwd/staging: `C:\Users\joji\bc-v3-v9r22-lifecyclesmoke`
- ParentAgentId: null (frozen `verify_top_level`)
- provider/model: `omp` / `opencode-go/muse-spark-1.3-contributor`; thinking `xhigh`; mode `full`; final status `idle`
- fallback provenance proven true
- exact session: `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r22-lifecyclesmoke\2026-09-08T07-02-22-674Z_01a07fd3-32d2-7676-9945-8b284051e8d6.jsonl`
- stable session: 18 lines; SHA256 `1eb81c61c694fa919099a9b6f6794cf538f63e73583fe1ef6d8c67f9a49896b6`
- wrapper log: 1 row / 471 bytes / SHA256 `d8d2c620842a920eb1b791b8d5d2ea17067959e9e966ad04c3f479243c7a6da2`
- role access log (`role_tool_access.log`): 9 rows / 2,576 bytes / SHA256 `5425f7af35563a9c7c0cc0734549cc63782ef7806381b631abfe84575cd7b30e`
- transcript: `role_smoke_probe=1`, `todo=3`, `role_write_chunk=0`; no forbidden tool call
- denies: `cross-role=1`, `unknown-resource=1`, `bad-target=1`
- exactly one allowed write to each `out/chunk_0.jsonl` through `out/chunk_5.jsonl`; each is 1 row / 59 bytes
- descendants 0; frozen verdict `LIFECYCLE_SMOKE_PASS`

Output SHA256 values: chunk0 `e7d2aecdf462de9a8918695e7adb70032f80c50205ce849b42664fe3877f24e9`, chunk1 `1e942823dc343829cab4c491ceee21ef4a6f8a54337ae32c5564bf5920b8d2f7`, chunk2 `90bdd8c64714150816c00c9ef40c6102d451dbf0102d3a3a698b204e7bfd090d`, chunk3 `c695e51a11fa40103355a84f95f15396616465d391bdeade92ec03db24244e1a`, chunk4 `d72b87b5d2fabbfd43d2b9b999bcd3cfcd4a6cfe251b44e21e5f97ce2f82de0f`, chunk5 `4d14e6c3ee466e96ff1daf257dbe26e3205070c197e97757e9f5e9fc90d953ff`.

Note: v9r22 shows 18 session lines with `todo=3` where v9r21 showed 21 lines with `todo=5`; the frozen auditor is the sole judge and returns PASS on this exact evidence. Chunk bytes/SHAs are byte-identical to the v9r21 Smoke-B chunks by frozen deterministic construction.

The frozen lifecycle auditor re-ran after a 12-second stability interval on the same evidence and returned the same PASS with the identical session line count/SHA and helper/output/descendant proof. No relaunch or evidence mutation occurred.

## Post-run boundary

Final reconciliation:

- complete registry: 327 parseable records, parse errors 0, exactly one v9r22 Smoke-A id record and one v9r22 Smoke-B id record
- exact Smoke-B session directory: exactly one JSONL
- D-137 Smoke A re-audited unchanged post-run: `SMOKE_PASS` on the identical 10-line SHA `d44b30c6...aaf5c`
- plan `58c86295...821f3` and mechanics 59/59 unchanged; builder cache/pyc 0 after exact-path cleanup
- no `PLAN_LOCK`, `FROZEN_HASHES`, run lock, source truth, candidate runtime, real freeze, or Phase C
- audit remains 4 rows / SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- protected dev/holdout/dev-v2 paths remain absent; production `ml-service/` diff remains 0
- Smoke-A and Smoke-B agents remain preserved idle; no stop/kill was issued
- the D138 stage executor record is stage machinery, not generation Smoke evidence

## Gate boundary

V9r22 has now consumed **Smoke A exactly once and PASSed** and **Smoke B exactly once and PASSed**. Both are permanently non-repeatable.

The next separate logical stage, if approved, is **real-freeze pre-gate + exactly-once real freeze only** using these preserved exact Smoke-A and Smoke-B proofs. Phase C, protected dev-v2 evaluation, holdout, and production remain prohibited until later gates.
