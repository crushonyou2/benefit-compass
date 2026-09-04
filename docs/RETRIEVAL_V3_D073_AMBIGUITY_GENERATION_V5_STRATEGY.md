# Retrieval v3 D-073 dev-v2 generation-v5 strategy — ambiguity paired-grounded alternatives + pre-result freeze

Status: D-073 NEW LOGICAL STAGE (user-authorized continuation). Plaintext-free. No generated query/gold plaintext on main.
Stage identity: D-073 creates an ambiguity-generation strategy and a generation-v5 PRE-RESULT freeze ONLY. No source-truth snapshot, no candidate generation in D-073.

## 1. Reconciled base (this record phase, actual repo/Git/remote/SSOT wins)

- Branch `codex/retrieval-v3-user-search-quality` HEAD `91a4a8248bac59eee4b9133cf6f47a54ac2dff07` clean, local = upstream = direct remote identical.
- `git diff --check` PASS; `git diff HEAD -- ml-service/` 0.
- Frozen six byte-identical: prereg `7842018613d66aa4570f4db2f8ae5a698ceb46757995a6b7e26873177b36160e`, plan-v4 `a25d9c482094696ff7a438593979813ac568c91a977a2543a50618ca4f5177d6`, safe-action `c512fb5627179697a987b05a2431b8f7e30d1153af2ff6dca37995f6b232a35d`, policy-v2 `6fee9ec22d5d3ac153ff19a6b1b5d27ab6a6a43bda11e35821d689f938968fe5`, link-V2 `f028ce4697f1a19e8d37e9048f6d7cd07d87c35ad68478d0efa968b7c62a7e71`, cost-V1 `5891b0bab0621da71499c5c2c6a21a6ac6692bd3ee94d6cb5342adc480958323`.
- Audit `eval/retrieval-v3/audit/events.jsonl` 4 events SHA `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506` byte-identical (D-068 open grant/run untouched).
- Canonical result absent; `eval/retrieval-v3/dev/` + `holdout/` absent on main; no dev-v2 branch/tag.
- OMP `18.1.5`; root/plan `opencode-go/muse-spark-1.3-contributor:xhigh`; no project override (`opencode.json`/`.opencode.json` absent); no child-agent fallback through Phase B.
- No protected plaintext recovery, no `git show`/`cat-file`/`checkout`/`restore` of protected evalsets, no audit append/run/result/benchmark/retrieval/ranking/model/latency/HTTP, no candidate tuning/B, no ml-service change, no protected branch/tag/worktree/import, no history rewrite in this stage.

## 2. D-072 substantive HOLD preserved + web-verified factual correction (append-only; old text never edited)

- D-072 substantive HOLD remains valid: C-authoritative total ambiguous 8<23 and loc 2<7. The selector uses C-total 8, so the verdict is unchanged.
- Private v4 builder `bc-v3-dev-v2-builder-20260904-v4` preserved byte-for-byte. Its 360 rows are failed-generation evidence only: DO NOT reuse, relabel, or supplement them.
- NEW WEB-VERIFIED FACTUAL CORRECTION (recorded append-only here; D-072 text untouched): D-072 durable diagnosis said `46 ambiguous-intended -> C-ambiguous 8`. Exact mechanical join of v4 `candidates_merged` to `adjudicated_pool` shows ambiguous-intended 46 -> C strata: ambiguous 6, exact_navigation 20, natural_needs 17, exploratory 1, multi 1, unsupported 1. C-ambiguous total 8 consists of intended ambiguous 6 + natural_needs 1 + short_keywords 1. HOLD stays unchanged because the selector uses C-total 8.
- This correction changes provenance bookkeeping only. Generation/annotation/C coverage/selector evidence, gates, forbidden-action counts, frozen artifacts, audit lifecycle, and protected-data disposition are unchanged.

## 3. v4 ambiguous construction evidence (failed-generation diagnostic only, not reusable truth, not a new gate)

- v4 ambiguous construction: 46/46 intended-ambiguous rows had exactly ONE source-truth anchor; ledger fields `base_intent`/`removed_span`/`referent_type`/`final_query`/`possible_completions`, exactly 3 completions each, but completions were not individually tied to distinct source-truth anchors.
- Referent types: 31 beneficiary, 7 scope, 7 condition, 1 target.
- Standing D-023 semantic construction was unchanged in v4 (exactly one essential referent dimension omitted; no exact title; no broad multi-result request; location alone must not remove ambiguity; labelable ambiguity safety-only semantics).
- Diagnosis: single-anchor plus imagined completions did not yield adjudicated ambiguity under genuine A/B/C. This evidence motivates the v5 author-provenance change below and nothing else.

