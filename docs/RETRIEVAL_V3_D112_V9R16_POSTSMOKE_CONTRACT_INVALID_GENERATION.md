# Retrieval v3 D-112 — generation-v9r16 post-smoke CONTRACT_INVALID_GENERATION

Date: 2026-09-07
Stage: one-shot Smoke A/B closure
Generation: `retrieval-v3-dev-generation-v9r16`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260907-v9r16`

## Verdict

**v9r16 = HARD HOLD / CONTRACT_INVALID_GENERATION / NON-RESUMABLE / NON-REPAIRABLE.** Smoke A passed. Smoke B was launched exactly once and produced the deterministic lifecycle helper evidence, but the local Paseo daemon connection failed immediately after launch during the frozen runner's early provenance inspection. After daemon recovery, the preserved Smoke-B agent is `closed`, not the frozen-required `idle`, and its final assistant stop reason is `aborted`, not `stop`. The frozen `audit_lifecycle_smoke.py` independently returns rc3 `CONTRACT_INVALID_GENERATION` on the preserved evidence.

No second Smoke B, no same-generation repair, no real freeze, and no Phase C are permitted.

## Reconciled D-111 base

Immediately before smoke execution, branch `codex/retrieval-v3-user-search-quality` was at D-111 commit `5657d8737fcafd2a8a01325a98cb89c3c4cf50a9`, with local/upstream/direct remote equal and clean. Production `ml-service/` diff remained zero and canonical audit remained exactly 4 events SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`.

The final PRE-SMOKE v9r16 bytes were exact, builder 67 source/support files/cache0, and no lock/frozen-hash/run-lock/source-truth/evalset/runtime artifacts existed.

## Smoke-A prelaunch transport attempt — no model execution

The first coordinator-launch transport attempt explicitly forced the desktop `paseo.exe` path instead of letting the frozen launcher resolve its standing bundled CLI wrapper. `paseo run` returned nonzero before any agent/model execution.

Preserved evidence proves this did **not** consume Smoke A:

- staging `C:\Users\joji\bc-v3-v9r16-coord-smoke-20260907\cwd` contains only the copied `wrapper_bin` files;
- no `wrapper_invocation.log` exists;
- no matching OMP session directory exists;
- no matching Paseo agent exists.

The frozen launcher's actual fixed CLI is `C:\Users\joji\AppData\Local\Programs\Paseo\resources\bin\paseo.cmd`, which sets the bundled CLI environment before invoking Paseo. The failed prelaunch root is preserved; it was not reused.

## Smoke A — actual one-shot, PASS

A fresh empty cwd was used for the first and only actual Smoke-A model launch:

- agent: `350c1a36-f18e-41ca-8c58-134212c508cc`
- cwd: `C:\Users\joji\bc-v3-v9r16-coord-smoke-20260907-r1\cwd`
- provider/model: `omp/opencode-go/muse-spark-1.3-contributor`
- thinking: `xhigh`
- ParentAgentId: null
- wrapper: exact-one `coord_wrapper_invoked`, mode `smoke`, custom tool `phasec_probe`, tools `todo`, frozen controls, coordinator extension SHA `1f32723037ed4cab2b087f29d3f12c4235e081a13a76d7c7f561cdf5b8a49a15`
- exact session: `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r16-coord-smoke-20260907-r1-cwd\2026-09-06T17-31-37-018Z_01a077c6-90ba-7200-a9a5-e0da3c15a51a.jsonl`
- final stable session lines: 11
- final stable session SHA256: `59c6cb6f46afefdbc33d20b17e3df62de22de5d8881638bdee323a85790f0517`
- transcript calls: `phasec_probe=1`
- frozen coordinator auditor after daemon recovery: rc0 `SMOKE_PASS`, descendants 0, fallback proven

An earlier immediate audit observed the same session before its final asynchronous append at 10 lines/SHA `6d0967a5...fe2e`; the later stable 11-line bytes above are authoritative and independently re-audit PASS. No second model launch occurred.

## Smoke B — exactly once, lifecycle terminal-state failure

Only after Smoke A frozen-auditor PASS, the frozen `run_lifecycle_smoke.py` was invoked once.

The runner launched exactly one top-level lifecycle agent and then lost its daemon connection during early `verify_top_level`/inspect. It exited without launching any second agent.

Preserved Smoke-B evidence:

- agent: `b2754ce2-9cd4-496f-8143-8c50b7c3bbc9`
- staging/cwd: `C:\Users\joji\bc-v3-v9r16-lifecyclesmoke`
- provider/model: `omp/opencode-go/muse-spark-1.3-contributor`
- thinking: `xhigh`
- ParentAgentId: null
- exact session: `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r16-lifecyclesmoke\2026-09-06T17-32-41-507Z_01a077c7-8ca3-7280-9785-0f7982872356.jsonl`
- session lines: 13
- session SHA256: `fe37e40cea0cf20126468d092b06d7940beed3b5e57d00117e60c35cd5a9b58c`
- transcript tool calls: `todo=1`, `role_smoke_probe=1`
- wrapper: exact-one role wrapper, tools `todo`, mode `role`, kind `lifecycle_smoke`, frozen role extension SHA `408ce7edff2b9af6abd3690a5648cb668517a453f4c06116c7de4350a3429509`
- helper access log: exactly 9 rows = exact deterministic deny triple once each plus six allowed writes once each
- outputs: exact six files, each 59 bytes / 1 row, with the standing deterministic hashes

The deterministic filesystem/probe portion therefore executed, but the frozen lifecycle contract also requires a live Paseo `idle` state and a final assistant `stop`.

After the local daemon was restarted solely to recover read access to the already-consumed evidence:

- agent status = `closed`
- `role_completion_gate.session_final_stop(...)` = false: `final assistant stopReason='aborted' != stop`
- frozen `audit_lifecycle_smoke.py` on the same agent/staging/session/wrapper = rc3: `CONTRACT_INVALID_GENERATION`, `agent status='closed' not idle at audit`

The daemon restart did not launch or resume a model. No second Smoke B was performed.

## Final immutability / boundary

Auditor imports created only v9r16 builder-local Python cache artifacts. Their resolved paths were proven inside the v9r16 builder and only those cache directories were removed.

Final v9r16 builder remains 67 source/support files, cache0, with final D-111 key bytes unchanged including:

- plan `729597182ba7ac646ee859b3b8a05baee448794d2aa7d84a27b60189c70d3105`
- freeze script `9741d4a01fec5d5141ea2061969d54c92d261c75a8e615642a1f99d02431a3e1`
- writer preflight regression `d1313f41501d9642c22224d9a5c34f1f92cd08608e9dab3a65f354cbf969f257`
- role extension `408ce7edff2b9af6abd3690a5648cb668517a453f4c06116c7de4350a3429509`

No real `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, source truth, semantic-role runtime, `evalset.jsonl`, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append occurred.

## Closure / next

**STOP v9r16.** Preserve both smoke roots, sessions, wrapper/access logs, outputs, the prelaunch transport-failure root, and the v9r16 builder as immutable evidence. Do not retry/reopen/repair v9r16.

If generation work continues, use a fresh successor generation. The successor may preserve the D-110 writer-envelope repair, but must treat D-112 as lifecycle-infrastructure evidence and establish a fresh pre-smoke execution plan; v9r16 one-shot smoke evidence cannot be reused as successor PASS evidence.
