# Retrieval v3 D-156 — generation-v9r25 PRE-SMOKE PASS

Date: 2026-09-09
Stage: fresh successor PRE-SMOKE construction + same-stage mechanical repairs (static only)
Generation: `retrieval-v3-dev-generation-v9r25`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260909-v9r25`
D-155 closure base commit: `6e3b3584ece725f716fadeda32f5133365cef0fb` (2026-09-09T06:08:49Z)

## Verdict

**D-156 / v9r25 PRE-SMOKE: PASS for static/PRE-SMOKE only. NOT Smoke-A authorization.**

V9r25 is a fresh D-156 successor to immutable D-155/v9r24. It makes only the narrow mechanical delta proven by the consumed v9r24 Phase-C failure: (1) carry v9r24's complete failed 360-row Author pool forward only as 360 unique normalized SHA256 query fingerprints (source_rows 360, duplicate groups 0) as the 15th exclusion set under D-087 precedent, (2) model-facing role extension locally rejects UNKNOWN resources (e.g. `reviewer_packet`) with zero helper spawn/filesystem/access-log row (retryable) while known cross-role resources still reach helper for fatal cross-role DENY, (3) reviewerA/B/C malformed-JSON/non-object/key-shape and packet-derived ID/order failures become plaintext-free REJECT_RETRYABLE (`reviewer_shape`/`reviewer_id_order`, no_write, retry before final DONE), with audit accepting only frozen reviewer/C codes while still failing any DENY and requiring 6 successful chunks. Retrieval/evaluation semantics, rubric, quotas, A/B/C semantics, selector algorithm, canonical gold exclusions (dev-v1/holdout/history only), D150 author reservation/retryables, D142 C 12x30, D143 no-literal-staging-path, D144 resource parity, D135 timestamp/O_EXCL mechanics, bundled Paseo provenance, completion/descendant rules, and protected-data boundaries are preserved. Reviewer prompt/brief already correctly says resource `packet`; no `reviewer_packet` alias was added and resource surface was not expanded.

No v9r25 Smoke A/B, real freeze, source-truth snapshot, Phase C, Author/Reviewer/C generation role, selector, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append occurred in D-156.

STOP before Smoke A. A future fresh explicit user `진행해` is required for a separate Smoke-A prelaunch/execution stage.

## Reconciled base and environment

Immediately before durable D-156 closure:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `6e3b3584ece725f716fadeda32f5133365cef0fb`
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- canonical `eval/retrieval-v3/audit/events.jsonl` 4 events SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/dev-v2/`, `eval/retrieval-v3/holdout/` absent
- OMP `18.1.13` verified; effective default/plan `muse-spark-1.3-contributor:xhigh`, no project override
- bundled Paseo `0.7.2` per standing evidence (exact CLI pinned in builder)

## D-155 reconciliation (immutable predecessor)

Durable D-155 closure and current v9r24 local bytes agree. Canonical v9r24 evidence hashes re-verified hash-only in this stage (no plaintext/semantic/gold reuse):

- PLAN_LOCK `d084914f3e3637636b30aa88cfe68bae75840967890ba517fb688bab8901730b`
- FROZEN_HASHES `056e789c4d3a5941a0e808e5e46275f1a02edf1790891ef3643e1a63b185e62d`
- run lock `39ab7c47e2ef56e51d0fb14314fc4752af1d91730fb337a3b0958665626ffc56`
- source_truth.jsonl `9fe194653a4b5c9c688364aa9ae686996cb7cabfebd446a6b9a7e8895374c1a5`
- source_truth_meta.json `4c8d363153afe6e1cfb24e9118a37d2114a262baa2ad4994d1fd9c9e1acf64da`
- anchors.json `5d2644160eecd69c799655518e6451f857a14aef101257d7f315e9044e99e729`
- slots_1.json `6ba5d97f216148e84697ed6e42b42b06d30df4e110a5417ec587136fb8c52a52`
- slots_2.json `2548fcf79a630b5af427cb13345ce513c1b03c2b6e4dd8cfa7a18df0fb9cb39a`
- author1_candidates.jsonl `4b8bbcc772f407cf463b944ff0f27aa1f501df2af6f1753f4d3ad9230c090f0f` rows 180
- author2_candidates.jsonl `3ac7af94558748bbd5882d35b587ce88b20d936c779eb58baf872535405a0668` rows 180
- normalized query fingerprints 360/360 unique, duplicate groups 0
- pool merge + FOURTEEN validation PASS (candidates_merged 159.5KB)
- reviewerA launched once (6/6 chunks, access log 15.1KB with exactly 3 DENYs: unknown-resource `reviewer_packet` line 2 fatal; chunk_0 line 57 not json self-repaired; chunk_2 id/order mismatch self-repaired); reviewerB never launched; C/selector/evalset absent

