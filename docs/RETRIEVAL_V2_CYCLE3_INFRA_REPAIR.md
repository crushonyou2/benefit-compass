# Retrieval v2 Cycle3 — Infra Repair v2

> **Branch:** `codex/retrieval-v2-cycle3-start` (from bootstrap `e4e56198ba3faef7ae687e356e41bf2d7543c198`)
> **Bootstrap tag (immutable):** `retrieval-v2-cycle3-start-v1` → `2a30e8d371...` → `e4e5619...`
> **Infra-repair tag:** `retrieval-v2-cycle3-infra-v2` (annotated, this repair)
> **Scope:** INFRA REPAIR only — no retrieval/DB/model/embedding/benchmark, no fresh dev/holdout creation, no cycle1/2 plaintext, no production/ml-service, no result artifact modification.

This document records the fail-closed repairs applied to the bootstrap infra after Web independent verification reproduced two real fail-open cases.

## 1. Reproducible fail-opens (bootstrap)

1. `cycle3_fingerprint.check_overlap({}, {}, strict=True)` returned overlap 0 PASS. Missing `query_fingerprints`/`gold_fingerprints` must be FAIL.
2. Audit log with one past holdout `protected_access_start` allowed `verify_holdout_access_allowed(set_role='holdout')` for a different `set_sha`. Stale access grant must be FAIL.

Both are repaired below with regression tests.

## 2. Audit log repairs (`eval/retrieval_v2/cycle3_audit.py`)

### 2.1 Git provenance — fail-closed
- `_get_git_head()` / `_get_git_dirty()` now raise `AuditError` on any `git` probe failure instead of silently returning `unknown` / `False`.
- `append_event(..., git_head=None, git_dirty=None)` probes strictly; failure aborts event write.
- `git_head` field validation now requires `40-hex` (lowercase stored), rejects `unknown`.
- Supplying explicit `git_head`/`git_dirty` bypasses probing but is strictly validated.

### 2.2 Schema strict validation (`_validate_payload` / `append_event`)
- `event_id`: strict UUID v4 — regex `8-4-4-4-12` with `4` at version position and `8/9/a/b` variant, `uuid.UUID(...).version==4`, canonical lowercase.
- `utc_timestamp`: strict ISO8601 UTC Z — regex `YYYY-MM-DDTHH:MM:SS[.frac]Z`, parseable via `fromisoformat(Z→+00:00)`, must be UTC (`+00:00`).
- `git_dirty`: must be `bool` (not int/truthy).
- `process_id`: must be `int` (not `bool`), positive `>0`.
- `session_id`: must be non-empty `str` (`strip()` non-empty).
- `previous_event_hash` / `event_hash`: `64-hex`.
- `set_sha` semantics:
  - `set_role in (dev, holdout)` → `set_sha` must be `64-hex`.
  - `set_role == none` → `set_sha` must be `None`.
- `action`/`set_role` semantics:
  - `protected_access_start` / `protected_access_end` require `set_role dev/holdout` (and thus `64-hex` `set_sha`).
- `candidate_id` / `command` / `runner_id` / `outcome`: `str | None` (if not `None`, `str`).

### 2.3 Holdout protected access gate — exact match + recency + outcome strict
- Signature: `verify_holdout_access_allowed(log_path, *, set_role="holdout", set_sha=..., session_id=..., expected_event_hash=None) -> dict`
  - `set_role` must be `dev`/`holdout` (for protected sets).
  - `set_sha` must be `64-hex`, `session_id` non-empty — missing/wrong type is FAIL.
  - Scans verified chain for `protected_access_start` with **exact** `set_role` + `set_sha` + `session_id`.
  - `outcome` must be explicit `"success"` or `"allowed"` — `None` or failure strings are denied (counts as no grant).
  - Picks the **most recent** matching `protected_access_start` (last in chain). Older events do not grant if a newer one exists.
  - If any later `protected_access_end` for the same `set_role`/`set_sha`/`session_id` exists after that latest start, grant is closed → FAIL (stale grant).
  - If `expected_event_hash` (64-hex token) is supplied, it must exactly equal the latest matching `event_hash` (lowercase) — mismatch is stale grant → FAIL. This allows callers to pass the `event_hash` of the `append_event` they just performed and structurally block reuse of an older grant.
  - On success returns the granting event dict; on failure raises `AuditError` (or `AuditChainError`/`AuditSchemaError` if chain broken).

