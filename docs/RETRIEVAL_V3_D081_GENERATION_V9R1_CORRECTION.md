# Retrieval v3 D-081-SC generation-v9r1 correction — OMP fallback-provenance narrow repair

Status: SAME-STAGE Web-HOLD → v9r1 PRE-RESULT narrow repair ONLY (user-authorized continuation). Plaintext-free: SHAs, counts, timestamps, filenames, structural facts only — no query text, no labels, no id mappings. D-081/v9 records preserved verbatim; this doc + DECISIONS `D-081-SC` block + SESSION-LOG entry are the only repo additions.

## 1. Reconciled base (actual repo/remote wins, this session — observed)

- Branch `codex/retrieval-v3-user-search-quality` HEAD `6990a306d40f81e88cfcc1131502e495e2b99428` clean, local = upstream = direct remote identical (`https://github.com/crushonyou2/benefit-compass.git`).
- `git diff --check` PASS; `git diff HEAD -- ml-service/` 0; frozen six byte-identical by clean-tree inheritance; audit `eval/retrieval-v3/audit/events.jsonl` 4 events SHA `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506` byte-identical.
- Canonical v3 result absent; `eval/retrieval-v3/dev/` + `holdout/` absent; no dev-v2 branch/tag/worktree; protected v3 freeze branches untouched.
- No project model override (`opencode.json`/`.opencode.json` absent); root session model `opencode-go/muse-spark-1.3-contributor:xhigh` (runtime context; model config never changed).
- No source-truth/candidate/plaintext read, no `git cat-file`/`show`/`checkout`/`restore`/sparse/worktree, no benchmark/retrieval/ranking/latency/HTTP/model-encode, no ml-service change, no history rewrite in this stage.

## 2. Web blocker (observed, v9 bytes preserved as HOLD evidence)

- Frozen v9 `launch_top_level_paseo.py` (7588 bytes, SHA `f91355c7…`) lines 130–138 treat absent fallback keys as fallback=false via model/provider match. Paseo inspect JSON carries no fallback field — self-inspect this session returned keys `Id/Name/Provider/Model/Thinking/Status/Cwd/CreatedAt/ParentAgentId` only (`CreatedAt` `2026-09-05T07:36:14.191Z`, `ParentAgentId` null). Model/provider match therefore cannot hard-prove fallback=false.
- Actual OMP session metadata carries the proof: same-session file line 2 `type=session {timestamp 2026-09-05T07:36:13.518Z, cwd exact}` followed by line 3 `type=model_change {model opencode-go/muse-spark-1.3-contributor, resolvedModelIsFallback false (literal)}`.
- v9 builder/plan (`386bc79a…`)/rubric (`728fdb9d…`)/lock (`c27cfef0…`) bytes preserved untouched as HOLD evidence; v9 was never executed.

## 3. Repair scope (helper ONLY; all semantics identical to v9)

