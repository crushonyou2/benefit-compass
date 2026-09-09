# Retrieval v3 D-155 — generation-v9r24 Phase-C CONTRACT_INVALID_GENERATION

Date: 2026-09-09
Stage: exactly-once Phase-C execution closure
Generation: `retrieval-v3-dev-generation-v9r24`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260909-v9r24`
D-154 pre-execution base commit: `4465db127ffc98ffbded7b63dc59016f8c1663ba`

## Verdict

**v9r24 = HARD HOLD / CONTRACT_INVALID_GENERATION / NON-RESUMABLE / NON-REPAIRABLE.** The D-154-authorized frozen Phase-C execute was consumed exactly once. The fresh source-truth snapshot, anchors/slots, both Author roles, the 360-row pool merge + FOURTEEN validation, both Reviewer stagings, and Reviewer A execution all completed. The frozen Reviewer A role-access audit then fail-closed before any Reviewer B launch, C launch, selector, protected evaluation, holdout, production, or canonical audit append.

The canonical frozen coordinator result is:

`phasec_execute: driver nonzero exit rc=3 ... {"verdict":"CONTRACT_INVALID_GENERATION","error":"reviewerA: role access audit FAIL rc=3 ... access log deny present line 2: role_read_resource/DENY:unknown-resource: bad resource 'reviewer_packet'..."}`

No retry, resume, run-lock removal, frozen-byte patch, manual access-log repair, manual Reviewer B/C launch, selector, second coordinator, or same-generation repair is permitted.

## Fresh execution base

Immediately before the sole execute launch (read-only reconcile):

- branch `codex/retrieval-v3-user-search-quality`
- base `4465db127ffc98ffbded7b63dc59016f8c1663ba`; direct origin independently verified at `4465db127` before closure
- canonical audit 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`, historical event chain unchanged (`ce5f9b3d` / `cf828cb9` / `c5d887c4` / `af724908`)
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/dev-v2/`, `eval/retrieval-v3/holdout/` absent
- immutable `PLAN_LOCK.json` 27,412B SHA `d084914f...1730b` / `FROZEN_HASHES.json` 7,965B SHA `056e789c...85e62d` / plan 73,596B SHA `ce6b55d1...f832c05` + rubric SHA `08e598a4...b02fe` (D-153 sizes exact)
- production `ml-service/` untouched (tree mtimes 1w, no D-155 change)
- v9r24 run lock / source truth / Phase-C root / execute root / session all absent at the freshness gate

Tooling note (no contract effect): the exec adapter failed closed during the reconcile half of this stage (missing Click gate hook), so the pre-launch reconcile used read-only file tools only — directory listings (names/sizes/mtimes), small metadata files, structural session/access-log parsing — and the process reloaded onto the installed adapter before closure application. No semantic candidate/query content and no protected evaluation content was read at any point. Frozen/driver-written metadata SHAs are quoted from those artifacts, not recomputed here.

## Executor provenance correction and sole stage owner

Two repo-cwd executor records exist; exactly one of them owns this stage:

- `86d2c5d5-7672-4dbd-a0dd-7889fe008c1a` (`D155 v9r24 Phase-C execute executor`, created `2026-09-09T04:31:15.409Z`, idle/finished) is a **wrong-model non-consuming record**: its config/model is `anthropic/claude-3-5-sonnet-20240620`, and its 8-line session ends in an assistant `404 model not_found` error with zero tokens and **zero tool calls**. It launched nothing, consumed nothing, and is preserved as provenance correction only.
- `d87e6ca0-cb44-4032-8056-0e088b1d4833` (`D155 v9r24 Phase-C execute executor corrected`, created `2026-09-09T04:32:02.216Z`, running, omp / `opencode-go/muse-spark-1.3-contributor` / xhigh / full, repo cwd) is the **actual sole stage owner** and the author of this closure, with no subagent.

## Sole D-155 stage execution and exactly-one coordinator launch

The corrected executor performed the single one-shot launch via the frozen launcher (`execute` mode, brand-new empty cwd, neutral prompt):

`Call phasec_execute exactly once with {}. Do not call phasec_probe. After the phasec_execute result, stop. Do not use any other tool except todo if needed.`

The sole frozen execute coordinator is:

- agent `8a40af85-8742-438a-9bfb-62f2176945f1`
- title `D155 v9r24 Phase-C execute` (exact-title registry count = 1; no second coordinator)
- cwd `C:\Users\joji\bc-v3-v9r24-coord-execute-20260909\cwd`
- provider/model `omp` / `opencode-go/muse-spark-1.3-contributor`, thinking `xhigh`, mode `full`, final idle/finished
- session `...-bc-v3-v9r24-coord-execute-20260909-cwd/2026-09-09T04-35-02-098Z_01a08472-a952-7360-9f76-64fd6a239653.jsonl`, 10 lines / 9.9KB: model_change `parentId null`, `resolvedModelIsFallback false`; exactly one `phasec_execute` toolCall (caller intent `Executing Phase-C driver`, which the frozen driver ignores by design) and exactly one matching toolResult at `2026-09-09T05:09:10.218Z`; final assistant stop report, no relaunch
- wrapper invocation exactly one row (551B): mode `execute`, custom tool `phasec_execute`, built-in tools `todo`, frozen controls `--tools=todo -e --no-extensions --no-skills --no-rules`, coordinator extension SHA256 `f617c25364cc8707aa54f2aeddc16dab351a33e9604efe700929946bffa07575`, real OMP, pid 50748

## Atomic run boundary and frozen-byte preservation

The driver consumed the atomic one-shot boundary exactly once:

- `phasec_driver.run.lock` present, 49B: `{"started": "2026-09-09T04:35:06Z", "pid": 51880}`
- the coordinator toolResult at 05:09:10Z proves driver exit (rc=3); no driver rerun exists
- frozen manifest direct rehash after failure: 81/81 exact
- runtime `__pycache__` byproducts (2 builder pyc + `coord_wrapper_tpl/__pycache__`) are preserved as consumed-run evidence; they are outside the frozen pin payload

## Completed runtime before the reviewerA failure

Fresh generation inputs are preserved (sizes observed; candidate/query content never read):

- `source_truth.jsonl` 71.7MB + `source_truth_meta.json` 789B: 13,589 rows (gov24 10,958 / youth 2,631), SHA256 `9fe194653a4b5c9c688364aa9ae686996cb7cabfebd446a6b9a7e8895374c1a5`, frozen read-only policy-table SQL (`ORDER BY source, source_id`, no vector/chunk/ranking query), snapshot `2026-09-09T04:35:15+00:00`
- `anchors.json` 44.8KB; `slots_1.json` 19.6KB; `slots_2.json` 19.9KB
- `author_chunks/` 12 chunks; collected `author1_candidates.jsonl` 55.8KB / `author2_candidates.jsonl` 103.8KB
- `candidates_merged.json` 159.5KB present: the mandatory pool merge + FOURTEEN validation **PASSED** (v9r23's STRUCTURAL_FAIL boundary is cleared; no content claim beyond presence/size)
- Reviewer A and B stagings prepared with `packet.jsonl` 43.0KB each (360 rows per the reviewerA access log), `source_truth.jsonl`, `RUBRIC.json`, `reviewer_brief.md`
- Reviewer A launched exactly once: wrapper one row (469B), role `reviewerA`, role extension SHA256 `11aa4634ffe3b4c662a5ebaa23c32b37707f5d40ece4197bef158b1416cbc402`, pid 61488; session exactly one file (`2026-09-09T05-02-49-817Z_01a0848c-...jsonl`, 915.9KB, content never read); `out/` holds all six final chunks (`chunk_0..5.jsonl`); access log 15.1KB
- Reviewer B staging prepared but **never launched** (no wrapper invocation log, no access log)

Only these Phase-C role agents exist: author1, author2, reviewerA. Adjudicator C count is zero.

## Exact role-access-audit failure boundary

The frozen role-access auditor fail-closed on Reviewer A's access log, which carries exactly three DENYs against otherwise-completing work:

1. `role_read_resource` `reviewer_packet` — `DENY:unknown-resource: bad resource 'reviewer_packet'` (access-log line 2; the auditor's cited fatal)
2. `role_write_chunk` `out/chunk_0.jsonl` — `DENY:shape: line 57 not json` (later rewritten OK, 60 rows)
3. `role_write_chunk` `out/chunk_2.jsonl` — `DENY:shape: chunk id/order mismatch` (later rewritten OK, 60 rows)

Deny 1 is a reader-side unknown-resource request for a name the frozen reviewer surface never stages (the staged packet file is `packet.jsonl`, which the role later read successfully at 360 rows). Denies 2–3 are transient shape rejections the role self-repaired before final-stop. The frozen auditor treats any deny as fatal, so the first deny alone terminally closed the run even though all six final chunks landed. This closure does not reinterpret the audit as a bug and authorizes no same-generation repair.

## Downstream zero-state after failure

Because the audit failed before raw-freeze/merge, the run left:

- no Adjudicator C root, agent, session, keymap, or adjudicated pool
- no raw A/B freeze, keymaps, agreement/disagreement artifacts
- no selector/final evalset, no `sealed/` outputs
- protected dev-v2 evaluation absent; holdout evaluation absent
- production `ml-service/` change 0
- canonical audit remains 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`, content unchanged

