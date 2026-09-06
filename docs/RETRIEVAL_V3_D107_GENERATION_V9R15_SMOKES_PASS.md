# Retrieval v3 D-107 — generation-v9r15 one-shot Smoke A/B PASS

Date: 2026-09-07
Stage: one-shot smoke gate durable record only
Generation: `retrieval-v3-dev-generation-v9r15`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260907-v9r15`

## Verdict

**v9r15 ONE-SHOT SMOKE GATE: PASS.** The already-consumed v9r15 Smoke A and Smoke B preserved evidence was independently re-audited with the frozen v9r15 auditors. Both auditors return PASS. No second smoke launch or retry occurred.

This record does **not** real-freeze v9r15 and does not authorize or run Phase C. The next logical stage is a read-only real-freeze pre-gate that must bind the exact Smoke A/B evidence below to the unchanged D-106 v9r15 bytes.

## Reconciled D-106 base

Before independent smoke auditing, actual repo state was branch `codex/retrieval-v3-user-search-quality`, HEAD/local/upstream/direct remote `ff186a48210c102129062ed9fc594159486b3769` (D-106), clean, `git diff --check` PASS, production `ml-service/` diff zero. Canonical audit remained exactly 4 events, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`.

OMP was `18.1.5`; effective default/plan remained `opencode-go/muse-spark-1.3-contributor:xhigh`.

The following D-106 final-byte hashes were rechecked before and after audit and remained exact:

- `freeze_plan_v9r15.py` `81197047e943801edd744c0baebbf8103f0ed6dbb911df1b1354d0135630cbdf`
- `test_freeze_binding_regression.py` `a7641001fd7462c8615fa2ee47649e59908e568018afc72733092828904d8e28`
- `GENERATION_PLAN.json` `83307b659b53b4340aecc68b259de63c311288b0f6fa7064dfe3799c1b02f6e3`
- `run_lifecycle_smoke.py` `32149e859823a9f71841dffc2183932a94d2cd0a8c627a34d32b8f3355f1adad`
- `audit_lifecycle_smoke.py` `6a43e2cb8bdf9323eb3a5b4135883ecaa6a1816497b867268fb6a7589775e2ef`
- `smoke_lifecycle_prompt.txt` `9f29ecbb6dbae10705e98a4da6753de2acc6d4a811585ae5bc0b854aad5c7350`

## Smoke A — preserved one-shot evidence, PASS

- agent: `d7424247-c7fe-4d60-b2f9-69effe362c31`
- cwd: `C:\Users\joji\bc-v3-v9r15-coord-smoke-20260907\cwd`
- model/provider: `omp/opencode-go/muse-spark-1.3-contributor`
- thinking: `xhigh`
- observed status: `idle`
- exact session: `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r15-coord-smoke-20260907-cwd\2026-09-06T16-15-40-621Z_01a07781-0a4c-70f4-80ad-a2403efc90e7.jsonl`
- session lines: 10
- session SHA256: `440409af7a6c74aacf8834d186779b79253154c2dc137d0d7089141a2c8a02bf`
- transcript tool calls: `phasec_probe=1`
- wrapper: exact-one coordinator wrapper row, tools `todo`, mode `smoke`, frozen controls `--tools=todo`, `-e`, `--no-extensions`, `--no-skills`, `--no-rules`
- coordinator extension SHA: `cdae659da7616b2225837e8a6778f12006d490a32ceb79dbb4113272c800e1f7`
- frozen `audit_coord_smoke.py`: rc 0, `SMOKE_PASS`
- descendants: 0
- fallback: proven

The first audit invocation could not reach provenance because the shell lacked `PASEO_CLI`/PATH. A second environment-only audit attempt reached Paseo but the parent Python process decoded Paseo JSON as Windows `cp949`, causing `UnicodeDecodeError` before semantic adjudication. No model was launched in either attempt. Following the standing Windows UTF-8 execution rule already used in D-103, the unchanged frozen auditor was then run with `python -X utf8` and Paseo available on PATH; it returned the rc0 PASS above on the same preserved session/wrapper evidence.