- New private builder only: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260905-v9r1` (built from v9 pre-result inputs/mechanics only; no source truth read at any step).
- New identity only: plan_version `retrieval-v3-dev-generation-v9r1`; seed `benefit-compass-retrieval-v3-dev-v2-generation-v9r1-2026-09-05`; candidate IDs `v3g9r1-001..360`; C opaque IDs `v9r1c-001..360`.
- Identical to v9 (verified §6): counts/reserve/location, all 8 authoring semantics incl paired-grounded ambiguous, neutral rubric semantics, A/B-all-360, C-every-360, agreement method, exact lexicographically-smallest selector, candidate-plan gates, detached env sanitization (ALL `PASEO_`/`OMP_` env removed, `PASEO_CLI` captured before sanitization).
- Repaired helper (`launch_top_level_paseo.py`, 19-file mechanics set): launch path byte-identical to v9 (`get_paseo_cli`/`sanitized_env`/`launch_top_level_agent` verified identical). `verify_top_level` keeps Paseo checks (ParentAgentId null, cwd exact, model now exact equality, provider omp) then parses inspect `CreatedAt` and proves fallback from OMP metadata: scan ONLY the first 10 lines of `~/.omp/agent/sessions/**/*.jsonl`, reading ONLY `type=session`/`type=model_change` lines (keys timestamp/cwd/model/resolvedModelIsFallback; every other line skipped without retaining content); require exactly one session with exact expected cwd and session timestamp within 180 s of `CreatedAt`; require its model_change model exactly `opencode-go/muse-spark-1.3-contributor` and `resolvedModelIsFallback` literally `False` (`is False`; missing/other truthy fails). Anything else ⇒ `CONTRACT_INVALID_GENERATION`. Zero-match polls metadata-only (5 s interval, 300 s ceiling) because the session file flushes asynchronously after agent creation; multi-match fails immediately (fail-closed). Same single helper for authors + reviewer A/B + C; no other launcher permitted.

## 4. Exclusions (carried byte-identically; no D078/D080 sets)

- 8 fingerprint files carried byte-for-byte from v9 `input/`: failed_d070 `0acc6f27` (273), failed_d071 `3a037d98` (273), failed_d072 `ff3f65d6` (360), failed_d074 `fde76331` (360), failed_d076 `3feaab4d` (365/365), dev-v1 `57716c6a` (180q/228g), holdout `3463a8a1` (250q/212g), history `42e8534d` (248q/248g) — plus `D076_CONTRACT_INVALID_SUMMARY.json` `0279c69a` (aggregate provenance reference). No failed-D078/D080 set (rows 0).
- New v9r1 manifest `input/EXCLUSION_INPUTS.json` SHA `b83c1690d326…` (2116 bytes; same EIGHT gates, required overlap 0; description only).

## 5. Smoke BEFORE freeze (actual, observed, plaintext-free)

- Exactly one neutral disposable child through the repaired helper from THIS agent-scoped root into empty temp `C:/Users/joji/Documents/programming/bc-v9r1-smoke-20260905-neutral` (empty at launch) with pwd-only prompt (no repo/source/project files). Returned `0f9f3033-acef-4967-bffd-93fba3e16dac`.
- Hard verification PASS via final frozen helper bytes: Paseo `ParentAgentId` null + Cwd exactly staging + Model exactly `opencode-go/muse-spark-1.3-contributor` + Provider `omp`; OMP exactly-one session (timestamp `2026-09-05T07:41:23.409Z` vs inspect `CreatedAt` `2026-09-05T07:41:23.963Z`, delta 0.55 s), model exact, `resolvedModelIsFallback` literal false. (First launch attempt exposed the async-flush race as count=0; bounded poll added to the helper — launch path untouched — and the same child re-verified PASS. No second child was spawned.)
- Child observed idle; `paseo stop` issued (no-op, already idle). No author/reviewer/C role, no candidate/benchmark/protected action. Pinned in lock.

## 6. Freeze record (frozen BEFORE source-truth content; immutable afterward)

- `GENERATION_PLAN.json` 32875 bytes SHA `2e6f8e0dfa2f25fc0af6f452b97d74658480588f712926eb650db822a207c002` (v9r1 identity; supersedes v9 plan `386bc79a…`; reserve 42/50/42/50/36/40/46/54=360 + location 12/14/12/16/10/12/14/18=108 unchanged).
- `RUBRIC.json` 3334 bytes SHA `e3d1bcf9192b…` (`dimensions`/`judgment_rules`/`role` identical to v9; diff keys `plan_version` + `rubric_version` only, now `retrieval-v3-dev-generation-v9r1-rubric-v1`).
- `PLAN_LOCK.json` 5046 bytes SHA `47ea88e069ba2da18dbfbb693b4b5ca7020b7425651c38ecc07d7e84d205ac59` (`frozen_at` `2026-09-05T07:45:20+00:00` truthful observed; source_truth false incl new `v9_…_in_this_stage` flags; d070–d080 + v9 semantic flags false; git-object-scan 0; carry-from-v9 recorded; 19 mechanics SHA-pinned incl repaired helper; `supersedes_v8_plan` + `supersedes_v9_plan`; v9 HOLD SHAs preserved; smoke pinned).
- Static verification before source truth (observed): all 19 mechanics compile (LF canonical, no CRLF); `run_selector.load_plan_binding()` hashes actual plan `2e6f8e0d…` and asserts lock binding PASS; 13 sections (`final_counts`, `reserve_counts`, `reserve_factor`, `authoring_contracts`, `a_b_packets`, `a_b_protocol`, `c_packets`, `c_protocol`, `agreement_diagnostics`, `disagreement_bundle`, `final_selector`, `mechanical_validators`, `standing_contract`) verified identical to v8-via-v9; 8 exclusion sets byte-identical; residuals 0 (`v3g9-`/`v9c-`/`generation-v9` non-r1 forms, `PLAN_SHA` literals, stale seal labels); `source_truth.jsonl`/candidates/anchors/sealed/staging absent in v9r1 builder (`input/` holds exactly the 10 fingerprint/manifest files).
- Gate: this record is committed+pushed and remote-verified BEFORE any Phase C source-truth content read. Post-freeze rule in force: NEVER mutate v9r1 plan/rubric/lock; infeasible/contract-invalid → STOP/HOLD, no supplement/relabel/retune/recycle.

## 7. End state and STOP

- Main contains only plaintext-free D-081-SC records (this doc + `D-081-SC` block + SESSION-LOG entry). Private v9r1 builder contains exclusions + scripts + plan/rubric/lock only; `source_truth.jsonl` ABSENT; candidates ABSENT; author/reviewer staging roots NOT created yet (smoke temp dir is neutral, outside builder, holds no source/candidate content).
- STOP for Web independent review. Phase C generation requires Web review/user continuation and is NOT authorized in D-081-SC. No D-082 execution.

## 8. Forbidden counts (this stage)

Forbidden counts all 0: source-truth snapshot, candidate generation, A/B/C, selector, benchmark/retrieval/ranking/latency/HTTP/model-encode, D068 retry/audit append/result, protected plaintext/recovery, `git cat-file` / `git show` / `checkout` / `restore` / sparse / worktree protected-data/object scanning, message/query content reads from session files (metadata-only scan), protected branch/tag/worktree/import, ml-service change, history rewrite, D074/D076/D078/D080/V9 row reuse (fingerprint-only exclusion excepted), D-081/v9 record mutation, D-082 execution, Desktop/browser/computer use.
