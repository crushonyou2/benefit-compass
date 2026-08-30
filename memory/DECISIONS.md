# DECISIONS — append-only ledger

Rules: only user-confirmed decisions are recorded. Nothing is edited or deleted. A changed decision gets a **new** entry that `supersedes D-xxx`, and the old entry receives exactly one added line: `→ superseded by D-yyy (date)`. Sequential ids, never reused. (Full protocol: ballast decision-ledger skill.)

---

## D-001 · Adopt the ballast memory structure — 2026-08-30 (user, project setup)

This project uses `memory/` as its durable brain: decisions in this ledger, unresolved items in OPEN-QUESTIONS, per-session notes in SESSION-LOG. Standing decisions are followed without relitigating; changes go through the supersede protocol.

<!-- Append new entries below. Example of a superseded pair:

## D-002 · Weekly report goes out Fridays — 2026-01-10 (user, chat)

→ superseded by D-005 (2026-02-01)

## D-005 · Weekly report moves to Mondays — 2026-02-01 (user, chat)

Supersedes D-002. Fridays kept slipping into the weekend; Monday forces the week to start closed-loop.
-->
## D-002 · Keep the P0 canonical evaluation baseline frozen — 2026-08-30 (historical backfill recorded 2026-08-30; user-confirmed during P0 work)

The P0 production-parity canonical artifacts remain the historical evaluation baseline.

Evaluation SSOT: `eval/canonical_manifest.json`.

Do not overwrite or silently regenerate the P0 canonical artifacts as a new baseline. Future Retrieval v2 evaluation artifacts must remain separate from the frozen P0 artifacts.

## D-003 · Keep the current production retrieval contract — 2026-08-30 (historical backfill recorded 2026-08-30; user-confirmed during P0-P3 work)

The standing production retrieval contract is:

- `RERANK=0`
- `CANDIDATES=30`
- `COSINE_MIN=0.78`
- `LEXICAL_OVERLAP_BIAS=0.01`
- `strip_region`
- expired-policy exclusion
- embedding model `intfloat/multilingual-e5-base`
- source-aware youth intent bias remains enabled for explicit youth-intent queries and is suppressed for known Gov24 organization queries

Evaluation numbers and provenance: `eval/canonical_manifest.json`.

Implementation truth: `ml-service/app.py` and `ml-service/source_ranking.py`.

## D-004 · Keep rejected retrieval alternatives out of the current scope — 2026-08-30 (historical backfill recorded 2026-08-30; user-confirmed during P0 work)

The following remain not adopted unless materially new evidence justifies reconsideration:

- cross-encoder reranking
- a global similarity / abstention threshold
- public region search

Public region search is disabled until trustworthy applicability-region data is available; it is not permanently excluded.

Evidence and experiment interpretation: `docs/CUSTOM_SEARCH_MVP.md` and the frozen P0 evaluation artifacts.

A future change must be recorded as a new decision that supersedes this entry rather than editing this entry.

## D-005 · Keep production topology Choice A — 2026-08-30 (historical backfill recorded 2026-08-30; user-confirmed during P3)

The current public request path is:

Public Web
 -> generic API service
 -> promoted P2 API revision
 -> tagged P2 ML revision

The generic ML service remains on the old ML rollback path and is not used by the promoted public API path.

Exact revisions, tags, traffic percentages, rollout evidence, and rollback commands are owned by `docs/P3_PUBLIC_ROLLOUT.md`.

Generic ML normalization is deferred and is a separate future production-routing change.

## D-006 · Follow the post-baseline work order — 2026-08-30 (historical backfill recorded 2026-08-30; user-confirmed)

The agreed work order is:

1. Public baseline freeze — complete.
2. Retrieval v2 — define the evaluation contract first, separate development from final holdout evaluation, then use offline/staging/no-traffic verification before any adoption.
3. Min instances — consider only if real public evidence shows cold starts materially affect users.
4. Generic ML normalization — defer until the final ML revision is settled.

Retrieval v2 does not automatically reopen cross-encoder reranking, a global threshold, or region search. Materially new evidence requires a new decision.

## D-007 · Adopt the Retrieval v2 evaluation contract — 2026-08-30 (AI-proposed, user-confirmed)

Retrieval v2 uses source-macro Recall@5 as the primary quality metric, with Recall@1, Recall@10, MRR@10, per-source Recall@5, and category slices as secondary or diagnostic measures.

The frozen P0 canonical sets remain historical regression gates, not tuning data:

- Youth Recall@5: `>= 28/60` PASS, `27/60` HOLD, `<= 26/60` NO-GO.
- Gov24 Recall@5: `>= 15/21` PASS, `14/21` HOLD, `<= 13/21` NO-GO.

Retrieval v2 uses a separate source-balanced development set of 30–40 new queries and a source-balanced final holdout of at least 40 new queries. The final holdout is frozen before tuning and is never used during development. P0 canonical artifacts remain frozen and the `canonical_*` namespace is not reused for Retrieval v2 artifacts.

