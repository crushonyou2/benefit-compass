# Retrieval v3 D-087 generation-v9r7 PRE-RESULT freeze (2026-09-06)

New logical stage: generation-v9r7 pre-result freeze ONLY — author-isolation
repair as identity successor from v9r6, frozen strictly after D-086 commit
fd83b57. No source truth, no authors/reviewers/C/selector/benchmark/protected
actions in this stage beyond the single authorized adversarial smoke.
Plaintext-free: SHAs, counts, timestamps, filenames, structural facts only —
no query text, no labels, no id-to-text mappings, no agreement values.

## 0. Reconciled base (actual wins, this freeze session — observed)

- Branch `codex/retrieval-v3-user-search-quality` HEAD
  `fd83b57e1385f5288a3dd7ffe36f957987cfe61c` (D-086) clean; local = upstream
  = direct remote identical; `git diff --check` PASS;
  `git diff HEAD -- ml-service/` 0.
- OMP `18.1.5`; `modelRoles` default/plan
  `opencode-go/muse-spark-1.3-contributor:xhigh`, no project override.
- HOLD base commit fd83b57 committer `2026-09-05T18:37:23Z`
  (`2026-09-06T03:37:23+09:00`).
- v9r6 builder preserved byte-identical as CONTRACT_INVALID evidence
  (plan 41927 `389adaff…`, rubric 3334 `08e598a4…`, lock 9200 `0715524b…`);
  `~/bc-v3-v9r6-phaseC` author1/author2 staging + transcripts preserved
  untouched (evidence, not repo).
