# Retrieval v3 D-084 generation-v9r5 PRE-RESULT freeze (2026-09-06)

New logical stage: generation-v9r5 pre-result freeze ONLY — Web-HOLD repair of the two
D-083-HOLD blockers (pool nine-set omission + packet bytes unfrozen). No source truth,
no authors/reviewers/C/selector/benchmark/protected actions in this stage.
Plaintext-free: SHAs, counts, timestamps, filenames, structural facts only — no query text,
no labels, no id-to-text mappings, no agreement values.

## 0. Reconciled base (actual wins, this freeze session — observed)

- Branch `codex/retrieval-v3-user-search-quality` HEAD `465baa3a3849925c33e9c5cfa8dbb012f609714a`
  (D-083-HOLD) clean; local = upstream = direct remote identical;
  `git diff --check` PASS; `git diff HEAD -- ml-service/` 0.
- OMP `18.1.5`; `modelRoles` default/plan `opencode-go/muse-spark-1.3-contributor:xhigh` (ROOT),
  task Luna xhigh, review Luna max; no project model override.
- v9r4 builder preserved byte-identical as Web-HOLD evidence (plan 39610 `0aea725f…`, rubric 3334
  `08e598a4…`, lock 7631 `aad284f1…`); audit `eval/retrieval-v3/audit/events.jsonl` 4 events SHA
  `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506` (no append).
- Frozen six byte-identical by clean-tree inheritance (prereg `78420186…`, plan-v4 `a25d9c48…`,
  safe-action `c512fb56…`, policy-v2 `6fee9ec2…`, link-V2 `f028ce46…`, cost-V1 `5891b0ba…`).
- Canonical v3 result absent; `eval/retrieval-v3/dev/` + `holdout/` + `dev-v2/` absent; no dev-v2
  branch/tag/worktree; protected v3 freeze branches untouched.
- No child agents in this freeze session. `git cat-file` / `show` / `checkout` / `restore` / sparse /
  worktree count 0. Generation / A-B-C / selector / benchmark / protected-access / source-snapshot
  execution count 0. No Desktop/browser/computer use.

## 1. Inputs carried (fingerprint-only, zero plaintext)

- Nine fingerprint sets carried byte-identically from v9r4 `input/` (verified SHA-equal):
  failed-D070 273 `0acc6f27…`, D071 273 `3a037d98…`, D072 360 `ff3f65d6…`, D074 360 `fde76331…`,
  D076 365 `3feaab4d…`, D082 360/unique 360 `1315b34a…` (hash-only, queries otherwise nonreusable),
  dev-v1 180 q / 228 g `57716c6a…`, holdout 250 q / 212 g `3463a8a1…`, history union 248 q / 248 g
  `42e8534d…`. Nine query sets pairwise overlap 0 (36/36); gold 3-set exclusions unchanged.
- 21 mechanics SHA-pinned in lock (carry/freeze renamed, `test_nine_set_gates.py` added):

| file | bytes | SHA256 |
|---|---|---|
| `launch_top_level_paseo.py` | 16821 | `4edbb8de…` (label only) |
| `search_snapshot.py` | 1708 | `36e135d8…` (label only) |
| `check_anchor.py` | 3157 | `8e61219b…` (label only) |
| `validate_pool.py` | 14136 | `f70b436b…` (NINE sets) |
| `merge_chunks.py` | 1467 | `15204c83…` (label only) |
| `make_anchors.py` | 2147 | `eef03a17…` (label only) |
| `build_packets_ab.py` | 3737 | `794e3f5f…` (seed + IDs) |
| `build_packets_c.py` | 3214 | `e633f79d…` (seed + IDs) |
| `merge_raw_ab.py` | 5204 | `c6a674ad…` (packet rehash) |
| `freeze_raw_ab.py` | 5543 | `3f1306b7…` (packet freeze) |
| `build_agreement.py` | 6164 | `bb39d817…` (label only) |
| `merge_c.py` | 5001 | `5d2141e6…` (label only) |
| `reconstruct_keymaps.py` | 6125 | `7e803020…` (packet gates) |
| `run_selector.py` | 17352 | `2e708d95…` (identity refs) |
| `take_snapshot.py` | 3372 | `1c653987…` (label only) |
| `author_brief.md` | 9400 | `98abdaf5…` (NINE sets + IDs) |
| `reviewer_brief.md` | 4366 | `007a9c6b…` (IDs only; schema unchanged) |
| `c_brief.md` | 3164 | `a2f00c0d…` (IDs only) |
| `carry_exclusions_v9r5.py` | 2824 | `09dca901…` (9-file carry) |
| `freeze_plan_v9r5.py` | 21963 | `7578fd7a…` (real freeze) |
| `test_nine_set_gates.py` | 5618 | `f07c505b…` (new) |

## 2. Web-HOLD repair vs v9r4 (only delta; all numerics/semantics/gates otherwise identical)

