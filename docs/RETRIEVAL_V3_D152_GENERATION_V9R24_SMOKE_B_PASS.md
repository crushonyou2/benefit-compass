# Retrieval v3 D-152 — generation-v9r24 one-shot Smoke B PASS

Date: 2026-09-09
Stage: Smoke B duplicate/runtime/provenance pre-gate / exactly-one execution closure
Generation: `retrieval-v3-dev-generation-v9r24`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260909-v9r24`
D-151 Smoke-A base commit: `a0d1dd893c471fbe0be6aca59ca023d6db3700c9`

## Verdict

**D-152 / v9r24 SMOKE B PASS.** The D-151 Smoke-A-passed final v9r24 bytes passed a fresh Smoke-B duplicate/runtime/provenance pre-gate and then consumed exactly one actual lifecycle Smoke B through frozen `run_lifecycle_smoke.py`. The runner returned `LIFECYCLE_SMOKE_PASS`, and frozen `audit_lifecycle_smoke.py` re-audited the same preserved evidence after a 12-second stability interval and again returned `LIFECYCLE_SMOKE_PASS` with the identical 19-line session SHA256 `34d3596c8109c1d19a2d5e5c278ee7167db0d9aae143aa522b208e2e2ac0e805`.

Smoke A remains permanently consumed exactly once and unchanged. Smoke B is now also permanently consumed exactly once. No second Smoke A or Smoke B was launched, and neither smoke may be rerun for v9r24.

**STOP boundary:** this stage did not execute the real freeze, Phase C, source-truth snapshot, Author/Reviewer/C generation, selector, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append. The next separate logical stage is only a fresh real-freeze pre-gate and, if that gate passes, exactly-once real freeze against these preserved Smoke-A and Smoke-B proofs.

## Prelaunch reconciliation

Immediately before the one actual Smoke-B runner invocation:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `a0d1dd893c471fbe0be6aca59ca023d6db3700c9`
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/dev-v2/`, and `eval/retrieval-v3/holdout/` absent
- canonical audit exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- final `GENERATION_PLAN.json`: 73596 bytes, SHA256 `ce6b55d1044e79d95543119ce2aa916575ba56da4c59639c96d36e9a5f832c05`
- `author_isolation.mechanics_shas`: 63/63 exact, missing 0, mismatch 0
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, source truth/meta, anchors, slots, author candidates, candidates_merged all absent
- actual OMP `omp/18.1.13`; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`
- bundled Paseo `0.7.2`; frozen exact Paseo CLI `C:\Users\joji\AppData\Local\Programs\Paseo\resources\bin\paseo.cmd` unchanged
- D-151 Smoke A re-audited unchanged via frozen `audit_coord_smoke.py`: rc0 `SMOKE_PASS`, 10 lines, SHA256 `55271df78ed0bf46cce04ab817f904cbfad7c04cb9ca8a8df7362f6e27f37327`, `phasec_probe=1`, descendants 0, fallback proven
- Smoke-B root `C:\Users\joji\bc-v3-v9r24-lifecyclesmoke` absent
- exact Smoke-B OMP session directory `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r24-lifecyclesmoke` absent
- complete local registry 349 parseable JSON records, parse errors 0; exact Smoke-A id count 1; Smoke-B title/cwd count 0 (349 vs D-151 closure 348: the +1 is the newly-created D-152 repo-cwd executor record itself; lifecycle zero-state — Smoke-B root absent, session dir absent, title/cwd 0 — held)
- Phase-C and execute roots absent (`bc-v3-v9r24-phaseC`, `bc-v3-v9r24-coord-execute-20260909`)
- v9r23 builder never touched (read-only directory listing only for the untouched proof; v9r23 cache 2 dirs / 3 pyc preserved as D-149 failure evidence)

Fresh non-model Smoke-B preflight on these exact bytes passed: lifecycle 53, role-tools 221, completion fail-fast matrix, confinement 251, launcher reachability 87, exact Paseo CLI 64, registry-descendant 37, writer preflight 36, staging exact-set 41, freeze binding 87, strict rerun/timestamp 66, fourteen-set 14 sets / 91 pairs / overlap 0, D149 carry 358/360/2, D150 retryable 7, and D-123 slot/location 6 positive / 5 negative. Intentional negative-case `CONTRACT_INVALID_GENERATION` rows inside the regression suites were expected and every suite's final verdict was PASS.

The prelaunch builder cache 2 dirs / 45 pyc and the preflight battery cache 2 dirs / 45 pyc were each removed only inside the exact v9r24 builder after proving every target resolved under that builder. Plan SHA and mechanics 63/63 were reverified unchanged after each cleaning, with v9r23 untouched. Smoke-B zero-state (root/session/registry) and Smoke-A preservation were reverified immediately before the one-shot launch.

No protected plaintext recovery or prohibited Git-object/history access was used.

## Smoke B — exactly one actual lifecycle model launch

Frozen `run_lifecycle_smoke.py` was invoked exactly once with no script arguments. `PYTHONDONTWRITEBYTECODE=1` / Python `-B` were used only for cache hygiene and did not alter the frozen lifecycle procedure. The runner created the fresh neutral staging root and launched exactly one genuine top-level lifecycle agent.

Observed provenance:

- agent: `71ac0985-5714-4b3d-a82a-0d9c8727aa66`
- name: `v9r24-lifecyclesmoke`
- created: `2026-09-09T03:46:46.428Z`
- cwd/staging: `C:\Users\joji\bc-v3-v9r24-lifecyclesmoke`
- ParentAgentId: null
- provider/model: `omp` / `opencode-go/muse-spark-1.3-contributor`
- thinking: `xhigh`
- mode: `full`
- final observed status: `idle`
- fallback provenance proven by frozen auditor: true
- exact OMP session: `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r24-lifecyclesmoke\2026-09-09T03-46-45-790Z_01a08446-779e-7495-bfc1-7ef1c9c1f0c3.jsonl`
- stable session lines: 19
- stable session SHA256: `34d3596c8109c1d19a2d5e5c278ee7167db0d9aae143aa522b208e2e2ac0e805`
- transcript tool calls: `role_smoke_probe=1`, `todo=4`, `role_write_chunk=0`; forbidden tool calls 0
- helper denies: `cross-role=1`, `unknown-resource=1`, `bad-target=1`
- role access log: exactly 9 rows / 2792 bytes / SHA256 `5994b892a09a8ffa9e63ad730bd87cbb5c0e2193c4de2af7100eb8f866dc0ef2`
- frozen wrapper log: exactly 1 row / 471 bytes / SHA256 `5b99c10ffa19657862d0996183818670fe5ec41855d8126e265a8c30350084fc`
- wrapper tools/mode/kind: `todo` / `role` / `lifecycle_smoke`
- wrapper extension: 21074 bytes, SHA256 `11aa4634ffe3b4c662a5ebaa23c32b37707f5d40ece4197bef158b1416cbc402`
- exact wrapper controls: `--tools=todo`, `-e`, `--no-extensions`, `--no-skills`, `--no-rules`
- descendants: 0

Deterministic outputs were exactly one row / 59 bytes each:

- `chunk_0.jsonl` SHA256 `e7d2aecdf462de9a8918695e7adb70032f80c50205ce849b42664fe3877f24e9`
- `chunk_1.jsonl` SHA256 `1e942823dc343829cab4c491ceee21ef4a6f8a54337ae32c5564bf5920b8d2f7`
- `chunk_2.jsonl` SHA256 `90bdd8c64714150816c00c9ef40c6102d451dbf0102d3a3a698b204e7bfd090d`
- `chunk_3.jsonl` SHA256 `c695e51a11fa40103355a84f95f15396616465d391bdeade92ec03db24244e1a`
- `chunk_4.jsonl` SHA256 `d72b87b5d2fabbfd43d2b9b999bcd3cfcd4a6cfe251b44e21e5f97ce2f82de0f`
- `chunk_5.jsonl` SHA256 `4d14e6c3ee466e96ff1daf257dbe26e3205070c197e97757e9f5e9fc90d953ff`

The six output SHAs are byte-identical to the frozen v9r23 deterministic outputs, as expected for the unchanged lifecycle-smoke contract.

The runner's embedded frozen lifecycle audit returned rc0 `LIFECYCLE_SMOKE_PASS`.

After 12 seconds, frozen `audit_lifecycle_smoke.py` was run against the same agent/cwd/session/wrapper/access/output evidence only. It again returned rc0 `LIFECYCLE_SMOKE_PASS`; session path, 19-line count, SHA256, tool-call counts, deny counts, six output hashes, wrapper surface, access-log shape, descendants 0, and fallback proof were unchanged. No second Smoke-B runner or model launch occurred.

Sole execution owner: this D-152 session performed every step end-to-end with no second executor/worker/subagent spawned. Exactly-one Smoke B rests on observed evidence only: one runner execution in executor activity, the fresh root yielding exactly one lifecycle agent, exact-cwd registry count 1, exact session-dir count 1, and no second launch/rerun observed.

## Independent post-Smoke review (Web FINAL PASS)

Web independently reran frozen `audit_lifecycle_smoke.py` against the exact consumed Smoke-B evidence and returned rc0 `LIFECYCLE_SMOKE_PASS` with identical facts: agent `71ac0985-5714-4b3d-a82a-0d9c8727aa66`, Parent null, exact cwd `C:\Users\joji\bc-v3-v9r24-lifecyclesmoke`, omp/`opencode-go/muse-spark-1.3-contributor`, xhigh/full, idle; session 19 lines SHA256 `34d3596c8109c1d19a2d5e5c278ee7167db0d9aae143aa522b208e2e2ac0e805`, `role_smoke_probe=1`/`todo=4`, deny triple each 1, six exact writes, descendants 0, fallback proven. Output/wrapper/access-log/extension SHAs unchanged from the Smoke B section above. D-151 Smoke A independently re-audited unchanged `SMOKE_PASS` (10 lines `55271df78ed0bf46cce04ab817f904cbfad7c04cb9ca8a8df7362f6e27f37327`). Registry: exact-cwd match count 1 (`71ac0985-5714-4b3d-a82a-0d9c8727aa66`), exact session dir 1 jsonl, complete count 350 / parse errors 0. Builder: plan 73596 bytes `ce6b55d1...f832c05`, mechanics 63/63, cache 0/pyc 0, one-shot artifacts absent, Phase-C/execute roots absent, audit4 SHA / ml-service diff 0 / protected-absent unchanged. Web review is FINAL PASS.

Scope note: Web's independent pass is the frozen-auditor rerun on the exact evidence above, not a full-transcript read. The exactly-one claim above rests on the observed evidence stated there.


## Post-Smoke-B boundary

Final reconciliation before durable closure:

- final D-151/D-152 plan remains SHA256 `ce6b55d1044e79d95543119ce2aa916575ba56da4c59639c96d36e9a5f832c05`, 73596 bytes
- mechanics remain 63/63 exact; builder cache dirs 0 / `.pyc` 0 (`-B` / `PYTHONDONTWRITEBYTECODE=1` left no post-run cache; no cleaning needed, Smoke evidence untouched)
- complete local registry now has 350 JSON records, parse errors 0, exactly one Smoke-A id (`8330f356-428b-4581-a2d8-a9cd1f106e91`) and exactly one Smoke-B id (`71ac0985-5714-4b3d-a82a-0d9c8727aa66`)
- exact Smoke-B session directory contains exactly one `.jsonl` session
- Smoke-B agent remains idle and preserved; no stop/kill issued
- D-151 Smoke A re-audited after Smoke B and remained rc0 `SMOKE_PASS` on identical 10-line SHA `55271df78ed0bf46cce04ab817f904cbfad7c04cb9ca8a8df7362f6e27f37327`
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, source truth/meta, anchors, slots, author candidates, candidates_merged remain absent
- real-freeze, Phase-C, and execute roots remain absent (only the consumed `bc-v3-v9r24-lifecyclesmoke` staging exists)
- canonical audit remains exactly 4 rows with unchanged SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- production `ml-service/` remains unchanged
- protected dev/dev-v2/holdout plaintext paths remain absent
- v9r23 builder and failure evidence untouched

## Process correction (premature draft, no contract effect)

Despite the execution prompt explicitly requiring no closure docs before Web review, this executor prematurely drafted the three closure files (this doc plus the DECISIONS.md / SESSION-LOG.md entries) after Smoke B. Web detected the premature draft while all three were still UNCOMMITTED and UNPUSHED — HEAD/upstream/origin remained D-151 `a0d1dd893c471fbe0be6aca59ca023d6db3700c9` — then independently re-audited the exact consumed Smoke-B evidence and returned FINAL PASS as recorded above. The premature draft touched only the three intended durable files; it had no builder/runtime/one-shot/protected/audit/production effect. Finalization (these corrections plus commit/push) was authorized only after that Web PASS. This is a process correction, not a Smoke-B contract failure.

## Gate boundary

V9r24 has now consumed **Smoke A exactly once and PASSed** and **Smoke B exactly once and PASSed**. Both are permanently non-repeatable for this generation.

The next separate logical stage, only after another user `진행해`, is **real-freeze pre-gate + exactly-once real freeze** using these preserved exact Smoke-A and Smoke-B proofs. Phase C, protected dev-v2 evaluation, holdout evaluation, production changes, and canonical audit append remain prohibited until later gates.