- Audit `eval/retrieval-v3/audit/events.jsonl` 4 events SHA
  `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
  (no append).
- Frozen six byte-identical by clean-tree inheritance. Canonical v3
  result absent; `eval/retrieval-v3/dev/` + `holdout/` + `dev-v2/` absent;
  no dev-v2 branch/tag/worktree; protected v3 freeze branches untouched.
- No `git cat-file`/`show`/`checkout`/`restore`/sparse/worktree in this
  freeze session. Generation / A-B-C / selector / benchmark / protected-access
  / source-snapshot execution count 0 beyond the single smoke. No
  Desktop/browser/computer use.

## 1. Inputs carried (fingerprint-only, zero plaintext)

- Nine fingerprint sets carried byte-identically from v9r6 `input/`
  (verified SHA-equal): failed-D070 273 `0acc6f27…`, D071 273 `3a037d98…`,
  D072 360 `ff3f65d6…`, D074 360 `fde76331…`, D076 365 `3feaab4d…`, D082
  360/unique 360 `1315b34a…` (hash-only), dev-v1 180q/228g `57716c6a…`,
  holdout 250q/212g `3463a8a1…`, history union 248q/248g `42e8534d…`.
- Tenth exclusion mechanically hashed in this stage from D-086
  CONTRACT_INVALID 360 existing query_text (author1 180 + author2 180,
  12 chunks x30) with standing NFC-strip-collapse-casefold-SHA256,
  plaintext-free (counts/hashes only, never printed/logged/stored):
  `input/failed_d086_query_fingerprints.json` 24427 bytes SHA
  `5d80ac3d38d2d61d285c9e3f8bd6640caa2804e5e1f777ca329b1613119c7939`,
  count 360 / unique 360, zero overlap prior nine (9/9 sets 0).
- Ten query sets pairwise overlap 0 (45/45). Gold 3-set exclusions unchanged.

## 2. Author-isolation repair vs v9r6 (only delta; numerics/semantics/gates otherwise identical)

- Identity successor: plan `retrieval-v3-dev-generation-v9r7`, seed
  `benefit-compass-retrieval-v3-dev-v2-generation-v9r7-2026-09-06`,
  candidate IDs `v3g9r7-001..360`, C opaque IDs `v9r7c-001..360`.
- TEN-set pool-gate enforcement: `validate_pool` operative loop checks all
  TEN sets (d086 added); `check_anchor` + `run_selector` enforce d086;
  permanent regression `test_ten_set_gates.py` (fails on v9r4/v9r6 bytes
  missing d086, passes on v9r7 with 45/45 overlap 0, d082 + d086 probes hit).
- Author sessions run through Paseo PLUS an agent-specific PATH wrapper
  invoking real OMP `C:\Users\joji\AppData\Local\omp\omp.exe` (18.1.5) with
  exact `--tools=read,eval,todo` (excluding task/hub); no global OMP config
  change. Wrapper `author_omp_wrapper.py` 3698 `a9d1d188…` + shim `omp.cmd`
  49 `b2d70b57…`: strips incoming `--tools`/`--no-tools`, fail-closed on
  task/hub mention, forces allowlist, logs one JSON invocation line
  (argv counts only, no prompt/query plaintext) to per-agent
  `OMP_WRAPPER_LOG`. Launcher `launch_top_level_paseo.py` 19737
  `ba691e62…` materializes per-agent `wrapper_bin/`, verifies copy bytes,
  passes `--env PATH=<wrapperBin>;<orig>` + `--env OMP_WRAPPER_LOG=<staging>/wrapper_invocation.log`
  to `paseo run`, keeps ParentAgentId-null/cwd/model/fallback exact-dir
  first-3-lines checks, and poll-verifies one `wrapper_invoked` allowlist
  event (fail-closed).
- Structural post-author transcript gate `audit_author_isolation.py` 2021
  `8974be4e…`: counts message.content toolCall names, requires task=0/hub=0
  before any merge (exit 0 PASS / 3 FAIL; counts only). Reproduces D-086:
  Author-1 197 lines task 1/hub 12 FAIL; Author-2 208 lines 0/0 PASS.
- Author brief + prompts carry v9r7 IDs with fresh-staging placeholders and
  explicit isolation paragraph (top-level only, tools read/eval/todo,
  no task/hub/subagents/descendants, coordinator never authors).
- Packet exact-bytes freeze, reviewer raw exact eight fields (no
  `query_text`), launcher exact-dir first-3-lines, 13 rename-only files
  normalized-equivalent — all preserved.
- Plan parity v9r6→v9r7: 47 diff leaves, all in
  identity/tenth/wrapper/isolation/lineage/mechanics allowlist.
  Counts/reserve/location, 8 authoring semantics, rubric semantics, A/B-360,
  C-every-360, agreement, exact selector algorithm, candidate-plan gates
  identical.

## 3. Adversarial smoke (exactly one, FINAL bytes, before freeze)

- Empty temp cwd `bc-v9r7-smoke-20260906-adversarial/cwd`; neutral prompt
  (514 bytes) requests task/hub once each, then requires single-line
  SMOKE_DONE with no retry/workaround; no source truth/candidates/benchmark.
- Launched via FINAL helper+wrapper bytes: agent
  `ca3500d2-94bd-4a82-8911-7de7e4e2454a` (`CreatedAt`
  `2026-09-05T18:57:47.191Z`); `--verify` PASS (ParentAgentId null, cwd
  exact, model exact, fallback false via exact-dir first-3-lines single
  session `2026-09-05T18-57-46-686Z_…jsonl` 36 lines `bf0fb011…`).
- Wrapper proves allowlist: `wrapper_invocation.log` 1 line
  `wrapper_invoked` tools `read,eval,todo`.
- Transcript audit PASS: task 0 / hub 0 (36 lines; other read 6 / todo 4).
- No descendant: 0 children of smoke agent; Paseo children count 0.
- Top-level provenance PASS. Agent stopped best-effort; staging
  (wrapper_bin + log) + session file preserved as evidence (not repo).
- Pinned structurally in lock `smoke_top_level_verification`
  (repeated True, adversarial True, IDs/paths/lines/sha16/counts).

## 4. Verification (this stage, hashes/counts/structure only)

- Frozen: plan 43552 SHA
  `cf47cc298234efabb3cf3688cd79f5b771c44d60ad866ee1d6bd0a0f4ffed2c9`,
  rubric 3334 SHA `08e598a4…` (byte-identical to v9r6), lock 10967 SHA
  `460ad017…` (`frozen_at` `2026-09-05T18:59:30+00:00`, later than HOLD base
  `18:37:23Z`; source_truth false; 24 mechanics pinned; `hold_base_commit`
  fd83b57; `provenance_order` `freeze_after_hold`),
  manifest 2254 SHA `7c5cc0f9…` (TEN gates).
- `py_compile` all 20 scripts PASS; plan/lock/rubric/seed/version binding
  PASS; 24 mechanics SHAs PASS (zero mismatch); `test_ten_set_gates.py`
  PASS on v9r7 (operative ten, d082 + d086 probes hit, clean miss, 45/45
  overlap 0, counts dev 180 / holdout 250 / history 248 / d070 273 / d071
  273 / d072 360 / d074 360 / d076 365 / d082 360 / d086 360); wrapper local
  PATH-shadowing PASS + forbidden-tools rejection PASS + allowlist
  forwarding to real OMP 18.1.5 PASS; audit gate reproduces D-086 FAIL/PASS
  as designed; inventory 33 top-level entries; §0 absences hold (incl
  frozen packets/attestation/keymaps/raw); v9r6 bytes unchanged
  (`389adaff…`/`08e598a4…`/`0715524b…`); v9r7 source truth/anchors/candidates/
  staging absent.
- Forbidden counts all 0: authors/reviewers/C/selector, benchmark,
  plaintext logging, protected access incl. git-object-scan, ref creation,
  ml-service change, history rewrite, D-081/v9/v9r1/v9r2/v9r3/v9r4/D-083-HOLD/
  D-084/D-084-HOLD/D-085/D-086 mutation, D082/D086 aggregate reuse beyond
  fingerprints, Desktop/browser/computer.

## 5. Disposition

Verdict: D-087 generation-v9r7 PRE-RESULT freeze complete. Added in this
stage: this doc + DECISIONS `D-087` block + SESSION-LOG entry (repo); v9r7
builder (private dir only, 33 entries). v9r6 marked CONTRACT_INVALID, never
resumed. STOP for Web independent review. Phase C execution requires Web
review/user continuation and is NOT authorized here. NO Phase C in this
continuation.
