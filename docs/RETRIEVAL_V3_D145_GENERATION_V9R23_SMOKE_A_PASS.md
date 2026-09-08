# Retrieval v3 D-145 — generation-v9r23 one-shot Smoke A PASS

Date: 2026-09-09
Stage: Smoke A duplicate/provenance gate / exactly-one execution closure
Generation: `retrieval-v3-dev-generation-v9r23`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r23`
D-144 corrected pre-smoke base commit: `cd533c203f5fe6c767efb36a7ee54c3c371770fc`

## Verdict

**D-145 / v9r23 SMOKE A PASS.** The D-144 corrected final bytes consumed exactly one actual v9r23 coordinator model Smoke A. Frozen `audit_coord_smoke.py` returned `SMOKE_PASS` on the first audit and again 12 seconds later on the same agent/cwd/session/wrapper evidence. The session remained exactly 10 lines with identical SHA256 `0c72127e7d224259bd269e290809efb6d15cb3d5002a22031e3ab1ca23efa53e`, `phasec_probe=1`, descendants 0, and no second Smoke A was launched.

**STOP boundary:** Smoke B has not been executed and is not authorized by this record. No real freeze, Phase C, source-truth snapshot, Author/Reviewer/C generation, selector, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append occurred in this stage. The next logical stage is a separate Smoke-B duplicate/preflight + exactly-one execution gate after a new user `진행해`.

## Fresh prelaunch reconciliation

Immediately before the single frozen launch:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `cd533c203f5fe6c767efb36a7ee54c3c371770fc`
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/dev-v2/`, `eval/retrieval-v3/holdout/` paths absent
- canonical audit exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- D-144 final `GENERATION_PLAN.json`: 69,469 bytes, SHA256 `6bddf1fe4661819b9cb7029f2694194298a91c99ba6d5d491e8634eae4b67eae`
- `author_isolation.mechanics_shas`: 60/60 exact, missing 0, mismatch 0
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, source truth/meta, and final evalset absent
- Smoke-A root/cwd absent
- exact expected Smoke-A OMP session directory `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r23-coord-smoke-20260908-cwd` absent
- complete local registry: 337 parseable records, parse errors 0, exact D-145 title/dedicated-cwd matches 0
- matching Smoke-A processes 0
- Smoke-B/lifecycle, Phase-C, and execute roots absent
- OMP `omp/18.1.13`; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`
- exact bundled Paseo CLI `C:\Users\joji\AppData\Local\Programs\Paseo\resources\bin\paseo.cmd`, version `0.7.2`
- immutable v9r22 `phasec_driver.run.lock` remained present

A broader title scan also found one older repo-cwd record named `D144 v9r23 Smoke A executor` (`0c3a4d53-e2f3-4f28-9160-e4073b7c696a`). Its cwd is the main repo, not the frozen dedicated Smoke-A cwd, so it is not the v9r23 one-shot coordinator. The canonical exact D-145 title/dedicated-cwd/session/root/process gate remained zero before launch.

Prime's read-only prelaunch imports had created one builder-local `__pycache__` directory and two `.pyc` files. The same sole v9r23 implementation executor `3526a9e5-dabd-498d-9c67-3df795c5650a` removed only resolved cache artifacts inside the exact builder via a `paseo send --prompt-file` cache-cleanup-only task. Prime then independently verified cache dirs 0 / `.pyc` 0, plan SHA unchanged, and mechanics 60/60 exact before the one-shot launch.

The previous prelaunch attempt had safely stopped before Smoke A because the local caller-identity gate rejected `paseo send`; no one-shot evidence was consumed. After the companion boundary recovered, the same executor was reused and no replacement implementation executor was created.

No protected plaintext recovery or prohibited git-object/history access was used.

## Smoke A — exactly one actual model launch

A brand-new empty staging cwd was reserved at:

`C:\Users\joji\bc-v3-v9r23-coord-smoke-20260908\cwd`

Frozen `launch_phasec_coordinator.py` was invoked exactly once in `smoke` mode with the exact bundled Paseo CLI and a neutral deterministic prompt requiring exactly one `phasec_probe` call and no other tool call. `PYTHONUTF8=1` remained in the frozen launch environment.

Observed provenance:

- agent: `3f22eda8-fae4-4f21-a4ca-ac72659cbe55`
- title: `D145 v9r23 Smoke A`
- created: `2026-09-08T21:40:17.952Z` (`2026-09-09T06:40:17.952+09:00`)
- cwd: `C:\Users\joji\bc-v3-v9r23-coord-smoke-20260908\cwd`
- ParentAgentId: null
- provider/model: `omp` / `opencode-go/muse-spark-1.3-contributor`
- thinking: `xhigh`
- mode: `full`
- final observed status: `idle`
- OMP fallback provenance: `resolvedModelIsFallback=false`
- exact OMP session: `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r23-coord-smoke-20260908-cwd\2026-09-08T21-40-17-326Z_01a082f6-f32e-7789-8a80-1e9bda66e725.jsonl`
- stable session lines: 10
- stable session SHA256: `0c72127e7d224259bd269e290809efb6d15cb3d5002a22031e3ab1ca23efa53e`
- transcript tool calls: `phasec_probe=1`
- forbidden tool calls: 0
- frozen wrapper log: exactly 1 row, SHA256 `d1216bf580c911a1d88886b56125adfa6d0361d739263872034ad5c47c2300e0`
- wrapper tools/mode: `todo` / `smoke`
- wrapper extension SHA256: `08d615b9d2547049d5a6039cb6d2306f15c2a7fb5a2612b76f2d5453900049a3`
- exact wrapper controls: `--tools=todo`, `-e`, `--no-extensions`, `--no-skills`, `--no-rules`
- descendants: 0
- fallback proven by frozen auditor: true

First frozen auditor result: rc0 `SMOKE_PASS`.

After 12 seconds, the exact same frozen auditor was run against the same agent/cwd/session/wrapper evidence. It again returned rc0 `SMOKE_PASS`; the session path, 10-line count, SHA256, `phasec_probe=1`, descendants 0, fallback proof, and wrapper surface were unchanged.

No second v9r23 Smoke A launcher invocation occurred.

## Independent post-Smoke review

A fresh read-only worker independently re-ran frozen `audit_coord_smoke.py` on the same existing agent/cwd with bytecode generation disabled and reproduced rc0 `SMOKE_PASS`, the exact same 10-line session SHA, `phasec_probe=1`, descendants 0, fallback proof, exact-one wrapper row, and exact agent/cwd/model/Parent-null provenance. It also independently verified plan SHA/bytes, mechanics 60/60, and final cache0.

A second minimal read-only verdict worker then independently checked only closure-critical canonical facts and returned **FINAL PASS — blockers none**. It verified repo clean at the D-144 base, plan 69,469/`6bddf1fe...`, mechanics 60/60, cache0, exact dedicated Smoke-A registry count 1, no later-stage roots/artifacts, audit4 unchanged, production diff0, and protected plaintext paths absent.

## Post-Smoke-A boundary

Post-audit reconciliation:

- final D-144 plan remains SHA256 `6bddf1fe4661819b9cb7029f2694194298a91c99ba6d5d491e8634eae4b67eae`, 69,469 bytes
- mechanics remain 60/60 exact
- builder cache dirs 0 / `.pyc` 0 after exact builder-local post-audit cleanup by the same implementation executor
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, source truth/meta, and final evalset remain absent
- complete registry now has 338 parseable records, parse errors 0, and exactly one D-145 dedicated Smoke-A title/cwd record: `3f22eda8-fae4-4f21-a4ca-ac72659cbe55`
- Smoke-A OMP session directory exists with exactly one `.jsonl` session file
- Smoke-A agent remains idle and its frozen wrapper process/evidence is preserved
- Smoke-B/lifecycle registry matches 0 and Smoke-B root absent
- Phase-C and execute roots absent; later-stage relevant processes 0
- canonical audit remains exactly 4 rows with unchanged SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- production `ml-service/` remains unchanged
- protected dev/dev-v2/holdout plaintext paths remain absent
- immutable v9r22 run lock remains present

Frozen-auditor imports created two builder-local cache directories/four `.pyc` files after the Smoke run. The same implementation executor removed only resolved cache artifacts under the exact v9r23 builder. Prime then independently reverified cache0/pyc0, plan SHA unchanged, and mechanics 60/60 exact. Smoke-A runtime/session/wrapper evidence was not touched.

## Gate boundary

V9r23 has now consumed **Smoke A exactly once and PASSed**. Smoke A is permanently non-repeatable for this generation, regardless of any future stage result.

Next, only after another separate user `진행해`, is **Smoke B duplicate/preflight + exactly-one execution**. Smoke B must not be silently consumed in D-145. Real freeze, Phase C, protected dev-v2, holdout, production, and canonical audit append remain prohibited until their later gates.
