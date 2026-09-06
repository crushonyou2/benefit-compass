# Retrieval v3 D-097 generation-v9r11 Smoke-B CONTRACT_INVALID_GENERATION durable closure (2026-09-06)

Append-only durable failure closure. D-096 and all earlier durable records remain
verbatim. This stage closes v9r11 only; it does not design, implement, freeze,
or smoke a successor generation. Plaintext-free: execution IDs, paths, hashes,
counts, status strings, and structural mechanics only -- no protected query/gold
plaintext.

## 0. Reconciled base (actual wins)

- Repo `C:\Users\joji\Documents\취준자료\project-repos\benefit-compass`, branch
  `codex/retrieval-v3-user-search-quality`, HEAD
  `a41d6cd6890b645dd078b8102c1da68921a9710d`; local = upstream = direct remote;
  working tree clean; `git diff --check` PASS; production `ml-service/` diff
  from `5327661445c37191a3fd61db195f3af4d2cf893a` = 0.
- OMP executable `C:\Users\joji\AppData\Local\omp\omp.exe`, version `18.1.5`;
  effective `modelRoles.default` and `modelRoles.plan` both
  `opencode-go/muse-spark-1.3-contributor:xhigh` from repo cwd, matching
  `C:\Users\joji\.omp\agent\config.yml`; no repo-root OMP overlay observed.
- Audit `eval/retrieval-v3/audit/events.jsonl`: exactly 4 events, SHA256
  `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`.
- Canonical `eval/retrieval-v3/result`, `dev`, `holdout`, and `dev-v2` absent.
  No real dev-v2 evaluation or holdout execution occurred.
- The authorizing channel records the v9r11 Web PRE-SMOKE verdict as PASS.
  Before this closure the repo durable SSOT ended at D-096; no D-097 closure
  existed.

## 1. Smoke A -- exactly once, PASS

- Coordinator smoke agent:
  `564acc04-af3f-45f6-9957-6cde1a1f051f`.
- Exact cwd:
  `C:\Users\joji\bc-v3-v9r11-coord-smoke-20260906\cwd`.
- Live Paseo re-inspection: model `opencode-go/muse-spark-1.3-contributor`,
  thinking `xhigh`, `ParentAgentId=null`, status `idle`.
- Exact session directory contains one JSONL session. Recomputed session SHA256:
  `bb2e204942d39d6b65d11dbb5cc5b78d32674650222e38942ade938501e7530a`;
  10 lines.
- Frozen `audit_coord_smoke.py` was re-run against the existing one-shot evidence
  only (no new model launch) and returned rc 0 `SMOKE_PASS`: tool calls
  `{phasec_probe: 1}`, wrapper tools `todo`, wrapper mode `smoke`, frozen
  controls matched, descendants 0, fallback provenance proven.
- No second Smoke A launch occurred and no post-Smoke-A byte repair occurred.

## 2. Smoke B -- exactly once, CONTRACT_INVALID_GENERATION

- Lifecycle smoke agent:
  `684c4050-4184-4940-b2c4-9645510f25e5`.
- Exact cwd: `C:\Users\joji\bc-v3-v9r11-lifecyclesmoke`.
- Live Paseo re-inspection: model `opencode-go/muse-spark-1.3-contributor`,
  thinking `xhigh`, `ParentAgentId=null`, status `idle`.
- Exact lifecycle session directory contains one JSONL session. Recomputed
  session SHA256:
  `4f369853e11835a6a8ddb8b38ab568a7c5f57fcbecfbac67f1213211315f3cb2`;
  51 lines.
- Structural tool-call extraction from that exact session:
  `read=7`, `bash=2`, `glob=1`, `grep=1`, `write=1`, `todo=5`.
  Expected confined `role_write_chunk=0`.
- Required `out/chunk_0.jsonl` through `out/chunk_5.jsonl` are absent. Instead
  the agent wrote `out/lifecycle_smoke_verdict.json`; the agent's own prose or
  verdict artifact is not authoritative.
- `wrapper_invocation.log` is absent and `role_tool_access.log` is absent.
- The transcript proves semantic staging-boundary escape: a built-in `bash`
  call directly opened and hashed
  `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260906-v9r11\coord_wrapper_tpl\phasec_role_ext.ts`,
  outside the declared lifecycle staging root. Other built-in filesystem and
  shell tools were also available, contrary to the frozen role-tool surface.
- Frozen `audit_lifecycle_smoke.py` was independently re-run against the same
  one-shot evidence and returned rc 3 `CONTRACT_INVALID_GENERATION`, failing on
  `missing file: ...\wrapper_invocation.log`.
