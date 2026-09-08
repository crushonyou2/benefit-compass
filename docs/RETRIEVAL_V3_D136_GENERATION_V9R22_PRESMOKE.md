# Retrieval v3 D-136 — generation-v9r22 PRE-SMOKE Web PASS

Date: 2026-09-08
Stage: fresh successor PRE-SMOKE construction + same-stage blocker repairs + independent Web review
Generation: `retrieval-v3-dev-generation-v9r22`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r22`
D-135 base commit: `c68bfdfa302cc9509e6838542cfd1f2f7ba6157a`

## Verdict

**D-136 / v9r22 PRE-SMOKE: WEB PASS.**

V9r22 is a fresh successor to the immutable D-135/v9r21 real-freeze failure. It repairs the D-135 false-`frozen_at` provenance defect before any v9r22 Smoke is consumed, preserves the v9r21 O_CREAT|O_EXCL exactly-once publication contract, advances fresh generation identity/lineage, and strengthens the production old-builder path deny list through v9r21.

Retrieval/evaluation semantics, rubric, final/reserve/location counts, authoring contracts, A/B-all-360, C-every-360, agreement diagnostics, exact selector, D-123 slot/location binding, D-117 staging exact-set semantics, D-112 exact bundled Paseo CLI provenance, D-110 writer envelope, TWELVE fingerprint exclusions, complete registry descendant proof, and protected-data boundaries remain unchanged.

No v9r22 Smoke A/B, real freeze, source-truth snapshot, Phase C, Author/Reviewer/C, selector, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append occurred in D-136.

The next separate gate may perform a fresh duplicate/runtime/provenance reconciliation and then consume **exactly one v9r22 Smoke A** on these final bytes. Smoke B, real freeze, Phase C, protected dev-v2, holdout, and production remain prohibited until later gates.

## Reconciled D-135 base

Before successor construction and again after final validation:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `c68bfdfa302cc9509e6838542cfd1f2f7ba6157a`
- D-135 commit time `2026-09-08T14:24:39+09:00` / `2026-09-08T05:24:39+00:00`
- working tree clean before D-136 durable documentation; `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- canonical audit exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- main-tree protected `eval/retrieval-v3/dev/` and `eval/retrieval-v3/holdout/` absent
- actual OMP `18.1.13`; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`
- exact bundled Paseo `0.7.2`
- fresh v9r22 destination and expected Smoke-A/Smoke-B roots were absent at stage start

V9r21 remained immutable throughout D-136:

- `GENERATION_PLAN.json` 65,857 bytes SHA256 `9a3369a3dada669a2cd448f59ceaf41982fb94fc11029b20d2431f72430653ec`
- `freeze_plan_v9r21.py` SHA256 `65ba9208033526052db0d77e90dd14145a7dcb3c391c9cad87b2d17ec1a2bcf4`
- `PLAN_LOCK.json` 25,208 bytes SHA256 `82196b602eab22df4a7484484399732db39dfaffdcc839b106a580305118c19f`
- `FROZEN_HASHES.json` 7,320 bytes SHA256 `4d6d7e9c0218578cf9b1457cd22ea10ba8b3dde36083f57fcd75d25219c44096`
- the 75 v9r21 frozen entries independently remain missing 0 / mismatch 0

## Sole implementation executor

Approved private-builder implementation was performed end-to-end by one Paseo/OMP stage-machinery agent:

- agent `d165d03b-9e36-4c1c-bfaa-c1f592e749ab`
- title `D136 successor mechanics implementation`
- ParentAgentId null
- cwd = main repo
- provider/model `omp` / `opencode-go/muse-spark-1.3-contributor`
- thinking `xhigh`, mode `full`, final status `idle`
- initial implementation prompt SHA256 `fa4edab5ce3f6d260942bf4473f1d787df6bfe11abe1028ba39101d9827574ae`

This agent is implementation machinery, not v9r22 Smoke/role/Phase-C evidence. Its title/cwd deliberately do not claim a v9r22 generation execution.

## Fresh identity and exclusions

Final v9r22 identity:

- plan version `retrieval-v3-dev-generation-v9r22`
- seed `benefit-compass-retrieval-v3-dev-v2-generation-v9r22-2026-09-08`
- candidate IDs `v3g9r22-001..360`
- C IDs `v9r22c-001..360`
- freeze hold/provenance base `c68bfdfa302cc9509e6838542cfd1f2f7ba6157a`
- freeze hold time `2026-09-08T05:24:39+00:00`

V9r21 produced zero Author/query rows, so it creates **no thirteenth fingerprint exclusion set**. V9r22 retains exactly the existing TWELVE query-overlap sets:

`dev_v1`, `holdout`, `history`, `d070`, `d071`, `d072`, `d074`, `d076`, `d082`, `d086`, `d117`, `d123`.

All twelve individual fingerprint payload files are byte-identical to v9r21. The exclusion manifest's operative `inputs`, `overlap_gates`, and `required_query_overlap` values are unchanged; only fresh-generation descriptive identity advances. Permanent TWELVE validation rechecked all 66 pairs with overlap 0 and counts `180/250/248/273/273/360/360/365/360/360/360/360`. Failed-generation gold exclusions were not added; canonical gold exclusions remain dev-v1/holdout/history only.

## D-135 timestamp-truthfulness repair

Final `freeze_plan_v9r22.py` captures one `observed_now_utc` immediately after argument parsing and before any persistent freeze write.

The effective freeze time is now mechanically constrained:

- omitted `--frozen-at` derives from that single observed UTC instant;
- supplied values must parse as timezone-aware UTC with zero offset;
- malformed, naive, and non-zero-offset values fail rc3;
- supplied values strictly later than the observed entry instant fail rc3 with **no positive tolerance**;
- effective `frozen_at` must be strictly later than the parsed D-135 hold base time;
- timestamp/hold comparisons use parsed datetimes, not lexicographic string ordering;
- all of these gates execute before `PLAN_LOCK.json` or `FROZEN_HASHES.json` publication.

Exactly-once publication from v9r21 remains standing: `PLAN_LOCK.json` and `FROZEN_HASHES.json` are in `ABSENT_AT_FREEZE`, and both are published only via the existing exclusive `O_CREAT|O_EXCL` helper with no overwrite path.

The permanent rerun/timestamp regression now proves on disposable copies only:

- `+1s` future timestamp -> rc3, no publication;
- naive timestamp -> rc3, no publication;
- non-zero UTC offset -> rc3, no publication;
- malformed timestamp -> rc3, no publication;
- at-hold-base and before-hold-base -> rc3, no publication;
- explicit after-hold past timestamp -> successful disposable freeze;
- omitted timestamp -> successful disposable freeze derived from observed UTC;
- sequential rerun rejection with first artifacts unchanged;
- preexisting lock-only rejection;
- genuine two-process publication race -> exactly one rc0 and one rc3 (`[0,3]`), with stable winner bytes;
- real v9r22 builder remains without freeze artifacts.

Final result: **`FREEZE_RERUN_REJECTION_PASS`, 66 checks.**

## Same-stage corrections before final PASS

Web did not accept the first implementation candidate blindly. All corrections below occurred before any v9r22 Smoke/model generation evidence was consumed.

### Strict-time correction

The executor's first draft allowed a five-second future tolerance and coerced a naive timestamp to UTC. Web classified that as contrary to D-135's truthfulness requirement and required the same executor to remove the tolerance, reject naive/non-UTC values, and bind the default to one observed entry instant. The final 66-check regression above proves the corrected behavior.

### Production old-builder token correction

Independent Web review then found that `test_phasec_confinement.py` expected v9r20/v9r21 old-token exclusion while the production `role_fs_helper.py` `OLD_TOKENS` still ended at v9r19. Because the final plan claimed old-builder filesystem/provenance paths were denied through the predecessor, this was an operative PRE-SMOKE consistency blocker.

The same executor repaired it before Smoke:

- production helper now includes v9r20 and v9r21 in all seven existing immediate-predecessor token families: bare `v9r*`, `v3g*`, `v9r*c`, dated `20260908-*`, `bc-*`, `bc-v3-*`, and full `bc-v3-dev-v2-builder-20260908-*`;
- the existing `resolve_fixed` deny path enforces those tokens before fixed-target filesystem access;
- semantic strings containing historical generation text remain allowed as before;
- plan `role_filesystem_confinement.reads_searches` now truthfully records `v9r6..v9r21` filesystem/provenance denial;
- `test_role_tools.py` now AST-extracts the **production** helper's `OLD_TOKENS`, requires all fourteen v9r20/v9r21 family tokens, invokes production `resolve_fixed` for each, and checks the plan claim.

Role-tools regression therefore strengthened from 172 to **202 checks** without changing semantic role behavior.

## Disclosed pre-publication real-builder probes

During the implementation pass, before Web explicitly prohibited any further real-builder freeze entry during PRE-SMOKE, the executor invoked `freeze_plan_v9r22.py --builder <real-v9r22>` twice as precondition probes:

1. first rc3 on an accidental CRLF condition before publication;
2. second rc3 at mandatory `smoke A pinning required`, also before publication.

Immediate and repeated reconciliation proved both attempts crossed **no persistent freeze publication boundary**:

- `PLAN_LOCK.json` absent
- `FROZEN_HASHES.json` absent
- `phasec_driver.run.lock` absent
- source truth absent
- no model/Smoke launched
- no protected/audit/production state changed

After Web correction, the real v9r22 freeze entry was not invoked again in D-136; all successful synthetic freeze tests used disposable copies only. Independent review classified the two rc3 probes as **non-consuming same-stage process deviations**, not one-shot freeze consumption, because no O_EXCL publication occurred. This is consistent with the D-108 precedent where a pre-write rc3 with lock/hash absent did not consume the later unchanged real freeze. The probes must not be repeated.

## Semantic preservation

Web and independent reviewers compared v9r22 with v9r21. Exact JSON-value equality remains for the core plan sections:

`final_counts`, `reserve_counts`, `reserve_factor`, `authoring_contracts`, `a_b_packets`, `a_b_protocol`, `agreement_diagnostics`, `c_packets`, `c_protocol`, `disagreement_bundle`, `final_selector`, `mechanical_validators`, `raw_freeze_lifecycle`, `standing_contract`, and `rubric`.

After only fresh-identity normalization, generation author assignment, isolation, coordinator/reviewer confinement, and author-isolation semantics are equal except for the authorized old-builder deny strengthening and refreshed mechanics SHA pins. Core generation/search/evaluation/selection mechanics likewise normalize to v9r21 identity except the D-135 timestamp/rerun repair, predecessor-token strengthening, and associated tests/pins.

## Independent Web final-byte validation

Web independently re-ran the final v9r22 static/PRE-SMOKE battery after all same-stage repairs:

- Paseo exact-CLI gate: `PASEO_CLI_GATE_PASS` — 64 checks
- role writer preflight: `PREFLIGHT_PASS` — 36 checks
- launcher reachability: `REACHABILITY_PASS` — 87 checks
- lifecycle contract: `LIFECYCLE_CONTRACT_PASS` — 53 checks
- role tools/Bun/helper proof: `ROLE_TESTS_PASS` — **202 checks**
- role completion gate: `GATE_TESTS_PASS`
- Phase-C confinement / compile/type gate: `CONFINEMENT_TESTS_PASS` — 212 checks
- freeze binding: `FREEZE_BINDING_PASS` — 66 checks
- strict timestamp + rerun/concurrency: `FREEZE_RERUN_REJECTION_PASS` — 66 checks
- staging exact set: `STAGING_EXACT_SET_PASS` — 24 checks
- TWELVE gates: 66 pairwise comparisons, overlap 0
- slot/location: 6 positive / 5 negative; mutation failure `slot_location_mismatch`
- registry descendant scan: `REGISTRY_SCAN_PASS` — 37 checks

Final `GENERATION_PLAN.author_isolation.mechanics_shas` matches every listed disk file by byte length and SHA256: **59/59 exact, mismatch 0**.

Two independent read-only reviewers then re-reviewed the latest stable final bytes after the old-token correction and both returned **PASS / no operative blocker**. They independently confirmed fresh identity/exclusion semantics, D-135 timestamp truthfulness, O_EXCL exactly-once mechanics, production helper/test alignment, semantic preservation, 59/59 binding, repo/protected/production boundaries, no v9r22 runtime artifacts, and immutable v9r21 evidence.

## Final hashes and hygiene

- `GENERATION_PLAN.json`: 66,960 bytes; SHA256 `58c862958dc2167b3a2ca7dab9ddb94af8f0c8a57fff307cd6cd89d354a821f3`
- `input/EXCLUSION_INPUTS.json`: 2,986 bytes; SHA256 `df59034f3d6022d7be89268d6bd642cbcd6c0b8d4fa553364801b18c85399ddc`
- `RUBRIC.json`: 3,334 bytes; SHA256 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- `freeze_plan_v9r22.py`: 90,090 bytes; SHA256 `9d59c80e14e10c237bf2ea56e50b5bb3278160867df6efa71325aa7552c8f769`
- `test_freeze_rerun_rejection.py`: 29,614 bytes; SHA256 `da19561ea5b88c035eed521bfd3e5b587f19082730e9a39aacee17f8ed4af20a`
- `role_fs_helper.py`: 26,293 bytes; SHA256 `84bb969a7abcbc8f0ab5724abaea21cfc2e073b587e206fa52b93efd0da03f8b`
- `test_role_tools.py`: 34,397 bytes; SHA256 `8917b0f4fd420aa8970dab35151e89f50b376756cb8ee294479840d659774834`
- builder files: 74
- mechanics: 59/59 exact
- builder `__pycache__` / `.pyc`: 0 after exact-path cleanup of Web-test caches
- `PLAN_LOCK.json`, `FROZEN_HASHES.json`, `phasec_driver.run.lock`, `source_truth.jsonl`: absent
- staging-like directories: absent
- expected v9r22 Smoke-A/Smoke-B roots: absent
- OMP session directories containing `v9r22`: 0
- complete local Paseo registry: 323 parseable JSON records, parse errors 0, v9r22 generation-token matches 0

The only CR-containing files after final cleanup are the two predecessor inputs that were restored byte-identical to v9r21: `input/failed_d076_query_fingerprints.json` and `input/history_catalog.json`.

## Gate boundary

**D-136 PRE-SMOKE PASS only. No v9r22 Smoke has been consumed.**

Next separate logical stage: fresh duplicate/runtime/provenance reconciliation, then **exactly one v9r22 Smoke A** on these final bytes. If that one-shot Smoke A fails, close v9r22 according to the standing one-shot contract; do not repair/retry/re-smoke on consumed final bytes. Smoke B, real freeze, Phase C, protected dev-v2, holdout, and production remain prohibited until their later gates.
