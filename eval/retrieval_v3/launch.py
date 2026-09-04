"""Canonical FIRST-dev launch orchestrator — narrow preflight + ordered launch (D-065).

SAME-STAGE narrow implementation in the pre-result launch-contract stage.
No frozen contract/threshold/ranking/audit semantic change; only centralizes
the existing canonical launch boundary so the CLI cannot bypass it:

  preflight (no DB, no protected plaintext, no append)
    frozen file SHAs (plan-v4 / prereg / link-V2 / cost-V1, non-protected
    docs only) + candidate-plan 18-config/policy-ref validation
    + arg shape (dev-only, 64-hex set_sha, non-empty session/materialized
    shape, exact canonical output) + audit chain integrity + one-shot
    zero prior run_start + canonical output absent
  ordered launch (injected factories, no fakes in signature)
    session_factory -> adapter_builder -> runner_factory -> run

Preflight never stats/resolves/reads the materialized protected evalset;
existence/content/SHA checks stay post-grant inside the protected loader.
No DB/model/embedding/HTTP/latency execution here; tests inject fakes.
No IO at import. FIRST dev remains BLOCKED pending Web review.
"""

from __future__ import annotations

import hashlib
import os
import pathlib
import re

from . import audit
from .candidate_registry import (
    EXPECTED_PLAN_ID,
    EXPECTED_PREREG_SHA,
    EXPECTED_SHA,
    load_and_validate,
)
from .paths import (
    CANONICAL_DEV_OUTPUT_ALT,
    CANONICAL_DEV_OUTPUT_REL,
    REPO_ROOT,
    validate_output_path,
)

FROZEN_PREREG_SHA = "7842018613d66aa4570f4db2f8ae5a698ceb46757995a6b7e26873177b36160e"
FROZEN_PLAN_SHA = "a25d9c482094696ff7a438593979813ac568c91a977a2543a50618ca4f5177d6"
FROZEN_LINK_V2_SHA = "f028ce4697f1a19e8d37e9048f6d7cd07d87c35ad68478d0efa968b7c62a7e71"
FROZEN_COST_V1_SHA = "5891b0bab0621da71499c5c2c6a21a6ac6692bd3ee94d6cb5342adc480958323"

PREREG_REL = pathlib.Path("docs/RETRIEVAL_V3_PREREG.md")
PLAN_REL = pathlib.Path("eval/retrieval-v3/candidate-plan/candidate-plan-v4.json")
PLAN_ALT = pathlib.Path("eval/retrieval_v3/candidate-plan/candidate-plan-v4.json")
LINK_V2_REL = pathlib.Path("docs/RETRIEVAL_V3_LINK_PROVENANCE_SUPERSESSION_V2.md")
COST_V1_REL = pathlib.Path("docs/RETRIEVAL_V3_COST_MEASUREMENT_V1.md")

DEFAULT_AUDIT_LOG = REPO_ROOT / "eval" / "retrieval-v3" / "audit" / "events.jsonl"

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_BATCH_ID = "v3-candidate-dev-v1"


def _sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest().lower()


def _resolve_plan_path(repo_root: pathlib.Path) -> pathlib.Path:
    primary = pathlib.Path(repo_root) / PLAN_REL
    if primary.exists():
        return primary
    alt = pathlib.Path(repo_root) / PLAN_ALT
    if alt.exists():
        return alt
    raise FileNotFoundError(f"candidate plan not found: {primary}")


def verify_frozen_files(repo_root: str | pathlib.Path | None = None) -> dict:
    """Verify non-protected frozen file SHAs + candidate-plan validation. No DB/protected IO."""
    base = pathlib.Path(repo_root) if repo_root is not None else REPO_ROOT
    if EXPECTED_SHA.lower() != FROZEN_PLAN_SHA.lower():
        raise ValueError("launch pin drift: candidate_registry.EXPECTED_SHA != FROZEN_PLAN_SHA (fail-closed)")
    if EXPECTED_PREREG_SHA.lower() != FROZEN_PREREG_SHA.lower():
        raise ValueError("launch pin drift: candidate_registry.EXPECTED_PREREG_SHA != FROZEN_PREREG_SHA (fail-closed)")
    targets = (
        (PREREG_REL, FROZEN_PREREG_SHA),
        (LINK_V2_REL, FROZEN_LINK_V2_SHA),
        (COST_V1_REL, FROZEN_COST_V1_SHA),
    )
    shas: dict[str, str] = {}
    for rel, expected in targets:
        p = base / rel
        if not p.exists():
            raise FileNotFoundError(f"frozen file missing: {rel.as_posix()} (fail-closed)")
        got = _sha256_file(p)
        if got != expected.lower():
            raise ValueError(
                f"frozen file SHA mismatch: {rel.as_posix()} got {got[:8]}... expected {expected[:8]}... (fail-closed)"
            )
        shas[rel.as_posix()] = got
    plan_path = _resolve_plan_path(base)
    plan_raw_sha = _sha256_file(plan_path)
    if plan_raw_sha != FROZEN_PLAN_SHA.lower():
        raise ValueError(
            f"candidate plan SHA mismatch: got {plan_raw_sha[:8]}... expected {FROZEN_PLAN_SHA[:8]}... (fail-closed)"
        )
    shas["candidate-plan-v4"] = plan_raw_sha
    plan_data = load_and_validate(str(plan_path))
    if plan_data.get("plan_id") != EXPECTED_PLAN_ID:
        raise ValueError("candidate plan identity drift (fail-closed)")
    return {"plan": plan_data, "shas": shas, "plan_path": str(plan_path)}


