# Retrieval v3 production-exclusion supersession V1 — pre-result gate supersession (D-052 stage)

Status: DESIGN/FREEZE ONLY. No runner, safety, sparse/fusion/dedup, candidate-registry,
selection, result-schema, or production code is changed by this document. The later bounded
implementation (D-003 exclusion inside Candidate-A retrieval + independent top-5 audit) is a
separately reviewed stage, not authorized here. No FIRST protected dev is authorized here.

## 1. Authoritative disposition (pre-result; no protected result exists)

The standing v3 per-policy global `eligible=false OR expired=true` full-corpus gate is not
executable, and its global `eligible` boolean is conceptually invalid for user-specific
applicability. D-049 established: the normalized policy table has no eligible/expired flags;
Gov24 10958 has no total structured active/expired equivalent; Youth official structured codes
are only partial and approval != user eligibility. Keeping the old gate makes v3 permanently
HOLD independent of retrieval results. Do NOT fabricate eligible=true,
NULL=>authoritatively-not-expired, free-text parsing, or inferred status.

The safety purpose remains valid. This document supersedes ONLY that gate with a measurable
D-003 production-parity exclusion contract. D-003 production SSOT already implements
expired-policy exclusion as `(biz_end IS NULL OR biz_end >= CURRENT_DATE)`
(`ml-service/app.py`, standing since D-003). D-007 historical safety likewise framed candidate
excluded-policy intrusion as a production-relative safety check. This is a semantic correction
to measurable production exclusion, NOT a claim that all real-world expired/ineligible
policies are known.

## 2. What is superseded (narrow)

- ONLY the ineligible/expired global-map gate semantics: the prereg §§5/9 gate wording
  (`ineligible/expired top-5 intrusion = 0 cases`, `eligible=false OR expired=true`) and the
  corresponding candidate-plan-v2 gate wording/reference (`selection_rule.safety_gates_dev`
  `ineligible_expired_intrusion`).
- D-015/D-016/D-017 historical text stays visible; D-052 supersedes ONLY their
  ineligible/expired global-map gate semantics, never their sizes, provenance, or other
  contracts. D-003, D-007, D-026, D-027..D-032, D-044..D-051 stand as history/corrected where
  applicable.
- Preserved bytes immutable: `docs/RETRIEVAL_V3_PREREG.md`, `candidate-plan-v1.json`,
  `candidate-plan-v2.json`, `safe-action-policy-v1.json`, D-049 eligibility evidence, D-050
  and all history — none rewritten by this freeze.

## 3. Frozen artifacts (old immutable, new append-only)

- Prereg `docs/RETRIEVAL_V3_PREREG.md` SHA256
  `7842018613d66aa4570f4db2f8ae5a698ceb46757995a6b7e26873177b36160e` — unchanged.
- `eval/retrieval-v3/candidate-plan/candidate-plan-v1.json` SHA256
  `2815361a469fee9bf69f6ffdf2124d19928220535cdb08b2005ae6674ae7d17c` — unchanged.
- `eval/retrieval-v3/candidate-plan/candidate-plan-v2.json` SHA256
  `d233f5c4d912e4d0856d89213d6392fbf44494f5538d018e7412f61781ae6cc6` — unchanged
  (D-050 corrected; D-049 historical `fa370e65…` preserved in history, never rewritten).
- `eval/retrieval-v3/candidate-plan/safe-action-policy-v1.json` SHA256
  `c512fb5627179697a987b05a2431b8f7e30d1153af2ff6dca37995f6b232a35d` — unchanged.
- `docs/RETRIEVAL_V3_SAFE_ACTION_SUPERSESSION_V1.md` SHA256
  `472b6183114a0ebf4d22e9b22c03bb9233b15a736587e29a917aa49113502364` — unchanged.
