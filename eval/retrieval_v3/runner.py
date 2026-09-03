"""Candidate A runner — orchestrator + CLI, pure/static/mock hardening, audit lifecycle."""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import re
import sys
import subprocess
from typing import Any, Callable

from .candidate_registry import load_and_validate, EXPECTED_SHA, EXPECTED_PREREG_SHA
from .normalization import strip_region, lexical_overlap_terms, youth_source_bias, normalize_exact
from .safe_action import classify_safe_action
from .production_exclusion import filter_policies_for_retrieval
from .evaluation_context import capture_pinned_context, validate_pinned_context
from .safety import evaluate_owned_unsupported, evaluate_owned_ambiguous, check_production_exclusion, cross_check_owned_core, action_correct_for_role
from .exact import is_exact_title, is_exact_org
from .dense import dense_top100, filter_dense_by_cosine_min, cosine_similarity
from .sparse import sparse_top100
from .fusion import fuse_candidates
from .dedup import full_top30_pipeline
from .metrics import compute_headline_metrics, compute_oracle_recall, compute_slice_diagnostics, wilson_interval, clopper_pearson_interval
from .selection import select_candidate, candidate_b_gate
from .latency import measure_paired_latency
from .result_schema import build_result_skeleton, validate_complete_result, atomic_write_result
from .paths import validate_output_path, CANONICAL_DEV_OUTPUT_REL
from . import audit

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_AUDIT_LOG = REPO_ROOT / "eval" / "retrieval-v3" / "audit" / "events.jsonl"
DEFAULT_AUDIT_LOG_ALT = REPO_ROOT / "eval" / "retrieval_v3" / "audit" / "events.jsonl"

CANDIDATE_PLAN_PATH = REPO_ROOT / "eval" / "retrieval-v3" / "candidate-plan" / "candidate-plan-v4.json"
PREREG_PATH = REPO_ROOT / "docs" / "RETRIEVAL_V3_PREREG.md"
HEADLINE_STRATA = frozenset({"exact_navigation", "natural_needs", "exploratory_multi_valid", "multi_constraint", "short_keywords", "colloquial_typo_spacing_abbrev"})
# D-039 canonical protected-dev invariants (D-015 §3 exact; D-003 production baseline descriptor).
DEV_CANONICAL_N = 180
DEV_HEADLINE_N = 130
DEV_LOCATION_N = 54
DEV_STRATA_EXACT = {"exact_navigation": 21, "natural_needs": 25, "exploratory_multi_valid": 21, "multi_constraint": 25, "short_keywords": 18, "colloquial_typo_spacing_abbrev": 20, "ambiguous": 23, "unsupported_no_answer": 27}
D003_BASELINE = {"RERANK": 0, "CANDIDATES": 30, "COSINE_MIN": 0.78, "LEXICAL_BIAS": 0.01, "strip_region": True, "youth_bias_suppressed_for_gov24_orgs": True, "embedding": "intfloat/multilingual-e5-base"}
# D-056: production-faithful real adapters live in .real_adapters, bound to
# ONE governing RealEvaluationSession (shared capture/corpus/D-003 context).
# Import and construction perform no real IO (lazy drivers/model, no connect,
# no file/network); missing prerequisites fail closed with explicit FIRST-dev
# preflight blockers. The eight D-054 independent stub factories are replaced
# by the session-bound bundle (independent factories would break the shared
# session/date lifecycle). Every bound callable carries __real_adapter__.
from .real_adapters import RealEvaluationSession, build_real_adapters
def _is_real_adapter(fn: object) -> bool:
    return bool(getattr(fn, "__real_adapter__", False))
def _is_canonical_output_path(output_path: str | pathlib.Path | None) -> bool:
    """Exact canonical dev output check (OS-agnostic, no IO)."""
    if not output_path:
        return False
    try:
        from .paths import CANONICAL_DEV_OUTPUT_REL as _REL, CANONICAL_DEV_OUTPUT_ALT as _ALT
        out_posix = pathlib.PurePath(str(output_path)).as_posix()
        return out_posix in (pathlib.PurePath(str(_REL)).as_posix(), pathlib.PurePath(str(_ALT)).as_posix())
    except Exception:
        return False
def validate_canonical_dev_tasks(tasks: list[dict]) -> dict:
    """Fail-closed exact DEV 180/130/54/strata/source-truth validation (pure, no retrieval/DB/model)."""
    if len(tasks) != DEV_CANONICAL_N:
        raise ValueError(f"canonical dev n must be 180, got {len(tasks)}")
    from collections import Counter as _Counter
    strata = _Counter(t.get("stratum") for t in tasks)
    for s, need in DEV_STRATA_EXACT.items():
        if strata.get(s, 0) != need:
            raise ValueError(f"canonical dev stratum {s} must be {need}, got {strata.get(s, 0)}")
    unknown = [s for s in strata if s not in DEV_STRATA_EXACT]
    if unknown:
        raise ValueError(f"canonical dev unknown strata {unknown} (fail-closed)")
    headline = [t for t in tasks if t.get("stratum") in HEADLINE_STRATA and not t.get("is_ambiguous") and not t.get("is_unsupported")]
    if len(headline) != DEV_HEADLINE_N:
        raise ValueError(f"canonical dev headline_n must be 130, got {len(headline)}")
    loc = sum(1 for t in tasks if t.get("location_bearing") is True)
    if loc != DEV_LOCATION_N:
        raise ValueError(f"canonical dev location must be 54, got {loc}")
    for t in headline:
        golds = t.get("golds") or t.get("gold") or []
        if not golds:
            raise ValueError(f"canonical headline task missing golds: {t.get('task_id') or t.get('id')}")
        ok = False
        for g in golds:
            if not isinstance(g, dict) or "grade" not in g:
                raise ValueError(f"canonical headline gold missing explicit grade: {t.get('task_id') or t.get('id')}")
            if not isinstance(g.get("source"), str) or not isinstance(g.get("source_id"), str):
                raise ValueError(f"canonical headline gold missing source/source_id: {t.get('task_id') or t.get('id')}")
            if isinstance(g.get("grade"), (int, float)) and g["grade"] >= 2:
                ok = True
        if not ok:
            raise ValueError(f"canonical headline task without grade>=2 source-truth gold: {t.get('task_id') or t.get('id')}")
    for t in tasks:
        if t.get("stratum") == "unsupported_no_answer":
            for g in (t.get("golds") or t.get("gold") or []):
                if isinstance(g, dict) and isinstance(g.get("grade"), (int, float)) and g["grade"] >= 2:
                    raise ValueError(f"canonical unsupported task with grade>=2 gold: {t.get('task_id') or t.get('id')}")
    return {"n": 180, "headline_n": 130, "location_n": loc, "strata": dict(strata)}

def _get_git_head() -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=str(REPO_ROOT))
        if r.returncode != 0:
            raise RuntimeError(f"git rev-parse HEAD failed: {r.stderr[:200]}")
        head = r.stdout.strip().lower()
        if not re.fullmatch(r"[0-9a-f]{40}", head):
            raise ValueError(f"git head not 40-hex: {head!r}")
        return head
    except Exception as e:
        raise RuntimeError(f"git head probe fail-closed: {e}") from e

def _get_git_dirty() -> bool:
    try:
        r = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=str(REPO_ROOT))
        if r.returncode != 0:
            raise RuntimeError(f"git status failed: {r.stderr[:200]}")
        return bool(r.stdout.strip())
    except Exception as e:
        raise RuntimeError(f"git dirty probe fail-closed: {e}") from e

