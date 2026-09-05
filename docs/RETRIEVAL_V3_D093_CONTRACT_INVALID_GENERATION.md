# Retrieval v3 D-093 generation-v9r9 Phase C CONTRACT_INVALID_GENERATION (docs-only closure)

Single frozen run executed exactly once per `C:\Users\joji\Documents\programming\D093_PHASEC_PROMPT.txt`, then failed closed under the one-run contract. No repair/rerun. Plaintext-free: IDs, paths (names only), status, existence booleans, launch counts. No query/gold semantic plaintext.

## 1. Reconciled base (actual wins, observed before launch)

- Branch `codex/retrieval-v3-user-search-quality` HEAD `3c5e273c7862ef7ccb53825b17fe3d544ca3b069` clean; local = upstream = direct remote identical; `git diff --check` PASS; `git diff HEAD -- ml-service/` 0.
- OMP `18.1.5`; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`.
- Audit `eval/retrieval-v3/audit/events.jsonl` 4 events SHA `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506` (no append).
- Canonical v3 result/dev/holdout/dev-v2 absent; no dev-v2 branch/tag/worktree.
- D-091 frozen v9r9 PRE-RESULT VALID/PASS; D-092 narrative correction authoritative.
- Frozen pre-run gate PASS (verified before launch, bytes immutable after): plan `c6ba5ad5a3a07fddf60fa56d9ac6b70c27e1e8d4ca64097f8649f8c8309c172c`, lock `e904f2851788603b58254528f4c813e9ef15ecb6d8d39e20cb425d1408ea7bfc`, rubric `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`, exclusion manifest `353df31a264f67ae76bf4daa740dd1dfe1c6db99df259cad44fba75f0a790dd8`, FROZEN_HASHES 53 files == actual set with zero missing/extra/mismatch; ext `31c05ed0457c1469a451ff6356d70c361fa0b278af684298a03aac1e7f186bab`, coord wrapper `61300a12fa57bfb370c37d448be59bdbf156cb3108ca48f4fb1be2de28de697b`, driver `fdf91460021ae46499794e1d8dfab6a4f57252a01dbc3a97f0718a7405234752`, execute auditor `3fc5a3c09a949a4b3a7a8681b4b4ba287da34ba99848bee94e21c3292a7b4ae5`, launcher `da3ac11307bf19f2942d425bfcf84af99b3d5a677676d6ee0f7c21ef3ffad67d`, freeze `d1e7531737997728c8c09b1bd6e2ce8d689818afa0f5f8ef53327d8726d2258f`.
- Coordinator cwd `C:\Users\joji\bc-v9r9-coord-execute-20260906\cwd` absent before creation; Phase-C root `C:\Users\joji\bc-v3-v9r9-phaseC` absent; `phasec_driver.run.lock` absent. One pre-result smoke already consumed; no second smoke.

## 2. The ONE execute launch (frozen mechanics only)

- Created brand-new empty coordinator cwd above; launched EXACTLY ONE execute coordinator via frozen `launch_phasec_coordinator.py` in `execute` mode.
- Coordinator `883c9301-a7be-4277-9fec-9755571b0430`, Parent null, exact cwd, model `opencode-go/muse-spark-1.3-contributor`, `BC_PHASEC_MODE=execute`, `PYTHONUTF8=1`, wrapper `todo` + frozen ext invocation logged once.
- Prompt instructed: invoke `phasec_execute` exactly once with empty input, no other tool except optional built-in `todo`, no arbitrary access; report status and stop.
- `phasec_execute` called once; frozen driver spawned once via fixed interpreter + frozen driver path.

## 3. Failure extent (Web-observed ground truth; no further execution-state diagnostics in this closure)

- Driver acquired `phasec_driver.run.lock` (one-run evidence); fresh source snapshot/meta + anchors created.
- Author-1 `f1d2e97e-4b22-432d-823c-ace7d7242989` launched top-level and ended `Status=error`; transcript ends `[System Error] Interrupted by user (stopReason=aborted, model=opencode-go/muse-spark-1.3-contributor)`.
- No author candidate chunks collected: no `author_chunks`/candidates; no A/B packets/raw/frozen/keymaps/agreement; no C packet/output/merge; no selector/evalset.
- No author2/reviewers/C/selector launches completed; no benchmark/retrieval/protected dev-v2/holdout execution or import after generation.
- Cause beyond the observed `error` + aborted transcript is not speculated in this root.

## 4. Verdict / boundary

- Generation-v9r9 Phase C = CONTRACT_INVALID_GENERATION under the one-run contract, regardless of root cause. No repair/rerun/byte changes under v9r9; v9r9 non-resumable/non-repairable.
- Evidence preserved untouched: frozen builder `bc-v3-dev-v2-builder-20260906-v9r9`, Phase-C root `C:\Users\joji\bc-v3-v9r9-phaseC`, execute coordinator cwd/session, author-1 staging/session.
- Repo changes in this closure ONLY: this doc + DECISIONS `D-093` block + SESSION-LOG entry. No frozen mutation; no history rewrite; no ml-service change; no audit append.
- Forbidden counts 0 in this closure root (second execute/author/reviewer/C/driver/model launch, driver rerun, frozen repair, runtime deletion/mutation, benchmark/protected access incl. git-object-scan, ref creation, D-081..D-092 mutation, D082/D086 reuse beyond fingerprints, Desktop/browser/computer, semantic plaintext logging).
- STOP. Successor, if any, requires a fresh identity/plan under a new decision outside this root.
