"""Hard-negative paired safety — D-007 blocking only on:

1. pure-positive gold hit@5 count  candidate < baseline  → FAIL
2. ineligible/excluded top-5 intrusion  candidate > baseline  → FAIL

Non-blocking diagnostics (score distribution, gap, lexical overlap, no-answer separation) are not gates and must not reintroduce global threshold.
"""
from __future__ import annotations


def hard_negative_gate(
    baseline_pure_hit5: int,
    candidate_pure_hit5: int,
    baseline_intrusion: int,
    candidate_intrusion: int,
) -> dict:
    pure_fail = candidate_pure_hit5 < baseline_pure_hit5
    intrude_fail = candidate_intrusion > baseline_intrusion
    failed = pure_fail or intrude_fail
    return {
        "baseline_pure_hit@5": baseline_pure_hit5,
        "candidate_pure_hit@5": candidate_pure_hit5,
        "baseline_intrusion_top5": baseline_intrusion,
        "candidate_intrusion_top5": candidate_intrusion,
        "pure_fail": pure_fail,
        "intrusion_fail": intrude_fail,
        "gate": "FAIL" if failed else "PASS",
        "overall": "FAIL" if failed else "PASS",
        # for adoption: FAIL → overall HOLD until re-pass
        "adoption": "HOLD" if failed else "PASS",
    }


def hard_negative_from_cases(baseline_cases: list[dict], candidate_cases: list[dict]) -> dict:
    """Helper that counts from hard-negative case lists.

    Each case dict is expected to have:
    - case_type: "pure_positive" vs "ineligible"/"excluded" etc.
    - hit@5: bool or rank 1..5
    For simplicity, caller passes counts, but this helper shows how to derive them.
    """
    # This is a stub for documentation; real counting is done by the evaluator that has per-case ranks.
    raise NotImplementedError("Use hard_negative_gate with pre-counted hit@5 and intrusion counts")
