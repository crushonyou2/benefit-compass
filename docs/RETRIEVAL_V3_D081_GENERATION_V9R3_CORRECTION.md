# Retrieval v3 D-081-SC3 generation-v9r3 correction — lineage-text-only narrow repair

Status: SAME-STAGE third Web-HOLD → v9r3 PRE-RESULT lineage-only correction (user-authorized continuation). Plaintext-free: SHAs, counts, timestamps, filenames, structural facts only — no query text, no labels, no id mappings. D-081/v9/v9r1/v9r2 records preserved verbatim; this doc + DECISIONS `D-081-SC3` block + SESSION-LOG entry are the only repo additions.

## 1. Reconciled base (actual repo/remote wins, this session — observed)

- Branch `codex/retrieval-v3-user-search-quality` HEAD `4be0f072f0d3d44c55ba026b96cbf29054feccc4` clean, local = upstream = direct remote identical (`https://github.com/crushonyou2/benefit-compass.git`).
- `git status --porcelain` clean; `git diff --check` PASS; `git diff HEAD -- ml-service/` 0; frozen six byte-identical by clean-tree inheritance (prereg `78420186…` + plan-v4 `a25d9c48…` + safe-action `c512fb56…` + policy-v2 `6fee9ec2…` + link-V2 `f028ce46…` + cost-V1 `5891b0ba…`); audit `eval/retrieval-v3/audit/events.jsonl` 4 events SHA `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506` byte-identical.
- Canonical v3 result absent; `eval/retrieval-v3/dev/` + `holdout/` + `dev-v2/` absent; no dev-v2 branch/tag/worktree; protected v3 freeze branches untouched.
- No project model override (`opencode.json`/`.opencode.json` absent); root session model `opencode-go/muse-spark-1.3-contributor:xhigh` (runtime context; model config never changed).
- No source-truth/candidate/plaintext read, no `git cat-file`/`show`/`checkout`/`restore`/sparse/worktree, no benchmark/retrieval/ranking/latency/HTTP/model-encode, no ml-service change, no history rewrite in this stage.

## 2. Web blocker (observed, v9 + v9r1 + v9r2 bytes preserved as HOLD evidence)

- Frozen v9r2 `GENERATION_PLAN.json` carries three lineage-text errors (helper exact-dir + first-3-lines mechanics themselves are sound and preserved):
  - `dataset_identity.note` says `Supersedes v9r2 before execution` (self-supersede) and `v6 HOLD + v6r1/v7/v8/v9/v9r2 CONTRACT_INVALID bytes preserved as evidence` (calls v9/v9r2 CONTRACT_INVALID; omits v9r1).
  - `post_freeze_rule` says `V6 HOLD + v6r1/v7/v8/v9/v9r1 CONTRACT_INVALID bytes remain preserved evidence` (calls v9/v9r1 CONTRACT_INVALID instead of HOLD).
  - `stage_forbidden` old-builder list says `old-builder (v5/v6/v6r1/v7/v8)` (omits v9/v9r1/v9r2).
- Frozen v9 bytes preserved untouched as HOLD evidence: plan `386bc79a858b9a9fcaf40a7728291c2370b1f97e90a56395266c67f2f03e9e54` (31522), rubric `728fdb9deb06915f17cf0c21f5efca9d29b0ca8b3532b4c884675b9026da63e1` (3330), lock `c27cfef04bb4cf40d4f14d843f05d893778a26df910a0ec37a411812ace47d33` (3947), helper `f91355c7a9b4ac27b7a0847350597b8f21328572a03a339c16303ecc605db1e0` (7588). V9 was never executed.
- Frozen v9r1 bytes preserved untouched as HOLD evidence: plan `2e6f8e0dfa2f25fc0af6f452b97d74658480588f712926eb650db822a207c002` (32875), rubric `e3d1bcf9192b47e71e4d13f815b5aebf957a4ade04672800fb639e8c252c34ec` (3334), lock `47ea88e069ba2da18dbfbb693b4b5ca7020b7425651c38ecc07d7e84d205ac59` (5046), helper `7c1b31e5be81e5ed364ad117f0eae1f6ab3531edef3827aff9153b78580696b9` (14279). V9r1 neutral-smoke-only.
- Frozen v9r2 bytes preserved untouched as HOLD evidence: plan `2fe9cbe657f12b7aeb3611cad2a367a21692aaec884615625a28781ee1b8407f` (35727), rubric `7a1dac2ae4c3c5ef246e2dd2e56e88f7c2d4fec07e2fe1af0824b3b6da7516c3` (3334), lock `a5316374673f771e29413aba242d6fe70b526226e18726b1fdd807723c38ac93` (6395), helper `0d4b9b391272172ec655111ae7ac9b8f9db3cfc7f3651242eea123f256787ca2` (16821). V9r2 neutral-smoke-only.

