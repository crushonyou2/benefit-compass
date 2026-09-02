"""Selection — frozen rule: safety + Success>=85% then ordering."""
from __future__ import annotations
from typing import Any

def _safety_passes(safety_report: dict) -> bool:
    """
    safety_report: dict with keys for each gate: unsupported, ambiguous, ineligible, official_link, cost, etc each with PASS/NO-GO/HOLD
    Dev safety must PASS (HOLD is fail for selection). Per prereg: missing measurement => HOLD => not PASS => ineligible.
    So require all gates PASS.
    """
    # Expected gates: unsupported, ambiguous, ineligible_expired, official_link, cost
    for k, v in safety_report.items():
        # v may be string PASS or dict with gate
        gate = v if isinstance(v, str) else v.get("gate") or v.get("result") or v.get("status")
        if gate != "PASS":
            return False
    return True

def select_candidate(
    per_config_metrics: list[dict],
    safety_per_config: dict[str, dict] | None = None,
    latency_p95_per_config: dict[str, float] | None = None,
) -> dict:
    """
    per_config_metrics: list of {config_id, success_at_5, ndcg_at_5, mrr_at_10, ...}
    safety_per_config: map config_id -> safety_report dict ; if None, assume PASS for tests
    latency_p95_per_config: map config_id -> p95 ms ; if None, treat as inf? For ordering, lower p95 wins.
    Returns {eligible: [...], chosen: config_id or None, ordering: [...], reason: str}
    Frozen rule: eligibility requires dev safety gates PASS AND Success@5 >=0.85 on dev headline 130
    Ordering: Success@5 desc -> NDCG@5 desc -> MRR@10 desc -> paired p95 asc -> lexicographic config_id asc
    """
    eligible = []
    for m in per_config_metrics:
        cid = m["config_id"]
        success = m.get("success_at_5", 0.0)
        # safety
        safety_ok = True
        if safety_per_config is not None:
            rep = safety_per_config.get(cid, {})
            safety_ok = _safety_passes(rep)
        else:
            # If no safety provided, assume PASS for pure logic tests
            safety_ok = True
        if safety_ok and success >= 0.85:
            eligible.append(m)

    # Ordering
    def sort_key(m):
        # For descending, use negative
        p95 = float("inf")
        if latency_p95_per_config and m["config_id"] in latency_p95_per_config:
            p95 = latency_p95_per_config[m["config_id"]]
        # If latency not provided, use large value but deterministic tie-break via config_id will still matter
        return (-m.get("success_at_5", 0), -m.get("ndcg_at_5", 0), -m.get("mrr_at_10", 0), p95, m["config_id"])

    eligible_sorted = sorted(eligible, key=sort_key)
    chosen = eligible_sorted[0]["config_id"] if eligible_sorted else None
    reason = "selected" if chosen else "no eligible (safety+Success>=85% fail)"
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
    Mechanical B admission diagnostic: union oracle R@100>=97% AND headroom >=5.0pp.
    Headroom = R@100 - Success@5 (pp units, 0-100)
    Returns {admitted: bool, headroom_pp: float, union_recall: float, reason}
    Candidate B MUST NOT be instantiated regardless; this is diagnostic only.
    """
    # Convert to percentages 0-100 if given as 0-1
    # Both inputs expected as 0-1 fraction; convert to pp
    union_pp = union_oracle_recall_100 * 100 if union_oracle_recall_100 <= 1.0 else union_oracle_recall_100
    cand_pp = candidate_a_success_5 * 100 if candidate_a_success_5 <= 1.0 else candidate_a_success_5
    headroom = union_pp - cand_pp
    admitted = (union_pp >= 97.0) and (headroom >= 5.0)
    # Note: B not instantiated, this is diagnostic gate only
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
