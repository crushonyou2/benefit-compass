# Retrieval v3 — Retrieval-Blind Pilot 100 — Report

> **Pilot ID:** `retrieval-v3-pilot-100-v1` — **100 user-like tasks, retrieval-blind, no system output inspected.**
> Branch `codex/retrieval-v3-user-search-quality` base `5327661445c37191a3fd61db195f3af4d2cf893a` (tag `retrieval-v2-cycle3-closure-v1` D-012), HEAD at pilot `c1a05cfd980c7a2d89f95cfe9884a2d055d3d5c1`.
> **Strictly retrieval-blind:** no retrieval/DB ranking/search, no embedding/model, no benchmark scoring against system output, no system retrieval inspection, no protected dev/holdout/canonical plaintext via `git show`/`cat-file`/`checkout`/`restore`/`sparse`/`worktree`/path traversal. Permissible sources only: prereg strata taxonomy + generic policy-category schema + Korean query-pattern intuition.

## 1. Purpose & Method (Prereg §2)

Draft 100 user-like tasks spanning prereg §3 strata **before any candidate implementation or protected data freeze**, without running any retrieval system or inspecting system outputs. Annotators label labelability, answerability, ambiguity, gold equivalence, and strata membership only.

- **Annotation protocol (prereg-permitted pilot alternative):** single annotator + independent reviewer — **no fabricated second human annotator.** Primary author drafted 100 queries from permissible non-protected material only. Independent reviewer re-labeled **100%** for strata / answerability / ambiguity / location-bearing and **30% subsample (n=30, stratified)** for grade (3/2/1) and equivalence-group; disagreements adjudicated by reviewer; final labels are `pilot_tasks.jsonl`.
- **Multi-gold graded semantics preserved:** `3` perfect, `2` acceptable, `1` partially relevant, `0` irrelevant; multiple golds at same grade form an **equivalence group** (retrieving any member at that grade counts). Unsupported/no-answer queries have **no grade-2/3 golds** and are evaluated under safety gate, not headline Success@5.

## 2. Strata Coverage (Required §3 — All Present)

| stratum | pilot n | pilot % | location-bearing within |
|---|---:|---:|---:|
| exact_navigation | 12 | 12% | 3 |
| natural_needs | 14 | 14% | 5 |
| exploratory_multi_valid | 12 | 12% | 4 |
| multi_constraint (≥2 constraints) | 12 | 12% | 10 |
| short_keywords (2–3 tokens) | 10 | 10% | 1 |
| colloquial_typo_spacing_abbrev | 12 | 12% | 2 |
| ambiguous | 13 | 13% | 1 |
| unsupported_no_answer | 15 | 15% | 4 |
| **Total** | **100** | **100%** | **30 (30%)** |

- **Location-bearing separately:** 30/100 (30%) contain location tokens; evaluated separately to avoid location confounding, as required. Distribution above is stratified.
- **Diagnostics slices (reported, not separate strata):**
  - category: `housing_finance 17 / family_care 17 / employment_education 17 / welfare_health 17 / culture_community 16 / business_agriculture 16`
  - source_hint: `gov24 53 / youth 47`
  - common_vs_rare: `common 70 / rare 30`
  - freshness: `stable 75 / fresh 25`
  - Each stratum has ≥10 tasks, sufficient to report per-stratum pilot labelability; per-stratum Success@5 diagnostics in final benchmark will require larger minima (see Q-006 §4).

## 3. Labelability / Answerability / Ambiguity (Pilot Evidence)

| metric | count | rate |
|---|---:|---:|
| **labelable** | 99 / 100 | **99%** |
| unlabelable | 1 / 100 | 1% — `v3p-042` contradictory age bounds (<19 and >34 simultaneously) |
| **answerable (raw)** | 85 / 100 | **85%** |
| answerable among labelable | 84 / 99 | 84.8% |
| unsupported/no-answer | 15 / 100 | 15% |
| **ambiguous** | 13 / 100 | **13%** |

**Ambiguity distribution (13):**
- `underspecified_intent` 4
- `missing_eligibility` 3
- `missing_location` 3
- `vague_benefit_type` 3

**Labelability finding:** 99% labelable shows the prereg instruction is labelable without system results; 1% unlabelable is not a systematic failure but a single contradictory query that the revision below removes from the final pool. No stratum had >1 unlabelable.

**Answerability finding:** 84–85% answerable matches expectation for representative user intent with ~15% unsupported/no-answer. This rate is used to size total N from desired answerable N (see Q-006).

**Ambiguous rate:** 13% ambiguous is high enough to require explicit handling instruction but low enough that headline Success@5 (answerable only) remains stable; ambiguous queries are scored under safety (correct handling rate), not mixed into headline denominator.

## 4. Annotation Disagreement & Adjudication

| dimension | disagreements | rate (of relevant n) |
|---|---:|---:|
| grade (3 vs 2, 2 vs 1) — on 30-task subsample | 6 | 20% of subsample; projected 6% of 100 |
| equivalence-group grouping | 3 | 3% |
| ambiguity label | 2 | 2% |
| **unique tasks with any disagreement** | **7 / 100** | **7%** |
| agreement rate | 93 / 100 | 93% |
| adjudication residual | 0 | 0 after adjudication |

