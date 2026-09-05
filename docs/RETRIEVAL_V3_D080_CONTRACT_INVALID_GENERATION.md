# Retrieval v3 D-080 SAME-STAGE failure closure — CONTRACT_INVALID_GENERATION (2026-09-05)

Same-stage narrow durable failure closure of the D-080 generation-v8 Phase C execution. No repair, no resume, no new design/freeze, no D-081/v9.
Plaintext-free: SHAs, counts, timestamps, filenames, structural facts only — no query text, no labels, no id-to-text mappings.

## 0. Reconciled base (actual wins, this closure session — observed)

- Branch `codex/retrieval-v3-user-search-quality` HEAD `a65a5f9926e8cd38c01c40b53dbe7d8908f552a5` clean; local = upstream = direct remote identical (all three `a65a5f9`); `git diff --check` PASS; `git diff HEAD -- ml-service/` 0.
- Frozen v8 bytes preserved as failed evidence (byte-identical to D-079 freeze): `GENERATION_PLAN.json` 29447 bytes SHA `2206582b58cdaac0f304662744c94e851359ba7bc62a567d7d25f0896f0f90c3`; `RUBRIC.json` 3330 bytes SHA `43e57129fcef793bc6b185734680fd027b72bf1aa43c2df41e05ea5b56b8589f`; `PLAN_LOCK.json` 3483 bytes SHA `0cad7acc8f986b30f33b074d7b0b0c31ac7f238631e650a5123021d3a17b5705`.
- Frozen six byte-identical by clean-tree inheritance from the D-079 verification (prereg `78420186…` + plan-v4 `a25d9c48…` + safe-action `c512fb56…` + policy-v2 `6fee9ec2…` + link-V2 `f028ce46…` + cost-V1 `5891b0ba…`; no tracked byte differs from verified remote HEAD).
- Audit `eval/retrieval-v3/audit/events.jsonl` 4 events SHA `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506` byte-identical (no append).
- Canonical v3 result absent; `eval/retrieval-v3/dev/` + `holdout/` absent; no dev-v2 branch/tag/worktree created or touched; protected v3 dev/holdout freeze branches pre-existing, untouched.
- No child agents in this closure session. No `git cat-file` / `git show` / `checkout` / `restore` / sparse / worktree invocation in this stage (count 0). No source-truth or query plaintext read in this stage.

## 1. Web hard-gate finding (authoritative per user instruction)

- D-080 root agent `1ae5b96a-63f4-4352-bba0-3b24783e7fca` executed frozen generation-v8 until source snapshot + mechanical anchors, then launched exactly two intended author Paseo agents `f4f283e3-5b16-4222-aebd-c052d335e418` and `856dd45a-98d6-47e8-b754-7064f57f6227`.
- Actual inspect showed BOTH authors with cwd = main repo (`C:/Users/joji/Documents/취준자료/project-repos/benefit-compass`), not their disjoint staging roots, and BOTH with ParentAgentId = D-080 root, not top-level.
- Frozen author_isolation requires genuine top-level authors with actual cwd exactly equal to their staging roots; mismatch => CONTRACT_INVALID_GENERATION.
- Both authors were stopped immediately and root stopped. No author candidate output exists.

## 2. Failure-closure evidence (mechanical, plaintext-free)

- Source snapshot (fresh, v8 builder, taken before stop): `source_truth.jsonl` SHA `9fe194653a4b5c9c688364aa9ae686996cb7cabfebd446a6b9a7e8895374c1a5`, 13589 rows; meta SHA `5b7d8c8dff7b168bc5fec6ca85eeded120f85fb0d15b0cfff8104558731ea8e5` (786 bytes).
- Mechanical slot anchors (v8 builder, taken before stop): `anchors.json` SHA `7137dc8e44fcb2c019a8f68c5d54614e63ef9e5536b1e9e2745966491e8d0d53`; `anchors_1.json` SHA `7c68b3bc5f752c015c1ca3bdf154f502a09558489ed2921cc67c1976da68276a`; `anchors_2.json` SHA `69fe737429d90beccb0ef314ed280f4e5eacd202b26f0b1bfe00f47878b8ad83`.
- Stage gates all zero/none: candidate/query rows 0; author staging roots 0; valid author agents 0 (2 intended, both invalid); packets A/B 0; reviewer agents 0; raw A/B 0; agreement none; C 0; selector none; protected actions 0; audit appends 0; result none.
- New artifact (private v8 builder only, hashes/counts/IDs only, no plaintext): `D080_CONTRACT_INVALID_SUMMARY.json` (verdict, root/author provenance, frozen v8 SHAs, source/anchor SHAs, expected-vs-actual isolation, gate zeros). No query fingerprint artifact created or needed (rows 0 — nothing to fingerprint). All v8 bytes/artifacts preserved as failed evidence; v8 builder scripts/plan/rubric/lock untouched.

## 3. Disposition

- Verdict: D-080 CONTRACT_INVALID_GENERATION. This supersedes the D-079 PASS disposition for generation-v8: v8 is NOT repaired or resumed post-source-truth.
- Source snapshot + mechanical anchors already exist, so v8 MUST NOT be repaired/resumed post-source-truth under any circumstance.
- D-075/D-075-SC/D-076/D-076-CORR/D-077/D-078/D-078-CORR/D-079 text/history preserved verbatim; this closure consumes no new design beyond the failure record.

## 4. Mutation boundary, forbidden counts, next gate

- Added in this stage: this doc + DECISIONS D-080 block + SESSION-LOG entry (repo); one JSON summary (private builder only). V8 builder plan/rubric/lock/scripts untouched.
- Stage gates all zero/none: candidate/query rows, author staging/valid agents, packets A/B, reviewer agents, raw A/B, agreement, C, selector, protected actions, audit appends, result.
- Forbidden counts all 0: v8 repair/resume, author resume, source-truth/query plaintext read, query fingerprint artifact, A/B/C/selector execution, benchmark/retrieval/ranking/latency/HTTP/model-encode, protected plaintext/recovery/git-show/cat-file/checkout/restore/sparse/worktree, protected branch/tag/worktree/import, ml-service change, history rewrite, D-081/v9 design/freeze.
- STOP for Web independent review. No D-081/v9 authorized here.