Terminal v9r24 failure stays immutable/non-resumable/non-repairable. Only the 360 hashes are carried forward as the 15th exclusion set.

## Final v9r25 identity and artifacts (static-verified)

- plan version `retrieval-v3-dev-generation-v9r25`, seed `benefit-compass-retrieval-v3-dev-v2-generation-v9r25-2026-09-09`
- `GENERATION_PLAN.json` 76169 bytes, SHA256 `9776649e526669144495008298bcd2935194376fe9a38adeabba5ebfb5ef9ee0`
- `RUBRIC.json` 3334 bytes, SHA256 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- `input/failed_d155_query_fingerprints.json` 24931 bytes, SHA256 `4e1f980dfe48317201941503202f8130bae64ffff13b547e666ce1b7cab551da`: 360 unique hashes from source_rows 360, duplicate groups 0, bound source SHAs above, zero overlap vs prior 14 sets, no failed-generation gold
- `input/EXCLUSION_INPUTS.json` 4766 bytes, SHA256 `d917de37e2c0b0cd761f9ff72d81906df31546cab6e4af15a5c89f36dd91b857`
- exact query exclusion sets 15; pairwise comparisons 105; overlap 0; positive D155 gate proven
- prior 14 inputs byte-identical to v9r24; gold exclusions stay dev-v1/holdout/history only
- `MECHANICS` 65 files, frozen_files 88 on disposable freeze repro (plan/manifest/rubric identical, no lock in real builder)
- old-token provenance deny lists include v9r24 in every family (v9r24, v3g9r24, v9r24c, 20260909-v9r24, bc-v9r24, bc-v3-v9r24, bc-v3-dev-v2-builder-20260909-v9r24)

## D-156 operative mechanics (frozen)

- Resource: extension `Known` map contains author_brief/slots/rubric, reviewer_brief/packet/rubric, c_brief/c_packet_00..11/rubric, smoke_task/rubric; UNKNOWN (e.g. `reviewer_packet`) throws local tool-parameter error with zero helper spawn/filesystem/access-log row (retryable, same role can correct). KNOWN cross-role (reviewer asks `slots`) still reaches helper for `DENY:cross-role allowed:false`, fatal under audit. Lifecycle-smoke fixed unknown-resource probe still calls helper directly for DENY.
- Writer: reviewerA/B/C shape (malformed JSON/non-object/exact-key) and packet-derived ID/order mismatch return `REJECT_RETRYABLE allowed:true/effect:no_write` with only IDs + `reviewer_shape`/`reviewer_id_order`, zero output mutation, corrected retry before final DONE allowed. Wrong chunk/row count stays extension-local + helper DENY. Security/provenance/path/target/role-kind/cross-role/symlink/reparse/escape/unreadable staged-contract failures stay fatal DENY. Authors keep D150 retryables unchanged.
- Audit: accepts only frozen author codes (`slot_stratum_mismatch`, `slot_location_mismatch`, `constraints_lt2`, `duplicate_query_fp`) for authors and only `reviewer_shape`/`reviewer_id_order` for reviewers/C, while still failing any DENY/allowed:false and requiring successful final writes for all 6 chunks. No post-final repair/send/resume.
- Regressions (disposable fixtures only): `test_d156_reviewer_resource_retryable.py` reproduces all 3 D155 failures (UNKNOWN local/no-helper/no-log, cross-role fatal, malformed JSON retryable, ID/order retryable, corrected OK, audit counting ignores retryables + requires 6 chunks, C analog).

## Repair history (same-stage, fail-closed)

