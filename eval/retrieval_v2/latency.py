"""Warm paired latency harness — D-007.

Principles:
- same environment, same DB/corpus, same benchmark queries
- model already warm, cold/model-load excluded
- baseline and candidate measured in the same run/window
- identical number of timed observations
- baseline/candidate interleaved, not all A then B
- warm-up excluded
- sample count, p50, p95 recorded

No production fixed numbers are invented; harness is deterministic/testable.
Primary gate: candidate p95 <= paired baseline p95.
"""
from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class Sample:
    query_id: str
    round: int
    variant: str  # "baseline" | "candidate"
    latency_ms: float


def p50(latencies: list[float]) -> float:
    if not latencies:
        raise ValueError("empty")
    s = sorted(latencies)
    n = len(s)
    # deterministic: lower-median for even, like numpy percentile 50 with interpolation?
    # Use nearest-rank: p50 = s[ceil(0.5*n)-1]
    idx = math.ceil(0.5 * n) - 1
    return float(s[idx])


def p95(latencies: list[float]) -> float:
    if not latencies:
        raise ValueError("empty")
    s = sorted(latencies)
    n = len(s)
    idx = math.ceil(0.95 * n) - 1
    return float(s[max(0, min(idx, n - 1))])


def summarize(samples: list[Sample]) -> dict:
    if not samples:
        raise ValueError("no samples")
    by_variant: dict[str, list[float]] = {"baseline": [], "candidate": []}
    for s in samples:
        if s.variant not in by_variant:
            raise ValueError(f"unknown variant {s.variant!r}")
        by_variant[s.variant].append(s.latency_ms)
    # check identical counts
    if len(by_variant["baseline"]) != len(by_variant["candidate"]):
        raise ValueError(f"baseline {len(by_variant['baseline'])} vs candidate {len(by_variant['candidate'])} count mismatch — must be identical timed sample count")
    out = {
        "sample_count": len(by_variant["baseline"]),
        "baseline": {
            "p50": round(p50(by_variant["baseline"]), 2),
            "p95": round(p95(by_variant["baseline"]), 2),
            "count": len(by_variant["baseline"]),
        },
        "candidate": {
            "p50": round(p50(by_variant["candidate"]), 2),
            "p95": round(p95(by_variant["candidate"]), 2),
            "count": len(by_variant["candidate"]),
        },
    }
    out["gate"] = "PASS" if out["candidate"]["p95"] <= out["baseline"]["p95"] else "HOLD"
    out["delta_p95"] = round(out["candidate"]["p95"] - out["baseline"]["p95"], 2)
    return out


def is_latency_pass(baseline_p95: float, candidate_p95: float) -> bool:
    return candidate_p95 <= baseline_p95
