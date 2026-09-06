# Retrieval v3 D-110 — generation-v9r15 Phase-C CONTRACT_INVALID_GENERATION

Date: 2026-09-07
Stage: one-shot Phase-C execution closure
Generation: `retrieval-v3-dev-generation-v9r15`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260907-v9r15`

## Verdict

**v9r15 = HARD HOLD / CONTRACT_INVALID_GENERATION / NON-RESUMABLE / NON-REPAIRABLE.** The single authorized Phase-C execute coordinator was consumed exactly once. The frozen driver reached Author-1 and Author-1 eventually produced the complete 6x30 output shape, but its metadata-only role access log contains two denied write attempts. The frozen real-role contract requires zero denied helper accesses; frozen `audit_role_access.py` independently returns rc 3 on the first deny. No retry, same-generation repair, resumed driver, second execute coordinator, or manual continuation is permitted.

Preserve the v9r15 builder, run lock, source-truth snapshot, coordinator staging/session, Author-1 staging/session/access log/output as immutable failure evidence.

## Reconciled D-109 base

Immediately before the one-shot execute launch, repo branch `codex/retrieval-v3-user-search-quality` was at D-109 commit `c5f77b64854a2cb67d5cf98c44b3c1b2beb9ea20`, local/upstream/direct remote equal and clean. Production `ml-service/` diff remained zero and canonical audit remained 4 events SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`.

D-108 freeze remained exact: 67/67 pinned source/freeze entries rehash with zero mismatch throughout and after the failed execution.

## Single execute coordinator

Final duplicate-prevention check immediately before launch proved:

- execute staging absent
- expected execute session directory absent
- `phasec_driver.run.lock` absent
- Phase-C root absent/fresh
- matching v9r15 execute/Phase-C Paseo agents: 0

The frozen launcher then created exactly one execute coordinator:

- agent `1116cbcf-bc13-4466-b7a1-26409f3c1f06`
- cwd `C:\Users\joji\bc-v3-v9r15-coord-execute-20260907\cwd`
- provider `omp/opencode-go/muse-spark-1.3-contributor`
- thinking `xhigh`
- Parent null
- wrapper mode `execute`, custom tool `phasec_execute`, tools `todo`
- frozen controls `--tools=todo -e <frozen-ext> --no-extensions --no-skills --no-rules`
- coordinator extension SHA256 `cdae659da7616b2225837e8a6778f12006d490a32ceb79dbb4113272c800e1f7`

The caller-side post-launch verifier initially returned `PASEO_CLI missing and paseo not in PATH` from `launch_top_level_paseo` after the coordinator had already been created. No second launch was attempted. Actual staging/wrapper/agent/run-lock evidence immediately proved the launch had been consumed.

Frozen `audit_coord_smoke.py` on the preserved execute evidence returns rc 0 `SMOKE_PASS` in execute mode:

- exact session `C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r15-coord-execute-20260907-cwd\2026-09-06T16-36-02-109Z_01a07793-adbd-735d-a02c-555ee2ae6799.jsonl`
- final session lines: 10
- final session SHA256 `4634897e7f0aaa496bfa5cb557fc5a9cdfb5ab3fa86b5734ecb2a6231994801c`
- `phasec_execute=1`
- descendants 0
- fallback proven true

Thus the one-shot execute confinement/launcher contract itself succeeded. No duplicate execute launch occurred.

## Frozen driver progress

The frozen driver acquired `phasec_driver.run.lock` exactly once:

`{"started": "2026-09-06T16:36:09Z", "pid": 63520}`

It then completed the fresh read-only source-truth snapshot and mechanical anchors before Author-1:

- source-truth rows: 13,589
- sources: gov24 10,958; youth 2,631
- `source_truth.jsonl` bytes: 75,207,689
- source-truth SHA256 `9fe194653a4b5c9c688364aa9ae686996cb7cabfebd446a6b9a7e8895374c1a5`
- `source_truth_meta.json`, `anchors.json`, `slots_1.json`, `slots_2.json`: present
- no vector/chunk/ranking query was used by the snapshot procedure

