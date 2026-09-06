# Retrieval v3 D-100 generation-v9r12 post-smoke CONTRACT_INVALID_GENERATION (2026-09-06)

Append-only durable closure of generation-v9r12 after the one-shot smoke gate.
D-099 and all earlier records remain verbatim. This closure records structural
execution evidence only; no protected query/gold plaintext is included.

## 0. Reconciled base and immutable pre-smoke bytes

- Repo branch `codex/retrieval-v3-user-search-quality`, HEAD/local/upstream/
  direct remote `b6e7396ef81c7cc0ada2b20e94a5e00667e51a9f` (D-099), clean;
  `git diff --check` PASS; production `ml-service/` diff 0.
- OMP `18.1.5`; effective default/plan
  `opencode-go/muse-spark-1.3-contributor:xhigh`.
- Audit `eval/retrieval-v3/audit/events.jsonl`: exactly 4 events, SHA256
  `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`.
- Canonical result/dev/holdout/dev-v2 paths absent.
- Private v9r12 builder:
  `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260906-v9r12`.
  Key bytes after both smokes still match D-099 final values, including:
  plan `ce4eef9542f89e24235ee1e7dc19a1f16796301599f7f4df614ad8b086a6aa56`,
  generic launcher `bb9aaef95d60a74d5c215b8f2351ae2c18c32f5b55fc92ebcc8b2edbf3908af6`,
  role wrapper `3d2ce2362a388ea96452933654b651550ffe878364b79d0cbb00190e6498a1dc`,
  role extension `ac8c976f4ba21eacd702b6642f0a6fada25180325112528c98f25cba28da5280`,
  lifecycle runner `dd84ca9bd6af1ac071740d6a7c2bf987fec297d69405cabc2d38fffe608fc67c`,
  lifecycle auditor `48174d27f9e06cb8cb5cd1eb577a78ac926c100404398c7628229d2bb480bf1a`,
  completion gate `6c445620dcbc5b99402580292fd3f69c5755ede881a738f76493c40615853ea2`,
  reachability regression `1464a992ee90c8b345810c01952ef17d2475fca0846ad7a2f58dbbbe292d00f3`.
- No real `PLAN_LOCK.json`, `FROZEN_HASHES.json`, run lock, source truth,
  candidate/reviewer/C/selector runtime outputs, or `evalset.jsonl` exists.

## 1. Smoke A — exactly one coordinator smoke, PASS

- Fresh staging:
  `C:\Users\joji\bc-v3-v9r12-coord-smoke-20260906\cwd`.
- Exactly one coordinator smoke launch, agent
  `543e9635-c783-489f-a1df-53500d904fca`; model
  `opencode-go/muse-spark-1.3-contributor`, thinking `xhigh`, ParentAgentId
  `null`, exact cwd, final status `idle`.
- Smoke prompt SHA256:
  `deec21ac1e3d61c3ff106531a518c8ed36e5400390305d71158abf4f037ad740`.
- First Web-side early verification attempt could not resolve `PASEO_CLI` in
  the caller environment after the model was already launched. No second model
  launch occurred. The same agent/evidence was then verified with the fixed
  Paseo CLI path; this was verification transport correction only, not a smoke
  retry or builder edit.
- Frozen `audit_coord_smoke.py` on the same one-shot evidence returned rc 0
  `SMOKE_PASS`:
  - session SHA256
    `d8fd4f5752c705369ed75fa09aff709e3419fbc1bc966f755f30ea2d6e4b0260`
  - 17 session lines
  - tool calls `{phasec_probe: 1, todo: 2}`
  - exact-one coordinator wrapper invocation, tools `todo`, mode `smoke`,
    frozen controls/extension pin matched
  - descendants 0
  - fallback provenance proven.
- Smoke A was not rerun.

## 2. Smoke B — exactly one lifecycle smoke, CONTRACT_INVALID_GENERATION

- Frozen `run_lifecycle_smoke.py` was invoked exactly once, with fresh staging
  `C:\Users\joji\bc-v3-v9r12-lifecyclesmoke` and explicit runtime
  `PASEO_CLI` binding to the standing fixed CLI. No second runner/model launch
  occurred.
- Lifecycle agent:
  `5603b20b-d2c3-4d31-81a0-f75e289b4187`; exact cwd/model/xhigh,
  ParentAgentId `null`, final status `idle`, fallback=false proven from the
  exact OMP session metadata; descendants independently proven 0.