def _is_canonical_output(output_path: str | pathlib.Path) -> bool:
    try:
        out_posix = pathlib.PurePath(str(output_path)).as_posix()
        return out_posix in (
            pathlib.PurePath(str(CANONICAL_DEV_OUTPUT_REL)).as_posix(),
            pathlib.PurePath(str(CANONICAL_DEV_OUTPUT_ALT)).as_posix(),
        )
    except Exception:
        return False


def validate_launch_args(
    *,
    session_id: object,
    set_role: object,
    set_sha: object,
    materialized_path: object,
    evalset_base: object,
    output_path: object,
    audit_log: object,
    expected_event_hash: object = None,
) -> dict:
    """Pure shape validation. No FS stat/resolve/read of the protected file, no DB."""
    if set_role != "dev":
        raise ValueError(f"canonical launch forbids role {set_role!r} (dev only, fail-closed)")
    if not isinstance(set_sha, str) or not _HEX64_RE.match(set_sha.lower()):
        raise ValueError("canonical launch requires 64-hex set_sha (fail-closed)")
    if not isinstance(session_id, str) or not session_id.strip():
        raise ValueError("canonical launch requires non-empty session_id (fail-closed)")
    if not isinstance(materialized_path, (str, pathlib.Path)) or not str(materialized_path).strip():
        raise ValueError("canonical launch requires non-empty materialized_path shape (fail-closed, no IO)")
    if not isinstance(evalset_base, (str, pathlib.Path)) or not str(evalset_base).strip():
        raise ValueError("canonical launch requires non-empty evalset_base shape (fail-closed, no IO)")
    if not isinstance(audit_log, (str, pathlib.Path)) or not str(audit_log).strip():
        raise ValueError("canonical launch requires non-empty audit_log shape (fail-closed)")
    if expected_event_hash is not None:
        if not isinstance(expected_event_hash, str) or not _HEX64_RE.match(expected_event_hash.lower()):
            raise ValueError("expected_event_hash must be 64-hex when supplied (fail-closed)")
    validate_output_path(output_path, strict_canonical=True)
    if not _is_canonical_output(output_path):
        raise ValueError(f"canonical launch must write exact canonical output (fail-closed): got {output_path!r}")
    return {
        "session_id": session_id,
        "set_role": set_role,
        "set_sha": str(set_sha).lower(),
    }


def preflight_canonical_launch(
    *,
    session_id: str,
    set_role: str = "dev",
    set_sha: str,
    materialized_path: str | pathlib.Path,
    evalset_base: str | pathlib.Path,
    output_path: str | pathlib.Path,
    audit_log: str | pathlib.Path,
    expected_event_hash: str | None = None,
    repo_root: str | pathlib.Path | None = None,
    audit_reader=None,
    output_exists_fn=None,
) -> dict:
    """Fail-fast preflight before any DB capture/grant/run_start. No protected IO, no append.

    Order: arg shape -> frozen files -> audit chain + one-shot -> output absent.
    """
    validated = validate_launch_args(
        session_id=session_id,
        set_role=set_role,
        set_sha=set_sha,
        materialized_path=materialized_path,
        evalset_base=evalset_base,
        output_path=output_path,
        audit_log=audit_log,
        expected_event_hash=expected_event_hash,
    )
    frozen = verify_frozen_files(repo_root)
    reader = audit_reader if audit_reader is not None else audit.read_and_verify_chain
    try:
        events = reader(str(audit_log))
    except Exception as e:
        raise RuntimeError(f"launch preflight audit chain unreadable (fail-closed): {type(e).__name__}") from e
    if not isinstance(events, list):
        raise RuntimeError("launch preflight audit reader must return list (fail-closed)")
    want_sha = validated["set_sha"]
    prior = [
        e
        for e in events
        if isinstance(e, dict)
        and e.get("action") == "run_start"
        and str(e.get("set_role") or "") == "dev"
        and str(e.get("set_sha") or "").lower() == want_sha
    ]
    if len(prior) >= 1:
        raise RuntimeError(
            f"launch preflight rerun detected: run_start count for dev/{want_sha[:8]}... is {len(prior)} (expected 0, fail-closed)"
        )
    if output_exists_fn is not None:
        try:
            exists = bool(output_exists_fn(str(output_path)))
        except Exception as e:
            raise RuntimeError(f"launch preflight output check failed (fail-closed): {type(e).__name__}") from e
    else:
        try:
            probe = pathlib.Path(str(output_path))
            abs_probe = probe if probe.is_absolute() else (REPO_ROOT / probe)
            exists = abs_probe.exists()
        except Exception as e:
            raise RuntimeError(f"launch preflight output check failed (fail-closed): {type(e).__name__}") from e
    if exists:
        raise FileExistsError(f"launch preflight output already exists: {output_path} — rerun guard")
    return {"args": validated, "frozen": frozen["shas"], "audit_events": len(events)}


