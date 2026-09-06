# Retrieval v3 D-118 — generation-v9r18 PRE-SMOKE Web PASS

Date: 2026-09-07
Stage: fresh successor construction + independent final-byte PRE-SMOKE review
Generation: `retrieval-v3-dev-generation-v9r18`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260907-v9r18`

## Verdict

**v9r18 PRE-SMOKE: PASS.** v9r18 is a fresh successor after D-117 closed v9r17 `CONTRACT_INVALID_GENERATION`. The D-117 repair is mechanical and bounded: Reviewer-A/B and C packet builders no longer stage obsolete `search_snapshot.py`; the frozen driver exact prepared-root allowlists remain narrow and unchanged. A permanent synthetic exact-set regression now executes both packet builders and proves the produced reviewer/C roots equal the production driver contract and reject extra/missing files.

No v9r18 model smoke, real freeze, Phase C, source-truth snapshot, semantic role, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append occurred in D-118.

## Reconciled base / predecessor preservation

Before final review, branch `codex/retrieval-v3-user-search-quality` was clean at D-117 commit `ecd2893d9e97ae3aca94e454b6ba36da747a6990`, with local/upstream/direct remote equal, production `ml-service/` diff zero, and canonical audit exactly 4 events SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`.

OMP remains 18.1.5 with effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`; bundled Paseo CLI/daemon is the standing 0.7.2 path and was reachable during pre-smoke review.

v9r17 remains immutable failure evidence. Its D-117 runtime is not resumed or repaired. v9r17 candidate/query rows are not reused as semantic templates.

## D-117 staging exact-set repair

The frozen v9r17 failure was a producer/consumer mismatch: `build_packets_ab.py` staged `search_snapshot.py` even though the frozen plan/driver requires Reviewer roots to contain only `packet.jsonl`, `RUBRIC.json`, `source_truth.jsonl`, `reviewer_brief.md`, and empty `out/`. Independent review also found the same latent mismatch in the unreached C builder.

v9r18 therefore changes only the staging producer side:
- `build_packets_ab.py` no longer stages `search_snapshot.py`.
- `build_packets_c.py` no longer stages `search_snapshot.py`.
- production driver exact-set allowlists are not widened.
- `test_staging_exact_set.py` permanently exercises A/B and C packet builders against the production prepared-root gate; final result `STAGING_EXACT_SET_PASS`, 24 checks.

This does not change packet ordering, opaque-ID mapping, annotation rubric/semantics, counts, A/B/C authority, selector, retrieval candidate plan, role tool confinement, or evaluation gates.

## Freshness exclusion disposition — D-117 fingerprint-only 11th set

Final Web disposition is that the complete D-117 360-row mechanically validated merged pool is eligible only for one-way query-fingerprint freshness exclusion, never semantic/template reuse. This follows the controlling D-087 precedent: after D-086 `CONTRACT_INVALID_GENERATION` produced a complete 360-query pool, the fresh successor mechanically added those normalized SHA256 query fingerprints as the then-tenth exclusion while leaving gold exclusions unchanged. D-092 `same-TEN` describes that generation's operative set; it is not a permanent numeric ceiling. D-110/v9r15 is not analogous because it stopped with only one Author's partial 180-row output and was durably treated as zero reusable candidate/query rows.

Accordingly v9r18 has exactly ELEVEN query-fingerprint sets: existing ten plus D-117. D-117 input is hash-only and bound to the failed merged-pool artifact:
- `input/failed_d117_query_fingerprints.json` SHA256 `fc681a835e41b85317eb257250d47b3b74ec201d218dfef561ae91db625ab5e4`
- query count / unique count 360
- source artifact SHA256 `96c31fe332faf2cc098f8d01e079d97f3f7ab01c74ab28aa0e8e7e812617c26d`
- no labels/golds/mappings/semantic row reuse
- gold exclusions remain exactly canonical dev-v1 / holdout / history.

Final `test_eleven_set_gates.py` proves 11 operative query sets, 55 pairwise comparisons, overlap 0, with D082/D086/D117 probes binding to their intended sets.

## D-112 lineage correction during pre-smoke review

An initial v9r18 draft overstated the cause of the historical D-112 Smoke-B terminal failure. Before any v9r18 smoke/freeze, the same implementation executor corrected the lineage to the canonical D-112 evidence only: after exactly one Smoke-B launch, the local Paseo daemon connection failed during early `verify_top_level`/inspect; after daemon recovery solely for evidence read, the agent was closed, final `stopReason` was `aborted`, and the frozen lifecycle auditor returned rc3. Unsupported claims of an intentional/graceful shutdown were removed. No v9r18 execution semantics changed.

## Independent final-byte validation

Final Web rerun on the post-correction bytes:
- D-117 staging exact set: `STAGING_EXACT_SET_PASS` — 24 checks
- ELEVEN freshness gates: 55 pairwise comparisons, overlap 0; counts `180/250/248/273/273/360/360/365/360/360/360`
- bundled Paseo CLI gate: `PASEO_CLI_GATE_PASS` — 64 checks
- D-110 writer preflight: `PREFLIGHT_PASS` — 36 checks
- launcher reachability: `REACHABILITY_PASS` — 87 checks
- lifecycle contract: `LIFECYCLE_CONTRACT_PASS` — 53 checks
- role tools: `ROLE_TESTS_PASS` — 171 checks
- role completion: `GATE_TESTS_PASS`
- Phase-C confinement: `CONFINEMENT_TESTS_PASS` — 210 checks
- freeze-binding regression: `FREEZE_BINDING_PASS` — 66 checks
- generation-plan mechanics map: 56/56 exact, mismatch 0
- Python compileall PASS
- Bun role-tool probe PASS
- Bun coordinator probe PASS
- TypeScript `tsc --noEmit` PASS.

The real builder ends at 70 source/support files, cache 0, and none of `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, source truth/meta, anchors/slots, candidates, `evalset.jsonl`, or `out/` exists.

