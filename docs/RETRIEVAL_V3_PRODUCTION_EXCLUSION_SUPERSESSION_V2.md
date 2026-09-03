# Retrieval v3 production-exclusion supersession V2 — timezone/CURRENT_DATE parity correction (D-053 stage)

Status: DESIGN/FREEZE ONLY. No runner, safety, sparse/fusion/dedup, candidate-registry,
selection, result-schema, or production code is changed by this document. The later bounded
implementation (D-003 exclusion capture inside Candidate-A retrieval + independent top-5
audit) is a separately reviewed stage, not authorized here. No FIRST protected dev is
authorized here. D-053 is a SAME-STAGE Web-HOLD narrow repair of D-052: it supersedes ONLY
the timezone/as-of capture semantics of
`eval/retrieval-v3/candidate-plan/production-exclusion-policy-v1.json`. Policy-v1 bytes and
history are immutable and stay on disk untouched.

## 1. Web-HOLD blocker (durable evidence, not contract)

- D-052 policy-v1 froze `evaluation_as_of_date` as Asia/Seoul and called the pinned date the
  explicit-date equivalent of the D-003 runtime
  `(biz_end IS NULL OR biz_end >= CURRENT_DATE)`.
- Web independent review read-only DB evidence on the governing connection: `SHOW TimeZone`
  returned `GMT`, and `SELECT CURRENT_DATE` returned `2026-09-03`, while the Asia/Seoul local
  date was already `2026-09-04`.
- Therefore a hardcoded Asia/Seoul as-of date can disagree with the actual D-003 decision at
  the date boundary. This is a real production-parity defect, not a wording preference.
- `GMT`, `2026-09-03`, and `2026-09-04` above are evidence only; they are not normative
  expected values. If DB configuration changes later, capture governs (see §3).
- D-053 performed no live DB probe and opened no new DB connection; this repair rests on the
  durable Web evidence above. The optional exact two-statement reconfirmation was not
  exercised, so no secret was handled and no session state was touched.

## 2. What is superseded (narrow)

- ONLY the policy-v1 timezone/as-of capture semantics: the `evaluation_as_of_date.timezone`
  `Asia/Seoul` field and the explicit-date equivalence claim in `predicate.equivalence` and
  `d003_runtime_reference.note`. They are historical/superseded and must not be read as
  normative. No hardcoded future DB timezone expectation is set anywhere in policy-v2.
- Preserved exactly: gate purpose, allowed fields `(source, source_id, biz_end)`, predicate
  shape, null semantics, fail-closed behavior, internal-final-top-5 audit scope, exact
  denominators dev 180/900 + holdout 250/1250, truth table (zero => PASS / any intrusion =>
  NO-GO / missing => HOLD), claim boundary (D-003 parity only), youth-diagnostic non-gating
  note. Policy-v1 SHA256
  `3bcfc5b8360af28ccd7ea9018f3e3ffda73fba7744ba33bbfb83446235284608` is unchanged.
- D-015/D-016/D-017 historical text stays visible; D-052 history stays visible. D-053 amends
  capture semantics only, never sizes, provenance, or other contracts.

## 3. Corrected normative as-of contract (exact, machine-recomputable)

Normative detail lives in `production-exclusion-policy-v2.json`; this section is the frozen
human-readable record of the same contract:

- Gate id/name `production_exclusion`, safety claim boundary, allowed inputs, null rule,
  fail-closed conditions, audit scope, denominators, and truth table are unchanged from
  policy-v1.
- No normative assumption exists that the evaluation date is Asia/Seoul or any other
  hardcoded timezone. `db_session_timezone` is provenance, never a permanent expected value.
- At each protected evaluation session, BEFORE protected plaintext access and BEFORE
  `run_start`, on the exact DB connection context governing the pinned evaluation corpus and
  the paired D-003 baseline/candidate, execute exactly once for capture: `SHOW TimeZone` and
  `SELECT CURRENT_DATE`. Do NOT apply `SET TIME ZONE` or any timezone/session override for
  capture. This allowed capture inventory is exact: these two statements, no other SQL, no
  write, no protected data needed.
- Pin the returned values as `db_session_timezone` (as returned by the DB) and
  `evaluation_as_of_date` (`SELECT CURRENT_DATE`, canonical ISO `YYYY-MM-DD`) in
  corpus/evaluation provenance and audit. Missing/malformed/error => HOLD; never fall back
  to OS/user/local/UTC date.
