# Retrieval v3 D-075 SAME-STAGE correction — v6 pre-result HOLD, v6r1 cwd-binding repair (2026-09-05)

Same-stage narrow durable correction of the D-075 generation-v6 pre-result freeze (`memory/DECISIONS.md` D-075, commit `fe4a9cb`; strategy `docs/RETRIEVAL_V3_D075_GENERATION_V6_STRATEGY.md`).
Plaintext-free: SHAs, counts, timestamps, filenames, structural facts only — no query text, no labels, no id mappings.
D-075 text is preserved verbatim; no new D-number is consumed here.

## 0. Reconciled base (actual wins, this correction session — observed)

- Branch `codex/retrieval-v3-user-search-quality` HEAD `fe4a9cb5e5b4cb8485970ee5fd04d42284d94dc9` clean; local = upstream = direct remote identical; `git diff --check` PASS; `git diff 5327661..HEAD -- ml-service/` 0.
- Frozen six byte-identical: prereg `7842018613d66aa4570f4db2f8ae5a698ceb46757995a6b7e26873177b36160e`, plan-v4 `a25d9c482094696ff7a438593979813ac568c91a977a2543a50618ca4f5177d6`, safe-action `c512fb5627179697a987b05a2431b8f7e30d1153af2ff6dca37995f6b232a35d`, policy-v2 `6fee9ec22d5d3ac153ff19a6b1b5d27ab6a6a43bda11e35821d689f938968fe5`, link-V2 `f028ce4697f1a19e8d37e9048f6d7cd07d87c35ad68478d0efa968b7c62a7e71`, cost-V1 `5891b0bab0621da71499c5c2c6a21a6ac6692bd3ee94d6cb5342adc480958323`.
- Audit `eval/retrieval-v3/audit/events.jsonl` 4 events SHA `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506` byte-identical.
- Canonical v3 result absent; `eval/retrieval-v3/dev/` + `holdout/` absent on main; no dev-v2 branch/tag/worktree created or touched; protected v3 freeze branches/worktrees pre-existing, untouched.
- V6 builder `bc-v3-dev-v2-builder-20260905-v6` frozen bytes verified byte-for-byte before repair: plan 21302 `4e5c869ba1694b48bc84580dd1a6e03fc7c928221e57b1360af3871b373de286`, rubric 3330 `3604105e737e1d87dc39a0a253b8f498750a2103f8e11a47695c43382f48b533`, lock 1312 `f5b09980feba349f7e38b9ca0ba6161664f82c6a4dc8aac57e95fb1749b087cc`; exclusions manifest `5d90c1357ab575cd0e7bc6790bdbd213cd6af52211c378eeb9ad94bd20707a11`, failed_d074 `fde763315b362774875b9142ebad85897363bd2180cce3ee4047281d79ad8d05` 360/360.
- Session model observed: `opencode-go/muse-spark-1.3-contributor`. OMP `18.1.5`; no project override. No child agents through this repair Phase B.

## 1. Web-HOLD finding (authoritative per user instruction)

- Frozen v6 `reviewer_filesystem_confinement` gives each reviewer a staging root and audits explicit paths, but does NOT bind the reviewer process/session effective cwd to that root.
- Actual OMP generic `task` spawn schema has no per-child cwd parameter; a child may inherit the parent repo cwd. Then a relative `ls`/read/bash with no explicit external path can see outside staging and evade a naive explicit-path scan.
- This is substantive to the D074 isolation repair (D074 was counterpart-packet/keymap exposure). V6 therefore enters pre-result HOLD before any execution; v6 bytes are preserved as HOLD evidence and never executed.

## 2. Repair (mechanics only; counts/semantics/exclusions identical to v6)

