# Retrieval v3 D-164 — generation-v9r28 PRE-SMOKE WEB PASS

Date: 2026-09-10 (KST)
Stage: fresh-successor private-builder construction + same-stage current-provenance correction + independent Web final-byte PRE-SMOKE review
Generation: `retrieval-v3-dev-generation-v9r28`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260910-v9r28`
D-163 closure base commit: `80b8d27c35d9976cbf74336aa9f5bfebbff81aa7` (`2026-09-09T17:07:45+00:00`)

## Verdict

**D-164 / v9r28 PRE-SMOKE: FINAL WEB PASS for static/PRE-SMOKE only. NOT Smoke-A authorization. STOP before Smoke A.**

V9r28 is a fresh D-164 successor to immutable terminal D-163/v9r27. D-163 remains `CONTRACT_INVALID_GENERATION / HARD HOLD / NON-RESUMABLE`: its single authorized Smoke-A shell use interpreted the backslash Windows script path as a POSIX-style `//C:\...` path and returned rc2 before Python opened the runner. Therefore v9r27 produced zero Phase-C Author/query rows and zero Smoke-A coordinator/model output. Exactly the existing FIFTEEN query-fingerprint exclusion sets carry forward; there is no sixteenth set.

The D-164 repair is narrow and mechanical: change the future executor-shell transport from the failed backslash form to the exact forward-slash `C:/` absolute script path, and repin current generation identity/provenance from v9r27 to v9r28. Retrieval/evaluation semantics, rubric, quotas/reserve/location, A/B-all-360, C-every-360, agreement/selector, failed-generation freshness semantics, protected-data boundaries, and one-shot terminality remain unchanged.

No v9r28 Smoke A/B, real freeze, source-truth snapshot, Phase C, semantic Author/Reviewer/C role, selector, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append occurred in D-164.

## Reconciled repo base before durable record

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin = `80b8d27c35d9976cbf74336aa9f5bfebbff81aa7`
- working tree clean
- production `ml-service/` diff from standing baseline = 0
- canonical `eval/retrieval-v3/audit/events.jsonl` remains 4 events, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`; no D-164 audit append
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/dev-v2/`, `eval/retrieval-v3/holdout/` absent
- immutable v9r27 predecessor key verification: 8/8 exact
- final v9r28 state before durable record: no runtime/freeze/source artifacts; cache0/pyc0

## Fresh v9r28 identity and final hashes

- plan version `retrieval-v3-dev-generation-v9r28`
- seed `benefit-compass-retrieval-v3-dev-v2-generation-v9r28-2026-09-10`
- candidate IDs `v3g9r28-001..360`; C opaque IDs `v9r28c-001..360`
- hold base D-163 commit `80b8d27c35d9976cbf74336aa9f5bfebbff81aa7`, hold time `2026-09-09T17:07:45+00:00`
- `GENERATION_PLAN.json` SHA256 `bd3cb2312c4cd72b6fa5e99e36112d1c2f41fc83e98b96d642defd8d6f471811`
- `RUBRIC.json` SHA256 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- `input/EXCLUSION_INPUTS.json` SHA256 `0ed656a3cf5e4fd2b65b67f67270f8d17c8344908aa7891bd2383ffd65142438`
- `freeze_plan_v9r28.py` SHA256 `7fa795804b4f11eeda7e72a65ef46b920e06903d10b5e7abf9c0a4a394efbc78`
- `carry_exclusions_v9r28.py` SHA256 `0cabc3c478d348a03b531e63458b6a225452f4e4b39a23ec158345ce937028dc`
- `run_smoke_a_once.py` SHA256 `9a2b9682886ecc6502ba369ee5cad0d942b5e3c44bc38e2e7458303ffba0fdbf`
- `test_smoke_a_once_runner.py` SHA256 `32fada728e02fbec6dc3027f6ae1302ad4764020b756bfbc6a19ebdafd06feba`
- `test_freeze_binding_regression.py` SHA256 `47c13b95721ab15e4dc2a6d085b43b457da20f040130cafef7a63d356df11476`
- `GENERATION_PLAN.author_isolation.mechanics_shas`: 69/69 exact disk bytes, missing 0, mismatch 0
- freshness exclusions: FIFTEEN sets, 105 pairwise comparisons, overlap 0; no sixteenth set