def _sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_candidate_plan_or_fail(plan_path: pathlib.Path | None = None) -> dict:
    pp = pathlib.Path(plan_path) if plan_path else CANDIDATE_PLAN_PATH
    if not pp.exists():
        alt = REPO_ROOT / "eval" / "retrieval_v3" / "candidate-plan" / "candidate-plan-v4.json"
        if alt.exists():
            pp = alt
        else:
            raise FileNotFoundError(f"candidate plan not found: {pp}")
    data, raw = json.loads(pp.read_text(encoding="utf-8")), pp.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != EXPECTED_SHA:
        raise ValueError(f"candidate plan SHA mismatch: {sha} != {EXPECTED_SHA}")
    return load_and_validate(str(pp))

def validate_protected_access(
    audit_log: pathlib.Path,
    set_role: str,
    set_sha: str,
    session_id: str,
    expected_event_hash: str | None = None,
) -> dict:
    """Verify grant before opening protected plaintext. Fail-closed."""
    return audit.verify_holdout_access_allowed(
        str(audit_log),
        set_role=set_role,
        set_sha=set_sha,
        session_id=session_id,
        expected_event_hash=expected_event_hash,
    )

class Runner:
    """Orchestrator — pure logic with injected dependencies for testing (fake DB/model/protected loader)."""

    def __init__(
        self,
        candidate_plan: dict,
        embedding_fn: Callable[[str], list[float]] | None = None,
        db_policy_loader: Callable[[], list[dict]] | None = None,
        protected_set_loader: Callable[[str, str], list[dict]] | None = None,
        audit_log_path: pathlib.Path | str | None = None,
        corpus_provenance_fn: Callable[[], dict] | None = None,
        http_checker: Callable | None = None,
        clock_fn: Callable[[], int] | None = None,
        safety_evidence_fn: Callable[[dict], dict] | None = None,
        d003_baseline_fn: Callable | None = None,
        evaluation_context_exec_fn: Callable[[str], Any] | None = None,
        adapter_kind: str = "mock",
        evaluation_session: Any | None = None,
    ):
        self.candidate_plan = candidate_plan
        self.plan_data = candidate_plan
        from .candidate_registry import validate_data
        validate_data(candidate_plan)
        self.embedding_fn = embedding_fn
        self.db_policy_loader = db_policy_loader
        self.protected_set_loader = protected_set_loader
        self.audit_log_path = pathlib.Path(audit_log_path) if audit_log_path else DEFAULT_AUDIT_LOG
        if not self.audit_log_path.exists():
            alt = DEFAULT_AUDIT_LOG_ALT
            if alt.exists():
                self.audit_log_path = alt
        self.corpus_provenance_fn = corpus_provenance_fn
        self.http_checker = http_checker
        self.clock_fn = clock_fn
        # D-039: real safety measurement + D-003 baseline hooks. None => pre-dev HOLD (fail-closed).
        self.safety_evidence_fn = safety_evidence_fn
        self.d003_baseline_fn = d003_baseline_fn
        # D-054: evaluation-context capture executor (SHOW TimeZone + SELECT CURRENT_DATE).
        # Canonical requires it pre-grant; None => pre-dev HOLD for production_exclusion (fail-closed).
        self.evaluation_context_exec_fn = evaluation_context_exec_fn
        # D-040: canonical-dev requires real adapters (mock CLI keeps fakes separately).
        if adapter_kind not in ("mock", "real"):
            raise ValueError(f"adapter_kind must be mock/real, got {adapter_kind!r}")
        self.adapter_kind = adapter_kind
        # D-056: governing real evaluation resource (close owned exactly once
        # by run_dev_evaluation when bound; None for pure/mock runs).
        self.evaluation_session = evaluation_session

    def _retrieve_for_query(
        self,
        query: str,
        policies: list[dict],
        config: dict,
        qvec: list[float] | None = None,
    ) -> dict:
        """Execute retrieval for single query under config — returns pools and final top30."""
        # D-039: fail-closed blank at lowest level (D-037 only checked callers). Blank never silently retrieves.
        if not isinstance(query, str) or not query.strip():
            raise ValueError("empty query (fail-closed)")
        q_stripped = strip_region(query)
        if not q_stripped.strip():
            raise ValueError("empty query after strip_region (fail-closed)")
        if qvec is None:
            if self.embedding_fn is None:
                raise RuntimeError("embedding_fn not injected (fail-closed, no real model load)")
            qvec = self.embedding_fn(f"query: {q_stripped}")
            if len(qvec) != 768:
                raise ValueError(f"embedding dim must be 768, got {len(qvec)}")

        d_top100 = dense_top100(qvec, policies)
        d_filtered = filter_dense_by_cosine_min(d_top100, 0.78)
        s_top100 = sparse_top100(q_stripped, policies, config)

        fused = fuse_candidates(
            query=q_stripped,
            dense_filtered=d_filtered,
            sparse_top100=s_top100,
            config=config,
            qvec=qvec,
            policies_by_key=None,
            dense_lookup={ (e["source"], e["source_id"]): e["dense_cosine"] for e in d_filtered },
            sparse_lookup={ (e["source"], e["source_id"]): e["weighted_overlap"] for e in s_top100 },
        )

        final_top30 = full_top30_pipeline(fused, config["dedup_cosine_threshold"], config["diversification_lambda"], qvec=qvec)

        exact_candidates = []
        for p in policies:
            it = is_exact_title(q_stripped, p.get("title") or "")
            io = is_exact_org(q_stripped, p.get("org") or "")
            if it or io:
                exact_candidates.append({
                    "policy": p,
                    "source": p["source"],
                    "source_id": p["source_id"],
                    "policy_id": p["id"],
                    "is_exact_title": it,
                    "is_exact_org": io,
                })
        exact_candidates.sort(key=lambda x: (-x["is_exact_title"], -x["is_exact_org"], x["source"], x["source_id"], x["policy_id"]))
        union_map = {}
        for e in d_filtered:
            key = (e["source"], e["source_id"])
            if key not in union_map:
                union_map[key] = e["policy"]
        for e in s_top100:
            key = (e["source"], e["source_id"])
            if key not in union_map:
                union_map[key] = e["policy"]
        for e in exact_candidates[:100]:
            key = (e["source"], e["source_id"])
            if key not in union_map:
                union_map[key] = e["policy"]

        dense_oracle = [{"source": e["source"], "source_id": e["source_id"]} for e in d_top100]
        sparse_oracle = [{"source": e["source"], "source_id": e["source_id"]} for e in s_top100]
        exact_oracle = [{"source": e["source"], "source_id": e["source_id"]} for e in exact_candidates]

        union_ordered = []
        seen = set()
        for e in d_filtered:
            k = (e["source"], e["source_id"])
            if k not in seen:
                union_ordered.append({"source": k[0], "source_id": k[1]})
                seen.add(k)
        for e in s_top100:
            k = (e["source"], e["source_id"])
            if k not in seen:
                union_ordered.append({"source": k[0], "source_id": k[1]})
                seen.add(k)
        for e in exact_candidates[:100]:
            k = (e["source"], e["source_id"])
            if k not in seen:
                union_ordered.append({"source": k[0], "source_id": k[1]})
                seen.add(k)

        return {
            "final_top30": final_top30,
            "dense_top100": d_top100,
            "dense_filtered": d_filtered,
            "sparse_top100": s_top100,
            "exact_candidates": exact_candidates,
            "union_ordered": union_ordered,
            "dense_oracle_pool": dense_oracle,
            "sparse_oracle_pool": sparse_oracle,
            "exact_oracle_pool": exact_oracle,
            "union_oracle_pool": union_ordered,
            "qvec": qvec,
            "q_stripped": q_stripped,
        }

    def run_dev_evaluation(
        self,
        tasks: list[dict],
        policies: list[dict],
        session_id: str,
        set_role: str = "dev",
        set_sha: str | None = None,
        audit_log: pathlib.Path | None = None,
        expected_event_hash: str | None = None,
        output_path: str | pathlib.Path | None = None,
        skip_audit: bool = False,
    ) -> dict:
        """Run full dev evaluation over tasks — pure logic with injected fakes, audit lifecycle.

        D-056 ownership: when evaluation_session is bound, it is closed exactly
        once here on every exit (success or any failure: capture, corpus,
        grant, loader, retrieval, safety, latency, result write, audit close).
        """
        session = self.evaluation_session
        try:
            return self._run_dev_evaluation_inner(
                tasks, policies, session_id, set_role, set_sha,
                audit_log, expected_event_hash, output_path, skip_audit,
            )
        finally:
            if session is not None and not session.is_closed:
                session.close()

    def _run_dev_evaluation_inner(
        self,
        tasks: list[dict],
        policies: list[dict],
        session_id: str,
        set_role: str = "dev",
        set_sha: str | None = None,
        audit_log: pathlib.Path | None = None,
        expected_event_hash: str | None = None,
        output_path: str | pathlib.Path | None = None,
        skip_audit: bool = False,
    ) -> dict:
        """Run full dev evaluation over tasks — pure logic with injected fakes, audit lifecycle."""
        # D-039: explicit canonical protected-dev mode (grant-before-loader, exact 180/130/54, no fake adapters).
        # D-040 correction-3: exact-one protected_access_end success/failure after verified grant.
        is_canonical = (set_role == "dev" and set_sha is not None)
        if is_canonical and skip_audit:
            raise ValueError("canonical protected-dev mode requires audit (skip_audit=False, fail-closed)")
        if is_canonical and tasks:
            raise ValueError("canonical protected-dev mode forbids directly injected tasks (no fake adapters; load via protected_set_loader after grant, fail-closed)")
        if is_canonical and self.protected_set_loader is None:
            raise ValueError("canonical protected-dev mode requires protected_set_loader (fail-closed)")
        if is_canonical and getattr(self, "adapter_kind", "mock") != "real":
            raise ValueError("canonical protected-dev mode forbids mock adapters (adapter_kind=real with lazy real adapters, patched only in tests, fail-closed)")
        if output_path:
            # D-040: canonical with set_sha must target exact canonical output (strict); mock keeps confined non-strict.
            validate_output_path(output_path, strict_canonical=bool(is_canonical))
            if is_canonical and not _is_canonical_output_path(output_path):
                raise ValueError(f"canonical dev result must write exact canonical output (fail-closed): got {output_path!r}")
        # D-041 correction-4: mandatory lazy REAL adapters wired before grant (presence checked pre-verification;
        # no close needed on this failure; unpatched factories raise without IO; tests patch with synthetics).
        if is_canonical and self.safety_evidence_fn is None:
            raise ValueError("canonical protected-dev mode requires safety_evidence_fn (lazy REAL six-gate measurement, patched only in tests, fail-closed)")
        if is_canonical and self.d003_baseline_fn is None:
            raise ValueError("canonical protected-dev mode requires d003_baseline_fn (lazy REAL production baseline, patched only in tests, fail-closed)")
        if is_canonical and self.clock_fn is None:
            raise ValueError("canonical protected-dev mode requires clock_fn (lazy REAL ns clock, patched only in tests, fail-closed)")
        if is_canonical and self.corpus_provenance_fn is None:
            raise ValueError("canonical protected-dev mode requires corpus_provenance_fn (lazy REAL corpus pin, patched only in tests, fail-closed)")
        # D-054: evaluation-context capture executor required pre-grant (presence checked
        # pre-verification; no close needed on this failure; tests patch with synthetics).
        if is_canonical and self.evaluation_context_exec_fn is None:
            raise ValueError("canonical protected-dev mode requires evaluation_context_exec_fn (lazy REAL capture adapter, patched only in tests, fail-closed)")
        audit_log = pathlib.Path(audit_log) if audit_log else self.audit_log_path
        # D-054: capture the pinned evaluation context EXACTLY ONCE here — after effective
        # plan-v4 validation (Runner.__init__) and BEFORE grant verification, protected
        # loader, corpus/task validation, and run_start. Immutable for the entire run,
        # shared by Candidate A, the paired D-003 baseline, filter, and audit.
        # Pre-grant failure raises with no grant-close side-effect (fail-closed, no fallback).
        pinned_context: dict | None = None
        if self.evaluation_context_exec_fn is not None:
            try:
                pinned_context = capture_pinned_context(self.evaluation_context_exec_fn)
                validate_pinned_context(pinned_context)
            except Exception as e:
                raise RuntimeError(f"evaluation-context capture failed (fail-closed, no fallback date): {e}") from e
        elif is_canonical:
            raise ValueError("canonical protected-dev mode requires evaluation_context_exec_fn (fail-closed)")
        # D-056: real canonical path loads the corpus AFTER capture on the
        # governing session (pre-capture load is forbidden: expiry inclusion
        # depends on the pinned date). Pre-grant failure needs no grant close.
        # Mock kind and loader-less runs keep the injected policies argument.
        if is_canonical and getattr(self, "adapter_kind", "mock") == "real" and self.db_policy_loader is not None:
            try:
                policies = self.db_policy_loader()
            except Exception as e:
                raise RuntimeError(f"real corpus load failed pre-grant (fail-closed): {e}") from e
            if not policies:
                raise ValueError("real corpus empty (fail-closed)")
        # D-040 grant lifecycle flags: verified once, closed exactly once, never closed on failed verification.
        grant_verified = False
        grant_closed = False
        grant_close_tried = False
        def _close_grant(outcome: str) -> None:
            nonlocal grant_closed, grant_close_tried
            if grant_closed:
                raise RuntimeError("grant already closed (exact-one violation, fail-closed)")
            if grant_close_tried:
                raise RuntimeError("grant close already attempted (exact-one violation, fail-closed)")
            grant_close_tried = True
            if outcome not in ("success", "failure"):
                raise ValueError(f"grant close outcome must be success/failure, got {outcome!r}")
            audit.append_event(
                str(audit_log),
                action="protected_access_end",
                set_role=set_role,
                set_sha=set_sha,
                candidate_id="v3-candidate-dev-v1",
                session_id=session_id,
                outcome=outcome,
                # D-054: pinned context rides the existing close event (no new gate/action).
                db_session_timezone=(pinned_context or {}).get("db_session_timezone"),
                evaluation_as_of_date=(pinned_context or {}).get("evaluation_as_of_date"),
            )
            grant_closed = True
        if is_canonical:
            # Grant BEFORE loader (fail-closed; loader never runs without grant; no close on failed verification).
            try:
                validate_protected_access(audit_log, set_role, set_sha, session_id, expected_event_hash)
            except Exception as e:
                raise RuntimeError(f"protected access grant verification failed (fail-closed): {e}") from e
            grant_verified = True
            try:
                tasks = self.protected_set_loader(set_role, set_sha)
            except Exception as e:
                try:
                    _close_grant("failure")
                except Exception as ce:
                    raise RuntimeError(f"grant close on loader failure failed (fail-closed): {ce}") from e
                raise RuntimeError(f"canonical protected loader failed (fail-closed): {e}") from e
            try:
                validate_canonical_dev_tasks(tasks)
            except Exception as e:
                try:
                    _close_grant("failure")
                except Exception as ce:
                    raise RuntimeError(f"grant close on canonical validation failure failed (fail-closed): {ce}") from e
                raise
        elif not skip_audit and set_sha:
            try:
                validate_protected_access(audit_log, set_role, set_sha, session_id, expected_event_hash)
            except Exception as e:
                raise RuntimeError(f"protected access grant verification failed (fail-closed): {e}") from e
        if output_path:
            out_abs = (REPO_ROOT / output_path).resolve() if not pathlib.Path(output_path).is_absolute() else pathlib.Path(output_path).resolve()
            if out_abs.exists():
                # D-040: pre-run rerun guard failure after verified grant must still close grant exactly once.
                if is_canonical and grant_verified and not grant_closed:
                    try:
                        _close_grant("failure")
                    except Exception as ce:
                        raise RuntimeError(f"grant close on pre-run output-exists failure failed (fail-closed): {ce}") from ce
                raise FileExistsError(f"output already exists: {out_abs} — rerun guard")
        # D-042: corpus provenance gathered pre-run (static per run); canonical failure closes grant exactly once.
        corpus_prov = None
        try:
            if self.corpus_provenance_fn is not None:
                corpus_prov = self.corpus_provenance_fn()
            if is_canonical:
                if not isinstance(corpus_prov, dict) or not corpus_prov:
                    raise ValueError("canonical corpus_provenance must be nonempty dict (fail-closed)")
                _tp = corpus_prov.get("total_policies")
                if "total_policies" in corpus_prov and (not isinstance(_tp, int) or isinstance(_tp, bool) or _tp <= 0):
                    raise ValueError("canonical corpus_provenance.total_policies must be positive int (fail-closed)")
                _snap = corpus_prov.get("snapshot")
                if isinstance(_snap, str):
                    if not _snap.strip():
                        raise ValueError("canonical corpus_provenance.snapshot must be nonempty (fail-closed)")
                elif isinstance(_snap, dict):
                    if not _snap:
                        raise ValueError("canonical corpus_provenance.snapshot must be nonempty (fail-closed)")
                else:
                    raise ValueError("canonical corpus_provenance.snapshot identity required (fail-closed)")
            # D-054: runner-owned pinned context overwrites into corpus provenance (fail-closed
            # against corpus forgery; canonical requires a pinned date for filter+audit).
            if is_canonical:
                if pinned_context is None:
                    raise ValueError("canonical run requires pinned evaluation context (fail-closed)")
                corpus_prov = {**corpus_prov, "db_session_timezone": pinned_context["db_session_timezone"], "evaluation_as_of_date": pinned_context["evaluation_as_of_date"]}
            elif pinned_context is not None and isinstance(corpus_prov, dict):
                corpus_prov = {**corpus_prov, "db_session_timezone": pinned_context["db_session_timezone"], "evaluation_as_of_date": pinned_context["evaluation_as_of_date"]}
        except Exception as e:
            if is_canonical and grant_verified and not grant_closed:
                try:
                    _close_grant("failure")
                except Exception as ce:
                    raise RuntimeError(f"grant close on corpus failure failed (fail-closed): {ce}") from e
            if is_canonical:
                raise RuntimeError(f"canonical corpus provenance failed (fail-closed): {e}") from e
            corpus_prov = None
        run_start_event = None
        run_end_event = None
        need_audit_close = False
        run_end_appended = False
        if not skip_audit:
            try:
                # D-039: preflight BEFORE second run_start — never append a duplicate (actions stay [run_start,run_end]).
                pre_chain = audit.read_and_verify_chain(str(audit_log))
                pre_starts = [e for e in pre_chain if e.get("action") == "run_start" and e.get("set_sha") == (set_sha.lower() if isinstance(set_sha, str) else set_sha) and e.get("set_role") == set_role]
                if len(pre_starts) >= 1:
                    raise RuntimeError(f"rerun detected (preflight): run_start count for {set_role}/{set_sha} is {len(pre_starts)} (expected 0, fail-closed)")
                run_start_event = audit.append_event(
                    str(audit_log),
                    action="run_start",
                    set_role=set_role,
                    set_sha=set_sha,
                    candidate_id="v3-candidate-dev-v1",
                    session_id=session_id,
                    # D-054: pinned context on the existing run event (no new gate/action).
                    db_session_timezone=(pinned_context or {}).get("db_session_timezone"),
                    evaluation_as_of_date=(pinned_context or {}).get("evaluation_as_of_date"),
                )
                need_audit_close = True
                chain = audit.read_and_verify_chain(str(audit_log))
                run_starts = [e for e in chain if e.get("action") == "run_start" and e.get("set_sha") == (set_sha.lower() if isinstance(set_sha, str) else set_sha) and e.get("set_role") == set_role]
                if len(run_starts) != 1:
                    raise RuntimeError(f"rerun detected: run_start count for {set_role}/{set_sha} is {len(run_starts)} (expected 1, fail-closed)")
            except Exception as e:
                # D-040: pre-run failure after verified grant must close grant exactly once (no run_end; run_start never succeeded).
                if is_canonical and grant_verified and not grant_closed:
                    try:
                        _close_grant("failure")
                    except Exception as ce:
                        raise RuntimeError(f"grant close on pre-run failure failed (fail-closed): {ce}") from e
                raise RuntimeError(f"audit run_start failed (fail-closed, no result): {e}") from e
        try:
            if not is_canonical and not tasks and self.protected_set_loader:
                tasks = self.protected_set_loader(set_role, set_sha)
            if not tasks:
                raise ValueError("tasks empty (fail-closed)")
            if is_canonical:
                validate_canonical_dev_tasks(tasks)
            # D-054: unfiltered pinned corpus lookup (input-side evidence for the
            # independent audit; never based only on the filtered output).
            biz_end_lookup: dict = {}
            for _p in (policies or []):
                if isinstance(_p, dict):
                    biz_end_lookup[(_p.get("source"), _p.get("source_id"))] = _p.get("biz_end")
            # D-054: pre-retrieval D-003 exclusion on the pinned date, once per run and
            # shared by all 18 configs. Excluded rows cannot enter dense/sparse/exact pools.
            if pinned_context is not None:
                retrieval_policies = filter_policies_for_retrieval(policies or [], pinned_context["evaluation_as_of_date"])
            else:
                retrieval_policies = policies
            # D-054: frozen safe-action classification — query-only (raw query_text only),
            # BEFORE any retrieval call, once per task/session, shared identically across
            # all 18 configs. Retrieval cannot influence the action.
            def _task_role(t: dict) -> str | None:
                if t.get("is_unsupported") is True or t.get("stratum") == "unsupported_no_answer":
                    return "unsupported"
                if t.get("is_ambiguous") is True or t.get("stratum") == "ambiguous":
                    return "ambiguous"
                return None
            actions_by_tid: dict = {}
            for _t in tasks:
                _tid = _t.get("task_id") or _t.get("id")
                _q = _t.get("query") or _t.get("query_text") or ""
                actions_by_tid[_tid] = classify_safe_action(_q)

            headline_tasks = [t for t in tasks if t.get("stratum") in HEADLINE_STRATA and not t.get("is_ambiguous") and not t.get("is_unsupported")]
            # D-039: explicit allowlist only (D-037 `not in safety` silently included missing/unknown stratum as headline).
            # SAME-STAGE fail-closed: no silent fallback to grade-based or full-task headline.

            per_config_metrics = []
            latency_per_config = {}
            all_config_results = {}
            _cost_qvec_cache: dict = {}
            _cost_qstripped_cache: dict = {}
            for cfg in self.plan_data["configs"]:
                cid = cfg["config_id"]
                task_results = []
                oracle_tasks = []
                for task in tasks:
                    golds = task.get("golds") or task.get("gold") or []
                    normalized_golds = []
                    for g in golds:
                        if isinstance(g, dict):
                            if "grade" not in g:
                                raise ValueError(f"gold missing explicit grade (fail-closed): task {task.get('task_id') or task.get('id')}")
                            normalized_golds.append(g)
                        else:
                            raise ValueError(f"gold tuple form without explicit grade forbidden (fail-closed): task {task.get('task_id') or task.get('id')}")
                    # D-039: headline tasks must carry ≥1 gold (empty headline gold silently scores 0, masking data error).
                    # Safety tasks (unsupported/ambiguous) may legitimately have empty golds.
                    _is_headline_task = task.get("stratum") in HEADLINE_STRATA and not task.get("is_ambiguous") and not task.get("is_unsupported")
                    if _is_headline_task and not normalized_golds:
                        raise ValueError(f"headline task missing golds (fail-closed): task {task.get('task_id') or task.get('id')}")
                    q = task.get("query") or task.get("query_text") or ""
                    if not isinstance(q, str) or not q.strip():
                        raise ValueError(f"empty query (fail-closed): task {task.get('task_id') or task.get('id')}")
                    res = self._retrieve_for_query(q, retrieval_policies, cfg)
                    final_top30 = res["final_top30"]
                    _rtid = task.get("task_id") or task.get("id")
                    if _rtid not in _cost_qvec_cache:
                        try:
                            _cost_qvec_cache[_rtid] = list(res.get("qvec") or [])
                            _cost_qstripped_cache[_rtid] = res.get("q_stripped") or ""
                        except Exception:
                            pass
                    internal = [{"source": e["source"], "source_id": e["source_id"]} for e in final_top30]
                    _action = actions_by_tid[task.get("task_id") or task.get("id")]
                    # D-054: ANSWER exposes the normal visible ranking; ABSTAIN/CLARIFY
                    # expose no policy recommendation (visible suppressed, headline miss).
                    # Internal ranking is preserved separately for the audit.
                    visible = internal if _action == "ANSWER" else []
                    task_results.append({
                        "retrieved": visible,
                        "retrieved_internal": internal,
                        "safe_action": _action,
                        "golds": normalized_golds,
                        "source": task.get("source"),
                        "stratum": task.get("stratum"),
                        "location_bearing": task.get("location_bearing"),
                        "category": task.get("category"),
                        "freshness": task.get("freshness"),
                        "common_vs_rare": task.get("common_vs_rare"),
                        "task_id": task.get("task_id") or task.get("id"),
                    })
                    oracle_tasks.append({
                        "dense_pool": res["dense_oracle_pool"],
                        "sparse_pool": res["sparse_oracle_pool"],
                        "exact_pool": res["exact_oracle_pool"],
                        "union_pool": res["union_oracle_pool"],
                        "golds": normalized_golds,
                    })

                headline_ids = {t.get("task_id") or t.get("id") for t in headline_tasks}
                # SAME-STAGE fail-closed: explicit stratum headline only, no silent full-task inclusion.
                headline_results = [tr for tr in task_results if tr.get("task_id") in headline_ids]
                # For oracle, filter to headline only for B gate (C regression: headline130 only)
                headline_oracle_tasks = []
                for tr, ot in zip(task_results, oracle_tasks):
                    if tr.get("task_id") in headline_ids:
                        headline_oracle_tasks.append(ot)
                metrics_head = compute_headline_metrics(headline_results)
                # Union oracle Recall@K is set union per C — computed inside metrics via set union
                oracle_metrics_headline = compute_oracle_recall(headline_oracle_tasks)
                oracle_metrics_all = compute_oracle_recall(oracle_tasks)
                # For B gate use headline union R100 only
                union_r100 = oracle_metrics_headline.get("union_recall_at_100", 0.0)
                slice_diagnostics = {}
                # D-026: secondary slices report unavailable if metadata absent
                for sk in ["source", "stratum", "location_bearing", "category", "freshness", "common_vs_rare"]:
                    try:
                        sd = compute_slice_diagnostics(task_results, sk)
                        # Metrics returns "unavailable" string when absent; preserve
                        slice_diagnostics[sk] = sd
                    except Exception as e:
                        slice_diagnostics[sk] = "unavailable"
                per_config_metrics.append({
                    "config_id": cid,
                    "success_at_1": metrics_head.get("success_at_1", 0.0),
                    "success_at_3": metrics_head.get("success_at_3", 0.0),
                    "success_at_5": metrics_head["success_at_5"],
                    "success_at_5_strict_grade3": metrics_head.get("success_at_5_strict_grade3", 0.0),
                    "success_at_5_grade3": metrics_head.get("success_at_5_strict_grade3", 0.0),
                    "ndcg_at_5": metrics_head["ndcg_at_5"],
                    "ndcg_at_10": metrics_head.get("ndcg_at_10", 0.0),
                    "mrr_at_10": metrics_head["mrr_at_10"],
                    "n": metrics_head["n"],
                    "success_count": metrics_head["success_at_5_count"],
                    "success_at_1_count": metrics_head.get("success_at_1_count", 0),
                    "success_at_3_count": metrics_head.get("success_at_3_count", 0),
                    "success_at_5_strict_grade3_count": metrics_head.get("success_at_5_strict_grade3_count", 0),
                    "oracle_recall": oracle_metrics_headline,
                    "oracle_recall_all": oracle_metrics_all,
                    "union_oracle_R100": union_r100,
                    "slice_diagnostics": slice_diagnostics,
                })
                all_config_results[cid] = {"task_results": task_results, "oracle_tasks": oracle_tasks, "metrics_head": metrics_head}
            # D-061 cost probes: once per task, outside timed samples, same session/snapshot.
            # Reuses cached qvec (0 extra model calls); pure lexical terms; never feeds ranking.
            if pinned_context is not None and getattr(self, "evaluation_session", None) is not None:
                _sess = self.evaluation_session
                _probe_fn = getattr(_sess, "probe_task_cost", None)
                if callable(_probe_fn):
                    try:
                        _as_of = (pinned_context or {}).get("evaluation_as_of_date")
                        for _tid, _qv in list(_cost_qvec_cache.items()):
                            _qs = _cost_qstripped_cache.get(_tid, "")
                            try:
                                _terms = lexical_overlap_terms(_qs if isinstance(_qs, str) else "")
                            except Exception:
                                continue
                            try:
                                _yb = youth_source_bias(_qs if isinstance(_qs, str) else "")
                            except Exception:
                                _yb = 0.0
                            try:
                                _probe_fn(_tid, _qv, _terms, _as_of, _yb)
                            except Exception:
                                continue
                    except Exception:
                        pass
            # derived from the frozen safe-action actions (exact 27/23 denominators), never from
            # retrieval emptiness. The injected adapter may supply only the other frozen gates
            # (official_link/http_resolution/cost); its core gates are recomputed/cross-checked
            # exactly (forgery => HOLD, never PASS).
            _dev_u_bools: list = []
            _dev_a_bools: list = []
            for _t in tasks:
                _role = _task_role(_t)
                _tid2 = _t.get("task_id") or _t.get("id")
                if _role == "unsupported":
                    _dev_u_bools.append(action_correct_for_role(actions_by_tid[_tid2], "unsupported"))
                elif _role == "ambiguous":
                    _dev_a_bools.append(action_correct_for_role(actions_by_tid[_tid2], "ambiguous"))
            owned_unsupported = evaluate_owned_unsupported(_dev_u_bools)
            owned_ambiguous = evaluate_owned_ambiguous(_dev_a_bools)
            safety_per_config = {}
            safety_evidence_per_config = {}
            for cfg in self.plan_data["configs"]:
                cid = cfg["config_id"]
                try:
                    # D-054: independent INTERNAL final-top-5 audit for this config over EVERY
                    # task regardless of visible ANSWER/ABSTAIN/CLARIFY, on the pinned date.
                    _tres = (all_config_results.get(cid) or {}).get("task_results", [])
                    _internal_top5: dict = {}
                    for _tr in _tres:
                        _items = _tr.get("retrieved_internal") or []
                        _internal_top5[_tr.get("task_id")] = list(_items[:5])
                    if pinned_context is not None:
                        _pe_gate, _pe_det = check_production_exclusion(
                            _internal_top5, biz_end_lookup, pinned_context["evaluation_as_of_date"], len(tasks), len(tasks) * 5
                        )
                    else:
                        _pe_gate, _pe_det = "HOLD", {"gate": "HOLD", "error": "missing pinned evaluation context"}
                    owned = {
                        "unsupported": owned_unsupported,
                        "ambiguous": owned_ambiguous,
                        "production_exclusion": {"gate": _pe_gate, **_pe_det},
                    }
                    # D-039: real safety measurement interfaces exist via safety_evidence_fn (FIRST dev only).
                    # SAME-STAGE pre-dev (no evidence fn): HOLD with pre_dev_no_real_measurement (no fabrication).
                    if self.safety_evidence_fn is not None:
                        ev = self.safety_evidence_fn({"config_id": cid, "config": cfg, "results": all_config_results.get(cid)})
                        need = ("unsupported", "ambiguous", "production_exclusion", "official_link", "http_resolution", "cost")
                        for k in need:
                            if k not in ev:
                                raise ValueError(f"safety evidence missing gate {k} (fail-closed)")
                            gv = ev[k] if isinstance(ev[k], str) else ev[k].get("gate")
                            if gv not in ("PASS", "NO-GO", "HOLD"):
                                raise ValueError(f"safety evidence gate {k} invalid {gv!r} (fail-closed)")
                        cross_check_owned_core(owned, ev)
                        _other = {}
                        for k in ("official_link", "http_resolution", "cost"):
                            _other[k] = ev[k] if isinstance(ev[k], str) else ev[k].get("gate")
                        _six = {
                            "unsupported": owned["unsupported"]["gate"],
                            "ambiguous": owned["ambiguous"]["gate"],
                            "production_exclusion": owned["production_exclusion"]["gate"],
                            **_other,
                        }
                        overall = "PASS" if all(v == "PASS" for v in _six.values()) else ("NO-GO" if any(v == "NO-GO" for v in _six.values()) else "HOLD")
                        # Selection map keeps gate strings; artifact map keeps structured dicts.
                        safety_per_config[cid] = {**_six, "gate": overall, "detail": "owned_core_cross_checked"}
                        safety_evidence_per_config[cid] = {
                            "unsupported": owned["unsupported"],
                            "ambiguous": owned["ambiguous"],
                            "production_exclusion": owned["production_exclusion"],
                            **{k: (ev[k] if isinstance(ev[k], dict) else {"gate": ev[k]}) for k in ("official_link", "http_resolution", "cost")},
                        }
                    else:
                        gate_u = "HOLD"
                        gate_ineligible = "HOLD"
                        gate_official = "HOLD"
                        gate_http = "HOLD"
                        cost_gate = "HOLD"
                        overall = "HOLD"
                        safety_per_config[cid] = {
                            "unsupported": gate_u,
                            "ambiguous": gate_u,
                            "production_exclusion": gate_ineligible,
                            "official_link": gate_official,
                            "http_resolution": gate_http,
                            "cost": cost_gate,
                            "gate": overall,
                            "detail": "pre_dev_no_real_measurement",
                        }
                        safety_evidence_per_config[cid] = {
                            k: {"gate": "HOLD", "detail": "pre_dev_no_real_measurement"} for k in ("unsupported", "ambiguous", "production_exclusion", "official_link", "http_resolution", "cost")
                        }
                except Exception as e:
                    safety_per_config[cid] = {
                        "unsupported": "HOLD",
                        "ambiguous": "HOLD",
                        "production_exclusion": "HOLD",
                        "official_link": "HOLD",
                        "http_resolution": "HOLD",
                        "cost": "HOLD",
                        "gate": "HOLD",
                        "error": str(e)[:200],
                    }
                    safety_evidence_per_config[cid] = {
                        k: {"gate": "HOLD", "error": str(e)[:200]} for k in ("unsupported", "ambiguous", "production_exclusion", "official_link", "http_resolution", "cost")
                    }

            latency_p95_per_config = None
            latency_evidence_per_config = None
            latency_gate_per_config = None
            if self.clock_fn is not None:
                try:
                    # D-039: D-003 production baseline paired latency. candidate-a-01 is FORBIDDEN as baseline
                    # (it manufactured latency PASS); baseline must come from d003_baseline_fn(task_id, query,
                    # D003_BASELINE descriptor, pinned evaluation context). D-054: the descriptor itself is
                    # unchanged; the pinned context travels separately (same date candidate + baseline).
                    if self.d003_baseline_fn is None:
                        raise RuntimeError("d003 baseline fn missing (fail-closed HOLD: no D-003 paired measurement)")
                    task_ids_sorted = sorted([t.get("task_id") or t.get("id") or f"task-{i:03d}" for i, t in enumerate(tasks)])
                    latencies = {}
                    latency_evidence_per_config = {}
                    latency_gate_per_config = {}
                    for cfg in self.plan_data["configs"]:
                        def _baseline_fn(tid):
                            task = next((tt for tt in tasks if (tt.get("task_id") or tt.get("id")) == tid), None)
                            if task is None:
                                raise ValueError(f"latency task id not found (fail-closed): {tid}")
                            q = task.get("query") or task.get("query_text") or ""
                            if not isinstance(q, str) or not q.strip():
                                raise ValueError(f"latency empty query (fail-closed): {tid}")
                            self.d003_baseline_fn(tid, q, D003_BASELINE, pinned_context)
                        def _candidate_fn(tid, _cfg=cfg):
                            task = next((tt for tt in tasks if (tt.get("task_id") or tt.get("id")) == tid), None)
                            if task is None:
                                raise ValueError(f"latency task id not found (fail-closed): {tid}")
                            q = task.get("query") or task.get("query_text") or ""
                            if not isinstance(q, str) or not q.strip():
                                raise ValueError(f"latency empty query (fail-closed): {tid}")
                            self._retrieve_for_query(q, retrieval_policies, _cfg)
                        res = measure_paired_latency(task_ids_sorted, _baseline_fn, _candidate_fn, clock_fn=self.clock_fn, warmup_n=30)
                        cand_p95 = res.get("candidate", {}).get("p95") if isinstance(res.get("candidate"), dict) else res.get("candidate_p95")
                        # SAME-STAGE fail-closed: no fabricated default; missing p95 stays None -> selection HOLD.
                        latencies[cfg["config_id"]] = cand_p95 if cand_p95 is not None else None
                        # D-041: full paired evidence per config (n/warmup/baseline+candidate p50/p95/p99+gate) for canonical result.
                        latency_evidence_per_config[cfg["config_id"]] = res
                        latency_gate_per_config[cfg["config_id"]] = res.get("gate") if isinstance(res, dict) else None
                    latency_p95_per_config = latencies
                except Exception:
                    latency_p95_per_config = None
                    latency_evidence_per_config = None
                    latency_gate_per_config = None
            selection = select_candidate(per_config_metrics, safety_per_config, latency_p95_per_config, latency_gate_per_config)
            if selection["chosen"]:
                chosen_metrics = next(m for m in per_config_metrics if m["config_id"] == selection["chosen"])
                union_r100 = chosen_metrics.get("union_oracle_R100", 0.0)
                cand_success = chosen_metrics.get("success_at_5", 0.0)
                b_gate = candidate_b_gate(union_r100, cand_success)
            else:
                # D-039: no finalist => B not_evaluated (same-finalist evidence only; max-of-all manufactured evaluation).
                b_gate = {"admitted": False, "instantiated": False, "status": "not_evaluated", "reason": "no finalist (fail-closed: B evaluated on chosen finalist only)", "union_oracle_recall_100": None, "candidate_a_success_5": None, "headroom_pp": None}
            git_head = _get_git_head()
            git_dirty = _get_git_dirty()
            plan_sha = _sha256_file(CANDIDATE_PLAN_PATH if CANDIDATE_PLAN_PATH.exists() else REPO_ROOT / "eval" / "retrieval_v3" / "candidate-plan" / "candidate-plan-v4.json")
            prereg_sha = _sha256_file(PREREG_PATH)
            # D-042: corpus_prov gathered pre-run (fail-closed there); reuse here without re-calling.
            set_prov = None
            if set_sha:
                set_prov = {"set_role": set_role, "set_sha": set_sha, "n": len(tasks), "headline_n": len(headline_tasks)}

            provenance = {
                "candidate_plan_sha256": plan_sha.lower(),
                "prereg_sha256": prereg_sha.lower(),
                "git_head": git_head.lower(),
                "git_dirty": git_dirty,
                "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat().replace("+00:00", "Z"),
            }
            audit_head_val = run_start_event.get("event_hash") if run_start_event else None
            result = build_result_skeleton(
                per_config_metrics=per_config_metrics,
                selection=selection,
                candidate_b_gate=b_gate,
                provenance=provenance,
                git_head=git_head,
                git_dirty=git_dirty,
                corpus_provenance=corpus_prov,
                set_provenance=set_prov,
                audit_head=audit_head_val,
                safety_per_config=safety_evidence_per_config,
                latency_per_config=latency_evidence_per_config,
                # D-054: pinned evaluation context in the canonical result (structured, no new gate).
                evaluation_context=pinned_context,
            )
            # D-042: canonical self-validation before publish (fail-closed even with output None; triggers failure close).
            if is_canonical:
                validate_complete_result(result)

            if output_path:
                atomic_write_result(result, output_path)

            if need_audit_close:
                try:
                    run_end_event = audit.append_event(
                        str(audit_log),
                        action="run_end",
                        set_role=set_role,
                        set_sha=set_sha,
                        candidate_id="v3-candidate-dev-v1",
                        session_id=session_id,
                        # D-054: pinned context on the existing run event (no new gate/action).
                        db_session_timezone=(pinned_context or {}).get("db_session_timezone"),
                        evaluation_as_of_date=(pinned_context or {}).get("evaluation_as_of_date"),
                    )
                    run_end_appended = True
                except Exception as e:
                    if output_path:
                        try:
                            out_abs = (REPO_ROOT / output_path).resolve() if not pathlib.Path(output_path).is_absolute() else pathlib.Path(output_path).resolve()
                            if out_abs.exists():
                                out_abs.unlink()
                        except Exception:
                            pass
                    # D-040: run_end failure after verified grant must still close grant exactly once.
                    if is_canonical and grant_verified and not grant_closed:
                        try:
                            _close_grant("failure")
                        except Exception as ce:
                            raise RuntimeError(f"grant close on run_end failure failed (fail-closed): {ce}") from e
                    raise RuntimeError(f"audit run_end failed (fail-closed, result removed): {e}") from e

            # D-040: success path closes verified grant exactly once (no close ever on failed verification).
            if is_canonical and grant_verified and not grant_closed and not grant_close_tried:
                try:
                    _close_grant("success")
                except Exception as e:
                    if output_path:
                        try:
                            out_abs = (REPO_ROOT / output_path).resolve() if not pathlib.Path(output_path).is_absolute() else pathlib.Path(output_path).resolve()
                            if out_abs.exists():
                                out_abs.unlink()
                        except Exception:
                            pass
                    raise RuntimeError(f"grant close on success failed (fail-closed, result removed): {e}") from e

            return result
        except Exception as e:
            # Execution-lifecycle: ensure audit closure even on failure — append run_end before cleanup (fail-closed, preserves chain).
            # D-040: plus exact-one grant failure close when verified (loader/pre-run/execution paths); never double-close.
            if need_audit_close and not run_end_appended:
                try:
                    # Attempt to close audit chain with run_end; if this fails, still clean up output and surface original error
                    audit.append_event(
                        str(audit_log),
                        action="run_end",
                        set_role=set_role,
                        set_sha=set_sha,
                        candidate_id="v3-candidate-dev-v1",
                        session_id=session_id,
                        # D-054: pinned context on the existing run event (no new gate/action).
                        db_session_timezone=(pinned_context or {}).get("db_session_timezone"),
                        evaluation_as_of_date=(pinned_context or {}).get("evaluation_as_of_date"),
                    )
                    run_end_appended = True
                except Exception as audit_e:
                    # If audit close itself fails, ensure output removed and raise with audit context
                    if output_path:
                        try:
                            out_abs = (REPO_ROOT / output_path).resolve() if not pathlib.Path(output_path).is_absolute() else pathlib.Path(output_path).resolve()
                            if out_abs.exists():
                                out_abs.unlink()
                        except Exception:
                            pass
                    # Still attempt grant failure close once (exact-one) before surfacing.
                    if is_canonical and grant_verified and not grant_closed and not grant_close_tried:
                        try:
                            _close_grant("failure")
                        except Exception:
                            pass
                    raise RuntimeError(f"audit run_end on failure failed (fail-closed): {audit_e}") from e
                # Audit close succeeded — now grant failure close once, then clean up output if present
                if is_canonical and grant_verified and not grant_closed and not grant_close_tried:
                    try:
                        _close_grant("failure")
                    except Exception as ce:
                        if output_path:
                            try:
                                out_abs = (REPO_ROOT / output_path).resolve() if not pathlib.Path(output_path).is_absolute() else pathlib.Path(output_path).resolve()
                                if out_abs.exists():
                                    out_abs.unlink()
                            except Exception:
                                pass
                        raise RuntimeError(f"grant close on execution failure failed (fail-closed): {ce}") from e
                if output_path:
                    try:
                        out_abs = (REPO_ROOT / output_path).resolve() if not pathlib.Path(output_path).is_absolute() else pathlib.Path(output_path).resolve()
                        if out_abs.exists():
                            out_abs.unlink()
                    except Exception:
                        pass
            elif is_canonical and grant_verified and not grant_closed and not grant_close_tried:
                # Failure before run_start (execution never started; no run_end) still closes grant once.
                try:
                    _close_grant("failure")
                except Exception as ce:
                    raise RuntimeError(f"grant close on execution failure failed (fail-closed): {ce}") from e
            raise
