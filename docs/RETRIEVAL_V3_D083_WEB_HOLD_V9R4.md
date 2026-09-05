# Retrieval v3 D-083 Web-HOLD — generation-v9r4 two blockers (2026-09-06)

New logical stage: v9r4 Web-HOLD closure ONLY. v9r4 bytes preserved untouched as
Web-HOLD evidence — never executed, repaired, resumed, or reused. No source truth,
no authors/reviewers/C/selector/benchmark/protected actions in this stage.
Plaintext-free: SHAs, counts, timestamps, filenames, structural facts only — no query
text, no labels, no id-to-text mappings, no agreement values.

## 0. Reconciled base (actual wins, this HOLD session — observed)

- Branch `codex/retrieval-v3-user-search-quality` HEAD `1013a7f133b947291e855405b795256a2498411f`
  clean; local = upstream = direct remote identical; `git diff --check` PASS;
  `git diff HEAD -- ml-service/` 0.
- OMP `18.1.5`; `modelRoles` default/plan `opencode-go/muse-spark-1.3-contributor:xhigh` (ROOT),
  task Luna xhigh, review Luna max; no project model override.
- v9r4 builder preserved byte-identical (plan 39610 `0aea725f…`, rubric 3334 `08e598a4…`,
  lock 7631 `aad284f1…`); audit `eval/retrieval-v3/audit/events.jsonl` 4 events SHA
  `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506` (no append).
- Canonical v3 result absent; `eval/retrieval-v3/dev/` + `holdout/` + `dev-v2/` absent; no dev-v2
  branch/tag/worktree; protected v3 freeze branches untouched.
- Frozen six byte-identical by clean-tree inheritance (prereg `78420186…`, plan-v4 `a25d9c48…`,
  safe-action `c512fb56…`, policy-v2 `6fee9ec2…`, link-V2 `f028ce46…`, cost-V1 `5891b0ba…`).
- No child agents in this HOLD session. `git cat-file` / `show` / `checkout` / `restore` / sparse /
  worktree count 0. Generation / A-B-C / selector / benchmark / protected-access / source-snapshot
  execution count 0. No Desktop/browser/computer use.

## 1. Blocker 1 — validate_pool nine-set omission (observed, structural)

- v9r4 `validate_pool.py` L144 loads `failed_d082_query_fingerprints.json` into `d082`,
  but the operative overlap loop (L146–147) checks eight sets only
  (`dev_v1, holdout, history, d070, d071, d072, d074, d076`) — `("d082", d082)` absent.
- Effect class: a D082 query fingerprint present in the candidate pool passes the pool gate
  silently. `check_anchor.py` (d082 in query_overlap sets) and `run_selector.py`
  (`d082_q` in the union gate) already enforce d082; only the pool gate omits it.
- Proven by a permanent regression test (v9r5 `test_nine_set_gates.py`, fingerprint-only):
  run with `--builder` pointed at the v9r4 tree it fails
  `loop gates [dev_v1 … d076] != nine […, d082]`; pointed at v9r5 it passes
  (operative nine + d082-only probe reported + 36/36 pairs overlap 0).

## 2. Blocker 2 — packet exact bytes not frozen (observed, structural)

- v9r4 `freeze_raw_ab.py` reads staging `packet.jsonl` for chunk-order checks only; it never
  copies packet bytes into `frozen_raw_A/B/` and pins no packet SHA in
  `raw_freeze_manifest.json`.
- v9r4 `reconstruct_keymaps.py` rehashes frozen chunks, then verifies packet order/queries
  and writes keymaps — with no frozen-vs-staging packet rehash and no regenerated-byte check,
  so a post-freeze packet rewrite is not fail-closed at keymap time.
- v9r4 `merge_raw_ab.py` rehashes frozen + staging chunks only, never packets.
- Reviewer raw schema itself is sound (exact eight fields, no `query_text`, fail-closed
  `SCHEMA_VIOLATION`) and is preserved unchanged.

## 3. Disposition

Verdict: v9r4 Web-HOLD. v9r4 MUST NOT be executed, repaired, resumed, or reused.
Repair is a fresh v9r5 pre-result freeze (D-084): nine-set pool-gate enforcement plus packet
exact-bytes freeze (freeze/copy/pin; rehash frozen+staging chunks and packets plus regenerated
expected-byte equality before any keymap write; rehash again at merge). Added in this stage:
this doc + DECISIONS `D-083-HOLD` block + SESSION-LOG entry (repo). No D-084 execution here.
Forbidden counts all 0: v9r4 repair/resume/reuse, generation, A/B/C/selector, benchmark,
plaintext logging, protected access incl. git-object-scan, ref creation, ml-service change,
history rewrite, D-081/v9/v9r1/v9r2/v9r3/D-083 mutation, D082 aggregate reuse beyond
fingerprints, Desktop/browser/computer use.
