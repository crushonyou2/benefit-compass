# Retrieval v3 — User Search Quality — Bootstrap Prereg

> **BOOTSTRAP prereg — 2026-09-01 — docs/memory only. NOT final execution authorization while Q-006 open.**
> This prereg records the evaluation design and candidate family for Retrieval v3 (user search quality) as D-013 standing decision. It is a bootstrap durable record, not a freeze/run authorization. Final execution remains blocked until Q-006 (exact dev/holdout sizes, confidence/precision rule, user-centered paired latency budget, final pilot protocol) is fixed after the retrieval-blind pilot and before candidate tuning / one-way protected evaluation. No retrieval/DB/model/embedding/benchmark execution, no protected holdout/dev plaintext access, no production change in this bootstrap.

## 0. Reconciled base

| item | value |
|---|---|
| Branch | `codex/retrieval-v3-user-search-quality` |
| Base | `5327661445c37191a3fd61db195f3af4d2cf893a` (tag `retrieval-v2-cycle3-closure-v1` object `0c94d801da23050d0c9537717b2a3e83ee1b0bf6`) |
| Prior HEAD | `257183f106c39ffee4aae1e52b8587c1d9db97c0` (HOLD: wrong file scope `docs/RETRIEVAL_V3.md` + `memory/00-INDEX.md` and omitted D-013/Q-006/prereg) — not rewritten, this repair is append-only |
| Standing decisions | D-003 / D-007 / D-008 / D-010 / D-011 / D-012 remain history/contracts as applicable; D-013 supersedes D-004 only for conditional reranking reconsideration |
| Q-006 | open — exact final dev/holdout sizes, confidence/precision rule, user-centered paired latency budget and final pilot protocol unresolved; fix after retrieval-blind pilot and before candidate tuning/one-way protected evaluation |

## 1. Goal and headline gates (D-013)

- **Goal:** user-satisfying search — system returns what the user actually needs for representative user intent queries over the benefit-compass policy corpus.
- **Headline metric (answerable tasks only):** **Success@5 grade>=2** — at least one result in top-5 is grade 2 (acceptable) or grade 3 (perfect) on a 3/2/1/0 multi-gold graded scale.
  - **Release floor:** **Success@5 >=85%** on representative answerable user-intent tasks.
  - **Strong / stretch target:** **Success@5 >=90%** — not promised, aspirational. Pass/fail for release is the 85% floor.
- **Supporting gates (required before release, diagnostic + safety, headline is not sufficient alone):** Top1 / Top3 / MRR / NDCG; no-answer / ambiguity safety; ineligible / expired intrusion; official-link validity; latency / cost.
- **CI rule:** pending Q-006 (confidence/precision rule unresolved). No public claim before sealed final evidence on the protected holdout.
- **Evaluation design / pilot before implementation:** candidate tuning and protected evaluation are blocked until the evaluation design in this prereg is validated by a retrieval-blind pilot.
- **Rollout:** no rollout is authorized by D-013 or this bootstrap prereg.

## 2. Retrieval-blind pilot — 100 user-like tasks (labelability only, no system results)

Before any candidate implementation or protected data freeze, run a **retrieval-blind pilot with 100 user-like tasks** for **labelability / answerability / ambiguity / strata / annotation disagreement only with no system-result inspection**.

- **Purpose:** validate that the evaluation design is labelable and that the strata/multi-gold scheme is answerable without ever inspecting system retrieval results.
- **Method:** draft 100 user-like tasks spanning the strata in §3 from user-intent sources (support logs, paraphrased needs) **without running any retrieval system or inspecting system outputs**. Annotators label answerability, ambiguity, gold equivalence, and strata membership only. No system-result inspection at any time during the pilot.
- **Outputs:** pilot labelability rate, answerability / ambiguous rate, strata coverage, ambiguity distribution, annotation disagreement rate, and revisions to query authoring / grading instructions. If pilot reveals low labelability or high disagreement, revise the benchmark design before freezing the final dev/holdout benchmark.

## 3. Strata (coverage required in both pilot 100 and final benchmark)

The benchmark (and pilot) must cover these strata explicitly; per-stratum diagnostics are required and no stratum may be omitted without justification:

