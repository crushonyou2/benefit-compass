# Retrieval v3 — Link Provenance Supersession V2 (D-060, pre-result)

Append-only correction to V1. `docs/RETRIEVAL_V3_LINK_PROVENANCE_SUPERSESSION_V1.md`
and all D-059 records stay verbatim as history. This V2 imports V1 semantic rules
unchanged and supersedes ONLY V1/D-059 implementation-reachability statements.
`docs/RETRIEVAL_V3_PREREG.md`, `candidate-plan-v4.json`, `safe-action-policy-v1.json`,
`production-exclusion-policy-v2.json` are NOT edited in place. No candidate-plan-v5;
ranking/config semantics remain exact 18/18 unchanged.

## 1. V1 semantic rules imported unchanged (no retune)

V1 sections 2-3 stay frozen: Gov24 online-application-URL else detail;
Youth aplyUrlAddr else refUrlAddr1; refUrlAddr2 excluded; trim-only;
exact case-sensitive http(s) prefix; exact-string trimmed dedupe; no invented
domain; non-http legacy treated as missing; denominator 0 => HOLD;
missing/incomplete => HOLD; numeric mismatch => NO-GO; HTTP protocol verbatim
(connect 5s / read 10s, 1 retry max 2 attempts 0ms backoff for 5xx/network/
timeout/TLS only, 200-299 success, 300-399 redirect up to 3 hops preserving
method, HEAD first with 405/501/network/TLS => single GET fallback, per-hop
fresh retry budget, duplicate URLs checked once, PASS >= ceil(0.99*unique)).
Gate key stays `official_link` with truthful `apply_url` evidence. V1 section 4
same-snapshot binding (ONE `RealEvaluationSession` REPEATABLE READ transaction)
stays frozen.

## 2. D-059 reachability correction (false at ff9a579)

D-059 section 4 / V1 section 7 claim "A+B mechanically reachable" was false at
`ff9a57917b68a2f2a041f1d576680b8edbbbbce8` for B canonical reachability:

- B1: `RealSafetyAdapter` requires `raw_lookup` for table-vs-raw derivation, but
  `main_canonical_dev` -> `build_real_adapters()` passed no `raw_lookup`, so the
  canonical FIRST-dev safety adapter constructed `_raw_lookup=None` and
  `official_link` deterministically HOLD.
- B2: D-057 already froze the exact real HTTP machinery
  (`check_url_with_transport` owns retry/redirect/fallback;
  `http_client_transport` is one single-attempt primitive), but
  `RealSafetyAdapter.__call__` never called it; `http_resolution` was hard-coded
  HOLD. The D-059 test asserting transport calls stay `[]` froze the bug rather
  than canonical FIRST-dev reachability.

D-059 is NOT rewritten; this V2 corrects the effective contract prospectively.

## 3. Repaired canonical call graph (after D-060)

`main_canonical_dev` -> `build_real_adapters(session)` (no manual `raw_lookup`)
-> auto-binds `session.get_link_raw` lazily (no IO at construction) ->
`RealSafetyAdapter(session, http_transport, raw_lookup=session.get_link_raw)`
-> `__call__`: table `apply_url` lookup via `session.official_url_lookup`
-> raw re-derivation via same-session `SELECT` (section 4) ->
`official_link` PASS/NO-GO/HOLD per V1 derivation equality ->
if and only if `official_link` PASS, `check_url_with_transport` exactly once per
deduped unique URL via `self._http_transport` (real `http_client_transport` in
future FIRST dev, injected mock in tests) -> `http_resolution` PASS/NO-GO/HOLD
per section 5. `cost` remains structural HOLD (unchanged).

## 4. Same-snapshot raw evidence (no second connection)

- New `RAW_EVIDENCE_SQL`: `SELECT p.source, p.source_id, p.raw FROM policy p
  ORDER BY p.source, p.source_id` (SELECT-only, deterministic, no LIMIT/
  CURRENT_DATE/writes/DDL/SET/timezone override, no ranking/output influence).
- `RealEvaluationSession._load_raw_map` / `get_link_raw(source, source_id)` own
  the lazy cached map on the SAME existing REPEATABLE READ connection via
  `execute_readonly` (no second `connect`; second safety call reuses cache).
  Available ONLY after capture (`_pinned` established); construction/parsing
  stay IO-free. JSON-string raws are parsed pure; unparseable stays as-is
  (adapter HOLD).
- Fail-closed: malformed/duplicate identity rows raise (`ValueError`); missing
  identity / non-dict raw / malformed query identity / pre-capture access yield
  HOLD at the adapter (never guessed, never PASS). No protected data involved.

## 5. Frozen HTTP auto-execution (no second implementation)

- Reuses D-057 `check_url_with_transport` + `http_client_transport` exactly; no
  second retry/redirect/fallback implementation; D-057 constants/semantics
  unchanged.
- Executes exactly once per deduped unique URL (trimmed exact-string dedupe
  denominator preserved) using `self._http_transport`; the state machine owns
  all per-URL attempts/retries/redirects/fallback.
- Structured `http_resolution`: `unique`, `successes`, `required=ceil(.99*unique)`;
  PASS iff `successes >= required`, else NO-GO. Denominator 0, unknown identity,
  `raw_lookup is None`, or `official_link != PASS` (missing raw / drift NO-GO)
  => HOLD with no HTTP execution (never PASS on non-authoritative denominator).
  No new policy invented. No URLs/secrets in error details beyond the standing
  safe result schema.
- Tests use injected mock transport only; no live HTTP in this stage. The real
  canonical path is nonetheless wired so future FIRST dev invokes the real
  single-attempt transport automatically. No HTTP before FIRST dev in this stage.

## 6. What is NOT changed

No candidate tuning/result-driven change; no new score/action threshold; no new
model/embedding/LLM classifier; no Candidate B; no 18 tuple/MAX24/safe-action/
production-exclusion/headline/location/latency change; COST remains HOLD exactly
(no DB rows=0 fiction, no new candidate DB ranking/index, no threshold
reinterpretation); no ml-service behavior change; no dataset
regenerate/reannotate/refreeze; no history rewrite. D-059 test hole is corrected
narrowly (one obsolete `calls == []` assertion superseded with documented reason;
all other D-059 tests preserved).

— END LINK PROVENANCE SUPERSESSION V2 (D-060 pre-result) —
