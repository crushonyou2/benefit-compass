# memory/ — benefit-compass brain

Purpose: this folder is the durable memory for benefit-compass. Conversations forget; this folder does not. What is recorded here survives topic changes, session resets, and context compaction.

## File map

| File | What | Write rule |
|---|---|---|
| `DECISIONS.md` | Confirmed decisions | Append-only. Supersede protocol — never edit past entries |
| `OPEN-QUESTIONS.md` | Unresolved items awaiting a decision, and readings in force the user has not confirmed | Two tables. Close each row with a link to the resolving decision, or drop it |
| `SESSION-LOG.md` | What happened, per working session | Append, dated |
| `PRODUCT-TRUTH.md` | What the product actually does (if applicable) | Evidence + date only. Three sections: implemented / not / excluded |

## Project status / reference docs

- `docs/RETRIEVAL_V2.md` — Retrieval v2 SSOT/status page (cycle-1 HOLD, D-007/D-008, frozen candidate, gate outcomes, provenance).
- `docs/RETRIEVAL_V3_PREREG.md` — Retrieval v3 FINAL REPAIR prereg/freeze (D-013/D-015 supersedes D-014, pilot 100 + auditable re-audit, dev 180 / holdout 250 exact, headline 130/180 BY CONSTRUCTION, Wilson/Clopper, deterministic safety/B/latency/tuning gates) — SSOT for v3 evaluation.
- `eval/retrieval-v3/pilot/` — Retrieval-blind pilot 100 durable artifact (tasks, report, provenance) — historical SSOT.
- `eval/retrieval-v3/pilot/re-audit/` — Auditable re-audit correction (sanitized input, raw A/B, disagreement matrix recomputable, adjudicated, protocol) — SSOT for Web HOLD A/B repair.

## Operating principles

1. **Record in-session.** Decisions and important facts are written the moment they appear, not at the end. Zero loss.
2. **User-confirmed vs AI-proposed are always distinguished.** A proposal the user hasn't confirmed is not a decision — and neither is your reading of a non-answer; that is registered in OPEN-QUESTIONS.md as `assumed`.
3. **Claims carry labels** — confirmed / observed / assumed / hearsay / unknown (see the ballast verify-gate skill).
4. **External product claims require truth-file evidence** (see the ballast proof-standard skill).
5. **Unresolved things get registered**, not remembered. If it's not in OPEN-QUESTIONS.md, it will be lost.
