# Retrieval v3 D-082 SAME-STAGE failure closure — CONTRACT_INVALID_GENERATION (2026-09-06)

Same-stage narrow durable failure closure of the D-082 generation-v9r3 Phase C execution. No repair, no resume, no new design/freeze, no D-083.
Plaintext-free: SHAs, counts, timestamps, filenames, structural facts only — no query text, no labels, no id-to-text mappings, no agreement values.

## 0. Reconciled base (actual wins, this closure session — observed)

- Branch `codex/retrieval-v3-user-search-quality` HEAD `ac7058d5fc62a5d716f880379841ae32cd94325b` clean; local = upstream = direct remote identical; `git diff --check` PASS; `git diff HEAD -- ml-service/` 0.
- Failed v9r3 builder `bc-v3-dev-v2-builder-20260905-v9r3` preserved unchanged: `GENERATION_PLAN.json` 35779 bytes SHA `7b5c47a1e61e24f8f8ec96a20b389a6dcc42002d4d14874c0daf7b64ac8da391`; `RUBRIC.json` 3334 bytes SHA `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe` (both byte-identical to the D-081-SC3 record).
- Frozen six byte-identical (prereg `78420186…` + plan-v4 `a25d9c48…` + safe-action `c512fb56…` + policy-v2 `6fee9ec2…` + link-V2 `f028ce46…` + cost-V1 `5891b0ba…`).
- Audit `eval/retrieval-v3/audit/events.jsonl` 4 events SHA `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506` byte-identical (no append).
- Canonical v3 result absent; `eval/retrieval-v3/dev/` + `holdout/` + `dev-v2/` absent; no dev-v2 branch/tag/worktree; protected v3 freeze branches untouched.
- No child agents in this closure session. No `git cat-file` / `show` / `checkout` / `restore` / sparse / worktree (count 0). No generation / A-B-C / selector / benchmark / protected-access / source-snapshot execution. `query_text` processed mechanically for hashing only — never logged, printed, or stored; fingerprint artifact verified hashes-only.

## 1. Failure finding (schema/merge defect + keymap-before-rewrite lifecycle violation)

- Source snapshot + 360 candidates created: `source_truth.jsonl` SHA `9fe194653a4b5c9c688364aa9ae686996cb7cabfebd446a6b9a7e8895374c1a5`, 13589 rows (gov24 10958 / youth 2631), mtime `2026-09-05T09:20:30.391169+00:00`; `candidates_merged.json` 360 rows / 360 unique item_ids, SHA `1908e7b27420c49c96b15b927c3447935484b9d6034df08602ba6784de45635a`, mtime `2026-09-05T09:41:33.161456+00:00`.
- Author isolation PASSED (launch record: both authors `parent_null`, cwd confinement PASS, descendants 0, no task spawn, coordinator semantic writes 0).
- A/B initial isolation PASSED (both reviewers `parent_null`, model exact, fallback false; packets 360 rows each, packet SHA A `287fd526…` / B `9b4e27fc…`).
- Schema/merge defect: frozen `reviewer_brief.md` raw row schema is exactly `item_id,stratum,location_bearing,labelable,source_truth_answerable,ambiguous,ambiguity_type,golds` with NO `query_text`; frozen `merge_raw_ab.py` L40 wrongly requires `query_text` non-null.
- Keymap-before-rewrite lifecycle violation: `packet_keymap_A.json` / `packet_keymap_B.json` materialized `2026-09-05T10:12:37.387256+00:00` / `2026-09-05T10:12:37.400259+00:00`; reviewer-A repair event `10:13:01.684Z` then 6 chunks rewritten `10:13:07.710150`–`10:13:07.716148Z`; reviewer-B repair event `10:13:11.566Z` then 6 chunks rewritten `10:13:18.434148`–`10:13:18.441145Z`; `raw_A.jsonl` / `raw_B.jsonl` frozen `10:13:40.204744Z` / `10:13:40.220751Z` now carrying `query_text` (360 rows / 360 unique each). Required frozen lifecycle was raw bytes frozen + transcript audits PASS BEFORE keymap materialization.
- Verdict: CONTRACT_INVALID_GENERATION — post-hoc same-agent `query_text` echo makes the raw bytes noncanonical; this generation cannot be repaired or reused.