This repairs both bootstrap fail-opens and adds the requested `event_hash` token API.

### 2.4 Holdout `outcome` strict
- `verify_holdout_access_allowed` no longer treats `outcome=None` as success. Only `success` / `allowed` grant. Tests for `None` / failure now correctly FAIL.

## 3. Fingerprint repairs (`eval/retrieval_v2/cycle3_fingerprint.py`)

### 3.1 `validate_fingerprint_manifest(manifest)` — new explicit validator
- `fingerprint_version == "v1"` required.
- `normalization_spec == NORMALIZATION_SPEC` required.
- `query_fingerprints` / `gold_fingerprints` keys required; `missing` / `None` / non-list → FAIL.
- Each fingerprint must be `64-hex`.
- Duplicate fingerprint inside same manifest → error (no silent `set` dedup).
- If `cases` present: must be positive `int` (not `bool`), and `len(query_fingerprints) == cases` and `len(gold_fingerprints) == cases` exactly, else FAIL.

### 3.2 `manifest_with_fingerprints()` — fail-closed
- Validates hex, detects duplicates before dedup, validates `cases` count mismatch, rejects `None`/type mismatch. No longer silently dedups or hides count mismatch. Calls `validate_fingerprint_manifest` on result.

### 3.3 `check_overlap()` — validated only
- Calls `validate_fingerprint_manifest` on **both** manifests before any overlap calc → empty `{}` or missing keys now FAIL instead of returning 0.
- Uses case-insensitive hex sets (`lower()`), reports `query_overlap`/`gold_overlap` counts and up to 3 examples; `strict=True` raises `ValueError` on any overlap >0.

## 4. Provenance clarification

- `prereg-v1.json:created_at = 2026-08-30T00:00:00Z` was a nominal placeholder; canonical freeze is the peeled bootstrap commit time `2026-08-30T18:34:01+09:00` (`09:34:01Z`, epoch `1788082441`). See `docs/RETRIEVAL_V2_CYCLE3_PREREG_ADDENDUM.md` and `eval/retrieval-v2/cycle3/prereg-v1.provenance.json`.
- Original `prereg-v1.json` SHA256 `18B6C997EB71A8CDFF36D84FF46B5BBB6B699874FF6D0FCCD18636F00268E156` (verified via `sha256sum`), tag object `2a30e8d371b9892f29ebcc21a81ab48ed9614378` → peeled commit `e4e56198ba3faef7ae687e356e41bf2d7543c198` (verified via `git rev-parse` / `git cat-file -p`).

## 5. Candidate / selection immutability

- Candidate IDs `c3e1-vector-pool-128` / `c3e2-vector-pool-256` / `c3e3-vector-pool-512`, pool K `128/256/512`, final N `30`, SQL template (nearest → vector_pool → lexical on K only → youth/lexical ORDER BY → LIMIT 30), selection predicates, tie-break, `max=3`, and D-003/D-004/D-007/D-011 contracts are **unchanged**. `prereg-v1.json` not edited; `retrieval-v2-cycle3-start-v1` not moved/deleted.

## 6. Tests (pure/static only)

- Regression suite `eval/test_retrieval_v2_cycle3_infra_repair.py` directly proves each fail-closed condition listed in the task (missing keys, wrong version/spec, invalid hash, duplicate/count mismatch, stale `set_sha`/`session_id`/`access_end`/`outcome`/`UUID`/`timestamp`/`git provenance`).
- Existing `test_retrieval_v2_cycle3_*` updated to conform to repaired strict schema (valid 64-hex `set_sha`, explicit UUID v4, valid timestamps, `session_id` etc.) and still PASS.
- No DB/retrieval/model/embedding/benchmark or protected plaintext access in any test (`pure/static`).

## 7. Verification gates (must all PASS before push/tag)

- `python -m py_compile` on changed modules
- `pytest eval/test_retrieval_v2_cycle3_*.py` (all PASS)
- `git diff --check` PASS
- `git diff HEAD~1 HEAD -- ml-service/` diff 0, `eval/retrieval-v2/` historical result artifacts diff 0
- prohibited access/run 0

## 8. Tag

Single infra-repair commit on `codex/retrieval-v2-cycle3-start`, annotated tag `retrieval-v2-cycle3-infra-v2` (this repair), pushed with verification of local/origin/actual remote peeled commit match and clean working tree.
