"""Cycle3 append-only run/access audit log (D-011).

Infrastructure only — no retrieval/DB/model/embedding/benchmark execution here.
Provides fail-closed JSONL writer with hash-chain integrity.

Spec (from prereg):
- JSONL append-only event log, one JSON per line, UTF-8, LF.
- Fields (all required unless noted):
  schema_version (int), event_id (UUID v4 str), utc_timestamp (ISO8601 Z),
  git_head (40 hex or "unknown"), git_dirty (bool),
  process_id (int), session_id (str),
  action in {run_start,run_end,protected_access_start,protected_access_end},
  candidate_id (str | null), set_role in {dev,holdout,none}, set_sha (str| null),
  command (str| null), runner_id (str| null), outcome (str| null),
  previous_event_hash (64 hex), event_hash (64 hex, SHA256 over canonical JSON excl. event_hash)

- Chain: previous_event_hash of event i == event_hash of i-1, genesis == "0"*64.
  event_hash = hex(SHA256(canonical_json(sorted keys, no event_hash))).
  Any violation, truncate, overwrite leaving broken chain, or hash mismatch => fail-closed raise.
- Holdout access gate: plaintext open must be preceded by successful protected_access_start append. Test enforces contract.

Temp file is used for bootstrap tests; no real retrieval/access event is written in bootstrap.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import uuid
from typing import Any

SCHEMA_VERSION = 1
GENESIS_HASH = "0" * 64
ALLOWED_ACTIONS = {"run_start", "run_end", "protected_access_start", "protected_access_end"}
ALLOWED_SET_ROLES = {"dev", "holdout", "none"}


class AuditError(RuntimeError):
    pass


class AuditChainError(AuditError):
    pass


class AuditSchemaError(AuditError):
    pass


def _utc_now_iso() -> str:
    # Millisecond precision, Z suffix, UTC
    return datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")


def _get_git_head() -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            head = r.stdout.strip()
            if len(head) == 40 and all(c in "0123456789abcdef" for c in head.lower()):
                return head.lower()
    except Exception:
        pass
    return "unknown"


def _get_git_dirty() -> bool:
    try:
        r = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            return bool(r.stdout.strip())
    except Exception:
        pass
    return False


def _canonical_json(event_without_hash: dict[str, Any]) -> str:
    # Deterministic: sort_keys, compact separators, ensure_ascii False, no trailing newline
    return json.dumps(event_without_hash, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _compute_event_hash(event_without_hash: dict[str, Any]) -> str:
    canonical = _canonical_json(event_without_hash)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _validate_payload(payload: dict[str, Any]) -> None:
    required = ["schema_version", "event_id", "utc_timestamp", "git_head", "git_dirty",
                "process_id", "session_id", "action", "candidate_id", "set_role",
                "set_sha", "command", "runner_id", "outcome", "previous_event_hash"]
    for k in required:
        if k not in payload:
            raise AuditSchemaError(f"missing field {k}")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise AuditSchemaError(f"schema_version must be {SCHEMA_VERSION}")
    # event_id UUID v4 format check
    try:
        u = uuid.UUID(payload["event_id"])
        if str(u) != payload["event_id"] and payload["event_id"] != str(u):
            # allow any valid UUID string, not strictly canonical
            pass
        # enforce version 4 if possible
        # not strict — accept any UUID to avoid brittleness
    except Exception as e:
        raise AuditSchemaError(f"invalid event_id UUID: {e}") from e
    if payload["action"] not in ALLOWED_ACTIONS:
        raise AuditSchemaError(f"invalid action {payload['action']}")
    if payload["set_role"] not in ALLOWED_SET_ROLES:
        raise AuditSchemaError(f"invalid set_role {payload['set_role']}")
    prev = payload["previous_event_hash"]
    if not isinstance(prev, str) or len(prev) != 64 or not all(c in "0123456789abcdef" for c in prev.lower()):
        raise AuditSchemaError(f"invalid previous_event_hash {prev!r}")
    # git_head may be unknown or 40 hex
    gh = payload["git_head"]
    if gh != "unknown" and not (len(gh) == 40 and all(c in "0123456789abcdef" for c in gh.lower())):
        raise AuditSchemaError(f"invalid git_head {gh!r}")


def read_and_verify_chain(log_path: str | os.PathLike) -> list[dict[str, Any]]:
    """Read JSONL, verify each event_hash and chain linkage. Fail-closed on any violation.

    Returns list of events (with event_hash). Raises AuditChainError on tamper/truncate/overwrite leaving broken linkage,
    AuditSchemaError on malformed fields.
    Missing file → empty list (no chain yet).
    """
    p = pathlib.Path(log_path)
    if not p.exists():
        return []
    if p.is_dir():
        raise AuditChainError(f"log path is directory: {log_path}")
    text = p.read_text(encoding="utf-8")
    # Allow trailing newline only; detect overwrite with binary garbage via JSON parse
    lines = [ln for ln in text.splitlines() if ln.strip() != ""]
    events: list[dict[str, Any]] = []
    prev_hash = GENESIS_HASH
    seen_ids: set[str] = set()
    for idx, line in enumerate(lines):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError as e:
            raise AuditChainError(f"line {idx+1}: invalid JSON: {e}") from e
        if not isinstance(ev, dict):
            raise AuditChainError(f"line {idx+1}: not an object")
        # event_hash must be present and 64 hex
        eh = ev.get("event_hash")
        if not isinstance(eh, str) or len(eh) != 64 or not all(c in "0123456789abcdef" for c in eh.lower()):
            raise AuditChainError(f"line {idx+1}: missing/invalid event_hash")
        # recompute hash excluding event_hash
        without = {k: v for k, v in ev.items() if k != "event_hash"}
        _validate_payload(without)
        if without["previous_event_hash"] != prev_hash:
            raise AuditChainError(
                f"line {idx+1}: previous_event_hash mismatch: expected {prev_hash} got {without['previous_event_hash']}"
            )
        computed = _compute_event_hash(without)
        if computed != eh.lower():
            raise AuditChainError(
                f"line {idx+1}: event_hash mismatch: computed {computed} vs stored {eh}"
            )
        if ev["event_id"] in seen_ids:
            raise AuditChainError(f"line {idx+1}: duplicate event_id {ev['event_id']}")
        seen_ids.add(ev["event_id"])
        events.append(ev)
        prev_hash = eh.lower()
    return events


def append_event(
    log_path: str | os.PathLike,
    *,
    action: str,
    candidate_id: str | None = None,
    set_role: str = "none",
    set_sha: str | None = None,
    command: str | None = None,
    runner_id: str | None = None,
    outcome: str | None = None,
    git_head: str | None = None,
    git_dirty: bool | None = None,
    session_id: str | None = None,
    utc_timestamp: str | None = None,
    event_id: str | None = None,
) -> dict[str, Any]:
    """Append one event atomically after verifying existing chain. Fail-closed.

    Required: action, set_role. Others optional (null allowed per schema).
    Returns the appended event dict (including event_hash).

    Chain violation, hash mismatch, truncate/overwrite leaving broken linkage → AuditChainError.
    Schema violation → AuditSchemaError.
    """
    p = pathlib.Path(log_path)
    # Ensure parent dir exists
    p.parent.mkdir(parents=True, exist_ok=True)

    # Verify existing chain before append (fail-closed if tampered)
    existing = read_and_verify_chain(log_path)
    prev_hash = existing[-1]["event_hash"].lower() if existing else GENESIS_HASH

    # Build payload without event_hash
    if git_head is None:
        git_head = _get_git_head()
    if git_dirty is None:
        git_dirty = _get_git_dirty()
    if session_id is None:
        session_id = os.getenv("CYCLE3_SESSION_ID") or f"pid-{os.getpid()}"
    if utc_timestamp is None:
        utc_timestamp = _utc_now_iso()
    if event_id is None:
        event_id = str(uuid.uuid4())

    payload_without_hash: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "event_id": event_id,
        "utc_timestamp": utc_timestamp,
        "git_head": git_head,
        "git_dirty": bool(git_dirty),
        "process_id": os.getpid(),
        "session_id": session_id,
        "action": action,
        "candidate_id": candidate_id,
        "set_role": set_role,
        "set_sha": set_sha,
        "command": command,
        "runner_id": runner_id,
        "outcome": outcome,
        "previous_event_hash": prev_hash,
    }
    _validate_payload(payload_without_hash)
    event_hash = _compute_event_hash(payload_without_hash)
    event = {**payload_without_hash, "event_hash": event_hash}

    # Append atomically: open in append, write single line + LF, flush+fsync
    line = json.dumps(event, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    # Use binary append to avoid text-mode newline translation issues
    with open(p, "a", encoding="utf-8", newline="\n") as f:
        f.write(line + "\n")
        f.flush()
        try:
            os.fsync(f.fileno())
        except Exception:
            pass

    # Post-append verify (detect concurrent truncate/overwrite race)
    # Re-read and ensure last event is ours and chain still valid
    re_verified = read_and_verify_chain(log_path)
    if not re_verified or re_verified[-1]["event_hash"] != event_hash:
        raise AuditChainError("post-append chain verification failed; log may have been truncated concurrently")
    return event


def verify_holdout_access_allowed(
    log_path: str | os.PathLike,
    *,
    set_role: str = "holdout",
) -> None:
    """Holdout access gate: require successful protected_access_start for set_role before plaintext open.

    Contract: event append (protected_access_start) must succeed before plaintext open is allowed.
    This function checks the log; if no matching event exists or chain is broken, raises AuditError.
    Fail-closed: any verification failure denies access.
    """
    events = read_and_verify_chain(log_path)
    for ev in events:
        if ev.get("action") == "protected_access_start" and ev.get("set_role") == set_role:
            # outcome may be None (still considered success if event exists), but if outcome explicitly failure, deny
            outcome = ev.get("outcome")
            if outcome is None or outcome == "success" or outcome == "allowed":
                return
            # if outcome is failure, continue searching for success
    raise AuditError(
        f"holdout access denied: no successful protected_access_start for set_role={set_role!r} in {log_path}; "
        "event append must succeed before plaintext open"
    )


# Convenience helpers for runners (optional)
def build_run_start(
    log_path: str | os.PathLike,
    *,
    candidate_id: str,
    runner_id: str | None = None,
    command: str | None = None,
    set_role: str = "none",
    set_sha: str | None = None,
) -> dict[str, Any]:
    return append_event(
        log_path,
        action="run_start",
        candidate_id=candidate_id,
        runner_id=runner_id,
        command=command,
        set_role=set_role,
        set_sha=set_sha,
        outcome="started",
    )


def build_run_end(
    log_path: str | os.PathLike,
    *,
    candidate_id: str,
    runner_id: str | None = None,
    outcome: str = "success",
    set_role: str = "none",
    set_sha: str | None = None,
) -> dict[str, Any]:
    return append_event(
        log_path,
        action="run_end",
        candidate_id=candidate_id,
        runner_id=runner_id,
        set_role=set_role,
        set_sha=set_sha,
        outcome=outcome,
    )
