# Retrieval v3 D-085 generation-v9r6 PRE-RESULT freeze (2026-09-06)

New logical stage: generation-v9r6 pre-result freeze ONLY — provenance-order repair
as identity-only successor from v9r5, frozen strictly after D-084-HOLD commit A.
No source truth, no authors/reviewers/C/selector/benchmark/protected actions in this stage.
Plaintext-free: SHAs, counts, timestamps, filenames, structural facts only — no query text,
no labels, no id-to-text mappings, no agreement values.

## 0. Reconciled base (actual wins, this freeze session — observed)

- Branch `codex/retrieval-v3-user-search-quality` HEAD `3d2d19c02c0c00a73aec06c97a7a5d5a0be4e207`
  (D-084-HOLD) clean; local = upstream = direct remote identical;
  `git diff --check` PASS; `git diff HEAD -- ml-service/` 0.
- OMP `18.1.5`; `modelRoles` default/plan `opencode-go/muse-spark-1.3-contributor:xhigh` (ROOT),
  no project model override.
- HOLD base commit A `3d2d19c02c0c00a73aec06c97a7a5d5a0be4e207` committer
  `2026-09-05T17:13:00Z` (`2026-09-06T02:13:00+09:00`).
- v9r5 builder preserved byte-identical as Web-HOLD evidence (plan 41147
  `7242dcce761130545789ee79a9759ba722523e31edc3a554acb53eb6b0154da4`, rubric 3334
  `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`, lock 8411
  `fe17866eb53726a5fcd9ec7b896570ebdff00b2a4909fe05dd8249ad253dd75c`
  `frozen_at` `2026-09-05T17:04:15+00:00`); audit `eval/retrieval-v3/audit/events.jsonl`
  4 events SHA `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506` (no append).
- Frozen six byte-identical by clean-tree inheritance (prereg `78420186…`, plan-v4 `a25d9c48…`,
  safe-action `c512fb56…`, policy-v2 `6fee9ec2…`, link-V2 `f028ce46…`, cost-V1 `5891b0ba…`).
- Canonical v3 result absent; `eval/retrieval-v3/dev/` + `holdout/` + `dev-v2/` absent; no dev-v2
  branch/tag/worktree; protected v3 freeze branches untouched.
- No child agents in this freeze session. `git cat-file` / `show` / `checkout` / `restore` / sparse /
  worktree count 0. Generation / A-B-C / selector / benchmark / protected-access / source-snapshot
  execution count 0. No Desktop/browser/computer use.

## 1. Inputs carried (fingerprint-only, zero plaintext)

- Nine fingerprint sets carried byte-identically from v9r5 `input/` (verified SHA-equal):
  failed-D070 273 `0acc6f27…`, D071 273 `3a037d98…`, D072 360 `ff3f65d6…`, D074 360 `fde76331…`,
  D076 365 `3feaab4d…`, D082 360/unique 360 `1315b34a…` (hash-only, queries otherwise nonreusable),
  dev-v1 180 q / 228 g `57716c6a…`, holdout 250 q / 212 g `3463a8a1…`, history union 248 q / 248 g
  `42e8534d…`. Nine query sets pairwise overlap 0 (36/36); gold 3-set exclusions unchanged.
- 21 mechanics SHA-pinned in lock (carry/freeze renamed, identity tokens only):

| file | bytes | SHA256 |
|---|---|---|
| `launch_top_level_paseo.py` | 16821 | `0ff2984c…` (label only) |
| `search_snapshot.py` | 1708 | `1ce903dd…` (label only) |
| `check_anchor.py` | 3157 | `1c9faf2a…` (label only) |
| `validate_pool.py` | 14136 | `467beb7d…` (NINE sets) |
| `merge_chunks.py` | 1467 | `d3cb2d0a…` (label only) |
| `make_anchors.py` | 2147 | `f85357b9…` (label only) |
| `build_packets_ab.py` | 3737 | `5ed73cff…` (seed + IDs) |
| `build_packets_c.py` | 3214 | `6bf502cd…` (seed + IDs) |
| `merge_raw_ab.py` | 5204 | `7c77a552…` (packet rehash) |
| `freeze_raw_ab.py` | 5543 | `d44b8e0c…` (packet freeze) |
| `build_agreement.py` | 6164 | `5a43a8f5…` (label only) |
| `merge_c.py` | 5001 | `17c8356f…` (label only) |
| `reconstruct_keymaps.py` | 6125 | `e917f2b7…` (packet gates) |
| `run_selector.py` | 17352 | `2148bc32…` (identity refs) |
| `take_snapshot.py` | 3372 | `47f52489…` (label only) |
| `author_brief.md` | 9400 | `4d31695f…` (NINE sets + IDs) |
| `reviewer_brief.md` | 4366 | `77274ade…` (IDs only; schema unchanged) |
| `c_brief.md` | 3164 | `3962263d…` (IDs only) |
| `carry_exclusions_v9r6.py` | 2821 | `cfccebe2…` (9-file carry) |
| `freeze_plan_v9r6.py` | 18782 | `93f3f939…` (real freeze) |
| `test_nine_set_gates.py` | 5618 | `1358b821…` (nine gates) |

