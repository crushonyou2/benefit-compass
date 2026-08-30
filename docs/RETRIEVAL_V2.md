# Retrieval v2 — Status (SSOT)

> This page is the current SSOT/status page for Retrieval v2. It does not rerun evaluations and does not propose a new candidate.

## Contract

- **D-003** — production retrieval contract (`RERANK=0`, `CANDIDATES=30`, `COSINE_MIN=0.78`, `LEXICAL_OVERLAP_BIAS=0.01`, `strip_region`, expired-policy exclusion, `intfloat/multilingual-e5-base`, source-aware youth bias).
- **D-004** — rejected alternatives remain out of scope (cross-encoder reranking, global similarity/abstention threshold, public region search) unless materially new evidence justifies reconsideration.
- **D-007** — Retrieval v2 evaluation contract. Primary metric source-macro Recall@5; final-holdout quality requires candidate > baseline, net hit@5 ≥ +2, no Youth/Gov24 regression; P0 gates Youth ≥ 28/60 and Gov24 ≥ 15/21; hard-negative paired safety (pure-positive not lower, intrusion not higher); warm paired latency non-regression `candidate p95 <= paired baseline p95`; GO only if all 7 mandatory checks pass (quality improvement, +2 net, no per-source regression, P0 PASS, hard-negative PASS, latency non-regression, holdout integrity). HOLD = fixable mandatory failure; NO-GO = clear quality regression/failure to improve. A GO does not itself authorize production rollout. **Cycle 2 uses same contract; latency requires fresh paired measurement.**
- **D-008** — Retrieval v2 evaluation cycle 1 closes as **HOLD** (2026-08-30). Candidate-v2 and all frozen cycle-1 artifacts remain immutable; no rerun/retune/threshold relaxation to manufacture PASS. Future cycle 2 is a separate evaluation cycle and must not retroactively change cycle-1 HOLD.
- **D-009** — Retrieval v2 evaluation cycle 2 starts (2026-08-30). D-003/D-004/D-007 unchanged; D-008 HOLD immutable; new independent holdout frozen before tuning; cycle-1 results not reused for PASS; latency gate still `candidate p95 <= paired D-003 baseline p95` with fresh measurement; cycle-2 candidate has separate freeze. Current phase: **dev frozen; Phase1 diagnostic + correction completed; Exp1 REJECTED; pre-Exp2** (no Exp2 execution yet, implementation untracked).
## Cycle 1 — frozen candidate

| item | value |
|---|---|
| candidate tag | `retrieval-v2-candidate-v2` |
| candidate commit | `5745cc3144b519da456b21030d0e0752d1d018ae` |
| artifact commit | `c6c082681b4f2fcd521790e50c5fd46549116307` |
| manifest | `eval/retrieval-v2/candidate/manifest.json` LF SHA256 `86f80ff6389ede4673e3c8d819cfab2ceefc79b8979a68b7b2bb5d64cc8eccff` |
| config | `lexical-rewrite-v1` (`lexical_overlap_terms_rewrite` — particle-stripped stem replacement, `MIN_STEM_LEN 2`) |
| production parity | `strip_region`, youth intent bias suppressed for Gov24 orgs, `LEXICAL_BIAS 0.01`, `CANDIDATES 30`, `COSINE_MIN 0.78`, no cross-encoder/threshold/region search |

## Cycle 1 — gate outcomes (no rerun; artifact/tag cross-verified)

| gate | result | detail | artifact | tag → commit |
|---|---|---|---|---|
| Final holdout quality (D-007) | **PASS** | 40 queries (Youth 20 + Gov24 20). Baseline 33/40 → candidate 36/40, source-macro 0.825 → 0.900, net +3 (gains holdout-001/028/036, losses 0), Youth 18/20→20/20, Gov24 15/20→16/20 | `eval/retrieval-v2/final/summary-v1.json` | `retrieval-v2-final-holdout-result-v1` → `d86e0119f9ac5cf3028364df24d898ff638d3b76` |
| P0 regression | **PASS** | Youth 28/60, Gov24 16/21 | `eval/retrieval-v2/p0/p0-candidate-v2.json` | `retrieval-v2-p0-result-v1` → `3373da294b73705861b7a0e494ba802f9e9f6786` |
| Hard-negative paired safety | **PASS** | pure-positive 15/21→16/21, excluded-policy intrusion 0/3→0/3 | `eval/retrieval-v2/hard-negative/paired-candidate-v2.json` | `retrieval-v2-hard-negative-result-v1` → `34ca5a537f0a537b9217e3b2fffd005b80a5fe19` |
| Warm paired latency (D-007) | **HOLD** | baseline p95 476.51 ms, candidate p95 480.55 ms, Δ +4.04 ms; D-007 requires `candidate p95 <= baseline p95`. p50 baseline 410.40 → candidate 395.82 (diagnostic), n=180 per variant (360 total), warmup 36/variant, interleaved paired design | `eval/retrieval-v2/latency/latency-candidate-v2.json` | `retrieval-v2-latency-result-v1` → `b04556f9251d6cabadd32c7c39c85dee690c8b48` |

