# Cycle3 Fresh Holdout Sealed

- **Plan**: cycle3-holdout-v1
- **Seed**: `benefit-compass-cycle3-holdout-v1-2026-08-31`
- **Generated at**: 2026-08-31T02:20:42.611596Z
- **Cases**: 40 (Youth 20 / Gov24 20)
- **Category totals**: housing_finance 7, family_care 7, employment_education 7, welfare_health 7, culture_community 6, business_agriculture 6
- **Source-category quotas**: as per GENERATION_PLAN.json immutable (housing_finance youth4 gov243, family_care youth3 gov244, employment_education youth4 gov243, welfare_health youth3 gov244, culture_community youth3 gov243, business_agriculture youth3 gov243)
- **Stable order**: `sha256(seed + NUL + source + NUL + source_id), ascending`
- **Classifier**: precedence family_care, housing_finance, business_agriculture, employment_education, welfare_health, culture_community with keywords hash 3e59a3d048c1…
- **Source truth**: `input/source_truth.jsonl` 11903 rows (youth 1492 / gov24 10411), SHA256 `67acd53304669208ad205bc79d119951b8e5ace3e881378a56d99390242d6144`, historical gold excluded 198, as_of 2026-08-31
- **Historical catalog**: union q/g 248/248, overlap q 0 / g 0 (fail-closed)
- **Fingerprint**: version v1, normalization "NFC + strip + collapse_whitespace + casefold(lower)"
- **Outputs**:
  - `output/evalset.jsonl` — SHA256 `4c631ce7cdcc03374bb1861d0a27e0ebbacf35a691fb6f54543b96c7f051c350`
  - `output/fingerprints.json` — SHA256 `93be481e3c4fee700615b8f66c0c9289472ea3315c46287a91174d278c625a89`
  - `output/annotation_audit.json` — SHA256 `739a72cb8d9e1eb67fdb6e73ebc3842ffad9efc9b0586cab57d5a3879e372ee6`
  - `output/manifest.json` — SHA256 `f8a836ed6913e915de439e528cd4216c22122fa2bbb8ee9938dcbf5dec7aaf39`
  - `output/builder_report.json` — SHA256 `73496f5a1fa665ec80d9055ece97563ee41aab01ce6874fb25a7b1375dc782fd`
- **Validation**: internal q duplicate 0, g duplicate 0, historical overlap 0/0, well_posed 40, ambiguous 0
- **Prohibitions observed**: no network/DB/retrieval/ranking/vector/embedding/model load/benchmark, no parent/sibling repo access, no result-based retuning, single canonical stable selection, queries from selected source truth only
- **Seal**: This holdout is sealed for independent Web validation and import into protected holdout branch. No Git commit/push/tag performed in this sanitized workspace.

*Builder report contains aggregates/hashes only, no case plaintext (query/title/source_id).*
