# Retrieval v3 D-084-HOLD Web-HOLD — generation-v9r5 provenance-order blocker (2026-09-06)

New logical stage: v9r5 Web-HOLD closure ONLY. v9r5 bytes preserved untouched as
Web-HOLD evidence — never executed, repaired, resumed, or reused. No source truth,
no authors/reviewers/C/selector/benchmark/protected actions in this stage.
Plaintext-free: SHAs, counts, timestamps, filenames, structural facts only — no query
text, no labels, no id-to-text mappings, no agreement values.

## 0. Reconciled base (actual wins, this HOLD session — observed)

- Branch `codex/retrieval-v3-user-search-quality` HEAD `787da471b838f2554b9e6523310bd1d8a605e16b`
  clean; local = upstream = direct remote identical (`787da471b838f2554b9e6523310bd1d8a605e16b`);
  `git diff --check` PASS; `git diff HEAD -- ml-service/` 0.
- OMP `18.1.5`; `modelRoles` default/plan `opencode-go/muse-spark-1.3-contributor:xhigh` (ROOT),
  no project model override.
- v9r5 builder preserved byte-identical as Web-HOLD evidence (plan 41147
  `7242dcce761130545789ee79a9759ba722523e31edc3a554acb53eb6b0154da4`,
  rubric 3334 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`,
  lock 8411 `fe17866eb53726a5fcd9ec7b896570ebdff00b2a4909fe05dd8249ad253dd75c`
  `frozen_at` `2026-09-05T17:04:15+00:00`; manifest 2056
  `d4df299f184ef466fb12edd5e8fc1d1cf299cfb682a5779f20b80b7c3a3e92c5` NINE gates);
  audit `eval/retrieval-v3/audit/events.jsonl` 4 events SHA
  `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506` (no append).
- v9r4 builder preserved byte-identical as prior HOLD evidence (plan 39610 `0aea725f…`,
  rubric 3334 `08e598a4…`, lock 7631 `aad284f1…`).
- Frozen six byte-identical by clean-tree inheritance (prereg `78420186…`, plan-v4 `a25d9c48…`,
  safe-action `c512fb56…`, policy-v2 `6fee9ec2…`, link-V2 `f028ce46…`, cost-V1 `5891b0ba…`).
- Canonical v3 result absent; `eval/retrieval-v3/dev/` + `holdout/` + `dev-v2/` absent; no dev-v2
  branch/tag/worktree; protected v3 freeze branches untouched.
- No child agents in this HOLD session. `git cat-file` / `show` / `checkout` / `restore` / sparse /
  worktree count 0. Generation / A-B-C / selector / benchmark / protected-access / source-snapshot
  execution count 0. No Desktop/browser/computer use.

## 1. Blocker — provenance-order violation (observed, structural, chronological)

- v9r5 lock `frozen_at` `2026-09-05T17:04:15Z` (D-084 §3, lock 8411 `fe17866e…`) precedes
  predecessor v9r4 Web-HOLD commit `465baa3a3849925c33e9c5cfa8dbb012f609714a`
  committer time `2026-09-05T17:05:28Z` (`2026-09-06T02:05:28+09:00`).
- D-084 §0 claiming freeze base `465baa3` clean local=upstream=remote is therefore
  chronologically false: at the `frozen_at` instant, `465baa3` did not yet exist on any ref.
- Effect class: pre-result freeze claims lineage from a HOLD closure that postdates it;
  provenance order invalid. v9r5 MUST NOT be executed, repaired, resumed, or reused.
- Permanent correction is a fresh v9r6 identity-only successor frozen strictly after HOLD
  commit A (this stage), with lock recording commit A full SHA and `frozen_at` strictly
  later than commit A committer timestamp.

## 2. Disposition

Verdict: v9r5 Web-HOLD. v9r5 MUST NOT be executed, repaired, resumed, or reused.
Repair is a fresh v9r6 pre-result freeze (D-085): identity-only successor from v9r5
(plan `retrieval-v3-dev-generation-v9r6`, seed `benefit-compass-retrieval-v3-dev-v2-generation-v9r6-2026-09-06`,
IDs `v3g9r6-001..360` / `v9r6c-001..360`; v9r5 numerics/semantics/rubric, nine fingerprint
bytes, operative D082 gate, packet exact-byte freeze/reconstruct/merge, launcher behavior
preserved; no source truth / A-B-C / selector / protected; freeze only after commit A).
Added in this stage: this doc + DECISIONS `D-084-HOLD` block + SESSION-LOG entry (repo).
No D-085 execution here.
Forbidden counts all 0: v9r5 repair/resume/reuse, generation, A/B/C/selector, benchmark,
plaintext logging, protected access incl. git-object-scan, ref creation, ml-service change,
history rewrite, D-081/v9/v9r1/v9r2/v9r3/v9r4/D-083-HOLD/D-084 mutation, D082 aggregate reuse
beyond fingerprints, Desktop/browser/computer use.
