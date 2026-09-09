# Retrieval v3 D-162 — generation-v9r27 PRE-SMOKE WEB PASS

Date: 2026-09-09
Stage: fresh successor static/PRE-SMOKE construction + same-stage stale-provenance repair + independent Web FINAL PASS (static only)
Generation: `retrieval-v3-dev-generation-v9r27`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260910-v9r27`
D-161 closure base commit: `a7c368c96aea4eb925a299a4b771b5ce2f2edf80` (2026-09-09T14:57:59+00:00 / local 2026-09-09T23:57:59+09:00)

## Verdict

**D-162 / v9r27 PRE-SMOKE: WEB PASS for static/PRE-SMOKE only. NOT Smoke-A authorization.**

V9r27 is a fresh D-162 successor to immutable D-161/v9r26. It carries retrieval/evaluation semantics, rubric, counts/reserve/location quotas, A/B-all-360, C-every-360, agreement and exact selector unchanged with exactly the FIFTEEN failed-fingerprint exclusion sets (105 pairwise checks, overlap 0; no sixteenth because v9r26 produced zero Phase-C Author/query rows and zero Smoke-A coordinator/model output). The narrow D-161 repair is: frozen no-argument Smoke-A target runner (`run_smoke_a_once.py`) plus permanent non-model regression (`test_smoke_a_once_runner.py` 44); exact future command `python -B C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260910-v9r27\run_smoke_a_once.py` with no args, no path search, no `python -c`; exact future cwd `C:\Users\joji\bc-v3-v9r27-coord-smoke-20260910\cwd`; title `D163 v9r27 Smoke A`; correct keyword launcher binding (`staging_root`/`prompt`/`mode="smoke"`/`title`, exactly once). During Web review one real same-stage blocker was found and repaired by the same executor: `source_truth_snapshot.note` carried a stale future-looking v9r26 Phase-C/source-truth statement. Final bytes preserve v9r26 as historical predecessor only and attribute future separately gated one-shot Phase C/source-truth creation to v9r27; a regression was added to `test_freeze_binding_regression.py`. This was same D-162 PRE-SMOKE repair, not a new logical stage.

No v9r27 Smoke A/B, real freeze, source-truth snapshot, Phase C, Author/Reviewer/C generation role, selector, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append occurred in D-162.

STOP before Smoke A. A future fresh explicit user `진행해` is required for a separate D-163 Smoke-A stage.

## Reconciled base and environment

Immediately before durable D-162 closure:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `a7c368c96aea4eb925a299a4b771b5ce2f2edf80`
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing baseline = 0 (`git diff --name-only -- ml-service` empty)
- canonical `eval/retrieval-v3/audit/events.jsonl` 4 events / SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/dev-v2/`, `eval/retrieval-v3/holdout/` absent
- OMP `18.1.13` / Paseo `0.7.2` per standing D-160 evidence (exact CLI pinned in builder); no model/Paseo execution occurred in D-162

## D-161 reconciliation (immutable predecessor)

D-161 closes v9r26 permanently as `CONTRACT_INVALID_GENERATION / HARD HOLD / NON-RESUMABLE`. The authorized Smoke-A one-shot was consumed by actual tool use plus terminal stop (repo `Path.cwd().rglob` search raised `IndexError` before any coordinator import; raw terminality `CONSUMED_NO_RETRY`); no coordinator launched and no retry is permitted. Key v9r26 hashes reverified read-only unchanged in this stage; failure cwd `C:\Users\joji\bc-v3-v9r26-coord-smoke-20260909\cwd` exists and is empty (0 items). No v9r26 Phase-C Author/query rows and no Smoke-A coordinator/model output exist, hence no sixteenth exclusion set. Terminal v9r26 failure stays immutable/non-resumable/non-repairable.

## Final v9r27 identity and artifacts (static-verified)

- plan version `retrieval-v3-dev-generation-v9r27`, seed `benefit-compass-retrieval-v3-dev-v2-generation-v9r27-2026-09-10`
- candidate IDs `v3g9r27-001..360`, C opaque IDs `v9r27c-001..360`
- hold base D-161 `a7c368c96aea4eb925a299a4b771b5ce2f2edf80`, time `2026-09-09T14:57:59+00:00` / local `2026-09-09T23:57:59+09:00`
- `GENERATION_PLAN.json` 82447 bytes, SHA256 `f0caf41ea6c846f5176b8e641be08c638e62ac97c67ff221e5b35b88d0ab1a0e`
- `RUBRIC.json` 3334 bytes, SHA256 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- `input/EXCLUSION_INPUTS.json` 4766 bytes, SHA256 `5c247121fce5c4726cc571f6527c6bb7a4624b999aa73a913c6cc771a3f78c64`
- `freeze_plan_v9r27.py` 119597 bytes, SHA256 `53c0354756d20ab238289aaa9a14c7f638e90baa104ab0e1a27f69f3b7f85a72`
- `carry_exclusions_v9r27.py` 9529 bytes, SHA256 `50a8b6a799e5d8a0542c1f4097e142c2d6e354b1ab760f69e0c06aaf4f887419`
- `run_smoke_a_once.py` 2259 bytes, SHA256 `23c1f86de4ead0bdd9ee687860100b6200e1694a778ba6f8c4fbf67b4e0516a8`
- `test_smoke_a_once_runner.py` 7180 bytes, SHA256 `d9918aee85c32306573baedc56628284a9af883673a2de055b51ce2b014f08de`
- `test_freeze_binding_regression.py` 21638 bytes, SHA256 `0ff87cca692f9dd668087af2bcc7e044d94699647f4333eec696892f8e400900`
- `GENERATION_PLAN.author_isolation.mechanics_shas` 69/69 exact disk bytes/SHA (.NET direct hashing), missing 0, mismatch 0
- exact query exclusion sets 15 (FIFTEEN inputs byte-identical lineage; v9r26 contributed zero rows); pairwise comparisons 105; overlap 0; gold exclusions stay dev-v1/holdout/history only
- old-token provenance deny lists include v9r26 in every family (v9r26, v3g9r26, v9r26c, 20260909-v9r26, bc-v9r26, bc-v3-v9r26, bc-v3-dev-v2-builder-20260909-v9r26)

