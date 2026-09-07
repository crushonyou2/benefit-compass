# Retrieval v3 D-127 — generation-v9r20 PRE-SMOKE Web PASS

Date: 2026-09-08
Stage: fresh-successor mechanics repair / independent pre-smoke gate
Generation: `retrieval-v3-dev-generation-v9r20`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r20`
Hold base / predecessor closure: D-126 commit `b9a129b549fbca018fc849df1ec90ca5262bbc7e`

## Verdict

**PRE-SMOKE PASS.** V9r20 is a fresh successor to permanently closed v9r19. The D-126 descendant-proof defect is repaired on fresh bytes without changing retrieval/evaluation semantics, rubric, counts, protected-data boundaries, exclusion-set contents, selector rules, or production code.

This record authorizes no smoke by itself beyond defining the next separately gated boundary. **No v9r20 Smoke A or Smoke B has been consumed.** No real freeze, Phase C, source-truth snapshot, Author/Reviewer/C role generation, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append occurred in this stage.

The next logical stage must first re-run duplicate/runtime/provenance gates and may consume **exactly one final-byte Smoke A only**. Smoke B remains conditional on a separately established stable Smoke-A PASS. Any smoke failure closes v9r20; no same-generation repair/retry.

## Reconciled base and provenance

Immediately before the final Web verdict:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `b9a129b549fbca018fc849df1ec90ca5262bbc7e` before this D-127 record
- pre-record working-tree delta was only the append-only implementation-stage `memory/SESSION-LOG.md` entry
- `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- main-tree `eval/retrieval-v3/dev/` and `eval/retrieval-v3/holdout/` plaintext paths absent
- canonical audit exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- actual OMP binary `omp/18.1.13`
- effective OMP default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`
- exact bundled Paseo CLI `C:\Users\joji\AppData\Local\Programs\Paseo\resources\bin\paseo.cmd`, version `0.7.2`
- Paseo daemon `running/reachable`

A single OMP/Paseo implementation executor, agent `59c723d9-ba0d-44aa-a722-1f3c19fec454`, built and validated the fresh successor as stage machinery. It was not a v9r20 generation Smoke/role/Phase-C agent. Before this verdict its display name was changed to `D127 presmoke successor implementation`, removing the `v9r20` token so future generation duplicate gates are not polluted by implementation metadata.

## D-126 defect and narrow successor repair

D-126 closed v9r19 after exactly one Smoke B because the frozen lifecycle auditor fail-closed at the mandatory descendant-listing parse: `agent listing unparseable; descendants unprovable`. Independent Web diagnosis found a deeper completeness defect than parsing alone:

- exact bundled `paseo ls --json` / global-all listing is capped at exactly **200** returned agents on this installation;
- the exact local Paseo registry `C:\Users\joji\.paseo\agents\*\*.json` contains **316** parseable agent metadata records at final review;
- installed Paseo 0.7.2 code derives `ParentAgentId` from canonical metadata label `paseo.parent-agent-id`;
- therefore tolerant CLI JSON parsing would still be insufficient to prove descendants = 0.

V9r20 removes the capped CLI listing from the mandatory descendant-completeness proof. The shared Phase-C helper now performs a complete exact local-registry metadata scan:

- exact registry root `C:\Users\joji\.paseo\agents`
- canonical parent label `labels["paseo.parent-agent-id"]`
- sorted traversal of every per-cwd registry directory and every `.json` agent metadata record
- filename stem must bind exactly to record `id`; duplicate ids fail closed
- malformed/unreadable/non-object records, malformed labels/parent values, missing ids, path escape, unexpected leaf/entry shape, and missing/unreadable root fail closed
- both top-level entries and leaves use the existing Windows reparse-aware `_is_link()` check (`is_symlink` plus `st_file_attributes & 0x400`), so junction/reparse points fail closed
- inspect-side strict-if-present children check remains in addition to the complete registry scan
- callers report child counts only; titles or unrelated metadata are not logged
- `find_daemon_children` and `paseo(["ls", "--json"])` are absent from the descendant-completeness path

The same repaired helper is used by the production Phase-C path and the coordinator, lifecycle-smoke, and role-access auditors.

The permanent registry regression contains a >200 case: 205 decoys plus a matching child sorted after position 200 must still be found. Final test coverage also includes a deterministic Windows junction (`mklink /J`) where `Path.is_symlink()` is false but `_is_link()` detects the reparse attribute and the registry scan fail-closes.

## Fresh v9r20 identity and final bytes

Final pre-smoke bytes after the Web-found stale-provenance and reparse-routing corrections:

- `GENERATION_PLAN.json`: 64,375 bytes
- plan SHA256: `d0be34e4648a76775e813f1d68097e6ac6c8b3fd3ee1f5211b2ab8534e054ad7`
- `input/EXCLUSION_INPUTS.json`: 2,986 bytes
- exclusion manifest SHA256: `822f39b80831f580df5f3e1e82b9a22c93e047381a8512a53536e1e941daf28b`
- `RUBRIC.json`: 3,334 bytes
- rubric SHA256: `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- mechanics: **58/58 exact** by bytes + SHA, missing/mismatch 0
- exact TWELVE query-fingerprint exclusion sets; required overlap 0
- failed-D123 fingerprint artifact remains byte-identical to v9r19, SHA256 `2821c326ab28b9704d569de37379141edb5816e3fe99e394321293e10820d3ba`
- rubric remains byte-identical to v9r19