- **exact / navigation** (known title, program name, or ID lookup)
- **natural needs** (natural-language need statements, e.g., "I need help with rent because ...")
- **exploratory multi-valid** (open-ended exploration where multiple policies are valid)
- **multi-constraint eligibility** (queries with ≥2 eligibility constraints that must all hold)
- **short keywords** (2–3 token keyword queries)
- **colloquial / typo / spacing / abbrev** (colloquial phrasing, typos, spacing errors, abbreviations)
- **ambiguous** (underspecified or ambiguous intent where system must handle ambiguity safely)
- **unsupported / no-answer** (requests for which no eligible policy exists — correct behavior is safe abstention / no-answer)
- **location-bearing separately** (queries that contain location; evaluated separately to avoid location confounding)
- **Diagnostics (not separate strata but reported slices):** source / category / freshness / common-vs-rare (rare-policy vs frequent-policy need) — report per-slice success to detect source/category/freshness/common-vs-rare bias.

Each stratum must have enough tasks to report per-stratum Success@5; the exact minimum per stratum is deferred to Q-006 fix after the pilot.

## 4. Golds, grading, and adjudication

- **Multi-gold graded 3/2/1/0 per query:** each query may have multiple golds, each graded 3 = perfect answer, 2 = acceptable, 1 = partially relevant, 0 = irrelevant. A query's gold set is an equivalence group per grade.
- **Equivalence groups:** when multiple documents are equally acceptable (e.g., same program via different sources), they form an equivalence group at the same grade; retrieving any member at that grade counts as that grade.
- **Annotation protocol:** **two annotators + adjudication for the final benchmark** (pilot may use two annotators with adjudication or a single annotator plus reviewer; final benchmark requires two independent annotators and an adjudicator for disagreements). Annotators assign grade per gold and equivalence grouping; disagreements on grade or equivalence are adjudicated. Inter-annotator agreement is reported for the pilot and final benchmark.
- **Answerability / ambiguity labeling:** each query is labeled answerable vs unsupported/no-answer and unambiguous vs ambiguous (with ambiguity type) by annotators before any gold assignment; unsupported/no-answer queries have no grade 2/3 golds and are evaluated under the safety gate, not the headline Success@5.

## 5. Metrics

- **Headline (answerable tasks only):** **Success@5 grade>=2** — fraction of answerable queries where at least one retrieved result in top-5 has grade 2 or 3.
  - Also report **strict grade 3** Success@5 (at least one grade 3 in top-5) as a diagnostic.
- **Secondary (per query, headline set):** **Top1 / Top3 / MRR@10 / NDCG@5 / NDCG@10 / per-stratum Success@5** — reported alongside headline, not gated as release floors unless Q-006 later adds a secondary gate.
- **Safety (separate evaluation, not mixed into headline):** no-answer / ambiguity safety (unsupported and ambiguous queries — correct handling rate, false-positive intrusion); **ineligible / expired intrusion** (rate at which ineligible or expired policies appear in top-5); **official-link validity** (fraction of top-5 official links that resolve and match the claimed source).
- **All metrics are computed on graded multi-gold equivalence groups**, not on raw source_id string match alone.

## 6. Thresholds, confidence, and claims

- **Release floor:** **Success@5 >=85%** on the representative held-out benchmark (answerable tasks).
- **Strong / stretch target:** **Success@5 >=90%** — aspirational, not promised. A system achieving 85–90% meets the release floor; >=90% is a strong result if achieved.
- **CI rule:** **pending Q-006** — the exact confidence interval / precision rule (e.g., Wilson interval width, required N for 85% ±X pp at 95% confidence) is unresolved in this bootstrap and will be fixed after the retrieval-blind pilot (when answerable rate and strata variances are observed) and before candidate tuning / one-way protected evaluation.
- **No public claim before sealed final evidence:** no public claim of meeting the 85% floor (or 90% target) may be made before the sealed final evaluation on the protected holdout (frozen before tuning, independent review PASS, explicit user approval, one-shot evaluation — see §9).

## 7. Candidate families

- **Candidate A — fielded primary family:** **fielded sparse+dense union/hybrid (Postgres FTS / BM25-equivalent as feasible) + exact title/org/entity + field weighting + duplicate/diversification**.
  - Union/hybrid: sparse lexical (Postgres FTS or BM25-equivalent as feasible) and dense vector retrieval are combined via union or hybrid scoring, not single-signal only.
  - Exact signals: exact title / organization / entity matching is an explicit signal, not subsumed by dense alone.
  - Field weighting: title, eligibility, and other fields are weighted explicitly.
  - Duplicate / diversification: duplicate detection and diversification are required to avoid redundant top-5.
  - This family is the primary family to be implemented and tuned on dev. No v2 K/threshold/source-bias sweep continuation.

