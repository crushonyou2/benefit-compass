# Cycle3 Audit Log — append-only

> Bootstrap infrastructure only. No retrieval/DB/model/embedding/benchmark execution, no protected plaintext access in bootstrap.

## Log file

- Path (configurable): `eval/retrieval-v2/cycle3/audit/events.jsonl` — default for cycle3; bootstrap tests use temp files.
- Format: JSONL, one JSON per line, UTF-8, LF, sorted keys, compact separators.

## Event schema

```json
{
  "schema_version": 1,
  "event_id": "uuid-v4",
  "utc_timestamp": "2026-08-30T09:00:00.123Z",
  "git_head": "5cabd2eecd78923da4751c5e60fa316e74f563fc",
  "git_dirty": false,
  "process_id": 12345,
  "session_id": "pid-12345",
  "action": "run_start | run_end | protected_access_start | protected_access_end",
  "candidate_id": "c3e1-vector-pool-128 | null",
  "set_role": "dev | holdout | none",
  "set_sha": "hex | null",
  "command": "str | null",
  "runner_id": "str | null",
  "outcome": "str | null",
  "previous_event_hash": "64-hex",
  "event_hash": "64-hex"
}
```

- `previous_event_hash` of first event = `0`*64 (genesis).
- `event_hash = SHA256(canonical_json(sorted keys, excluding event_hash)))` over UTF-8.
- Writer verifies chain before append; post-append re-verifies.
- `git_head`/`git_dirty` captured from `git rev-parse HEAD` / `git status --porcelain`; **probe failure is fail-closed (no fallback to `unknown`/`false` — event write aborts)**. Supply explicit values to bypass probing in tests (must be `40-hex` / `bool`).
- `session_id` defaults to `CYCLE3_SESSION_ID` env or `pid-<pid>`; must be non-empty `str`, `process_id` positive `int`, `utc_timestamp` strict ISO8601 UTC `Z` (`YYYY-MM-DDTHH:MM:SS[.frac]Z`), `event_id` strict UUID v4.
- `set_sha`: for `set_role dev/holdout` must be `64-hex`; for `none` must be `null`. `protected_access_start`/`end` require `dev`/`holdout`.
## Writer contract

- Use `eval/retrieval_v2/cycle3_audit.py:append_event(log_path, action=..., ...)` — verifies chain, computes hashes, appends atomically (LF, flush, fsync), re-verifies.
- Helpers: `build_run_start` / `build_run_end`.
- `read_and_verify_chain(log_path)` returns verified list or raises `AuditChainError`.

## Tamper detection

- File with invalid JSON, hash mismatch, broken `previous_event_hash` linkage, or duplicate `event_id` → verification fails.
- Truncate / overwrite that leaves broken linkage (e.g., removing last line then appending with wrong `previous_event_hash`, or editing a field without updating hash) → next `read_and_verify_chain` or `append_event` fails.
- Overwrite that replaces file with a wholly new valid chain from genesis is not detectable without external anchor; such full-replacement is prohibited by procedure — logs must be append-only and anchored in git history.

## Holdout access gate (repaired — exact match + recency + token)

- `verify_holdout_access_allowed(log_path, *, set_role="holdout", set_sha="64-hex", session_id="...", expected_event_hash="64-hex"|None)` must be called **with exact `set_sha` + `session_id`** before opening protected plaintext. Optional `expected_event_hash` token verifies the exact latest `protected_access_start` `event_hash` to structurally block stale grants.
- Scans verified chain for `protected_access_start` with **exact** `set_role`+`set_sha`+`session_id` and explicit outcome `success`/`allowed` (`None`/failure does not grant). Picks **most recent** match; if a later `protected_access_end` for same `set_role`/`set_sha`/`session_id` exists, grant is closed → fail. If `expected_event_hash` supplied, it must equal the latest grant's `event_hash` (stale token → fail).
- No matching/latest grant or stale/closed/token mismatch → raises `AuditError` and plaintext must not be opened (fail-closed). Tests `test_holdout_access_gate_requires_event`, `test_stale_wrong_set_sha_fail`, `test_wrong_session_fail`, `test_access_end_closes_grant_fail`, `test_outcome_none_and_failure_fail`, `test_token_stale_grant_structurally_blocked` enforce contract.
## Bootstrap tests

- Tests use `tempfile` temp logs only, never the real `events.jsonl`.
- No retrieval/DB/model/embedding or protected plaintext is accessed.
- See `eval/test_retrieval_v2_cycle3_audit.py`.

## Operational rule for next builders (repaired)

1. Before any `run_start` or `protected_access_start`, call `append_event` and handle `AuditError` fail-closed (git provenance must succeed; UUID/timestamp/field strict).
2. Before opening `holdout`/`dev` protected plaintext, call `verify_holdout_access_allowed` with exact `set_sha`+`session_id` (+ `expected_event_hash` token if available) — event append must have succeeded first with `success`/`allowed`.
3. Never truncate or overwrite `events.jsonl`; always append via `append_event`.
4. Commit `events.jsonl` only via accounted process — history must remain append-only.
5. See `docs/RETRIEVAL_V2_CYCLE3_INFRA_REPAIR.md` and `docs/RETRIEVAL_V2_CYCLE3_PREREG_ADDENDUM.md` for provenance.
