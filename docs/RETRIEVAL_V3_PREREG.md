# Retrieval v3 — User Search Quality — FINAL REPAIR Prereg (Freeze) — Supersedes D-014, Governed by D-015

> **FINAL REPAIR prereg — 2026-09-01 — Q-006 closed → D-014 (historical) → superseded by D-015, pilot 100 evidence + auditable re-audit, Web HOLD repair. Candidate implementation is still NOT performed in this stage.**
> This FINAL REPAIR prereg locks exact benchmark sizes, exact allocations, headline denominator BY CONSTRUCTION, Wilson/Clopper precision rule with deterministic PASS/HOLD/NO-GO, deterministic safety gates, exact Candidate B admission, exact paired latency methodology, MAX 24 dev-tuning freeze, retrieval-blind annotation/adjudication protocol, protected-set freeze/isolation, audit/provenance, one-shot final holdout, rerun prevention, and explicit next stage. Results remain unseen; no post-result tuning loopholes. D-014 sizing/provenance interpretation is superseded per Web HOLD; D-013 remains standing. V3 candidate tuning / dataset freeze begins only after this commit, in separate isolated stages.

> **Pilot provenance (original, preserved as historical evidence):** `eval/retrieval-v3/pilot/pilot_tasks.jsonl` SHA256 `b3250e592d4c80099e29d20d1bf87594f2bac11a59907ac8067d3e1ddbd65da3` (100 lines), `pilot_report.md` SHA256 `f3a01a5f286705df9e9ca6cc8cf6d5fd320a427093649072bc1d5f559e6c669f`, `pilot_provenance.json` SHA256 `64f2dbecb49cf624e0e6b05d84f4c3e1db8876406b473b18ed7526078920b2d2` — single annotator + independent reviewer, 99% labelable / 85% **conceptual** answerable raw / 13% ambiguous / 30% location-bearing / 7% disagreement claim (93% agreement) — **not auditable provenance; not claimed proven here**.

> **Pilot re-audit (auditable correction, 2026-09-01):** sanitized input `pilot_reaudit_input.jsonl` SHA256 `a47bb525f7966d7c23a06e57fc361119eca1c610e0cc1caf77e4cf2cd828aea3` (task_id+query_text only, 100 lines, excludes all label fields), `reviewer_A_raw_labels.jsonl` SHA256 `2d8a84b93d1e62870d42978d1d51ddef18373da6b6809d65d33d069929eba1eb`, `reviewer_B_raw_labels.jsonl` SHA256 `15b98f3522ed9acd560aa5bb75f7fc30991fb2815f6521bfbeadbb171f5fcb89`, `disagreement_matrix.json` SHA256 `f6b7a5ae1ae2aebaf9b1eb6a42894016b7f79c39a56aa2ec207d6127c6dc1f40` (recomputable: any_disagreement 19/100 (19%), stratum 7/100, location 2/100, conceptual_answerable 3/100, ambiguous 2/100, golds 9/100), `adjudicated_labels.jsonl` SHA256 `fe198a28676f5b628f803a2cf60a2ecce0aaa0bccae262389363ed82c58d3f2a` residual 0, `reaudit_protocol.json` + `adjudicator_provenance.json` + `pilot_correction.json`. **Pilot answerability is CONCEPTUAL/INTENT only (not corpus-grounded); final benchmark answerability is source-truth grounded.**

## 0. Reconciled base

| item | value |
|---|---|
| Branch | `codex/retrieval-v3-user-search-quality` |
| Base | `5327661445c37191a3fd61db195f3af4d2cf893a` (tag `retrieval-v2-cycle3-closure-v1` object `0c94d801da23050d0c9537717b2a3e83ee1b0bf6`, peeled commit verified) |
| Prior HEAD | `26e819e63fd658c24ce55e26838ccc058003f713` (D-014 freeze) — not rewritten, this REPAIR is append-only |
| Standing decisions | D-003 / D-007 / D-008 / D-010 / D-011 / D-012 remain history/contracts as applicable; **D-013** supersedes D-004 only for conditional reranking reconsideration and **remains standing**; **D-014** → **superseded by D-015 (2026-09-01) per Web HOLD**; **D-015** now governs |
| Q-006 | **closed → D-014 (historical) → superseded by D-015** — exact sizes, allocations, CI rule, latency, safety, B gate, tuning boundary now fixed under D-015 |
| Pilot | `retrieval-v3-pilot-100-v1` executed retrieval-blind (§2 evidence) + auditable **re-audit** `retrieval-v3-pilot-100-v1-re-audit-2026-09-01` (all 100 reviewed for stratum/location/conceptual-answerability/ambiguity + all 100 for grade/equivalence, two independent reviewers + adjudicator, 19/100 disagreement recomputable) |
| Production `ml-service` diff vs D-012/closure baseline | **`0` — `git diff 5327661..HEAD -- ml-service/` 0** preserved |