- Blocker 1: `validate_pool` operative overlap loop now checks all NINE sets
  (`("d082", d082)` added; d082 was loaded but unchecked in v9r4). Permanent regression
  `test_nine_set_gates.py`: operative-loop AST nine-name assertion + d082-only probe functional
  check + 36/36 pairwise overlap + sibling-gate d082 references. Fails on v9r4 bytes, passes on v9r5.
- Blocker 2: packet exact-bytes freeze. `freeze_raw_ab` copies `packet.jsonl` per role into
  `frozen_raw_A/B/` and pins its SHA in `raw_freeze_manifest.json` alongside the six chunks.
  `reconstruct_keymaps` before ANY keymap write rehashes frozen+staging chunks AND frozen+staging
  packets against the manifest, regenerates deterministic expected packet bytes from seed+candidates
  (byte-identical construction to `build_packets_ab.py`) and requires frozen and staging packet
  bytes to equal them EXACTLY; `merge_raw_ab` rehashes frozen+staging chunks and packets again.
  Any packet/chunk mutation after freeze => rehash/byte mismatch => `CONTRACT_INVALID_GENERATION`.
- Reviewer raw schema exactly eight fields
  `item_id,stratum,location_bearing,labelable,source_truth_answerable,ambiguous,ambiguity_type,golds`;
  no `query_text` or extras (enforced fail-closed; unchanged).
- Launcher preserved: exact-dir derivation + first-3-lines + fallback-literal-false + bounded polling +
  no global scan unchanged (`rglob` absent); v9r5 helper normalized-equivalent to v9r4 (`906f379b…`
  → `4edbb8de…`, docstring L1 only).
- Prompts carry v9r5 IDs with fresh-staging placeholders. 14 rename-only files verified
  normalized-equivalent to v9r4 (token replace only, zero semantic drift).
- Plan parity v9r4→v9r5: 55 diff leaves, all within the identity/nine-set/packet/lifecycle
  allowlist (version/seed/IDs, exclusion manifest SHA, lifecycle + keymap + confinement + agreement
  packet texts, lineage notes/supersedes, 21 mechanics SHAs). Counts/reserve/location, 8 authoring
  semantics, rubric semantics, A/B-360, C-every-360, agreement, exact selector algorithm,
  candidate-plan gates identical.

## 3. Verification (this stage, hashes/counts/structure only)

- `py_compile` all 18 scripts PASS; plan/lock/rubric/seed/version binding PASS
  (`run_selector.load_plan_binding` contract re-verified offline: plan `7242dcce…`).
- Frozen: plan 41147 SHA `7242dcce761130545789ee79a9759ba722523e31edc3a554acb53eb6b0154da4`,
  rubric 3334 SHA `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
  (semantics identical to v9r4), lock 8411 SHA `fe17866eb53726a5fcd9ec7b896570ebdff00b2a4909fe05dd8249ad253dd75c`
  (`frozen_at` `2026-09-05T17:04:15+00:00` truthful observed; source_truth false; 21 mechanics pinned),
  manifest 2056 SHA `d4df299f184ef466fb12edd5e8fc1d1cf299cfb682a5779f20b80b7c3a3e92c5` (NINE gates).
- `test_nine_set_gates.py` PASS on v9r5 (operative nine, d082 probe hit, clean probe miss,
  36/36 overlap 0, counts dev 180 / holdout 250 / history 248 / d070 273 / d071 273 / d072 360 /
  d074 360 / d076 365 / d082 360); FAILS on v9r4 bytes as designed.
- Neutral synthetic lifecycle test (placeholder rows only, temp dirs, 11 cases): build + freeze
  (chunks + packet pinned) + attest + reconstruct + merge-360 happy PASS; staging-packet-mutation
  fails; frozen-packet-mutation fails; staging-chunk-mutation fails; frozen-chunk-mutation fails;
  `query_text`-in-raw rejected; missing `--audits-pass` fails; merge-after-packet-mutation fails.
  ALL PASS.
- Builder inventory (30 entries) and §0 absence list verified. No new source truth accessed; v9r5
  source truth absent.
- Forbidden counts all 0: authors/reviewers/C/selector/benchmark/protected-access/source-snapshot
  execution, query plaintext logging, protected plaintext/recovery/`git cat-file`/`show`/`checkout`/
  `restore`/sparse/worktree, ref creation, `ml-service` change, history rewrite, D-081/v9/v9r1/v9r2/
  v9r3/v9r4-record mutation, D082 aggregate reuse beyond fingerprints, Desktop/browser/computer use.

## 4. Disposition

Verdict: D-084 generation-v9r5 PRE-RESULT freeze complete. Added in this stage: this doc + DECISIONS
`D-084` block + SESSION-LOG entry (repo); v9r5 builder (private dir only). STOP for Web independent
review. Phase C execution requires Web review/user continuation and is NOT authorized here.