## Independent post-failure review

A separate read-only reviewer independently verified the terminal state and returned **FINAL CONTRACT_INVALID / HARD HOLD**: terminal `CONTRACT_INVALID_GENERATION` rc=3 on the reviewerA role-access audit with the three-DENY boundary above (unknown-resource `reviewer_packet`; chunk_0 line-57 non-JSON; chunk_2 id/order mismatch); exactly one coordinator with exactly one `phasec_execute` call/result; run lock and all evidence preserved; zero downstream/protected/prod/audit change. It performed no rerun, mutation, protected access, or agent messaging.

## Closure / successor boundary

V9r24 is permanently closed as `CONTRACT_INVALID_GENERATION`. Preserve the immutable freeze artifacts, run lock, source-truth snapshot + meta, anchors/slots, Phase-C roots, Author/Reviewer-A sessions/wrappers/access logs/chunks/packets, collected candidate files, merged pool, coordinator/stage-executor sessions, runtime caches, and every current failure artifact in place.

Do not retry or resume the driver, delete/recreate the run lock, patch frozen bytes, edit failed Reviewer rows, manually freeze/merge the pool, launch Reviewer B/C, run selector, or launch a second execute coordinator for v9r24.

A future successor, if authorized by a separate user `진행해`, is a **fresh logical stage and fresh generation identity only** after reconciling standing failed-generation freshness/provenance rules. This D-155 closure does not yet decide successor repairs (reviewer-surface resource vocabulary, writer-envelope shape discipline), quota/selector changes, or any protected evaluation. Protected dev-v2, holdout, production change, and canonical audit append remain prohibited.
