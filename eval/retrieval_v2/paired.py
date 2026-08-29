"""Paired baseline-vs-candidate result model — D-007.

Input: two equal-length rank lists for the same query set (same order),
       plus by_source breakdowns.

Output:
- baseline metrics, candidate metrics
- net hit@5, macro delta
- per-case ranks for inspection
- GO/HOLD helper for +2 practical-effect rule
"""
from __future__ import annotations

from .metrics import compute_metrics, macro_recall_at_5


def paired_result(
    baseline_ranks: list[int],
    candidate_ranks: list[int],
    baseline_by_source: dict[str, list[int]] | None = None,
    candidate_by_source: dict[str, list[int]] | None = None,
    baseline_by_category: dict[str, list[int]] | None = None,
    candidate_by_category: dict[str, list[int]] | None = None,
    baseline_case_ids: list[str] | None = None,
    candidate_case_ids: list[str] | None = None,
    baseline_case_sources: list[str] | None = None,
    candidate_case_sources: list[str] | None = None,
) -> dict:
    if len(baseline_ranks) != len(candidate_ranks):
        raise ValueError(f"baseline {len(baseline_ranks)} vs candidate {len(candidate_ranks)} length mismatch — must be same query set and order")
    if not baseline_ranks:
        raise ValueError("empty ranks")

    # D-007 holdout requires explicit case identity and source enforcement
    if baseline_case_ids is not None or candidate_case_ids is not None:
        if baseline_case_ids is None or candidate_case_ids is None:
            raise ValueError("both baseline_case_ids and candidate_case_ids must be provided together")
        if len(baseline_case_ids) != len(baseline_ranks) or len(candidate_case_ids) != len(candidate_ranks):
            raise ValueError("case_ids length must match ranks length")
        if baseline_case_ids != candidate_case_ids:
            raise ValueError(f"baseline and candidate case_ids differ — must be same query set and order: {baseline_case_ids!r} vs {candidate_case_ids!r}")
        if baseline_case_sources is not None or candidate_case_sources is not None:
            if baseline_case_sources is None or candidate_case_sources is None:
                raise ValueError("both baseline_case_sources and candidate_case_sources must be provided together")
            if baseline_case_sources != candidate_case_sources:
                raise ValueError("baseline and candidate source membership differ")
            if len(baseline_case_sources) != len(baseline_ranks):
                raise ValueError("case_sources length must match ranks")
            # source membership and counts already checked via by_source, but also check per-source counts match
            from collections import Counter
            if Counter(baseline_case_sources) != Counter(candidate_case_sources):
                raise ValueError("source membership counts differ between baseline and candidate")

    # enforce by_source for holdout
    if baseline_by_source is None or candidate_by_source is None:
        raise ValueError("baseline_by_source and candidate_by_source are required for D-007 holdout — must contain youth and gov24")
    if "youth" not in baseline_by_source or "gov24" not in baseline_by_source:
        raise ValueError("baseline_by_source must contain youth and gov24")
    if "youth" not in candidate_by_source or "gov24" not in candidate_by_source:
        raise ValueError("candidate_by_source must contain youth and gov24")
    if len(baseline_by_source["youth"]) + len(baseline_by_source["gov24"]) != len(baseline_ranks):
        raise ValueError("by_source youth+gov24 counts must equal total ranks")
    if len(candidate_by_source["youth"]) + len(candidate_by_source["gov24"]) != len(candidate_ranks):
        raise ValueError("by_source youth+gov24 counts must equal total ranks")
    # also check source membership counts same between baseline and candidate
    if len(baseline_by_source["youth"]) != len(candidate_by_source["youth"]):
        raise ValueError(f"youth count differs baseline {len(baseline_by_source['youth'])} vs candidate {len(candidate_by_source['youth'])}")
    if len(baseline_by_source["gov24"]) != len(candidate_by_source["gov24"]):
        raise ValueError(f"gov24 count differs baseline {len(baseline_by_source['gov24'])} vs candidate {len(candidate_by_source['gov24'])}")

    baseline = compute_metrics(baseline_ranks, baseline_by_source, baseline_by_category)
    candidate = compute_metrics(candidate_ranks, candidate_by_source, candidate_by_category)

    b_hit5 = baseline["hit@5"]
    c_hit5 = candidate["hit@5"]
    net = c_hit5 - b_hit5

    per_source_delta = {}
    for src in sorted(set(baseline_by_source) | set(candidate_by_source)):
        b = sum(1 for r in baseline_by_source.get(src, []) if 1 <= r <= 5)
        c = sum(1 for r in candidate_by_source.get(src, []) if 1 <= r <= 5)
        per_source_delta[src] = {"baseline_hit@5": b, "candidate_hit@5": c, "delta": c - b, "regression": c < b}

    macro_delta = None
    b_macro = (baseline["by_source"]["youth"]["recall@5"] + baseline["by_source"]["gov24"]["recall@5"]) / 2
    c_macro = (candidate["by_source"]["youth"]["recall@5"] + candidate["by_source"]["gov24"]["recall@5"]) / 2
    macro_delta = round(c_macro - b_macro, 4)

    per_case = [
        {"index": i, "baseline_rank": br, "candidate_rank": cr, "baseline_hit@5": 1 <= br <= 5, "candidate_hit@5": 1 <= cr <= 5}
        for i, (br, cr) in enumerate(zip(baseline_ranks, candidate_ranks), 1)
    ]

    macro_pass = macro_delta > 0
    no_source_regression = all(not v["regression"] for v in per_source_delta.values())
    practical = net >= 2

    return {
        "n": len(baseline_ranks),
        "baseline": baseline,
        "candidate": candidate,
        "net_hit@5": net,
        "macro_delta": macro_delta,
        "per_source_delta": per_source_delta,
        "per_case": per_case,
        "summary": {
            "macro_pass": macro_pass,
            "practical_ge_2": practical,
            "no_source_regression": no_source_regression,
        },
    }


def is_practical_improvement(net_hit5: int, no_source_regression: bool) -> str:
    """Return PASS/HOLD/NO-GO for the +2 rule (without macro). Fixed precedence: net first."""
    if net_hit5 <= 0:
        return "NO-GO"
    if net_hit5 == 1:
        return "HOLD"
    if no_source_regression is False:
        return "HOLD"
    if net_hit5 >= 2:
        return "PASS"
    return "NO-GO"


def holdout_quality_gate(macro_pass: bool, net_hit5: int, no_source_regression: bool) -> str:
    """D-007 final holdout quality gate with macro, net, and source regression."""
    if not macro_pass:
        return "NO-GO"
    if net_hit5 <= 0:
        return "NO-GO"
    if net_hit5 == 1:
        return "HOLD"
    if no_source_regression is False:
        return "HOLD"
    if net_hit5 >= 2:
        return "PASS"
    return "NO-GO"
