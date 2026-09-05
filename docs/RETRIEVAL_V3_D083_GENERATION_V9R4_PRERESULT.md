# Retrieval v3 D-083 generation-v9r4 PRE-RESULT freeze (2026-09-06)

New logical stage: generation-v9r4 pre-result freeze ONLY — mechanics repair of the D-082 failure class
(schema/merge defect + keymap-before-rewrite). No source truth, no authors/reviewers/C/selector/
benchmark/protected actions in this stage.
Plaintext-free: SHAs, counts, timestamps, filenames, structural facts only — no query text, no labels,
no id-to-text mappings, no agreement values.

## 0. Reconciled base (actual wins, this freeze session — observed)

- Branch `codex/retrieval-v3-user-search-quality` HEAD `238ea7601a2af47dd593e81aabd24a9f5dfa05d1`
  clean; local = upstream = direct remote identical (`git rev-parse HEAD` == `@{u}` == `ls-remote`);
  `git diff --check` PASS; `git diff HEAD -- ml-service/` 0.
- OMP `18.1.5`; `modelRoles` default/plan `opencode-go/muse-spark-1.3-contributor:xhigh` (ROOT),
  task Luna xhigh, review Luna max; no project model override.
- Frozen six byte-identical by clean-tree inheritance (prereg `78420186…`, plan-v4 `a25d9c48…`,
  safe-action `c512fb56…`, policy-v2 `6fee9ec2…`, link-V2 `f028ce46…`, cost-V1 `5891b0ba…`); audit
  `eval/retrieval-v3/audit/events.jsonl` 4 events SHA `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
  recomputed match (no append).
- Canonical v3 result absent; `eval/retrieval-v3/dev/` + `holdout/` + `dev-v2/` absent; no dev-v2
  branch/tag/worktree; protected v3 freeze branches untouched.
- No child agents in this freeze session. `git cat-file` / `show` / `checkout` / `restore` / sparse /
  worktree count 0. Generation / A-B-C / selector / benchmark / protected-access / source-snapshot
  execution count 0.

## 1. Inputs carried (fingerprint-only, zero plaintext)

- v9r3 `GENERATION_PLAN.json` 35779 bytes SHA `7b5c47a1e61e24f8f8ec96a20b389a6dcc42002d4d14874c0daf7b64ac8da391`
  + `RUBRIC.json` 3334 bytes SHA `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
  (structure only; SHAs verified before use; bytes never mutated).
- Eight fingerprint sets carried byte-identically from v9r3 `input/`:

| set | file | SHA256 | count |
|---|---|---|---|
| failed D-070 | `failed_d070_query_fingerprints.json` | `0acc6f27…` | 273 |
| failed D-071 | `failed_d071_query_fingerprints.json` | `3a037d98…` | 273 |
| failed D-072 | `failed_d072_query_fingerprints.json` | `ff3f65d6…` | 360 |
| failed D-074 | `failed_d074_query_fingerprints.json` | `fde76331…` | 360 |
| failed D-076 | `failed_d076_query_fingerprints.json` | `3feaab4d…` | 365 |
| dev v1 | `dev_v1_fingerprints.json` | `57716c6a…` | 180 q / 228 g |
| holdout | `holdout_fingerprints.json` | `3463a8a1…` | 250 q / 212 g |
| history union | `history_catalog.json` | `42e8534d…` | 248 q / 248 g |

- Ninth set (hash-only): D082 `failed_d082_query_fingerprints.json` 360 hashes sorted, count = unique = 360,
  file SHA `1315b34a0b9c08b332774e22d826ef427512158ba4c177c699d511567a338e83`; D082 summary file SHA
  `f2d4c6c482e7c3761fa94eeb2622bf0edcbb6a4c89ddb615869b1f75f156ea59` (aggregates only).
  D082 queries remain nonreusable except these fingerprints.
- 20 mechanics SHA-pinned in lock (carry/freeze renamed, `freeze_raw_ab.py` added):

