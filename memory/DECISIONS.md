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