- `docs/RETRIEVAL_V3_ELIGIBILITY_EVIDENCE_V1.md` SHA256
  `eea3c5ce393f1f3c9563983df16f4648e9c005fd4f317b44cd168b082af91d32` — unchanged.
- NEW `eval/retrieval-v3/candidate-plan/production-exclusion-policy-v1.json` SHA256
  `3bcfc5b8360af28ccd7ea9018f3e3ffda73fba7744ba33bbfb83446235284608` — the single
  frozen machine-readable normative contract (§4; normative detail lives in that file).
- NEW `eval/retrieval-v3/candidate-plan/candidate-plan-v3.json` — v2 values preserved except
  the single authorized gate replacement (§5); carries all six parent SHAs including this
  document's. Hash circularity note: this document is written before plan-v3 so that plan-v3
  can embed this document's hash in its parents; plan-v3's own hash therefore cannot be quoted
  here. It is pinned instead in the D-052 ledger entry and in
  `eval/test_retrieval_v3_production_exclusion_contract.py`, which recomputes and cross-checks
  every SHA in this section.
- NEW `eval/test_retrieval_v3_production_exclusion_contract.py` — pure/static proof: old-byte
  immutability, v2→v3 substantive identity with only the authorized gate diff, exact predicate
  fixtures, denominator/truth-table proof, as-of pin semantics, `eligible` absence from
  normative gate keys. No protected/DB/network/model/retrieval execution.

## 4. Normative replacement gate (exact, machine-recomputable)

Normative detail lives in `production-exclusion-policy-v1.json`; this section is the frozen
human-readable record of the same contract:

- Gate id/name: `production_exclusion` — used consistently in the new contract/plan;
  implementation comes later.
- Safety claim boundary: prove only that Candidate A does not re-introduce policies that the
  frozen D-003 production expiry predicate would exclude. Never label this universal
  `expired`, universal `eligible`, or user-specific eligibility correctness.
- Allowed source fields for classification: `(source, source_id, biz_end)` from the pinned
  evaluation corpus plus one pinned `evaluation_as_of_date`. No raw text, no 신청기한
  parsing, no age/income/region/add_qualify inference, no LLM/model, no score, no protected
  labels/results, no source-specific guesswork.
- `evaluation_as_of_date`: one ISO `YYYY-MM-DD` date in `Asia/Seoul`, captured exactly once
  for the evaluation session BEFORE protected plaintext access/run_start, stored in
  corpus/evaluation provenance/audit, then immutable for the candidate and the paired D-003
  baseline for that run. The later implementation must use the same pinned date rather than
  allowing midnight drift. This freeze stage sets no value and performs no DB query.
- Predicate: `production_excluded = (biz_end is not null AND biz_end < evaluation_as_of_date)`.
  This is the explicit-date equivalent of the D-003 runtime
  `(biz_end IS NULL OR biz_end >= CURRENT_DATE)` under the pinned as-of date.
- `biz_end == null`: classify as `not_production_excluded_by_D003_predicate`; explicitly DO
  NOT claim `not expired` or `eligible`.
- Fail-closed: malformed/non-date non-null `biz_end`, missing `(source,source_id)` lookup,
  missing corpus pin, missing/invalid as-of date, or checker not executed => HOLD, never PASS.
- Audit scope: the Candidate-A internal final top-5 for EVERY benchmark task, even when
  safe-action later yields ABSTAIN/CLARIFY. Safe-action must not waive or hide this
  ranking-layer parity gate. Exact denominators: dev 180 tasks / 900 slots, holdout 250
  tasks / 1250 slots.
- Gate truth table: intrusion task count = 0 AND intrusion slot count = 0 => PASS; any one
  production-excluded policy in any internal final top-5 => NO-GO; missing measurement => HOLD.
- Later bounded implementation MUST apply the same D-003 exclusion before/within Candidate-A
  retrieval so production-excluded rows cannot be ranked, and the safety checker independently
  audits the exact top-5. Not implemented in D-052.
