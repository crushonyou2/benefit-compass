# Retrieval v3 D-132 — generation-v9r21 PRE-SMOKE Web PASS

Date: 2026-09-08
Stage: fresh successor PRE-SMOKE construction + same-stage blocker repair + independent Web review
Generation: `retrieval-v3-dev-generation-v9r21`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r21`
D-131 base commit: `e93c258a314065c75120dcdbb9f165ca28ba3295`

## Verdict

**D-132 / v9r21 PRE-SMOKE: WEB PASS.**

V9r21 is a fresh successor to D-131. It repairs only the v9r20 pre-freeze exactly-once/rerun-prevention defect, corrects the stale Smoke-A lock-note description, and advances fresh generation identity/lineage. Retrieval/evaluation semantics, rubric, counts, quotas, selector, role-confinement semantics, D-123 slot/location binding, TWELVE fingerprint exclusions, and protected-data boundaries remain unchanged.

No v9r21 Smoke A/B, real freeze, source-truth snapshot, Phase C, Author/Reviewer/C, selector, protected evaluation, holdout evaluation, production change, or canonical audit append occurred in D-132.

The next separate gate may consume exactly one v9r21 Smoke A on these final bytes after a fresh duplicate/runtime/provenance reconciliation. Smoke B remains conditional on a later stable Smoke-A PASS stage.

## Reconciled base

Before successor construction:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `e93c258a314065c75120dcdbb9f165ca28ba3295`
- D-131 commit time `2026-09-08T06:40:36+09:00` / `2026-09-07T21:40:36+00:00`
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- canonical audit exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- main-tree protected `eval/retrieval-v3/dev/` and `eval/retrieval-v3/holdout/` absent
- actual OMP `18.1.13`; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`
- exact bundled Paseo CLI/daemon `0.7.2`, daemon running/reachable
- fresh v9r21 destination absent; expected Smoke-A/Smoke-B session roots absent
- v9r20 remains D-131 immutable failure evidence; no v9r20 real-freeze artifacts exist

## Sole implementation executor

Approved local implementation was performed end-to-end by one Paseo/OMP stage-machinery agent:

- agent `59e9f9ba-f0e3-45ad-b6ee-35e413915706`
- title `D132 successor mechanics implementation`
- ParentAgentId null
- cwd = main repo
- provider/model `omp` / `opencode-go/muse-spark-1.3-contributor`
- thinking `xhigh`, mode `full`, final status `idle`
- initial implementation prompt SHA256 `4ccf81b7f36050185990b03d0e98538a92b110ef9f1e27c184b1b0dca1738bfa`
- same-stage concurrency-repair prompt SHA256 `9b962887fe33cbafeafb0739f4599b8a030d2fe8087f0717a8333ef9bd187ef2`

This agent is implementation machinery, not generation Smoke/role/Phase-C evidence. Its title/cwd intentionally do not claim a v9r21 generation execution.

## Fresh v9r21 identity and exclusions

Final builder identity:

- plan version `retrieval-v3-dev-generation-v9r21`
- seed `benefit-compass-retrieval-v3-dev-v2-generation-v9r21-2026-09-08`
- candidate IDs `v3g9r21-001..360`
- C IDs `v9r21c-001..360`
- freeze hold/provenance base D-131 `e93c258a314065c75120dcdbb9f165ca28ba3295`

V9r20 produced zero Author/query rows, so it creates **no thirteenth fingerprint exclusion set**. Final plan retains exactly the existing TWELVE query-overlap sets:

`dev_v1`, `holdout`, `history`, `d070`, `d071`, `d072`, `d074`, `d076`, `d082`, `d086`, `d117`, `d123`.

Permanent TWELVE regression independently re-ran 66 pairwise comparisons with overlap 0 and counts `180/250/248/273/273/360/360/365/360/360/360/360`.

## D-131 exactly-once freeze repair

Final frozen mechanic `freeze_plan_v9r21.py`:

- adds `PLAN_LOCK.json` and `FROZEN_HASHES.json` to `ABSENT_AT_FREEZE`;
- publishes both freeze artifacts only through `exclusive_write_bytes`, using `os.open(..., O_CREAT|O_EXCL, ...)`;
- contains no overwrite `write_bytes` path for either freeze artifact;
- rejects any second invocation once either freeze artifact exists;
- removes the stale “same frozen_at reproduces identical bytes” statement and instead records rerun rejection;
- corrects the future Smoke-A lock note to the actual neutral deterministic contract: exactly one `phasec_probe` and no other tool call.