- The captured `evaluation_as_of_date` is immutable for the entire run and shared by
  Candidate A and the paired D-003 baseline. The later bounded implementation must use the
  explicit pinned date for BOTH sides to avoid midnight drift, e.g.
  `(biz_end IS NULL OR biz_end >= :evaluation_as_of_date)` with audit
  `production_excluded = biz_end IS NOT NULL AND biz_end < evaluation_as_of_date`.
- The pinned predicate reproduces the D-003 decision exactly when the pinned date equals the
  governing connection's `CURRENT_DATE`, which capture guarantees by construction (same
  connection, no override, one shared date for the run).
- Claim boundary stays D-003 production-exclusion parity only; not universal expiration,
  user eligibility, or real-world active status.
- `biz_end == null` remains only `not_production_excluded_by_D003_predicate`, with explicit
  non-claims `not expired` / `eligible`.
- Youth structured evidence remains non-gating diagnostic only.
- Capture/query mechanics are later bounded implementation; D-053 freezes the contract only.
  This freeze stage sets no value and performs no DB query.

## 4. Frozen artifacts (old immutable, new append-only)

- Prereg `docs/RETRIEVAL_V3_PREREG.md` SHA256
  `7842018613d66aa4570f4db2f8ae5a698ceb46757995a6b7e26873177b36160e` — unchanged.
- `eval/retrieval-v3/candidate-plan/candidate-plan-v1.json` SHA256
  `2815361a469fee9bf69f6ffdf2124d19928220535cdb08b2005ae6674ae7d17c` — unchanged.
- `eval/retrieval-v3/candidate-plan/candidate-plan-v2.json` SHA256
  `d233f5c4d912e4d0856d89213d6392fbf44494f5538d018e7412f61781ae6cc6` — unchanged.
- `eval/retrieval-v3/candidate-plan/safe-action-policy-v1.json` SHA256
  `c512fb5627179697a987b05a2431b8f7e30d1153af2ff6dca37995f6b232a35d` — unchanged.
- `docs/RETRIEVAL_V3_SAFE_ACTION_SUPERSESSION_V1.md` SHA256
  `472b6183114a0ebf4d22e9b22c03bb9233b15a736587e29a917aa49113502364` — unchanged.
- `docs/RETRIEVAL_V3_ELIGIBILITY_EVIDENCE_V1.md` SHA256
  `eea3c5ce393f1f3c9563983df16f4648e9c005fd4f317b44cd168b082af91d32` — unchanged.
- `eval/retrieval-v3/candidate-plan/production-exclusion-policy-v1.json` SHA256
  `3bcfc5b8360af28ccd7ea9018f3e3ffda73fba7744ba33bbfb83446235284608` — unchanged
  (superseded on capture semantics only, §2).
- `docs/RETRIEVAL_V3_PRODUCTION_EXCLUSION_SUPERSESSION_V1.md` SHA256
  `63cdc4325b10c75cdb468ce775043c351ec22326642b70f0763189b846936fdc` — unchanged.
- `eval/retrieval-v3/candidate-plan/candidate-plan-v3.json` SHA256
  `665771f991a3891869f7d27658eedacbed28ba522afdcadcf8edd4d62b412681` — unchanged.
- NEW `eval/retrieval-v3/candidate-plan/production-exclusion-policy-v2.json` SHA256
  `6fee9ec22d5d3ac153ff19a6b1b5d27ab6a6a43bda11e35821d689f938968fe5` — the single
  frozen machine-readable normative contract (§3; normative detail lives in that file).
- NEW `eval/retrieval-v3/candidate-plan/candidate-plan-v4.json` — v3 values preserved except
  the authorized capture-semantics reference updates (§5); carries all parent SHAs including
  this document's. Hash circularity note: this document is written before plan-v4 so that
  plan-v4 can embed this document's hash in its parents; plan-v4's own hash therefore cannot
  be quoted here. It is pinned instead in the D-053 ledger entry and in
  `eval/test_retrieval_v3_production_exclusion_timezone_contract.py`, which recomputes and
  cross-checks every SHA in this section.
