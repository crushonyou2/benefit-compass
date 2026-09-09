# Retrieval v3 D-168 — generation-v9r29 one-shot Smoke B PASS

Date: 2026-09-10 (KST)
Stage: Smoke B fresh pre-gate + exactly-one lifecycle execution + stability re-audit + durable closure
Generation: `retrieval-v3-dev-generation-v9r29`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260910-v9r29`
D-167 Smoke-A closure base: `09a3f0cec1b9969bb1cb92c528bc9a6fee259f76`

## Verdict

**D-168 / v9r29 SMOKE B PASS.** The D-167 final v9r29 bytes passed the fresh Smoke-B duplicate/runtime/provenance pre-gate and consumed exactly one actual lifecycle Smoke B through frozen `run_lifecycle_smoke.py`. The runner's embedded frozen audit returned `LIFECYCLE_SMOKE_PASS`; after 15 seconds, frozen `audit_lifecycle_smoke.py` re-audited the same preserved evidence and returned the same PASS.

Smoke A remains permanently consumed exactly once and was re-audited unchanged after Smoke B. Smoke B is now also permanently consumed exactly once. No second Smoke-A or Smoke-B launcher process was started.

**STOP boundary:** no real freeze, source-truth snapshot, Phase C, semantic Author/Reviewer/C generation, protected dev-v2/holdout evaluation, production change, or canonical audit append occurred. Next stage requires separate authorization for real-freeze pre-gate + exactly-one real freeze.

## Fresh prelaunch gate

- branch `codex/retrieval-v3-user-search-quality`
- local HEAD = upstream = direct origin `09a3f0cec1b9969bb1cb92c528bc9a6fee259f76`; working tree clean; `git diff --check` PASS
- OMP `18.1.13`; bundled Paseo `0.7.2`; global default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`; no repo `.omp` or relevant ambient override
- Smoke A frozen re-audit: rc0 `SMOKE_PASS`, session 10 lines SHA256 `c5e29e457c6a657c951246f2056f79b4c8b5f96adc40131cc06ad30a139f8b0f`, `phasec_probe=1`, descendants 0, fallback proven
- v9r29 primary hashes 10/10 exact; mechanics 69/69 exact
- lifecycle runner SHA256 `686f1ee2b05d9842a14e6fcca48a3c62e2d9f4043054f8446e6759cca4576013`
- Smoke-B root and exact OMP session directory absent before execution; Phase-C/downstream/freeze artifacts absent
- audit remained 4 rows SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`; protected dev/dev-v2/holdout absent; `ml-service` diff0; v9r28 key8/8 exact

Fresh static/non-model battery PASS on final bytes: lifecycle53, role-tools267, completion gate PASS, confinement253, reachability87, Paseo CLI64, registry37, preflight36, staging41, freeze binding120, rerun rejection66, FIFTEEN15/105/0, D149 358/360/2, D150-7, D156-9, slot/location6+5. The battery created exactly 2 builder-local `__pycache__` dirs / 51 pyc; only those exact resolved-under-builder dirs were removed and PowerShell/.NET-only verification restored cache0/pyc0 with final bytes unchanged.

## Exactly-one Smoke B

Frozen runner invocation:

`python -B run_lifecycle_smoke.py`

The single Core `exec_command` remained live past its 30-second yield. Only that same process session was polled to its terminal rc0 result; no replacement, retry, correction, or second lifecycle-runner process occurred.

Observed provenance:

- agent `0e4ae1f5-8ed9-42ce-9a3a-ced18817e2c1`
- title `v9r29-lifecyclesmoke`
- cwd `C:\Users\joji\bc-v3-v9r29-lifecyclesmoke`
- ParentAgentId `null`
- provider/model `omp` / `opencode-go/muse-spark-1.3-contributor`; thinking `xhigh`; mode `full`; final status `idle`
- exact OMP session `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r29-lifecyclesmoke\2026-09-09T19-36-54-940Z_01a087ac-5b9c-7430-8dc1-6efaa3904fb0.jsonl`
- session 15 lines, SHA256 `9abc5e96090f35696a92540318d2507eaa4ff61d610cbf045ba36bc6d99a3a85`
- `role_smoke_probe=1`, `todo=2`; expected deny triple `cross-role=1`, `unknown-resource=1`, `bad-target=1`
- exactly six one-row/59-byte outputs with frozen SHAs: `e7d2aec...`, `1e94282...`, `90bdd8c...`, `c695e51...`, `d72b87b...`, `4d14e6c...`
- role access log 9 rows / 2792 bytes / SHA256 `e4b4211fe85b584580aacf95813accdc1d45732dadbd54ab1a30a5de0ab897d6`
- wrapper log 471 bytes / SHA256 `af9bc6d625ca1ae3d218578073fc80e6feba97226fff36eda42fa343f2174598`
- descendants 0; fallback proven

Runner embedded audit: rc0 `LIFECYCLE_SMOKE_PASS`.

After a 15-second stability interval, the same frozen auditor returned rc0 `LIFECYCLE_SMOKE_PASS` on the identical agent/session/wrapper/access/output evidence. No model or second lifecycle runner was launched by this re-audit.

## Post-Smoke boundary

- Smoke A re-audited after Smoke B and remained the same rc0 `SMOKE_PASS` on its 10-line SHA `c5e29e457c6a657c951246f2056f79b4c8b5f96adc40131cc06ad30a139f8b0f`
- complete local registry: 370 records, 0 parse errors, 0 duplicate IDs; Smoke A and Smoke B each title/cwd/both exactly 1/1/1
- exact Smoke-B session directory contains exactly one JSONL
- runtime/auditor imports left 2 cache dirs / 3 pyc; only those exact two builder-local `__pycache__` dirs were removed; final cache0/pyc0
- v9r29 primary 10/10 and mechanics 69/69 exact; downstream/freeze/source artifacts0
- canonical audit4 unchanged; protected paths absent; `ml-service` diff0; v9r28 key8/8 exact

## Gate boundary

V9r29 has now consumed **Smoke A exactly once and PASSed** and **Smoke B exactly once and PASSed**. Both are permanently non-repeatable for this generation.

**D-168 SMOKE B PASS. STOP before real freeze.** A next separately explicit continuation may authorize only fresh real-freeze preflight + exactly-one real freeze. Source truth, Phase C, semantic roles, protected dev-v2, holdout, production, and canonical audit append remain prohibited.