## Final key SHA256

- `GENERATION_PLAN.json` `df11b9454039ec369c936204197a345847e8077f284319901f0b10b57d7d0667`
- `input/EXCLUSION_INPUTS.json` `168105ac49d357f4c05d4ac999b0d01aaa60b6db5c9c88b91cb0374503a72f44`
- `input/failed_d117_query_fingerprints.json` `fc681a835e41b85317eb257250d47b3b74ec201d218dfef561ae91db625ab5e4`
- `freeze_plan_v9r18.py` `f0a3bd4d2add0d52e9bd15a7718d6b7cae3e02799d08c81ec26ae45ae6ce1c79`
- `carry_exclusions_v9r18.py` `e267a893f56e5dd9cf5dceb44a590880f8a479fd8f08f434c1f8b87c44b2e04b`
- `test_eleven_set_gates.py` `965d653e8cd61f18729c6947b81651cf571efc48eaa10ce364a5f7e8f1a70b4a`
- `test_staging_exact_set.py` `96065b202ee7a8291728aedbbbb91c30ac0c3985e6200e7d00a64f8348dce4ea`
- `build_packets_ab.py` `48e15e6ac64d17f94c9dc1de47ab804d938b07312a2705ad2c1bfe84f44d5a32`
- `build_packets_c.py` `1aba214d747d6aa4f263b47f6d6c6f4f3da0eaca912d0aa1041448854155f0c1`
- `RUBRIC.json` `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`

Single v9r18 implementation executor OMP session: `C:\Users\joji\.omp\agent\sessions\-Documents-programming\2026-09-06T19-08-22-606Z_01a0781f-26ce-740e-b1eb-f28bdff3556a.jsonl`; final observed 1225 lines, SHA256 `4cf6377fff92c8d5196d1a6791eaf14dcc12d7eeb418b71fed0b9161ed8d5e34`, model `opencode-go/muse-spark-1.3-contributor`, fallback false. Same session handled the same PRE-SMOKE blocker corrections; no second implementation executor modified the builder.

## Final boundary / next gate

No v9r18 Smoke-A/B staging root/session or matching Paseo agent exists at final review time.

**NEXT:** exactly one v9r18 Smoke A on these exact final bytes, only after a final duplicate/prelaunch transport gate. Only if its frozen auditor returns a stable PASS may exactly one v9r18 Smoke B run. Any smoke failure closes v9r18 with no retry/same-generation repair. Real freeze and Phase C remain forbidden until both one-shot smokes pass and later gates authorize them.
