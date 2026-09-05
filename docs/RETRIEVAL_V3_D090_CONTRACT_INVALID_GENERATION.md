# Retrieval v3 D-090 CONTRACT_INVALID_GENERATION (2026-09-06)

Docs-only closure. No v9r8 pre-result freeze, no smoke PASS, no Phase C execution.
The v9r8 builder and smoke directories are preserved as failure evidence and are
not mutated by this closure. Plaintext-free: SHAs, counts, timestamps,
filenames, agent IDs, tool names, path-category facts only — no query text, no
labels, no id-to-text mappings, no agreement values.

## 0. Reconciled base (actual wins, this closure session — observed)

- Branch `codex/retrieval-v3-user-search-quality` HEAD
  `4d96f0fbddec06cd5af938231b882db941861a62` (D-089) clean;
  local = upstream = direct remote identical; `git status --porcelain` empty;
  `git diff --check` PASS; `git diff HEAD -- ml-service/` 0.
- OMP `18.1.5`; `modelRoles` default/plan
  `opencode-go/muse-spark-1.3-contributor:xhigh`, no project override.
- Seed capsule `bc-v3-v9r8-seed-capsule` manifest SHA256
  `4c3eeb39843ab9892c5e67da1aa2922dcda0ffcb8ab1b63b1fec5d14f144075e`
  verified (43/43 entries) at stage start.
- Audit `eval/retrieval-v3/audit/events.jsonl` 4 events SHA256
  `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
  (no append).
- Canonical v3 result absent; `eval/retrieval-v3/dev/` + `holdout/` +
  `dev-v2/` absent; no dev-v2 branch/tag/worktree; protected v3 freeze
  branches untouched.

## 1. Child provenance (structural fact — not the invalidating cause)

- One task child (`V9r8Builder`) was spawned for implementation, then the user
  ordered root-only work with no task/hub/subagents/descendants. The child was
  cancelled immediately; no child result was delivered, consumed, or copied.
- User-reported ground truth: child cancelled `19:29:17Z`; target v9r8 builder
  verified absent `19:29:21Z`; root created the builder `19:29:33Z` from the
  verified capsule. Root-only from `19:29:33Z`; transcript remains auditable on
  capsule-only provenance for the builder seed.
- The child is recorded here for provenance completeness and is NOT the
  invalidating cause of this verdict.

## 2. Void setup-defective smoke (reason A)

- Coordinator smoke attempt 1 used FINAL-at-the-time bytes but a defective
  launcher: the shim was named `coordinator_omp.cmd`, which does not shadow
  Paseo's `omp` resolution on the agent-specific PATH prepend, so the wrapper
  was never invoked (no wrapper invocation log).
- Agent `a00232b7-9078-4508-99b0-2afa622f2018`, cwd
  `bc-v9r8-coord-smoke-20260906/cwd`, launched `2026-09-05T19:37:54Z`,
  `--verify` PASS (ParentAgentId null, cwd exact, model
  `opencode-go/muse-spark-1.3-contributor`, literal fallback false).
- Transcript toolCall counts: `todo` 1, `read` 6, `bash` 3, `grep` 1,
  `phasec_probe` 0. Required zero forbidden-tool / probe-fallback behavior
  not met.
- Predecessor accesses by that unconfined agent (path-category facts):
  `ls` of the v9r7 builder directory; `grep` for coordinator tokens over the
  v9r7 builder directory; `read` of v9r7 `launch_top_level_paseo.py` lines
  120–200. This violates D-090 input confinement (capsule-only) and the
  smoke's required zero semantic-old-path access.
- No v9r8 builder mutation by the agent: zero `write`/`edit` calls; bash
  commands were listings/environment only; carried-file SHAs re-verified
  intact (10 inputs + rubric SHA-equal); only root's own edit mtimes present.
- Agent stopped (final status `error`). Attempt 1 is voided as
  setup-defective; continued repairs changed the bytes afterwards, so no PASS
  is claimable from it.

## 3. One-smoke rule breach (reason B)

- D-090 authorized exactly ONE smoke using FINAL bytes. Instead the lifecycle
  was: attempt 1 (defective, §2) → launcher repair → failed launch
  (`coord_wrapper_fail`: frozen extension not materialized in wrapper_bin,
  `19:40:21Z`) → repaired launch of agent
  `e1af6386-6e53-4ca2-b7cd-a98525d24dba` (`2026-09-05T19:40:49Z`, verify PASS)
  with wrapper invocation proven (`coord_wrapper_invoked`, tools `todo`,
  mode `smoke`, `argc_in` 8 / `argc_out` 14).
- Attempt-2 session: 17 lines, `todo` 4, `phasec_probe` 0, no `SMOKE_DONE`.
  Root cause found before any further run: the extension used a guessed
  `tools()`/`onToolCall` API instead of the real `CustomToolFactory`
  default-export contract, so the probe tool never registered; the agent
  correctly reported itself blocked on `todo` only. Agent stopped while idle.
- A pre-smoke web review then listed 6 repair defects; repairs began but were
  STOPPED by the present verdict before completion and before any further run.
- Multiple launches/smokes while the bytes were still changing breaches the
  exactly-one-FINAL-bytes smoke rule. Together with §2, v9r8 is
  non-resumable and non-repairable as a generation package.

## 4. No Phase C confirmation (observed)

- Fresh Phase C root `~/bc-v3-v9r8-phaseC` absent (driver never ran).
- v9r8 builder holds no `source_truth.jsonl`, `anchors.json`,
  `candidates_merged.json`, `raw_A/B`, `adjudicated_pool.json`, `sealed/`,
  packets, keymaps, or attestations; no authors/reviewers/C/selector/
  benchmark/protected/dev-v2 execution; audit unchanged (§0).

## 5. Closure method and boundary

- Added this doc + DECISIONS `D-090` block + SESSION-LOG entry ONLY (repo).
- v9r8 builder (`bc-v3-dev-v2-builder-20260906-v9r8`), smoke dirs
  (`bc-v9r8-coord-smoke-20260906`, `bc-v9r8-coord-smoke-20260906b`),
  discovery probe dir (`probe-discover`), Paseo/OMP session evidence, and all
  wrapper logs are preserved untouched as failure evidence.
- No v9r8 repair/resume/reuse, no new generation, no snapshot/authors/A-B-C/
  selector/benchmark/protected actions, no `git cat-file`/`show` (beyond
  metadata-only `git show -s` reconcile)/`checkout`/`restore`/sparse/
  worktree, no ml-service change, no history rewrite, no D-081…D-089
  mutation, no Desktop/browser/computer use.

## 6. Verdict

- **D-090 closes as CONTRACT_INVALID_GENERATION.** One normal commit+push,
  verify clean/local=upstream=direct remote/diff-check/ml-service0/
  audit-exact/result-dev-holdout-devv2-absent, then STOP this D-090 root.
- A successor generation (if chosen) requires a new decision with a new
  generation identity and plan, started outside this root. v9r8 MUST NOT be
  repaired, resumed, relabeled, or reused.
