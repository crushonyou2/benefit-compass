# Historical Protected-Set Fingerprint Catalog — Cycle3 (D-011)

> Fingerprint-only, no plaintext. Fresh builders can enforce overlap 0 without reopening protected plaintext.

## Entrypoint (single file)

- **Single file:** `eval/retrieval-v2/cycle3/catalog/catalog.json`
  - Read this ONE file to obtain the full historical exclusion set (union of 6 sets).
  - Contains `union.query_fingerprints` / `union.gold_fingerprints` (deduped, sorted, 64-hex).
  - Use with `eval/retrieval_v2/cycle3_fingerprint.py:check_overlap` (pure) for fail-closed validation.

```python
from retrieval_v2.cycle3_historical_catalog import load_historical_catalog, check_fresh_no_overlap
catalog = load_historical_catalog()  # reads single catalog.json
res = check_fresh_no_overlap(fresh_manifest, catalog)  # strict 0 check, fingerprint-only
```

- **Directory:** `eval/retrieval-v2/cycle3/catalog/` also contains per-set manifests (`p0.json`, `cycle1_dev.json`, `cycle1_holdout.json`, `cycle2_dev.json`, `cycle2_holdout_disqualified.json`, `hard_negative.json`) — each valid per `validate_fingerprint_manifest`.

## Historical sets (6)

| id | display | cases | query/gold count | provenance |
|---|---|---|---|---|
| p0 | P0 canonical (Youth 60 + Gov24 21) | 81 | 81 / 81 | `eval/canonical_manifest.json` `6c902b3…`, `eval/evalset.jsonl` `02853c0…` (youth infer), `eval/expansion_evalset.jsonl` `86fb2d8…` |
| cycle1_dev | Cycle1 dev 36 (Youth 18/Gov24 18) | 36 | 36 / 36 | `12515a20…:eval/retrieval-v2/dev/evalset.jsonl` `e951020…` tag `retrieval-v2-holdout-v1` |
| cycle1_holdout | Cycle1 holdout 40 (Youth 20/Gov24 20) | 40 | 40 / 40 | `12515a20…:eval/retrieval-v2/holdout/evalset.jsonl` `02eb038…` |
| cycle2_dev | Cycle2 dev 36 (balanced 6×6) | 36 | 36 / 36 | `372ed686…:eval/retrieval-v2/cycle2/dev/evalset.jsonl` `c8b66fef…` tag `retrieval-v2-cycle2-dev-v1` |
| cycle2_holdout_disqualified | Cycle2 disqualified holdout 40 — D-010 | 40 | 40 / 40 | `9e2cd6ea…:eval/retrieval-v2/cycle2/holdout/evalset.jsonl` `cf003bab…` tag `retrieval-v2-cycle2-holdout-v1` (immutable history, not final gate) |
| hard_negative | hard-negative 36 (pure 21 + ineligible 3 + no_answer 12, synthetic gold for no-gold) | 36 | 36 / 36 | `eval/expansion_api_evalset.jsonl` `2b56dcf…`, artifact `eval/canonical_hard_negative_36_production_parity.json` `9355f826…` |

- Each manifest: `fingerprint_version == "v1"`, `normalization_spec == "NFC + strip + collapse_whitespace + casefold(lower)"`, `cases == len(query_fingerprints) == len(gold_fingerprints)`, each 64-hex, no duplicate (fail-closed).

## Union

- Query union: 248 (sum 269 − 21 dedup P0 vs hard_negative)
- Gold union: 248 (same)
- Hashes: `query_union_hash` / `gold_union_hash` SHA256 of concatenated sorted union (for quick compare).

## Inter-set overlap

- Computed via `check_overlap` on fingerprint manifests (fail-closed, validated first).
- **P0 vs hard_negative:** query 21 / gold 21 — **expected_allowed** (Gov24 21 reuses same queries/golds, by design).
- All other 14 pairs: query 0 / gold 0 — pass.
- `overall_pass: true` — no disallowed overlap; stage not HOLD.

## Audit

- Log: `eval/retrieval-v2/cycle3/audit/events.jsonl` (append-only, fsync, chain hash).
- This freeze used 10 events in session `catalog-freeze-20260831-<pid>`:
  - 2× `run_start` (set_role none) for P0 / hard-negative (schema has no p0 role)
  - 4× `protected_access_start` + `protected_access_end` (dev/holdout) for cycle1/2 sets, each gated via `verify_holdout_access_allowed` with exact `set_sha`/`session_id`/`expected_event_hash` (latest-success, outcome success only, closed by end).
- Chain verified via `read_and_verify_chain` (previous_event_hash / event_hash SHA256(canonical JSON)).
- **Schema limitation (documented):** P0/hard-negative cannot be honestly represented as `protected_access_*` with `set_role dev/holdout` (would be false role). Existing schema only allows `dev`/`holdout`/`none`; `none` requires `set_sha null` and does not model P0/hard-negative protected sets. Therefore this stage logs plaintext-free `run_start` events + catalog provenance instead of false `protected_access` roles, and does not add new roles. Final report documents this limitation.

## Fingerprint contract

- Helper: `eval/retrieval_v2/cycle3_fingerprint.py` unchanged (D-011).
- Query: `SHA256(NFC + strip + collapse + casefold)`
- Gold: `SHA256(source + NUL + source_id)` where source ∈ {youth, gov24}. For hard-negative no-gold cases, synthetic `gov24` + `hard_negative_*` distinct id used to satisfy 36/36 and avoid duplicate; pure gold already protects real policy id.

## Fresh builder usage

```python
from retrieval_v2.cycle3_fingerprint import manifest_with_fingerprints, check_overlap
from retrieval_v2.cycle3_historical_catalog import load_historical_catalog, get_union_manifest
fresh = manifest_with_fingerprints(role="holdout", cycle=3, cases=40, query_fingerprints=[...], gold_fingerprints=[...])
catalog = load_historical_catalog()
union = get_union_manifest(catalog)
check_overlap(fresh, union, strict=True)  # raises ValueError if any overlap, fail-closed
```

- No DB/retrieval/model/embedding needed; pure static check.
- One file read (`catalog.json`) suffices for historical exclusion.

## No plaintext

- Catalog files contain only fingerprints (64-hex), counts, provenance hashes/refs, and aggregates.
- No query, no gold_title, no reversible raw identifiers.
- Verified via `plaintext leak` check (search for known query substrings) in builder and tests.

## Next (historical at catalog-freeze; as of D-012 `a6a232c` + closure commit, current closure state)

- Historical next at catalog-freeze: Fresh Cycle3 holdout 40 builder (isolated session, plaintext not reused from this catalog builder) — **now completed**; holdout 40 (`4c631ce7...`) and dev 36 (`3791368f...`) are frozen, audited, and canonical dev batch executed (count=1, `DEV_SELECTABLE []` closes without holdout per D-012). This Next list is preserved as historical sequence, not current.
- This catalog builder workspace must not be reused for candidate tuning/fresh builder/final evaluation (isolation) — remains in force.
- **Current closure (D-012, 2026-09-01):** Cycle3 closed without holdout; no candidate freeze, no holdout evaluation; archival tag `retrieval-v2-cycle3-closure-v1` will point to D-012 closure commit; next logical stage is Git hygiene with fresh CAS checks (no deletion in this stage).