The manifest SHA differs from v9r19 only because the manifest description identifies generation-v9r20; the exclusion data contents are unchanged. No thirteenth set is added because v9r19 Smoke A/B produced no Author candidate/query pool.

The earlier implementation-stage SESSION-LOG entry recorded an intermediate plan SHA `38b6a8fb...0d678`. That value is **superseded prospectively for v9r20 final bytes** by this D-127 plan SHA after two same-stage pre-smoke corrections: (1) stale descriptive Paseo-version/daemon-scan wording, then (2) Web-found reparse-routing hard blocker. Historical v9r19 evidence is not rewritten.

## Final non-model validation

The implementation executor reran the complete final-byte non-model battery after the reparse repair; all 12 suites passed:

- Paseo exact-CLI gate: 64 checks
- role writer preflight: 36 checks
- launcher reachability: 87 checks
- lifecycle-smoke contract: 53 checks
- role-tool confinement/helper matrix: 172 checks
- role completion gate: PASS
- Phase-C confinement: 212 checks
- freeze-binding regression: 66 checks
- Reviewer/C staging exact-set regression: 24 checks
- TWELVE-set regression: rc0 / D-123 360 retained
- slot/location regression: rc0, 6 positive / 5 negative
- registry descendant scan: **33 checks**

Web independently re-ran the pivotal final-byte suites after the last repair:

- registry descendant scan: `REGISTRY_SCAN_PASS`, 33 checks
- Phase-C confinement: `CONFINEMENT_TESTS_PASS`, 212 checks
- freeze-binding regression: `FREEZE_BINDING_PASS`, 66 checks, hold base exactly D-126 `b9a129b...2bbc7e`

Expected negative probes emit `CONTRACT_INVALID_GENERATION` inside these passing suites and are part of the fail-closed contract.

## Final fresh-builder / duplicate boundary

After exact-path cleanup of builder-local test caches and four abandoned `v9r20_live_tmp_*` synthetic confinement-test roots from interrupted development runs:

- v9r20 builder `__pycache__` directories: 0
- `PLAN_LOCK.json`: absent
- `FROZEN_HASHES.json`: absent
- `phasec_driver.run.lock`: absent
- home directories matching v9r20: 0
- OMP session directories matching v9r20: 0
- processes matching v9r20: 0
- Paseo registry title/cwd metadata matching v9r20: 0
- all 316 registry JSON metadata records parse successfully
- v9r19 plan remains `a442f5641f1dbada08ce5eeb71b838746910c58c8b979e25bacc24a134420705`
- v9r19 exclusion manifest remains `1caffc012103abea5c85487588bd0c6daaea2766e90cc41cb113569086f56e3b`
- v9r19 failed-D123 fingerprint bytes remain untouched

Therefore v9r20 has consumed **zero generation smoke evidence** and is ready only for the next separately gated Smoke-A preflight.

## Gate boundary

**D-127 PRE-SMOKE PASS.** V9r19 remains permanently closed under D-126 and must never be repaired/resumed/re-smoked. V9r20 is the only fresh successor identity authorized to continue.

Next stage, if approved, must re-reconcile actual repo/origin/SSOT/OMP/Paseo provenance and duplicate/runtime state, then may execute **exactly one v9r20 Smoke A** on these final bytes. Smoke B, real freeze, Phase C, protected dev-v2, holdout, and production remain prohibited in D-127.
