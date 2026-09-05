# Retrieval v3 D-096 D-095 post-smoke root-cause correction (2026-09-06)

Append-only durable correction. The D-095 closure doc, the D-095
DECISIONS entry, and the D-095 SESSION-LOG entry are preserved verbatim.
Plaintext-free: IDs, timestamps, counts, status strings, paths, and
structural facts only — no query/gold semantic plaintext.

Authorization chain (all received in this root, repo docs only from here):
D-095 docs-only closure (two authorized smokes recorded PASS, Web
post-smoke verdict CONTRACT_INVALID recorded as received with no reasoning
invented) → user-supplied authoritative D-095 post-smoke root cause in this
D-096 root (recorded verbatim below as authoritative, no downgrade) →
D-096 repo docs-only append-only correction, and only this. No successor
repair in this stage.

## 0. Reconciled base (actual wins, observed in this correction root)

- Branch `codex/retrieval-v3-user-search-quality` HEAD
  `1ac29048c04340cefe8b6344cba17b385feba208` (D-095) clean;
  local = upstream = direct remote identical; `git diff --check` PASS;
  `git diff HEAD -- ml-service/` 0.
- OMP `18.1.5`; modelRoles default/plan
  `opencode-go/muse-spark-1.3-contributor:xhigh` (runtime context, no override).
- Audit `eval/retrieval-v3/audit/events.jsonl` 4 events SHA
  `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
  (no append).
- Canonical v3 result/dev/holdout/dev-v2 absent; no dev-v2 branch/tag/worktree.
- This correction root performed no freeze, no repair, no smoke launch/retry,
  no v9r10 byte change, no Phase C generation (no authors/reviewers/C/selector),
  no runtime deletion/mutation, no benchmark/retrieval/protected access
  including git-object-scan (`git show`/`cat-file`/`checkout`/`restore`/
  sparse/worktree 0), no new refs, no history rewrite, no
  Desktop/browser/computer. Outside-repo v9r10 builder and both smoke
  stagings/sessions/logs preserved untouched (not accessed in this correction).

## 1. Authoritative post-smoke root cause (user-supplied, recorded verbatim as authoritative)

- Smoke A passed. Smoke B is nevertheless CONTRACT_INVALID_GENERATION
  because the Smoke-B agent violated its explicit filesystem-confinement
  contract: its fresh lifecycle-smoke staging root was declared to be the ONLY
  filesystem scope it may touch, but the actual transcript shows Read accesses
  outside that root, including
  `C:\Users\joji\bc-v3-v9r6-phaseC\launch_author1.txt`,
  `C:\Users\joji\bc-v3-v9r7-phaseC\launch_author1.txt`, and files in the v9r10
  builder.
- The frozen `audit_lifecycle_smoke.py` still returned `LIFECYCLE_SMOKE_PASS`
  because it checked output/session completion, wrapper allowlist, task/hub
  counts, descendants, and provenance, but did not audit or enforce filesystem
  path confinement for read/eval accesses.
- Therefore the Smoke-B PASS was a false positive and v9r10 is
  non-resumable/non-repairable: no freeze, no smoke retry, no v9r10 byte
  repair, and no Phase C.

## 2. What D-095 is corrected to (narrowly, stated only)

- D-095 §2 Smoke-B `LIFECYCLE_SMOKE_PASS` is superseded only as a validity
  claim: the recorded completion/wrapper/task-hub/descendant facts stand as
  observed auditor output, but the PASS is a false positive as a confinement
  proof because path confinement was never audited.
- D-095 §3 `recorded as received; no reasoning invented` is superseded by the
  concrete cause in §1 above. The D-095 verdict itself
  (CONTRACT_INVALID_GENERATION, v9r10 non-resumable/non-repairable, both
  authorized smokes consumed, freeze/repair/retry/byte-change forbidden, no
  Phase C) stands and is now caused, not merely received.
- D-095 text/history otherwise preserved verbatim. No v9r10 builder/smoke
  bytes mutated, moved, or re-read in this correction.

## 3. Boundary

- Added this doc plus the DECISIONS `D-096` block plus the SESSION-LOG entry
  ONLY (repo). No frozen mutation; no history rewrite; no ml-service change;
  no audit append; no semantic plaintext logged.
- Successor repair (e.g. a path-confinement-audited lifecycle gate under a
  fresh identity/plan) is explicitly NOT designed, frozen, or executed in this
  correction stage. It requires a new decision outside this root.
- Forbidden counts 0 in this correction root (freeze, repair, smoke launch or
  retry A/B, v9r10 byte change, Phase C generation incl.
  authors/reviewers/C/selector, runtime deletion/mutation,
  benchmark/retrieval/protected access including git-object-scan, new refs,
  D-081..D-095 mutation, D082/D086 reuse beyond fingerprints,
  Desktop/browser/computer).
- STOP. No Phase C and no successor design/freeze in this root.