## Narrow D-163 executor-transport repair

The future D-165 Smoke-A target is frozen to exactly:

`python -B C:/Users/joji/Documents/programming/bc-v3-dev-v2-builder-20260910-v9r28/run_smoke_a_once.py`

- exact title: `D165 v9r28 Smoke A`
- exact runtime cwd/root: `C:\Users\joji\bc-v3-v9r28-coord-smoke-20260910\cwd`
- runner remains same-directory-import only and performs exactly one keyword `launch_coordinator` call under the standing one-shot contract
- permanent runner regression pins the exact forward-slash `C:/` command and rejects the failed backslash command form
- a harmless non-runtime executor-shell transport proof used the same `python -B C:/Users/...` prefix against a disposable non-runtime probe and returned rc0; no Smoke runner/model/runtime was invoked

**The D-165 command/title/root above were NOT executed in D-164.** They are future frozen targets only.

## Same-stage Web-found current-provenance blocker and repair

The first implementation completion report was invalidated by Web's reread of the actual bytes. `freeze_plan_v9r28.py` still contained stale *operative current* provenance naming v9r26 and D-161/D-162 as the current delta/base, including stale D-161 hold-base wording, stale `IDENTICAL to v9r26` wording, a no-sixteenth clause attributed to v9r26, and a runner delta attributed to D-161 command-composition/reachability. Historical D-161/D-162 notes were allowed, but these operative current statements made D-164 a HARD HOLD at that point.

The same D-164 executor repaired only those current-provenance lines to the truthful D-164-after-D-163 state: hold commit `80b8d27...`, v9r27 zero-row/zero-Smoke-output no-sixteenth basis, D-163 backslash-to-`C:/` executor transport repair, and v9r27-to-v9r28 identity repin. `test_freeze_binding_regression.py` gained source-text assertions requiring the exact stale current phrases to be absent and the D-164/D-163 phrases to be present. Canonical plan/manifest were regenerated on disposable copies, mechanics were repinned, and the full required battery was rerun. Web then independently reviewed the corrected bytes and returned FINAL PRE-SMOKE PASS with blockers none.

## Final executor validation on corrected bytes

All checks below were non-model/static/disposable where applicable:

- syntax compile: 51 files
- D149 carry: 358 unique / 360 source rows / 2 duplicate groups
- D150 retryable: 7
- D156 reviewer-resource retryable: 9
- FIFTEEN: 15 sets / 105 pairs / overlap 0
- freeze binding: 105
- freeze rerun rejection: 66
- reachability: 87
- lifecycle: 53
- one-shot terminality: 24/24
- Smoke-once runner regression: 47
- Paseo CLI gate: 64
- confinement: 251
- registry scan: 37
- completion/gate suite: PASS
- role tools: 250
- preflight: 36
- slot/location: 6 positive / 5 negative
- staging exact set: 41
- mechanics: 69/69 exact
- deterministic disposable plan/manifest reproduction: identical
- non-runtime exact-`C:/` shell transport proof: rc0

## Independent Web validation and cache hygiene

Web independently reran corrected final-byte checks and PASSed: runner 47, binding 105, FIFTEEN 15/105/0, one-shot 24/24, CLI 64, confinement 251, staging 41. The final independent reviewer then returned **`FINAL PRE-SMOKE PASS`**, blockers none.

Those Web Python imports created exactly two builder-local `__pycache__` directories containing 51 `.pyc` files: the v9r28 builder-root cache and `coord_wrapper_tpl\__pycache__`. The same D-164 executor deleted only those exact cache directories. After cleanup, verification used PowerShell/.NET only — **no Python was run after cleanup** — and proved cache0/pyc0, all key hashes above unchanged, mechanics 69/69 exact, no v9r28 Smoke runtime root, and no runtime/freeze/source artifacts.

## Final boundary

**D-164 PRE-SMOKE WEB PASS ONLY; NOT Smoke-A authorization. STOP before Smoke A.**

A next, separately and explicitly authorized user continuation may authorize only a fresh D-165 Smoke-A prelaunch gate and, if that gate still passes on these exact final bytes, exactly one execution of the frozen D-165 command above. Smoke B, real freeze, source truth, Phase C, semantic generation roles, protected dev-v2, holdout, production, and canonical audit append remain prohibited until their own later explicit gates.