## 1. Goal and headline gates (D-013 + D-015 final sizes)

- **Goal:** user-satisfying search — system returns what the user actually needs for representative user intent queries over the benefit-compass policy corpus.
- **Headline metric (labelable + source-truth-grounded answerable tasks only):** **Success@5 grade≥2** — at least one result in top-5 is grade 2 (acceptable) or grade 3 (perfect) on a 3/2/1/0 multi-gold graded scale with equivalence groups.
  - **Release floor:** **Success@5 ≥85%** on representative answerable user-intent tasks (holdout **headline** set — see §3).
  - **Strong / stretch target:** **Success@5 ≥90%** — not promised, aspirational; if `≥90%` and Wilson lower bound `≥85%`, noted as **strong**.
- **Benchmark sizes (FINAL REPAIR, frozen before tuning) — exact, headline denominator BY CONSTRUCTION:**
  - **Pilot 100** (already executed, retrieval-blind, no system results): 100 tasks — strata `12/14/12/12/10/12/13/15` (exact/natural/exploratory/multi_constraint/short/colloquial/ambiguous/unsupported), location-bearing 30. **Conceptual answerability only** — not corpus-grounded.
  - **Dev (tuning/diagnostics): 180 total tasks exact** — strata exact `exact_navigation 21, natural_needs 25, exploratory_multi_valid 21, multi_constraint 25, short_keywords 18, colloquial_typo_spacing_abbrev 20, ambiguous 23, unsupported_no_answer 27`. **Headline = first six strata only = EXACT 130 source-truth-grounded, unambiguous, labelable tasks.** Ambiguous 23 + unsupported 27 safety-only (not headline). **Location-bearing EXACT 54 (30%)** cross-cutting across strata.
  - **Holdout (final one-shot): 250 total tasks exact** — strata exact `exact_navigation 28, natural_needs 33, exploratory_multi_valid 31, multi_constraint 36, short_keywords 24, colloquial_typo_spacing_abbrev 28, ambiguous 32, unsupported_no_answer 38`. **Headline = first six only = EXACT 180 source-truth-grounded, unambiguous, labelable tasks.** Ambiguous 32 + unsupported 38 safety-only. **Location-bearing EXACT 75 (30%)** cross-cutting.
  - All totals and headline 130/180 and location 54/75 are **exact post-freeze invariants** — not minimums that can drift. Builders must reject/replace any unlabelable/misclassified item before seal; final counts above must remain exact (replace, not shrink). Sums verified: dev 21+25+21+25+18+20=130 headline +23+27=50 safety =180 total; holdout 28+33+31+36+24+28=180 headline +32+38=70 safety =250 total. All totals exclusive of every v2/Cycle3 history case (union 248) and of each other — overlap 0 required via fingerprint checks (query `SHA256(NFC+strip+collapse_whitespace+casefold)` and gold `SHA256(source+NUL+source_id)`).
- **Supporting gates (required before release, diagnostic + safety, headline is not sufficient alone):** safety (unsupported/ambiguous), ineligible/expired intrusion, official-link, latency/cost; secondary Top1/Top3/MRR@10/NDCG@5/NDCG@10 per-slice diagnostics (§5–§6 + §9).
- **No public claim before sealed final evidence** on the protected holdout (frozen before tuning, independent review PASS, explicit user approval, one-shot evaluation — see §9).
- **Rollout:** no rollout is authorized by D-013/D-015 or this FINAL REPAIR prereg.

## 2. Retrieval-blind pilot — 100 user-like tasks + auditable re-audit

### 2.1 Original pilot (preserved historical evidence)

The retrieval-blind pilot required by the bootstrap has been executed exactly as preregistered (but provenance is not auditable — see 2.2 correction):

- **Purpose:** validate labelability / strata / annotation without inspecting system retrieval results.
- **Method:** 100 user-like tasks spanning strata in §3 from user-intent patterns **without running retrieval**. Annotators labeled labelability, **conceptual** answerability, ambiguity, gold equivalence, strata only.
- **Annotation protocol (original, not auditable):** **single annotator + independent reviewer — no fabricated second human annotator** (prereg-permitted alternative). Primary author drafted 100; reviewer re-labeled 100% for strata/conceptual-answerability/ambiguity/location and 30% subsample (n=30) for grade/equivalence. Final labels in `pilot_tasks.jsonl`. **Disagreement provenance not durable — 7% claim not proven.**
- **Outputs (observed, conceptual):**
  - labelability **99%** (99/100; 1 unlabelable `v3p-042` contradictory age bounds)
  - **conceptual** answerability **85% raw** (85/100; 84/99 84.8% among labelable) — **concept-level intuition, not corpus-grounded**
  - ambiguous **13%** (13/100; distribution 4/3/3/3) — all 13 ambiguous tasks were **conceptually answerable=True** in original, while prereg says ambiguous is **safety-only** — contradiction that D-015 repairs (§3)
  - strata coverage every stratum ≥10, location-bearing 30%
  - instruction revisions (3): contradictory-query exclusion, ambiguity handling (clarification vs safe abstention), exploratory equivalence-group rule
  - Full metrics in `pilot_report.md` §§3–8

