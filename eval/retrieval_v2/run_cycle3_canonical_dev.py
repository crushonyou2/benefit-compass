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
    lexical_terms_for_stripped,
    youth_bias_for_runner,
    youth_bias_for_stripped,
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
    assert_no_prior_canonical_attempt,
    format_pgvector,
    get_corpus_provenance,
    validate_corpus_provenance,
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
    p.add_argument("--grant-token", type=str, default=None, help="CYCLE3_GRANT_TOKEN — optional but if supplied must be 64-hex and pinned to latest protected_access_start event_hash (fail-closed)")
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
    """Return embedding_fn that encodes strip_region(raw) via SentenceTransformer.

    Production parity: must exactly match production/eval contract
    model.encode([f"query: {q}"], normalize_embeddings=True)[0]
    and use same production-compatible pgvector string formatting "[x.xxxxxx,...]" (6-decimal).
    """
    def _embed(stripped: str):
        # Production contract: prefix "query: " + stripped, list form, normalize True
        qvec = model.encode([f"query: {stripped}"], normalize_embeddings=True)[0]
        # Production pgvector string formatting: "[" + ",".join(f"{x:.6f}" for x in qvec) + "]"
        return format_pgvector(qvec)
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

    Contract (repaired to D-007 frozen methodology per prereg §7):
    - Same-process / same-DB / interleaved / warmup-excluded
    - Timed count fixed before inspection (ROUNDS*len(dev_items) per variant = 5*36=180)
    - Only invoked for quality-selectable candidates (enforced by orchestrator)
    - Precompute stripped query/qvec outside timed section (embedding + strip excluded from timed)
    - Warm all 36 dev queries exactly once per measured variant, excluded from timed
    - Timed 5 rounds x 36 per measured variant, interleaved/paired, with t0 before
      lexical_terms + youth_source_bias and including SQL/fetch + post-LIMIT cosine filter
    - Timed sample uses stripped helpers (lexical_terms_for_stripped / youth_bias_for_stripped)
      so strip_region cost is NOT inside timed — matches D-007 q=strip_region(raw) precomputed
    - Uses time.perf_counter_ns + canonical nearest-rank p50/p95 (latency.py) to match D-007
    - Do not include model load / cold samples; same process/DB/corpus/query set
    - Returns dict[candidate_id, {"p50": ..., "p95": ..., "samples": [...], "count": ...}]

    For real execution, this measures retrieval time including lexical/youth+SQL+filter
    (qvec precomputed). For tests, a fake measurer can be injected via orchestrate directly.
    """
    LATENCY_ROUNDS = 5  # timed rounds -> 5*36=180 per variant
    SHUFFLE_SEED = 20260831

    def _measure(quality_ids: list[str]) -> dict[str, dict]:
        # Include baseline in measurement for paired delta
        variants = [BASELINE_ID] + [cid for cid in quality_ids if cid != BASELINE_ID]
        # Ensure baseline always measured for delta
        if BASELINE_ID not in variants:
            variants = [BASELINE_ID] + variants
        # Fix timed count before inspection (same as D-007: 5*36)
        timed_per_variant = len(dev_items) * LATENCY_ROUNDS
        # Precompute stripped query and qvec outside warmup/timed (embedding + strip excluded)
        # This mirrors D-007: q=strip_region(raw), vec_by_case precomputed before warmup (qvec before warmup/timing)
        # Each dev query's qvec is computed exactly once here, then reused for warmup and every timed sample
        # Do NOT recompute strip/embedding inside warmup or timed loops (would drift p95 gate)
        precomputed: list[tuple[dict, str, str, str]] = []
        for case in dev_items:
            raw = str(case.get("query", "") or case.get("raw", ""))
            stripped = strip_region_for_runner(raw)
            vec = embedding_fn(stripped)
            precomputed.append((case, raw, stripped, vec))
        # Warmup phase (excluded from timed): each of 36 queries exactly once per variant, not random-with-replacement
        # D-007 warms every benchmark query once per variant (36/variant), excluded, baseline then candidate per case.
        # Interleaved per case: for each case, execute all variants consecutively (paired) in fixed order.
        for (case, raw, stripped, vec) in precomputed:
            for cid in variants:
                terms = lexical_terms_for_stripped(stripped, candidate_id=cid)
                yb = youth_bias_for_stripped(stripped)
                age = case.get("age")
                rp = None
                raw_res = retrieval_fn(cid, vec, terms, yb, age, rp)
                _ = apply_cosine_filter(raw_res, 0.78)
        # Timed phase: 5 rounds x 36 per variant, interleaved/paired
        latencies: dict[str, list[float]] = {cid: [] for cid in variants}
        for rnd in range(LATENCY_ROUNDS):
            # Deterministic shuffle per round (same methodology as D-007: seed + rnd)
            # Preserve same-process / same-DB / same corpus / same query set, just shuffled order per round
            shuffled = precomputed[:]
            rnd_rng = random.Random(SHUFFLE_SEED + rnd)
            rnd_rng.shuffle(shuffled)
            for q_idx, (case, raw, stripped, vec) in enumerate(shuffled):
                # Interleaved per case: for 2 variants, use D-007 alternating (round+q_idx)%2 to exactly match harness
                # For >2 variants, use random permutation per case (still paired consecutive per case)
                if len(variants) == 2:
                    baseline_first = ((rnd + q_idx) % 2 == 0)
                    other = variants[1]
                    order = [BASELINE_ID, other] if baseline_first else [other, BASELINE_ID]
                else:
                    order = rnd_rng.sample(variants, len(variants))
                for cid in order:
                    t0 = time.perf_counter_ns()
                    # --- timed section start: lexical term generation + youth bias + SQL/fetch + postfilter inside ---
                    # Use stripped helpers so strip_region is NOT recomputed inside timed (precomputed q)
                    terms = lexical_terms_for_stripped(stripped, candidate_id=cid)
                    yb = youth_bias_for_stripped(stripped)
                    age = case.get("age")
                    rp = None
                    raw_res = retrieval_fn(cid, vec, terms, yb, age, rp)
                    filtered = apply_cosine_filter(raw_res, 0.78)
                    _ = len(filtered)
                    t1 = time.perf_counter_ns()
                    latencies[cid].append((t1 - t0) / 1_000_000.0)  # ms
        # Compute p50/p95 via canonical nearest-rank (latency.py) to match D-007 gate
        import math
        out: dict[str, dict] = {}
        for cid in variants:
            samples = latencies[cid]
            if len(samples) != timed_per_variant:
                _fail_closed(f"latency timed count mismatch for {cid}: got {len(samples)} expected {timed_per_variant} (fixed before inspection)")
            samples_sorted = sorted(samples)
            n = len(samples_sorted)
            # p50 = s[ceil(0.5*n)-1], p95 = s[ceil(0.95*n)-1]  (latency.py)
            idx_p50 = math.ceil(0.5 * n) - 1
            idx_p95 = math.ceil(0.95 * n) - 1
            p50 = float(samples_sorted[max(0, min(idx_p50, n - 1))])
            p95 = float(samples_sorted[max(0, min(idx_p95, n - 1))])
            # Round to 2 decimals as D-007 summarize does before gate (candidate p95 <= baseline p95)
            out[cid] = {"p50": round(p50, 2), "p95": round(p95, 2), "count": len(samples), "samples": samples_sorted[:5], "all_samples_count": len(samples)}
        # For quality_ids, ensure we return at least baseline + quality_ids
        # Fill missing candidates with None (not measured)
        full: dict[str, dict | None] = {cid: None for cid in ALL_CANONICAL_IDS}
        for cid in variants:
            full[cid] = out[cid]
        return full

    return _measure


def main(
    argv: list[str] | None = None,
    *,
    _embedding_fn_factory=None,
    _retrieval_fn_factory=None,
    _latency_measurer_factory=None,
    _corpus_provenance_fn=None,
    _load_and_validate_fn=None,
    _canonical_sha_fn=None,
) -> None:
    """Canonical entry point — accepts optional injected factories for E2E fake tests (no DB/model/plaintext).

    Production call: main(argv) with no injection — uses real DB/model/corpus.
    Test call: main(argv, _embedding_fn_factory=fake_factory, ...) — bypasses DB/model with injected fakes.
    This keeps the actual CLI/main path exercised (parse_args, guards, audit lifecycle, validation, atomic write)
    while avoiding protected plaintext/DB/model via dependency injection.
    """
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

    # Single-batch guard: must request exactly baseline+3 (file existence check)
    validate_single_batch_request(args.candidates, output_path=str(out_path))

    # Validate requested candidates match canonical ids exactly
    if set(args.candidates) != set(ALL_CANONICAL_IDS):
        _fail_closed(f"candidates must be exactly {ALL_CANONICAL_IDS}, got {args.candidates}")

    # Validate SQL semantics for all candidates (no drift)
    for cid in ALL_CANONICAL_IDS:
        sql = get_sql_for_candidate(cid)
        validate_sql_semantics(sql, cid)
        validate_cosine_filter_position(sql)

    # Durable one-shot: reject if prior canonical attempt already exists in audit (even if prior failed before output)
    audit_log = pathlib.Path(audit_log_path)
    try:
        assert_no_prior_canonical_attempt(audit_log)
    except Exception as e:
        # FileNotFoundError means no log yet — not a prior attempt, proceed
        if isinstance(e, FileNotFoundError):
            pass
        else:
            # Re-raise one-shot violation as fail-closed (contains batch_id)
            _fail_closed(str(e))

    # Protected dev access grant: require exact dev SHA + session + explicit token pinning (fail-closed) before plaintext open
    session_id = args.session_id or os.getenv("CYCLE3_SESSION_ID") or f"pid-{os.getpid()}"
    if not session_id.strip():
        _fail_closed("session_id must be non-empty for protected dev access")

    # Grant token pinning: explicit, fail-closed — from CLI --grant-token > env CYCLE3_GRANT_TOKEN
    # If supplied, must be 64-hex and pinned to latest protected_access_start event_hash
    # Code/docs/tests consistent: optional but if present, strictly enforced; logs show token source
    expected_token = args.grant_token
    token_source = "cli --grant-token"
    if expected_token is None:
        expected_token = os.getenv("CYCLE3_GRANT_TOKEN")
        token_source = "env CYCLE3_GRANT_TOKEN"
    if expected_token is not None and not str(expected_token).strip():
        expected_token = None
    if expected_token is not None:
        import re

        if not re.fullmatch(r"[0-9a-f]{64}", str(expected_token).strip().lower()):
            _fail_closed(f"CYCLE3_GRANT_TOKEN ({token_source}) must be 64-hex, got {expected_token!r}")
        expected_token = str(expected_token).strip().lower()
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
            f"for set_role=dev set_sha={EXPECTED_DEV_SHA256[:8]}... session_id={session_id!r} token_source={token_source} token={expected_token[:8] + '...' if expected_token else 'None'} in {audit_log}: {e}"
        )

    # Implementation-stage gate: do NOT open dev plaintext or execute retrieval.
    # Real canonical execution requires explicit opt-in env.
    if os.getenv("CYCLE3_CANONICAL_EXECUTION") != "1":
        _fail_closed(
            "canonical dev batch execution is not allowed in the implementation stage — "
            "this runner is code-complete but must be invoked only after Web static review "
            "in a dedicated canonical execution session (single batch, audit grant required). "
            f"batch_id={BATCH_ID} dev_sha={EXPECTED_DEV_SHA256[:8]}... session={session_id!r} grant={grant['event_hash'][:8]}... token_source={token_source}"
        )

    # --- ONLY below this line would real execution open plaintext ---
    # We are now in canonical execution mode (gate passed). Wire audit lifecycle fail-closed.
    # Verify dev evalset sha matches expected (canonical bytes LF)
    dev_path_resolved = pathlib.Path(dev_path)
    if not dev_path_resolved.exists():
        _fail_closed(f"dev evalset not found: {dev_path_resolved} (sparse isolated worktree must provide dev plaintext via grant)")
    _sha_fn = _canonical_sha_fn or canonical_text_sha256
    actual_sha = _sha_fn(dev_path_resolved)
    if actual_sha.lower() != EXPECTED_DEV_SHA256.lower():
        _fail_closed(f"dev evalset sha mismatch: got {actual_sha} expected {EXPECTED_DEV_SHA256}")

    # Durable one-shot re-check immediately before run_start (detect concurrent race after grant)
    try:
        assert_no_prior_canonical_attempt(audit_log)
    except Exception as e:
        if not isinstance(e, FileNotFoundError):
            _fail_closed(str(e))

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
    # If closure fails, no canonical result may remain — mandatory closure errors must not be swallowed.
    success = False
    result_path = None
    try:
        # Load and validate dev items (36) — injectable for fake E2E (no plaintext)
        _sha_fn = _canonical_sha_fn or canonical_text_sha256
        # actual_sha already computed via _sha_fn? We already computed actual_sha above via canonical_text_sha256; for injection, caller already patched file existence, but we recompute via injected if needed.
        # For dev items, use injection if supplied
        if _load_and_validate_fn is not None:
            dev_items = _load_and_validate_fn(dev_path_resolved, role="dev")
        else:
            dev_items = load_and_validate(dev_path_resolved, role="dev")
        if len(dev_items) != EXPECTED_DEV_CASES:
            _fail_closed(f"dev cases mismatch: got {len(dev_items)} expected {EXPECTED_DEV_CASES}")

        # --- Retrieval execution: real DB/model vs injected fakes (both go through same orchestration/validation/write/audit lifecycle) ---
        # Injection path: when any test factory is supplied, bypass real DB/model and use fakes (no DATABASE_URL/model load)
        is_injected = any(x is not None for x in (_embedding_fn_factory, _retrieval_fn_factory, _latency_measurer_factory, _corpus_provenance_fn))
        if is_injected:
            # Injected fake path — no DB/model, but still same audit lifecycle, corpus validation, orchestration, atomic write
            if _corpus_provenance_fn is not None:
                corpus_provenance = _corpus_provenance_fn()
            else:
                # Default valid corpus for pure tests without DB
                corpus_provenance = {
                    "total_policies": 13589,
                    "total_chunks": 17609,
                    "by_source": {
                        "youth": {"policies": 2631, "chunks": 3083},
                        "gov24": {"policies": 10958, "chunks": 14526},
                    },
                }
            try:
                validate_corpus_provenance(corpus_provenance)
            except Exception as e:
                _fail_closed(f"corpus provenance validation failed (injected): {e} — got {corpus_provenance}")
            # Build injected embedding/retrieval/latency — factories accept dummy placeholder if needed
            if _embedding_fn_factory is not None:
                embedding_fn = _embedding_fn_factory(None)
            else:
                # Default fake embedding that validates prefix contract via caller-observable side-effect: use format_pgvector on dummy vector
                def _default_fake_embed(stripped: str):
                    # Simulate production prefix: must be called with stripped that was strip_region(raw)
                    # For test, we just return pgvector string of dummy vector
                    import hashlib
                    # deterministic dummy vector via hash
                    h = hashlib.sha256(stripped.encode()).hexdigest()
                    vals = [int(h[i:i+2], 16) / 255.0 for i in range(0, 6, 2)]
                    return format_pgvector(vals)
                embedding_fn = _default_fake_embed
            if _retrieval_fn_factory is not None:
                retrieval_fn = _retrieval_fn_factory(None, None)
            else:
                # Default fake retrieval that returns controlled ranks: baseline worst, candidates better
                def _default_fake_retrieve(candidate_id: str, vec, lexical_terms: list[str], youth_bias: float, age, rp):
                    assert_rp_is_null(rp)
                    # Validate vec is pgvector string (production parity)
                    assert isinstance(vec, str) and vec.startswith("[") and vec.endswith("]"), f"vec must be pgvector string, got {vec!r}"
                    # Return 30 results with synthetic source_ids; gold is determined by test's dev_items gold fields
                    # For generic fallback, return empty (no gold) — metrics will be zero
                    return []
                retrieval_fn = _default_fake_retrieve
            if _latency_measurer_factory is not None:
                latency_measurer = _latency_measurer_factory(dev_items, embedding_fn, retrieval_fn)
            else:
                latency_measurer = None
            # Orchestrate with injected dependencies — same single code path
            result = orchestrate_4way_batch(
                dev_items,
                embedding_fn=embedding_fn,
                retrieval_fn=retrieval_fn,
                latency_measurer=latency_measurer,
                corpus_provenance=corpus_provenance,
            )
            result["provenance"] = {
                "dev_sha256": actual_sha,
                "grant_event_hash": grant["event_hash"],
                "run_start_event_hash": run_start_event["event_hash"] if run_start_event else None,
                "session_id": session_id,
                "executed_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
                "corpus_provenance": corpus_provenance,
            }
            validate_complete_result(result)
            result_path = atomic_write_result(result, out_path)
        else:
            # --- Real DB/model path (production canonical) ---
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

            # Use single DB connection for same-DB constraint (corpus provenance + 4-way retrieval)
            conn = psycopg2.connect(db_url)
            try:
                # Corpus provenance: same DB/corpus, fail-closed — total policy/chunk + Youth/Gov24 split from same connection
                corpus_provenance = get_corpus_provenance(conn)
                try:
                    validate_corpus_provenance(corpus_provenance)
                except Exception as e:
                    _fail_closed(f"corpus provenance validation failed (same DB/corpus required): {e} — got {corpus_provenance}")

                # Warm model
                model = SentenceTransformer("intfloat/multilingual-e5-base")
                embedding_fn = _real_embedding_fn_factory(model)
                retrieval_fn = _real_retrieval_fn_factory(conn, model)

                # Latency measurer: predefined warm paired, only for quality-selectable
                latency_measurer = _real_latency_measurer_factory(dev_items, embedding_fn, retrieval_fn)

                # Orchestrate 4-way batch (this is the real single code path) — pass same-DB corpus provenance
                result = orchestrate_4way_batch(
                    dev_items,
                    embedding_fn=embedding_fn,
                    retrieval_fn=retrieval_fn,
                    latency_measurer=latency_measurer,
                    corpus_provenance=corpus_provenance,
                )

                # Enrich result with provenance (audit grant linkage)
                result["provenance"] = {
                    "dev_sha256": actual_sha,
                    "grant_event_hash": grant["event_hash"],
                    "run_start_event_hash": run_start_event["event_hash"] if run_start_event else None,
                    "session_id": session_id,
                    "executed_at": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
                    "corpus_provenance": corpus_provenance,
                }

                # Strict validation before write (includes corpus, git SHA, selected candidate, latency, metrics consistency)
                validate_complete_result(result)

                # Atomic write only after all validation — single batch guard + concurrent race guard
                result_path = atomic_write_result(result, out_path)

            finally:
                try:
                    conn.close()
                except Exception:
                    pass

        # Success path: append run_end success and close protected access — fail-closed, cleanup result on failure
        try:
            append_canonical_run_end(
                audit_log,
                candidate_id=BATCH_ID,
                set_sha=EXPECTED_DEV_SHA256,
                outcome="success",
                session_id=session_id,
            )
        except Exception as e:
            # Mandatory closure failed — result must not remain
            if result_path is not None:
                try:
                    pathlib.Path(result_path).unlink()
                except Exception:
                    pass
            _fail_closed(f"audit run_end append failed (fail-closed, result removed): {e}")
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
            if result_path is not None:
                try:
                    pathlib.Path(result_path).unlink()
                except Exception:
                    pass
            _fail_closed(f"audit protected_access_end append failed (fail-closed, result removed): {e}")
        success = True
    except Exception as e:
        # Failure path: append run_end with failure, then lifecycle closure — mandatory, not swallowed
        run_end_failed = False
        protected_failed = False
        run_end_err = None
        protected_err = None
        try:
            append_canonical_run_end(
                audit_log,
                candidate_id=BATCH_ID,
                set_sha=EXPECTED_DEV_SHA256,
                outcome="failure",
                session_id=session_id,
            )
        except Exception as ee:
            run_end_failed = True
            run_end_err = ee
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
        except Exception as ee:
            protected_failed = True
            protected_err = ee
        # Cleanup result if it was published before failure (fail-closed: no result may remain if closure fails)
        if result_path is not None:
            try:
                pathlib.Path(result_path).unlink()
            except Exception:
                pass
        # Also handle case where result_path is set but file not yet written? Ensure by checking out_path exists
        else:
            # If orchestration succeeded partially and atomic_write was attempted but failed after run_end?
            # Check if output file now exists at out_path (race) and remove if failure closure
            try:
                if pathlib.Path(out_path).exists():
                    # If we are in failure path, ensure no result remains even if result_path not set (e.g., after atomic_write but before assign)
                    pathlib.Path(out_path).unlink()
            except Exception:
                pass
        if run_end_failed or protected_failed:
            _fail_closed(
                f"audit closure failed after canonical failure (fail-closed, result removed): run_end_failed={run_end_failed} err={run_end_err!r} protected_failed={protected_failed} err={protected_err!r} original_error={e!r}"
            )
        _fail_closed(f"canonical dev batch failed (fail-closed): {e}")
    finally:
        # Ensure result artifact exists only on success; on failure it must not exist (fail-closed) — handle closure-failure case where success flag not yet set
        if not success and result_path is not None:
            try:
                p = pathlib.Path(result_path)
                if p.exists():
                    p.unlink()
            except Exception:
                pass
        # Also ensure out_path not left if success is False (e.g., atomic_write succeeded but closure failed and we already removed result_path, but check direct path)
        if not success:
            try:
                direct = pathlib.Path(out_path)
                if direct.exists():
                    # Only remove if this invocation created it (audit one-shot ensures single batch, so safe to remove on failure)
                    # Verify by checking if audit has failure run_end for this session? But simpler: remove if not success
                    direct.unlink()
            except Exception:
                pass


if __name__ == "__main__":
    main()
