# Retrieval v3 D-092 D-091 PRE-RESULT narrative correction (2026-09-06)

Append-only durable correction BEFORE Phase C data execution. Does NOT mutate
the frozen v9r9 builder (`C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260906-v9r9`):
no plan/rubric/lock/mechanics/smoke-staging/session/wrapper-evidence change.
Plaintext-free: SHAs, counts, timestamps, filenames, structural facts only.

## 1. Smoke narrative stale — frozen lock/current bytes authoritative

- Stale durable narrative (superseded ONLY as to this pair, text left untouched):
  D-091 repo doc §3 + D-091 DECISIONS block + D-091 SESSION-LOG entry say
  `session 9 lines / SHA 90543d996d341d28a5db37f58444ce560638f1fbc8fdb2b16011c2f67efa91b1`.
- Authoritative (frozen `PLAN_LOCK.smoke_top_level_verification`, verified from
  frozen bytes in this correction session; current frozen auditor revalidation binds the same):
  smoke agent `772e5402-160b-44dd-ad26-2fda83a33e1c`;
  session file `C:/Users/joji/.omp/agent/sessions/-bc-v9r9-coord-smoke-20260906-cwd/2026-09-05T21-12-14-196Z_01a0736a-3074-762a-b1a1-fc143ff88eef.jsonl`;
  `smoke_session_lines 10`;
  `smoke_session_sha256 77b3404b60c564265e3ac2c6e869a72114e5026dd9b933351458b5f834e8dcfd`;
  `smoke_tool_calls {phasec_probe: 1}`, `smoke_descendants 0`,
  wrapper `todo`/`smoke`/frozen controls, `audit_verdict SMOKE_PASS`.
- Reading: the frozen lock + current exact bytes supersede only that stale
  `9 lines / 90543d99…` narrative pair. No cause speculated. All other D-091
  smoke facts (single launch, fresh cwd, idle, exact-one frozen surface,
  descendants 0 both sides, provenance PASS) stand as written.

## 2. Frozen plan descriptive TEN drift — operative TEN authoritative

- Immutable `input/EXCLUSION_INPUTS.json` is the TEN-set manifest, SHA
  `353df31a264f67ae76bf4daa740dd1dfe1c6db99df259cad44fba75f0a790dd8`;
  `test_ten_set_gates.py` PASS proves operative gates
  dev_v1/holdout/history/d070/d071/d072/d074/d076/d082/d086 with 45 pairwise
  overlaps 0. Immutable `validate_pool.py`, `check_anchor.py`, and
  `run_selector.py` all enforce failed-D086.
- Descriptive omission (verified from frozen bytes, structure only):
  frozen `GENERATION_PLAN.final_selector.constraints[8]` reads
  `query overlap 0 vs dev-v1/holdout/history-union/failed-D070-273/failed-D071-273/failed-D072-360/failed-D074-360/failed-D076-365/failed-D082-360`
  — stops at failed-D082; joined D086 textual occurrence count is 0.
- Reading: per standing D-087/D-088 same-TEN decision and operative mechanics,
  this is a descriptive omission only; operative TEN including D086 is
  authoritative and MUST be the gating reading. Frozen plan bytes remain
  immutable and are NOT repaired.

## 3. Frozen plan coordinator description drift — pinned mechanics authoritative

- Descriptive omissions (verified from frozen bytes, structure only):
  `GENERATION_PLAN.coordinator_confinement.wrapper` string omits `--no-extensions`;
  `coordinator_confinement.launcher` string omits `PYTHONUTF8=1`.
- Authoritative mechanics (frozen/pinned, unchanged):
  wrapper SHA `61300a12fa57bfb370c37d448be59bdbf156cb3108ca48f4fb1be2de28de697b`
  invokes `--tools=todo -e <frozen ext> --no-extensions --no-skills --no-rules`;
  launcher SHA `da3ac11307bf19f2942d425bfcf84af99b3d5a677676d6ee0f7c21ef3ffad67d`
  passes `PYTHONUTF8=1`; `PLAN_LOCK` pins these exact SHAs (plus ext
  `31c05ed0457c1469a451ff6356d70c361fa0b278af684298a03aac1e7f186bab`, driver
  `fdf91460021ae46499794e1d8dfab6a4f57252a01dbc3a97f0718a7405234752`, auditor
  `3fc5a3c09a949a4b3a7a8681b4b4ba287da34ba99848bee94e21c3292a7b4ae5`,
  `smoke_wrapper_controls [--tools=todo, -e, --no-extensions, --no-skills, --no-rules]`);
  smoke wrapper log confirms the five frozen controls.
- Reading: descriptive omission only — no weakening, no mutation.

## 4. Independent PASS evidence (Web-established per correction prompt)

- Builder `FROZEN_HASHES.json` pins 53 files; independently recomputed actual set
  53, missing/extra/hash-mismatch all zero.
- Plan SHA `c6ba5ad5a3a07fddf60fa56d9ac6b70c27e1e8d4ca64097f8649f8c8309c172c`;
  lock SHA `e904f2851788603b58254528f4c813e9ef15ecb6d8d39e20cb425d1408ea7bfc`;
  rubric SHA `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`;
  exclusion manifest SHA as in §2.
- Final counts `21/25/21/25/18/20/23/27 total 180`,
  location `6/7/6/8/5/6/7/9 total 54`;
  reserve `42/50/42/50/36/40/46/54 total 360`,
  location `12/14/12/16/10/12/14/18 total 108`;
  A/B all-360 opaque; C every-360 exactly once; selector exact-180.
- No `phasec_driver.run.lock`/source_truth/candidates/raw/adjudicated/evalset;
  no Phase C root; driver never ran. Web verdict: frozen PRE-RESULT PASS.

## 5. Reconciled base for this correction (observed)

- Branch `codex/retrieval-v3-user-search-quality` HEAD
  `70a0c586b66cc75b46b9d5955de05a060c8078b1` clean; local = upstream =
  direct remote identical; `git diff --check` PASS; `git diff HEAD -- ml-service/` 0.
- OMP `18.1.5`; `modelRoles` default/plan
  `opencode-go/muse-spark-1.3-contributor:xhigh`.
- Audit `eval/retrieval-v3/audit/events.jsonl` 4 events SHA
  `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506` (no append).
- Canonical v3 result/dev/holdout/dev-v2 absent; no dev-v2 branch/tag/worktree.

## 6. Boundary / verdict

Added this doc + DECISIONS `D-092` block + SESSION-LOG entry ONLY (repo).
No frozen plan/rubric/lock/mechanics mutation. No source snapshot, generation,
A/B/C, selector, benchmark, protected access, git-object protected recovery,
ref creation, or ml-service change in this correction commit.
D-091 frozen v9r9 PRE-RESULT remains VALID/PASS; only the durable narrative
pairs in §§1–3 are superseded by D-092. Real Phase C is authorized ONLY after
Web verifies this correction commit; Phase C was NOT run in this root.
