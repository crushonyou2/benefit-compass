# Retrieval v3 — User Search Quality — FINAL Prereg (Freeze)

> **FINAL prereg — 2026-09-01 — Q-006 closed → D-014, pilot 100 evidence, freeze. Candidate implementation is still NOT performed in this stage.**
> This FINAL prereg locks exact benchmark sizes, allocations/minimums, CI/precision rule, latency/cost gate, annotation/adjudication protocol, candidate family boundaries, dev diagnostics, reranker conditional gate, protected-set freeze/isolation plan, audit/provenance requirements, one-shot final holdout rules, rerun prevention, and explicit next stage. Results remain unseen; no post-result tuning loopholes. V3 candidate tuning / dataset freeze begins only after this commit, in separate isolated stages.
> Pilot provenance: `eval/retrieval-v3/pilot/pilot_tasks.jsonl` SHA256 `b3250e592d4c80099e29d20d1bf87594f2bac11a59907ac8067d3e1ddbd65da3` (100 lines), `pilot_report.md` SHA256 `f3a01a5f286705df9e9ca6cc8cf6d5fd320a427093649072bc1d5f559e6c669f`, `pilot_provenance.json` SHA256 `64f2dbecb49cf624e0e6b05d84f4c3e1db8876406b473b18ed7526078920b2d2` — single annotator + independent reviewer, 99% labelable / 85% answerable raw / 13% ambiguous / 7% disagreement (93% agreement).

## 0. Reconciled base

| item | value |
|---|---|
| Branch | `codex/retrieval-v3-user-search-quality` |
| Base | `5327661445c37191a3fd61db195f3af4d2cf893a` (tag `retrieval-v2-cycle3-closure-v1` object `0c94d801da23050d0c9537717b2a3e83ee1b0bf6`, peeled commit verified) |
| Prior HEAD | `c1a05cfd980c7a2d89f95cfe9884a2d055d3d5c1` (bootstrap user search quality program) — not rewritten, this freeze is append-only |
| Standing decisions | D-003 / D-007 / D-008 / D-010 / D-011 / D-012 remain history/contracts as applicable; **D-013** supersedes D-004 only for conditional reranking reconsideration; **D-014** closes Q-006 (exact sizes, CI rule, latency budget, annotation protocol) |
| Q-006 | **closed → D-014** (exact final dev/holdout sizes, confidence/precision rule, user-centered paired latency budget, final pilot/annotation protocol now fixed) |
| Pilot | `retrieval-v3-pilot-100-v1` executed retrieval-blind (§2 evidence) — no retrieval/DB/model/embedding/benchmark/latency execution, no protected plaintext access, no system-output inspection |
| Production `ml-service` diff vs D-012/closure baseline | **`0` — `git diff 5327661..HEAD -- ml-service/` 0** preserved |

## 1. Goal and headline gates (D-013 + D-014 final sizes)

- **Goal:** user-satisfying search — system returns what the user actually needs for representative user intent queries over the benefit-compass policy corpus.
- **Headline metric (labelable-answerable tasks only):** **Success@5 grade≥2** — at least one result in top-5 is grade 2 (acceptable) or grade 3 (perfect) on a 3/2/1/0 multi-gold graded scale with equivalence groups.
  - **Release floor:** **Success@5 ≥85%** on representative answerable user-intent tasks (holdout answerable set).
  - **Strong / stretch target:** **Success@5 ≥90%** — not promised, aspirational; if `≥90%` and Wilson lower bound `≥85%`, noted as **strong**.
- **Benchmark sizes (FINAL, frozen before tuning):**
  - **Pilot 100** (already executed, retrieval-blind labelability only, no system results): 100 tasks — strata `12/14/12/12/10/12/13/15` (exact/natural/exploratory/multi-constraint/short/colloquial/ambiguous/unsupported), location-bearing 30.
  - **Dev (tuning/diagnostics): 160 total tasks** inclusive of unsupported.
  - **Holdout (final one-shot): 220 total tasks** inclusive of unsupported.
  - Expected answerable-labelable after excluding unsupported/unlabelable (pilot observed 85% raw → 84.8% among labelable): dev ≈136 answerable (160×0.85), holdout ≈187 answerable (220×0.85). Minimum required answerable-labelable after freeze: **dev ≥130, holdout ≥180** (see §3 per-stratum minima). All totals are exclusive of every v2/Cycle3 history case (union 248) and of each other — overlap 0 required via fingerprint checks.
