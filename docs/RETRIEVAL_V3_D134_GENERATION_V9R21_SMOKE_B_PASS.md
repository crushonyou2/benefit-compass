# Retrieval v3 D-134 — generation-v9r21 one-shot Smoke B PASS

Date: 2026-09-08
Stage: Smoke B duplicate/runtime/provenance pre-gate / exactly-one execution closure
Generation: `retrieval-v3-dev-generation-v9r21`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r21`
D-133 Smoke-A base commit: `eb24d52fdc50f34367ac67be0241cf7a0c76b094`

## Verdict

**SMOKE B PASS.** D-133's Smoke-A-passed v9r21 final bytes passed a fresh duplicate/runtime/provenance pre-gate and then consumed exactly one actual lifecycle Smoke B through frozen `run_lifecycle_smoke.py`. The runner returned `LIFECYCLE_SMOKE_PASS`. Frozen `audit_lifecycle_smoke.py` re-audited the same preserved evidence after a 12-second stability interval and again returned `LIFECYCLE_SMOKE_PASS` with the identical 21-line session SHA256 `6e7f1517bf1dac95a82d80488400d571974d113adfa6e02860d9babec60312bb`.

Smoke A remains permanently consumed exactly once and unchanged. Smoke B is now also permanently consumed exactly once. No second Smoke A or Smoke B was launched, and neither smoke may be rerun for v9r21.

Two independent read-only post-run reviews returned PASS with no concrete lifecycle-contract, duplicate, provenance, registry, data-boundary, or runtime blocker.

**STOP boundary:** this stage did not execute the real freeze, Phase C, source-truth snapshot, Author/Reviewer/C generation, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append. The next separate logical stage is only a fresh real-freeze pre-gate and, if that gate passes, exactly-once real freeze against these preserved Smoke-A and Smoke-B proofs.

## Prelaunch reconciliation

Immediately before the one actual Smoke-B runner invocation:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `eb24d52fdc50f34367ac67be0241cf7a0c76b094`
- working tree clean
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- protected `eval/retrieval-v3/dev/` and `eval/retrieval-v3/holdout/` plaintext paths absent
- canonical audit exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- final plan SHA256 `9a3369a3dada669a2cd448f59ceaf41982fb94fc11029b20d2431f72430653ec`, 65,857 bytes; mechanics 59/59 exact
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock` absent; builder cache/pyc 0
- actual OMP `omp/18.1.13`; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`; bundled Paseo `0.7.2` reachable
- D-133 Smoke A re-audited unchanged: `SMOKE_PASS`, 10-line SHA256 `37c536ce6fb4dcbe686c9e3f6efb70a7dc008e9192583c5f52fc6cad9b3ddae5`, `phasec_probe=1`, descendants0, fallback proven
- Smoke-B registry/root/session/process duplicates all zero

Final-byte pre-Smoke-B regressions passed: lifecycle53, role172, registry37, reachability87, staging24, freeze-binding66, freeze-rerun38, and completion gate. Freeze tests used disposable copies only. Two independent read-only pre-gate reviews also returned PASS before the one-shot was consumed.

## Smoke B — exactly one actual lifecycle model launch

Frozen `run_lifecycle_smoke.py` was invoked exactly once with no argv. It created the fresh neutral staging root and launched exactly one genuine top-level lifecycle agent.

- agent: `2989f690-8e62-48a5-809b-7fa61331e6e0`
- title: `v9r21-lifecyclesmoke`
- cwd/staging: `C:\Users\joji\bc-v3-v9r21-lifecyclesmoke`
- ParentAgentId: null
- provider/model: `omp` / `opencode-go/muse-spark-1.3-contributor`; thinking `xhigh`; mode `full`; final status `idle`
- exact session: `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r21-lifecyclesmoke\2026-09-08T04-50-10-622Z_01a07f5a-2a3e-75ce-abfb-08454a505eee.jsonl`
- stable session: 21 lines; SHA256 `6e7f1517bf1dac95a82d80488400d571974d113adfa6e02860d9babec60312bb`
- wrapper log: 1 row / 471 bytes / SHA256 `b1c1b56220880fb02ed4d0423ace3fa2313d083124cb783547abecbdd9856f67`
- role access log: 9 rows / 2,576 bytes / SHA256 `e49eaee551903d92c7c5a744df8064b02d5c466626d7e120ffd6b24633c7925c`
- transcript: `role_smoke_probe=1`, `todo=5`, `role_write_chunk=0`; no forbidden tool call
- denies: `cross-role=1`, `unknown-resource=1`, `bad-target=1`
- exactly one allowed write to each `out/chunk_0.jsonl` through `out/chunk_5.jsonl`; each is 1 row / 59 bytes
- descendants0; fallback provenance proven; frozen verdict `LIFECYCLE_SMOKE_PASS`

Output SHA256 values: chunk0 `e7d2aecdf462de9a8918695e7adb70032f80c50205ce849b42664fe3877f24e9`, chunk1 `1e942823dc343829cab4c491ceee21ef4a6f8a54337ae32c5564bf5920b8d2f7`, chunk2 `90bdd8c64714150816c00c9ef40c6102d451dbf0102d3a3a698b204e7bfd090d`, chunk3 `c695e51a11fa40103355a84f95f15396616465d391bdeade92ec03db24244e1a`, chunk4 `d72b87b5d2fabbfd43d2b9b999bcd3cfcd4a6cfe251b44e21e5f97ce2f82de0f`, chunk5 `4d14e6c3ee466e96ff1daf257dbe26e3205070c197e97757e9f5e9fc90d953ff`.

The frozen lifecycle auditor re-ran after 12 seconds on the same evidence and returned the same PASS with the identical session line count/SHA and helper/output/descendant proof. A separate raw PowerShell read once encountered the preserved live wrapper's file lock; the frozen shared-read auditor remained stable and no relaunch or evidence mutation occurred.

## Independent post-run review and boundary

Two independent read-only reviewers returned PASS. They confirmed exact-one B agent/session/registry evidence, exact A+B total v9r21 registry count, descendants0, stable session/probe/access/output proof, unchanged Smoke A, no duplicate/retry, and that the remaining lifecycle wrapper process belongs to the intentionally preserved idle B agent.

Final reconciliation:

- complete registry: 321 parseable records, exactly one v9r21 Smoke-A record and one v9r21 Smoke-B record
- exact Smoke-B session directory: exactly one JSONL
- plan `9a3369a3...653ec` and mechanics59/59 unchanged; builder cache/pyc0
- no `PLAN_LOCK`, `FROZEN_HASHES`, run lock, source truth, candidate runtime, real freeze, or Phase C
- audit remains 4 rows / SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- protected dev/holdout paths remain absent; production `ml-service/` diff remains 0
- Smoke-A and Smoke-B agents/wrappers remain preserved; no stop/kill was issued

## Gate boundary

V9r21 has now consumed **Smoke A exactly once and PASSed** and **Smoke B exactly once and PASSed**. Both are permanently non-repeatable.

The next separate logical stage, if approved, is **real-freeze pre-gate + exactly-once real freeze only** using these preserved exact Smoke-A and Smoke-B proofs. Phase C, protected dev-v2 evaluation, holdout, and production remain prohibited until later gates.
