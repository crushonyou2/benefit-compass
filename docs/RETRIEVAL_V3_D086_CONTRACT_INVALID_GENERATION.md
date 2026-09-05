# Retrieval v3 D-086 Phase C CONTRACT_INVALID_GENERATION — generation-v9r6 author-descendant violation (2026-09-06)

Plaintext-free: SHAs, counts, timestamps, filenames, structural facts only — no query text,
no labels, no id-to-text mappings, no agreement values.

## 0. Reconciled base (actual wins, this execution — observed)

- Branch `codex/retrieval-v3-user-search-quality` HEAD `c55e6c81545155e2e2b989111c8273778d15d359`
  (D-085) clean; local = upstream = direct remote identical;
  `git diff --check` PASS; `git diff HEAD -- ml-service/` 0.
- OMP `18.1.5`; provider `omp/opencode-go/muse-spark-1.3-contributor`, thinking `xhigh`, mode `full`.
- Audit `eval/retrieval-v3/audit/events.jsonl` 4 events SHA
  `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506` (no append).
- Canonical v3 result absent; `eval/retrieval-v3/dev/` + `holdout/` + `dev-v2/` absent; no dev-v2
  branch/tag/worktree; protected v3 freeze branches untouched.
- Frozen v9r6 carried verbatim: plan 41927 SHA
  `389adaff370d6e46c4c0ba9d8e645100da59e72a000cb02bd8b0436552bed3cb`, rubric 3334 SHA
  `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`, lock 9200 SHA
  `0715524b4ef6f9a420e3f0452d306281f94243c46cfdca3d5bda0b43771d00aa`
  (`frozen_at` `2026-09-05T17:16:38+00:00`); seed
  `benefit-compass-retrieval-v3-dev-v2-generation-v9r6-2026-09-06`; IDs `v3g9r6-001..360`.
- No plan/rubric/lock/mechanics change in this execution; `py_compile` 18 scripts PASS (pre-launch).

## 1. Phase C executed steps (mechanical, pre-violation)

- Fresh source-truth snapshot (read-only `SELECT ... FROM policy ORDER BY source,source_id`,
  no vector/chunk/ranking query, DSN never printed): 13589 rows (gov24 10958 / youth 2631),
  SHA `9fe194653a4b5c9c688364aa9ae686996cb7cabfebd446a6b9a7e8895374c1a5`,
  `snapshot_at` `2026-09-05T18:14:51+00:00` (after plan freeze `17:16:38Z`, correct order).
  Bytes in private builder only.
- Mechanical slot anchors 360 (author-1 180 `v3g9r6-001..180` / author-2 180 `v3g9r6-181..360`;
  per-stratum 42/50/42/50/36/40/46/54; location 108 = 12/14/12/16/10/12/14/18).
- Two author staging roots under home (filesystem-disjoint; evidence preserved, not repo):
  `~/bc-v3-v9r6-phaseC/author1-2091a0bd`, `~/bc-v3-v9r6-phaseC/author2-03173bd7`,
  each with role-specific 180-slot `slots.json` + snapshot + meta + `RUBRIC.json` +
  `author_brief.md` + `search_snapshot.py` + `check_anchor.py` + role prompt + `input/`.
- Launch via frozen `launch_top_level_paseo.py` ONLY (`--verify`): Author-1 agent
  `9e2e8bdf-3fc8-46ee-8f04-dd52af481a4d` (`CreatedAt` `2026-09-05T18:15:48.356Z`),
  Author-2 agent `678e52b1-97c6-4583-b6a7-523590f401ab` (`CreatedAt`
  `2026-09-05T18:16:07.902Z`); both `ParentAgentId` null + cwd exact + model
  `opencode-go/muse-spark-1.3-contributor` exact + `ResolvedModelIsFallback` false.
  Launch verification PASS for both.
- Both authors wrote 6/6 chunks x 30 rows = 180 + 180 = 360 rows; per-chunk row schema
  (six keys incl `candidate_id`) and ID ranges verified structurally
  (`v3g9r6-001..180`, `v3g9r6-181..360`, unique within author).

