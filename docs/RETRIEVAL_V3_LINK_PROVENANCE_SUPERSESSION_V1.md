# Retrieval v3 — Link Provenance Supersession V1 (D-059, pre-result)

Supersedes ONLY the prereg §9 `official_link` field/domain wording. All other prereg
gates, thresholds, HTTP protocol, ranking/selection/MAX24/B-gate/safe-action/
production-exclusion/latency/headline/location semantics are unchanged.
`docs/RETRIEVAL_V3_PREREG.md`, `candidate-plan-v4.json`, `safe-action-policy-v1.json`,
`production-exclusion-policy-v2.json` are NOT edited in place.

## 1. Standing wording being corrected (no deletion)

Prereg §9 freezes an `official_link` URL field + source/domain match (e.g. gov24 URLs
must be gov.kr domain) with exact-string trimmed dedupe denominator, HEAD/retry/
fallback/redirect/timeouts/status semantics, `>=ceil(0.99*unique)`, missing/incomplete
=> HOLD.

Actual policy/runtime schema (`db/schema.sql`, `ml-service/app.py`, `eval/retrieval-v3/real_adapters.py`
`CORPUS_COLUMNS`/`CORPUS_SQL`/`D003_SQL`) carries `apply_url` (application link) only.
There is no `official_link` column and no frozen claimed-source domain/path map.
External application sites are legitimate in current ingestion semantics. The prereg
field name/domain assumption therefore has no source-truth backing and MUST NOT be
used to invent a youthcenter canonical detail URL/domain rule without first-party
authority.

## 2. Frozen visible-link provenance contract (pre-result, deterministic)

Visible/user-facing application URL for each retrieved `(source,source_id)` MUST equal
the URL deterministically derived from that source's raw record by the already-
established ingest rule. No invented URL/domain.

- Gov24 (`ingest/ingest_gov24.py:normalize`): `apply_url = _official_url(온라인신청사이트URL, 상세조회URL)`
  where `_official_url` returns the first candidate whose `_text` (strip leading/trailing
  whitespace, `None` if empty) starts with `https://` or `http://` (case-sensitive,
  exact prefix), else `None`. `온라인신청사이트URL` comes from `raw.serviceDetail`,
  `상세조회URL` from `raw.serviceList`. `raw` is `{"serviceList","serviceDetail","supportConditions"}`.
- Youth (`ingest/ingest_youth.py:normalize`): `apply_url = _official_url(aplyUrlAddr, refUrlAddr1)`
  where `_official_url` returns the first candidate whose `(candidate or "").strip()`
  starts with `https://` or `http://` (case-sensitive, exact prefix), else `None`.
  `refUrlAddr2` is explicitly EXCLUDED per standing P0/P1 decision. `raw` is the full
  youth record. No youthcenter canonical detail URL is invented.
- Whitespace/string rules: trim leading/trailing whitespace only (Python `strip`
  semantics); exact-string dedupe after trim, no casefold, path case-sensitive, NFC
  not applied to URLs (`safety.dedupe_official_links` preserved verbatim).
- Missing-evidence behavior: `NULL`/blank/non-`http(s)` stored `apply_url` (including
  35 legacy Youth non-http values) counts as `missing_url_fields`, excluded from the
  unique denominator (accepted source limitation per P0/P1: Youth 599 missing =
  NULL 564 + non-http 35; Gov24 0 missing). Denominator `0` => HOLD (missing
  measurement, never PASS). Missing/incomplete checker evidence (any unique URL not
  checked, log incomplete, snapshot pin invalid, raw for a required identity missing)
  => HOLD. Numeric mismatch or HTTP `<ceil` => NO-GO. Thresholds unchanged.
- Source-specific authority: Gov24 authority is `serviceList.상세조회URL` +
  `serviceDetail.온라인신청사이트URL`; Youth authority is `aplyUrlAddr` + `refUrlAddr1`
  only. If Youth authority is incomplete for a required retrieved identity (both
  `NULL`/non-http where `refUrlAddr2` alone is valid but excluded), fail closed/HOLD,
  never guess.
- Gate key stability: result/audit gate key remains `official_link` (stable, no schema
  churn), but evidence MUST truthfully identify the measured visible field as
  `apply_url` derived above (`url_field: apply_url` diagnostics + this supersession ref).
  No fabricated `official_link` column.

## 3. HTTP protocol preserved exactly (no relaxation)

Denominator = unique VALID `http(s)` `apply_url` values across visible top-5 per task
after trim + exact-string dedupe (non-http legacy treated as missing per §2, consistent
with accepted limitation). All prereg §9 HTTP semantics preserved verbatim: connect 5s /
read 10s per attempt, 1 retry (max 2 attempts, 0ms backoff) for 5xx/network/timeout/TLS
only, 200–299 success, 300–399 redirect up to 3 hops preserving method, HEAD first with
405/501/network/TLS => single GET fallback, TLS/DNS/reset/timeout as attempt failure,
per-hop fresh retry budget, duplicate URLs checked once, `PASS >= ceil(0.99*unique)`,
missing/incomplete => HOLD, numeric failure => NO-GO. HTTP checks run on the exact
frozen visible-link denominator ONLY during FIRST dev, not in D-059. D-059 tests use
pure/mock transport only.