| file | bytes | SHA256 |
|---|---|---|
| `launch_top_level_paseo.py` | 16821 | `906f379b…` |
| `search_snapshot.py` | 1708 | `e7976aab…` (label only) |
| `check_anchor.py` | 3157 | `8e38a09a…` |
| `validate_pool.py` | 14096 | `5effb4d9…` |
| `merge_chunks.py` | 1467 | `b32238c7…` (IDs + path) |
| `make_anchors.py` | 2147 | `debe9f6c…` (IDs + path) |
| `build_packets_ab.py` | 3737 | `d5c4f14c…` (seed + `--builder` opt) |
| `build_packets_c.py` | 3214 | `cf2f50bb…` (seed + IDs) |
| `merge_raw_ab.py` | 4647 | `3e9f3629…` (rewrite) |
| `freeze_raw_ab.py` | 5130 | `4ae00cd6…` (new) |
| `build_agreement.py` | 6164 | `c7c1805b…` (path + label) |
| `merge_c.py` | 5001 | `9534ddd7…` (path + IDs) |
| `reconstruct_keymaps.py` | 4433 | `149b2430…` (gate + `--builder`) |
| `run_selector.py` | 17352 | `30039a20…` (d082 gate) |
| `take_snapshot.py` | 3372 | `99b49c4e…` (path + label) |
| `author_brief.md` | 9400 | `c40a4aca…` (NINE sets + IDs) |
| `reviewer_brief.md` | 4366 | `bc39db64…` (title only; schema unchanged) |
| `c_brief.md` | 3164 | `e0f24b02…` (title + IDs) |
| `carry_exclusions_v9r4.py` | 3169 | `4dcda68b…` (9-file carry) |
| `freeze_plan_v9r4.py` | 21755 | `bb7ff0b7…` (real freeze) |
## 3. Mechanics repair vs v9r3 (only delta; all numerics/semantics/gates otherwise identical)

- Reviewer raw schema exactly eight fields
  `item_id,stratum,location_bearing,labelable,source_truth_answerable,ambiguous,ambiguity_type,golds`;
  no `query_text` or extras (`reviewer_brief.md` schema unchanged; enforced fail-closed by
  `freeze_raw_ab.py` + `merge_raw_ab.py` `SCHEMA_VIOLATION`).
- Fail-closed raw-freeze lifecycle (plan `raw_freeze_lifecycle`): reviewer complete →
  hash/freeze six chunks per role + manifest → both transcript audits PASS attestation
  (`transcript_audit_attestation.json` + `--audits-pass`) → reconstruct keymaps while rehashing
  unchanged chunks and mechanically verifying packet/order/query against candidates → merge unchanged
  raw while rehashing again → agreement → C. Any mutation after freeze → rehash mismatch →
  `CONTRACT_INVALID_GENERATION`.
- `merge_raw_ab` never requires/reads raw `query_text` (v9r3 L40 defect removed; packet/query check is
  mechanical against `candidates_merged.json` + frozen packet bytes only).
- Launcher preserved: exact-dir derivation + first-3-lines + fallback-literal-false + bounded polling +
  no global scan unchanged (`rglob` absent); v9r4 helper normalized-equivalent to v9r3 (`ce4daa89…`
  → `906f379b…`, docstring L1 only).
- Prompts carry v9r4 IDs with fresh-staging placeholders (D082 concrete `bc-v9r3-phasec-*` roots removed).
- Nine-set gates in `check_anchor.py` / `validate_pool.py` / `run_selector.py` + manifest; gold gates
  unchanged. v9r3 builder bytes preserved untouched as failure evidence. No D082 semantic tuning.

## 4. Verification (this stage, hashes/counts/structure only)

- `py_compile` all 17 scripts PASS; plan/lock/rubric/seed/version binding PASS
  (`run_selector.load_plan_binding` contract re-verified offline).
- 36/36 query pairs overlap 0; gold 3-set unchanged; plan parity 47 diff leaves, all within the
  identity/nine-set/lifecycle allowlist (counts/reserve/location, 8 authoring semantics, rubric
  semantics, A/B-360, C-every-360, agreement, exact selector algorithm, candidate-plan gates identical).
- Neutral synthetic lifecycle test (placeholder rows only, temp dirs): freeze/reconstruct/merge happy
  PASS; staging-mutation-after-freeze fails; frozen-mutation-after-freeze fails; `query_text`-in-raw
  rejected; missing `--audits-pass` fails. ALL PASS.
- Builder inventory (29 entries) and §2 absence list verified. No new source truth accessed; v9r4 source
  truth absent.
- Forbidden counts all 0: authors/reviewers/C/selector/benchmark/protected-access/source-snapshot
  execution, query plaintext logging, protected plaintext/recovery/`git cat-file`/`show`/`checkout`/
  `restore`/sparse/worktree, ref creation, `ml-service` change, history rewrite, D-081/v9/v9r1/v9r2/v9r3
  record mutation, D082 aggregate reuse beyond fingerprints, Desktop/browser/computer use.

## 5. Disposition

Verdict: D-083 generation-v9r4 PRE-RESULT freeze complete. Added in this stage: this doc + DECISIONS
`D-083` block + SESSION-LOG entry (repo); v9r4 builder (private dir only). STOP for Web independent
review. Phase C execution requires Web review/user continuation and is NOT authorized here. No D-084.