- **Supporting gates (required before release, diagnostic + safety, headline is not sufficient alone):** Top1 / Top3 / MRR@10 / NDCG@5 / NDCG@10; no-answer / ambiguity safety; ineligible / expired intrusion; official-link validity; latency / cost (§6 + §9).
- **No public claim before sealed final evidence** on the protected holdout (frozen before tuning, independent review PASS, explicit user approval, one-shot evaluation — see §9).
- **Rollout:** no rollout is authorized by D-013/D-014 or this FINAL prereg.

## 2. Retrieval-blind pilot — 100 user-like tasks (evidence for this freeze)

The retrieval-blind pilot required by the bootstrap has been **executed exactly as preregistered**:

- **Purpose:** validate labelability / answerability / ambiguity / strata / annotation disagreement without ever inspecting system retrieval results.
- **Method:** 100 user-like tasks spanning the strata in §3 from user-intent patterns (paraphrased needs, colloquial/typo variants) **without running any retrieval system or inspecting system outputs**. Annotators labeled labelability, answerability, ambiguity, gold equivalence, and strata membership only. **No system-result inspection at any time.** Permissible sources only: prereg taxonomy + generic 6-category policy schema + Korean query-pattern intuition; **no protected evalset plaintext reused**.
- **Annotation protocol (prereg-permitted pilot alternative):** **single annotator + independent reviewer — no fabricated second human annotator.** Primary author drafted 100 queries; independent reviewer re-labeled 100% for strata/answerability/ambiguity/location-bearing and 30% stratified subsample (n=30) for grade/equivalence; disagreements adjudicated; final labels durable in `pilot_tasks.jsonl` (see provenance above).
- **Outputs (observed):**
  - labelability **99%** (99/100; 1 unlabelable `v3p-042` contradictory age bounds — revision below)
  - answerability **85% raw** (85/100; 84/99 84.8% among labelable) — supports sizing with 15% unsupported uplift
  - ambiguous **13%** (13/100; distribution 4/3/3/3 across underspecified/missing_eligibility/missing_location/vague_benefit_type)
  - strata coverage: every required stratum ≥10 (10–15), location-bearing **30%** stratified
  - annotation disagreement **7%** unique tasks (6 grade, 3 equivalence, 2 ambiguity on relevant subsamples; 93% agreement, 0 residual after adjudication)
  - instruction revisions (3): contradictory-query exclusion, explicit ambiguity handling (clarification vs safe abstention), exploratory equivalence-group grouping rule
  - Full metrics, distributions, and limitations in `eval/retrieval-v3/pilot/pilot_report.md` §§3–8; validation in `eval/test_retrieval_v3_pilot.py` (8 tests).
- **Gate to proceed:** pilot showed 99% labelable / 13% ambiguous / 7% disagreement — **no re-pilot required.** If pilot had shown <90% labelable, >30% ambiguous, or >20% disagreement, benchmark design would have been revised and re-piloted. The observed rates justify fixing sizes as in §3 and moving to FINAL freeze.

## 3. Strata — exact minimums / allocations (coverage required in dev 160 + holdout 220)

The benchmark (and pilot) must cover these strata explicitly; per-stratum diagnostics are required and no stratum may be omitted without justification. The minima below are **exact minimum allocations sufficient for per-stratum diagnostics** (Q-006 requirement):

| stratum | pilot 100 (done) | **dev 160 minimum** | **holdout 220 minimum** | notes |
|---|---:|---:|---:|---|
| exact / navigation | 12 | **≥18** | **≥25** | known title/program/ID lookup |
| natural needs | 14 | **≥22** | **≥30** | natural-language need statements |
| exploratory multi-valid | 12 | **≥18** | **≥28** | open-ended, multiple policies valid — 2–3 grade-2 equivalence groups each |
| multi-constraint eligibility (≥2 constraints) | 12 | **≥22** | **≥32** | ≥2 eligibility constraints must all hold |
| short keywords (2–3 tokens) | 10 | **≥15** | **≥22** | 2–3 token keyword queries |
| colloquial / typo / spacing / abbrev | 12 | **≥18** | **≥25** | colloquial, typos, spacing, abbreviations |
| ambiguous | 13 | **≥18** | **≥28** | underspecified; safe handling under safety gate |
| unsupported / no-answer | 15 | **≥29** | **≥30** | no eligible policy — correct behavior safe abstention / no-answer |
| **Total** | **100** | **160** | **220** | each column sums to its total; excess stays within minima |
| **location-bearing separately** | 30 | **40–56 (25–35%)** | **55–77 (25–35%)** | cross-cutting; distributed across strata, not isolated; evaluated pooled + separate location vs not |

