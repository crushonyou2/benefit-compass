# Retrieval v3 D-095 generation-v9r10 post-smoke CONTRACT_INVALID_GENERATION (2026-09-06)

Append-only durable closure. The D-094 DECISIONS entry, the D-094
SESSION-LOG entry, and `docs/RETRIEVAL_V3_D094_D093_EXTENT_CORRECTION.md`
are preserved verbatim. Plaintext-free: IDs, timestamps, counts, status
strings, and structural facts only — no query/gold semantic plaintext.

Authorization chain (all received in this root, repo docs only from here):
D-095 v9r10 PRE-RESULT implementation/testing (single top-level root, no
task/hub/subagents, stop before model smokes) → Web PRE-SMOKE FINAL
VERDICT = PASS authorizing EXACTLY TWO DISTINCT MODEL SMOKES on current
final v9r10 bytes with no byte changes (A: one coordinator confinement
smoke; then only if A PASS, B: one neutral lifecycle smoke; no
repair/retry; no real Phase C) → both smokes PASS → Web POST-SMOKE REVIEW
= CONTRACT_INVALID_GENERATION with prohibitions (no freeze, no repair, no
retry, no v9r10 byte changes, no Phase C) → clarification that the byte
prohibition covers outside-repo builder/smoke artifacts only and REQUIRES
this repo docs-only append-only closure, and only this.

## 0. Reconciled base (actual wins, observed in this closure root)

- Branch `codex/retrieval-v3-user-search-quality` HEAD
  `27f2c432a39384afbe0ca5002edb551d64acb6f6` (D-094) clean;
  local = upstream = direct remote identical; `git diff --check` PASS;
  `git diff HEAD -- ml-service/` 0.
- OMP `18.1.5`; modelRoles default/plan
  `opencode-go/muse-spark-1.3-contributor:xhigh` (runtime context, no override).
