"""Paired baseline-vs-candidate result model — D-007.

Input: two equal-length rank lists for the same query set (same order),
       plus explicit case identity.

Output:
- baseline metrics, candidate metrics
- net hit@5, macro delta
- per-case ranks for inspection
- GO/HOLD helper for +2 practical-effect rule
"""
from __future__ import annotations

from .metrics import compute_metrics


def _derive_by_source(ranks: list[int], case_sources: list[str]) -> dict[str, list[int]]:
    if len(ranks) != len(case_sources):
        raise ValueError("ranks and case_sources length mismatch")
    by: dict[str, list[int]] = {"youth": [], "gov24": []}
    for r, s in zip(ranks, case_sources):
        if s not in {"youth", "gov24"}:
            raise ValueError(f"case source must be youth|gov24, got {s!r}")
        by[s].append(r)
    return by


def paired_result(
    baseline_ranks: list[int],
    candidate_ranks: list[int],
    baseline_case_ids: list[str],
    candidate_case_ids: list[str],
    baseline_case_sources: list[str],
    candidate_case_sources: list[str],
    baseline_by_source: dict[str, list[int]] | None = None,
    candidate_by_source: dict[str, list[int]] | None = None,
    baseline_by_category: dict[str, list[int]] | None = None,
    candidate_by_category: dict[str, list[int]] | None = None,
) -> dict:
    if len(baseline_ranks) != len(candidate_ranks):
        raise ValueError(f"baseline {len(baseline_ranks)} vs candidate {len(candidate_ranks)} length mismatch — must be same query set and order")
    if not baseline_ranks:
        raise ValueError("empty ranks")

    # mandatory identity
    for name, ids, srcs in [
        ("baseline_case_ids", baseline_case_ids, baseline_case_sources),
        ("candidate_case_ids", candidate_case_ids, candidate_case_sources),
    ]:
        if ids is None or srcs is None:
            raise ValueError(f"{name} and corresponding case_sources are required — D-007 holdout requires explicit identity")
    if baseline_case_ids is None or candidate_case_ids is None or baseline_case_sources is None or candidate_case_sources is None:
        raise ValueError("case ids and sources are required")
    if len(baseline_case_ids) != len(baseline_ranks):
        raise ValueError(f"baseline_case_ids {len(baseline_case_ids)} != ranks {len(baseline_ranks)}")
    if len(candidate_case_ids) != len(candidate_ranks):
        raise ValueError(f"candidate_case_ids {len(candidate_case_ids)} != ranks {len(candidate_ranks)}")
    if len(baseline_case_sources) != len(baseline_ranks):
        raise ValueError("baseline_case_sources length must equal ranks")
    if len(candidate_case_sources) != len(candidate_ranks):
        raise ValueError("candidate_case_sources length must equal ranks")
    # non-empty and unique
    for ids in (baseline_case_ids, candidate_case_ids):
        if any(not isinstance(x, str) or not x.strip() for x in ids):
            raise ValueError("case IDs must be non-empty strings")
        if len(set(ids)) != len(ids):
            raise ValueError(f"duplicate case ID found: {ids!r}")
    # sources valid and both present
    for srcs in (baseline_case_sources, candidate_case_sources):
        for s in srcs:
            if s not in {"youth", "gov24"}:
                raise ValueError(f"case source must be youth|gov24, got {s!r}")
        if "youth" not in srcs or "gov24" not in srcs:
            raise ValueError("both youth and gov24 must be present in case sources")
    # exact order equality
    if baseline_case_ids != candidate_case_ids:
        raise ValueError(f"baseline and candidate case_ids differ — must be same query set and order: {baseline_case_ids!r} vs {candidate_case_ids!r}")
    if baseline_case_sources != candidate_case_sources:
        raise ValueError(f"baseline and candidate case sources differ — must be same order: {baseline_case_sources!r} vs {candidate_case_sources!r}")

    # derive by_source from ranks+case_sources
    derived_baseline = _derive_by_source(baseline_ranks, baseline_case_sources)
    derived_candidate = _derive_by_source(candidate_ranks, candidate_case_sources)

    # if caller provided by_source, verify consistency
    if baseline_by_source is not None:
        if baseline_by_source != derived_baseline:
            raise ValueError(f"provided baseline_by_source inconsistent with ranks/case_sources: {baseline_by_source!r} vs derived {derived_baseline!r}")
    else:
        baseline_by_source = derived_baseline
    if candidate_by_source is not None:
        if candidate_by_source != derived_candidate:
            raise ValueError(f"provided candidate_by_source inconsistent with ranks/case_sources: {candidate_by_source!r} vs derived {derived_candidate!r}")
    else:
        candidate_by_source = derived_candidate

    # also check source counts same between baseline and candidate (already via derived, but explicit)
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

    b_macro = (baseline["by_source"]["youth"]["recall@5"] + baseline["by_source"]["gov24"]["recall@5"]) / 2
    c_macro = (candidate["by_source"]["youth"]["recall@5"] + candidate["by_source"]["gov24"]["recall@5"]) / 2
    macro_delta = round(c_macro - b_macro, 4)

    per_case = [
        {"index": i, "case_id": cid, "baseline_rank": br, "candidate_rank": cr, "baseline_hit@5": 1 <= br <= 5, "candidate_hit@5": 1 <= cr <= 5}
        for i, (cid, br, cr) in enumerate(zip(baseline_case_ids, baseline_ranks, candidate_ranks), 1)
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
