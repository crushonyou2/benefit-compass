# Retrieval v3 D-078 SAME-STAGE failure closure — CONTRACT_INVALID_GENERATION (2026-09-05)

Same-stage narrow durable failure closure of the D-078 generation-v7 Phase C execution. No repair, no resume, no new design/freeze, no D-079/v8.
Plaintext-free: SHAs, counts, timestamps, filenames, structural facts only — no query text, no labels, no id-to-text mappings.

## 0. Reconciled base (actual wins, this closure session — observed)

- Branch `codex/retrieval-v3-user-search-quality` HEAD `4064308367048f159b9309fff3857a9d8190f205` clean; local = upstream = direct remote identical (all three `4064308`); `git diff --check` PASS; `git diff HEAD -- ml-service/` 0.
- Frozen v7 bytes preserved as failed evidence (byte-identical to D-077 freeze): `GENERATION_PLAN.json` 28766 bytes SHA `c8adfcf2c1cb86e622c7fa4033b7dd72b63de42494de332261f3a489c770d1da`; `RUBRIC.json` 3330 bytes SHA `597aa53a39c69cfb9409a339ebe8f79f15e07f635899d4d24203289ea46de492`; `PLAN_LOCK.json` 3332 bytes SHA `1db0687e0eb5321a64236991139144440e2f34678b91e91bcce80103afd5d140`.
- Frozen six byte-identical by clean-tree inheritance from the D-077 verification (prereg `78420186…` + plan-v4 `a25d9c48…` + safe-action `c512fb56…` + policy-v2 `6fee9ec2…` + link-V2 `f028ce46…` + cost-V1 `5891b0ba…`; no tracked byte differs from verified remote HEAD).
- Audit `eval/retrieval-v3/audit/events.jsonl` 4 events SHA `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506` byte-identical (no append).
- Canonical v3 result absent; `eval/retrieval-v3/dev/` + `holdout/` absent (`result_schema.py` is a pre-existing module, not a result); no dev-v2 branch/tag/worktree created or touched; protected v3 dev/holdout freeze branches pre-existing, untouched.
- No child agents in this closure session. No `git cat-file` / `git show` / `checkout` / `restore` / sparse / worktree invocation in this stage (count 0). No source-truth plaintext read in this stage.

## 1. Web hard-gate finding (authoritative per user instruction)

- D-078 root agent `20c7c512-9c43-4ff8-9fc6-5e599958557a` was stopped on this hard gate.
- Cause: frozen generation-v7 mechanics are internally provenance-invalid. In v7 `run_selector.py`, `PLAN_SHA` is stale v6r1 SHA `9bc432648576189affb9333aa5dfaaf2d1f58b387da56f02676aaf01b073cf64` while plan version says `retrieval-v3-dev-generation-v7` and the actual frozen v7 plan SHA is `c8adfcf2c1cb86e622c7fa4033b7dd72b63de42494de332261f3a489c770d1da`; selector HOLD/manifest/provenance would therefore bind to the wrong plan.
- Also stale D-076 provenance labels exist in `run_selector` / `take_snapshot` / briefs, and `c_brief` carries stale `v6r1c` opaque-ID wording.
- Before the stop, D-078 had already taken a fresh source snapshot and mechanical slot anchors, so v7 MUST NOT be repaired or resumed post-source-truth.

## 2. Failure-closure evidence (mechanical, plaintext-free)

- Source snapshot (fresh, v7 builder): `source_truth.jsonl` SHA `9fe194653a4b5c9c688364aa9ae686996cb7cabfebd446a6b9a7e8895374c1a5`, 13589 rows (gov24 10958 / youth 2631); meta SHA `31cdb2620cd4d8b81203bdffa77b280a1897bc97d3d93ca657b6ffc1bad21f66`.
- Mechanical slot anchors (v7 builder, taken before stop): `anchors_1.json` SHA `ef53b89b2078fc029b3fa267f36d98cde8d7af042d18a7dfcfaa85bbadb56968`; `anchors_2.json` SHA `4754ae87caf3a7d8ccdcfdc9b3ea028d11c90dfc11bc3f707e012c479e8130ef`.
- Stage gates all zero/none: candidate/query rows 0; author staging roots 0; author agents 0; packets A/B 0; reviewer agents 0; raw A/B 0; agreement none; C 0; selector none; protected actions 0; audit appends 0; result none.
- New artifact (private v7 builder only, hashes/counts only, no plaintext): `D078_CONTRACT_INVALID_SUMMARY.json` (verdict, root provenance, frozen v7 SHAs, source/anchor SHAs, gate zeros). No query fingerprint artifact created or needed. All v7 bytes/artifacts preserved as failed evidence; v7 builder scripts/plan/rubric/lock untouched.

## 3. Disposition

- Verdict: D-078 CONTRACT_INVALID_GENERATION. This supersedes the D-077 PASS disposition for generation-v7: v7 is NOT resumed or repaired post-source-truth.
- D-075/D-075-SC/D-076/D-076-CORR/D-077 text/history preserved verbatim; this closure consumes no new design beyond the failure record.

## 4. Mutation boundary, forbidden counts, next gate

- Added in this stage: this doc + DECISIONS D-078 block + SESSION-LOG entry (repo); one JSON summary (private builder only). V7 builder plan/rubric/lock/scripts untouched.
- Stage gates all zero/none: candidate/query rows, author staging/agents, packets A/B, reviewer agents, raw A/B, agreement, C, selector, protected actions, audit appends, result.
- Forbidden counts all 0: v7 repair/resume, source-truth plaintext read, query fingerprint artifact, A/B/C/selector execution, benchmark/retrieval/ranking/latency/HTTP/model-encode, protected plaintext/recovery/git-show/cat-file/checkout/restore/sparse/worktree, protected branch/tag/worktree/import, ml-service change, history rewrite, D-079/v8 creation.
- STOP for Web independent review. No D-079/v8 authorized here.