### 2.2 Re-audit correction (auditable, 2026-09-01 — repairs HOLD A/B)

- **Sanitized re-audit input:** `eval/retrieval-v3/pilot/re-audit/pilot_reaudit_input.jsonl` SHA256 `a47bb525f7966d7c23a06e57fc361119eca1c610e0cc1caf77e4cf2cd828aea3` — 100 lines `task_id + query_text` only, **excludes all label fields** (`stratum`, `location_bearing`, `answerable/conceptual_answerable`, `ambiguous`, `golds`, etc.). No system results/protected data exposed.

- **Two genuinely independent delegated annotators (separate sessions, no shared state, blind to each other):**
  - Reviewer A: `reviewer_A_raw_labels.jsonl` SHA256 `2d8a84b93d1e62870d42978d1d51ddef18373da6b6809d65d33d069929eba1eb` + `reviewer_A_provenance.json` (agent_label AnnotatorA, timestamp, model_role Muse Spark 1.2 delegated, sanitized_input_sha256)
  - Reviewer B: `reviewer_B_raw_labels.jsonl` SHA256 `15b98f3522ed9acd560aa5bb75f7fc30991fb2815f6521bfbeadbb171f5fcb89` + `reviewer_B_provenance.json` (blind to A)
  - Both reviewed **all 100 for stratum/location/conceptual-answerability/ambiguity** and **all 100 for grade/equivalence** (exceeds prereg `30% stratified sample` requirement; full 100 preferred per repair spec; grade 3/2 boundary on exploratory is the hardest).
  - OMP delegated session identifiers are not durably obtainable via filesystem — recorded as `agent_label + timestamp + SHAs` without overclaiming independence (see `reaudit_protocol.json: session_identifiers_limitation`).

- **Separate adjudication:** `adjudicated_labels.jsonl` SHA256 `fe198a28676f5b628f803a2cf60a2ecce0aaa0bccae262389363ed82c58d3f2a` — third adjudicator C resolves all 19 disagreements deterministically (log `adjudication_log.json`, residual 0; provenance `adjudicator_provenance.json`).

- **Disagreement recomputable:** `disagreement_matrix.json` SHA256 `f6b7a5ae1ae2aebaf9b1eb6a42894016b7f79c39a56aa2ec207d6127c6dc1f40` stores **any_disagreement 19/100 (19%)**, per-dimension `stratum 7/100, location 2/100, conceptual_answerable 3/100, ambiguous 2/100, golds grade/equivalence 9/100, labelable 0/100`, stratum confusion matrix, detailed diffs per task. Recompute by aligning `task_id` between raw A/B JSONLs — pure JSON, no DB/retrieval. Original `7%` is superseded by this **recomputable 19% (full grade review)** and is not claimed as proven.

- **Terminology correction:** pilot `answerability` is **CONCEPTUAL/INTENT only** (user intent corresponds to a conceivable eligible policy), **not corpus-grounded source-truth**. Prior `85%` **MUST NOT** size final benchmark. Final frozen benchmark answerability is **source-truth grounded**: every headline task must have `≥1 grade≥2 (source,source_id)` validated against source-truth table; unsupported has none; ambiguous is safety-only (see §3/D-015).

- **Gate to proceed:** original pilot + re-audit together show labelability high, ambiguity low enough, and disagreement adjudicable — **no re-pilot required.** Re-audit is transparent correction, not history rewrite.

## 3. Strata — exact allocations (coverage required in dev 180 + holdout 250 — EXACT)

The benchmark (and pilot) must cover these strata explicitly; per-stratum diagnostics are required and no stratum may be omitted without justification. The allocations below are **exact** (not minimums) to guarantee headline denominator BY CONSTRUCTION:

