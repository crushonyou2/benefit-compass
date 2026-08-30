"""Cycle3 append-only run/access audit log (D-011) — INFRA REPAIR v2.

Infrastructure only — no retrieval/DB/model/embedding/benchmark execution here.
Provides fail-closed JSONL writer with hash-chain integrity.

Spec (from prereg + infra-repair):
- JSONL append-only event log, one JSON per line, UTF-8, LF.
- Fields (all required unless noted):
  schema_version (int), event_id (UUID v4 str), utc_timestamp (ISO8601 Z),
  git_head (40 hex, fail-closed if unknown), git_dirty (bool),
  process_id (positive int), session_id (non-empty str),
  action in {run_start,run_end,protected_access_start,protected_access_end},
  candidate_id (str | null), set_role in {dev,holdout,none}, set_sha (64-hex for dev/holdout, None for none),
  command (str | null), runner_id (str | null), outcome (str | null),
  previous_event_hash (64 hex), event_hash (64 hex, SHA256 over canonical JSON excl. event_hash)

- Chain: previous_event_hash of event i == event_hash of i-1, genesis == "0"*64.
  event_hash = hex(SHA256(canonical_json(sorted keys, no event_hash))).
  Any violation, truncate, overwrite leaving broken chain, or hash mismatch => fail-closed raise.
- Holdout access gate: plaintext open must be preceded by successful protected_access_start append
  with exact set_sha + exact session_id + latest matching start not closed by protected_access_end.
  outcome must be explicit success/allowed (None/failure denied). Optional expected_event_hash
  token verifies exact latest event to structurally block stale grants.
- Git provenance: if git_head/git_dirty not explicitly supplied, they are probed via git.
  Probe failure => FAIL (no silent fallback to unknown/False).

Temp file is used for bootstrap tests; no real retrieval/access event is written in bootstrap.
"""

from __future__ import annotations

import datetime
import hashlib
import json
import os
import pathlib
import re
import subprocess
import uuid
from typing import Any

SCHEMA_VERSION = 1
GENESIS_HASH = "0" * 64
ALLOWED_ACTIONS = {"run_start", "run_end", "protected_access_start", "protected_access_end"}
ALLOWED_SET_ROLES = {"dev", "holdout", "none"}

_UUID_V4_RE = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
_HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")


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
    """Strict git HEAD probe — fail-closed on any failure (no fallback to 'unknown')."""
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, timeout=5)
    except Exception as e:
        raise AuditError(f"git rev-parse HEAD probe failed: {e}") from e
    if r.returncode != 0:
        raise AuditError(f"git rev-parse HEAD failed (rc={r.returncode}): {r.stderr.strip()}")
    head = r.stdout.strip()
    if not _HEX40_RE.match(head.lower()):
        raise AuditError(f"git HEAD is not 40-hex: {head!r}")
    return head.lower()


def _get_git_dirty() -> bool:
    """Strict git dirty probe — fail-closed on failure (no fallback to False)."""
    try:
        r = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, timeout=5)
    except Exception as e:
        raise AuditError(f"git status --porcelain probe failed: {e}") from e
    if r.returncode != 0:
        raise AuditError(f"git status --porcelain failed (rc={r.returncode}): {r.stderr.strip()}")
    return bool(r.stdout.strip())