- NEW `eval/test_retrieval_v3_production_exclusion_timezone_contract.py` — pure/static proof:
  old-byte immutability, v3→v4 substantive identity with only the authorized capture diffs,
  policy-v2 capture contract (exact two-statement inventory, no override, shared pinned date,
  HOLD on missing/error, no normative timezone, no local-date fallback), predicate fixtures,
  denominator/truth-table proof, `eligible` absence from normative gate keys. No
  protected/DB/network/model/retrieval execution.

## 5. Candidate-plan-v4 mapping (v3 → v4)

- `plan_id` `retrieval-v3-candidate-plan-v3` → `retrieval-v3-candidate-plan-v4`, version
  `3.0.0` → `4.0.0`. v3 bytes untouched.
- Parents carry all identities: prereg SHA, plan-v1 SHA, plan-v2 SHA `d233f5c4…`, plan-v3 SHA
  `665771f9…`, safe-action policy SHA, production-exclusion policy-v2 SHA `6fee9ec2…`, and
  this document's SHA.
- `production_exclusion_policy` block: id/artifact/SHA ref `policy-v1` → `policy-v2`
  (`6fee9ec2…`), supersession artifact → this V2 doc; common-to-all-configs, not-a-tuning-axis,
  MAX24-untouched scope identical.
- `selection_rule.safety_gates_dev.production_exclusion_intrusion`: policy reference
  `production-exclusion-policy-v1` → `production-exclusion-policy-v2`; thresholds 0/180-tasks
  AND 0/900-slots, NO-GO/HOLD structure identical.
- `supersession`, `provenance`, `assertions`, `frozen_at` are D-053 stage-local (this repair,
  Muse Spark 1.3:xhigh lineage, durable Web evidence with no live DB probe and no
  DB/network/model/retrieval/protected execution in D-053).
- Plan-v4 makes no Asia/Seoul production-exclusion date-source claim; `GMT` appears, if at
  all, only as quoted Web evidence in stage-local provenance. Stage-local wall-clock stamps
  (`frozen_at`, `frozen_at_basis`) are artifact-authoring instants, not evaluation dates.
- Everything else — all 18 ranking tuples/order/semantics, dense+sparse/fusion/exact/
  final-pool/dedup/diversification semantics, D-003 baseline descriptor, embedding, MAX24,
  Candidate-B gate, headline >= 85% + Wilson/Clopper, unsupported/ambiguous integer gates,
  location, official-link/HTTP, latency/cost, audit/provenance/isolation/one-shot/rerun
  prevention, D-026 diagnostics, safe-action reference, gating-contract denominators,
  selection ordering — value-identical to v3.
- The change is a pre-result contract repair before any protected result, not result-driven
  relaxation: no protected result exists; nothing was tuned or relaxed against outcomes.

## 6. Verification (pure/static only, before commit)

- New focused timezone-contract tests plus the D-052 focused 17 plus the existing
  Retrieval-v3 10-file gate suite (216 PASS) still PASS; new total reported in D-053.
- `git diff --check` PASS; `ml-service` diff 0 vs
  `5327661445c37191a3fd61db195f3af4d2cf893a`; main dev/holdout/result/audit absent; one-shot
  unconsumed; all nine old SHAs unchanged.
- Intended files only: this doc, the policy-v2 JSON, plan-v4 JSON, the new test, D-053 ledger
  entry, session log. No runner/safety/registry/selection/schema/production change.

## 7. Change control for the frozen contract

- The predicate, allowed fields, denominators, truth table, capture connection/statements/
  timing/override-prohibition, pin/immutability/sharing, and fail-closed HOLD above are
  frozen. Any future change requires a new versioned policy artifact plus a new plan version
  and decision entry — never an edit to `production-exclusion-policy-v2.json` (or v1).
- The `evaluation_as_of_date` value itself is NOT frozen here; it is captured per evaluation
  session under the semantics in §3. The `db_session_timezone` value is likewise captured per
  session as provenance, never asserted in advance.

### VERDICT: FIRST protected-dev launch REMAINS BLOCKED (not authorized; do not launch)

This repair stage only corrects the as-of capture semantics to true D-003 parity before any
protected result. Implementation is unreviewed and no protected measurement exists.
Next gate after this record and its atomic commit/push is **STOP for Web read-only
independent review** (not bounded implementation, not FIRST dev retrieval, not candidate
tuning).
