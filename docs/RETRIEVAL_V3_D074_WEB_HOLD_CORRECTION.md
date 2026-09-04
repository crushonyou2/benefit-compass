# Retrieval v3 D-074 SAME-STAGE Web-HOLD correction — CONTRACT_INVALID_GENERATION (2026-09-05)

Same-stage narrow durable correction of the D-074 Phase C execution record (`memory/DECISIONS.md` D-074, commit `e0e1d74`).
Plaintext-free: SHAs, counts, timestamps, filenames, structural facts only — no query text, no labels, no id mappings.
D-074/D-073 text is preserved verbatim; D-075 (future design/freeze) is not consumed and not authorized here.

## 0. Reconciled base (actual wins, this correction session — observed)

- Branch `codex/retrieval-v3-user-search-quality` HEAD `e0e1d74c88a0a569b0d6824359fe5e5737e334fc` clean;
  local = upstream = direct remote (`git ls-remote` identical); `git diff --check` PASS;
  `git diff 5327661..HEAD -- ml-service/` 0.
- Tracked `eval/retrieval-v3/` = modules + pilot/re-audit + candidate-plan only — no dev-v2 generation bytes;
  `eval/retrieval-v3/audit/events.jsonl` unchanged since `7018efc` (clean tree); no dev-v2 branch/tag/worktree
  created or touched; protected v3 dev/holdout freeze branches + worktrees pre-existing, untouched.
- Session model observed: `opencode-go/muse-spark-1.3-contributor`.

## 1. Contract violation (Web-HOLD fact, authoritative per user instruction)

- ReviewerA transcript `2026-09-04T18:07:34.441Z`: a tool call read `packet_A.jsonl` AND `packet_B.jsonl` AND
  `packet_keymap_A.json` AND `packet_keymap_B.json` — BEFORE the first A semantic output write at
  `2026-09-04T18:11:32.845Z`.
- The tool result exposed packet B ids and the first three A/B opaque-id → candidate-id mappings
  (mappings NOT reproduced here).
- The frozen v5 reviewer contract forbids counterpart packet/mappings. Therefore A/B opaque
  independent-annotation provenance is broken. The parent later telling A to continue does not undo exposure.

## 2. Canonical disposition (Web-HOLD fact, authoritative)

- The D-074 canonical verdict `INFEASIBLE_STOP_HOLD` is SUPERSEDED by `CONTRACT_INVALID_GENERATION`
  (effected by `memory/DECISIONS.md` block `D-074-SC`; D-074 text/history and all private v5 bytes preserved).
- C/selector counts (C census, eligible 282/360, shortfalls) remain DIAGNOSTIC ONLY — noncanonical
  feasibility evidence, not evaluation results.
- The D-074 360 rows and their A/B/C rows must never be reused, relabeled, or supplemented in any future
  canonical run.

## 3. Provenance (Web-HOLD fact, authoritative)

- D-074 root had 5 DIRECT child sessions: AuthorOne, AuthorTwo, ReviewerA, ReviewerB, AdjudicatorC.
- AdjudicatorC spawned 6 nested adjudication chunk sessions.
- Actual root-descendant task-session JSONLs = 11 total. All 11 metadata show model
  `opencode-go/muse-spark-1.3-contributor`, agent/modelRole `task`, `resolvedModelIsFallback=false`.
- Nested C chunking itself is not the violation.
- (This corrects D-074's "5 child task agents" phrasing to 5-direct + 6-nested = 11 sessions; D-074 text untouched.)

## 4. Diagnostic-only facts (Web-HOLD fact, authoritative — noncanonical)

- Paired-grounded ambiguous structural checks passed 46/46; C census ambiguous 53.
- Selector diagnostic shortfalls: exploratory eligible 18<21; short loc 3<5; colloquial eligible 19<20;
  colloquial loc 5<6.
- These are NOT canonical evaluation results.

## 5. Mutation boundary, forbidden counts, next gate

- Added in this stage: this doc + DECISIONS `D-074-SC` block + SESSION-LOG entry. Nothing else.
- No dataset / A / B / C / selector rerun; no v5 plan/rubric/lock/private-byte change; no transcript, packet,
  keymap, or builder-byte reads in this session (facts taken as authoritative Web-HOLD input, not re-verified
  by reading protected bytes); no audit event; no protected branch/tag/worktree/import; no history rewrite;
  no D-075 design/freeze.
- Forbidden counts all 0: old-D068-retry, D070/71/72-reuse, audit-append, dev-v2-run, holdout-contact,
  protected-plaintext, plan-mutation, tuning, config-change, ml-service-change, history-rewrite,
  protected-ref-creation.
- STOP for Web independent review.
