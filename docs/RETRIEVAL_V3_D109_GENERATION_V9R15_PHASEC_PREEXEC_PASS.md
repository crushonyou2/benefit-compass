# Retrieval v3 D-109 — generation-v9r15 Phase-C PRE-EXECUTION PASS

Date: 2026-09-07
Stage: post-freeze independent Web pre-execution gate
Generation: `retrieval-v3-dev-generation-v9r15`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260907-v9r15`

## Verdict

**v9r15 PHASE-C PRE-EXECUTION GATE: PASS.** D-108 real-freeze artifacts and D-107 one-shot Smoke A/B proofs remain exact. No Phase-C/source-truth/semantic-role artifact or execute coordinator exists. The frozen execute path is mechanically reachable on the current machine. Exactly one execute coordinator may now be launched through frozen `launch_phasec_coordinator.py` in `execute` mode; no alternate launcher or retry is authorized.

## Reconciled canonical state

- branch `codex/retrieval-v3-user-search-quality`
- HEAD/local/upstream/direct remote `8ba67471e35e862245aff19ff98ec30102fb9da2` (D-108)
- working tree clean before this record; `git diff --check` PASS
- production `ml-service/` diff from `5327661445c37191a3fd61db195f3af4d2cf893a`: 0
- canonical audit: 4 events, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- OMP `18.1.5`; default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`

## Freeze verification

- `PLAN_LOCK.json` SHA256 `8c94ff00e5f4833e645472da1f176bf9c0792f57dac39a31a99751d5b5fb8d70`
- `FROZEN_HASHES.json` SHA256 `e9e9df7ac1f2452b663541961497e7f554bb5f0fd3b9403372aee89e94c97df7`
- `GENERATION_PLAN.json` SHA256 `83307b659b53b4340aecc68b259de63c311288b0f6fa7064dfe3799c1b02f6e3`
- frozen entries independently rehashed: 67; mismatches 0
- builder files: 68 = 66 source/support + PLAN_LOCK + FROZEN_HASHES; Python cache 0
- `phasec_driver.run.lock`, `source_truth.jsonl`, `source_truth_meta.json`, `evalset.jsonl`, builder `out/`: all absent

## Execute-path review

Frozen `phasec_coordinator_ext.ts` in execute mode exposes only `todo` + `phasec_execute`; `phasec_execute` takes an empty-object schema and spawns exactly one fixed Python interpreter plus frozen `coord_wrapper_tpl/phasec_driver.py`. The driver verifies frozen hashes first, then atomically creates `phasec_driver.run.lock`; rerun is forbidden. It next requires all runtime artifacts absent and a fresh Phase-C root before the single source snapshot.

The source snapshot procedure is read-only against the `policy` table only, `ORDER BY source,source_id`, with no vector/chunk/ranking query and no database writes. `DATABASE_URL` is present as a configured key without exposing its value, and `psycopg2` imports successfully.

Current machine prerequisites:
- frozen fixed Paseo command `C:\Users\joji\AppData\Local\Programs\Paseo\resources\bin\paseo.cmd`: present
- installed Paseo executable: present
- frozen Python interpreter path: covered by the already-frozen execute extension and current Python 3.11 environment
- `C:\Users\joji\bc-v3-v9r15-phaseC`: absent
- planned execute coordinator staging `C:\Users\joji\bc-v3-v9r15-coord-execute-20260907\cwd`: absent
- expected execute OMP session directory: absent
- current Paseo agents matching v9r15 execute/Phase-C cwd: 0

This duplicate-prevention check is load-bearing: no execute launch has already been consumed by another path.

## Authorized next action

Launch exactly one neutral top-level execute coordinator via the frozen launcher in a brand-new empty `C:\Users\joji\bc-v3-v9r15-coord-execute-20260907\cwd`, model Muse Spark 1.3 contributor xhigh/full, `BC_PHASEC_MODE=execute`, `PYTHONUTF8=1`. Prompt: invoke `phasec_execute` exactly once with empty input; no other tool except optional `todo`; no arbitrary access; report the resulting status and stop.

After launch, verify Parent null, exact cwd/model/fallback=false, exact-one wrapper invocation, and then let the frozen driver own the entire logical execution end-to-end. Do not manually run snapshot/helpers/semantic roles outside that driver. Any frozen contract failure closes v9r15; do not retry or patch same-generation.