def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Retrieval v3 Candidate A runner (pure/mock, no real DB/model)")
    p.add_argument("--tasks", type=str, help="path to tasks jsonl (fake for tests)")
    p.add_argument("--policies", type=str, help="path to policies json (fake for tests)")
    p.add_argument("--output", type=str, default=str(CANONICAL_DEV_OUTPUT_REL), help="output result path")
    p.add_argument("--audit-log", type=str, default=str(DEFAULT_AUDIT_LOG), help="audit log path")
    p.add_argument("--session-id", type=str, required=True, help="session id")
    p.add_argument("--set-role", type=str, choices=["dev", "holdout", "none"], default="dev")
    p.add_argument("--set-sha", type=str, help="64-hex set SHA")
    p.add_argument("--expected-event-hash", type=str, help="grant token")
    p.add_argument("--skip-audit", action="store_true", help="skip audit for pure tests")
    p.add_argument("--materialized-evalset", type=str, default=None, help="explicit already-authorized materialized dev evalset path (FIRST-dev only; unset in D-056, loader stays fail-closed)")
    p.add_argument("--materialized-evalset-base", type=str, default=None, help="explicit already-authorized external materialized base directory for the dev evalset file (FIRST-dev only; runtime-supplied, no IO at parse; loader confines the file inside this base after grant; unset defaults to repo root fail-closed)")
    return p.parse_args(argv)

