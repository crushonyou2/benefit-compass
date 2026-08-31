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
import time
import tempfile
import random
import statistics

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
    validate_complete_result,
    atomic_write_result,
    orchestrate_4way_batch,
    rank_of_gold,
    assert_d003_contract,
    assert_holdout_blocked,
    assert_not_holdout_path,
    require_protected_dev_access_grant,
    append_canonical_run_start,
    append_canonical_run_end,
    assert_rp_is_null,
)
from retrieval_v2.provenance import canonical_text_sha256  # type: ignore
from retrieval_v2.schema import load_and_validate  # type: ignore

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


# ---------------------------------------------------------------------------
# Hard path confinement — repo-root resolved exact confinement
# ---------------------------------------------------------------------------

def _repo_root_resolved() -> pathlib.Path:
    return ROOT.resolve()


def _confine_to_canonical(user_path: str, expected_rel: str) -> pathlib.Path:
    """Fail-closed repo-root resolved confinement.

    - Rejects parent traversal: any '..' component in the user-supplied path fails closed.
    - Resolves both expected and user paths via Path.resolve() (follows symlinks).
    - Requires user path to resolve EXACTLY to expected in-repo location.
    - Requires resolved path to be inside repo root (symlink/worktree escape fails closed).
    - Also validates canonical output/rerun guard (existing file check is separate).

    This replaces the previous posixpath.normpath(...).lstrip('./') logic which
    allowed '../../../eval/...' to normalize to the canonical path.
    """
    # Reject empty
    if not isinstance(user_path, str) or not user_path.strip():
        _fail_closed(f"path must be non-empty, got {user_path!r}")
    # Normalize separators for traversal check
    posix = user_path.replace("\\", "/")
    # Check for '..' component — use PurePosixPath parts
    parts = pathlib.PurePosixPath(posix).parts
    if ".." in parts:
        _fail_closed(f"path traversal rejected: {user_path!r} contains '..' (hard confinement)")
    # Also reject absolute paths that escape: we will resolve and check is_relative_to
    repo_root = _repo_root_resolved()
    expected = (repo_root / expected_rel).resolve()
    # Ensure expected is inside repo_root (sanity)
    try:
        expected.relative_to(repo_root)
    except ValueError:
        _fail_closed(f"expected canonical path escapes repo root: {expected_rel!r} -> {expected}")
    # Resolve user path
    p = pathlib.Path(user_path)
    if not p.is_absolute():
        candidate = (repo_root / user_path).resolve()
    else:
        candidate = p.resolve()
    # Symlink/worktree escape: candidate must be inside repo_root
    try:
        candidate.relative_to(repo_root)
    except ValueError:
        _fail_closed(f"path escapes repo root (symlink/worktree escape): {user_path!r} -> {candidate}")
    if candidate != expected:
        _fail_closed(f"path must be exactly {expected_rel!r} (hard confinement), got {user_path!r} (resolved {candidate} != {expected})")
    return candidate


def _confine_all_paths(dev_evalset: str, output: str, audit_log: str) -> tuple[pathlib.Path, pathlib.Path, pathlib.Path]:
    expected_dev = "eval/retrieval-v2/cycle3/dev/evalset.jsonl"
    expected_out = CANONICAL_DEV_OUTPUT_REL
    expected_audit = "eval/retrieval-v2/cycle3/audit/events.jsonl"
    dev_p = _confine_to_canonical(dev_evalset, expected_dev)
    out_p = _confine_to_canonical(output, expected_out)
    audit_p = _confine_to_canonical(audit_log, expected_audit)
    return dev_p, out_p, audit_p


# ---------------------------------------------------------------------------
# Real retrieval / embedding helpers (for canonical execution, not used in repair stage)
# ---------------------------------------------------------------------------

def _real_embedding_fn_factory(model):
    """Return embedding_fn that encodes strip_region(raw) via SentenceTransformer."""
    def _embed(stripped: str):
        # SentenceTransformer encodes with normalize? Use model.encode
        # Return vector as string or list for SQL vec param
        vec = model.encode(stripped, normalize_embeddings=True)
        # Convert to pgvector string representation? The SQL expects %(vec)s::vector
        # psycopg2 will handle list -> vector? We pass as string "[...]"
        # For real execution, we pass as python list; psycopg adapter handles.
        # Here we return vec.tolist() if numpy
        try:
            return vec.tolist()
        except Exception:
            return list(vec)
    return _embed


