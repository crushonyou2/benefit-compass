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
) -> dict:
    if len(baseline_ranks) != len(candidate_ranks):
        raise ValueError(f"baseline {len(baseline_ranks)} vs candidate {len(candidate_ranks)} length mismatch — must be same query set and order")
    if not baseline_ranks:
        raise ValueError("empty ranks")

    baseline = compute_metrics(baseline_ranks, baseline_by_source, baseline_by_category)
    candidate = compute_metrics(candidate_ranks, candidate_by_source, candidate_by_category)

    # net hit@5 on same set
    b_hit5 = baseline["hit@5"]
    c_hit5 = candidate["hit@5"]
    net = c_hit5 - b_hit5

    # per-source hit deltas
    per_source_delta = {}
    if baseline_by_source and candidate_by_source:
        for src in sorted(set(baseline_by_source) | set(candidate_by_source)):
            b = sum(1 for r in baseline_by_source.get(src, []) if 1 <= r <= 5)
            c = sum(1 for r in candidate_by_source.get(src, []) if 1 <= r <= 5)
            per_source_delta[src] = {"baseline_hit@5": b, "candidate_hit@5": c, "delta": c - b, "regression": c < b}

    # macro delta
    macro_delta = None
    if baseline_by_source and candidate_by_source and "youth" in baseline_by_source and "gov24" in baseline_by_source:
        b_macro = (baseline["by_source"]["youth"]["recall@5"] + baseline["by_source"]["gov24"]["recall@5"]) / 2
        c_macro = (candidate["by_source"]["youth"]["recall@5"] + candidate["by_source"]["gov24"]["recall@5"]) / 2
        macro_delta = round(c_macro - b_macro, 4)

    # per-case
    per_case = [
        {"index": i, "baseline_rank": br, "candidate_rank": cr, "baseline_hit@5": 1 <= br <= 5, "candidate_hit@5": 1 <= cr <= 5}
        for i, (br, cr) in enumerate(zip(baseline_ranks, candidate_ranks), 1)
    ]

    # D-007 holdout PASS requires:
    # candidate macro > baseline AND net >= +2 AND no source regression
    # Here we expose the raw check; caller decides HOLD/NO-GO.
    macro_pass = (macro_delta is not None and macro_delta > 0) if macro_delta is not None else (net > 0)
    no_source_regression = all(not v["regression"] for v in per_source_delta.values()) if per_source_delta else True
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
    """Return PASS/HOLD/NO-GO string for the +2 rule (without P0)."""
    if no_source_regression is False:
        # any source loses — HOLD or NO-GO, but for paired alone it's HOLD
        return "HOLD"
    if net_hit5 >= 2:
        return "PASS"
    if net_hit5 == 1:
        return "HOLD"
    return "NO-GO"
