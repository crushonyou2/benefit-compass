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

---

# Retrieval v2 Cycle3 — NARROW INFRA REPAIR v3 (this session) — Sol/High + Luna Max 합의 3개만

> **Branch:** `codex/retrieval-v2-cycle3-start` (from `87bb13f28cf4f6484f2c1141951da608c12139fb` infra-v2)
> **Scope:** NARROW INFRA REPAIR only — 정확히 3개 blocker만 보수, 범위 확장 없음. No retrieval/DB/model/embedding/benchmark, no historical/fresh protected plaintext, no fresh dev/holdout 생성, no candidate/prereg K/selection semantics 수정, no production ml-service, no existing result artifact 수정, no history rewrite, no new external audit store/HMAC/file-lock/signature, no final-holdout approval-token 결합.

This repair addresses exactly the 3 blockers that independent Sol/High + Luna Max reviewers 합의한 것으로, 이전 INFRA REPAIR v2 이후 추가 fail-open 3건을 보수한다.

## 9. Blocker 1 — audit latest-start fail-open (`verify_holdout_access_allowed` latest outcome strict)

- **Fail-open (before):** `verify_holdout_access_allowed()`가 `success`/`allowed`만 필터링한 뒤 최신을 골랐다. 동일 `set_role`+`set_sha`+`session_id`에서 `success → failure` 또는 `success → None` 순서로 이벤트가 기록되면, 최신이 `failure`/`None`임에도 불구하고 이전 `success`가 최신 success로 남아 grant되어 DENY 해야 할 접근을 ALLOW 했다.
- **Repair (`eval/retrieval_v2/cycle3_audit.py:verify_holdout_access_allowed`):**
  - 동일 `set_role`+`set_sha`+`session_id`의 **모든** `protected_access_start`를 수집한 뒤 chain 순서상 **최신**(마지막) 이벤트를 먼저 선택.
  - 그 latest `outcome`이 `"success"` 또는 `"allowed"`일 때만 grant. `None`, `""`, `"failure"`, `"failed"`, `"error"` 등은 모두 DENY (`AuditError`).
  - 이후 `protected_access_end` closed check 및 `expected_event_hash` token check는 latest grant에 대해서만 수행.
  - 검증 계약: `success→failure` / `success→None` / `success→""` 는 반드시 DENY, `failure→success` 는 최신이 success이므로 GRANT, 단일 failure/None 도 DENY.
- **Regression tests (pure/static):** `eval/test_retrieval_v2_cycle3_infra_repair.py::AuditLatestStartFailOpenTest` — `test_success_then_failure_denies`, `test_success_then_none_denies`, `test_success_then_empty_string_denies`, `test_failure_then_success_grants`, `test_single_failure_denies`, `test_success_then_allowed_grants` 6건으로 최신 outcome strict를 직접 증명. 기존 `AuditInfraRepairTest`의 `test_outcome_none_and_failure_fail`, `test_access_end_closes_grant_fail` 등은 그대로 PASS (latest가 success일 때만 grant).

## 10. Blocker 2 — protected-set fingerprint builder gate (cases 필수·exact·0금지)

- **Fail-open (before):** `validate_fingerprint_manifest()`가 `cases`가 있을 때만 검증하고, 없으면 통과했다. `manifest_with_fingerprints()`는 `cases`를 요구했으나, `check_overlap({}, {}, strict=True)` 가 이미 v2에서 missing keys로 FAIL 된 뒤에도, `fingerprint_version`/`normalization_spec`을 갖춘 빈 manifest (`query_fingerprints: []`, `gold_fingerprints: [], cases 없음 또는 0`) 가 `check_overlap`에서 overlap 0 PASS로 인증될 수 있었다. Historical catalog / fresh holdout / fresh dev builder가 빈 manifest를 만들어 overlap 0을 인증하는 fail-open.
- **Repair (`eval/retrieval_v2/cycle3_fingerprint.py:validate_fingerprint_manifest` — builder/protected-set validation 경계):**
  - 범용 helper `fingerprints_for_items()` / `query_fingerprint()` / `gold_fingerprint()` / `normalize_query()` 는 그대로 유지 (과도하게 바꾸지 않음).
  - **Builder/protected-set validation 경계**인 `validate_fingerprint_manifest()`에서 `cases`를 **필수**로 변경: `missing` → `ValueError`, `cases <=0` → `ValueError` (0건 금지, positive int만 허용, `bool` 금지), `len(query_fingerprints) != cases` 또는 `len(gold_fingerprints) != cases` → `ValueError` (exact 일치).
  - `manifest_with_fingerprints()`는 이미 `cases>0` 및 exact를 강제했으나, 이제 `validate_fingerprint_manifest()`까지 동일 게이트로 이중 방어. 빈 manifest (`[]`/`[]`/`cases 없음` 또는 `cases 0`) 는 어떤 경로로도 PASS 불가, 반드시 FAIL.
  - `check_overlap()`는 `validate_fingerprint_manifest()`를 양쪽에 호출하므로, 빈 manifest overlap 0 PASS는 fail-closed DENY. `fingerprint_version`/`normalization_spec`이 correct여도 `cases` 없거나 0이면 FAIL.
  - 검증 계약: `cases` 필수, `cases>0`, `query_fingerprints.length == cases && gold_fingerprints.length == cases` 정확 일치, 0 금지. 빈 manifest는 인증 불가.