Additional immutable refs: holdout `retrieval-v2-holdout-v1` (`12515a20758265b0b5a5f52acef5aa40de3b6253`, SHA `02eb03866f8e09b66ea7c3b83856fe939ee0b966350053277aaca3f2d7121eda`, 40 cases), evaluator `retrieval-v2-holdout-evaluator-v1` (`e32d3ebee871918bccf08613e34ae7a72d953737`), p0 evaluator `retrieval-v2-p0-evaluator-v1` (`63b9ac62dc980ca0a1ab84fe90456e85cdae1a18`), hard-negative evaluator `retrieval-v2-hard-negative-evaluator-v1` (`ba2b3099ea0daf67f47453390c24ccbc9a389819`), latency evaluator `retrieval-v2-latency-evaluator-v2` (`7b8c4ea868afc3eb8b4ab33f63b067bd23c087ba`, harness LF `66a4e48e9c71ecd03aa389ac93ac651817d3147355cb40d64511044357ac26e0`).

## Provenance & review

- Latency provenance SSOT: `retrieval-v2-latency-provenance-v3` — tag object `c0d2a9321114144b5ab4235a66c80faf6f112c57` → commit `3ac62181de9c343511adfb2db82cb0cc64b36009` on branch `codex/retrieval-v2-latency-provenance-recovery`.
- Independent reviewer verdict: **APPROVE** — measurement **provenance blocker resolved**, not latency PASS. Latency numerical gate remains HOLD.
- Superseded tags `retrieval-v2-latency-provenance-v1/v2` remain immutable audit history.
- Recovery scope: 3 files only (`PROVENANCE-RECOVERY.md`, `provenance-attestation-v1.json`, `test_retrieval_v2_latency_provenance_attestation.py`); no measurement rerun.

## Overall verdict

- **Cycle 1 = HOLD** per D-007/D-008. Quality / P0 / hard-negative success is explicitly distinguished from mandatory **latency failure**.
- Evaluation **GO not granted**; **production rollout not authorized**.
- Cycle-1 HOLD is durable and not retroactively changeable by a future cycle.

## Cycle 2 — current phase: dev frozen; Phase1 diagnostic/correction completed; Exp1 REJECTED; pre-Exp2 (no retrieval/DB/model run in this doc update)