- **Candidate B — optional lightweight ranker (conditional):** **optional lightweight reranking only after materially new v3 evidence shows high first-stage recall yet ranking still limits, not an old cross-encoder re-enable.**
  - Candidate B is permitted **only if first-stage oracle Recall@100 >=95–97% and ranking still limits** — i.e., the dev diagnostic shows that the union/hybrid first stage already covers the answer in its top-100 for >=95–97% of queries, but the answer is not ranked into top-5 by the current ranker.
  - D-013 supersedes D-004 **only for this conditional reconsideration**; the old cross-encoder reranking remains not adopted otherwise.
  - **Embedding replacement / LLM rewrite / judge is last resort / out of initial scope** — not in the fielded families unless first-stage coverage and lightweight reranking both fail to close the gap after diagnosis on dev.

## 8. Dev diagnostics and coverage gate

- **On dev, measure dense / sparse / exact / union oracle Recall@30 / Recall@50 / Recall@100** (oracle = whether any grade>=2 gold appears in the top-K of that signal or the union, regardless of current ranker score). Report per-signal and per-stratum (especially location-bearing vs not, and rare-policy vs common).
- **If union Recall@100 <95%, stop ranker work and fix coverage / data representation first** — do not proceed to Candidate B lightweight reranking. The first-stage coverage or index/data representation must be fixed until the union oracle reaches >=95% before any reranker is considered.
- **No v2 K / threshold / source-bias sweep continuation:** v2 vector-pool K=128/256/512, threshold, and source-bias sweeps are historical cycle3 results (baseline 36/36, all candidates net 0) and are not continued as v3 tuning.

## 9. Guardrails — freeze, review, one-way evaluation

- **Final protected holdout only after freeze + implementation complete + independent review PASS + explicit user approval.** The final dev and final holdout are each frozen before any candidate tuning, with fingerprint-only overlap checks against all prior v2/Cycle3 sets and each other.
- **Final evaluation is one-shot:** the protected holdout is evaluated exactly once. No post-result retuning is permitted after the protected holdout is evaluated.
- **No post-result retuning:** after the one-shot protected evaluation, the result is durable evidence; no candidate may be tuned, retrained, or threshold-adjusted to manufacture a PASS on the same holdout.
- **Audit / provenance before protected execution:** audit/provenance infrastructure (append-only, hash-chained, independent review) must be in place and PASS before any protected evaluation execution.
- **D-007 is historical v2 contract:** D-007 governs v2/Cycle3 history only; v3 is governed by D-013 and this prereg. **v3 latency budget is pending Q-006** (user-centered paired latency budget unresolved; to be fixed after the pilot).
- **This bootstrap prereg is not final execution authorization:** while Q-006 is open, no freeze, implementation, or protected evaluation is authorized beyond the retrieval-blind pilot. Candidate tuning and one-way protected evaluation begin only after Q-006 is fixed and the final dev/holdout sizes, CI rule, and pilot protocol are durably recorded.

## 10. What is NOT authorized or changed in this bootstrap

- No `eval/` creation/modification (no dev/holdout builder, no candidate, no runner, no audit `events.jsonl` append, no canonical result access via `git show`/`cat-file`/`checkout`/`restore`/`sparse`/`parent worktree`).
- No retrieval/DB/model/embedding/benchmark/latency execution, no `CYCLE3_CANONICAL_EXECUTION` / `DATABASE_URL` / `SENTENCE_TRANSFORMER` usage.
- No protected dev/holdout/evalset/canonical result plaintext per-case access (use only existing aggregate/provenance facts durable in docs/memory).
- No production `ml-service` behavior change (`git diff HEAD -- ml-service/` 0 preserved from D-012 base).
- No new branch/tag creation beyond this repair commit and its push; no history rewrite; no tag/branch deletion/main merge.
- No `docs/RETRIEVAL_V2.md` rewrite (V2 remains cycle-1 HOLD / cycle-2 disqualified / cycle3 closure without holdout).

## 11. Next gates (explicit, no auto-advance)

1. **Retrieval-blind pilot 100** — execute the pilot described in §2, report labelability/answerability/ambiguity/strata/disagreement, revise design if needed.
2. **Fix Q-006** — after the pilot and before candidate tuning / one-way protected evaluation, fix exact final dev/holdout sizes, confidence/precision rule, user-centered paired latency budget, and final pilot protocol; record as a new decision that closes Q-006.
3. **Pre-registration update + freeze plan** — update this bootstrap prereg to a final prereg with fixed sizes/CI/latency budget, and record the isolated freeze plan (fingerprint-only overlap checks, builder isolation).
4. **Isolated dataset freeze(s) + runner implementation + independent review** — only after execution authorization; then one-shot protected evaluation.

This bootstrap **STOPs** after the durable docs/memory repair commit. No dataset freeze, runner implementation, retrieval execution, or holdout access follows from this record.
