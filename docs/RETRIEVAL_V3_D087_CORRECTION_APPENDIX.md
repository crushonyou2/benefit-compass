# Retrieval v3 D-087 narrative correction appendix (2026-09-06)

Append-only durable correction BEFORE Phase C data execution. Does NOT mutate
the frozen v9r7 builder (`C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260906-v9r7`):
no plan/rubric/lock/mechanics change. Plaintext-free: SHAs, counts,
timestamps, filenames, structural facts only.

## 1. git show count correction

- D-087 block + `RETRIEVAL_V3_D087_GENERATION_V9R7_PRERESULT.md` §0 said
  `git cat-file`/`show`/`checkout`/`restore`/sparse/worktree 0 in the freeze session.
- True (user-authorized correction): metadata-only `git show -s` was used for
  reconcile (commit metadata, no blob/file content, no protected plaintext).
- Corrected counts: metadata-only `git show -s` >0; blob/content `git show` 0;
  `git cat-file` 0; `checkout`/`restore`/sparse/worktree 0; protected
  plaintext via git objects 0. No source-truth/candidate/protected exposure.
- Frozen plan/builder unaffected; provenance order (`freeze_after_hold`) unchanged.

## 2. EIGHT vs TEN author-isolation text correction

- Stale descriptive text: `GENERATION_PLAN.json` `author_isolation.rules[0]`
  parenthetical says `check_anchor.py (EIGHT sets incl failed-D076-365)` —
  carried verbatim from v7/v8 lineage, NOT updated to v9r7 operative scope.
- Operative frozen mechanics enforce TEN (authoritative, verified):
  `validate_pool.py` TEN loop (dev/holdout/history/d070/d071/d072/d074/d076/d082/d086),
  `check_anchor.py` TEN, `run_selector.py` 10-set query gate,
  `test_ten_set_gates.py` 45/45 pairwise overlap 0 PASS (d082 + d086 probes hit),
  `author_brief.md` TEN list (dev-v1/holdout/history/D070/D071/D072/D074/D076/D082/D086).
- Interpretation: operative TEN wins; stale EIGHT parenthetical is descriptive
  only and MUST NOT be read as gating scope. Frozen bytes intentionally NOT
  mutated per user instruction; this appendix is the authoritative reading.
- Note: `exclusion_inputs.required_query_overlap_sets` lists nine names textually
  (d086 named separately via `d086_exclusion` lock entry + tenth fingerprint file);
  operative enforcement remains TEN as above.

## 3. Reconciled base for this correction (observed)

- Branch `codex/retrieval-v3-user-search-quality` HEAD
  `828e3a4ad841b29449920ac0f73c955fcca34016` clean; local = upstream =
  direct remote identical; `git diff --check` PASS; `git diff HEAD -- ml-service/` 0.
- OMP `18.1.5`; `modelRoles` default/plan
  `opencode-go/muse-spark-1.3-contributor:xhigh`, no project override.
- Audit `eval/retrieval-v3/audit/events.jsonl` 4 events SHA
  `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506` (no append).
- `eval/retrieval-v3/dev/` + `holdout/` + `dev-v2/` absent; no dev-v2 branch/tag/worktree.
- Frozen v9r7 builder SHAs unchanged: plan 43552
  `cf47cc298234efabb3cf3688cd79f5b771c44d60ad866ee1d6bd0a0f4ffed2c9`,
  rubric 3334 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`,
  lock 10967 `460ad0175e347328a0cefcbb39500820ba1e73fff90e78551a455ff5028af6a1`.

## 4. Boundary

Added this doc + DECISIONS `D-088` block + SESSION-LOG entry ONLY (repo).
No frozen plan/rubric/lock/mechanics mutation. No source snapshot, authors,
A/B/C, selector, benchmark, protected access in this correction commit.
Phase C execution follows ONLY after this correction is committed+pushed.
