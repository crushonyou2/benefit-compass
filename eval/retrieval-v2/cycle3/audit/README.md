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
- Any `previous_event_hash` mismatch, `event_hash` mismatch, duplicate `event_id`, or broken JSON → `AuditChainError` (fail-closed).
- `git_head`/`git_dirty` captured from `git rev-parse HEAD` / `git status --porcelain`; fallback `unknown` / `false`.
- `session_id` defaults to `CYCLE3_SESSION_ID` env or `pid-<pid>`.

## Writer contract

- Use `eval/retrieval_v2/cycle3_audit.py:append_event(log_path, action=..., ...)` — verifies chain, computes hashes, appends atomically (LF, flush, fsync), re-verifies.
- Helpers: `build_run_start` / `build_run_end`.
- `read_and_verify_chain(log_path)` returns verified list or raises `AuditChainError`.

## Tamper detection

- File with invalid JSON, hash mismatch, broken `previous_event_hash` linkage, or duplicate `event_id` → verification fails.
- Truncate / overwrite that leaves broken linkage (e.g., removing last line then appending with wrong `previous_event_hash`, or editing a field without updating hash) → next `read_and_verify_chain` or `append_event` fails.
- Overwrite that replaces file with a wholly new valid chain from genesis is not detectable without external anchor; such full-replacement is prohibited by procedure — logs must be append-only and anchored in git history.

## Holdout access gate

- `verify_holdout_access_allowed(log_path, set_role="holdout")` must be called before opening holdout plaintext.
- It scans verified chain for `action == "protected_access_start"` with matching `set_role` and success outcome.
- No matching event → raises `AuditError` and plaintext must not be opened (fail-closed). Test `test_holdout_access_gate_requires_event` enforces this contract.

## Bootstrap tests

- Tests use `tempfile` temp logs only, never the real `events.jsonl`.
- No retrieval/DB/model/embedding or protected plaintext is accessed.
- See `eval/test_retrieval_v2_cycle3_audit.py`.

## Operational rule for next builders

1. Before any `run_start` or `protected_access_start`, call `append_event` and handle `AuditError` fail-closed.
2. Before opening `holdout` plaintext, call `verify_holdout_access_allowed` — event append must have succeeded first.
3. Never truncate or overwrite `events.jsonl`; always append via `append_event`.
4. Commit `events.jsonl` only via accounted process — history must remain append-only.