- **Regression tests (pure/static):** `eval/test_retrieval_v2_cycle3_infra_repair.py::FingerprintBuilderGateTest` — `test_missing_cases_fails`, `test_zero_cases_forbidden`, `test_empty_manifest_no_cases_cannot_pass_overlap`, `test_cases_exact_count_required`, `test_builder_empty_fingerprint_lists_fail` 5건으로 빈 manifest PASS 불가 및 count exact를 직접 증명. `eval/test_retrieval_v2_cycle3_fingerprint.py`는 `_m` helper가 `cases`를 auto-infer 하도록 갱신하고, `test_check_overlap_pure_no_file_access`가 빈 manifest는 FAIL을 기대하도록, `test_no_protected_plaintext_read_in_this_test`가 `manifest_with_fingerprints`로 cases를 포함하도록 수정되어 PASS.

## 11. Blocker 3 — audit durability (`append_event` `os.fsync` failure must not be swallowed)

- **Fail-open (before):** `append_event()`가 `f.flush()` 후 `os.fsync(f.fileno())`를 `try: os.fsync ... except Exception: pass` 로 삼켰다. 디스크 fsync 실패 시에도 `event`와 `event_hash`를 성공으로 반환해, durability가 보장되지 않았음에도 caller가 success token을 받아 protected access gate 등에 재사용할 수 있었다.
- **Repair (`eval/retrieval_v2/cycle3_audit.py:append_event`):**
  - `os.fsync` 실패를 삼키지 않고 `AuditError(f\"fsync failed for {p}: {e}\") from e` 로 전파.
  - 실패 시 `event`/`event_hash`를 성공으로 반환하지 않으며, chain post-verify도 도달하지 않음 (fail-closed, no success token).
  - 검증 계약: `os.fsync`가 `OSError`/`Exception`을 던지면 `append_event`는 `AuditError`를 던지고 caller는 token을 받지 못한다. fsync 성공 시 기존 동작 유지.
- **Regression tests (pure/static):** `eval/test_retrieval_v2_cycle3_infra_repair.py::AuditDurabilityTest` — `test_fsync_failure_raises_audit_error` (mock `os.fsync` raise → `AuditError` 및 메시지 `fsync` 포함), `test_fsync_failure_no_success_token` (token `None` 보장, call count 1), `test_fsync_success_still_works` (정상 시 `event_hash` 반환 및 chain 1건) 3건으로 durability fail-closed를 직접 증명. `unittest.mock` 없이 `audit_mod.os.fsync`를 monkey-patch 하여 pure/static, no DB/retrieval.

## 12. Tests & gates (this narrow repair, pure/static only)

- `eval/test_retrieval_v2_cycle3_infra_repair.py`에 `AuditLatestStartFailOpenTest` 6건 + `FingerprintBuilderGateTest` 5건 + `AuditDurabilityTest` 3건 = **14건 신규**를 추가하고, 기존 `FingerprintInfraRepairTest`/`AuditInfraRepairTest` 및 `test_retrieval_v2_cycle3_fingerprint.py`/`test_retrieval_v2_cycle3_audit.py`/`test_retrieval_v2_cycle3_prereg.py`를 `cases` mandatory 등 strict에 맞춰 갱신. 전체 `pytest eval/test_retrieval_v2_cycle3_*.py` **62 passed** (기존 48 + 신규 14), `py_compile` PASS, `git diff --check` PASS.
- `ml-service/` diff 0, `eval/retrieval-v2/` historical result artifacts diff 0, 금지 동작 0 (retrieval/DB/model/embedding/benchmark 미실행, protected plaintext 미접근, fresh dev/holdout 미생성, candidate/prereg K/selection semantics 미수정, production ml-service 미수정, existing result artifact 미수정, history rewrite 없음, 새로운 외부 audit store/HMAC/file-lock/signature 등 범위 확장 없음, final-holdout approval-token 결합 없음).
- 검증: pure/static tests만, 기존 관련 테스트 + 새 회귀 모두 통과, `py_compile`/`git diff --check`/`production diff 0` 확인, Web 개입 없음 (self-contained plan→implementation→tests→self-review→정리).