- The global per-policy `eligible` boolean is removed from mandatory release-gate semantics
  with no default replacement. User-specific applicability is not asserted by this gate.
- Youth first-party structured application-period/closed markers from D-049 may be retained
  only as clearly NON-GATING diagnostic evidence when authoritative/recomputable; no new hard
  gate, no synthetic full-corpus map, no dataset regeneration.

## 5. Candidate-plan-v3 mapping (v2 → v3)

- `plan_id` `retrieval-v3-candidate-plan-v2` → `retrieval-v3-candidate-plan-v3`, version
  `2.0.0` → `3.0.0`. v2 bytes untouched.
- Parents carry all six identities: prereg SHA, plan-v1 SHA, plan-v2 SHA `d233f5c4…`, safe-action
  policy SHA, production-exclusion policy SHA `3bcfc5b8…`, and this document's SHA.
- `gating_contract_ref`: the single authorized substring replacement — the
  `ineligible/expired 0/250 & 0/1250 holdout 0/180 & 0/900 dev` wording becomes
  `production_exclusion 0/250 & 0/1250 holdout 0/180 & 0/900 dev`; every other character
  identical.
- `selection_rule.safety_gates_dev`: key `ineligible_expired_intrusion` renamed to
  `production_exclusion_intrusion` with the same 0/180-tasks AND 0/900-slots thresholds, now
  referencing the production-exclusion predicate; selection still requires all mandatory dev
  safety gates PASS and headline Success@5 >= 85%. All other selection fields identical.
- New `production_exclusion_policy` block parallel to `safe_action_policy` (id, SHA, artifact,
  common-to-all-configs, not-a-tuning-axis scope).
- `supersession`, `provenance`, `assertions`, `frozen_at` are D-052 stage-local (this freeze,
  Muse Spark 1.3:xhigh lineage, no DB/network/model/retrieval/protected execution in D-052).
- Everything else — all 18 ranking tuples/order/semantics, dense+sparse/fusion/exact/
  final-pool/dedup/diversification semantics, D-003 baseline descriptor, embedding, MAX24,
  Candidate-B gate, headline >= 85% + Wilson/Clopper, unsupported/ambiguous integer gates,
  location, official-link/HTTP, latency/cost, audit/provenance/isolation/one-shot/rerun
  prevention, D-026 diagnostics, safe-action reference — value-identical to v2.
- The change is prereg/plan semantic supersession before any protected result, not
  result-driven relaxation: no protected result exists; nothing was tuned or relaxed against
  outcomes.

## 6. Verification (pure/static only, before commit)

- New focused contract tests plus the existing Retrieval-v3 10-file gate suite (216 PASS)
  still PASS; new total reported in D-052.
- `git diff --check` PASS; `ml-service` diff 0 vs
  `5327661445c37191a3fd61db195f3af4d2cf893a`; main dev/holdout/result/audit absent; one-shot
  unconsumed; all six old SHAs unchanged.
- Intended files only: this doc, the policy JSON, plan-v3 JSON, the new test, D-052 ledger
  entry, session log. No runner/safety/registry/selection/schema/production change.

## 7. Change control for the frozen contract

- The predicate, allowed fields, denominators, truth table, and as-of pin semantics above are
  frozen. Any future change requires a new versioned policy artifact plus a new plan version
  and decision entry — never an edit to `production-exclusion-policy-v1.json`.
- The `evaluation_as_of_date` value itself is NOT frozen here; it is pinned per evaluation
  session under the semantics in §4.

### VERDICT: FIRST protected-dev launch REMAINS BLOCKED (not authorized; do not launch)

This freeze stage only replaces an unmeasurable gate with a measurable production-parity gate
before any protected result. Implementation is unreviewed and no protected measurement exists.
Next gate after this record and its atomic commit/push is **STOP for Web read-only
independent review** (not bounded implementation, not FIRST dev retrieval, not candidate
tuning).