def _canonical_json(event_without_hash: dict[str, Any]) -> str:
    # Deterministic: sort_keys, compact separators, ensure_ascii False, no trailing newline
    return json.dumps(event_without_hash, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def _compute_event_hash(event_without_hash: dict[str, Any]) -> str:
    canonical = _canonical_json(event_without_hash)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _is_hex64(s: str) -> bool:
    return isinstance(s, str) and bool(_HEX64_RE.match(s.lower()))


def _is_hex40(s: str) -> bool:
    return isinstance(s, str) and bool(_HEX40_RE.match(s.lower()))


def _validate_uuid_v4(event_id: Any) -> None:
    if not isinstance(event_id, str):
        raise AuditSchemaError(f"event_id must be str, got {type(event_id).__name__}")
    low = event_id.lower()
    if not _UUID_V4_RE.match(low):
        raise AuditSchemaError(f"event_id must be UUID v4 (xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx, y in 8/9/a/b), got {event_id!r}")
    try:
        u = uuid.UUID(event_id)
    except Exception as e:
        raise AuditSchemaError(f"invalid event_id UUID: {e}") from e
    if u.version != 4:
        raise AuditSchemaError(f"event_id UUID version must be 4, got {u.version} for {event_id!r}")
    # Accept any case, normalized to lower; no strict canonical mismatch beyond regex+version

def _validate_timestamp(ts: Any) -> None:
    if not isinstance(ts, str):
        raise AuditSchemaError(f"utc_timestamp must be str, got {type(ts).__name__}")
    if not _TIMESTAMP_RE.match(ts):
        raise AuditSchemaError(f"utc_timestamp must be ISO8601 UTC Z (YYYY-MM-DDTHH:MM:SS[.frac]Z), got {ts!r}")
    # Try to parse to ensure valid date (e.g., month 13 fails)
    try:
        # Replace Z with +00:00 for fromisoformat
        iso = ts.replace("Z", "+00:00")
        dt = datetime.datetime.fromisoformat(iso)
        if dt.tzinfo is None:
            raise AuditSchemaError(f"utc_timestamp missing timezone: {ts!r}")
        # Ensure it's UTC
        if dt.utcoffset() != datetime.timedelta(0):
            raise AuditSchemaError(f"utc_timestamp must be UTC Z, got {ts!r}")
    except AuditSchemaError:
        raise
    except Exception as e:
        raise AuditSchemaError(f"invalid utc_timestamp {ts!r}: {e}") from e


def _validate_payload(payload: dict[str, Any]) -> None:
    required = ["schema_version", "event_id", "utc_timestamp", "git_head", "git_dirty",
                "process_id", "session_id", "action", "candidate_id", "set_role",
                "set_sha", "command", "runner_id", "outcome", "previous_event_hash"]
    for k in required:
        if k not in payload:
            raise AuditSchemaError(f"missing field {k}")
    if payload["schema_version"] != SCHEMA_VERSION:
        raise AuditSchemaError(f"schema_version must be {SCHEMA_VERSION}")
    _validate_uuid_v4(payload["event_id"])
    _validate_timestamp(payload["utc_timestamp"])
    if payload["action"] not in ALLOWED_ACTIONS:
        raise AuditSchemaError(f"invalid action {payload['action']}")
    if payload["set_role"] not in ALLOWED_SET_ROLES:
        raise AuditSchemaError(f"invalid set_role {payload['set_role']}")
    prev = payload["previous_event_hash"]
    if not isinstance(prev, str) or not _HEX64_RE.match(prev.lower()):
        raise AuditSchemaError(f"invalid previous_event_hash {prev!r} (must be 64-hex)")
    # git_head strict 40-hex (no 'unknown')
    gh = payload["git_head"]
    if not isinstance(gh, str) or not _HEX40_RE.match(gh.lower()):
        raise AuditSchemaError(f"invalid git_head {gh!r} (must be 40-hex, unknown not allowed)")
    # git_dirty strict bool
    if not isinstance(payload["git_dirty"], bool):
        raise AuditSchemaError(f"git_dirty must be bool, got {type(payload['git_dirty']).__name__}: {payload['git_dirty']!r}")
    # process_id positive int (not bool)
    pid = payload["process_id"]
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        raise AuditSchemaError(f"process_id must be positive int, got {pid!r}")
    # session_id non-empty str
    sid = payload["session_id"]
    if not isinstance(sid, str) or not sid.strip():
        raise AuditSchemaError(f"session_id must be non-empty str, got {sid!r}")
    # set_role / set_sha / action semantics (fail-closed)
    set_role = payload["set_role"]
    set_sha = payload["set_sha"]
    action = payload["action"]
    # set_sha semantics: dev/holdout => 64-hex, none => None
    if set_role in ("dev", "holdout"):
        if not isinstance(set_sha, str) or not _HEX64_RE.match(set_sha.lower()):
            raise AuditSchemaError(f"set_sha must be 64-hex for set_role={set_role!r}, got {set_sha!r}")
    elif set_role == "none":
        if set_sha is not None:
            raise AuditSchemaError(f"set_sha must be None for set_role='none', got {set_sha!r}")
    # action/role semantics for protected access: protected_access_* must have dev/holdout
    if action in ("protected_access_start", "protected_access_end"):
        if set_role not in ("dev", "holdout"):
            raise AuditSchemaError(f"action {action!r} requires set_role dev/holdout, got {set_role!r}")
        # set_sha already validated as 64-hex above
    # candidate_id if not None must be non-empty str
    cid = payload["candidate_id"]
    if cid is not None and (not isinstance(cid, str) or not cid.strip()):
        raise AuditSchemaError(f"candidate_id must be str or None, got {cid!r}")
    # command/runner_id/outcome if not None must be str (allow empty? but check type)
    for k in ("command", "runner_id", "outcome"):
        v = payload[k]
        if v is not None and not isinstance(v, str):
            raise AuditSchemaError(f"{k} must be str or None, got {type(v).__name__}: {v!r}")


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
        if not isinstance(eh, str) or not _HEX64_RE.match(eh.lower()):
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
    process_id: int | None = None,
) -> dict[str, Any]:
    """Append one event atomically after verifying existing chain. Fail-closed.

    Required: action, set_role. Others optional (null allowed per schema).
    Returns the appended event dict (including event_hash).

    Chain violation, hash mismatch, truncate/overwrite leaving broken linkage → AuditChainError.
    Schema violation → AuditSchemaError.
    Git provenance probe failure → AuditError (fail-closed, no fallback to unknown/False).
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
    else:
        # Validate supplied git_head early to give clear error (also validated in _validate_payload)
        if not isinstance(git_head, str) or not _HEX40_RE.match(git_head.lower()):
            raise AuditSchemaError(f"invalid git_head {git_head!r} (must be 40-hex)")
        git_head = git_head.lower()
    if git_dirty is None:
        git_dirty = _get_git_dirty()
    else:
        if not isinstance(git_dirty, bool):
            raise AuditSchemaError(f"git_dirty must be bool, got {type(git_dirty).__name__}: {git_dirty!r}")
    if session_id is None:
        session_id = os.getenv("CYCLE3_SESSION_ID") or f"pid-{os.getpid()}"
    if not isinstance(session_id, str) or not session_id.strip():
        raise AuditSchemaError(f"session_id must be non-empty str, got {session_id!r}")
    if utc_timestamp is None:
        utc_timestamp = _utc_now_iso()
    else:
        _validate_timestamp(utc_timestamp)
    if event_id is None:
        event_id = str(uuid.uuid4())
    else:
        _validate_uuid_v4(event_id)
    if process_id is None:
        process_id = os.getpid()
    if not isinstance(process_id, int) or isinstance(process_id, bool) or process_id <= 0:
        raise AuditSchemaError(f"process_id must be positive int, got {process_id!r}")

    payload_without_hash: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "event_id": event_id.lower() if isinstance(event_id, str) else event_id,
        "utc_timestamp": utc_timestamp,
        "git_head": git_head.lower(),
        "git_dirty": bool(git_dirty),
        "process_id": process_id,
        "session_id": session_id,
        "action": action,
        "candidate_id": candidate_id,
        "set_role": set_role,
        "set_sha": set_sha.lower() if isinstance(set_sha, str) else set_sha,
        "command": command,
        "runner_id": runner_id,
        "outcome": outcome,
        "previous_event_hash": prev_hash.lower(),
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
    set_sha: str | None = None,
    session_id: str | None = None,
    expected_event_hash: str | None = None,
) -> dict[str, Any]:
    """Holdout/dev protected access gate — fail-closed.

    Requires exact set_sha + exact session_id + most recent matching protected_access_start
    with explicit success/allowed outcome, not closed by a later protected_access_end.

    Stale grants (different set_sha, different session_id, or already closed) are denied.
    outcome=None/failure is denied (only success/allowed).

    If expected_event_hash is supplied, the latest matching start's event_hash must equal it,
    structurally blocking stale grants that reuse an older event_hash token.

    Returns the granting event dict on success; raises AuditError/AuditChainError/AuditSchemaError on denial.
    """
    if set_role not in ("dev", "holdout"):
        raise AuditError(f"protected access gate requires set_role dev/holdout, got {set_role!r}")
    if not isinstance(set_sha, str) or not _HEX64_RE.match(set_sha.lower()):
        raise AuditError(f"protected access gate requires set_sha 64-hex for set_role={set_role!r}, got {set_sha!r}")
    if not isinstance(session_id, str) or not session_id.strip():
        raise AuditError(f"protected access gate requires non-empty session_id, got {session_id!r}")
    if expected_event_hash is not None:
        if not isinstance(expected_event_hash, str) or not _HEX64_RE.match(expected_event_hash.lower()):
            raise AuditError(f"expected_event_hash must be 64-hex, got {expected_event_hash!r}")
        expected_event_hash = expected_event_hash.lower()
    set_sha = set_sha.lower()

    events = read_and_verify_chain(log_path)
    # Find all matching protected_access_start with exact set_sha+session_id+success outcome
    candidates: list[tuple[int, dict[str, Any]]] = []
    for idx, ev in enumerate(events):
        if ev.get("action") == "protected_access_start" and ev.get("set_role") == set_role and isinstance(ev.get("set_sha"), str) and ev.get("set_sha","").lower() == set_sha and ev.get("session_id") == session_id:
            outcome = ev.get("outcome")
            if outcome in ("success", "allowed"):
                candidates.append((idx, ev))
    if not candidates:
        raise AuditError(
            f"protected access denied: no successful protected_access_start for set_role={set_role!r} set_sha={set_sha[:8]}... session_id={session_id!r} in {log_path}; "
            "event append must succeed with outcome success/allowed before plaintext open"
        )
    # Most recent is last in chain order
    latest_idx, latest = candidates[-1]
    # Check if a later protected_access_end for same set_role/set_sha/session_id closes the grant
    for later in events[latest_idx + 1:]:
        if later.get("action") == "protected_access_end" and later.get("set_role") == set_role and isinstance(later.get("set_sha"), str) and later.get("set_sha","").lower() == set_sha and later.get("session_id") == session_id:
            raise AuditError(
                f"protected access denied: grant for set_role={set_role!r} set_sha={set_sha[:8]}... session_id={session_id!r} was closed by protected_access_end at {later.get('event_hash')[:8]}... (stale grant)"
            )
    if expected_event_hash is not None and latest.get("event_hash","").lower() != expected_event_hash:
        raise AuditError(
            f"protected access denied: expected_event_hash {expected_event_hash[:8]}... does not match latest grant {latest.get('event_hash','')[:8]}... for set_role={set_role!r} set_sha={set_sha[:8]}... session_id={session_id!r} (stale grant token)"
        )
    return latest


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