Initial v9r25 construction (copy 80 static files, no runtime) passed compile but hit same-stage mechanics blockers, all repaired by the sole executor and retested to full PASS without touching D-155/v9r24 evidence or protected data: carry `V9R24` var rename, freeze FIFTEEN docstring/summary, wrapper SHA repins (role + coordinator), CRLF→LF normalization (64 files) with byte-identical restore of 14 prior inputs, plan/manifest sync via disposable-copy freeze repro (GENERATION_PLAN 76169, EXCLUSION_INPUTS 4766), OLD_TOKENS v9r24 families, FIFTEEN wiring (helper/validate/check/selector/driver/plan/freeze/carry/gates), reviewer retryable + UNKNOWN local + audit per-kind codes, D155 fingerprints 360/0/overlap0, test updates (fifteen 105, d149 carry 15, role_tools FIFTEEN + v9r24 deny families, confinement FIFTEEN + v9r24 tokens, freeze binding/rerun times after HOLD base 06:08:49Z, plan/stage lineage D-156/v9r24/D-155). No hard provenance/security/protected-data violation occurred; otherwise the stage would have gone HARD HOLD per contract.

Final battery on final bytes (disposable fixtures only for freeze): compile 47 py PASS; D155_FINGERPRINTS 360/0/overlap0 PASS; CARRY 15 PASS; FIFTEEN 15/105/0 PASS; D149_CARRY 358/360/2 PASS; D150_RETRYABLE 7 PASS; D156_REVIEWER_RESOURCE_RETRYABLE 7 PASS; ROLE_TOOLS 250 PASS; PREFLIGHT 36 PASS; SLOT_LOCATION PASS; STAGING_EXACT 41 PASS; COMPLETION_GATE PASS; LIFECYCLE 53 PASS; REACHABILITY 87 PASS; CLI_GATE 64 PASS; REGISTRY_SCAN 37 PASS; FREEZE_BINDING 87 PASS; FREEZE_RERUN 66 PASS; CONFINEMENT PASS. All rc0 with no Smoke A/B, real freeze, source snapshot, semantic roles, Phase C, selector, protected eval, audit append, or production.

Static tests created builder-local caches (2 dirs/47 pyc); the same D-156 executor removed ONLY exact v9r25 caches. Final cache0/pyc0, plan SHA unchanged after cleanup, live one-shot zero-state intact (no PLAN_LOCK/FROZEN/runlock/source truth/meta/anchors/slots/candidates/runtime roots/sessions).

## Sole implementation executor

Approved private-builder implementation and all same-stage repairs were performed end-to-end by the sole stage executor with no subagents and no second executor or generation role launched. D-155/v9r24 preserved only as immutable predecessor history.

STOP. No Smoke A/B, real freeze, source truth, Phase C, semantic generation, protected eval, holdout, audit append, or production change in D-156.

## D-156 CORRECTION — Web-found static gaps repaired same-stage (no runtime)

- Initial closure `5b310e3` claimed PRE-SMOKE PASS prematurely. Independent Web review found three static contract/test blockers in v9r25 bytes; no Smoke A/freeze/runtime had run, so all were repaired same-stage without touching D-155/v9r24 evidence or protected data.
- (1) Operative author contract stale: `author_brief.md` lines 29/117 said FOURTEEN and omitted D-155 while helper/validators enforce FIFTEEN. Fixed author wording to exact FIFTEEN with failed D-155 and `D-117/D-123/D-141/D-149/D-155` freshness; preserved historical v9r24 FOURTEEN / v9r23 THIRTEEN notes. Swept all operative brief/prompt/plan/freeze/driver descriptions: fixed freeze `validate_pool` gate to require `d155` with fifteen-set error wording, freeze driver summary `360+FOURTEEN` to `360+FIFTEEN`, and added lock `fifteenth_exclusion_d155_360_hash_only` + source binding + rows. `carry_exclusions_v9r25.py` docstring now explicitly carries D155 as the 15th set. Deprecated `FOURTEEN_NAMES`/`THIRTEEN_NAMES` aliases and historical notes preserved.
- (2) Hermetic proof gap: D156 regression proved `reviewer_packet` local reject only statically. Added real Bun mock-harness execution proof in `probe/role_tools_probe.mjs`: reviewerA `role_read_resource reviewer_packet` throws with `pi.exec` count exactly 0; known cross-role `slots` proceeds to `pi.exec` exactly once and throws on mocked helper DENY. Probe verdict now exposes `d156_unknown_spawns:0` and `d156_cross_spawns:1` (PROBE_PASS). `test_d156_reviewer_resource_retryable.py` now actually invokes the probe via Bun and asserts verdict + both fields instead of grepping strings.
- (3) Vacuous assertion: D156 shape test contained `or True`, making the no-write check unfalsifiable. Removed dead `rows_keybad`/`r_key` path; the test now explicitly establishes `out/chunk_1.jsonl` absent before the retryable shape write, asserts it remains absent after `REJECT_RETRYABLE`, then proves corrected write succeeds.
- Re-synced via disposable-copy freeze repro after changed bytes (no lock in real builder): `GENERATION_PLAN.json` 76168B SHA `58b8b1c813f22c722260e6c7d8ac580ee4995d3dd583c8017a98dadba2eecb33`, `EXCLUSION_INPUTS.json` 4766B SHA `d917de37e2c0b0cd761f9ff72d81906df31546cab6e4af15a5c89f36dd91b857`, RUBRIC unchanged `08e598a4`. Prior 14 inputs byte-identical; FIFTEEN 15/105/0; D155 source-bound 360/0. Full battery re-run PASS on final bytes (including updated Bun probe + hardened D156 + fixed gates/binding/rerun/confinement); caches back to 0/0; zero runtime preserved.
- **D-156 PRE-SMOKE PASS stands corrected on final bytes. STOP before Smoke A.**

