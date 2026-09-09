# Retrieval v3 D-150 — generation-v9r24 PRE-SMOKE Web PASS

Date: 2026-09-09
Stage: fresh successor PRE-SMOKE construction + same-stage mechanical repairs + independent Web review (FINAL PASS)
Generation: `retrieval-v3-dev-generation-v9r24`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260909-v9r24`
D-149 closure base commit: `56c9138ef9a1ad3db2d0dfa949d5d31764cf5d61`

## Verdict

**D-150 / v9r24 PRE-SMOKE: WEB PASS for static/PRE-SMOKE only. NOT Smoke-A authorization.**

V9r24 is a fresh D-150 successor to immutable D-149/v9r23. It makes only the narrow mechanical repairs proven by the consumed v9r23 Phase-C failure: (1) carry v9r23's complete failed 360-row Author pool forward only as 358 unique normalized SHA256 query fingerprints under the standing D-087 precedent, (2) retryable pre-write rejection of the four author-correctable failure classes with no post-final repair, and (3) a coordinator-owned hidden hash-only Author-1 reservation staged only to Author-2 for cross-author uniqueness. Retrieval/evaluation semantics, rubric, quotas, A/B/C semantics, selector algorithm, canonical gold exclusions, D141 C 12x30, D143 no-literal-staging-path, D144 resource parity, D135 timestamp/O_EXCL mechanics, and protected-data boundaries remain unchanged.

No v9r24 Smoke A/B, real freeze, source-truth snapshot, Phase C, Author/Reviewer/C generation role, selector, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append occurred in D-150.

STOP before Smoke A. A future fresh explicit user `진행해` is required for a separate Smoke-A prelaunch/execution stage.

## Reconciled base and environment

Immediately before durable D-150 closure:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `56c9138ef9a1ad3db2d0dfa949d5d31764cf5d61`
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- canonical `eval/retrieval-v3/audit/events.jsonl` 4 events SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/dev-v2/`, `eval/retrieval-v3/holdout/` absent
- OMP `18.1.13` verified; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`, slow/expert `openai-codex/gpt-5.6-sol:high`, smol `openai-codex/gpt-5.6-luna:high`, task luna:xhigh, review luna:max, prewalk disabled, memory off, maxConcurrency 4
- bundled Paseo `0.7.2` per standing evidence (exact CLI pinned in builder)

## D-149 reconciliation (stale handoff correction)

Durable D-149 closure and current v9r23 local bytes agree; the previously observed discrepancy was stale handoff metadata, not mutation. Canonical v9r23 evidence hashes re-verified in this stage:

- PLAN_LOCK `b8c1fa42e23c3ef085b30e54fd08a5e68d8895219328e4415764caf574468c3f`
- FROZEN_HASHES `bda5f88c3d89d60ff79c38144fafa300139f41a55ff6182ad1231a44fb18aeb2`
- run lock `6f8ff2f719fa3d117ed51e95f81edd639aaa9eb35ddf26c996010c21add47db2`
- source_truth.jsonl `9fe194653a4b5c9c688364aa9ae686996cb7cabfebd446a6b9a7e8895374c1a5`
- source_truth_meta.json `9f6a3a99f8c9060072f390871d30e7be4550245a19a4e015a68c3e3b4f089189`
- anchors.json `38ef33e8e90317e6b57bd6a44edecb303c6e132ca420b5c6e34291ecca414485`
- slots_1.json `64172dae13a8af7ba278a87bf811b58e67de8477d1208ee7119ca253cfeaba43`
- slots_2.json `baa2ce070bc28c4ad47ee79410def1d8dd89e0987a107d1f59599a0b526c0222`
- author1_candidates.jsonl `8f217b6ebd78de9beccdf903ba0a6e613b1e1c86acb957f9aa6060f71ff10d81`
- author2_candidates.jsonl `4326625e8453646a6253433f4aa3f368d41116178f108f129a60c029593ecdbd`

Terminal v9r23 failure stays immutable/non-resumable/non-repairable.

## Final v9r24 identity and artifacts (Web-verified)

- plan version `retrieval-v3-dev-generation-v9r24`, seed `benefit-compass-retrieval-v3-dev-v2-generation-v9r24-2026-09-09`
- `GENERATION_PLAN.json` 73,596 bytes, SHA256 `ce6b55d1044e79d95543119ce2aa916575ba56da4c59639c96d36e9a5f832c05`
- `RUBRIC.json` 3,334 bytes, SHA256 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- `input/failed_d149_query_fingerprints.json` SHA256 `e6c5beea530c2d7e740823a12c78be1b64005afcd0b6f661cbfde9028739bcea`: 358 unique hashes from source_rows 360, duplicate_groups 2, bound source SHAs above, zero overlap vs earlier 13 sets, no failed-generation gold
- exact query exclusion sets 14; pairwise comparisons 91; overlap 0; positive D149 gate proven
- `mechanics_shas` count 63, exact bytes/SHA parity PASS against final builder files

## D-150 author behavior (operative)

- Sequential Author-1 -> stable final + audits PASS -> accepted chunks copied -> coordinator builds hidden hash-only reservation of exactly 180 unique normalized query SHA256s (no plaintext, no Author-1 IDs/semantic rows) -> staged ONLY to Author-2, never via `role_read_resource` -> Author-2 pre-write cross-author uniqueness.
- ONLY four author-correctable pre-write failures are retryable no-write in the same author session before final DONE: `slot_stratum_mismatch`, `slot_location_mismatch`, `constraints_lt2`, `duplicate_query_fp`. Retry log semantics: `allowed:true`, outcome `REJECT_RETRYABLE`, effect `no_write`, IDs + stable codes only, no query/ledger plaintext.
- Fatal DENY/security/provenance/path/envelope/ID-order failures remain fatal. No post-final coordinator repair/send/resume. Final `validate_pool.py` nonzero is terminal `CONTRACT_INVALID_GENERATION`.

## Repair history

- Initial D-150 construction passed the static battery; independent Web exact-byte review found plan/runtime drift (stale `paseo send` repair text, Author-2 reservation missing from plan staging text, stale THIRTEEN/D-141 counts in current-mechanics descriptions). Same executor repaired, regenerated the unfrozen plan via the safe disposable-copy mechanism, and re-ran the battery.
- Second Web review caught two remaining operative drifts (`generation_authors.contract` vs rule 2, freeze top summary). Same executor repaired, extended the narrow D150 assertions to both plan locations plus the freeze summary, rebound the plan, and re-ran the battery to full PASS.
- Final Web review: FINAL PRE-SMOKE PASS. Battery on final bytes (disposable fixtures only): compile 45 files; D149_CARRY (358/360/2); fourteen 14/91/0 + D149 probe + plan/runtime regression assertions; D150_RETRYABLE checks7; ROLE_TOOLS checks221; PREFLIGHT checks36; completion gate; CONFINEMENT checks251; REACHABILITY checks87; CLI_GATE checks64; REGISTRY_SCAN checks37; STAGING_EXACT checks41; FREEZE_BINDING checks87; FREEZE_RERUN checks66; LIFECYCLE checks53. All rc0/PASS with no real freeze/model/Paseo semantic launch.
- Static tests created builder-local caches (2 dirs/45 pyc); the same D-150 executor removed ONLY exact v9r24 caches. Final cache0/pyc0, plan SHA unchanged, live one-shot zero-state intact (no PLAN_LOCK/FROZEN/runlock/source truth/meta/anchors/slots/candidates).

## Sole implementation executor

Approved private-builder implementation and all same-stage repairs were performed end-to-end by one stage-machinery executor: `c4fef7ce-6b72-4418-b341-f8d28e07b66a` (D-150 v9r24 successor PRE-SMOKE executor). No second executor or generation role was launched.

STOP. No Smoke A/B, real freeze, source truth, Phase C, semantic generation, protected eval, holdout, audit append, or production change in D-150.