| stratum | pilot 100 (done, conceptual) | **dev 180 exact** | **holdout 250 exact** | notes |
|---|---:|---:|---:|---|
| exact / navigation | 12 | **21** | **28** | known title/program/ID lookup |
| natural needs | 14 | **25** | **33** | natural-language need statements |
| exploratory multi-valid | 12 | **21** | **31** | open-ended, multiple policies valid — 2–3 grade-2 equivalence groups each |
| multi-constraint eligibility (≥2 constraints) | 12 | **25** | **36** | ≥2 eligibility constraints must all hold |
| short keywords (2–3 tokens) | 10 | **18** | **24** | 2–3 token keyword queries |
| colloquial / typo / spacing / abbrev | 12 | **20** | **28** | colloquial, typos, spacing, abbreviations |
| **Headline subtotal (first six)** | **72** | **130** | **180** | **source-truth-grounded, unambiguous, labelable — headline denominator** |
| ambiguous | 13 | **23** | **32** | underspecified; safe handling under safety gate ONLY, not headline |
| unsupported / no-answer | 15 | **27** | **38** | no eligible policy — correct behavior safe abstention / no-answer; no grade 2/3 golds |
| **Total** | **100** | **180** | **250** | each column sums to its total exactly |
| **location-bearing separately (cross-cutting)** | 30 | **54 (30%) exact** | **75 (30%) exact** | cross-cutting; distributed across strata, not isolated; evaluated pooled + separate location vs not |

- **Headline denominator guarantee:** headline set is **exactly** the first six strata = **130 dev / 180 holdout**, all source-truth-grounded (each headline task has `≥1 grade≥2 (source,source_id)` validated against source-truth), unambiguous, labelable. **Ambiguous and unsupported are safety-only and excluded from headline.** Frozen sets replace any unlabelable/misclassified item before seal but **counts above must remain exact** (replace, not shrink). The pilot contradiction (all 13 ambiguous were answerable=True) is repaired: ambiguous is safety-only, not headline.
- **Diagnostics (not separate strata but reported slices):** source (Youth/Gov24) / category (6-way) / freshness (stable vs fresh) / common-vs-rare — report per-slice Success@5 to detect bias. Each category/common/rare slice has ≥12 tasks in holdout for gross bias detection.
- **Per-stratum diagnostic precision limitation (explicit):** with per-stratum n≈21–36 (dev/holdout headline strata), per-stratum Wilson 95% half-width at `p=0.85` is **±9–14 pp** (n=33→±11.9 pp, n=28→±13.0 pp, n=21→±15.0 pp). Per-stratum diagnostics therefore detect **only large gaps (>18–20 pp)** and are **not gated as per-stratum release floors**.
- **All strata allocations must be exact after excluding unlabelable** — frozen dev/holdout have **0 unlabelable tasks** (builders reject/replace before seal).

## 4. Golds, grading, and adjudication (FINAL REPAIR protocol)

- **Multi-gold graded 3/2/1/0 per query:** each query may have multiple golds, each graded 3 = perfect answer, 2 = acceptable, 1 = partially relevant, 0 = irrelevant. Equivalence group per grade.
- **Equivalence groups:** when multiple documents are equally acceptable, they form an equivalence group at the same grade; retrieving any member at that grade counts as that grade.
- **Answerability / ambiguity labeling (FINAL REPAIR):**
  - **Pilot:** CONCEPTUAL/INTENT answerability only (no source/source_id) — for sizing intuition, not corpus-grounded.
  - **Final benchmark (dev 180 + holdout 250):** **source-truth-grounded** — each headline task must have `≥1 grade≥2 (source,source_id)` validated against source-truth policy table; unsupported/no-answer has **no grade 2/3 golds** (safety gate) and is excluded from headline; ambiguous is **safety-only** (ambiguous tasks are not headline even if they have a conceivable answer concept).
