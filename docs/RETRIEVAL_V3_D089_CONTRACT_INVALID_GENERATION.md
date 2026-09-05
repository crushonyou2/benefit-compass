# Retrieval v3 D-089 Phase C CONTRACT_INVALID_GENERATION (2026-09-06)

Docs-only closure. No new generation. No old-builder content read in this closure.
Plaintext-free: SHAs, counts, timestamps, filenames, structural facts only —
no query text, no labels, no id-to-text mappings, no agreement values.

## 0. Reconciled base (actual wins, this closure session — observed)

- Branch `codex/retrieval-v3-user-search-quality` HEAD
  `3492bd9d6cabec4216c2ffaa7ab27042becd1ac4` (D-088 correction) clean;
  local = upstream = direct remote identical
  (`git rev-parse HEAD` = `git rev-parse origin/codex/retrieval-v3-user-search-quality`
  = `git ls-remote origin codex/retrieval-v3-user-search-quality`
  = `3492bd9d6cabec4216c2ffaa7ab27042becd1ac4`);
  `git status --porcelain` empty; `git diff --check` PASS;
  `git diff HEAD -- ml-service/` 0.
- Frozen v9r7 builder
  `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260906-v9r7`
  bytes unchanged (observed full SHA256 + sizes):
  - `GENERATION_PLAN.json` 43552
    `cf47cc298234efabb3cf3688cd79f5b771c44d60ad866ee1d6bd0a0f4ffed2c9`
  - `RUBRIC.json` 3334
    `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
  - `PLAN_LOCK.json` 10967
    `460ad0175e347328a0cefcbb39500820ba1e73fff90e78551a455ff5028af6a1`
  - `input/EXCLUSION_INPUTS.json` (manifest) 2254
    `7c5cc0f9bb373e05221bf368f23dab592b0b746bc03c5aff983bfd72e8ec3e66`
- Audit `eval/retrieval-v3/audit/events.jsonl` 4 events SHA256
  `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
  (no append).
- Canonical v3 result absent; `eval/retrieval-v3/dev/` + `holdout/` +
  `dev-v2/` absent; no dev-v2 branch/tag/worktree (tags present are only the
  four historical v2 result tags); protected v3 freeze branches untouched.

## 1. Violation (user-reported ground truth — this alone invalidates generation)

- Frozen v9r7 `GENERATION_PLAN.json` `stage_forbidden` requires old-builder
  (v9r6 included) content access beyond pinned aggregate facts + carried
  fingerprints = 0; `post_freeze_rule` forbids D-086 recycling.
- The coordinator nevertheless read, while setting up v9r7 staging:
  `~/bc-v3-v9r6-phaseC/runlog.json`, `launch_author1.txt`,
  `launch_author2.txt`, and `author2-03173bd7/slots.json`.
- Phase C root `d855812d` was stopped after the hard violation.
- Disposition: CONTRACT_INVALID_GENERATION. v9r7 is non-resumable and
  non-repairable. A future retry requires a fresh identity/plan under a new
  decision — v9r7 MUST NOT be repaired, resumed, relabeled, or reused.

## 2. Extent before stop (hashes/sizes observed, identities user-reported)

- D-088 correction was committed + pushed first (base HEAD `3492bd9`).
- Fresh snapshot (builder + both staging copies, identical hashes):
  - `source_truth.jsonl` 75207689
    `9fe194653a4b5c9c688364aa9ae686996cb7cabfebd446a6b9a7e8895374c1a5`
  - `source_truth_meta.json` 788
    `2b01a51a856098f2b059625908874aee9fda76a870e39ccd5a8bba3c24e77f0d`
  - `anchors.json` 45475
    `79a7416b23e513138a8813745558c40f40187458d8814825a82a0e8f7509d2f9`
    (plus per-author `anchors_1.json` / `anchors_2.json`, content not read).
- v9r7 staging roots created: `~/bc-v3-v9r7-phaseC/author1-9e0bed3d` and
  `~/bc-v3-v9r7-phaseC/author2-494d2423` (runlog `1031` bytes,
  launch files `2988`/`3006` bytes, sizes only — contents not read).
- Author-1 agent `21af747f` launched then immediately stopped, ParentAgentId
  null (user-reported); `author1-9e0bed3d/out/` empty (observed).
- Author-2 not launched (user-reported; `launch_author2.txt` is a prepared
  command only); `author2-494d2423/out/` empty (observed).
- No merge / validate / A / B / C / selector / benchmark / protected /
  dev-v2 refs or outputs: builder holds no `candidates_merged`,
  packets, `frozen_raw_*`, keymaps, agreement outputs, or selected files
  (only the snapshot + anchors extent above); repo has no result/dev/
  holdout/dev-v2 dirs or refs.

## 3. Closure method and boundary

- Added this doc + DECISIONS `D-089` block + SESSION-LOG entry ONLY (repo).
- All v9r7 builder / staging / Paseo / OMP evidence preserved untouched.
- No old v9r6 builder/staging content read during this closure — verification
  used v9r7 names/sizes/hashes and repo git metadata only; old paths never
  opened. No new generation, no snapshot/authors/A-B-C/selector/benchmark/
  protected actions, no `git cat-file`/`show`/`checkout`/`restore`/sparse/
  worktree, no ml-service change, no history rewrite, no D-081…D-088
  mutation, no Desktop/browser/computer use.
- D-082/D-086 aggregates reused only as hash fingerprints, values withheld.

## 4. Verdict

- **D-089 closure complete. v9r7 Phase C closes as
  CONTRACT_INVALID_GENERATION.** One normal commit+push, verify
  clean/local=upstream=direct remote/diff-check/ml-service0/audit-exact/
  result-dev-holdout-devv2-absent/frozen-bytes-unchanged, then STOP.
- Future retry (if chosen) requires a new decision + new generation identity
  and plan. No v9r7 execution here.
