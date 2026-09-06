# Retrieval v3 D-098 D-097 post-commit provenance correction (2026-09-06)

Append-only durable correction of D-097 verification provenance. D-097 and all
earlier durable records remain verbatim. This correction records one process
violation that occurred after the D-097 commit/push; it does not change the
v9r11 execution verdict, builder bytes, smoke evidence, or product code.
Plaintext-free: commit IDs, command identity, file paths, counts, and structural
facts only -- no protected query/gold plaintext.

## 0. Reconciled base (actual wins)

- Branch `codex/retrieval-v3-user-search-quality`, HEAD
  `6f9fa61764e0aa2bdd3784dc30d2998595339433` (D-097), clean; local = upstream =
  direct remote identical; `git diff --check` PASS; production `ml-service/`
  diff from `5327661445c37191a3fd61db195f3af4d2cf893a` = 0.
- OMP `18.1.5`; effective modelRoles default/plan
  `opencode-go/muse-spark-1.3-contributor:xhigh`.
- Audit `eval/retrieval-v3/audit/events.jsonl`: exactly 4 events, SHA256
  `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`.
- Canonical `eval/retrieval-v3/result`, `dev`, `holdout`, and `dev-v2` absent.
- Durable SSOT ended at D-097 before this correction. `memory/00-INDEX.md` does
  not enumerate individual D-09x closure/correction documents, so it remains
  unchanged under current repository convention.

## 1. Exact post-commit provenance correction

After D-097 commit `6f9fa61764e0aa2bdd3784dc30d2998595339433` was created and pushed,
and after the normal local/upstream/direct-remote checks, the Web prime issued
exactly one forbidden command during final verification:

`git show --stat HEAD`

Observed output was limited to the current D-097 docs-only commit summary/stat:

- `docs/RETRIEVAL_V3_D097_V9R11_CONTRACT_INVALID_GENERATION.md` -- 157 additions;
- `memory/DECISIONS.md` -- 12 additions;
- `memory/SESSION-LOG.md` -- 10 additions;
- total: 3 files changed, 179 insertions.

This was a process/provenance contract violation because the D-097 authorizing
prompt explicitly prohibited `git show`. It occurred only after the D-097
closure commit/push and did not mutate the repository, private v9r11 builder,
smoke staging, or sessions.

D-097 lines 124-126 are therefore superseded only as follows:

- The statement that no `git show` was used is false for the full D-097 closure
  chronology after post-commit verification.
- Correct chronology: no protected-data reconstruction or protected-path
  recovery occurred; no `git cat-file`, checkout/restore, sparse/worktree
  traversal, or protected-data object/path scan occurred; exactly one
  `git show --stat HEAD` was nevertheless issued post-commit, limited to the
  current D-097 docs-only commit summary/stat above.
- The command did not expose protected plaintext, protected refs, dev/holdout
  files, source-truth data, candidate rows, or runtime semantic artifacts.

No attempt is made to erase, downgrade, or retroactively relabel the violation.
It is preserved here append-only.

## 2. Verdict impact

The provenance correction does **not** alter the substantive v9r11 verdict:

**generation-v9r11 = HARD HOLD / CONTRACT_INVALID_GENERATION / NON-RESUMABLE /
NON-REPAIRABLE.**

The verified execution cause remains the generic role-launcher wrapper PATH
reachability defect recorded in D-097. Smoke A remains consumed/PASS; Smoke B
remains consumed/CONTRACT_INVALID_GENERATION; no retry, same-generation repair,
real freeze, Phase C, Author/Reviewer/C, selector/dev-v2, protected evaluation,
holdout, or production retriever change is authorized or performed here.

The v9r11 private builder plus Smoke A/B staging/session evidence remain failure
evidence and are not modified by this correction.

## 3. Durable boundary

This correction adds only this document plus an append-only D-098 block in
`memory/DECISIONS.md` and an append-only D-098 entry in
`memory/SESSION-LOG.md`. D-097 itself remains byte-for-byte unchanged.
`memory/00-INDEX.md` remains unchanged by current convention. No `ml-service/`
change and no audit append.

No successor generation is designed, implemented, frozen, or smoked in D-098.
After this correction commit/push is verified without another prohibited
`git show`, the D-097/D-098 durable closure is complete and the next logical
stage may start only as a fresh successor generation/fresh private builder from
read-only reconciliation, preserving v9r11 unchanged as failure evidence.