def _is_canonical_cli(args) -> bool:
    """Canonical-dev CLI iff dev role with set_sha (exact grant lifecycle + canonical output)."""
    return getattr(args, "set_role", "none") == "dev" and getattr(args, "set_sha", None) is not None

def main_mock(args):
    """Mock CLI (non-canonical only): fakes + --tasks/--policies/--skip-audit allowed. No real IO."""
    if _is_canonical_cli(args):
        raise ValueError("mock CLI forbids canonical dev (set_sha present; use canonical-dev path, fail-closed)")
    if getattr(args, "materialized_evalset", None):
        raise ValueError("mock CLI forbids --materialized-evalset (FIRST-dev canonical only, fail-closed)")
    if getattr(args, "materialized_evalset_base", None):
        raise ValueError("mock CLI forbids --materialized-evalset-base (FIRST-dev canonical only, fail-closed)")
    plan = load_candidate_plan_or_fail()
    def fake_embedding(q):
        import hashlib, random
        h = hashlib.sha256(q.encode()).digest()
        rnd = random.Random(int.from_bytes(h[:4], "little"))
        vec = [rnd.uniform(-1, 1) for _ in range(768)]
        norm = (sum(x*x for x in vec) ** 0.5) or 1
        return [x / norm for x in vec]

    def fake_policies():
        if args.policies:
            pp = pathlib.Path(args.policies)
            if pp.exists():
                return json.loads(pp.read_text(encoding="utf-8"))
        return []

    def fake_tasks(set_role, set_sha):
        if args.tasks:
            pp = pathlib.Path(args.tasks)
            if pp.exists():
                lines = pp.read_text(encoding="utf-8").strip().splitlines()
                return [json.loads(l) for l in lines if l.strip()]
        return []

    runner = Runner(
        candidate_plan=plan,
        embedding_fn=fake_embedding,
        db_policy_loader=fake_policies,
        protected_set_loader=fake_tasks,
        audit_log_path=args.audit_log,
        adapter_kind="mock",
    )
    tasks = []
    if args.tasks:
        pp = pathlib.Path(args.tasks)
        if pp.exists():
            tasks = [json.loads(l) for l in pp.read_text(encoding="utf-8").splitlines() if l.strip()]
    policies = fake_policies()
    if not policies:
        import random, hashlib
        policies = []
        for i in range(5):
            vec = fake_embedding(f"policy {i}")
            policies.append({
                "id": i+1,
                "source": "youth" if i%2==0 else "gov24",
                "source_id": f"p{i}",
                "title": f"청년 지원 정책 {i}",
                "support_content": "지원 내용",
                "summary": "",
                "keywords": "",
                "add_qualify": "",
                "income_etc": "",
                "apply_method": "",
                "org": "고용노동부" if i%2==0 else "문화체육관광부",
                "chunks": [{"embedding": vec, "chunk_index": 0, "id": 100+i}],
            })

    result = runner.run_dev_evaluation(
        tasks=tasks or [{"task_id": f"t{i}", "query": f"청년 지원 {i}", "golds": [{"source": "youth", "source_id": "p0", "grade": 2}], "stratum": "natural_needs", "location_bearing": False} for i in range(5)],
        policies=policies,
        session_id=args.session_id,
        set_role=args.set_role,
        set_sha=args.set_sha,
        audit_log=args.audit_log,
        expected_event_hash=args.expected_event_hash,
        output_path=args.output,
        skip_audit=args.skip_audit,
    )
    print(json.dumps({"chosen": result["selection"]["chosen"], "eligible": result["selection"]["eligible"]}, ensure_ascii=False))
    return 0

