"""Selection — frozen rule: safety + Success>=85% then ordering. Fail-closed on missing gates/latency. Remove implicit PASS."""

from __future__ import annotations
from typing import Any
import math

# Expected gates per prereg §9 and candidate-plan selection_rule — must all be present and PASS
EXPECTED_SAFETY_GATES = {"unsupported", "ambiguous", "ineligible_expired", "official_link", "http_resolution", "cost"}

def _safety_passes(safety_report: dict) -> bool:
    """
    safety_report: dict with keys for each gate: unsupported, ambiguous, ineligible_expired, official_link, cost, http_resolution etc each with PASS/NO-GO/HOLD
    Dev safety must PASS (HOLD is fail for selection). Per prereg: missing measurement => HOLD => not PASS => ineligible.
    So require all expected gates PASS and any present gate PASS. Missing expected gate => HOLD => not PASS.
    Returns False if missing safety or any gate not PASS.
    """
    if not safety_report or not isinstance(safety_report, dict):
        return False
    for eg in EXPECTED_SAFETY_GATES:
        if eg not in safety_report:
            return False
        v = safety_report[eg]
        gate = v if isinstance(v, str) else v.get("gate") or v.get("result") or v.get("status")
        if gate != "PASS":
            return False
    for k, v in safety_report.items():
        if k == "gate":
            gv = v if isinstance(v, str) else v.get("gate") or v.get("result") or v.get("status")
            if gv != "PASS":
                return False
            continue
        gate = v if isinstance(v, str) else v.get("gate") or v.get("result") or v.get("status")
        if gate is not None and gate != "PASS":
            return False
    return True

def _is_finite_latency(val) -> bool:
    try:
        f = float(val)
        return math.isfinite(f)
    except Exception:
        return False

def select_candidate(
    per_config_metrics: list[dict],
    safety_per_config: dict[str, dict] | None = None,
    latency_p95_per_config: dict[str, float] | None = None,
) -> dict:
    """
    per_config_metrics: list of {config_id, success_at_5, ndcg_at_5, mrr_at_10, ...}
    safety_per_config: map config_id -> safety_report dict ; missing safety map => fail-closed no eligible
    latency_p95_per_config: map config_id -> p95 ms ; missing latency map => fail-closed no eligible; non-finite (inf/nan) => ineligible for that config
    Returns {eligible: [...], chosen: config_id or None, ordering: [...], reason: str}
    Frozen rule: eligibility requires dev safety gates PASS AND Success@5 >=0.85 on dev headline 130
    Ordering: Success@5 desc -> NDCG@5 desc -> MRR@10 desc -> paired p95 asc -> lexicographic config_id asc
    """
    # Fail-closed: missing safety map OR missing latency map => no eligible, always HOLD
    if safety_per_config is None or latency_p95_per_config is None:
        return {
            "eligible": [],
            "eligible_details": [],
            "chosen": None,
            "ordering": "Success@5 desc -> NDCG@5 desc -> MRR@10 desc -> paired p95 asc -> lexicographic config_id asc",
            "reason": "no eligible (missing safety or latency map fail-closed HOLD)",
        }
    eligible = []
    for m in per_config_metrics:
        cid = m["config_id"]
        success = m.get("success_at_5", 0.0)
        # safety fail-closed
        if cid not in safety_per_config:
            continue
        rep = safety_per_config.get(cid, {})
        if not _safety_passes(rep):
            continue
        # latency fail-closed: missing entry or non-finite => HOLD => ineligible
        if cid not in latency_p95_per_config:
            continue
        p95_val = latency_p95_per_config[cid]
        if p95_val is None or not _is_finite_latency(p95_val):
            continue
        if success >= 0.85:
            eligible.append(m)

    def sort_key(m):
        p95 = float("inf")
        val = latency_p95_per_config.get(m["config_id"])
        if val is not None and _is_finite_latency(val):
            try:
                p95 = float(val)
            except Exception:
                p95 = float("inf")
        return (-m.get("success_at_5", 0), -m.get("ndcg_at_5", 0), -m.get("mrr_at_10", 0), p95, m["config_id"])

    eligible_sorted = sorted(eligible, key=sort_key)
    chosen = eligible_sorted[0]["config_id"] if eligible_sorted else None
    reason = "selected" if chosen else "no eligible (safety+Success>=85% fail or latency HOLD)"
    return {
        "eligible": [e["config_id"] for e in eligible_sorted],
        "eligible_details": eligible_sorted,
        "chosen": chosen,
        "ordering": "Success@5 desc -> NDCG@5 desc -> MRR@10 desc -> paired p95 asc -> lexicographic config_id asc",
        "reason": reason,
    }

def candidate_b_gate(
    union_oracle_recall_100: float,
    candidate_a_success_5: float,
) -> dict:
    """
    Mechanical B admission diagnostic: union oracle R@100>=97% AND headroom >=5.0pp on headline 130 only.
    Headroom = R@100 - Success@5 (pp units, 0-100)
    Returns {admitted: bool, headroom_pp: float, union_recall: float, reason}
    Candidate B MUST NOT be instantiated regardless; this is diagnostic only.
    Headline 130 scope is enforced by caller (runner) — this function is pure diagnostic on supplied metrics.
    """
    union_pp = union_oracle_recall_100 * 100 if union_oracle_recall_100 <= 1.0 else union_oracle_recall_100
    cand_pp = candidate_a_success_5 * 100 if candidate_a_success_5 <= 1.0 else candidate_a_success_5
    headroom = union_pp - cand_pp
    admitted = (union_pp >= 97.0) and (headroom >= 5.0)
    return {
        "union_oracle_recall_100": union_oracle_recall_100,
        "candidate_a_success_5": candidate_a_success_5,
        "union_pp": union_pp,
        "candidate_pp": cand_pp,
        "headroom_pp": headroom,
        "admitted": admitted,
        "instantiated": False,
        "reason": "diagnostic only; B forbidden unless admitted and separate future gate" if not admitted else "gate passed: B may be considered in future stage (not instantiated now)",
    }