- No Smoke B retry and no second lifecycle agent launch occurred.

## 3. Independently verified root cause -- role wrapper PATH unreachable

The failure is execution reachability, not merely missing audit output.

- Final v9r11 `launch_top_level_paseo.py` constructs
  `wrapper_path_value = str(wbin) + ";" + orig_path` but never uses that value
  in the Paseo launch command and never installs it into the sanitized process
  environment that reaches the role agent. Its launch command passes only
  `BC_ROLE_STAGING`, `BC_ROLE_MODE=role`, and `BC_ROLE_KIND` before `--json`.
- In contrast, final `launch_phasec_coordinator.py` explicitly passes
  `--env PATH=<wrapper_bin>;<original PATH>` (plus its wrapper log/mode env)
  into the coordinator launch.
- Therefore Smoke A reached the coordinator wrapper while Smoke B's generic
  role launcher did not place the role wrapper on the effective PATH. The
  lifecycle agent consequently received ordinary built-in tools rather than
  the intended frozen `role_*` confinement surface. The absent wrapper/access
  logs and actual built-in call set are direct execution evidence of that
  reachability defect.
- `launch_top_level_paseo.py` is the intended launcher for later Author-1,
  Author-2, Reviewer-A, Reviewer-B, and C roles, so real Phase C cannot proceed
  from v9r11.

## 4. Final v9r11 bytes and no-real-freeze proof

The following final builder hashes were recomputed after both smokes and match
exactly; no post-result repair was made:

- `GENERATION_PLAN.json` --
  `90a968f446235fd142209b6c850ce2331db414c5f87b90798eade5c832453a85`
- `run_lifecycle_smoke.py` --
  `db06806d8ee54483e5a3f9407cbfbaf6fa0db94b1eeb1162439eb1b7c6fcd66c`
- `audit_lifecycle_smoke.py` --
  `acea49ff05c7c4a1d165f2c4577457dbfa34d5498eb819b0659f6b9837daa769`
- `role_completion_gate.py` --
  `71b1b47195ee6a667f3217298bd5e54d225e29d7bc4fbd06c1355decbb5b7fa0`
- `role_omp_wrapper.py` --
  `fdfdc1d1362a18b676e588e1d811834114140fa892c7394b804c31163687cedc`
- `coord_wrapper_tpl/phasec_role_ext.ts` --
  `7127be65cd715218cc45ae81022945c28c901a32c3c7a930940373bb09b8da71`
- `smoke_lifecycle_prompt.txt` --
  `6a99f0a9b620ce53601f5960176aedb056facb3ae553412b2e10f0107e146f71`
- `smoke_task.json` --
  `be91a285ae085ce82bf73531dbe11dd2347fbaf0b62e21c3ffe4b229608faaf5`

Real builder absence was rechecked: no `PLAN_LOCK.json`, no
`FROZEN_HASHES.json`, no `phasec_driver.run.lock`, no real
`source_truth.jsonl`, no `source_truth_meta.json`, and no `evalset.jsonl`.
No candidate/reviewer/C/selector runtime outputs exist. The only v9r11 home
execution directories are the two smoke roots above. Paseo currently lists
exactly those two v9r11 smoke agents for those cwds.

No protected-data reconstruction or protected-path recovery was performed.
No `git show`, `git cat-file`, checkout/restore, sparse/worktree traversal, or
object scan was used. The smoke evidence is synthetic; no Phase C source-truth
snapshot, protected dev evaluation, or holdout evaluation was run.

## 5. Durable verdict and boundary

**generation-v9r11 = HARD HOLD / CONTRACT_INVALID_GENERATION / NON-RESUMABLE /
NON-REPAIRABLE.**

Under the consumed one-shot contract:

- no Smoke A or Smoke B retry;
- no same-generation repair or post-result byte edit;
- no real freeze;
- no Phase C;
- no Author/Reviewer/C launch;
- no selector or dev-v2 generation;
- no protected dev evaluation or holdout;
- no production retriever change.

The v9r11 private builder, both smoke stagings, and both session evidence sets
remain immutable failure evidence and must not be deleted or rewritten.

This closure adds only this document plus the append-only D-097 entry in
`memory/DECISIONS.md` and the append-only D-097 entry in
`memory/SESSION-LOG.md`. `memory/00-INDEX.md` is intentionally unchanged
because current repository convention does not index individual D-09x closure
documents there. No `ml-service/` change and no audit append.

Successor work, if continued, must start as a **fresh generation with a fresh
private builder**, from read-only reconciliation, repairing generic role-launcher
wrapper PATH reachability while preserving v9r11 unchanged as failure evidence.
STOP after this durable closure commit/push verification.