## 3. Repair scope (lineage texts ONLY; all semantics identical to v9r2)

- New private builder only: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260905-v9r3` (built from v9r2 pre-result inputs/mechanics only; no source truth read at any step).
- New identity only: plan_version `retrieval-v3-dev-generation-v9r3`; seed `benefit-compass-retrieval-v3-dev-v2-generation-v9r3-2026-09-05`; candidate IDs `v3g9r3-001..360`; C opaque IDs `v9r3c-001..360`.
- Identical to v9r2 (verified §6): counts/reserve/location, all 8 authoring semantics incl paired-grounded ambiguous, neutral rubric semantics, A/B-all-360, C-every-360, agreement method, exact lexicographically-smallest selector, candidate-plan gates, detached env sanitization (ALL `PASEO_`/`OMP_` env removed, `PASEO_CLI` captured before sanitization), exact-dir first-3-lines verification.
- Lineage corrections ONLY (three texts + supersedes):
  - `dataset_identity.note` now says `v9r3 supersedes v9r2 before execution (lineage-text correction only); v6 HOLD + v6r1/v7/v8 CONTRACT_INVALID + v9/v9r1/v9r2 Web-HOLD bytes preserved as evidence` (truthful statuses; current v9r3 not called invalid).
  - `post_freeze_rule` now says `NEVER mutate v9r3 plan/rubric/lock … V6 HOLD + v6r1/v7/v8 CONTRACT_INVALID + v9/v9r1/v9r2 HOLD bytes remain preserved evidence; v9r3 is the active frozen plan` (v9/v9r1/v9r2 as HOLD, not CONTRACT_INVALID).
  - `stage_forbidden` old-builder list now says `old-builder (v5/v6/v6r1/v7/v8/v9/v9r1/v9r2) content access beyond pinned aggregate facts + carried fingerprint bytes (zero)` (includes v9/v9r1/v9r2; no semantic/source/candidate reuse).
  - `supersedes` preserves v9/v9r1 plans/rubrics/notes verbatim and adds `v9r2_plan` `2fe9cbe6…` / `v9r2_rubric` `7a1dac2a…` / `v9r2_note` identifying this exact lineage-text blocker; reason rewritten for v9r3 lineage-only correction.
- Preserved helper (`launch_top_level_paseo.py`, 16821 bytes, SHA `ce4daa8941a24f510f22e1fddec7eff04e2291e1fd52f4f1ab9ca0f15c091d02`): docstring L1 identity only (`generation-v9r3`); launch path + exact-dir first-3-lines algorithm verbatim. Normalized equivalence verified: replacing `generation-v9r3` with `generation-v9r2` in the v9r3 helper yields byte-identical v9r2 helper bytes. No new smoke required on this basis; no new child was launched in v9r3.

## 4. Exclusions (carried byte-identically; no D078/D080 sets)

- 8 fingerprint files carried byte-for-byte from v9r2 `input/` (which carried from v9r1/v9): failed_d070 `0acc6f27` (273), failed_d071 `3a037d98` (273), failed_d072 `ff3f65d6` (360), failed_d074 `fde76331` (360), failed_d076 `3feaab4d` (365/365), dev-v1 `57716c6a` (180q/228g), holdout `3463a8a1` (250q/212g), history `42e8534d` (248q/248g) — plus `D076_CONTRACT_INVALID_SUMMARY.json` `0279c69a` (aggregate provenance reference). No failed-D078/D080 set (rows 0).
- New v9r3 manifest `input/EXCLUSION_INPUTS.json` SHA `09bd7b52aad34dc6f8ac81907018f32bca61015828ee69fd9ac2d4bf541cb15d` (2120 bytes, pretty-printed LF like v9r2; same EIGHT gates, required overlap 0; description chain only).

## 5. Smoke (NOT repeated — helper normalized-equivalent; v9r2 smoke preserved)

- No new Paseo child was launched in v9r3 (neutral or otherwise). Basis: v9r3 helper normalized for identity is byte-equivalent to frozen v9r2 helper (docstring L1 only; `get_paseo_cli`/`sanitized_env`/`launch_top_level_agent`/`inspect_agent`/exact-dir derivation/polling/first-3-lines checks verbatim), so a new smoke would prove nothing new.
- Preserved v9r2 neutral-smoke evidence (not re-executed): exactly one neutral disposable child through the v9r2 helper into empty `C:/Users/joji/Documents/programming/bc-v9r2-smoke-20260905-neutral` with pwd-only prompt, returned `7d5ca7be-1bca-4cc9-9f2c-e9e39c874724`; PASS via final v9r2 helper bytes (ParentAgentId null + cwd exact + model exact + provider omp; exact OMP session dir unique single `*.jsonl`; session `2026-09-05T07:53:41.129Z` vs CreatedAt `2026-09-05T07:53:41.777Z` delta 0.648 s; model exact; `resolvedModelIsFallback` literal false; first-3-lines only). Child idle, `paseo stop` no-op, staging empty after stop. Pinned in v9r3 lock by reference (not repeated).

## 6. Freeze record (frozen BEFORE source-truth content; immutable afterward)

- `GENERATION_PLAN.json` 35779 bytes SHA `7b5c47a1e61e24f8f8ec96a20b389a6dcc42002d4d14874c0daf7b64ac8da391` (v9r3 identity; supersedes v9r2 plan `2fe9cbe6…`; reserve 42/50/42/50/36/40/46/54=360 + location 12/14/12/16/10/12/14/18=108 unchanged; three lineage texts corrected; `v9r2_plan`/`v9r2_rubric`/`v9r2_note` added; manifest SHA `09bd7b52…`; rubric SHA `08e598a4…`; 19 mechanics SHAs pinned incl preserved helper `ce4daa89…`).
- `RUBRIC.json` 3334 bytes SHA `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe` (`dimensions`/`judgment_rules`/`role` identical to v9r2; diff keys `plan_version` + `rubric_version` only, now `retrieval-v3-dev-generation-v9r3-rubric-v1`).
- `PLAN_LOCK.json` 6029 bytes SHA `2fa48764350da5af8e237a8c7c26c4a6fafd94fdbc731cc121147e18a1df661d` (`frozen_at` `2026-09-05T08:08:07+00:00` truthful observed; source_truth false incl new `v9r2_…_in_this_stage` flags; d070–d080 + v9 + v9r1 + v9r2 semantic flags false; git-object-scan 0; carry-from-v9 + carry-from-v9r1 + carry-from-v9r2; 19 mechanics SHA-pinned incl preserved helper `ce4daa89…` 16821 bytes; `supersedes_v8_plan` + `supersedes_v9_plan` + `supersedes_v9r1_plan` + `supersedes_v9r2_plan` `2fe9cbe6…`; v9 + v9r1 + v9r2 HOLD SHAs preserved; smoke NOT repeated with normalized-equivalence proof + v9r2 smoke reference).
- Static verification before source truth (observed): all 19 mechanics compile (LF canonical, no CRLF; `__pycache__` removed); `run_selector.load_plan_binding()` hashes actual plan `7b5c47a1…` and asserts lock binding PASS (plan/rubric/version/seed); 13 sections (`final_counts`, `reserve_counts`, `reserve_factor`, `authoring_contracts`, `a_b_packets`, `a_b_protocol`, `c_packets`, `c_protocol`, `agreement_diagnostics`, `disagreement_bundle`, `final_selector`, `mechanical_validators`, `standing_contract`) verified identical to v9r2; `author_isolation` claim/semantics/rules identical (mechanics_shas updated to v9r3); 8 exclusion sets + D076 summary byte-identical; active-ID residuals 0 (`v3g9r2` 0; `v9r2c` only as forbidden-old-prefix example in `merge_c.py` comment alongside `v9r1c`; `generation-v9r2` only as history in carry/freeze/lock-normalization notes; `v9`/`v9r1` only as HOLD-evidence keys/notes/SHAs); helper normalized-equivalent (see §3).
- Gate: this record is committed+pushed and remote-verified BEFORE any Phase C source-truth content read. Post-freeze rule in force: NEVER mutate v9r3 plan/rubric/lock; infeasible/contract-invalid → STOP/HOLD, no supplement/relabel/retune/recycle.

## 7. End state and STOP

- Main contains only plaintext-free D-081-SC3 records (this doc + `D-081-SC3` block + SESSION-LOG entry). Private v9r3 builder contains exclusions + scripts + plan/rubric/lock only; `source_truth.jsonl` ABSENT; `source_truth_meta.json` ABSENT; candidates ABSENT; anchors ABSENT; author/reviewer staging roots NOT created.
- STOP for Web independent review. Phase C generation requires Web review/user continuation and is NOT authorized in D-081-SC3. No D-082 execution.

## 8. Forbidden counts (this stage)

Forbidden counts all 0: source-truth snapshot, candidate generation, A/B/C, selector, benchmark/retrieval/ranking/latency/HTTP/model-encode, D068 retry/audit append/result, protected plaintext/recovery, `git cat-file` / `git show` / `checkout` / `restore` / sparse / worktree protected-data/object scanning, global `~/.omp/agent/sessions/**/*.jsonl` scan and first-10-lines/message-content reads (v9r2 helper already exact-dir + first-3-lines; v9r3 preserves byte-equivalent), protected branch/tag/worktree/import, ml-service change, history rewrite, D074/D076/D078/D080/V9/V9R1/V9R2 row reuse (fingerprint-only exclusion excepted), D-081/v9/v9r1/v9r2 record mutation, D-082 execution, Desktop/browser/computer use.