- New private builder only: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260905-v6r1`. V6 builder never modified.
- Exclusions carried byte-identically from v6 input/ (8 files): manifest `5d90c135` (description still records v6 sets; sets identical), failed_d074 `fde76331` 360/360, D070 `0acc6f27` 273, D071 `3a037d98` 273, D072 `ff3f65d6` 360, dev-v1 `57716c6a` 180q/228g, holdout `3463a8a1` 250q/212g, history `42e8534d` 248q/248g. No D074 semantic read, no source-truth read; D074 fingerprints carried, not re-extracted.
- New identity: plan_version `retrieval-v3-dev-generation-v6r1`; seed `benefit-compass-retrieval-v3-dev-v2-generation-v6r1-2026-09-05`; candidate IDs `v3g6r1-001..v3g6r1-360`. Counts/reserve/all eight authoring semantics/rubric semantics/A-B-C/agreement/selector/exclusions identical to v6. Rubric semantic content identical to v6; metadata version only (`retrieval-v3-dev-generation-v6r1-rubric-v1`).
- Superseded mechanics (only change): A/B reviewers MUST be INDEPENDENT Paseo agents, not generic OMP `task` children, via non-GUI CLI `paseo run --cwd <that reviewer's random staging root> --provider omp/opencode-go/muse-spark-1.3-contributor --thinking xhigh --mode full ...` (or byte-equivalent); brief contains only role + own root/local filenames. Coordinator records each reviewer Paseo agent ID + inspect/session evidence showing ACTUAL cwd == staging root, model muse-spark-1.3-contributor, fallback=false; mismatch => CONTRACT_INVALID_GENERATION. Transcript audit resolves EFFECTIVE paths (pinned staging-root cwd; explicit cwd must resolve inside root; relative resolves against cwd; absolute must stay under root; `..` escape/parent/system/OMP-session/counterpart/keymap/candidate/intended/plan/ledger/author-output/other-root => CONTRACT_INVALID; bash/eval audited for explicit cwd + literals/traversal; no-cwd commands inherit verified staging cwd; desktop/browser/network/connector forbidden). No keymaps before BOTH raw outputs freeze + both cwd/path audits PASS; deterministic reconstruction afterward unchanged. C likewise independent Paseo `--cwd` agent; same-role chunk children audited with the same effective-path rule before merge (parent C cwd = C root); disagreement bundle remains only permitted A/B info. Durable claim: `filesystem-disjoint staging + verified session cwd confinement + no pre-review keymap materialization + transcript effective-path fail-closed gate`; still NO OS-sandbox claim.
- Frozen (`freeze_plan.py`, canonical single-line bytes + LF): `GENERATION_PLAN.json` 22314 bytes SHA `9bc432648576189affb9333aa5dfaaf2d1f58b387da56f02676aaf01b073cf64`; `RUBRIC.json` 3334 bytes SHA `6e7b0cd97b54c8c001843338da8ac39ea99827344e81babadfb20194197bdb78` (semantics identical to v6 `3604105e`, version-only change); `PLAN_LOCK.json` 1378 bytes SHA `c7cbd156d9583089f9b855ebc89e314a8ee2580572e501409494f964746b1b3f` (source_truth false, v6-source-truth-not-read false, v6r1-source-truth-not-read false, d070/d071/d072/d074 semantic false, protected_old false, D074 fingerprints carried recorded). V6 base verified identical before use.

## 3. Disposition

- V6 plan/rubric/lock remain preserved HOLD evidence (never executed, never mutated). V6r1 is the only authorized pre-result plan going forward; it is likewise frozen before source truth and immutable afterward.
- D-075 text/history preserved verbatim; this correction consumes no new D-number. D-075 strategy doc untouched.

## 4. Mutation boundary, forbidden counts, next gate

- Added in this stage: this doc + DECISIONS same-stage correction block + SESSION-LOG entry. V6r1 builder: exclusions + scripts + frozen plan/rubric/lock only; `source_truth.jsonl` ABSENT; candidates ABSENT; staging roots NOT created yet.
- No source-truth snapshot, no candidate generation, no A/B/C, no selector, no benchmark/retrieval/ranking/latency/HTTP/model-encode, no D068 retry/audit append/result, no protected plaintext/recovery/git-show/cat-file/checkout/restore/sparse/worktree, no protected branch/tag/worktree/import, no ml-service change, no history rewrite, no D074 row reuse beyond carried fingerprints.
- Forbidden counts all 0. STOP for Web independent review. Phase C requires Web review/user continuation and is NOT authorized here.
