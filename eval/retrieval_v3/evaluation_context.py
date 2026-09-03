"""Evaluation-context capture — pinned date/timezone mechanics (D-053/D-054).

Frozen contract: eval/retrieval-v3/candidate-plan/production-exclusion-policy-v2.json
§evaluation_as_of_date / §db_session_timezone.

At each protected evaluation session, BEFORE protected plaintext access and
BEFORE run_start, on the exact DB connection context governing the pinned
evaluation corpus and the paired D-003 baseline/candidate, execute exactly once
for capture: SHOW TimeZone and SELECT CURRENT_DATE. No SET TIME ZONE or session
override for capture. Pin returned values as db_session_timezone (as returned)
and evaluation_as_of_date (SELECT CURRENT_DATE, canonical ISO YYYY-MM-DD) in
corpus/evaluation provenance and audit. Immutable for the entire run, shared by
Candidate A and the paired D-003 baseline. Missing/malformed/error => HOLD;
never fall back to OS/user/local/UTC date.

This stage performs no real DB connection (tests inject a synthetic capture
adapter). Pure except for the injected executor call. No clock reads, no
datetime/time imports: the pinned date is the ONLY evaluation date.
"""

from __future__ import annotations

from typing import Callable

CAPTURE_STATEMENTS = ("SHOW TimeZone", "SELECT CURRENT_DATE")

POLICY_ID = "retrieval-v3-production-exclusion-policy-v2"
POLICY_SHA256 = "6fee9ec22d5d3ac153ff19a6b1b5d27ab6a6a43bda11e35821d689f938968fe5"

_DATE_RE = None


def _iso_date_pattern():
    global _DATE_RE
    if _DATE_RE is None:
        import re

        _DATE_RE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")
    return _DATE_RE


def is_valid_iso_date(value: object) -> bool:
    """Strict canonical ISO YYYY-MM-DD calendar-date check (no clock, no IO)."""
    if not isinstance(value, str):
        return False
    m = _iso_date_pattern().match(value)
    if not m:
        return False
    year, month, day = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if not 1 <= month <= 12:
        return False
    leap = (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)
    month_days = (31, 29 if leap else 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
    return 1 <= day <= month_days[month - 1]


def capture_pinned_context(db_exec_fn: Callable[[str], object]) -> dict:
    """Execute the exact two-statement capture inventory once via db_exec_fn.

    Calls db_exec_fn("SHOW TimeZone") then db_exec_fn("SELECT CURRENT_DATE")
    and nothing else. Returns {"db_session_timezone", "evaluation_as_of_date"}.
    Any missing/malformed/error raises (caller fails closed to HOLD); no
    fallback date is ever synthesized.
    """
    if not callable(db_exec_fn):
        raise ValueError("db_exec_fn must be callable (fail-closed)")
    try:
        timezone_value = db_exec_fn(CAPTURE_STATEMENTS[0])
    except Exception as e:
        raise RuntimeError(f"evaluation-context capture failed on SHOW TimeZone (fail-closed): {e}") from e
    try:
        current_date_value = db_exec_fn(CAPTURE_STATEMENTS[1])
    except Exception as e:
        raise RuntimeError(f"evaluation-context capture failed on SELECT CURRENT_DATE (fail-closed): {e}") from e
    if not isinstance(timezone_value, str) or not timezone_value.strip():
        raise ValueError("db_session_timezone missing/malformed (fail-closed, no fallback)")
    if not is_valid_iso_date(current_date_value):
        raise ValueError(f"evaluation_as_of_date missing/malformed {current_date_value!r} (fail-closed, no fallback)")
    return {
        "db_session_timezone": timezone_value,
        "evaluation_as_of_date": current_date_value,
    }


def validate_pinned_context(ctx: object) -> dict:
    """Strict validation of a pinned context dict. Fail-closed on drift."""
    if not isinstance(ctx, dict):
        raise ValueError(f"evaluation context must be dict, got {type(ctx).__name__}")
    tz = ctx.get("db_session_timezone")
    as_of = ctx.get("evaluation_as_of_date")
    if not isinstance(tz, str) or not tz.strip():
        raise ValueError("db_session_timezone must be nonempty str (fail-closed)")
    if not is_valid_iso_date(as_of):
        raise ValueError(f"evaluation_as_of_date must be ISO YYYY-MM-DD, got {as_of!r} (fail-closed)")
    return {"db_session_timezone": tz, "evaluation_as_of_date": as_of}
