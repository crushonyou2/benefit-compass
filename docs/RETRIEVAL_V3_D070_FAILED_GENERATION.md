# Retrieval v3 D-070 failed generation — durable noncanonical evidence record (plaintext-free)

Status: **FAILED GENERATION — CONTRACT_INVALID_GENERATION**. Local STOP before seal/import was correct.
This 273-query pool is **noncanonical**: do NOT complete, repair, relabel, or reuse it as truth, seed, or partial pool.
Fresh restart only (D-071 generation-v3). No query text, golds, or protected plaintext below — SHAs, counts, and gate evidence only.

## 1. Reconciled base (this record phase)

- Branch `codex/retrieval-v3-user-search-quality` HEAD `93f8bc0158c10138718b1f31a6fe9719d9fb4f93`, clean, local = upstream = direct remote.
- `git diff --check` PASS; `git diff 5327661..HEAD -- ml-service/` 0.
- Frozen six byte-identical: prereg `78420186…`, plan-v4 `a25d9c48…`, safe-action `c512fb56…`, policy-v2 `6fee9ec2…`, link-V2 `f028ce46…`, cost-V1 `5891b0ba…`.
- Audit `eval/retrieval-v3/audit/events.jsonl` 4 events, SHA `90cfb54d…`, byte-identical (D-068 open grant/run untouched).
- Canonical result absent; `dev/` + `holdout/` absent; no dev-v2 branch/tag.
- OMP `18.1.5`, default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`, no project `.omp` override.

## 2. Failed builder identity (bytes preserved, not mutated)

- Private builder (outside repo, never reused): `bc-v3-dev-v2-builder-20260904`.
- `GENERATION_PLAN.json` `dcb8fa5b142191ea992de5e276bb5ecef5387dbf2154b913fb6f7b4fe9712872` — version `retrieval-v3-dev-generation-v2`, seed `benefit-compass-retrieval-v3-dev-v2-2026-09-04`.
- `PLAN_LOCK.json` `42bbe4678404ab01e7a2050d12f79f94b253b39416a407f5f1590e28f5f267b6` — `mutated_after_freeze false`.
- Source-truth aggregate only: `3ba5b1aaf122fdafe3c04b929eed6d584ee09213bc82366fc33983467153df41`, 13589 rows (youth 2631 / gov24 10958).
- Pool: 273 candidates, `reserve_quotas_met true`, `bad_anchors 0`, query overlap 0 vs dev-v1 / 0 vs history union / 0 vs holdout.

## 3. Annotation aggregate (SHAs + diagnostics only)

- `raw_A_H1` `7c7c8edb…`, `raw_A_H2` `964fbb68…`, `raw_B_H1` `ebf97fb8…`, `raw_B_H2` `7410813f…`, `c_output_1` `e11d48da…`, `c_output_2` `66ff912b…`, `candidates_merged.json` `b8c4db36…`, `adjudicated_pool.json` `c0fba5e4…`, `agreement_audit_builder.json` `04f082faed14be006d41ac11ef57c8a13215c5da96b7ac9e82e62ba8f333d67f` (full SHAs in D-070 ledger entry).
- A/B disagreements 210/273; kappa stratum 0.6569 / answerable 1.0 / ambiguous 0.7607 / location 1.0 / per-gold 0.0166.
- Local census (noncanonical): ambiguous need 23 pool 13 `SHORTFALL_10`; natural_needs_location need 7 pool 5 `SHORTFALL_2`; short_keywords need 18 pool 13 `SHORTFALL_5`; verdict `HOLD_FEASIBILITY` (`2026-09-04T11:29:59+00:00`).
- `D070_HOLD_SUMMARY.json` `4814d2a9c7d937fac747ff424953e6905638e2e82679bec8ac197ad4ab5b6fe4`.
- Forbidden counts all 0; not done: no seal, no protected branch/tag/worktree, no main record (before D-070), no dev-v2 run, no holdout contact.

## 4. Web independent disposition (authorized correction)

Local STOP was right; `HOLD_FEASIBILITY` is not the canonical root cause. Canonical root cause: **CONTRACT_INVALID_GENERATION** —
(1) generation-v2 taxonomy weakened D-023 mutually-exclusive authoring rules (short_keywords exact 2–3 tokens + title/fragment/broad/≥2-constraint exclusion with exact-title substring mechanical validator; ambiguous essential-referent omission + no exact title/broad + location-alone rule). Aggregate symptoms only: intended short 27 → final short 13 / exact 13 / ambiguous 1; intended ambiguous 35 → final ambiguous 10 / exploratory 10 / natural 15. No reserve/quota change.
(2) Standing D-023/D-033 requires A/B + third C on EVERY query; D-070 ran C only on 210/273 disagreements and merged 63 agreements without C — census not canonical feasibility evidence.

Do NOT repair/relabel/complete D-070. Do NOT run C on the missing 63. Preserve builder bytes. Fresh D-071 restart only.

## 5. Untouched

D-068 consumed/open and untouched; audit unchanged; frozen six unchanged; `ml-service` 0; no history rewrite. Standing D-013/D-015/D-017/D-023/D-033/D-034/D-035/D-068/D-069 preserved.