## Author-1 evidence and hard failure

Exactly one Author-1 top-level role was launched:

- agent `0cfa383a-3101-4d4f-9e56-1968fc2b2c49`
- cwd `C:\Users\joji\bc-v3-v9r15-phaseC\author1`
- provider Muse Spark 1.3 contributor, xhigh
- role wrapper exact-one row, kind `author1`, tools `todo`
- frozen role extension SHA256 `6b5a1f426752e403a7ba96585b263cedd0bb9aea3646779a37c6a4bad3e62534`
- final Author-1 session: 542 lines
- Author-1 session SHA256 `7b1126624c3526596ec3593ad6a3a23ffbd915b0c60bccdd86fa7615efee1df3`

Author-1 ultimately produced all six required chunks, each exactly 30 rows:

- `chunk_0.jsonl` SHA256 `71d9cca14d65453029bffc2bf891582719c8b434367fcbe30da470294e83e746`
- `chunk_1.jsonl` SHA256 `51afdcebe59e35e9a79c01215d012c436f9680ad1908447142cc5d71b3ab7f19`
- `chunk_2.jsonl` SHA256 `c58162d6ae70ffcfc1c86843921c80e90f6e7fd22a0d0b7d3aac358342935dc7`
- `chunk_3.jsonl` SHA256 `d9a1d93af80c6b898ff5d7decb3a32b989f5d7108b50c42c5dec1b933ea7c440`
- `chunk_4.jsonl` SHA256 `4b106416a97dbfa1fb11068d154b3de36c14fc4f311ae09520d7b4470e03915e`
- `chunk_5.jsonl` SHA256 `d6274064ea09e15c961e1ba925a26692742a8d8fd237aa0e419a0c7fff8d0bd3`

However the metadata-only access log contains two denied writes before those valid outputs:

1. `role_write_chunk`, path `chunk_0.jsonl` -> `DENY:bad-target: not an exact chunk target`
2. `role_write_chunk`, path `out/chunk_0.jsonl` with 2 rows -> `DENY:shape: rows=2 != 30 for author1`

The frozen real-role contract requires zero denied accesses. Independent frozen re-audit:

`audit_role_access.py ... author author1` -> rc 3

`CONTRACT_INVALID_GENERATION: access log deny present line 217: role_write_chunk/DENY:bad-target: not an exact chunk target`

The later successful 6x30 writes do not erase an earlier deny. The driver therefore stopped at the Author-1 post-completion audit gate before any collect/merge.

## Exact stop boundary

Present failure evidence:

- `phasec_driver.run.lock`
- source-truth snapshot/meta
- anchors/slots
- Phase-C staging root containing only `author1`
- Author-1 wrapper/access/session/output evidence

Absent / never reached:

- `author_chunks`
- `author1_candidates.jsonl`
- Author-2 staging/session/output
- `author2_candidates.jsonl`
- `candidates_merged.json`
- reviewer A/B staging or raw output
- `frozen_raw_A/B`
- packet keymaps
- agreement/disagreement artifacts
- C staging/output
- adjudicated pool
- selector output
- `evalset.jsonl`
- final manifest/provenance/sealed output
- protected dev-v2 evaluation
- holdout evaluation
- production change
- canonical audit append

All 67 D-108 frozen/pinned entries remain byte-exact with zero mismatches.

## Closure / next rule

Do not delete or rewrite the v9r15 runtime evidence. Do not remove the run lock to resume. Do not send repair instructions to Author-1. Do not launch Author-2 manually. Do not launch another execute coordinator. Do not patch v9r15 frozen bytes.

If Retrieval v3 generation work continues, it requires a fresh successor generation with a new private builder and a pre-execution contract decision about whether rejected helper calls must be fatal or whether role prompts/mechanics must deterministically prevent malformed preliminary writes. Any successor must preserve v9r15 as immutable failure evidence and must not reuse v9r15 authored query/candidate rows as semantic material.