## 4. V5 identity and unchanged final contract

- New private builder only: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260905-v5`. Never D-070/D-071/D-072 directories.
- New identity: plan_version `retrieval-v3-dev-generation-v5`; seed `benefit-compass-retrieval-v3-dev-v2-generation-v5-2026-09-05` (new builder only).
- Final contract EXACTLY unchanged: total 180; strata 21/25/21/25/18/20/23/27; headline first-six 130; safety ambiguous 23 + unsupported 27 = 50; location exact 54 at 6/7/6/8/5/6/7/9. 18 candidate configs/gates unchanged.
- Reserve remains uniform 2.0x, exactly 360 slots 42/50/42/50/36/40/46/54 and location 108 at 12/14/12/16/10/12/14/18. Do NOT inflate or target reserve from D-071/D-072 outcomes. Symmetric construction capacity only; no gate change.

## 5. V5 ambiguous authoring construction (strengthens author provenance only; annotation semantics/gates unchanged)

- Standing D-023 semantic construction still governs: exactly one essential referent dimension omitted; no exact title; no broad multi-result request; location alone must not remove ambiguity; labelable ambiguity safety-only semantics unchanged.
- Replace single-anchor plus imagined completions with PAIRED-GROUNDED ALTERNATIVES. During future authoring AFTER a fresh snapshot, every intended-ambiguous row must start from exactly TWO DISTINCT source-truth anchors/interpretations A and B. They must share one coherent user-need frame and differ materially on exactly ONE declared essential referent dimension. The final query is the shared surface form after that dimension is omitted, so clarification is required to choose A vs B. The two alternatives are construction evidence only, never final labels/golds.
- Private ledger schema at minimum: `anchor_a {source,source_id}`, `anchor_b {source,source_id}`, `shared_need_frame`, `omitted_dimension`, `completion_a`, `completion_b`, `distinguishing_evidence_a`, `distinguishing_evidence_b`, `final_query`. Never expose ledger/intended stratum/quota to A/B/C.
- Mechanical validators only: two anchor IDs are distinct and exist in pinned snapshot; both ledger branches structurally complete; exactly one `omitted_dimension` declared; final query excludes normalized exact-title substrings and recorded differentiating spans from both alternatives; final query differs from both completed intents; no broad multi-result wording; query fingerprint exclusions pass; for location-bearing ambiguous slots BOTH alternatives share the same explicit location and `omitted_dimension` is non-location, so the location cannot resolve ambiguity. Validators MUST NOT decide ambiguity/stratum/answerability/golds. No semantic challenger/prefilter before A/B/C.
- Keep all other seven D-023 authoring contracts unchanged (exact, natural, exploratory, multi, short, colloquial, unsupported with their frozen mechanical checks).

## 6. Unchanged annotation, agreement, selector, rubric rules

- A/B independent ALL 360 and C EVERY 360 protocol unchanged. C final authoritative, no fallback. Agreement method from D-072 unchanged (query_dim_any/gold_any/full_agreement plus task-local per-gold union+ABSENT diagnostic). Exact selector unchanged (lexicographically-smallest feasible 180 on C-rows only; selected-only gold uniqueness; infeasible -> STOP/HOLD; no supplement/relabel/plan edit).
- Rubric semantic definitions MUST remain byte-semantically identical to v4 (ambiguity != unlabelability verified: dimensions/judgment_rules/role equal); only truthful plan/rubric version metadata changed to v5. No quotas/intended labels in rubric.

## 7. Plan lock and boundaries (frozen BEFORE fresh source truth)

- Freeze `GENERATION_PLAN.json`, `RUBRIC.json`, `PLAN_LOCK.json` BEFORE fresh source truth. Lock truthfully says `source_truth_content_read_for_this_plan=false`, `d070/d071/d072_semantic_rows_read_for_plan=false` (except aggregate/structural facts supplied by Web prompt), `protected_old_plaintext_read=false`. Once frozen NEVER mutate.
- D-073 ends after durable SHA record commit/push remote verification. Phase C generation is a later logical stage requiring Web review/user continuation. D-073 does NOT snapshot source truth or generate any candidate.
- Boundaries restated: D-068 consumed/open untouched; holdout sealed/unused; no launcher/grant/run_start/run_end/result/benchmark/tuning/Candidate-B; no protected branch/tag/worktree/import; no ml-service change; no history rewrite; frozen six + audit bytes preserved; main stays plaintext-free; normal commits/pushes only.

## 8. Phase B freeze record (frozen BEFORE source-truth content; immutable afterward)

- Builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260905-v5` (new directory; never D-070/D-071/D-072).
- Exclusion (`build_exclusions.py`): v4 `candidates_merged.json` (SHA `f72b39dda184743014cd8484ab6106513a50bb549c92702a2ae9011f4e28a612`) query_text ONLY -> SHA256(NFC->strip->collapse whitespace->casefold), sorted unique 360/360 -> `input/failed_d072_query_fingerprints.json` SHA `ff3f65d60b1af9bb0d5dc9dac67a1ce4ad55704904e18c72c96ca3f38380ddde`. No old plaintext printed/stored outside the v4 builder; no D-072 labels/golds/ledgers/mappings read. Byte-carried fingerprint-only inputs verified identical to v4 manifest: D-070 `0acc6f279fb3c89db3d5df9a8268cfc668571401945830d99763384216f06b53` (273), D-071 `3a037d988bba8993cca642cd3e2e2c40dbb003301efe77b1d652328570e320f9` (273), dev-v1 `57716c6a6b3aaa08e9e8072f7148aac691d80ed81fdc7e10bd07957386035f88` (180q/228g), holdout `3463a8a1737c19b9a4a7536d7c8f3d92051c8526506096ecaea2d54d3d7f8bc1` (250q/212g), history `42e8534d578bc45808d6546bee9f59a49564ad455cd3b693d23853676d169454` (248q/248g). Zero protected branch/tag/worktree contact in this stage. Manifest `input/EXCLUSION_INPUTS.json` SHA `883d71cea5462beeef4c4fb92b024de36c3db55aeea3eae8a890a46861d2e2b1`. Required new-query overlap 0 vs all six failed/canonical sets; required new-gold overlap 0 vs canonical dev-v1/holdout/history.
- Frozen (`freeze_plan.py`, canonical single-line bytes + LF): `GENERATION_PLAN.json` 16711 bytes SHA `70cc98ff78c332005c3e4cdc8718c86b0c5c753bcb8e41bcf2ef7c56c2d0726a` (version `retrieval-v3-dev-generation-v5`, seed `benefit-compass-retrieval-v3-dev-v2-generation-v5-2026-09-05`, reserve 42/50/42/50/36/40/46/54=360 + location 12/14/12/16/10/12/14/18=108, paired-grounded ambiguous contract, seven other contracts unchanged, A/B-all-360 + C-every-360, D-072 agreement scope + task-local per-gold method, exact lexicographically-smallest selector with selected-only gold uniqueness); `RUBRIC.json` 3330 bytes SHA `249892030c0bb2f78e6045050a71348adfc22cc201b6e79e581e55405bf77aff` (v5 rubric, dimensions/rules/role byte-semantically identical to v4, only version metadata changed, ambiguity != unlabelability stands); `PLAN_LOCK.json` SHA `dff69b0734b1c0bc76860ffa4857698dfde3e3b74607ce6f9731b30e33ccb38b` (`frozen_at` `2026-09-04T17:24:27+00:00`). Lock flags all false: `source_truth_content_read_for_this_plan=false`, `d070_semantic_rows_read_for_plan=false`, `d071_semantic_rows_read_for_plan=false`, `d072_semantic_rows_read_for_plan=false`, `protected_old_plaintext_read=false`. Plan/rubric contain zero query/gold plaintext (0 non-ASCII bytes).
- Provenance (actual, observed): OMP `18.1.5`; root session model `opencode-go/muse-spark-1.3-contributor:xhigh` (runtime context; model config never changed); no project model override (no `opencode.json`/`.opencode.json`); no child agents spawned through Phase B; no fallback model used. Phase C child agents/sessions will be recorded with their model/session evidence at spawn time.
- Gate: this record is committed+pushed and remote-verified BEFORE any Phase C source-truth content read. Post-freeze rule in force: NEVER mutate plan/rubric/lock; infeasible -> STOP/HOLD.

## 9. End state and STOP

- Main contains only plaintext-free D-073 strategy/freeze records. Private builder contains exclusions + plan/rubric/lock only; `source_truth.jsonl` ABSENT; candidates ABSENT.
- Verify clean local=upstream=direct remote, diff-check PASS, ml-service 0, frozen six/audit exact, result/dev/holdout absent, no dev-v2 protected refs.
- STOP for Web independent review. Phase C generation requires Web review/user continuation and is NOT authorized in D-073.