## D-161 repair contract (frozen)

- Runner is invoked only as the exact target process `python -B C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260910-v9r27\run_smoke_a_once.py` with NO args and no `python -c` / dynamic code / path search.
- Runner imports `launch_phasec_coordinator` from its own builder by ordinary same-directory import only.
- Exact runtime cwd is `C:\Users\joji\bc-v3-v9r27-coord-smoke-20260910\cwd`, created brand-new with `exist_ok=False` before launch; existing root/cwd fails closed and is never deleted/recreated.
- Exactly one `launch_coordinator` call with keyword binding `staging_root=<exact cwd>`, `prompt=<neutral>`, `mode="smoke"`, `title="D163 v9r27 Smoke A"`.
- Neutral prompt requires `phasec_probe` exactly once with `{}`, forbids `phasec_execute`, then stop; `todo` only if needed. Coordinator semantics otherwise preserved.
- No audit/wait/hash/cleanup/retry/correction/post-helper in the runner. Structured launch result only; any exception/nonzero is terminal.
- Plan-bound one-shot execution contract freezes the exact command string: the future executor must issue exactly one Shell tool call running exactly that command and nothing else. Existing raw-OMP terminality/consumption contract is unchanged.

## Sole implementation executor

Approved private-builder implementation and all same-stage repairs were performed end-to-end by the sole D-162 executor `90908d7c-5ddb-4088-83be-bb6218ac5029`. No second implementation executor or semantic generation role was created or delegated.

## Repair history (same-stage, fail-closed)

Web review found one real blocker: `GENERATION_PLAN.source_truth_snapshot.note` (as constructed in `freeze_plan_v9r27.py`) left a stale future-current statement equivalent to "v9r26 source truth is not read in its freeze and will be created only by a later separately gated one-shot Phase C" — wrong because v9r26 is permanently NON-RESUMABLE after D-161. The same executor narrowly edited `freeze_plan_v9r27.py` so the generated note preserves historical v9r26 facts but the operative future statement says v9r27 source truth will be created only by a later separately gated one-shot Phase C; tightened `test_freeze_binding_regression.py` current-identity coverage so it FAILS on any future-looking v9r26 Phase-C/source-truth statement and PASSES only when the future statement belongs to v9r27; regenerated `GENERATION_PLAN.json` and `input/EXCLUSION_INPUTS.json` deterministically on disposable copies only and repinned `mechanics_shas` to exact final bytes. Final note verified: stale future-v9r26 count 0, future-v9r27 count 1, v9r26 D-161 history present. This was same-stage D-162 PRE-SMOKE repair, not a new logical stage.

Final battery on final bytes (disposable fixtures only for freeze): syntax compile 51; D149 carry 358 unique / 360 source / 2 duplicate groups; D150 retryable 7; D156 reviewer retryable 9; FIFTEEN 15 sets / 105 pairs / 0 overlaps; FREEZE_BINDING 91; FREEZE_RERUN 66 including race and timestamp rejection; REACHABILITY 87; LIFECYCLE 53; one-shot terminality 24/24; SMOKE_ONCE_RUNNER 44; PASEO_CLI 64; CONFINEMENT 251; REGISTRY_SCAN 37; GATE PASS; ROLE_TOOLS 250; PREFLIGHT 36; slot/location 6 positive / 5 negative; STAGING_EXACT_SET 41. All rc0 with no Smoke A/B, real freeze, source snapshot, semantic roles, Phase C, selector, protected eval, audit append, or production.

Web independent final-byte static review on the exact final bytes above: ALL PASS with identical counts (binding 91, rerun 66, mechanics 69/69, stale-future-v9r26 false, correct future-v9r27 true).

Web's Python independent regressions recreated exactly 2 v9r27-local `__pycache__` dirs / 51 pyc (49 + 2). The same D-162 executor verified each resolved path inside the v9r27 builder, removed ONLY those two exact dirs, ran no Python builder tests afterward, rehashed all seven key files unchanged via .NET direct hashing, and verified final cache0/pyc0. This is review-test hygiene, not a source/mechanics defect.

Final v9r27 zero-state after cleanup: cache dirs 0 / pyc 0; PLAN_LOCK / FROZEN_HASHES / source_truth (+meta) / anchors / slots / authors / `candidates_merged` / run lock / `out` / `sealed` / `evidence` absent. No Smoke-A root/model smoke, real freeze, source snapshot, Phase C, semantic Author/Reviewer/C, selector, protected evaluation, holdout, production, or audit append occurred.

STOP. No Smoke A/B, real freeze, source truth, Phase C, semantic generation, protected eval, holdout, audit append, or production change in D-162.

## D-162 WEB FINAL PASS

Independent Web FINAL VERDICT is D-162 / v9r27 PRE-SMOKE WEB PASS on the exact final bytes above. **WEB PASS covers static/PRE-SMOKE only. NOT Smoke-A authorization. STOP before Smoke A.**