## 2. Closure evidence (mechanical, plaintext-free)

- C staging `bc-v9r3-phasec-c-4e0477b1/adjudicator-C`: `c_packet_1.jsonl` 180 rows + `c_packet_2.jsonl` 180 rows; `out/` absent, out files 0. C agent `1221960c-e873-4b2d-a46e-99d976f39a53` created `2026-09-05T10:14:12.565Z`, closed. D082 root `a263a275-a21e-4c9f-86e4-d76b7d378283` idle.
- Stage gates: selector 0, seal 0, protected actions 0, audit appends 0, result none.
- New artifacts (private closure dir `bc-v3-d082-closure-20260906` only): `failed_d082_query_fingerprints.json` — 360 hashes sorted, count = unique = 360, method `SHA256(NFC+strip+collapse_whitespace+casefold)`, source `candidates_merged.json` SHA `1908e7b2…` rows 360, `generated_at` `2026-09-05T16:31:48Z`; file SHA `1315b34a0b9c08b332774e22d826ef427512158ba4c177c699d511567a338e83`. `D082_CONTRACT_INVALID_SUMMARY.json` — aggregate structural facts only; file SHA `f2d4c6c482e7c3761fa94eeb2622bf0edcbb6a4c89ddb615869b1f75f156ea59`. Neither contains plaintext.
- Semantic aggregates (`raw_A/B`, `ab_by_candidate.jsonl` 360 rows, `agreement_audit.json`, `disagreement_matrix.json`) are noncanonical and forbidden for tuning; values withheld.
- D082 queries nonreusable except hash-only fingerprints for exclusion. Protected branches / audit chain / result sets untouched. Safe-to-stop and lossless-to-stop (fingerprints preserve exclusion power; nothing else of value lost).

## 3. D-081-SC3 durable-recording correction (append-only; old text preserved verbatim)

- The D-081-SC3 block/doc recorded manifest `09bd7b52` (2120 bytes) + lock `2fa48764` (6029 bytes, `frozen_at` `2026-09-05T08:08:07+00:00`). Actual final pre-D082 v9r3 bytes (observed, cause not stated): plan 35779 SHA `7b5c47a1…` UNCHANGED; rubric 3334 SHA `08e598a4…` UNCHANGED; `input/EXCLUSION_INPUTS.json` 2123 bytes SHA `470a6763332ac8c0be63453e86c5ff595039d83bd8f8888b556f142e6bdd23e7` (mtime `08:06:56Z`); `PLAN_LOCK.json` 6132 bytes SHA `01b70c673bab1ccb83a8bd7bfa125c737a45d35980f5c78aeedbc5ca9335e826` `frozen_at` `2026-09-05T08:09:28+00:00` (mtime `08:09:28Z`). Source truth appeared later around `09:20:30Z`. No cause invented; D-081-SC3 verdict and lineage correction unchanged.

## 4. Disposition, mutation boundary, forbidden counts

- Verdict: D-082 CONTRACT_INVALID_GENERATION. This supersedes v9r3 executability: v9r3 plan/rubric preserved as evidence but MUST NOT be repaired, resumed, or reused.
- Added in this stage: this doc + DECISIONS `D-081-SC3-CORR` + `D-082` blocks + SESSION-LOG entry (repo); two JSONs (private closure dir only). v9r3 builder plan/rubric/lock/scripts untouched.
- Forbidden counts all 0: v9r3 repair/resume/reuse, generation, A/B/C/selector execution, benchmark/retrieval/ranking/latency/HTTP/model-encode, source-truth/query plaintext logging, protected plaintext/recovery/git-show/cat-file/checkout/restore/sparse/worktree, protected branch/tag/worktree/import, ml-service change, history rewrite, D-081/v9/v9r1/v9r2 record mutation, D-083 design/freeze, Desktop/browser/computer use.