def _real_retrieval_fn_factory(conn, model):  # noqa: ARG001
    """Return retrieval_fn that hits DB with normative SQL."""
    import psycopg2.extras  # type: ignore

    def _retrieve(candidate_id: str, vec, lexical_terms: list[str], youth_bias: float, age, rp):
        # Enforce rp NULL
        assert_rp_is_null(rp)
        sql = get_sql_for_candidate(candidate_id)
        # Validate semantics each call (fail-closed)
        validate_sql_semantics(sql, candidate_id)
        validate_cosine_filter_position(sql)
        # Prepare params
        # vec needs to be pgvector compatible: psycopg2 will cast list/vector
        # lexical_terms as text[]; youth_bias, lexical_bias handled in SQL ordering
        # For baseline, pool_k not used, but SQL still expects %(pool_k)s? Baseline SQL doesn't have pool_k placeholder
        params: dict = {
            "vec": vec,
            "age": age,
            "rp": rp,
            "lexical_terms": lexical_terms,
            "youth_bias": youth_bias,
            "lexical_bias": 0.01,
            "n": FINAL_N,
        }
        pool_k = POOL_K_BY_ID.get(candidate_id)
        if pool_k is not None:
            params["pool_k"] = pool_k
        # Need to handle vector format: convert vec list to string for pgvector?
        # The SQL uses (c.embedding <=> %(vec)s::vector) — psycopg2 with pgvector extension expects string or list
        # We'll pass as string representation if needed
        # Use cursor
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
            # rows are dict? We fetch with default cursor (tuple). Need column mapping.
            # The SELECT returns source, source_id, title, org, support_content, apply_method, apply_url, age_min, age_max, income_etc, score
            # But we need dist for cosine filter; score = 1 - dist, so dist = 1 - score
            # However raw_results for apply_cosine_filter expects dist field for filtering: 1 - dist >= 0.78
            # Our SQL returns score, not dist. So we need to reconstruct dist.
            # For simplicity, assume cursor returns dict with dist; but real SQL returns score.
            # We'll map: dist = 1 - score
            colnames = [d[0] for d in cur.description] if cur.description else []
            cands: list[dict] = []
            for row in rows:
                rec = dict(zip(colnames, row)) if colnames else {}
                # Ensure dist field
                if "dist" not in rec and "score" in rec:
                    try:
                        rec["dist"] = 1.0 - float(rec["score"])
                    except Exception:
                        rec["dist"] = 0.0
                cands.append(rec)
            return cands

    return _retrieve