At the successful-publication boundary, exclusive creation of `PLAN_LOCK.json` is the first persistent freeze artifact and therefore the atomic publication claim. A second/concurrent publisher cannot truncate or replace it.

New permanent mechanic `test_freeze_rerun_rejection.py` proves the production path on disposable builders only:

- first synthetic contract-valid freeze succeeds;
- identical second invocation fails rc3 with first `PLAN_LOCK`/`FROZEN_HASHES` bytes unchanged;
- preexisting `PLAN_LOCK` alone rejects;
- two separate Python processes run the real `freeze_plan_v9r21.main()` against one disposable builder;
- a harness-only barrier wraps the production exclusive-write helper so both processes contend at the PLAN_LOCK publication boundary;
- exactly one process succeeds and one fails rc3 (`[0,3]`);
- one coherent lock/hash artifact set remains and binds the race sentinel;
- artifact bytes remain stable after both processes exit;
- a subsequent rerun still rc3 with winner artifacts byte-identical;
- real v9r21 builder remains free of freeze artifacts.

Web initially HOLDed the executor's first candidate because the new test only proved sequential rerun rejection. The same executor repaired this within the same PRE-SMOKE logical stage before any model smoke was consumed. Final rerun regression: **`FREEZE_RERUN_REJECTION_PASS`, 38 checks.**

## Independent Web final-byte validation

Web independently re-ran the final v9r21 static/pre-smoke battery:

- Paseo exact-CLI gate: `PASEO_CLI_GATE_PASS` — 64 checks
- role writer preflight: `PREFLIGHT_PASS` — 36 checks
- launcher reachability: `REACHABILITY_PASS` — 87 checks
- lifecycle contract: `LIFECYCLE_CONTRACT_PASS` — 53 checks
- role tools/Bun probe: `ROLE_TESTS_PASS` — 172 checks
- role completion gate: `GATE_TESTS_PASS`
- Phase-C confinement, py_compile and tsc gate: `CONFINEMENT_TESTS_PASS` — 212 checks
- freeze binding: `FREEZE_BINDING_PASS` — 66 checks
- freeze rerun/concurrency: `FREEZE_RERUN_REJECTION_PASS` — 38 checks
- staging exact set: `STAGING_EXACT_SET_PASS` — 24 checks
- TWELVE gates: 66 pairwise comparisons, overlap 0
- slot/location: 6 positive / 5 negative; mutation failure `slot_location_mismatch`
- registry descendant scan: `REGISTRY_SCAN_PASS` — 37 checks, including >200 and Windows reparse/root-junction fail-close coverage

Final `GENERATION_PLAN.author_isolation.mechanics_shas` map matches disk byte length + SHA for every entry: **59/59 exact, mismatch 0**.

## Final hashes and hygiene

- `GENERATION_PLAN.json`: 65,857 bytes; SHA256 `9a3369a3dada669a2cd448f59ceaf41982fb94fc11029b20d2431f72430653ec`
- `input/EXCLUSION_INPUTS.json`: SHA256 `518292880dbdf24335eb2412204e62582d3abf0a73e3a2276f01dac9d3b08b59`
- `RUBRIC.json`: SHA256 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- `freeze_plan_v9r21.py`: SHA256 `65ba9208033526052db0d77e90dd14145a7dcb3c391c9cad87b2d17ec1a2bcf4`
- `test_freeze_rerun_rejection.py`: SHA256 `28f5383e9f8476604997055e048f5bfdd96a92c22e1d086769e51c74b083dd86`
- builder files: 74
- mechanics: 59/59 exact
- builder `__pycache__` / `.pyc`: 0 after exact-path cleanup
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`: absent
- v9r21 Smoke-A root/session: absent
- v9r21 Smoke-B root/session: absent
- v9r21 Phase-C root: absent
- complete local Paseo registry: 319 parseable JSON records, v9r21 title/cwd generation matches 0

V9r20 predecessor remains immutable at plan SHA `4baf17f208db63a27948cf1b11ac88f87b052f0f8db7f0f5468a1267023be542` and freeze-mechanic SHA `ac1460d6229686901828458ac7a7274be98babfc46ca7b39f6adb853b5dc3336`.

## Gate boundary

**D-132 PRE-SMOKE PASS only.** No v9r21 model smoke has been consumed.

Next separate logical stage: fresh duplicate/runtime/provenance reconciliation, then **exactly one v9r21 Smoke A** on these final bytes. If Smoke A fails, v9r21 closes `CONTRACT_INVALID_GENERATION` with no same-generation repair/retry/re-smoke. Smoke B, real freeze, Phase C, protected dev-v2, holdout, and production remain prohibited until their later gates.
