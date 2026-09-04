# Retrieval v3 D-071 dev-v2 generation-v3 plan — durable pre-result record (plaintext-free)

Status: **PLAN FROZEN — PRE-EXECUTION**. Source-truth content has NOT been read under this plan; no candidates generated yet.
D-070 generation-v2 stays preserved as noncanonical failed evidence (see `RETRIEVAL_V3_D070_FAILED_GENERATION.md`); it is never repaired, completed, or reused.

## 1. Base

Branch `codex/retrieval-v3-user-search-quality` at D-070 record `9e45c05`, clean, local = upstream = direct remote.
Diff-check PASS, `ml-service` 0, frozen six identical, audit 4 events `90cfb54d…` untouched (D-068 open grant/run preserved),
result absent, `dev/` + `holdout/` absent, no dev-v2 branch/tag. OMP `18.1.5`, default/plan xhigh, no project override.

## 2. New generation identity

- New private builder (logical identity `bc-v3-dev-v2-builder-20260904-v3`; D-070 directory never reused).
- `plan_version` `retrieval-v3-dev-generation-v3`, seed `benefit-compass-retrieval-v3-dev-v2-generation-v3-2026-09-04`.
- Future protected dataset identity remains dev-v2 (D-069): plan revision v3, not a dev-v3 dataset.

## 3. Frozen bytes (before source-truth content)

- `GENERATION_PLAN.json` 13477 bytes `558f7df7e8a15ad14ba686b32dd7bb1c32ebdb1477dfde32a234e92486bdc769`.
- `PLAN_LOCK.json` `f17d8e40e7ce1aeb7dbf84667a6a402ffe31be77c9575f21faec2b89223755e7` (`frozen_at` `2026-09-04T12:36:44+00:00`; `source_truth_content_read_for_this_plan`, `d070_semantic_rows_read_for_this_plan`, `protected_old_plaintext_read` all false).
- Neutral `RUBRIC.json` 2924 bytes `9ceda4ee52835e30aa556bd3fe95f2558751f5852576f3b8f332969bcf5521bc`.
- Failed-D070 exclusion `input/failed_d070_query_fingerprints.json` `0acc6f279fb3c89db3d5df9a8268cfc668571401945830d99763384216f06b53` (273/273 unique, hashes only) + dev-v1 `57716c6a…` + holdout `3463a8a…` + history union `42e8534d…` + manifest `001e44c0…`. Required new-query overlap 0 vs all four.
- Post-freeze: NEVER mutate; infeasible → STOP/HOLD; no expansion, relabel, retune, supplement, or D-070 recycle.

## 4. Exact counts (unchanged)

Final 180: 21/25/21/25/18/20/23/27; headline 130; safety 50 (ambiguous 23 + unsupported 27); location 54 (6/7/6/8/5/6/7/9).
Reserve 273 (uniform 1.5×, not tuned to D-070): 32/38/32/38/27/30/35/41; location slots 83 (9/11/9/12/8/9/11/14).
Headline validity, safety semantics, and 18-config candidate-plan-v4 stand unchanged.

## 5. Taxonomy, validators, A/B/C, selector

- Eight mutually-exclusive authoring contracts restored from standing D-023 (short: exactly 2–3 tokens + mechanical normalized title/substring/fragment exclusion; ambiguous: exactly-one-missing-referent + private omission ledger never shown to annotators; colloquial: salient perturbation + private ledger; unsupported: exhaustive snapshot-negative validation).
- Mechanical validators reject/advance only; never assign semantic truth.
- A/B independent opaque packets `{item_id, query_text}` for all 273; C judges EVERY 273 exactly once (disagreement rows: frozen disagreement dimensions/values only; agreement rows: query only, no A/B labels); C final authoritative everywhere; residual 0.
- Exact deterministic feasibility selector: ascending-ID include-first backtracking with provable-infeasibility pruning for the lexicographically smallest feasible 180 tuple; infeasible → STOP/HOLD. Future case IDs `v3d2-001..v3d2-180`.

## 6. Boundaries

Forbidden counts all 0 (D-068 retry, D-070 reuse, audit append, dev-v2 run, holdout/plaintext access, plan mutation, tuning, config changes, production changes, history rewrite, protected refs).
Even after a passing local seal: NO freeze branch/tag, NO worktree/import, NO audit append, NO benchmark, NO holdout contact — STOP for Web independent review.
