# Retrieval v3 D-069 — Pre-Result Recovery Strategy (frozen)

Status: frozen pre-result strategy. Append-only. Does NOT change old prereg/candidate-plan/gates.
Scope: disposition after D-068 timeout. Authorizes a future independent dev-v2 strategy only.

## 1. D-068 history is immutable evidence

- D-068 protected dev SHA `2f014112f394541bb389a3db0aa1de7a1279b737ac8673d472ed351479fe7cd1` has a real canonical `run_start` and an open `protected_access_start` in `eval/retrieval-v3/audit/events.jsonl` (4 events, SHA `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`), with no `run_end`, no `protected_access_end` for `d068-repaired-dev-20260904-01`, and no canonical result.
- The same set can never rerun. No retry/resume/relaunch in any workspace. No synthetic audit closure is permitted (no manual append/close of the historical lifecycle).
- `events.jsonl` bytes are preserved exactly in D-069.

## 2. Holdout remains sealed and eligible

- Because D-068 produced no canonical result and post-timeout scoring/tuning/config/threshold changes were zero, the existing holdout remains sealed, unused, and eligible to remain the future final holdout.
- This stage does NOT access it (no access/materialize/read/hash/recover, no plaintext).

## 3. Continuing v3 requires a future fresh protected dev-v2 identity

- Not a retry/resume: new set SHA, new branch/tag identity, new session/run identity, canonical same audit chain preserving old open history.
- Proposed frozen names (may be used): branch `codex/retrieval-v3-dev-v2-freeze`, tag `retrieval-v3-dev-v2`.
- D-069 creates no dev-v2, launches no protected evaluation, and touches no holdout.

## 4. Fresh dev-v2 preserves the existing exact dev contract

- Total 180, headline 130, safety 50 = ambiguous 23 + unsupported 27, location-bearing 54.
- Standing exact strata/location/source-truth/annotation/isolation rules preserved.
- Same existing 18-config `candidate-plan-v4` and deterministic selection; no config addition/deletion/value change; no result-driven adaptation.

## 5. Fresh dev-v2 uses fingerprint-only zero-overlap checks

- Fingerprint-only zero-overlap checks against historical v3 dev-v1 and existing holdout and prior history, without reading old protected plaintext.
- Builder must be isolated from candidate code/results as standing freeze rules require.
- No `git show`/`cat-file`/`checkout`/`restore`/sparse/new worktree/path traversal for protected evalset plaintext.

## 6. Holdout considered only after valid dev-v2 result + review

- Existing holdout may be considered only after a valid fresh dev-v2 canonical result selects a finalist under standing gates, followed by a separate Web review/user approval.
- No holdout access now.

## 7. Dev-v2 one-shot rule

- If fresh dev-v2 later consumes `run_start` and again fails to produce a result, that dev-v2 set also becomes non-rerunnable; STOP for a new strategy decision rather than retry.

## 8. What D-069 does NOT change

- D-069 does NOT relax headline/safety/location/latency/cost/Candidate-B/MAX24/18-config/production-exclusion/link-provenance rules.
- D-069 does NOT supersede the frozen six (prereg, candidate-plan-v4, safe-action-policy-v1, production-exclusion-policy-v2, link-provenance-supersession-V2, cost-measurement-V1).
- It supersedes only the recovery/disposition after D-068 timeout by authorizing a future independent dev-v2 strategy.

## 9. D-069 runtime note (non-result, meaning-preserving)

- D-069 implements ONLY a non-timed scoring-phase runtime optimization that removes config-invariant recomputation (stripped query, query embedding/qvec, dense top100 + COSINE_MIN filtered pool, exact candidate discovery/order reused per task across 18 configs).
- Timed latency closures remain standalone full end-to-end calls; D-041 complete 18-config dev latency evidence requirement unchanged; selection/result-schema/latency methodology/gates unchanged.
