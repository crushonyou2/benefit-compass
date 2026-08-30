# SESSION LOG — append, dated

One short section per working session: what was worked on, what was decided (with D-### links), what's pending. When context resets, this file is the recovery path — write it for the next session's reader.

---

## 2026-08-30

- Project initialized with the ballast memory structure (D-001)
- Public baseline freeze is complete. Ballast scaffold was initialized and the confirmed P0-P3 standing decisions were backfilled (D-002…D-006). Next planned work is to define the Retrieval v2 evaluation contract (Q-001). Evaluation and production SSOTs remain `eval/canonical_manifest.json` and `docs/P3_PUBLIC_ROLLOUT.md`.
- Retrieval v2 evaluation contract approved and recorded as D-007; Q-001 closed. Next work may begin with Retrieval v2 dev/holdout evaluation scaffolding and offline experimentation. Q-002 cold-start and Q-003 generic ML normalization remain open.
- Retrieval v2 evaluation scaffolding implemented (eval/retrieval-v2/*, source-macro Recall@5, paired baseline-vs-candidate, P0/hard-negative/latency gates, canonical guard); no candidate algorithm, canonical and production retrieval unchanged.

## 2026-08-30 — Retrieval v2 evaluation cycle 1 closes as HOLD (D-008)

- **Scope:** state整理 only — no benchmark/DB/model/embedding/holdout/P0/hard-negative/latency rerun, no candidate retune, no threshold/gate relaxation, no code/eval artifact edits. Branch `codex/retrieval-v2-cycle1-hold-record` from `3ac62181de9c343511adfb2db82cb0cc64b36009`.
- **Reconciled base:** clean branch `codex/retrieval-v2-latency-provenance-recovery` HEAD `3ac62181de9c343511adfb2db82cb0cc64b36009`; tag `retrieval-v2-latency-provenance-v3` (object `c0d2a9321114144b5ab4235a66c80faf6f112c57`) peeled HEAD verified; remote一致. D-002…D-007, OPEN-QUESTIONS, SESSION-LOG read. Model `Muse Spark 1.2 Contributor / 매우 높음` unchanged.
- **Cycle-1 frozen candidate:** `retrieval-v2-candidate-v2` commit `5745cc3144b519da456b21030d0e0752d1d018ae` (artifact `c6c082681b4f2fcd521790e50c5fd46549116307`, manifest `eval/retrieval-v2/candidate/manifest.json` LF `86f80ff6389ede4673e3c8d819cfab2ceefc79b8979a68b7b2bb5d64cc8eccff`).
- **Gate outcomes (artifact/tag cross-verified, no rerun):**
  - Final holdout quality **PASS**: baseline 33/40 → candidate 36/40, source-macro 0.825 → 0.900, net +3 (gains holdout-001/028/036, losses 0), Youth 18/20→20/20, Gov24 15/20→16/20. Tag `retrieval-v2-final-holdout-result-v1` (`d86e0119f9ac5cf3028364df24d898ff638d3b76`, summary `eval/retrieval-v2/final/summary-v1.json`).
  - P0 regression **PASS**: Youth 28/60, Gov24 16/21. Tag `retrieval-v2-p0-result-v1` (`3373da294b73705861b7a0e494ba802f9e9f6786`, `eval/retrieval-v2/p0/p0-candidate-v2.json`).
  - Hard-negative paired safety **PASS**: pure-positive 15/21→16/21, excluded-policy intrusion 0/3→0/3. Tag `retrieval-v2-hard-negative-result-v1` (`34ca5a537f0a537b9217e3b2fffd005b80a5fe19`, `eval/retrieval-v2/hard-negative/paired-candidate-v2.json`).
  - Warm paired latency **HOLD**: baseline p95 476.51 ms, candidate p95 480.55 ms, delta +4.04 ms; D-007 requires `candidate p95 <= baseline p95`. Tag `retrieval-v2-latency-result-v1` (`b04556f9251d6cabadd32c7c39c85dee690c8b48`, `eval/retrieval-v2/latency/latency-candidate-v2.json`).
- **Provenance:** `retrieval-v2-latency-provenance-v3` is final SSOT; independent reviewer verdict **APPROVE** = measurement provenance blocker resolved, **not** latency PASS. Latency numerical gate remains HOLD. `v1`/`v2` remain immutable superseded audit history. Known non-blocking limitations preserved: tags unsigned, no DB snapshot/append-only run log (does not affect HOLD).
- **Overall verdict:** Retrieval v2 evaluation **HOLD** per D-007 §6; evaluation GO not granted, production rollout not authorized. Quality success is explicitly distinguished from mandatory latency failure.
- **Durable record:** D-008 appended (append-only), Q-004 registered (cycle-2 whether to start, open), `docs/RETRIEVAL_V2.md` created as SSOT/status page. Candidate and all cycle-1 artifacts remain immutable; same holdout/benchmark not rerun or retuned to manufacture PASS. Future cycle 2, if chosen, is a separate evaluation cycle and does not retroactively change cycle-1 HOLD.
- ** validations in this task:** `git diff --check` clean; `git diff 3ac6218..HEAD` limited to `memory/` + `docs/RETRIEVAL_V2.md`; no retrieval/DB tests rerun per HARD RULES.

## 2026-08-30 — Retrieval v2 evaluation cycle 2 starts (D-009) — holdout preparation

- **Scope:** cycle-2 start durable record only — no benchmark/retrieval/search/DB ranking, no embedding/model load, no cycle-1 artifact modification, no candidate tuning. Branch `codex/retrieval-v2-cycle2-start` from cycle-1 HOLD `5311e9807bab43f869655e13d4cdd006123f1ed5`.
- **Reconciled base:** branch `codex/retrieval-v2-cycle1-hold-record` HEAD `5311e9807bab43f869655e13d4cdd006123f1ed5`; tag `retrieval-v2-cycle1-hold-v1` object `86482c0b4f76a8adf1f7bc5ed55d9f4a1ff59582` peeled HEAD verified; D-008 HOLD, Q-004 open verified. Model `Muse Spark 1.2 Contributor / 매우 높음` unchanged.
- **Decisions:** D-009 appended (user-confirmed cycle 2 start; D-003/D-004/D-007 unchanged, D-008 immutable, new independent holdout frozen before tuning, cycle-1 results not reused for PASS, latency `candidate p95 <= paired D-003 baseline p95` with fresh D-007 measurement, separate candidate freeze). Q-004 closed → D-009. No algorithm/implementation direction chosen.
- **Docs:** `docs/RETRIEVAL_V2.md` updated to reflect cycle-2 holdout-preparation phase; `memory/00-INDEX.md` unchanged (already links RETRIEVAL_V2 SSOT).
- **Next:** holdout freeze on `codex/retrieval-v2-cycle2-holdout-freeze` + clean candidate start; this holdout-builder session not reused for tuning.
- **Validations:** `git diff --check` clean (to be verified before commit); no retrieval/DB/model rerun per HARD RULES.