## 2. Provenance-order repair vs v9r5 (only delta; all numerics/semantics/gates otherwise identical)

- Identity-only successor: `validate_pool` operative overlap loop still checks all NINE sets
  (no enforcement change); `test_nine_set_gates.py` still fails on v9r4 bytes, passes on v9r6.
- Packet exact-bytes freeze preserved identically: `freeze_raw_ab` copies/pins packet per role;
  `reconstruct_keymaps` rehashes frozen+staging chunks and packets plus regenerated-byte equality
  before any keymap write; `merge_raw_ab` rehashes all again.
- Reviewer raw schema exactly eight fields
  `item_id,stratum,location_bearing,labelable,source_truth_answerable,ambiguous,ambiguity_type,golds`;
  no `query_text` or extras (enforced fail-closed; unchanged).
- Launcher preserved: exact-dir derivation + first-3-lines + fallback-literal-false + bounded polling +
  no global scan unchanged (`rglob` absent); v9r6 helper normalized-equivalent to v9r5 (`4edbb8de…`
  → `0ff2984c…`, docstring L1 only).
- Prompts carry v9r6 IDs with fresh-staging placeholders. 24 rename-only files verified
  normalized-equivalent to v9r5 (token replace only, zero semantic drift; zero leftover v9r5 tokens
  outside intentional lineage).
- Provenance order: freeze strictly after HOLD commit A. Lock records commit A full SHA
  `3d2d19c02c0c00a73aec06c97a7a5d5a0be4e207` (`hold_base_commit_time` `2026-09-05T17:13:00+00:00`)
  and `frozen_at` `2026-09-05T17:16:38+00:00` (3m38s later; `provenance_order` `freeze_after_hold`).
- Plan parity v9r5→v9r6: 37 diff leaves, all within the identity/provenance-order/HOLD/lifecycle
  allowlist (version/seed/IDs, exclusion manifest SHA, HOLD-base + lineage notes/supersedes incl
  `v9r5_note`, 21 mechanics SHAs, stage_forbidden old-builder +v9r5). Counts/reserve/location, 8 authoring
  semantics, rubric semantics, A/B-360, C-every-360, agreement, exact selector algorithm,
  candidate-plan gates identical.

## 3. Verification (this stage, hashes/counts/structure only)

- `py_compile` all 18 scripts PASS; plan/lock/rubric/seed/version binding PASS
  (`run_selector.load_plan_binding` contract re-verified offline: plan `389adaff…`).
- Frozen: plan 41927 SHA `389adaff370d6e46c4c0ba9d8e645100da59e72a000cb02bd8b0436552bed3cb`,
  rubric 3334 SHA `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
  (byte-identical to v9r5), lock 9200 SHA `0715524b4ef6f9a420e3f0452d306281f94243c46cfdca3d5bda0b43771d00aa`
  (`frozen_at` `2026-09-05T17:16:38+00:00` truthful observed, later than HOLD base `17:13:00Z`;
  source_truth false; 21 mechanics pinned; `hold_base_commit` `3d2d19c…`),
  manifest 2031 SHA `d7651f486a6acb784e24fd7bb81ad241ab40021f9e44d90d44c71cda88a38884` (NINE gates).
- `test_nine_set_gates.py` PASS on v9r6 (operative nine, d082 probe hit, clean probe miss,
  36/36 overlap 0, counts dev 180 / holdout 250 / history 248 / d070 273 / d071 273 / d072 360 /
  d074 360 / d076 365 / d082 360); FAILS on v9r4 bytes as designed.
- Neutral synthetic lifecycle test (placeholder rows only, temp dirs, 11 cases): build + freeze
  (chunks + packet pinned) + attest + reconstruct + merge-360 happy PASS; staging-packet-mutation
  fails; frozen-packet-mutation fails; staging-chunk-mutation fails; frozen-chunk-mutation fails;
  `query_text`-in-raw rejected; missing `--audits-pass` fails; merge-after-packet-mutation fails.
  ALL PASS.
- Builder inventory (30 entries) and §0 absence list verified. No new source truth accessed; v9r6
  source truth absent; v9r5 bytes unchanged (plan `7242dcce…` / rubric `08e598a4…` / lock `fe17866e…`).
- Forbidden counts all 0: authors/reviewers/C/selector/benchmark/protected-access/source-snapshot
  execution, query plaintext logging, protected plaintext/recovery/`git cat-file`/`show`/`checkout`/
  `restore`/sparse/worktree, ref creation, `ml-service` change, history rewrite, D-081/v9/v9r1/v9r2/
  v9r3/v9r4/D-083-HOLD/D-084/D-084-HOLD mutation, D082 aggregate reuse beyond fingerprints,
  Desktop/browser/computer use.

## 4. Disposition

Verdict: D-085 generation-v9r6 PRE-RESULT freeze complete. Added in this stage: this doc + DECISIONS
`D-085` block + SESSION-LOG entry (repo); v9r6 builder (private dir only). STOP for Web independent
review. Phase C execution requires Web review/user continuation and is NOT authorized here.
