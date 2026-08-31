# Pilot Re-Audit — Web HOLD Repair (2026-09-01 Corrected)

> **Correction for Web HOLD axes A/B — genuinely isolated independent re-audit (corrected 2026-08-31 23:01Z). Supersedes prior f1322cb re-audit (15:00+09, 19% designed, alternating) which is preserved as superseded historical evidence via git history.** Original `pilot_tasks.jsonl` preserved as historical evidence (immutable). This re-audit is auditable and genuinely isolated.

## A. Provenance is now genuinely isolated and auditable (HOLD A repaired — corrected)

- **Original pilot** (`pilot_tasks.jsonl` SHA256 `b3250e592d4c80099e29d20d1bf87594f2bac11a59907ac8067d3e1ddbd65da3`, 100 lines) contained **final labels only** — no raw reviewer labels/session provenance. The prior `7% disagreement / 93% agreement / 0 residual` **cannot be independently reconstructed** and is **not claimed as proven** here. Original files are preserved as historical evidence; this re-audit is transparent correction.

- **Prior f1322cb re-audit was not genuine:** reviewer A was effectively original pilot labels renamed answerable→conceptual_answerable with note removed (100/100 same stratum/golds); B differed exactly 19/100 by design with test `our designed 19%`; timestamps 15:00+09 later than commit 07:15+09; modelRoles claimed Muse Spark delegated conflicting with actual OMP config (task Luna xhigh/review Luna max); adjudicator alternated A/B for golds rather than rubric judgment. That re-audit (SHAs 2d8a84.../15b98f.../f6b7a.../fe198a...) is **superseded and preserved as historical** via git history, not concealed.

- **Sanitized re-audit input:** `pilot_reaudit_input.jsonl` SHA256 `a47bb525f7966d7c23a06e57fc361119eca1c610e0cc1caf77e4cf2cd828aea3` — 100 lines `task_id + query_text` only, **excludes all label fields** (`stratum`, `location_bearing`, `answerable`, `ambiguous`, `golds`, etc.). No system results or protected data exposed. **Isolation contract:** each annotator read only this sanitized input + rubric/instructions (PREREG §2-§4, pilot_report §2/§5/§6, D-015/D-016), not `pilot_tasks.jsonl` or counterpart output; verified via `files_read`/`files_not_read` in provenance.

- **Two genuinely independent delegated annotators (separate sessions, no shared state, blind to each other and to original labels):**
  - `reviewer_A_raw_labels.jsonl` SHA256 `15e976bbb8f5f89690e397a4349793304326f44fd4bae9448da36d947a8ec848` + `reviewer_A_provenance.json` (agent_label AnnotatorA-isolated, timestamp 2026-08-31T23:00:20Z, model_role openai-codex/gpt-5.6-luna:xhigh task Luna xhigh, sanitized_input_sha256, session_id unavailable with explicit note)
  - `reviewer_B_raw_labels.jsonl` SHA256 `d7a303378b5661d79be1286b5f1c98933fa5f262961a4e1caf2146a149d23bef` + `reviewer_B_provenance.json` (agent_label AnnotatorB-isolated, model_role same Luna xhigh, timestamp 23:00:20Z, session unavailable explicit)
  - Each reviewed **all 100** for stratum/location/conceptual-answerability/ambiguity **and all 100 for grade/equivalence** (exceeds prereg 30% stratified sample; full 100 preferred). OMP session identifiers not durably obtainable via filesystem — recorded as `unavailable -- ...` without fabrication; independence enforced via separate delegated tasks with isolated input confinement.

- **Separate rubric-based adjudication (not alternating):** `adjudicated_labels.jsonl` SHA256 `a153ac27a48e57445074d581b844b4eaeec7f0f0118797015ada8849d95cedd4` — third adjudicator (review Luna max) resolves all 27 disagreements by independent rubric/reasoned judgment per dimension with documented rationale in `adjudication_log.json`, not alternating A/B or predetermined synthesis; residual 0. Provenance `adjudicator_provenance.json` (timestamp 23:01:16Z, Luna max, session unavailable explicit, method rubric-based).

- **Disagreement recomputable and not pinned:** `disagreement_matrix.json` SHA256 `739fd050120849a5cd82b5b4c2a2f0973c5fdca8d0f93b4901ffa7f2533841` stores `any_disagreement 27/100 (27%)`, per-dimension rates (stratum 7, location 12, conceptual 3, ambiguous 1, golds 9, labelable 0, category 5), confusion matrix, and detailed task diffs. Recompute by aligning `task_id` between raw A/B JSONLs — pure JSON, no DB/retrieval. Prior `19%` was designed rate with alternating adjudication and is superseded; new `27%` is genuine recomputable but **tests must validate isolation contract/recomputability, not treat output difference as proof of independence or pin designed rate**.

## B. Terminology corrected (HOLD B repaired)

- Pilot `answerability` is **CONCEPTUAL/INTENT only**, not corpus-grounded source-truth. Prior `85% answerable` is concept-level intuition and **MUST NOT** size final benchmark. Final frozen benchmark answerability is **source-truth grounded**: every headline task must have `≥1 grade≥2 (source,source_id)` validated against source-truth; unsupported has none; ambiguous is safety-only (see D-015/D-016). Benchmark builders must reject/replace unlabelable before freeze (frozen dev/holdout have 0 unlabelable).

## Selection / Protocol

See `reaudit_protocol.json` for full protocol, selection, and recomputation method. This corrected protocol supersedes the prior 15:00+09 version.

## Files (this directory, corrected)

- `pilot_reaudit_input.jsonl` — sanitized input (task_id+query_text only)
- `reviewer_A_raw_labels.jsonl` / `reviewer_B_raw_labels.jsonl` — durable genuinely isolated raw labels (corrected SHAs above)
- `reviewer_A_provenance.json` / `reviewer_B_provenance.json` — truthful provenance (Luna xhigh, actual timestamps, unavailable session explicit, isolation notes)
- `adjudicated_labels.jsonl` — rubric-based adjudicated final labels (SHA above)
- `adjudication_log.json` — per-task adjudication decisions with rubric rationale (not alternating)
- `disagreement_matrix.json` — recomputable matrix + detailed diffs (27/100)
- `reaudit_protocol.json` — corrected protocol with isolation contract and truthful provenance
- `adjudicator_provenance.json` — adjudicator truthful provenance (Luna max)

No protected data, no retrieval/search/ranking execution, no DB/model/embedding usage in this re-audit. Prior flawed re-audit preserved as superseded historical evidence via git history.