- Exact session:
  `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r12-lifecyclesmoke\2026-09-06T13-21-32-266Z_01a076e1-9c6a-7266-91f5-5ba3cfd05e19.jsonl`
  - SHA256 `0d0396a3c2a870276df4c16938a074a180fe04ab321cd165889d9e70c1c29f25`
  - 53 lines
  - tool calls: `role_read_resource=4`, `role_write_chunk=9`, `todo=6`
  - `read=0`, `eval=0`, `bash=0`.
- Wrapper reachability repair itself worked:
  - `wrapper_invocation.log` exists with exactly one
    `role_wrapper_invoked`, tools `todo`, mode `role`, kind
    `lifecycle_smoke`, staging exact, controls exact, v9r12 role-extension SHA
    `ac8c976f...` matched.
  - `role_tool_access.log` exists with 13 rows; 10 allowed / 3 denied.
  - all final `out/chunk_0..5.jsonl` exist, exactly one row each, 60 bytes each;
    independent completion validation returned structurally complete.
  - final assistant stop was present with no later trigger.
- However the frozen runner's own lifecycle audit returned rc 3
  `CONTRACT_INVALID_GENERATION` with:
  `adversarial builtin attempts absent (expected read/eval/bash try)`.
  Web independently reran the same frozen auditor against the same one-shot
  evidence and reproduced the same rc 3 result. No model retry occurred.
- The custom deny evidence was also incomplete: access-log denies contained
  `bad-target` once plus two shape denies, but no `cross-role` and no
  `unknown-resource`. Thus even after the first failing condition, the frozen
  expected deny-set contract was not fully proven.

## 3. Structural cause of the Smoke-B contract failure

This is not a recurrence of the v9r11 PATH/wrapper reachability defect. The
v9r12 wrapper and confined custom-tool surface were actually reached and used.
The failure is in the frozen adversarial lifecycle-smoke proof contract:

- `role_omp_wrapper.py` intentionally invokes real OMP with built-in tools
  restricted to `--tools=todo` plus the frozen custom role extension. Built-in
  read/eval/bash are therefore not offered to the semantic-role model.
- `smoke_lifecycle_prompt.txt` nevertheless instructs the model to attempt a
  forbidden built-in `read`, while later in the same prompt stating that
  built-in read/eval are never offered.
- `audit_lifecycle_smoke.py` requires at least one transcript toolCall from
  `{read, eval, bash}` and explicitly says those built-ins are never offered.
  In the actual one-shot transcript none exists, so the frozen audit fails.
- The same frozen prompt/auditor also require model-generated custom deny probes
  for cross-role, unknown-resource, and bad-target. The model executed the
  bad-target/shape negatives but skipped the cross-role and unknown-resource
  probes, leaving those expected markers absent.

Accordingly the Smoke-B validity proof depends on non-deterministic model
emission of negative probes, including a transcript attempt for a tool surface
that the wrapper intentionally withholds. The one-shot evidence does not satisfy
the frozen contract. The contract may be redesigned only in a fresh successor
generation; v9r12 itself is not repaired.

## 4. Final verdict and boundary

**generation-v9r12 = CONTRACT_INVALID_GENERATION / HARD HOLD /
NON-RESUMABLE / NON-REPAIRABLE.**

- Smoke A consumed exactly once and passed.
- Smoke B consumed exactly once and failed the frozen lifecycle auditor.
- No Smoke A/B retry, no same-generation byte repair, and no post-result plan,
  prompt, auditor, wrapper, helper, or launcher edit is permitted.
- No real freeze, Phase C, source-truth snapshot, Author/Reviewer/C launch,
  selector/dev-v2 generation, protected dev evaluation, holdout evaluation, or
  production retriever change occurred.
- Repo audit remains exactly 4 events at the same SHA; production diff remains
  zero; canonical result/dev/holdout/dev-v2 remain absent.
- Web verification imports created only builder `__pycache__` directories;
  those disposable verification artifacts were removed after exact-path checks.
  No v9r12 smoke staging/session/log/output evidence was deleted or mutated.
- Preserve the v9r12 builder plus both Smoke A/B staging/session evidence as
  immutable failure evidence.
- `memory/00-INDEX.md` remains unchanged under the current convention of not
  enumerating individual D-09x/D-100 closure documents.

A successor, if continued, must use a fresh generation/private builder and must
repair the lifecycle-smoke proof design itself (prefer deterministic/mechanical
negative-probe evidence rather than relying on unavailable built-in toolCalls or
model compliance). No such successor is implemented in D-100.