On the final holdout, the current D-003 production retrieval baseline and the Retrieval v2 candidate are evaluated on the same queries. A quality PASS requires:

- candidate source-macro Recall@5 greater than the same-set baseline;
- at least `+2` net hit@5 cases;
- no Youth hit@5 regression;
- no Gov24 hit@5 regression.

Hard-negative evaluation is a paired safety check. Blocking conditions are only:

- candidate pure-positive gold hit@5 count lower than baseline; or
- candidate ineligible/excluded-policy top-5 intrusion count higher than baseline.

Absolute score distributions, score gaps, lexical overlap, and no-answer score separation remain diagnostics only and must not reintroduce a global abstention threshold.

Latency is judged by warm paired non-regression. Baseline and candidate are measured with the same environment, database/corpus, benchmark queries, and timed sample count, interleaved in the same run/window after warm-up. Cold/model-load samples are excluded. The primary latency gate is:

`candidate retrieval/search p95 <= paired D-003 baseline p95`.

The timed sample count must be fixed before results are inspected. p50 and sample count are recorded as diagnostics.

Final Retrieval v2 adoption is GO only when all mandatory checks pass:

1. final-holdout quality improvement;
2. `>= +2` net hit@5;
3. no Youth or Gov24 hit@5 regression;
4. both P0 regression gates PASS;
5. hard-negative paired safety PASS;
6. warm paired retrieval latency non-regression;
7. final holdout integrity preserved.

A fixable mandatory failure is HOLD. Clear quality regression or failure to improve on the final holdout is NO-GO.

A Retrieval v2 evaluation GO does not itself authorize production rollout. A passing candidate still proceeds through staging / no-traffic verification and a separate rollout decision.

This decision does not reopen cross-encoder reranking, a global similarity/abstention threshold, or public region search. Those remain governed by D-004.

## D-008 · Close Retrieval v2 evaluation cycle 1 as HOLD — 2026-08-30 (user-confirmed, recorded 2026-08-30)

Retrieval v2 evaluation cycle 1 closes as **HOLD** under D-007 because mandatory warm paired latency non-regression (D-007 §6) failed, despite quality / P0 / hard-negative PASS. Evaluation GO is therefore not granted and production rollout is not authorized.

Cycle-1 gate summary (re-execution prohibited; artifact/tag cross-verified only):

- Final holdout quality **PASS** — baseline 33/40 → candidate 36/40, source-macro 0.825 → 0.900, net +3, Youth 18/20 → 20/20, Gov24 15/20 → 16/20, losses 0. Tag `retrieval-v2-final-holdout-result-v1` (commit `d86e0119f9ac5cf3028364df24d898ff638d3b76`, candidate `retrieval-v2-candidate-v2` `5745cc3144b519da456b21030d0e0752d1d018ae`).
- P0 regression **PASS** — Youth 28/60, Gov24 16/21. Tag `retrieval-v2-p0-result-v1` (commit `3373da294b73705861b7a0e494ba802f9e9f6786`).
- Hard-negative paired safety **PASS** — pure-positive 15/21 → 16/21, excluded-policy intrusion 0/3 → 0/3. Tag `retrieval-v2-hard-negative-result-v1` (commit `34ca5a537f0a537b9217e3b2fffd005b80a5fe19`).
- Warm paired latency **HOLD** — baseline p95 476.51 ms, candidate p95 480.55 ms, delta +4.04 ms; D-007 requires `candidate p95 <= paired baseline p95`. Result tag `retrieval-v2-latency-result-v1` (commit `b04556f9251d6cabadd32c7c39c85dee690c8b48`). Measurement provenance blocker resolved via `retrieval-v2-latency-provenance-v3` (tag object `c0d2a9321114144b5ab4235a66c80faf6f112c57` → commit `3ac62181de9c343511adfb2db82cb0cc64b36009`); reviewer verdict APPROVE means provenance blocker resolved, not latency PASS. Latency numerical gate remains HOLD.

Consequences:

- `retrieval-v2-candidate-v2` and all frozen cycle-1 artifacts remain **immutable evidence**; no retuning, no threshold/gate relaxation, no rerun to manufacture PASS.
- The same cycle-1 holdout / P0 / hard-negative / warm paired latency benchmark is **not rerun or retuned** to seek PASS. D-007 is unchanged.
- No production rollout is authorized from cycle 1.
- A future cycle 2, if chosen (Q-004), is a **separate evaluation cycle** with a separately designed holdout frozen before tuning. It must not reuse the cycle-1 holdout to claim a new PASS and must not retroactively change the cycle-1 HOLD verdict. This HOLD record branch `codex/retrieval-v2-cycle1-hold-record` and tag `retrieval-v2-cycle1-hold-v1` are the durable closure marker.

Reconciled at `3ac62181de9c343511adfb2db82cb0cc64b36009` on branch `codex/retrieval-v2-latency-provenance-recovery`; provenance v3 peeled HEAD verified against remote. No benchmark/DB/model/embedding rerun was performed to produce this record.