## Smoke B — preserved one-shot evidence, PASS

- agent: `79114e77-92c7-4a9b-aae8-232e65b35237`
- staging/cwd: `C:\Users\joji\bc-v3-v9r15-lifecyclesmoke`
- model/provider: `omp/opencode-go/muse-spark-1.3-contributor`
- thinking: `xhigh`
- observed status: `idle`
- exact session: `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r15-lifecyclesmoke\2026-09-06T16-16-42-020Z_01a07781-fa24-7739-a8c6-fe19ffa316d2.jsonl`
- session lines: 19
- session SHA256: `0a7b32dc8a63bb2f485b2ab6a75812aa9452846d9043802b87773fe60e1870d3`
- transcript tool calls: `role_smoke_probe=1`, `todo=4`
- wrapper: exact-one role wrapper row, tools `todo`, mode `role`, kind `lifecycle_smoke`
- role extension SHA: `6b5a1f426752e403a7ba96585b263cedd0bb9aea3646779a37c6a4bad3e62534`
- access log: exactly 9 rows
  - `cross-role` deny: exactly 1
  - `unknown-resource` deny: exactly 1
  - `bad-target` deny: exactly 1
  - allowed writes `out/chunk_0.jsonl` ... `out/chunk_5.jsonl`: exactly 1 each
- outputs: exactly six files, each 59 bytes / 1 row
- frozen `audit_lifecycle_smoke.py`: rc 0, `LIFECYCLE_SMOKE_PASS`
- descendants: 0
- fallback: proven

Exact output SHA256 values:

- `chunk_0.jsonl` `e7d2aecdf462de9a8918695e7adb70032f80c50205ce849b42664fe3877f24e9`
- `chunk_1.jsonl` `1e942823dc343829cab4c491ceee21ef4a6f8a54337ae32c5564bf5920b8d2f7`
- `chunk_2.jsonl` `90bdd8c64714150816c00c9ef40c6102d451dbf0102d3a3a698b204e7bfd090d`
- `chunk_3.jsonl` `c695e51a11fa40103355a84f95f15396616465d391bdeade92ec03db24244e1a`
- `chunk_4.jsonl` `d72b87b5d2fabbfd43d2b9b999bcd3cfcd4a6cfe251b44e21e5f97ce2f82de0f`
- `chunk_5.jsonl` `4d14e6c3ee466e96ff1daf257dbe26e3205070c197e97757e9f5e9fc90d953ff`

The same PATH/cp949 transport-only issue affected the first two auditor attempts. The unchanged frozen lifecycle auditor then ran under `python -X utf8` with Paseo on PATH and returned the rc0 PASS above. No second Smoke B launch occurred.

## Final immutability / forbidden-state checks

Auditor imports created only Python `__pycache__` / `.pyc` files inside the v9r15 builder. Their resolved absolute paths were verified to remain strictly below `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260907-v9r15`, then only those cache directories were removed. Final builder state: 66 source/support files, zero Python cache artifacts.

After cleanup and rehash, the D-106 key bytes remained exact. The v9r15 builder still has none of:

- `PLAN_LOCK.json`
- `FROZEN_HASHES.json`
- `phasec_driver.run.lock`
- `source_truth.jsonl`
- `source_truth_meta.json`
- `evalset.jsonl`
- `out/`

No real freeze, Phase C, source-truth snapshot, Author/Reviewer/C/selector run, protected evaluation, holdout evaluation, production change, or canonical audit append occurred in D-107.

## Next logical stage

**NEXT: read-only v9r15 real-freeze pre-gate.** Reconcile the unchanged D-106 builder bytes and exact D-107 Smoke A/B proofs, then invoke the repaired v9r15 freeze CLI only if all bindings are exact. The real freeze must bind all eight smoke identity/provenance values: A agent/cwd/session/wrapper and B agent/cwd/session/wrapper.

Do not launch another smoke. Do not run Phase C until the real freeze itself has completed and an independent review explicitly approves the transition.