def launch_canonical_dev(
    *,
    session_id: str,
    set_role: str = "dev",
    set_sha: str,
    materialized_path: str | pathlib.Path,
    evalset_base: str | pathlib.Path,
    output_path: str | pathlib.Path,
    audit_log: str | pathlib.Path,
    expected_event_hash: str | None = None,
    session_factory,
    adapter_builder,
    runner_factory,
    repo_root: str | pathlib.Path | None = None,
    audit_reader=None,
    output_exists_fn=None,
) -> dict:
    """Ordered canonical launch with exact-once session ownership. Injected factories only.

    No tasks/policies/skip_audit parameters exist by construction (fakes forbidden).
    Preflight runs before session creation (no DB on preflight failure).
    Session closes exactly once on every post-creation exit.
    """
    if not callable(session_factory):
        raise ValueError("launch requires session_factory callable (fail-closed)")
    if not callable(adapter_builder):
        raise ValueError("launch requires adapter_builder callable (fail-closed)")
    if not callable(runner_factory):
        raise ValueError("launch requires runner_factory callable (fail-closed)")
    preflight = preflight_canonical_launch(
        session_id=session_id,
        set_role=set_role,
        set_sha=set_sha,
        materialized_path=materialized_path,
        evalset_base=evalset_base,
        output_path=output_path,
        audit_log=audit_log,
        expected_event_hash=expected_event_hash,
        repo_root=repo_root,
        audit_reader=audit_reader,
        output_exists_fn=output_exists_fn,
    )
    try:
        session = session_factory()
    except Exception as e:
        raise RuntimeError(f"launch session creation failed (fail-closed): {type(e).__name__}") from e
    if session is None:
        raise RuntimeError("launch session factory returned None (fail-closed)")
    try:
        try:
            adapters = adapter_builder(session, materialized_path, evalset_base)
        except Exception as e:
            raise RuntimeError(f"launch adapter build failed (fail-closed): {type(e).__name__}") from e
        try:
            runner = runner_factory(adapters, session)
        except Exception as e:
            raise RuntimeError(f"launch runner construction failed (fail-closed): {type(e).__name__}") from e
        run_fn = getattr(runner, "run_dev_evaluation", None)
        if not callable(run_fn):
            raise ValueError("launch runner must expose run_dev_evaluation (fail-closed)")
        result = run_fn(
            tasks=[],
            policies=[],
            session_id=session_id,
            set_role="dev",
            set_sha=preflight["args"]["set_sha"],
            audit_log=audit_log,
            expected_event_hash=expected_event_hash,
            output_path=output_path,
            skip_audit=False,
        )
        return result
    finally:
        try:
            closed = bool(getattr(session, "is_closed", False))
        except Exception:
            closed = False
        if not closed:
            try:
                session.close()
            except Exception as e:
                raise RuntimeError(f"launch session close failed (fail-closed): {type(e).__name__}") from None


def launch_canonical_dev_real(
    *,
    session_id: str,
    set_sha: str,
    materialized_path: str | pathlib.Path,
    evalset_base: str | pathlib.Path,
    output_path: str | pathlib.Path = CANONICAL_DEV_OUTPUT_REL,
    audit_log: str | pathlib.Path = DEFAULT_AUDIT_LOG,
    expected_event_hash: str | None = None,
) -> dict:
    """Real wiring entry point (lazy imports, no IO at import). Delegates to launch_canonical_dev."""
    from .real_adapters import RealEvaluationSession, build_real_adapters

    from .runner import Runner

    def _session_factory():
        return RealEvaluationSession()

    def _adapter_builder(session, mat_path, base):
        return build_real_adapters(session, materialized_path=mat_path, evalset_base=base)

    def _runner_factory(adapters, session):
        return Runner(
            candidate_plan=verify_frozen_files()["plan"],
            embedding_fn=adapters["embedding_fn"],
            db_policy_loader=adapters["policy_loader"],
            protected_set_loader=adapters["protected_loader"],
            audit_log_path=audit_log,
            adapter_kind="real",
            safety_evidence_fn=adapters["safety_evidence_fn"],
            d003_baseline_fn=adapters["d003_baseline_fn"],
            clock_fn=adapters["clock_fn"],
            corpus_provenance_fn=adapters["corpus_provenance_fn"],
            evaluation_context_exec_fn=adapters["evaluation_context_fn"],
            evaluation_session=session,
        )

    _ = os.name
    return launch_canonical_dev(
        session_id=session_id,
        set_role="dev",
        set_sha=set_sha,
        materialized_path=materialized_path,
        evalset_base=evalset_base,
        output_path=output_path,
        audit_log=audit_log,
        expected_event_hash=expected_event_hash,
        session_factory=_session_factory,
        adapter_builder=_adapter_builder,
        runner_factory=_runner_factory,
    )