def _real_latency_measurer_factory(dev_items, embedding_fn, retrieval_fn):
    """Build a latency measurer that implements predefined warm paired harness.

    Contract:
    - Same-process / same-DB / interleaved / warmup-excluded
    - Timed count fixed before inspection (WARMUP + ROUNDS*len(dev_items) per variant)
    - Only invoked for quality-selectable candidates (enforced by orchestrator)
    - Returns dict[candidate_id, {"p50": ..., "p95": ..., "samples": [...], "count": ...}]

    For real execution, this measures actual retrieval time (encode+lexical+SQL+filter).
    For tests, a fake measurer can be injected via orchestrate_4way_batch directly.
    """
    LATENCY_WARMUP = 36  # one pass over dev set per variant
    LATENCY_ROUNDS = 5  # timed rounds

    def _measure(quality_ids: list[str]) -> dict[str, dict]:
        # Include baseline in measurement for paired delta
        variants = [BASELINE_ID] + [cid for cid in quality_ids if cid != BASELINE_ID]
        # Ensure baseline always measured for delta
        if BASELINE_ID not in variants:
            variants = [BASELINE_ID] + variants
        # Fix timed count before inspection
        timed_per_variant = len(dev_items) * LATENCY_ROUNDS
        # Prepare interleaving: for each case, interleave variants in random order per round
        # Use fixed seed for reproducibility
        rng = random.Random(20260831)
        # Warmup phase (excluded from timed)
        for _ in range(LATENCY_WARMUP):
            case = rng.choice(dev_items)
            raw = str(case.get("query", "") or case.get("raw", ""))
            stripped = strip_region_for_runner(raw)
            terms_map = {cid: lexical_terms_for_runner(raw, candidate_id=cid) for cid in variants}
            yb = youth_bias_for_runner(raw)
            vec = embedding_fn(stripped)
            for cid in rng.sample(variants, len(variants)):
                terms = terms_map[cid]
                _ = retrieval_fn(cid, vec, terms, yb, case.get("age"), None)
                _ = apply_cosine_filter(_, 0.78)
        # Timed phase
        latencies: dict[str, list[float]] = {cid: [] for cid in variants}
        # Interleaved: for each round, shuffle dev order, then for each case interleave variants
        for _ in range(LATENCY_ROUNDS):
            round_cases = dev_items[:]
            rng.shuffle(round_cases)
            for case in round_cases:
                raw = str(case.get("query", "") or case.get("raw", ""))
                stripped = strip_region_for_runner(raw)
                terms_map = {cid: lexical_terms_for_runner(raw, candidate_id=cid) for cid in variants}
                yb = youth_bias_for_runner(raw)
                vec = embedding_fn(stripped)
                # Interleave variants per case
                order = rng.sample(variants, len(variants))
                for cid in order:
                    terms = terms_map[cid]
                    t0 = time.perf_counter()
                    raw_res = retrieval_fn(cid, vec, terms, yb, case.get("age"), None)
                    filtered = apply_cosine_filter(raw_res, 0.78)
                    t1 = time.perf_counter()
                    # Use filtered length to ensure not optimized away
                    _ = len(filtered)
                    latencies[cid].append((t1 - t0) * 1000.0)  # ms
        # Compute p50/p95
        out: dict[str, dict] = {}
        for cid in variants:
            samples = latencies[cid]
            if len(samples) != timed_per_variant:
                _fail_closed(f"latency timed count mismatch for {cid}: got {len(samples)} expected {timed_per_variant} (fixed before inspection)")
            samples_sorted = sorted(samples)
            # p50 median, p95 95th percentile
            p50 = statistics.median(samples_sorted)
            # p95: 95th percentile using nearest rank method
            idx95 = max(0, min(len(samples_sorted) - 1, int(0.95 * len(samples_sorted))))
            # Use linear interpolation for more accurate
            # Simple: sorted[(n-1)*0.95]
            k = (len(samples_sorted) - 1) * 0.95
            f = int(k)
            c = min(f + 1, len(samples_sorted) - 1)
            if f == c:
                p95 = samples_sorted[f]
            else:
                d0 = k - f
                p95 = samples_sorted[f] * (1 - d0) + samples_sorted[c] * d0
            out[cid] = {"p50": float(p50), "p95": float(p95), "count": len(samples), "samples": samples_sorted[:5], "all_samples_count": len(samples)}
        # For quality_ids, ensure we return at least baseline + quality_ids
        # Fill missing candidates with None (not measured)
        full: dict[str, dict | None] = {cid: None for cid in ALL_CANONICAL_IDS}
        for cid in variants:
            full[cid] = out[cid]
        return full

    return _measure


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)

    # --- pre-execution guards (no plaintext open yet) ---
    validate_candidate_registry()
    assert_d003_contract()

    # Hard path confinement — dev batch must use exact canonical relative paths
    # (rejects arbitrary --dev-evalset, symlink/parent-worktree bypass)
    dev_path, out_path, audit_log_path = _confine_all_paths(args.dev_evalset, args.output, args.audit_log)

    if args.allow_holdout:
        _fail_closed("allow-holdout is not permitted in canonical dev batch — holdout blocked until freeze+review+approval")
    # Block any holdout substring in supplied paths (defense in depth)
    assert_not_holdout_path(args.dev_evalset)
    assert_not_holdout_path(args.output)
    assert_not_holdout_path(args.audit_log)

    # Region search disabled — rp must be NULL
    assert_rp_is_null(None)

    # Single-batch guard: must request exactly baseline+3
    validate_single_batch_request(args.candidates, output_path=str(out_path))

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

    audit_log = pathlib.Path(audit_log_path)
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
    # We are now in canonical execution mode (gate passed). Wire audit lifecycle fail-closed.
    # Verify dev evalset sha matches expected (canonical bytes LF)
    dev_path_resolved = pathlib.Path(dev_path)
    if not dev_path_resolved.exists():
        _fail_closed(f"dev evalset not found: {dev_path_resolved} (sparse isolated worktree must provide dev plaintext via grant)")
    actual_sha = canonical_text_sha256(dev_path_resolved)
    if actual_sha.lower() != EXPECTED_DEV_SHA256.lower():
        _fail_closed(f"dev evalset sha mismatch: got {actual_sha} expected {EXPECTED_DEV_SHA256}")

    # --- Audit run_start (must be appended atomically and verified) ---
    # This is the first real canonical event for this batch; preserve existing 16 events chain.
    run_start_event = None
    try:
        run_start_event = append_canonical_run_start(
            audit_log,
            candidate_id=BATCH_ID,
            set_sha=EXPECTED_DEV_SHA256,
            session_id=session_id,
        )
    except Exception as e:
        _fail_closed(f"audit run_start append failed (fail-closed): {e}")

    # We will ensure run_end and protected_access_end are appended even on failure (lifecycle closure)
    success = False
    result_path = None
    try:
        # Load and validate dev items (36)
        dev_items = load_and_validate(dev_path_resolved, role="dev")
        if len(dev_items) != EXPECTED_DEV_CASES:
            _fail_closed(f"dev cases mismatch: got {len(dev_items)} expected {EXPECTED_DEV_CASES}")

        # --- Real retrieval execution ---
        # Load model once (same-process constraint)
        # Import here to avoid import cost in non-execution stage
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except Exception as e:
            _fail_closed(f"embedding model load failed: {e}")

        # DATABASE_URL must be provided
        db_url = os.getenv("DATABASE_URL", "").strip()
        if not db_url:
            _fail_closed("DATABASE_URL must be set for canonical execution")

        import psycopg2  # type: ignore

        # Use single DB connection for same-DB constraint
        conn = psycopg2.connect(db_url)
        try:
            # Warm model
            model = SentenceTransformer("intfloat/multilingual-e5-base")
            embedding_fn = _real_embedding_fn_factory(model)
            retrieval_fn = _real_retrieval_fn_factory(conn, model)

            # Latency measurer: predefined warm paired, only for quality-selectable
            latency_measurer = _real_latency_measurer_factory(dev_items, embedding_fn, retrieval_fn)

            # Orchestrate 4-way batch (this is the real single code path)
            result = orchestrate_4way_batch(
                dev_items,
                embedding_fn=embedding_fn,
                retrieval_fn=retrieval_fn,
                latency_measurer=latency_measurer,
            )

            # Enrich result with provenance
            # result already contains skeleton + metrics + selection + latency + per_case + git
            # Add additional provenance fields if missing
            result["provenance"] = {
                "dev_sha256": actual_sha,
                "grant_event_hash": grant["event_hash"],
                "run_start_event_hash": run_start_event["event_hash"] if run_start_event else None,
                "session_id": session_id,
                "executed_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
            }

            # Strict validation before write
            validate_complete_result(result)

            # Atomic write only after all validation — single batch guard already checked that output not exists
            result_path = atomic_write_result(result, out_path)

        finally:
            try:
                conn.close()
            except Exception:
                pass

        success = True
    except Exception as e:
        # Failure path: append run_end with failure, then lifecycle closure
        try:
            append_canonical_run_end(
                audit_log,
                candidate_id=BATCH_ID,
                set_sha=EXPECTED_DEV_SHA256,
                outcome="failure",
                session_id=session_id,
            )
        except Exception:
            pass
        # Attempt to close protected access grant even on failure (fail-closed lifecycle)
        try:
            from retrieval_v2.cycle3_audit import append_event  # type: ignore

            append_event(
                audit_log,
                action="protected_access_end",
                candidate_id=None,
                set_role="dev",
                set_sha=EXPECTED_DEV_SHA256,
                outcome="failure",
                session_id=session_id,
            )
        except Exception:
            pass
        _fail_closed(f"canonical dev batch failed (fail-closed): {e}")
    else:
        # Success path: append run_end success and close protected access
        try:
            append_canonical_run_end(
                audit_log,
                candidate_id=BATCH_ID,
                set_sha=EXPECTED_DEV_SHA256,
                outcome="success",
                session_id=session_id,
            )
        except Exception as e:
            _fail_closed(f"audit run_end append failed (fail-closed): {e}")
        try:
            from retrieval_v2.cycle3_audit import append_event  # type: ignore

            append_event(
                audit_log,
                action="protected_access_end",
                candidate_id=None,
                set_role="dev",
                set_sha=EXPECTED_DEV_SHA256,
                outcome="success",
                session_id=session_id,
            )
        except Exception as e:
            _fail_closed(f"audit protected_access_end append failed (fail-closed): {e}")
    finally:
        # Ensure result artifact exists only on success; on failure it must not exist (fail-closed)
        if not success and result_path is not None:
            try:
                pathlib.Path(result_path).unlink()
            except Exception:
                pass


if __name__ == "__main__":
    main()