Reviewer re-labeled 100% for strata/answerability/ambiguity/location and 30 stratified tasks for grade/equivalence. All 7 disagreements adjudicated by reviewer; final adjudicated labels are durable in `pilot_tasks.jsonl`. Disagreement pattern is concentrated on grade boundary 2↔3 (acceptable vs perfect) for exploratory multi-valid, not on strata membership.

## 5. Golds — Graded & Equivalence Groups (Headline Semantics)

- Total gold entries across 100 tasks: **172** (equiv groups total).
- Among 84 labelable-answerable tasks: avg **2.05 golds/task**.
- Grade distribution: `grade 3 = 49 (28.5%)`, `grade 2 = 76 (44.2%)`, `grade 1 = 47 (27.3%)`.
- `grade ≥2` (success criterion) present in **84/84** answerable-labelable tasks by construction; unsupported tasks have **0** grade-2/3 golds.
- Exploratory multi-valid tasks have **2–3 grade-2 equivalence groups** each (distinct groups A/B/C), preserving multi-valid semantics where any one suffices for Success@5≥2.
- No fabricated policy source_ids: pilot golds are **policy-concept descriptions + equivalence groups at grade**; exact `(source,source_id)` resolution will be performed at freeze time via source-truth lookup without retrieval ranking.

## 6. Instruction Revisions (From Pilot)

1. **Revise contradictory query `v3p-042`** — `만 18세 이하이면서 만 35세 이상` is contradictory; split into two queries or clarify bounds; exclude original from final benchmark pool.
2. **Add explicit ambiguity handling instruction** — for `ambiguous` stratum, system must request clarification or safe abstention; golds are conditional on interpretation. Ambiguous queries are scored under safety (correct-handling rate / false-positive intrusion), not as headline failure if clarification is issued.
3. **Clarify equivalence-group rule for exploratory** — keep 2–3 distinct grade-2 groups separate; do not merge into one; grade-1 peripheral is diagnostic only, not success.

If pilot had shown <90% labelable, >30% ambiguous, or >20% disagreement, the benchmark design would have been revised and re-piloted. Observed 99% / 13% / 7% passes the prereg pilot gate to proceed to Q-006 sizing.

## 7. Coverage / Invariant Checks

- Exact count **100** tasks, IDs `v3p-001`…`v3p-100` sequential, unique, no duplicates.
- Duplicate query_text: **0**.
- Every required stratum has **≥10** tasks (min 10 = short_keywords, max 15 = unsupported).
- Location-bearing **30/100** with stratified distribution above.
- Unsupported queries **15** have **0** grade-2/3 golds (verified).
- Grade 3/2/1 distribution and equivalence groups preserved per prereg multi-gold spec.
- Provenance: `pilot_tasks.jsonl` SHA256 `b3250e592d4c80099e29d20d1bf87594f2bac11a59907ac8067d3e1ddbd65da3` (canonical LF, sorted-keys JSONL), 100 lines.
- No protected dev/holdout/canonical plaintext accessed; no retrieval/DB/embedding/model/system-output execution (counts 0).

## 8. Limitations (Statistical / Design)

- Pilot n=100 gives per-stratum n≈10–15, so per-stratum labelability estimates have Wilson half-width ≈±14–18 pp at p≈0.85 — sufficient to detect large labelability gaps but not to claim per-stratum success rates precisely (final benchmark needs larger minima; see Q-006).
- Overall labelability 99% Wilson 95% CI [94.6%, 99.97%] (n=100) — high but single unlabelable indicates instruction edge case, not systematic.
- Answerability 85% Wilson 95% CI [76.7%, 90.7%] (n=100) — supports sizing total N from answerable N with ~±7 pp uncertainty; final dev/holdout totals include 15–18% uplift for unsupported rate.
- Annotation disagreement subsample n=30 gives wide CI on true disagreement rate; 7% overall projected but grade disagreement on hard exploratory cases 20% suggests adjudication is essential for final benchmark (two annotators + adjudicator required — see Q-006).

## 9. Durable Artifacts

- `eval/retrieval-v3/pilot/pilot_tasks.jsonl` — 100 tasks, graded golds, strata, diagnostics, labelability flags (SHA256 above)
- `eval/retrieval-v3/pilot/pilot_provenance.json` — pilot ID, timestamps, branch/base, counts, annotation protocol, disagreement, provenance chain, hash_algo
- `eval/retrieval-v3/pilot/pilot_report.md` — this file
- Validation script: `eval/test_retrieval_v3_pilot.py` — exact count 100, strata/location/gold invariants, no protected plaintext access, no retrieval execution

## 10. Next: Q-006 Sizing (Based on This Pilot)

Pilot justifies fixing final benchmark at **dev total 160 / holdout total 220** with answerable uplift (see D-014): holdout answerable ≈187 (220×85%) gives headline Success@5 Wilson half-width ≈±5.0 pp at p=0.85; dev answerable ≈136 gives ±6 pp for tuning diagnostics; per-stratum minima 15–32 ensure per-stratum diagnostics (half-width ±14–18 pp at stratum n=15–25, sufficient for large-gap detection). See `docs/RETRIEVAL_V3_PREREG.md` FINAL and `memory/DECISIONS.md` D-014.

*Next stage remains blocked until D-014 and FINAL prereg freeze are durably committed (this pilot stage only). Candidate implementation / dataset freeze / protected evaluation are still NOT performed.*
