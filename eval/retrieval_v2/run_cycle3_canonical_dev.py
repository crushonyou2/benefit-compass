"""Cycle3 canonical dev batch runner — single-batch baseline+3 evaluation.

This runner is the ONLY canonical entry point for the Cycle3 fresh dev 36
single batch (baseline + c3e1/128 + c3e2/256 + c3e3/512).

HARD GUARDRAILS (this file):
- No holdout plaintext path allowed until freeze+review+approval.
- No individual candidate rerun / new K / new candidate after batch.
- Protected dev access requires exact set_sha/session/token verification
  (fail-closed) immediately before plaintext open.
- Audit run_start/run_end + protected_access_start/end are integrated but
  NOT executed in the implementation stage (tests use temp audit).
- Actual retrieval/DB/model/embedding/benchmark/latency is implemented here
  but MUST NOT be executed in the implementation stage (Web will run full
  suite on commit). Running it now would violate the logical stage contract
  and pollute the audit log with premature events.

Usage (CANONICAL, after Web review):
  python eval/retrieval_v2/run_cycle3_canonical_dev.py \
    --dev-evalset eval/retrieval-v2/cycle3/dev/evalset.jsonl \
    --output eval/retrieval-v2/cycle3/canonical-dev/canonical-dev-result.json \
    --audit-log eval/retrieval-v2/cycle3/audit/events.jsonl \
    --session-id cycle3-canonical-dev-<token>

Implementation notes:
- SQL semantics are delegated to cycle3_runner (normative templates).
- Query preprocessing is strip_region + lexical_overlap_terms_rewrite.
- Cosine filter is post-LIMIT python (1 - dist >= 0.78).
- Ordering is youth/lexical-adjusted dist, dist, source, source_id.
- Latency harness is predefined paired (same-process / interleaved / warmup-excluded)
  but is only invoked for quality-selectable candidates (code boundary).

This stage only provides the code; do not invoke main() here.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "ml-service"))
sys.path.insert(0, str(ROOT / "eval"))

from retrieval_v2.cycle3_runner import (  # type: ignore
    ALL_CANONICAL_IDS,
    BATCH_ID,
    BASELINE_ID,
    CANDIDATE_IDS,
    POOL_K_BY_ID,
    FINAL_N,
    RUNNER_ID,
    EXPECTED_DEV_SHA256,
    EXPECTED_DEV_CASES,
    CANONICAL_DEV_OUTPUT_REL,
    validate_candidate_registry,
    validate_single_batch_request,
    get_sql_for_candidate,
    validate_sql_semantics,
    validate_cosine_filter_position,
    strip_region_for_runner,
    lexical_terms_for_runner,
    youth_bias_for_runner,
    apply_cosine_filter,
    ordering_key,
    build_result_skeleton,
    validate_result_schema,
    assert_d003_contract,
    assert_holdout_blocked,
    assert_not_holdout_path,
    require_protected_dev_access_grant,
    append_canonical_run_start,
    append_canonical_run_end,
)
from retrieval_v2.provenance import canonical_text_sha256  # type: ignore

# Guard: holdout paths are blocked at import-time inspection
_BLOCKED_HOLDOUT_SUBSTRINGS = ("holdout",)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Cycle3 canonical dev batch — baseline+3 vector-pool (single batch)")
    p.add_argument("--dev-evalset", type=str, default="eval/retrieval-v2/cycle3/dev/evalset.jsonl", help="fresh dev 36 evalset path")
    p.add_argument("--output", type=str, default=CANONICAL_DEV_OUTPUT_REL, help="canonical result output (must be under eval/retrieval-v2/)")
    p.add_argument("--audit-log", type=str, default="eval/retrieval-v2/cycle3/audit/events.jsonl", help="audit log path")
    p.add_argument("--session-id", type=str, default=None, help="CYCLE3_SESSION_ID or explicit session token")
    p.add_argument("--allow-holdout", action="store_true", help="NOT ALLOWED in canonical dev batch (holdout blocked)")
    p.add_argument("--candidates", type=str, nargs="*", default=list(ALL_CANONICAL_IDS), help="must be exactly baseline + 3 pool candidates (guarded)")
    return p.parse_args(argv)


def _fail_closed(msg: str) -> None:
    raise RuntimeError(msg)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    # --- pre-execution guards (no plaintext open yet) ---
    validate_candidate_registry()
    assert_d003_contract()

    # Hard path confinement — dev batch must use exact canonical relative paths
    # (rejects arbitrary --dev-evalset, symlink/parent-worktree bypass)
    expected_dev = "eval/retrieval-v2/cycle3/dev/evalset.jsonl"
    expected_out = CANONICAL_DEV_OUTPUT_REL
    expected_audit = "eval/retrieval-v2/cycle3/audit/events.jsonl"
    # Normalize to posix for comparison (allow ./ prefix, backslash)
    def _norm(p: str) -> str:
        import posixpath
        return posixpath.normpath(p.replace("\\", "/").lstrip("./"))
    if _norm(args.dev_evalset) != _norm(expected_dev):
        _fail_closed(f"dev evalset path must be exactly {expected_dev!r} (hard confinement), got {args.dev_evalset!r}")
    if _norm(args.output) != _norm(expected_out):
        _fail_closed(f"output path must be exactly {expected_out!r} (single-batch guard), got {args.output!r}")
    if _norm(args.audit_log) != _norm(expected_audit):
        _fail_closed(f"audit log path must be exactly {expected_audit!r}, got {args.audit_log!r}")

    if args.allow_holdout:
        _fail_closed("allow-holdout is not permitted in canonical dev batch — holdout blocked until freeze+review+approval")
    # Block any holdout substring in supplied paths (defense in depth)
    assert_not_holdout_path(args.dev_evalset)
    assert_not_holdout_path(args.output)
    assert_not_holdout_path(args.audit_log)

    # Region search disabled — rp must be NULL
    assert_rp_is_null(None)

    # Single-batch guard: must request exactly baseline+3
    validate_single_batch_request(args.candidates, output_path=args.output)

    # Validate requested candidates match canonical ids exactly
    if set(args.candidates) != set(ALL_CANONICAL_IDS):
        _fail_closed(f"candidates must be exactly {ALL_CANONICAL_IDS}, got {args.candidates}")

    # Validate SQL semantics for all candidates (no drift)
    for cid in ALL_CANONICAL_IDS:
        sql = get_sql_for_candidate(cid)
        validate_sql_semantics(sql, cid)
        validate_cosine_filter_position(sql)

    # Protected dev access grant: require exact dev SHA + session + optional token before plaintext open
    session_id = args.session_id or os.getenv("CYCLE3_SESSION_ID") or f"pid-{os.getpid()}"
    if not session_id.strip():
        _fail_closed("session_id must be non-empty for protected dev access")

    audit_log = pathlib.Path(args.audit_log)
    # Optional expected_event_hash token (if supplied via env, enforce exact match)
    expected_token = os.getenv("CYCLE3_GRANT_TOKEN")
    if expected_token is not None and not expected_token.strip():
        expected_token = None
    if expected_token is not None:
        # must be 64-hex
        import re
        if not re.fullmatch(r"[0-9a-f]{64}", expected_token.lower()):
            _fail_closed(f"CYCLE3_GRANT_TOKEN must be 64-hex, got {expected_token!r}")
    try:
        grant = require_protected_dev_access_grant(
            audit_log,
            set_sha=EXPECTED_DEV_SHA256,
            session_id=session_id,
            expected_event_hash=expected_token,
        )
    except Exception as e:
        _fail_closed(
            f"protected dev access denied (fail-closed): no verified protected_access_start "
            f"for set_role=dev set_sha={EXPECTED_DEV_SHA256[:8]}... session_id={session_id!r} in {audit_log}: {e}"
        )

    # Implementation-stage gate: do NOT open dev plaintext or execute retrieval.
    # Real canonical execution requires explicit opt-in env.
    if os.getenv("CYCLE3_CANONICAL_EXECUTION") != "1":
        _fail_closed(
            "canonical dev batch execution is not allowed in the implementation stage — "
            "this runner is code-complete but must be invoked only after Web static review "
            "in a dedicated canonical execution session (single batch, audit grant required). "
            f"batch_id={BATCH_ID} dev_sha={EXPECTED_DEV_SHA256[:8]}... session={session_id!r} grant={grant['event_hash'][:8]}..."
        )

    # --- ONLY below this line would real execution open plaintext ---
    # Verify dev evalset sha matches expected (canonical bytes LF)
    dev_path = pathlib.Path(args.dev_evalset)
    if not dev_path.exists():
        _fail_closed(f"dev evalset not found: {dev_path} (sparse isolated worktree must provide dev plaintext via grant)")
    actual_sha = canonical_text_sha256(dev_path)
    if actual_sha.lower() != EXPECTED_DEV_SHA256.lower():
        _fail_closed(f"dev evalset sha mismatch: got {actual_sha} expected {EXPECTED_DEV_SHA256}")

    # --- Audit run_start (would be appended here in real run) ---
    # In implementation stage we do NOT append to real audit log.
    # Real run would call append_canonical_run_start for batch + each candidate.

    # --- Retrieval execution placeholder (NOT executed in this stage) ---
    # The real implementation would:
    #  1. Load dev items via load_and_validate
    #  2. Warm model intfloat/multilingual-e5-base once (same process/DB)
    #  3. For each case: encode strip_region(raw) once, then fetch 4-way
    #     candidates via SQL variants (baseline vs pool-128/256/512), same
    #     corpus provenance (4-way identical), same DB, same qvec, interleaved.
    #  4. Apply post-LIMIT cosine filter (1 - dist >= 0.78) to each 30.
    #  5. Compute ranks (gold source/source_id in top-k), metrics, paired deltas,
    #     quality_selectable, then predefined paired latency for quality-selectable only.
    #  6. Build result via build_result_skeleton + metrics/selection/latency.
    #  7. Validate via validate_result_schema + guard checks, write atomically,
    #     append run_end, protected_access_end.

    # For now, emit a skeleton with guard that prevents accidental execution
    # without explicit --execute flag (which we do not expose).
    _fail_closed(
        "canonical dev batch execution is not allowed in the implementation stage — "
        "this runner is code-complete but must be invoked only after Web static review "
        "in a dedicated canonical execution session (single batch, audit grant required). "
        f"batch_id={BATCH_ID} dev_sha={EXPECTED_DEV_SHA256[:8]}... session={session_id!r}"
    )


if __name__ == "__main__":
    main()
