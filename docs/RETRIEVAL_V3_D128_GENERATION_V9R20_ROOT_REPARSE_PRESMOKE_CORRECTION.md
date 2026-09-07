# Retrieval v3 D-128 — generation-v9r20 PRE-SMOKE root-reparse correction

Date: 2026-09-08
Stage: Smoke-A pre-gate / append-only correction of D-127 final-byte verdict
Generation: `retrieval-v3-dev-generation-v9r20`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r20`
Published predecessor record: D-127 commit `dff03c5b3820e82e5c7ee5bfc842922d35f6ad30`

## Verdict

**PRE-SMOKE PASS on corrected final bytes.** D-127 remains historical evidence but its final-byte PASS for plan `d0be34e4648a76775e813f1d68097e6ac6c8b3fd3ee1f5211b2ab8534e054ad7` is superseded by this record. During the next Smoke-A pre-gate, before any v9r20 generation smoke was consumed, independent review found that the registry descendant scan rejected reparse-point entries and leaves but did not reject a reparse-point registry root before traversal.

Because the defect was discovered pre-smoke and pre-freeze, v9r20 remained repairable in the same generation. The same implementation executor made the narrow mechanics repair; retrieval/evaluation semantics, rubric, counts, exclusion contents, D-123 fingerprints, selector, protected-data boundaries, and production code were unchanged.

No v9r20 Smoke A or Smoke B has been consumed. No real freeze, Phase C, source-truth snapshot, Author/Reviewer/C generation, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append occurred in this correction stage.

## D-127 hard blocker

The published D-127 code already used the Windows-aware `_is_link()` helper for registry entries and JSON leaves. `_is_link()` returns true for either a Python symlink or `FILE_ATTRIBUTE_REPARSE_POINT` (`st_file_attributes & 0x400`). However, `scan_registry_children()` did not call `_is_link()` on the supplied registry root itself before `iterdir()` / `resolve()`.

Independent Web reproduction on Windows Python 3.11 used a real temporary junction as the registry root and observed:

- `root_junction.is_symlink() == False`
- `_is_link(root_junction) == True`
- `scan_registry_children(..., root=root_junction) == []`
- no `SystemExit(3)` / no fail-close

That contradicted the intended root-integrity / reparse fail-closed contract and made D-127's final-byte PRE-SMOKE PASS stale.

## Narrow repair

`coord_wrapper_tpl/phasec_driver.py::scan_registry_children` now rejects a non-plain root before any traversal:

```python
base = Path(root)
if _is_link(base) or not base.is_dir():
    contract_invalid(...)
```

Only after that gate may the code call `base.iterdir()` or `base.resolve()`. Existing entry/leaf `_is_link()` checks, filename/id binding, duplicate detection, label validation, path-confinement checks, inspect-side strict-if-present semantics, and the complete local-registry parent-label scan are unchanged.

`test_registry_descendant_scan.py` now includes a deterministic real Windows root-junction regression. It requires all of the following rather than treating a skipped facility as proof:

- root junction creation succeeds with `mklink /J`
- `Path.is_symlink()` remains false
- `_is_link()` returns true from the reparse attribute
- `scan_registry_children(..., root=<junction>)` exits 3
- a dedicated `root_reparse_proof_real` check must pass

The existing >200 child-after-200 proof and entry-junction proof remain.

## Corrected final bytes

- `GENERATION_PLAN.json`: 64,375 bytes
- plan SHA256: `4baf17f208db63a27948cf1b11ac88f87b052f0f8db7f0f5468a1267023be542`
- `input/EXCLUSION_INPUTS.json` SHA256: `822f39b80831f580df5f3e1e82b9a22c93e047381a8512a53536e1e941daf28b`
- `RUBRIC.json` SHA256: `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- failed-D123 fingerprint SHA256 remains `2821c326ab28b9704d569de37379141edb5816e3fe99e394321293e10820d3ba`
- mechanics: **58/58 exact**, mismatch 0
- D-127 plan `d0be34e4...54ad7` is superseded only as the pre-repair v9r20 final-byte identity; it is not rewritten.

## Validation

The same implementation executor `59c723d9-ba0d-44aa-a722-1f3c19fec454` reran the full final-byte 12-suite non-model battery and reported PASS:

- Paseo exact-CLI gate: 64
- role writer preflight: 36
- launcher reachability: 87
- lifecycle-smoke contract: 53
- role-tool/helper matrix: 172
- role completion gate: PASS
- Phase-C confinement: 212
- freeze-binding regression: 66
- Reviewer/C staging exact-set: 24
- TWELVE-set regression: rc0, D-123 360 retained
- slot/location regression: rc0, 6 positive / 5 negative
- registry descendant scan: **37**

Web independently reran the pivotal corrected-byte tests:

- `REGISTRY_SCAN_PASS`, 37 checks
- `CONFINEMENT_TESTS_PASS`, 212 checks
- `FREEZE_BINDING_PASS`, 66 checks
- exact plan SHA `4baf17f208db63a27948cf1b11ac88f87b052f0f8db7f0f5468a1267023be542`
- mechanics 58/58, mismatch 0

Before this record, repo HEAD/upstream/direct origin were all D-127 `dff03c5b3820e82e5c7ee5bfc842922d35f6ad30`, working tree clean, `git diff --check` PASS, production `ml-service/` diff 0, protected main-tree dev/holdout plaintext paths absent, and canonical audit remained 4 rows with SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`.

## Gate boundary

**D-128 supersedes D-127 for the v9r20 final-byte PRE-SMOKE verdict.** V9r19 remains permanently closed and immutable. V9r20 remains the fresh successor and has consumed zero generation smoke evidence.

The next logical stage must re-run duplicate/runtime/provenance checks against these corrected final bytes and may then consume **exactly one v9r20 Smoke A**. Smoke B, real freeze, Phase C, protected dev-v2, holdout, and production remain prohibited until their later gates.
