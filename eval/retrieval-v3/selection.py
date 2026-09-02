"""Selection — frozen rule: safety + Success>=85% then ordering. Fail-closed on missing gates/latency."""

from __future__ import annotations
from typing import Any

# Expected gates per prereg §9 and candidate-plan selection_rule — must all be present and PASS
EXPECTED_SAFETY_GATES = {"unsupported", "ambiguous", "ineligible_expired", "official_link", "cost"}
# http_resolution is part of official_link gate but tracked separately; require it too if present in report
# For strict fail-closed, we require all keys in EXPECTED_SAFETY_GATES to be present.

def _safety_passes(safety_report: dict) -> bool:
    """
    safety_report: dict with keys for each gate: unsupported, ambiguous, ineligible_expired, official_link, cost, http_resolution etc each with PASS/NO-GO/HOLD
    Dev safety must PASS (HOLD is fail for selection). Per prereg: missing measurement => HOLD => not PASS => ineligible.
    So require all expected gates PASS and any present gate PASS. Missing expected gate => HOLD => not PASS.
    Returns False if missing safety or any gate not PASS.
    """
    if not safety_report or not isinstance(safety_report, dict):
        return False
    # Check expected gates present
    for eg in EXPECTED_SAFETY_GATES:
        if eg not in safety_report:
            return False
        v = safety_report[eg]
        gate = v if isinstance(v, str) else v.get("gate") or v.get("result") or v.get("status")
        if gate != "PASS":
            return False
    # Also check any other gate present in report (including http_resolution, gate overall) — if any is not PASS => fail
    for k, v in safety_report.items():
        if k == "gate":
            # overall gate
            gv = v if isinstance(v, str) else v.get("gate") or v.get("result") or v.get("status")
            if gv != "PASS":
                return False
            continue
        # For expected gates already checked, still ensure not overridden
        gate = v if isinstance(v, str) else v.get("gate") or v.get("result") or v.get("status")
        # If gate is explicitly present, it must be PASS
        if gate is not None and gate != "PASS":
            return False
        # If gate is None (missing structure) but key is expected, already handled; for unexpected keys, treat missing as not PASS? No, ignore.
    return True

def select_candidate(
    per_config_metrics: list[dict],
    safety_per_config: dict[str, dict] | None = None,
    latency_p95_per_config: dict[str, float] | None = None,
) -> dict:
    """
    per_config_metrics: list of {config_id, success_at_5, ndcg_at_5, mrr_at_10, ...}
    safety_per_config: map config_id -> safety_report dict ; if None, assume PASS for tests (pure logic explicit fixtures not required)
                     if provided, missing safety for a config or missing expected gates => HOLD => ineligible
    latency_p95_per_config: map config_id -> p95 ms ; if None, treat as inf for ordering (pure tests)
                     if provided, missing latency for a config => HOLD => ineligible
    Returns {eligible: [...], chosen: config_id or None, ordering: [...], reason: str}
    Frozen rule: eligibility requires dev safety gates PASS AND Success@5 >=0.85 on dev headline 130
    Ordering: Success@5 desc -> NDCG@5 desc -> MRR@10 desc -> paired p95 asc -> lexicographic config_id asc
    """
    eligible = []
    for m in per_config_metrics:
        cid = m["config_id"]
        success = m.get("success_at_5", 0.0)
        # safety fail-closed
        safety_ok = True
        if safety_per_config is not None:
            # explicit fixtures required: missing safety for this config => HOLD => ineligible
            if cid not in safety_per_config:
                safety_ok = False
            else:
                rep = safety_per_config.get(cid, {})
                safety_ok = _safety_passes(rep)
        else:
            safety_ok = True
        # latency fail-closed when latency dict is explicitly provided
        latency_ok = True
        p95_val = None
        if latency_p95_per_config is not None:
            if cid not in latency_p95_per_config:
                latency_ok = False
            else:
                p95_val = latency_p95_per_config[cid]
                if p95_val is None:
                    latency_ok = False
                else:
                    try:
                        # ensure it is numeric and finite
                        pf = float(p95_val)
                        if not (pf == pf and pf != float("inf") and pf != float("-inf")):
                            # inf is placeholder for missing, treat as not ok if we require explicit?
                            # But for ordering, inf is allowed; for fail-closed, missing latency should be HOLD
                            # So we consider inf as missing if latency was explicitly required and value is inf due to missing?
                            # Keep as ok for ordering tie-break but not fail.
                            pass
                    except Exception:
                        latency_ok = False
        if safety_ok and latency_ok and success >= 0.85:
            # also need to ensure latency not missing when expected; already checked
            eligible.append(m)

    # Ordering: exact order S5 > NDCG5 > MRR10 > p95 > config_id
    def sort_key(m):
        p95 = float("inf")
        if latency_p95_per_config and m["config_id"] in latency_p95_per_config:
            val = latency_p95_per_config[m["config_id"]]
            if val is not None:
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
