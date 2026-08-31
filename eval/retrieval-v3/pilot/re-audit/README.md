# Pilot Re-Audit — Web HOLD Repair (2026-09-01)

> **Correction for Web HOLD axes A/B.** Preserves original `pilot_tasks.jsonl` as historical evidence (immutable). Adds auditable re-audit.

## A. Provenance is now auditable (HOLD A repaired)

- **Original pilot** (`pilot_tasks.jsonl` SHA256 `b3250e592d4c80099e29d20d1bf87594f2bac11a59907ac8067d3e1ddbd65da3`, 100 lines) contained **final labels only** — no raw reviewer labels/session provenance. The prior `7% disagreement / 93% agreement / 0 residual` **cannot be independently reconstructed** and is **not claimed as proven** here. Original files are preserved as historical evidence; this re-audit is transparent correction.

- **Re-audit sanitized input:** `pilot_reaudit_input.jsonl` SHA256 `a47bb525f7966d7c23a06e57fc361119eca1c610e0cc1caf77e4cf2cd828aea3` — 100 lines `task_id + query_text` only, **excludes all label fields** (`stratum`, `location_bearing`, `answerable`, `ambiguous`, `golds`, etc.). No system results or protected data exposed.

- **Two independent delegated annotators** reviewed **all 100** for stratum/location/conceptual-answerability/ambiguity **and all 100 for grade/equivalence** (exceeds prereg 30% stratified sample; full 100 preferred):
  - `reviewer_A_raw_labels.jsonl` SHA256 `2d8a84b93d1e62870d42978d1d51ddef18373da6b6809d65d33d069929eba1eb` + `reviewer_A_provenance.json`
  - `reviewer_B_raw_labels.jsonl` SHA256 `15b98f3522ed9acd560aa5bb75f7fc30991fb2815f6521bfbeadbb171f5fcb89` + `reviewer_B_provenance.json`
  - Each provenance records `agent_label`, `timestamp`, `model_role` (Muse Spark 1.2 Contributor delegated; root gate verified), `sanitized_input_sha256`, `total_tasks 100`. OMP session identifiers are not durably obtainable via filesystem — recorded as available (agent_label+timestamp+SHAs) without overclaiming.

- **Separate adjudication:** `adjudicated_labels.jsonl` SHA256 `fe198a28676f5b628f803a2cf60a2ecce0aaa0bccae262389363ed82c58d3f2a` — third adjudicator resolves all 19 disagreements deterministically (log: `adjudication_log.json`), residual 0.

- **Disagreement recomputable:** `disagreement_matrix.json` stores `any_disagreement 19/100 (19%)`, per-dimension rates, stratum confusion, and detailed task diffs. Recompute by aligning `task_id` between raw A/B JSONLs — pure JSON, no DB/retrieval.

## B. Terminology corrected (HOLD B repaired)

- Pilot `answerability` is **CONCEPTUAL/INTENT only**, not corpus-grounded source-truth. Prior `85% answerable` is concept-level intuition and **MUST NOT** size final benchmark. Final frozen benchmark answerability is **source-truth grounded**: every headline task must have `≥1 grade≥2 (source,source_id)` validated against source-truth; unsupported has none; ambiguous is safety-only (see D-015). Benchmark builders must reject/replace unlabelable before freeze (frozen dev/holdout have 0 unlabelable).

## Selection / Protocol

See `reaudit_protocol.json` for full protocol, selection, and recomputation method.

## Files (this directory)

- `pilot_reaudit_input.jsonl` — sanitized input (task_id+query_text only)
- `reviewer_A_raw_labels.jsonl` / `reviewer_B_raw_labels.jsonl` — durable raw labels
- `reviewer_A_provenance.json` / `reviewer_B_provenance.json` — reviewer provenance
- `adjudicated_labels.jsonl` — adjudicated final labels
- `adjudication_log.json` — per-task adjudication decisions
- `disagreement_matrix.json` — recomputable matrix + detailed diffs
- `reaudit_protocol.json` — protocol, selection, terminology correction

No protected data, no retrieval/search/ranking execution, no DB/model/embedding usage in this re-audit.