- **Status:** D-009 started 2026-08-30; holdout frozen before tuning; dev frozen before tuning (tuning data, not sealed final holdout, but frozen so composition does not drift during tuning); Phase1 diagnostic completed (diagnostic_only), correction completed, Exp1 REJECTED, Exp2 not yet executed. No holdout plaintext access, no final gate executed in this session.
- **cycle2-start:** branch `codex/retrieval-v2-cycle2-start` from cycle-1 HOLD `5311e9807bab43f869655e13d4cdd006123f1ed5` → commit `434b798d60bf15433590362aaad4a021846094d4`; tag `retrieval-v2-cycle2-start-v1` object `f8d03d1b5565cd1e6dcda341bfe92230c7dab4cd` peeled `434b798` (verified remote).
- **holdout freeze:** remote branch `codex/retrieval-v2-cycle2-holdout-freeze` → commit `9e2cd6ea4b8203b474d7d6a6a69a088763284043`; tag `retrieval-v2-cycle2-holdout-v1` object `03da4cc28d1bb324f5176efb500dfeaa1684b3fa` peeled `9e2cd6ea4b8203b474d7d6a6a69a088763284043` (verified remote).
- **holdout aggregates (plaintext-free):** n=40 Youth 20 / Gov24 20, categories housing_finance 7 / family_care 7 / employment_education 7 / welfare_health 7 / culture_community 6 / business_agriculture 6, evalset `eval/retrieval-v2/cycle2/holdout/evalset.jsonl` LF SHA256 `cf003bab7713138fbd9c4622addeeb886c01f401aeab3d43b1144ae6e4c79727`, P0/dev/cycle1-holdout/hard-negative query+gold overlaps all 0, `retrieval_observed=false`, `candidate_tuning_started=false`, sealed before tuning.
- **dev freeze:** branch `codex/retrieval-v2-cycle2-candidate` → commit `372ed686579b4e8e2b9854d297e44fee18775352`; tag `retrieval-v2-cycle2-dev-v1` object `500beadae11ddb423cc2ea4d46494c0a9f2b1173` peeled `372ed686579b4e8e2b9854d297e44fee18775352` (verified remote).
- **dev aggregates (plaintext-free):** n=36 Youth 18 / Gov24 18, categories housing_finance 6 / family_care 6 / employment_education 6 / welfare_health 6 / culture_community 6 / business_agriculture 6 (each 3/3 balanced), evalset `eval/retrieval-v2/cycle2/dev/evalset.jsonl` LF SHA256 `c8b66fef69bdfd0db053ac7cac0fb027fc3271c6072ab992b622cacdc71ace5e`, P0/cycle1-dev/cycle1-holdout/cycle2-holdout/hard-negative query+gold overlaps all 0, `retrieval_observed=false`, `candidate_tuning_started=false`, frozen before tuning. No benchmark/retrieval/search/DB ranking or embedding/model load executed to create dev; cycle1 candidate per-case results not used for case selection.
- **candidate branch current:** branch `codex/retrieval-v2-cycle2-candidate` at `22d6e6c32b9a443d963d2db67698e779ec07a42d` (Phase1 diagnostic + correction + Exp1). Dev plaintext `eval/retrieval-v2/cycle2/dev/` present, holdout plaintext `eval/retrieval-v2/cycle2/holdout/` absent. Phase1 diagnostic artifacts `eval/retrieval-v2/cycle2/dev/phase1-*` and Exp1 artifacts `eval/retrieval-v2/cycle2/phase2-exp1-region-hint/` present on candidate branch; Exp2 embedding-hint implementation is untracked (not committed) and no Exp2 output artifact exists ( discarded per pre-cleanup instruction).
- **Phase1 diagnostic (diagnostic_only, not_final_gate):** commit `6d743bb366530cb34d03a3efd0a7860e221421c5` — baseline R@5 28/36 (Youth10/18 Gov24 18/18) vs candidate-v2 R@5 30/36 (Youth12/18 Gov24 18/18) net +2 gains `c2d-025` `c2d-031` losses 0; MRR baseline 0.6577 vs candidate 0.6884; latency diagnostic p95 baseline 487.31 ms vs candidate 546.50 ms delta +59.18 ms (diagnostic_only, 180/variant interleaved, warmup 18)
- **Correction:** commit `c2dfd87bf6602e78bef5ecbc09d297bfbf2a6f74` — corrected Phase1 `filtered_by_cosine` to threshold-only semantics and added `outside_top10_after_threshold` for `c2d-025` (threshold PASS but rank_top30 14 outside top10). No quality/latency numbers changed.
- **Exp1 — bounded region-core lexical hint (lexical-only, 1 SIDO canonical per matched code):** commit `22d6e6c32b9a443d963d2db67698e779ec07a42d` — **REJECTED** on dev 36 (quality early-stop): new R@5 30/36 (Youth12/18 Gov24 18/18, R@1 22/36 vs 21/36 candidate, MRR 0.7069 vs 0.6884) not > candidate-v2 30/36, net vs baseline +2 gains2 loss0 (`c2d-025` `c2d-031`), vs candidate-v2 net 0 gains0 loss0; hinted 23/36 cases avg 1.0; latency **NOT_RUN_EARLY_STOP** per spec; paired artifact `eval/retrieval-v2/cycle2/phase2-exp1-region-hint/phase2-exp1-paired.json`; production files diff 0; metadata youth_intent_bias corrected 0.01→0.015 in this commit (deterministic patch, no rerun)
- **Next:** clean baseline for Exp2 (embedding preserves at most one SIDO via earliest alias, lexical unchanged) — implementation untracked, not yet executed; no retrieval/DB/model run in this commit.

## Next state

- Phase1 diagnostic and correction completed; Exp1 REJECTED (no new hit@5 beyond candidate-v2). Exp2 (embedding at most one SIDO earliest, lexical unchanged) is prepared as untracked implementation; no output artifact yet. Clean baseline commit pending; no holdout access, no final gate.


## Known limitations (non-blocking)