## 2. Pre-A/B transcript audit FAIL (Author-1 descendant sharding)

- Author-1 transcript 197 lines SHA
  `0bc3965987243ad8e5264197bc2c199ee1388f8386e7f46024039cd5ef5045a1`:
  tool calls `read` 16 / `todo` 7 / `eval` 29 / `task` 1 / `hub` 12.
- The single `task` call (`.../18:19:02Z`, intent `Author four stratum slices`) spawned
  FOUR background descendant agents (`ExactAuthor`, `NaturalAuthor`,
  `ExploratoryAuthor`, `MultiConstraintAuthor` job set) to author stratum slices,
  coordinated via 12 subsequent `hub` calls (slice wait/request/save-file intents).
- Frozen `generation_authors.assignment` requires exactly TWO genuine top-level Paseo
  author agents with no generic OMP task-child sharding, no subagents, no descendants.
  Author-1's slice delegation is that forbidden pattern verbatim: Author-1's 180 rows
  are descendant-authored, not top-level-authored. No same-author repair can cure
  provenance (descendant bytes cannot become top-level bytes; coordinator MUST NOT author).
- Author-2 transcript 208 lines SHA
  `5039ca909a4310ffcc4f653da2e17d13379ef1f4ae2dd2e8b2ed7b6e6af24170`:
  tool calls `eval` 50 / `read` 10 / `todo` 8; zero `task`/`hub` — clean on this axis.
  But the 360-pool requires BOTH authors genuine; Author-1's 180 poison the pool.
- Per-chunk SHA16 (structural, hash-only): author-1
  `a30645f0/a4d96ff3/065ef0ef/47c950af/8fcdfcb6/eaaf2cc0` (30 rows each);
  author-2 `f4bb6168/f667f308/12e6d0e7/a7cac602/c5bcc5ff/ed9d9cbd` (30 rows each).

## 3. Verdict

CONTRACT_INVALID_GENERATION per frozen `post_freeze_rule` (contract violation => STOP).
STOP before `merge_chunks`/`validate_pool`/repair/A/B freeze/audits/keymaps/agreement/C/
selector: none of `merge_chunks.py`, `validate_pool.py`, `build_packets_ab.py`,
`freeze_raw_ab.py`, `reconstruct_keymaps.py`, `merge_raw_ab.py`, `build_agreement.py`,
`build_packets_c.py`, `merge_c.py`, `run_selector.py` executed on Phase C data in this run.
No reviewer/C/selector/benchmark/retrieval/ranking/latency/HTTP/model-encode execution.
Both author agents stopped best-effort via frozen helper; staging roots + transcripts +
`runlog.json` + `evidence_hashes.json` preserved under `~/bc-v3-v9r6-phaseC` and OMP
session dirs (evidence, not repo).

## 4. Forbidden counts (this execution)

All 0: benchmark/retrieval/ranking/latency/HTTP/model-encode; protected dev/holdout
plaintext or recovery via Git (`cat-file`/`show`/`checkout`/`restore`/sparse/worktree 0);
protected dev-v2 freeze/branch/tag/import; candidate-plan tuning; rerun after results
(no results produced); query plaintext logging to repo; ref creation; `ml-service`
change; history rewrite; D-081/v9/v9r1/v9r2/v9r3/v9r4/D-083-HOLD/D-084/D-084-HOLD/D-085
mutation; D-070/D-071/D-072/D-074/D-076/D-082 semantic reuse beyond carried
fingerprints; old-builder content access beyond pinned aggregates; Desktop/browser/computer use.

## 5. Disposition

D-086 Phase C closed as CONTRACT_INVALID_GENERATION. v9r6 plan/rubric/lock/builder bytes
remain frozen evidence (unmutated). Added in this stage: this doc + DECISIONS `D-086`
block + SESSION-LOG entry (repo). STOP. Any retry is a new decision with a new
generation identity; v9r6 MUST NOT be repaired, resumed, or relabeled.
