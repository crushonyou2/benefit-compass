# SEALED — Cycle3 Fresh Dev 36
Generated: 2026-08-31T03:00:33Z
Seed: benefit-compass-cycle3-dev-v1-2026-08-31
Plan: cycle3-dev-v1
Cases: 36

## Provenance DAG
core(evalset.jsonl, fingerprints.json, annotation_audit.json) -> manifest.json(core only) -> builder_report.json(core+manifest) -> SEALED.md(core+manifest+builder_report)

## Hashes (LF canonical SHA256, lower-hex)
- evalset.jsonl: 3791368f4722b612058b7a005e17bf5f1caae4ac0437daa9d44ff28f28ca260c
- fingerprints.json: e0ed52f257601e9c8ded2abe58950c49622f352cb135a71fdca4fb2ae0f4c120
- annotation_audit.json: 7a44be39779674c0d3076ba80cae46f43fef2c07a4504cef40ea8c82d35666e9
- manifest.json: e35432ac43903216c4b56d2758717013929f6bf575cd22a652b7e28d436927b8
- builder_report.json: 90121b66ed1def000d852b436cd4b970ee0fb6a5bd16dae92ffcbf6fa685e07f

## Validation Aggregates (no plaintext)
- cases: 36
- source_totals: youth 18 / gov24 18
- category_totals: each 6
- internal_duplicate: query 0 gold 0
- historical_overlap: query 0 gold 0
- holdout_overlap: query 0 gold 0
- annotation: well_posed 36 ambiguous 0

## Notes
- No retrieval/ranking/policy_chunk/vector/embedding.
- Provenance hash circular/self-reference prohibited: manifest(core only), builder_report(core+manifest), SEALED(core+manifest+builder_report).
- All output text LF canonical bytes; hashes on LF final bytes.