## D-156 CORRECTION 2 — Reviewer retryable plaintext-free + worst-case log hardening (no runtime)

- Final Web review found two adversarial/log robustness gaps in the corrected v9r25 bytes; still no Smoke/freeze/runtime had run. (1) Reviewer/C retryable path was not mechanically plaintext-free: shape branch used model-provided ID when present and id/order branch logged model-provided got, so a model could leak semantic text via the ID field into REJECT stdout/log. Fixed reviewerA/B/C only to load staged packet-derived EXPECTED IDs fail-closed before parsing and to use expected ID by row index for all shape rejects and expected ID (not got) for id/order mismatches; unreadable/malformed staged packet remains fatal DENY. Authors D150 behavior unchanged. (2) Worst-case retry logging could truncate: `_reject_retryable`/`log_attempt` caps error at 300, so 60 reviewer rows would malform the audit parser. Added reviewer/C-specific compact stable representation `reviewer_retryable:<code>:<count>:<first>:<last>` (expected IDs only, deterministic, <=300, parseable); stdout still lists all expected IDs for correction. Audit accepts the compact form for reviewers/C (per-ID retained as fallback) with the same frozen whitelist and no broadened codes; fatal DENY text globally unchanged.
- Regressions (disposable fixtures only): adversarial marker `LEAKMARKER_9R25_ADVERSARIAL_XQZ7` in model ID with shape and id mismatches proves neither stdout nor log contains the marker while rejects identify only expected packet-derived IDs + frozen codes, with no output mutation and corrected retry OK; 60 shape rejects prove allowed:true/no_write, no mutation, compact log `reviewer_retryable:reviewer_shape:60:<first>:<last>` parses under the whitelist with no truncation malformation, then corrected write succeeds. D156 checks 7→9.
- Re-synced via disposable-copy freeze repro (no lock in real builder): `GENERATION_PLAN.json` 76168B SHA `c017d6578bf4a81c73c7960fd62d8b11c25d899e0330a293314d2a219ec9383c` (mechanics SHAs for hardened helper/audit/test), `EXCLUSION_INPUTS.json` unchanged 4766B `d917de37`, RUBRIC unchanged. Prior14 identical, FIFTEEN15/105/0, D155 bound, full battery PASS, cache0/pyc0, zero runtime.
- **D-156 PRE-SMOKE PASS stands corrected (2) on final bytes. STOP before Smoke A.**

## D-156 CORRECTION 3 — Post-closure cache provenance repair (no runtime)

- Web read-only check after correction-2 closure `8ba34c5` found exactly one builder byproduct: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260909-v9r25\__pycache__\role_fs_helper.cpython-311.pyc` (sole file in its `__pycache__` dir), created 2026-09-09T06:58:41Z by Web post-closure inspection/import after the prior cache0 claim. It is excluded from freeze hashing and no Smoke/runtime was consumed. No v9r25 source/mechanics/plan/input bytes were altered and no Smoke A/B, freeze, or Phase-C was run.
- Removed ONLY that exact resolved target (verified inside the v9r25 builder) before Smoke A. Reverified cache_dirs=0/pyc=0, PLAN_LOCK/FROZEN_HASHES/runlock/source/runtime roots absent, plan SHA `c017d6578bf4a81c73c7960fd62d8b11c25d899e0330a293314d2a219ec9383c` unchanged, audit/protected/ml-service unchanged.
- **D-156 PRE-SMOKE PASS stands corrected (3) on final bytes. STOP before Smoke A.**