- **Annotation protocol:**
  - **Pilot 100 (already executed, corrected via re-audit):** re-audit used **two independent reviewers + third adjudicator for all 100** (see §2.2) — not the original single+reviewer with 30% subsample. Re-audit raw A/B + adjudication are auditable and recomputable.
  - **Final benchmark (dev 180 + holdout 250, frozen before tuning):** **two independent annotators + third adjudicator for every query** (not subsample). Annotators independently assign strata, location-bearing, **source-truth-grounded** answerability (headline vs unsupported), ambiguity type, per-gold grade (3/2/1/0) and equivalence grouping. **Inter-annotator agreement reported** (raw agreement + Cohen's κ for strata/conceptual-answerability/ambiguity and for per-gold grade). **All disagreements adjudicated** by third adjudicator; residual 0 after adjudication. Instruction version is the **revised instruction post-pilot** (pilot_report.md §6) plus **D-015 conceptual→source-truth correction**.
  - **Quality of golds:** every query's `(source, source_id)` golds are validated against the **source-truth policy table** (no synthetic golds without table existence); duplicate golds within a query are rejected; empty gold set allowed only for unsupported/no-answer. **Headline tasks must have ≥1 grade≥2 source-truth gold.**

## 5. Metrics (FINAL REPAIR)

- **Headline (labelable + source-truth-grounded answerable tasks only — 130 dev / 180 holdout):** **Success@5 grade≥2** — fraction of headline queries where at least one retrieved result in top-5 has grade 2 or 3 on equivalence groups. **Denominator is exact 130 / 180 by construction (see §3).**
  - Also report **strict grade-3** Success@5 as diagnostic; and Success@5 vs Success@3 vs Success@1 curves.
- **Secondary (per query, headline set):** **Top1 / Top3 / MRR@10 / NDCG@5 / NDCG@10 / per-stratum Success@5 / location vs not Success@5** — reported alongside headline, not gated as release floors (diagnostic).
- **Safety (separate evaluation, not mixed into headline):** no-answer / ambiguity safety (correct handling rate for unsupported 27/38 + ambiguous 23/32; false-positive intrusion rate when system answers where it should abstain or clarify); **ineligible / expired intrusion** (rate at which ineligible or expired policies appear in top-5); **official-link validity** (fraction of top-5 official links that resolve and match the claimed source). Headline denominator **excludes** unsupported/no-answer + ambiguous + unlabelable; safety has its own denominators (38 unsupported holdout, 32 ambiguous holdout).
- **All metrics are computed on graded multi-gold equivalence groups**, not on raw source_id string match alone; grade≥2 is success, grade-3 strict is reported separately.

## 6. Thresholds, confidence, precision, and claims (FINAL REPAIR, replaces D-014 §6)

- **Release floor:** **Success@5 ≥85%** on the representative held-out benchmark **headline set (n=180)** (point estimate, source-truth-grounded).
- **Strong / stretch target:** **Success@5 ≥90%** — aspirational, not promised. If `≥90%` with Wilson lower bound `≥85%`, noted as **strong**.
- **Confidence / precision rule (D-015 fixed, deterministic):**
  - **Interval:** **95% Wilson score interval** (no continuity correction) is primary; **Clopper-Pearson exact** reported as sensitivity. Both on headline Success@5 (holdout headline n=180 primary; dev headline n=130 diagnostic).
  - **Design precision (sizing rationale):** benchmarks sized so that **Wilson half-width at p=0.85 is ≈5.2 pp for n=180 (≤5.5 pp)**. For `p=0.85`: `n=130 → half 6.2 pp`, `n=180 → 5.2 pp`, `n=250 → 4.4 pp` (Wilson). Holdout headline 180 meets `≤5.5 pp` design target; dev 130 is diagnostic. **Not derived from pilot 85% rate.**
  - **Gate (no post-result tuning, deterministic):**
    - **PASS** iff **point estimate ≥85% AND Wilson 95% lower bound ≥80%** on **holdout headline n=180**. Example: `n=180, p=0.85 → Wilson [79.2%, 89.5%] → lower 79.2 <80 → HOLD (not PASS)`; `n=180, p=0.86 → [80.3%, 90.3%] → PASS`. This prevents passing on lucky variance with modest n while keeping the floor at 85% point estimate. **Strong** iff `point≥90% AND Wilson lower≥85%` on same.
    - **HOLD** = `point ≥85% but Wilson lower <80%` (insufficient precision). No vague secondary/safety HOLD — safety is gated separately in §9.
    - **NO-GO** = `point <85%` (numerical floor failure, regardless of CI) or safety gate NO-GO (see §9). No rerun or threshold relaxation after the one-shot holdout is evaluated.
  - **Per-stratum diagnostic precision limitation (documented):** with holdout per-stratum n≈24–36, per-stratum Wilson half-width at `p=0.85` is **±9–15 pp**; diagnostics detect **only large gaps (>18–20 pp)** and are **not gated** as release floors.
- **No public claim before sealed final evidence:** no public claim of meeting the 85% floor (or 90% target) may be made before the sealed one-shot final evaluation on the protected holdout (frozen before tuning, independent review PASS, explicit user approval, audit chain verified — see §9). The dev 180 result is **not** a claimable floor.

## 7. Candidate families — exact boundaries (FINAL REPAIR)

- **Candidate A — fielded primary family (only family implemented in next stage):** **fielded sparse+dense union/hybrid (Postgres FTS / BM25-equivalent as feasible) + exact title/org/entity + field weighting + duplicate/diversification**.
  - Union/hybrid: sparse lexical (Postgres FTS or BM25-equivalent) and dense vector retrieval are combined via union or hybrid scoring, not single-signal only.
  - Exact signals: exact title / organization / entity matching is an explicit signal, not subsumed by dense alone.
  - Field weighting: title, eligibility, and other fields are weighted explicitly.
  - Duplicate / diversification: duplicate detection and diversification are required to avoid redundant top-5.
  - This family is the **only** family to be implemented and tuned on dev headline 130. **No v2 K/threshold/source-bias sweep continuation.** No embedding replacement at this stage.
  - **Dev-tuning boundary: MAX 24 configurations**, one-way pre-dev freeze of exact config IDs/parameter tuples + deterministic selection rule (see §8). **No new signal/model/embedding** beyond D-013 family.
- **Candidate B — optional lightweight ranker (conditional, exact gate below):** **optional lightweight reranking only; never old cross-encoder re-enable.**
  - **Admission gate (exact, replaces 95 to 97 percent range / vague ranking-limited wording):** Candidate B is permitted **only if** on **dev headline 130** `union oracle Recall@100 ≥97%` (whether any grade≥2 gold appears in the union of sparse+dense+exact top-100, before ranking) **AND** `(union oracle Recall@100 - Candidate-A Success@5) ≥5.0 percentage points` on the same dev headline set. Otherwise **B is forbidden**. Evidence must be a dev diagnostic report on headline 130, not intuition. D-015 supersedes D-014 for this gate.
  - **Embedding replacement / LLM rewrite / LLM-as-judge is last resort / out of initial scope** — not in the fielded families unless first-stage coverage **and** lightweight reranking both fail to close the gap after diagnosis (requires a new decision).
- **Out of scope for this FINAL REPAIR:** global abstention threshold, public region search (D-004 otherwise in force), new candidate families beyond A/(conditional)B.

## 8. Dev diagnostics and tuning selection (FINAL REPAIR)

- **On dev headline 130 (and safety sets separately), measure dense / sparse / exact / union oracle Recall@30 / Recall@50 / Recall@100** (oracle = whether any grade≥2 gold appears in the top-K of that signal or the union, regardless of current ranker score). Report per-signal and per-stratum **and** per location-bearing vs not and per rare-policy vs common.
- **If union Recall@100 <97%, stop ranker work and fix coverage / data representation first** — do not proceed to Candidate B. The first-stage coverage or index/data representation must be fixed until the union oracle reaches **≥97%** before any reranker is considered.
- **Candidate A dev-tuning boundary (exact, FINAL REPAIR):**
  - **MAX 24 dev-scored configurations total** — not a range, not adaptive.
  - Before the **FIRST dev retrieval**, a separate **candidate-plan artifact must freeze ALL exact config IDs/parameter tuples and the deterministic selection rule**; after first dev result **no new configs/adaptive generation**.
  - Allowed axes remain **only D-013 family** (sparse/dense fusion/weights, exact title-org-entity signal weights, field weights, duplicate/diversification threshold) and **NO new signal/model/embedding**.
  - **Deterministic selection rule (frozen in candidate-plan before dev access):** require dev **safety gates (§9) + Success@5 ≥85%** on dev headline 130; choose highest `Success@5`, then `NDCG@5`, then `MRR@10`, then **lower paired p95** (per §9 latency method over dev 180), then **lexicographic `config_id`**. If none pass, **no holdout** (NO-GO for this cycle). Candidate B admission evaluated only after Candidate A finalist diagnostics.
  - The exact 24-or-fewer tuples may be instantiated in the future candidate-plan stage **BEFORE dev access**; this prereg makes that one-way pre-dev freeze **mandatory** and prohibits result-driven additions. The candidate-plan artifact is separate and must be auditable.
- **Reranker conditional gate is exactly §7 B** — not an independent dev threshold.

## 9. Guardrails — freeze / review / one-way evaluation / audit / rerun prevention / deterministic safety & latency gates (FINAL REPAIR)

### Protected-set freeze & isolation plan

- **Two frozen benchmarks, both before any candidate tuning:**
  - **Dev 180** and **Holdout 250** are each frozen in **separate isolated builder sessions** that have no access to candidate code or to each other's plaintext after freeze. **Headline denominator BY CONSTRUCTION (130/180) via exact strata allocations (§3); builders replace unlabelable before seal to keep counts exact.**
  - **Fingerprint-only overlap checks (fail-closed) required before tuning:** each freeze validates **query fingerprint** `SHA256(NFC+strip+collapse_whitespace+casefold)` and **gold fingerprint** `SHA256(source+NUL+source_id)` against (i) all v2/Cycle3 history — P0 canonical 81, cycle1 dev 36, cycle1 holdout 40, cycle2 dev 36, cycle2 disqualified holdout 40, hard-negative 36, cycle3 dev 36 + holdout 40, catalog union 248 — and (ii) between dev ↔ holdout and against each other. Overlap must be **exactly 0** for query and for gold, except the documented `P0↔hard_negative 21` expected overlap which is excluded from the holdout gate. Fail-closed: any non-zero unexpected overlap → freeze rejected.
  - **Source-truth validation:** every `(source,source_id)` gold must exist in the policy table at freeze time; **every headline task must have ≥1 grade≥2 source-truth gold**; unsupported/no-answer tasks have **no grade≥2 golds**; expired/ineligible intrusion cases are validated as ineligible per table.
  - **Sealing:** each benchmark has `evalset.jsonl` (LF, canonical JSON), `manifest.json` (counts, SHA256, provenance), `annotation_audit.json` (strata/balance/ambiguity/freshness), `SEALED.md` — plus `fingerprints.json`/`fingerprints.sha256`. The holdout's plaintext (`evalset.jsonl`) lives **only** on its isolated protected branch/tag (e.g., `codex/retrieval-v3-holdout-freeze` / `retrieval-v3-holdout-v1`) — **never on the candidate/dev branch** and never merged/cherry-picked.
  - **Builders are not reused for tuning.** No retrieval/DB/model/embedding execution in builder sessions beyond table-existence checks.

### Deterministic safety gates (FINAL REPAIR, no “marginal” discretion)

Use these **exact release gates** unless a mathematical impossibility is found (then STOP, do not silently substitute):

- `unsupported/no-answer correct safe handling ≥95%` on **holdout unsupported 38** (safe abstain/no-answer; no grade≥2 policy asserted);
- `ambiguous correct clarification-or-safe-abstention ≥90%` on **holdout ambiguous 32**;
- `ineligible/expired top-5 intrusion = 0 cases` in the designated audited slice (any intrusion => **NO-GO**);
- `official-link semantic/source match = 100%; HTTP resolution ≥99%` under a **preregistered fixed retry/check protocol**; missing measurement => **HOLD**, numeric failure => **NO-GO**;
- `cost: candidate index size ≤2x baseline, per-query DB scanned rows ≤3x baseline, and 0 extra external model calls unless Candidate B is admitted`; missing measurement => **HOLD**, numeric failure => **NO-GO**.
- No discretionary “marginal safety HOLD” — above gates are deterministic; **missing measurement => HOLD, numeric failure => NO-GO**. Dev safety is checked on dev safety sets (27/23) but **holdout safety is the final gate (38/32)**.

### Deterministic latency gate (FINAL REPAIR, no “if feasible”)

- **Method (exact, no “if feasible”):** **paired baseline-vs-candidate on ALL benchmark tasks** for the relevant gate, **same env/DB/corpus, warm, interleaved, cold/model-load excluded**. For **final holdout gate use all 250 tasks**, **exactly one timed sample per task per variant after a deterministic warm-up pass over the first 30 task_ids in canonical sorted order**; **alternate variant order by task index**; report **nearest-rank p50/p95/p99**. Dev finalist may use **same method over all 180 tasks** (warm-up 30 of those 180). Gate remains **`candidate p95 ≤ paired baseline p95 +80ms AND candidate p95 ≤700ms`**. Both must hold.
- **Baseline:** D-003 production `RERANK=0, CANDIDATES=30, COSINE_MIN=0.78, LEXICAL_BIAS=0.01, strip_region, youth bias suppressed for Gov24 orgs, intfloat/multilingual-e5-base`.

### Cost gate (exact)

- `index size ≤2× baseline corpus index`, `per-query DB scanned rows ≤3× baseline CANDIDATES scan`, `no extra external model calls unless Candidate B admitted`. Missing measurement => HOLD, numeric failure => NO-GO.

### Audit / provenance (must PASS before protected execution)

- **Append-only, hash-chained audit log** for every protected-set access and every benchmark execution: `eval/retrieval-v3/audit/events.jsonl` (JSONL, fields `schema_version, event_id, utc_timestamp, git_head, git_dirty, process_id, session_id, action, candidate_id, set_role, set_sha, command, runner_id, outcome, previous_event_hash, event_hash`), chain verified via `previous_event_hash`/`event_hash` (SHA256 of canonical JSON). Actions include `run_start/run_end`, `protected_access_start/protected_access_end` (with exact `set_sha`, `session_id`, `expected_event_hash`, outcome).
- **Independent review required:** before any protected holdout evaluation, an independent reviewer verifies (i) audit chain integrity, (ii) fingerprint isolation (0 overlap), (iii) manifest SHA256 pinned, (iv) candidate freeze identity. Review verdict must be **PASS**.
- **Explicit user approval** required after review and before the one-shot holdout run.

### One-shot final holdout rules & rerun prevention

- **Final evaluation is one-shot:** the protected holdout (250, headline 180) is evaluated **exactly once** in a single canonical batch (all tuned candidates + baseline together, interleaved per latency methodology where applicable). The batch identity (e.g., `v3-canonical-holdout-v1`) and run event are logged in the audit chain.
- **No post-result retuning:** after the holdout batch is evaluated, **no candidate may be tuned, retrained, threshold-adjusted, or re-ranked to manufacture a PASS on the same holdout**. No additional holdout runs are permitted, even if the result is HOLD/NO-GO. A new evaluation requires a **new holdout frozen before tuning** and a new prereg decision (not an addendum to this prereg).
- **Canonical execution count guard:** the holdout batch `run_start`/`run_end` pair is **exactly one** in the audit chain forever; any second `run_start` for the same holdout set is rejected fail-closed.
- **No history rewrite:** no amend/reset/rebase/squash/force-push of benchmark commits; tags are annotated and peeled identities are verified and immutable; audit log is append-only (no delete/reset/truncate).
- **D-007 is historical:** D-007 governs v2/Cycle3 history only; v3 is governed by D-013 + D-015 + this FINAL REPAIR prereg. **v3 latency/safety gates are now defined in D-015/§9** (D-007 latency does not apply to v3).
- **This FINAL REPAIR prereg is execution authorization for the next stage only as far as dataset freeze + runner implementation + independent review + one-shot protected evaluation under the gates above.** It does not authorize production rollout.

## 10. What is STILL NOT authorized or changed in this stage (explicit)

- **Candidate implementation is still NOT performed in this stage.** This commit freezes the repair design only; no `eval/retrieval-v3/` candidate code, no runner, no DB/model/embedding/benchmark/latency execution, no `DATABASE_URL`/`SENTENCE_TRANSFORMER` usage.
- **No dataset freeze is performed in this stage.** Dev 180 / holdout 250 are sized and planned but not yet built/frozen — that is the next isolated stage.
- **No protected dev/holdout/evalset/canonical result plaintext per-case access** beyond the aggregate/provenance facts durable in docs/memory and the pilot 100 + re-audit 100 (which are not protected). No `git show`/`cat-file`/`checkout`/`restore`/`sparse`/`parent worktree` access to any v2/Cycle3 or v3 protected set.
- **No production `ml-service` behavior change** (`git diff HEAD -- ml-service/` still 0 from D-012 base through this freeze).
- **No new branch/tag creation** beyond this freeze commit and its push; no history rewrite; no tag/branch deletion/main merge.
- **No `docs/RETRIEVAL_V2.md` rewrite** (V2 remains cycle-1 HOLD / cycle-2 disqualified / cycle3 closure without holdout) except an exact stale cross-reference correction if required by this REPAIR.

## 11. Next gates (explicit, no auto-advance)

1. **Isolated dataset freeze(s)** — separate isolated builder session(s) with fingerprint-only isolation checks — freeze dev 180 (`retrieval-v3-dev-v1`, 130 headline) and holdout 250 (`retrieval-v3-holdout-v1`, 180 headline), each sealed before tuning, independent review of manifests/fingerprints/audit.
2. **Candidate-plan freeze (MAX 24, before FIRST dev retrieval)** — separate artifact freezing ALL exact config IDs/parameter tuples + deterministic selection rule (Success@5 → NDCG@5 → MRR@10 → lower p95 → lexicographic config_id); no adaptive generation after.
3. **Runner implementation + independent review** — implement Candidate A hybrid family (§7) + dev diagnostics + latency harness + audit integration in a sparse-isolated worktree without accessing holdout plaintext; pure/static/mock tests + self-review; no holdout evaluation.
4. **One-shot final holdout evaluation** — only after freeze + implementation complete + independent review PASS + explicit user approval — single canonical batch on protected holdout 250 (headline 180), interleaved warm paired latency measurement (all 250 tasks, one sample per variant, warm-up 30), audit-logged exactly once; report headline Success@5 Wilson CI + Clopper sensitivity + secondary/safety (unsupported 38, ambiguous 32) + per-slice + latency/cost; durable result commit.
5. **Hold decision from sealed evidence** — PASS (point≥85 AND Wilson lower≥80 on n=180) / HOLD (point≥85 but lower<80) / NO-GO (point<85 or safety NO-GO) per §6/§9 gates; no post-result retuning; rollout is a separate decision if PASS.

**This FINAL REPAIR prereg STOPs after the durable docs/memory/pilot re-audit commit.** No dataset freeze, runner implementation, retrieval execution, or holdout access follows from this commit. Results remain unseen; no post-result tuning loopholes.

*— END FINAL REPAIR prereg freeze — D-015 supersedes D-014, Web HOLD A-D repaired, headline 130/180 BY CONSTRUCTION —*