def main_canonical_dev(args):
    """Canonical-dev CLI: forbids --tasks/--policies/--skip-audit/fakes; lazy real adapters; exact canonical output."""
    if args.tasks:
        raise ValueError("canonical-dev forbids --tasks (protected loader after grant only, fail-closed)")
    if args.policies:
        raise ValueError("canonical-dev forbids --policies (real policy adapter only, fail-closed)")
    if args.skip_audit:
        raise ValueError("canonical-dev forbids --skip-audit (audit required, fail-closed)")
    if not _is_canonical_cli(args):
        raise ValueError("canonical-dev requires --set-role dev with --set-sha (fail-closed)")
    # Strict canonical output before any IO/grant (fail-closed, no close needed pre-verification).
    validate_output_path(args.output, strict_canonical=True)
    if not _is_canonical_output_path(args.output):
        raise ValueError(f"canonical-dev must write exact canonical output (fail-closed): got {args.output!r}")
    plan = load_candidate_plan_or_fail()
    # D-056: ONE governing real evaluation session (no IO at construction).
    # All eight real surfaces bind to it; the corpus is loaded by the runner
    # AFTER capture on this same session (no pre-capture policy DB load).
    # D-041/D-054 presence rules are enforced by run_dev_evaluation pre-grant.
    session = RealEvaluationSession()
    try:
        adapters = build_real_adapters(
            session,
            materialized_path=getattr(args, "materialized_evalset", None),
            evalset_base=getattr(args, "materialized_evalset_base", None),
        )
        runner = Runner(
            candidate_plan=plan,
            embedding_fn=adapters["embedding_fn"],
            db_policy_loader=adapters["policy_loader"],
            protected_set_loader=adapters["protected_loader"],
            audit_log_path=args.audit_log,
            adapter_kind="real",
            safety_evidence_fn=adapters["safety_evidence_fn"],
            d003_baseline_fn=adapters["d003_baseline_fn"],
            clock_fn=adapters["clock_fn"],
            corpus_provenance_fn=adapters["corpus_provenance_fn"],
            evaluation_context_exec_fn=adapters["evaluation_context_fn"],
            evaluation_session=session,
        )
        result = runner.run_dev_evaluation(
            tasks=[],
            policies=[],
            session_id=args.session_id,
            set_role=args.set_role,
            set_sha=args.set_sha,
            audit_log=args.audit_log,
            expected_event_hash=args.expected_event_hash,
            output_path=args.output,
            skip_audit=False,
        )
    finally:
        if not session.is_closed:
            session.close()
    print(json.dumps({"chosen": result["selection"]["chosen"], "eligible": result["selection"]["eligible"]}, ensure_ascii=False))
    return 0

def main(argv=None):
    args = parse_args(argv)
    # D-040: split mock CLI from canonical-dev (canonical forbids fakes; lazy real adapters).
    if _is_canonical_cli(args):
        return main_canonical_dev(args)
    validate_output_path(args.output, strict_canonical=False)
    return main_mock(args)

if __name__ == "__main__":
    sys.exit(main())