- **Diagnostics (not separate strata but reported slices):** source (Youth/Gov24) / category (6-way: housing_finance / family_care / employment_education / welfare_health / culture_community / business_agriculture) / freshness (stable vs fresh) / common-vs-rare (frequent vs infrequent policy need) — report per-slice Success@5 to detect bias. Each category/common/rare slice has ≥12 tasks in holdout for gross bias detection.
- **Per-stratum diagnostic precision limitation (explicit):** with per-stratum n≈22–32 (holdout), per-stratum Wilson 95% half-width at `p=0.85` is **±9–14 pp** (n=32→±12.2 pp, n=25→±13.8 pp, n=15→±15–17 pp). Per-stratum diagnostics therefore detect **only large gaps (>18–20 pp)** and are **not gated as per-stratum release floors**. Claiming per-stratum 85% floors would require n≥60 per stratum and is out of scope. This limitation is accepted.
- **All strata minima must be met after excluding unlabelable** (pilot 1% unlabelable rate included as slack).

## 4. Golds, grading, and adjudication (FINAL protocol)

- **Multi-gold graded 3/2/1/0 per query:** each query may have multiple golds, each graded 3 = perfect answer, 2 = acceptable, 1 = partially relevant, 0 = irrelevant. A query's gold set is an equivalence group per grade.
- **Equivalence groups:** when multiple documents are equally acceptable (e.g., same program via different sources, duplicate-deduped), they form an equivalence group at the same grade; retrieving any member at that grade counts as that grade.
- **Answerability / ambiguity labeling:** each query is labeled answerable vs unsupported/no-answer and unambiguous vs ambiguous (with ambiguity type: underspecified_intent / missing_eligibility / missing_location / vague_benefit_type) by annotators **before** gold assignment; unsupported/no-answer queries have **no grade 2/3 golds** and are evaluated under the safety gate, not the headline Success@5.
- **Annotation protocol:**
  - **Pilot 100 (already executed):** **single annotator + independent reviewer** (prereg §4 permitted alternative, no fabricated second human annotator) — reviewer re-labeled 100% for strata/answerability/ambiguity/location and 30% subsample for grade/equivalence; 7% disagreement, 0 residual after adjudication.
  - **Final benchmark (dev 160 + holdout 220, frozen before tuning):** **two independent annotators + third adjudicator for every query** (not subsample). Annotators independently assign strata, location-bearing, answerability, ambiguity type, per-gold grade (3/2/1/0) and equivalence grouping. **Inter-annotator agreement reported** (raw agreement + Cohen's κ for strata/answerability/ambiguity and for per-gold grade). **All disagreements adjudicated** by third adjudicator; residual 0 after adjudication. Instruction version is the **revised instruction post-pilot** (pilot_report.md §6): (i) contradictory-query exclusion, (ii) ambiguity handling — system must request clarification or safe abstention; ambiguous golds conditional on interpretation and scored under safety, (iii) exploratory equivalence-group rule — keep 2–3 distinct grade-2 groups separate; grade-1 peripheral diagnostic only. **No system retrieval output is shown to annotators at any time** (retrieval-blind annotation).
- **Quality of golds:** every query's `(source, source_id)` golds are validated against the **source-truth policy table** (no synthetic golds without table existence); duplicate golds within a query are rejected; empty gold set allowed only for unsupported/no-answer.

## 5. Metrics (FINAL)

- **Headline (labelable-answerable tasks only):** **Success@5 grade≥2** — fraction of answerable queries where at least one retrieved result in top-5 has grade 2 or 3 on equivalence groups.
  - Also report **strict grade-3** Success@5 as diagnostic; and Success@5 vs Success@3 vs Success@1 curves.
- **Secondary (per query, headline set):** **Top1 / Top3 / MRR@10 / NDCG@5 / NDCG@10 / per-stratum Success@5 / location vs not Success@5** — reported alongside headline, not gated as release floors (diagnostic).
- **Safety (separate evaluation, not mixed into headline):** no-answer / ambiguity safety (correct handling rate for unsupported + ambiguous; false-positive intrusion rate when system answers where it should abstain or clarify); **ineligible / expired intrusion** (rate at which ineligible or expired policies appear in top-5); **official-link validity** (fraction of top-5 official links that resolve and match the claimed source). Headline denominator **excludes** unsupported/no-answer and unlabelable; safety has its own denominator (≥30 unsupported holdout + ≥28 ambiguous holdout).
- **All metrics are computed on graded multi-gold equivalence groups**, not on raw source_id string match alone; grade≥2 is success, grade-3 strict is reported separately.

## 6. Thresholds, confidence, precision, and claims (FINAL, replaces bootstrap §6)

- **Release floor:** **Success@5 ≥85%** on the representative held-out benchmark **answerable set** (point estimate).
- **Strong / stretch target:** **Success@5 ≥90%** — aspirational, not promised. If `≥90%` with Wilson lower bound `≥85%`, noted as **strong**.
- **Confidence / precision rule (Q-006 fixed):**
  - **Interval:** **95% Wilson score interval** (no continuity correction) is primary; **Clopper-Pearson exact** reported as sensitivity. Both on headline Success@5.
  - **Design precision (sizing rationale):** benchmarks sized so that **expected Wilson half-width ≤5.5 pp when observed p=0.85** on holdout answerable set and **≤5.0 pp when answerable n≥190**. For `p=0.85`: `n=136 → half 6.0 pp`, `n=180 → 5.2 pp`, `n=187 → 5.0 pp`, `n=196 → 4.9 pp`, `n=250 → 4.4 pp`. Holdout 220 total → expected answerable ~187 (using pilot 85% rate) → expected half **≈5.0 pp**, meets design `≤5.5 pp`; dev 160 → expected 136 → half ≈6.0 pp for tuning diagnostics (acceptable for non-final).
  - **Gate (no post-result tuning):**
    - **PASS** iff **point estimate ≥85% AND Wilson 95% lower bound ≥80%** on holdout answerable set. Example: `n=187, p=0.85 → Wilson [79.3%, 89.4%] → lower 79.3 <80 → HOLD (not PASS)`; `n=187, p=0.86 → [80.4%, 90.3%] → PASS`. This prevents passing on lucky variance with modest n while keeping the floor at 85% point estimate.
    - **HOLD** = point ≥85% but lower <80% (insufficient precision), or marginal secondary/safety HOLD.
    - **NO-GO** = point <85% or safety/headline regression, or ineligible/expired intrusion regression.
    - **Per-stratum and secondary metrics are not gated** on Wilson; their per-stratum half-width is ±9–17 pp (see §3 limitation) and they serve as bias diagnostics (>20 pp gap triggers investigation).
- **No public claim before sealed final evidence:** no public claim of meeting the 85% floor (or 90% target) may be made before the sealed one-shot final evaluation on the protected holdout (frozen before tuning, independent review PASS, explicit user approval, audit chain verified — see §9). The dev 160 result is **not** a claimable floor.

## 7. Candidate families — exact boundaries (FINAL)

- **Candidate A — fielded primary family (only family implemented in next stage):** **fielded sparse+dense union/hybrid (Postgres FTS / BM25-equivalent as feasible) + exact title/org/entity + field weighting + duplicate/diversification**.
  - Union/hybrid: sparse lexical (Postgres FTS or BM25-equivalent) and dense vector retrieval are combined via union or hybrid scoring, not single-signal only.
  - Exact signals: exact title / organization / entity matching is an explicit signal, not subsumed by dense alone.
  - Field weighting: title, eligibility, and other fields are weighted explicitly.
  - Duplicate / diversification: duplicate detection and diversification are required to avoid redundant top-5.
  - This family is the **only** family to be implemented and tuned on dev. **No v2 K/threshold/source-bias sweep continuation.** No embedding replacement at this stage.
- **Candidate B — optional lightweight ranker (conditional, not fielded unless gate below passes):** **optional lightweight reranking only after materially new v3 evidence shows high first-stage recall yet ranking still limits, not an old cross-encoder re-enable.**
  - **Admission gate (strict):** Candidate B is permitted **only if** on dev **union oracle Recall@100 ≥95–97%** (whether any grade≥2 gold appears in the union of sparse+dense+exact top-100, before ranking) **and** ranking still limits headroom to top-5. I.e., dev diagnostic shows first stage already covers the answer in top-100 for ≥95–97% of answerable queries, but the answer is not ranked into top-5 by the current hybrid ranker. Evidence must be a dev diagnostic report, not an intuition.
  - D-013 supersedes D-004 **only for this conditional reconsideration**; the old cross-encoder reranking remains not adopted otherwise.
  - **Embedding replacement / LLM rewrite / LLM-as-judge is last resort / out of initial scope** — not in the fielded families unless first-stage coverage **and** lightweight reranking both fail to close the gap after diagnosis on dev (requires a new decision).
- **Out of scope for this FINAL:** global abstention threshold, public region search (D-004 otherwise in force), new candidate families beyond A/(conditional)B.

## 8. Dev diagnostics and coverage gate (FINAL)

- **On dev, measure dense / sparse / exact / union oracle Recall@30 / Recall@50 / Recall@100** (oracle = whether any grade≥2 gold appears in the top-K of that signal or the union, regardless of current ranker score). Report per-signal and per-stratum **and** per location-bearing vs not and per rare-policy vs common.
- **If union Recall@100 <95%, stop ranker work and fix coverage / data representation first** — do not proceed to Candidate B lightweight reranking. The first-stage coverage or index/data representation must be fixed until the union oracle reaches **≥95%** before any reranker is considered. No v2 K / threshold / source-bias sweep continuation: v2 vector-pool K=128/256/512, threshold, and source-bias sweeps are historical cycle3 results (baseline 36/36, all candidates net 0) and are not continued as v3 tuning.
- **Dev selection:** candidate tuning on dev 160 may explore hybrid weighting / field weights / dedup threshold within the fielded family, but **no new signal** beyond §7 A. Selection uses headline Success@5 on dev answerable set plus the safety/secondary diagnostics (§5); dev result does not gate the holdout claim.
- **Reranker conditional gate is exactly §7 B** — not an independent dev threshold.

## 9. Guardrails — freeze / review / one-way evaluation / audit / rerun prevention (FINAL)

### Protected-set freeze & isolation plan

- **Two frozen benchmarks, both before any candidate tuning:**
  - **Dev 160** and **Holdout 220** are each frozen in **separate isolated builder sessions** that have no access to candidate code or to each other's plaintext after freeze.
  - **Fingerprint-only overlap checks (fail-closed) required before tuning:** each freeze validates **query fingerprint** `SHA256(NFC+strip+collapse_whitespace+casefold)` and **gold fingerprint** `SHA256(source+NUL+source_id)` against (i) all v2/Cycle3 history — P0 canonical 81, cycle1 dev 36, cycle1 holdout 40, cycle2 dev 36, cycle2 disqualified holdout 40, hard-negative 36, cycle3 dev 36 + holdout 40, catalog union 248 — and (ii) between dev ↔ holdout and against each other. Overlap must be **exactly 0** for query and for gold, except the documented `P0↔hard_negative 21` expected overlap which is excluded from the holdout gate. Fail-closed: any non-zero unexpected overlap → freeze rejected.
  - **Source-truth validation:** every `(source,source_id)` gold must exist in the policy table at freeze time; expired/ineligible intrusion cases are validated as ineligible per table.
  - **Sealing:** each benchmark has `evalset.jsonl` (LF, canonical JSON), `manifest.json` (counts, SHA256, provenance), `annotation_audit.json` (strata/balance/ambiguity/freshness), `SEALED.md` — plus `fingerprints.json`/`fingerprints.sha256`. The holdout's plaintext (`evalset.jsonl`) lives **only** on its isolated protected branch/tag (e.g., `codex/retrieval-v3-holdout-freeze` / `retrieval-v3-holdout-v1`) — **never on the candidate/dev branch** and never merged/cherry-picked.
  - **Builders are not reused for tuning.** No retrieval/DB/model/embedding execution in builder sessions beyond table-existence checks.

### Audit / provenance (must PASS before protected execution)

- **Append-only, hash-chained audit log** for every protected-set access and every benchmark execution: `eval/retrieval-v3/audit/events.jsonl` (JSONL, fields `schema_version, event_id, utc_timestamp, git_head, git_dirty, process_id, session_id, action, candidate_id, set_role, set_sha, command, runner_id, outcome, previous_event_hash, event_hash`), chain verified via `previous_event_hash`/`event_hash` (SHA256 of canonical JSON). Actions include `run_start/run_end`, `protected_access_start/protected_access_end` (with exact `set_sha`, `session_id`, `expected_event_hash`, outcome).
- **Independent review required:** before any protected holdout evaluation, an independent reviewer verifies (i) audit chain integrity, (ii) fingerprint isolation (0 overlap), (iii) manifest SHA256 pinned, (iv) candidate freeze identity. Review verdict must be **PASS**.
- **Explicit user approval** required after review and before the one-shot holdout run.

### One-shot final holdout rules & rerun prevention

- **Final evaluation is one-shot:** the protected holdout (220) is evaluated **exactly once** in a single canonical batch (all tuned candidates + baseline together, interleaved per §6 latency methodology where applicable). The batch identity (e.g., `v3-canonical-holdout-v1`) and run event are logged in the audit chain.
- **No post-result retuning:** after the holdout batch is evaluated, **no candidate may be tuned, retrained, threshold-adjusted, or re-ranked to manufacture a PASS on the same holdout**. No additional holdout runs are permitted, even if the result is HOLD/NO-GO. A new evaluation requires a **new holdout frozen before tuning** and a new prereg decision (not an addendum to this prereg).
- **Canonical execution count guard:** the holdout batch `run_start`/`run_end` pair is **exactly one** in the audit chain forever; any second `run_start` for the same holdout set is rejected fail-closed.
- **No history rewrite:** no amend/reset/rebase/squash/force-push of benchmark commits; tags are annotated and peeled identities are verified and immutable; audit log is append-only (no delete/reset/truncate).
- **D-007 is historical:** D-007 governs v2/Cycle3 history only; v3 is governed by D-013 + D-014 + this FINAL prereg. **v3 latency budget is now defined in D-014/§9** (D-007 latency does not apply to v3).
- **This FINAL prereg is execution authorization for the next stage only as far as dataset freeze + runner implementation + independent review + one-shot protected evaluation under the gates above.** It does not authorize production rollout.

## 10. What is STILL NOT authorized or changed in this stage (explicit)

- **Candidate implementation is still NOT performed in this stage.** This commit freezes the design only; no `eval/retrieval-v3/` candidate code, no runner, no DB/model/embedding/benchmark/latency execution, no `DATABASE_URL`/`SENTENCE_TRANSFORMER` usage.
- **No dataset freeze is performed in this stage.** Dev 160 / holdout 220 are sized and planned but not yet built/frozen — that is the next isolated stage.
- **No protected dev/holdout/evalset/canonical result plaintext per-case access** beyond the aggregate/provenance facts durable in docs/memory and the pilot 100 (which is not protected). No `git show`/`cat-file`/`checkout`/`restore`/`sparse`/`parent worktree` access to any v2/Cycle3 or v3 protected set.
- **No production `ml-service` behavior change** (`git diff HEAD -- ml-service/` still 0 from D-012 base through this freeze).
- **No new branch/tag creation** beyond this freeze commit and its push; no history rewrite; no tag/branch deletion/main merge.
- **No `docs/RETRIEVAL_V2.md` rewrite** (V2 remains cycle-1 HOLD / cycle-2 disqualified / cycle3 closure without holdout).

## 11. Next gates (explicit, no auto-advance)

1. **Isolated dataset freeze(s)** — separate isolated builder session(s) with fingerprint-only isolation checks — freeze dev 160 (`retrieval-v3-dev-v1`) and holdout 220 (`retrieval-v3-holdout-v1`), each sealed before tuning, independent review of manifests/fingerprints/audit.
2. **Runner implementation + independent review** — implement Candidate A hybrid family (§7) + dev diagnostics + latency harness + audit integration in a sparse-isolated worktree without accessing holdout plaintext; pure/static/mock tests + self-review; no holdout evaluation.
3. **One-shot final holdout evaluation** — only after freeze + implementation complete + independent review PASS + explicit user approval — single canonical batch on protected holdout 220, interleaved warm paired latency measurement, audit-logged exactly once; report headline Success@5 Wilson CI + secondary/safety + per-slice + latency/cost; durable result commit.
4. **Hold decision from sealed evidence** — PASS/HOLD/NO-GO per §6 gates; no post-result retuning; rollout is a separate decision if PASS.

**This FINAL prereg STOPs after the durable docs/memory/pilot commit.** No dataset freeze, runner implementation, retrieval execution, or holdout access follows from this commit. Results remain unseen; no post-result tuning loopholes.

*— END FINAL prereg freeze — pilot evidence + D-014 Q-006 closure locked before any candidate tuning —*