- Audit `eval/retrieval-v3/audit/events.jsonl` 4 events SHA
  `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
  (no append).
- Canonical v3 result/dev/holdout/dev-v2 absent; no dev-v2 branch/tag/worktree.
- v9r10 final bytes verified unchanged before and after both smokes (18 key
  SHA16: plan `bbd122c64b890ba5` 50016 / driver `528884c144397181` 23247 /
  gate `e06ced73b2e47a54` 13218 / gate-test `4ce4605a44cfd135` 14401 /
  confinement `872b4b811635d55a` 27495 / TEN `c69b9afeacb13b28` 6949 /
  freeze `b2672e4952fd9ba1` 41365 / ext `47966390eaea6e62` 5012 /
  coord-wrapper `0b79c0b1f2d1cd49` 7055 / launcher-top `21e9646f2df180c6`
  20061 / launcher-coord `61a14291b6c1bc7b` 8295 / lifecycle-auditor
  `34c21d929bcb8b52` 5931 / smoke-runner `f35695d154e553b0` 3976 /
  smoke-prompt `caede30db28eed30` 1579 / coord-auditor `920ba6c5c46845d2`
  8384 / isolation-auditor `3ecdd290e1c7e5f1` 2022 / carry `3e996b67f1c6df2b`
  4485 / manifest `390489bf7a180197` 2183). No `PLAN_LOCK.json`, no
  `FROZEN_HASHES.json`, no run lock, no runtime outputs in the real builder.
- This closure root performed no freeze, no repair, no smoke retry, no v9r10
  byte change, no Phase C generation (no authors/reviewers/C/selector), no
  runtime deletion/mutation, no benchmark/retrieval/protected access
  including git-object-scan (`git show`/`cat-file`/`checkout`/`restore`/
  sparse/worktree 0), no new refs, no history rewrite, no
  Desktop/browser/computer. Outside-repo smoke evidence preserved untouched.

## 1. Pre-smoke (D-095 implementation/testing, observed in this root)

- Fresh v9r10 builder outside repo only (57 files, 666880 bytes): 52 files
  from verified v9r9 FROZEN_HASHES pins (53/53 verified, minus PLAN_LOCK,
  2 renames) + 5 new (completion gate, gate tests, lifecycle auditor,
  lifecycle runner, lifecycle prompt). Capsule manifest SHA `4c3eeb39…`
  verified; RUBRIC + 10 inputs byte-identical to capsule; forbidden runtime
  files 0.
- D-094 repair implemented narrowly: `paseo wait` / `TERMINAL_OK` /
  `wait_idle` / `require_terminal` / successful-path `stop_agent` removed
  from the driver; `paseo()` fail-closes on `wait`; deterministic polling
  completion gate (exact author 6x30 / reviewer 6x60 / C 6x60 outputs +
  final-stop session + >=15s byte-stable quiescence; dedicated smoke 6x1
  spec); audits only after stable completion; agents left idle.
- Non-model battery on final bytes: GATE_TESTS_PASS, TEN 45 pairs overlap 0
  (d082/d086 360, dev_v1 180, D093 11th absent), CONFINEMENT_TESTS_PASS 167
  checks, Bun PROBE_PASS, no CR in mechanics, throwaway dry-freeze
  fail-closed (rc=3, no lock) with byte-identical plan/manifest/rubric
  reproduction, bogus-smoke binding fail-closed (rc=3, no lock).
- Descriptive drift fixed in plan: selector constraint includes
  failed-D086-360; wrapper string includes `--no-extensions`; launcher
  string includes `PYTHONUTF8=1`. TEN unchanged, no 11th (D-093 zero rows).

## 2. Authorized smokes (exactly one each, observed in this root, no retry)

- Smoke A (coordinator confinement): ONE launch, agent
  `04d6373c-b49c-4dd8-ad6e-d99f08337964`, fresh
  `bc-v9r10-coord-smoke-20260906/cwd`, adversarial neutral prompt (old
  v9r9/v9r8 paths + read/shell/task/hub attempts, phasec_probe fallback, no
  protected data). Idle observed; frozen `audit_coord_smoke.py` once → rc 0
  `SMOKE_PASS`: session 23 lines SHA `7fdd5e62…`, tool_calls
  `{phasec_probe: 1, todo: 5}`, forbidden 0, required_calls 1, wrapper
  exact-one (`todo`/`smoke`/frozen controls), descendants 0, fallback proven.
- Smoke B (neutral lifecycle, after A PASS): frozen `run_lifecycle_smoke.py`
  once (no argv), fresh `~/bc-v3-v9r10-lifecyclesmoke` (no
  source_truth/policy/query/gold/protected data). Agent
  `aacf232c-c0db-431c-a21b-3d9999b7b171`; polling gate accepted only after
  exact 6x1 chunks + final stop + stable quiescence (~152s); frozen
  `audit_lifecycle_smoke.py` → `LIFECYCLE_SMOKE_PASS`: 6 chunks × 9 bytes ×
  1 row, session 138 lines / 476670 bytes SHA `04ad0c42…`, wrapper
  `read,eval,todo`, transcript task=0/hub=0, descendants 0, agent left idle,
  no stop_agent call.
- Single launch per smoke; no second attempt of either for any reason.

## 3. Verdict standing

- Web POST-SMOKE REVIEW = CONTRACT_INVALID_GENERATION (received via the
  authorizing channel; recorded as received, no reasoning invented here).
  Consequently: NO real freeze was run (no `PLAN_LOCK.json`, no
  `FROZEN_HASHES.json` in the real builder); NO Phase C was run (no source
  snapshot, no authors, no A/B/C, no selector, no benchmark/protected/
  dev-v2); v9r10 is non-resumable/non-repairable under this verdict — both
  authorized smokes are consumed, and freeze/repair/retry/byte-change were
  explicitly forbidden, so no frozen execution may follow from these bytes.
  A successor, if any, requires a fresh identity/plan under a new decision
  outside this root.
- D-094 text/history preserved verbatim. The frozen v9r10 builder, both
  smoke stagings/sessions/logs, and all outside-repo evidence are untouched.

## 4. Boundary

- Added this doc plus the DECISIONS `D-095` block plus the SESSION-LOG entry
  ONLY (repo). No frozen mutation; no history rewrite; no ml-service change;
  no audit append; no semantic plaintext logged.
- Forbidden counts 0 in this closure root (freeze, repair, second smoke A/B,
  v9r10 byte change, Phase C generation incl. authors/reviewers/C/selector,
  runtime deletion/mutation, benchmark/retrieval/protected access including
  git-object-scan, new refs, D-081..D-094 mutation, D082/D086 reuse beyond
  fingerprints, Desktop/browser/computer).
- STOP. No Phase C and no successor design/freeze in this root.
