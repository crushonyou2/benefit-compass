# Retrieval v3 D-076 SAME-STAGE failure closure — CONTRACT_INVALID_GENERATION (2026-09-05)

Same-stage narrow durable failure closure of the D-076 generation-v6r1 Phase C execution. No resume, no row repair, no new design/freeze.
Plaintext-free: SHAs, counts, timestamps, filenames, chunk IDs, structural facts only — no query text, no labels, no id-to-text mappings.

## 0. Reconciled base (actual wins, this closure session — observed)

- Branch `codex/retrieval-v3-user-search-quality` HEAD `d12aba904fd6a76739137987ad13d4f183189b1b` clean; local = upstream = direct remote identical (all three `d12aba9`); `git diff --check` PASS; `git diff 5327661..HEAD -- ml-service/` 0.
- Frozen v6r1 bytes preserved (byte-identical to D-075-SC freeze): `GENERATION_PLAN.json` 22314 bytes SHA `9bc432648576189affb9333aa5dfaaf2d1f58b387da56f02676aaf01b073cf64`; `RUBRIC.json` 3334 bytes SHA `6e7b0cd97b54c8c001843338da8ac39ea99827344e81babadfb20194197bdb78`; `PLAN_LOCK.json` 1378 bytes SHA `c7cbd156d9583089f9b855ebc89e314a8ee2580572e501409494f964746b1b3f`.
- Frozen six byte-identical: prereg `78420186…` + plan-v4 `a25d9c48…` + safe-action `c512fb56…` + policy-v2 `6fee9ec2…` direct-SHA verified; link-V2 `f028ce46…` + cost-V1 `5891b0ba…` covered by clean tree + pinned HEAD (no tracked byte differs from verified remote HEAD).
- Audit `eval/retrieval-v3/audit/events.jsonl` 4 events SHA `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506` byte-identical (no append).
- Canonical v3 result absent; `eval/retrieval-v3/dev/` + `holdout/` absent (`result_schema.py` is a pre-existing module, not a result); no dev-v2 branch/tag/worktree created or touched; protected v3 freeze branches/worktrees pre-existing, untouched.
- Session model observed: `opencode-go/muse-spark-1.3-contributor`. No child agents in this closure session.

## 1. Web hard-gate finding (authoritative per user instruction)

- D-076 root agent `e930fd06-12a0-422b-8e29-c49b0b2719e1` was stopped before A/B.
- Cause: the coordinator itself wrote 5 `query_text` repairs into author chunks after mechanical validation, instead of returning fail codes to the SAME Author2 role. This violates the frozen coordinator-does-not-author / same-author-pre-annotation-repair contract.
- The violating shell tool call happened before any packet_A/B, reviewer top-level agent, raw A/B, agreement, C, selector, or protected action. No A/B/C/selector output exists for D-076; nothing downstream consumed the repaired rows.

## 2. Failure-closure evidence (mechanical, plaintext-free)

- Source snapshot (fresh read-only policy-table snapshot, v6r1 builder): `source_truth.jsonl` SHA `9fe194653a4b5c9c688364aa9ae686996cb7cabfebd446a6b9a7e8895374c1a5`, 13589 rows (gov24 10958 / youth 2631); meta SHA `e738fa36…`.
- Candidate pool (current, post-violation): `candidates_merged.json` SHA `7955d90de0e6c36ba6450bf8408189ee697102b72831e94ffde5e4415fcc7389`, 360 JSONL rows, 360 unique normalized query fingerprints (method `SHA256(NFC+strip+collapse_whitespace+casefold)` per `validate_pool.py fpq`; 0 dup groups).
- Pre-coordinator Author2 originals: `C:/tmp/repair5.txt` SHA `ae726a23a8feb9b696b27f73c043da100526986a06429db0136005df590bd37a`, 6878 bytes, 135 CRLF lines, 5 blocks (chunk IDs `v3g6r1-272`, `v3g6r1-273`, `v3g6r1-293`, `v3g6r1-302`, `v3g6r1-306`), 5 unique normalized fingerprints. All 5 IDs present in merged pool; 0 of 5 merged fingerprints equal their original — consistent with coordinator overwrite.
- Union: current360 unique, original5 unique, overlap 0, union 365.
- New artifacts (private v6r1 builder `input/`, hashes only, no plaintext): `failed_d076_query_fingerprints.json` 27755 bytes SHA `3feaab4dd3811d75321663824f9b89146df8a1236b508ab12725b1bfe36818f0` (365 fingerprints + source SHAs/counts); `D076_CONTRACT_INVALID_SUMMARY.json` 2203 bytes SHA `0279c69a3e438d8c2ab5eef40a33ac82dc9cea6786a554d69891f84ce3bb0b5b` (verdict, root/author provenance, source/pool SHAs, gate zeros).

## 3. Disposition

- Verdict: D-076 CONTRACT_INVALID_GENERATION. D-076 rows are NOT resumed or repaired. The 365 fingerprints are failure-exclusion evidence only, never reusable as generation rows.
- V6r1 plan/rubric/lock bytes preserved above; D-075/D-075-SC text/history preserved verbatim; this closure consumes no new design beyond the failure record.

## 4. Mutation boundary, forbidden counts, next gate

- Added in this stage: this doc + DECISIONS D-076 block + SESSION-LOG entry (repo); two JSON artifacts (private builder only). V6r1 builder plan/rubric/lock/scripts untouched.
- Stage gates all zero/none: packets A/B 0, reviewer top-level agents 0, raw A/B 0, agreement none, C 0, selector none, protected actions 0, audit appends 0.
- Forbidden counts all 0: D-076 row resume/repair, source-truth reread, A/B/C/selector execution, benchmark/retrieval/ranking/latency/HTTP/model-encode, protected plaintext/recovery/git-show/cat-file/checkout/restore/sparse/worktree, protected branch/tag/worktree/import, ml-service change, history rewrite, D074-row reuse beyond carried fingerprints, D-077 design/freeze.
- STOP for Web independent review. No D-077 design/freeze authorized here.