## 4. Source-truth evidence binding (same snapshot, no ranking influence)

Link evidence used by the gate MUST come from the same governing read-only evaluation
snapshot/provenance as ranking (ONE `RealEvaluationSession` REPEATABLE READ transaction:
capture -> corpus load/fingerprint -> D-003 baseline -> link raw audit until close).
`official_url_lookup` (`(source,source_id) -> apply_url`) and raw re-derivation (when
present) are read from that same snapshot; they MUST NOT alter ranking/output (read-only
`SELECT` only, no writes/DDL/SET/timezone override). Corpus provenance fingerprint +
pinned `evaluation_as_of_date`/`db_session_timezone` ride the result/audit as before.

## 5. Read-only live authority evidence (aggregate only, D-059 reconcile, no protected data)

Governing-session read-only aggregates on current production corpus (same env that FIRST
dev will use; DSN never printed; no protected evalset/ranking/model/HTTP benchmark):

- `policy` counts: gov24 10958, youth 2631 (total 13589).
- Gov24 raw 3 keys (`serviceList`+`serviceDetail`+`supportConditions`) 10958/10958.
- Gov24 `serviceList.상세조회URL` present 10958/10958, `LIKE http%` 10958/10958,
  `LIKE %gov.kr%` 10958/10958 (universal gov.kr detail authority).
- Gov24 `serviceDetail.온라인신청사이트URL` present 2003, `http%` 1654 (partial online;
  external application sites legitimate).
- Gov24 stored `apply_url` derivation mismatch (`apply_url IS DISTINCT FROM CASE online-else-detail`) 0.
- Gov24 stored `apply_url LIKE %gov.kr%` 9304, external (online) 1654 => domain allowlist
  would wrongly reject 1654 legitimate external URLs; therefore NO domain allowlist.
- Youth raw keys `aplyUrlAddr`/`refUrlAddr1`/`refUrlAddr2` each 2631/2631.
- Youth `aplyUrlAddr LIKE http%` 812, `refUrlAddr1 LIKE http%` 1654, both 435.
- Youth stored `apply_url` missing (`NULL OR !~ ^https?://`) 599 = NULL 564 + non-http 35
  (16-row P1 fix already reflected: non-http 51 -> 35; remaining 35 are legacy truthy
  non-http treated as missing per §2).
- Youth stored-vs-raw derivation mismatch 36 = 35 legacy non-http (expected NULL) + 1
  both-http-differ (table drift candidate; fail-closed NO-GO if retrieved).
- Youth `refUrlAddr2`-only recoverable where stored NULL 0 (exclusion costs nothing new).
- Stored `apply_url` needs-trim (`btrim <> value`) 0 (ingest trim already enforced).
- Index inventory (`pg_indexes` on `policy`/`policy_chunk`) 8: `idx_chunk_embedding`,
  `idx_policy_age`, `idx_policy_income`, `idx_policy_region`, `policy_chunk_pkey`,
  `policy_chunk_policy_id_chunk_index_key`, `policy_pkey`, `policy_source_source_id_key`.

These aggregates prove the §2 derivation (Gov24 0 mismatch; Youth mismatches are the known
legacy/limitation set, not a new rule) and justify freezing without inventing domains.

## 6. What is NOT changed

No candidate tuning/result-driven change; no new score/action threshold; no new
model/embedding/LLM classifier; no Candidate B instantiate; no 18 tuple/config change;
no MAX24 change; no safe-action semantic change; no production-exclusion semantic change;
no headline/safety/location/latency threshold relaxation; no `ml-service` behavior change;
no dataset regenerate/reannotate/refreeze; no history rewrite. Ranking tuples/order/
selection/MAX24/B-gate/safe-action/production-exclusion/latency/headline/location
semantics are mechanically identical to candidate-plan-v4 (no v5 needed; gate key stable
with truthful `apply_url` evidence mapping per §2).

## 7. FIRST-dev measurability (D-059 implements, FIRST dev executes)

`RealSafetyAdapter` implements §2 semantic measurement (pure derivation helpers +
same-snapshot table-vs-raw comparison, fail-closed HOLD when raw evidence missing) with
existing `dedupe_official_links` + injectable-transport HTTP state machine unchanged.
D-059 proves it with TEMP SYNTHETIC files/records only (no protected bytes, no live HTTP
benchmark, no model load). During FIRST dev, the adapter will measure the exact frozen
visible-link denominator (§2–§3) on the pinned snapshot; HTTP via real single-attempt
transport; Youth incomplete authority => HOLD, never guessed.

— END LINK PROVENANCE SUPERSESSION V1 (D-059 pre-result) —
