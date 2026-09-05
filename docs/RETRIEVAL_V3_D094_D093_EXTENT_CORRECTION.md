# Retrieval v3 D-094 D-093 execution-extent/root-cause correction (2026-09-06)

Append-only durable correction. The D-093 DECISIONS entry, the D-093
SESSION-LOG entry, and `docs/RETRIEVAL_V3_D093_CONTRACT_INVALID_GENERATION.md`
are preserved verbatim; this doc corrects only the execution-extent and
root-cause readings stated below. Plaintext-free: IDs, timestamps, counts,
status strings, and structural facts only — no query/gold semantic plaintext.

Authorization: user-ordered D-094 stage (append-only correction of D-093
execution extent/root cause; modification scope repo docs only; no generation),
plus user clarification recording the structural facts below as Web
independently observed authoritative evidence. Outside-repo builder / Phase-C
root / coordinator / author evidence was not accessed in this correction root;
those facts are recorded strictly as supplied.

## 0. Reconciled base (actual wins, observed in this correction root, repo only)

- Branch `codex/retrieval-v3-user-search-quality` HEAD
  `87eecda0382a20e01ac89f2e112d7849ea9d275a` (D-093) clean;
  local = upstream = direct remote identical; `git diff --check` PASS;
  `git diff HEAD -- ml-service/` 0.
- OMP `18.1.5`; modelRoles default/plan
  `opencode-go/muse-spark-1.3-contributor:xhigh` (runtime context, no override).
- Audit `eval/retrieval-v3/audit/events.jsonl` 4 events SHA
  `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
  (no append).
- Canonical v3 result/dev/holdout/dev-v2 absent (`eval/retrieval-v3/dev/` and
  `eval/retrieval-v3/holdout/` absent); no dev-v2 branch/tag/worktree.
- This correction root performed no generation, no execute/author/reviewer/C/
  driver/model launch, no driver rerun, no frozen repair, no runtime
  deletion/mutation, no benchmark/retrieval/protected access including
  git-object-scan (`git show`/`cat-file`/`checkout`/`restore`/sparse/worktree 0),
  no ref creation, no history rewrite, no Desktop/browser/computer.

## 1. Execution-extent correction (supersedes D-093 extent reading as stated)

- D-093 durable narrative (text left untouched; superseded ONLY as stated here):
  Author-1 `f1d2e97e-4b22-432d-823c-ace7d7242989` launched top-level and ended
  `Status=error`, transcript ends `[System Error] Interrupted by user
  (stopReason=aborted, model=opencode-go/muse-spark-1.3-contributor)`;
  "no author2/reviewers/C/selector launches completed".
- Corrected extent (Web-observed authoritative evidence):
  - Execute toolResult rc=3 is authoritative:
    `author2: agent status='running' not terminal-idle`.
  - Author-1 staging out count = 0; Author-1 was nevertheless followed by an
    Author-2 launch. Frozen driver code order proves it passed
    `wait_idle -> verify_top_level -> require_terminal ->
    wrapper/descendant/audit -> stop_agent` for Author-1, and `stop_agent`
    is literally `paseo stop`.
  - Author-1 OMP timeline: tool results through 21:23:42.233Z, then assistant
    stopReason=aborted 21:23:42.749Z; Author-2 created later at 21:23:54.712Z.
    This establishes the frozen driver stopped Author-1 after a transient idle
    before output completion.
  - Author-2 out count = 0; `paseo wait` returned, then inspect saw it
    `running`, producing the rc=3 above.
  - Post-closure Web safety-stopped the still-running Author-2; recorded as
    containment, not original failure cause.
  - D-093's "no author2 launches completed" is narrowed accordingly: the
    Author-2 launch occurred (creation 21:23:54.712Z); Author-2 never reached
    terminal-idle, which is exactly the rc=3 failure.
  - Both author out dirs had 0 files => no candidate/query rows; same TEN,
    no 11th exclusion.

## 2. Root-cause correction (supersedes D-093 "no cause speculated")

- Paseo `wait --help`: `Wait for an agent to become idle`. Frozen `TERMINAL_OK`
  includes idle and has no output-completeness/quiescence proof before stop.
- Root cause (structural evidence, not speculation): terminal-completion race —
  transient idle was treated as role completion; successful-path stop_agent can
  abort a still-progressing role. The Author-1 abort was the frozen driver's
  own stop_agent after transient idle (tool results 21:23:42.233Z → aborted
  21:23:42.749Z → Author-2 created 21:23:54.712Z), and the execute then failed
  closed at Author-2 with rc=3 (running, not terminal-idle).

## 3. Verdict standing (unchanged)

- D-093 CONTRACT_INVALID_GENERATION plus v9r9 non-resumable/non-repairable
  stands: the single authorized frozen execute was consumed and failed closed
  (rc=3); post-source-truth snapshot/anchors exist, so per standing precedent
  (D-080: snapshot plus anchors exist, so no repair/resume under any
  circumstance) v9r9 MUST NOT be repaired or resumed. A successor, if any,
  still requires a fresh identity/plan under a new decision outside that root.
- D-093 text/history preserved verbatim. The frozen builder, Phase-C root,
  execute coordinator cwd/session, and author staging/sessions are untouched
  and were not accessed in this correction.

## 4. Boundary

- Added this doc plus the DECISIONS `D-094` block plus the SESSION-LOG entry
  ONLY (repo). No frozen mutation; no history rewrite; no ml-service change;
  no audit append; no semantic plaintext logged.
- Forbidden counts 0 in this correction root (generation, second
  execute/author/reviewer/C/driver/model launch, driver rerun, frozen repair,
  runtime deletion/mutation, benchmark/retrieval/protected access including
  git-object-scan, ref creation, D-081..D-093 mutation, D082/D086 reuse beyond
  fingerprints, Desktop/browser/computer).
- STOP. No Phase C and no successor design/freeze in this root.
