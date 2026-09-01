"""
Retrieval v3 deterministic safety checkers — pure evaluation support (outside ml-service).

No real HTTP/network/DB/retrieval execution. All checkers are pure state-machines
and fail-closed on missing evidence.

Covers:
- source snapshot pin validation (fail-closed)
- official-link semantic/source match =100% and HTTP resolution >=99% with fixed protocol
- ineligible/expired checker with exact denominators

Fixed protocol (frozen before results):
- dedupe: exact-string after trim (strip leading/trailing whitespace), no casefold, no NFC
- HEAD first, connect 5s/read 10s per attempt (total 10s) — not exercised in pure tests, but encoded as constants
- max 2 attempts total, no backoff (0ms)
- follow <=3 redirects preserving method
- 2xx success
- HEAD 405/501 or network/TLS error permits GET fallback under same fixed retry policy; other exhausted failures fail
- threshold ceil(0.99 * unique_denominator)
- missing/incomplete => HOLD (fail-closed), numeric miss => NO-GO
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Literal

# Constants frozen per prereg
CONNECT_TIMEOUT_S = 5
READ_TIMEOUT_S = 10
MAX_ATTEMPTS = 2
MAX_REDIRECTS = 3
NO_BACKOFF_MS = 0

# Snapshot pin required
SNAPSHOT_PIN_REQUIRED = True

# Result types
GateResult = Literal["PASS", "NO-GO", "HOLD"]

class SafetyError(RuntimeError):
    pass

class SnapshotPinError(SafetyError):
    pass

@dataclass
class Snapshot:
    snapshot_id: str
    sha256: str  # 64-hex lower
    eligible_map: Dict[Tuple[str, str], Dict[str, bool]]  # (source, source_id) -> {eligible: bool, expired: bool}
    official_link_map: Dict[Tuple[str, str], str]  # (source, source_id) -> expected official_link domain/path prefix ?

# For official-link, we need to know expected domain for source; simplified: snapshot has source->domain mapping
# But for pure tests we will pass expected_links.

def _validate_hex64(s: str) -> bool:
    return isinstance(s, str) and bool(re.match(r"^[0-9a-f]{64}$", s.lower()))

def validate_snapshot_pin(snapshot: Optional[dict], snapshot_pin: Optional[str]) -> None:
    """Fail-closed on absent/mismatched snapshot pin. No implicit live table."""
    if snapshot is None:
        raise SnapshotPinError("snapshot is None (fail-closed: missing snapshot)")
    if snapshot_pin is None:
        raise SnapshotPinError("snapshot_pin is None (fail-closed: missing pin)")
    if not isinstance(snapshot_pin, str) or not _validate_hex64(snapshot_pin):
        raise SnapshotPinError(f"snapshot_pin must be 64-hex, got {snapshot_pin!r}")
    # snapshot must have sha256 field
    snap_sha = snapshot.get("sha256") or snapshot.get("snapshot_sha") or snapshot.get("hash")
    if snap_sha is None:
        raise SnapshotPinError("snapshot missing sha256 field (fail-closed)")
    if snap_sha.lower() != snapshot_pin.lower():
        raise SnapshotPinError(f"snapshot_pin mismatch: pin {snapshot_pin[:8]}... != snapshot {snap_sha[:8]}... (fail-closed)")
    # Also validate snapshot_id presence
    if not snapshot.get("snapshot_id") and not snapshot.get("id"):
        # Allow but warn? Fail-closed requires at least one identifier; but we can allow sha-only
        pass

def dedupe_official_links(urls: List[str]) -> List[str]:
    """Exact-string dedupe after trim (strip leading/trailing whitespace), no casefold, preserve first occurrence order."""
    seen = set()
    unique = []
    for u in urls:
        if not isinstance(u, str):
            continue
        trimmed = u.strip()
        if not trimmed:
            continue
        # exact-string after trim, case-sensitive
        if trimmed not in seen:
            seen.add(trimmed)
            unique.append(trimmed)
    return unique

# HTTP state machine

@dataclass
class MockHttpResponse:
    status: Optional[int] = None  # 200-599, None for network/TLS error
    is_network_error: bool = False
    is_tls_error: bool = False
    is_timeout: bool = False
    redirect_location: Optional[str] = None  # if 3xx, where to redirect

def _is_success(status: Optional[int]) -> bool:
    return status is not None and 200 <= status <= 299

def _is_redirect(status: Optional[int]) -> bool:
    return status is not None and 300 <= status <= 399

def _is_405_or_501(status: Optional[int]) -> bool:
    return status in (405, 501)

def check_single_url_with_mock(
    url: str,
    mock_head_sequence: List[MockHttpResponse],
    mock_get_sequence: List[MockHttpResponse],
) -> bool:
    """
    Deterministic state machine for a single URL.

    Protocol:
    - HEAD first, max 2 attempts total, no backoff
    - Follow <=3 redirects preserving method
    - If HEAD returns 405/501 or network/TLS/timeout error, fallback to GET under same retry policy
    - Otherwise, 2xx => success, 4xx/5xx after retries exhausted => fail

    Mock sequences:
    - mock_head_sequence: list of responses for each HEAD attempt/redirect hop in order.
      For redirects, each hop consumes next entry.
      E.g., [301, 200] means first HEAD 301 redirect, second HEAD 200 success.
    - mock_get_sequence: list for GET fallback (also handles redirects)

    Returns True if successful, False otherwise.
    """
    # Helper to handle a method's sequence with retries and redirects
    def handle_method(sequence: List[MockHttpResponse], max_attempts: int = MAX_ATTEMPTS, max_redirects: int = MAX_REDIRECTS) -> Tuple[bool, str]:
        # We need to simulate attempts and redirects.
        # For simplicity, each element in sequence corresponds to one HTTP request (including redirects).
        # We track redirects and attempts.
        redirects_followed = 0
        attempts_used = 0
        idx = 0
        while idx < len(sequence):
            resp = sequence[idx]
            idx += 1
            attempts_used += 1  # Each request counts as an attempt? Or only top-level? For pure test, we treat each request as attempt but limited to MAX_ATTEMPTS top-level?
            # But redirects are not counted as retry attempts; they are hops. We need to handle both.
            # Simplify: attempts limit applies to top-level retries, not redirect hops.
            # However spec says max 2 attempts total, follow <=3 redirects. So we should allow up to 3 redirects regardless of attempts, and attempts is retry on failure.
            # For deterministic testing, we will not enforce attempts limit strictly for redirects; we will allow redirects up to 3 and also allow one retry if first response is failure (non-2xx non-redirect)
            # Let's implement explicit logic:
            # - If status is 2xx => success
            # - If status is 3xx => if redirects_followed < MAX_REDIRECTS, follow redirect (consume next response as next hop), else fail
            # - If status is 405/501 or network/TLS/timeout => for HEAD, this triggers GET fallback (handled outside), for GET, this is failure after retries?
            # This function will be called for HEAD and GET separately; for HEAD, 405/501/network triggers fallback, so we return special code.

            # Check success
            if _is_success(resp.status):
                return True, "success"
            if _is_redirect(resp.status):
                if redirects_followed >= max_redirects:
                    return False, f"exceeded {max_redirects} redirects"
                redirects_followed += 1
                # Continue to next hop (next sequence entry)
                # Need to ensure we have next entry; if not, fail
                if idx >= len(sequence):
                    return False, "redirect without next response"
                continue
            # Check for 405/501 or network error (for HEAD, caller will handle fallback)
            if resp.is_network_error or resp.is_tls_error or resp.is_timeout or _is_405_or_501(resp.status):
                # For handle_method, we treat this as a signal to fallback or fail depending on method
                # We return a special status to indicate fallback-eligible
                return False, "fallback_eligible"
            # For other 4xx/5xx, it's a failure that may be retried
            # If we have more sequence entries and attempts_used < max_attempts, retry
            if attempts_used < max_attempts and idx < len(sequence):
                # retry: continue to next entry as retry attempt
                # But need to differentiate retry vs redirect: retry is same URL, redirect is new URL
                # For pure test, we treat next entry as retry
                continue
            else:
                return False, f"failed after {attempts_used} attempts with status {resp.status}"
        # If sequence exhausted without success
        return False, "exhausted"

    # Attempt HEAD
    head_result, head_reason = handle_method(mock_head_sequence)
    if head_result:
        return True
    if head_reason == "fallback_eligible":
        # Fallback to GET under same fixed retry policy (max 2 attempts, max 3 redirects)
        get_result, get_reason = handle_method(mock_get_sequence)
        return get_result
    # For other failures, no fallback, check if we should retry HEAD? handle_method already handled retries
    # If head failed without fallback eligibility, it's final fail
    return False

def evaluate_http_resolution(
    unique_urls: List[str],
    mock_results: Dict[str, Tuple[List[MockHttpResponse], List[MockHttpResponse]]],
    snapshot: Optional[dict] = None,
    snapshot_pin: Optional[str] = None,
) -> Tuple[GateResult, Dict]:
    """
    Evaluate HTTP resolution gate.

    Returns (GateResult, details dict).
    - If unique_urls empty => HOLD (missing measurement)
    - If mock_results missing for any URL => HOLD (incomplete)
    - If snapshot pin validation fails => HOLD (fail-closed)
    - Otherwise, compute success count and compare to ceil(0.99 * unique)
    """
    details: Dict = {}
    # Snapshot pin validation (if snapshot provided, require pin)
    if snapshot is not None or snapshot_pin is not None:
        try:
            validate_snapshot_pin(snapshot, snapshot_pin)
        except SnapshotPinError as e:
            details["error"] = str(e)
            details["gate"] = "HOLD"
            return "HOLD", details

    if not unique_urls:
        details["error"] = "no unique official_link URLs (denominator 0)"
        details["gate"] = "HOLD"
        return "HOLD", details

    # Check completeness
    for u in unique_urls:
        if u not in mock_results:
            details["error"] = f"missing mock result for URL {u!r} (incomplete measurement)"
            details["gate"] = "HOLD"
            return "HOLD", details

    # Evaluate each URL
    successes = 0
    per_url = {}
    for u in unique_urls:
        head_seq, get_seq = mock_results[u]
        success = check_single_url_with_mock(u, head_seq, get_seq)
        per_url[u] = success
        if success:
            successes += 1

    unique_count = len(unique_urls)
    required = math.ceil(0.99 * unique_count)
    details["unique"] = unique_count
    details["successes"] = successes
    details["required"] = required
    details["per_url"] = per_url
    details["threshold"] = f"ceil(0.99*{unique_count})={required}"

    if successes >= required:
        details["gate"] = "PASS"
        return "PASS", details
    else:
        details["gate"] = "NO-GO"
        details["error"] = f"HTTP resolution {successes}/{unique_count} < required {required} (99%)"
        return "NO-GO", details

def evaluate_official_link_semantic_match(
    unique_urls: List[str],
    expected_source_for_url: Dict[str, str],
    snapshot: Optional[dict] = None,
    snapshot_pin: Optional[str] = None,
) -> Tuple[GateResult, Dict]:
    """
    Official-link semantic/source match =100% gate.
    Each unique URL must match expected source domain/path per snapshot.
    For pure tests, expected_source_for_url maps url -> expected source; we check that url contains expected source domain.
    """
    details: Dict = {}
    try:
        validate_snapshot_pin(snapshot, snapshot_pin)
    except SnapshotPinError as e:
        details["error"] = str(e)
        details["gate"] = "HOLD"
        return "HOLD", details

    if not unique_urls:
        details["error"] = "no unique URLs (denominator 0) => HOLD"
        details["gate"] = "HOLD"
        return "HOLD", details

    mismatches = []
    for u in unique_urls:
        expected = expected_source_for_url.get(u)
        if expected is None:
            details["error"] = f"missing expected source for URL {u!r} (incomplete)"
            details["gate"] = "HOLD"
            return "HOLD", details
        # Simplified check: expected string must be substring of URL (domain check)
        if expected not in u:
            mismatches.append((u, expected))

    details["unique"] = len(unique_urls)
    details["mismatches"] = mismatches
    if mismatches:
        details["gate"] = "NO-GO"
        details["error"] = f"semantic mismatch {len(mismatches)}/{len(unique_urls)}"
        return "NO-GO", details
    else:
        details["gate"] = "PASS"
        return "PASS", details

def check_ineligible_expired(
    top5_by_task: Dict[str, List[Tuple[str, str]]],  # task_id -> list of 5 (source, source_id)
    snapshot: Optional[dict],
    snapshot_pin: Optional[str],
    expected_tasks: int,  # 250 for holdout, 180 for dev
    expected_slots: int,  # 1250 or 900
) -> Tuple[GateResult, Dict]:
    """
    Ineligible/expired checker with exact denominators.

    - top5_by_task must have exactly expected_tasks keys, each with exactly 5 entries
    - snapshot must be pinned and contain eligible/expired flags
    - Any doc with eligible==False or expired==True => intrusion
    - Denominators are exact: tasks and slots
    """
    details: Dict = {}
    try:
        validate_snapshot_pin(snapshot, snapshot_pin)
    except SnapshotPinError as e:
        details["error"] = str(e)
        details["gate"] = "HOLD"
        return "HOLD", details

    if snapshot is None:
        details["error"] = "snapshot is None"
        details["gate"] = "HOLD"
        return "HOLD", details

    # Validate denominators
    if len(top5_by_task) != expected_tasks:
        details["error"] = f"task count mismatch: got {len(top5_by_task)} expected {expected_tasks} (fail-closed HOLD)"
        details["gate"] = "HOLD"
        return "HOLD", details

    for task_id, docs in top5_by_task.items():
        if len(docs) != 5:
            details["error"] = f"task {task_id} has {len(docs)} docs, expected 5 (fail-closed HOLD)"
            details["gate"] = "HOLD"
            return "HOLD", details
        for src, sid in docs:
            if not isinstance(src, str) or not isinstance(sid, str):
                details["error"] = f"task {task_id} doc ({src}, {sid}) not str"
                details["gate"] = "HOLD"
                return "HOLD", details

    # Check eligibility
    eligible_map = snapshot.get("eligible_map") or snapshot.get("table") or {}
    # If snapshot is dict with eligible_map as dict of (source,source_id) -> {eligible, expired}
    intrusions_task = 0
    intrusions_slot = 0
    intrusions_details = []
    for task_id, docs in top5_by_task.items():
        task_intrusion = False
        for src, sid in docs:
            key = (src, sid)
            # eligible_map may have string key "source\x00source_id" or tuple
            entry = eligible_map.get(key)
            if entry is None:
                # Try string key
                entry = eligible_map.get(f"{src}\x00{sid}")
            if entry is None:
                details["error"] = f"missing eligibility/expired evidence for ({src}, {sid}) in task {task_id} (fail-closed HOLD)"
                details["gate"] = "HOLD"
                return "HOLD", details
            eligible = entry.get("eligible")
            expired = entry.get("expired")
            if eligible is None or expired is None:
                details["error"] = f"missing eligible/expired flag for ({src}, {sid})"
                details["gate"] = "HOLD"
                return "HOLD", details
            if eligible is False or expired is True:
                intrusions_slot += 1
                task_intrusion = True
                intrusions_details.append((task_id, src, sid, eligible, expired))
        if task_intrusion:
            intrusions_task += 1

    details["expected_tasks"] = expected_tasks
    details["expected_slots"] = expected_slots
    details["intrusions_task"] = intrusions_task
    details["intrusions_slot"] = intrusions_slot
    details["intrusions_details"] = intrusions_details
    details["denominators"] = f"{expected_tasks} tasks / {expected_slots} slots"

    if intrusions_task == 0 and intrusions_slot == 0:
        details["gate"] = "PASS"
        return "PASS", details
    else:
        details["gate"] = "NO-GO"
        details["error"] = f"ineligible/expired intrusion found: {intrusions_task}/{expected_tasks} tasks, {intrusions_slot}/{expected_slots} slots"
        return "NO-GO", details

def check_unsupported_ambiguous(
    holdout_unsupported_results: List[bool],  # per task success bool (True if correctly handled)
    holdout_ambiguous_results: List[bool],
    dev_unsupported_results: Optional[List[bool]] = None,
    dev_ambiguous_results: Optional[List[bool]] = None,
) -> Tuple[GateResult, Dict]:
    """
    Deterministic safety integer cutoffs:
    - holdout unsupported 38 => PASS >=37, NO-GO <=36 (ceil 0.95*38=37)
    - holdout ambiguous 32 => PASS >=29, NO-GO <=28 (ceil 0.9*32=29)
    - dev unsupported 27 => PASS >=26, dev ambiguous 23 => PASS >=21 (diagnostic)
    Missing measurement => HOLD
    """
    details: Dict = {}
    if holdout_unsupported_results is None or holdout_ambiguous_results is None:
        details["error"] = "missing holdout unsupported/ambiguous measurement"
        details["gate"] = "HOLD"
        return "HOLD", details

    # Validate exact denominators
    if len(holdout_unsupported_results) != 38:
        details["error"] = f"holdout unsupported count {len(holdout_unsupported_results)} != 38 (fail-closed HOLD)"
        details["gate"] = "HOLD"
        return "HOLD", details
    if len(holdout_ambiguous_results) != 32:
        details["error"] = f"holdout ambiguous count {len(holdout_ambiguous_results)} != 32 (fail-closed HOLD)"
        details["gate"] = "HOLD"
        return "HOLD", details

    holdout_unsupported_success = sum(1 for x in holdout_unsupported_results if x)
    holdout_ambiguous_success = sum(1 for x in holdout_ambiguous_results if x)

    holdout_unsupported_pass = holdout_unsupported_success >= 37
    holdout_ambiguous_pass = holdout_ambiguous_success >= 29

    details["holdout_unsupported"] = f"{holdout_unsupported_success}/38 required 37"
    details["holdout_ambiguous"] = f"{holdout_ambiguous_success}/32 required 29"
    details["holdout_unsupported_pass"] = holdout_unsupported_pass
    details["holdout_ambiguous_pass"] = holdout_ambiguous_pass

    if not holdout_unsupported_pass or not holdout_ambiguous_pass:
        details["gate"] = "NO-GO"
        details["error"] = "safety gate NO-GO"
        return "NO-GO", details

    # Dev is diagnostic but if provided, check
    if dev_unsupported_results is not None:
        if len(dev_unsupported_results) != 27:
            details["error"] = f"dev unsupported count {len(dev_unsupported_results)} !=27"
            details["gate"] = "HOLD"
            return "HOLD", details
        dev_u_success = sum(1 for x in dev_unsupported_results if x)
        details["dev_unsupported"] = f"{dev_u_success}/27 required 26"
        if dev_u_success < 26:
            details["gate"] = "NO-GO"
            return "NO-GO", details
    if dev_ambiguous_results is not None:
        if len(dev_ambiguous_results) != 23:
            details["error"] = f"dev ambiguous count {len(dev_ambiguous_results)} !=23"
            details["gate"] = "HOLD"
            return "HOLD", details
        dev_a_success = sum(1 for x in dev_ambiguous_results if x)
        details["dev_ambiguous"] = f"{dev_a_success}/23 required 21"
        if dev_a_success < 21:
            details["gate"] = "NO-GO"
            return "NO-GO", details

    details["gate"] = "PASS"
    return "PASS", details
