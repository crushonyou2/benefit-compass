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
    # validate finite and non-negative
    for s in samples:
        if not isinstance(s.latency_ms, (int, float)):
            raise ValueError(f"latency_ms must be number, got {s.latency_ms!r} for {s.query_id}/{s.variant}")
        if not math.isfinite(s.latency_ms):
            raise ValueError(f"latency_ms must be finite, got {s.latency_ms!r} for {s.query_id}/{s.variant}")
        if s.latency_ms < 0:
            raise ValueError(f"latency_ms must be >=0, got {s.latency_ms!r} for {s.query_id}/{s.variant}")
        if s.variant not in {"baseline", "candidate"}:
            raise ValueError(f"unknown variant {s.variant!r}")
    # build key -> {baseline, candidate} and check duplicate and pairing
    from collections import defaultdict
    by_key: dict[tuple[str, int], dict[str, Sample]] = defaultdict(dict)
    for s in samples:
        key = (s.query_id, s.round)
        if s.variant in by_key[key]:
            raise ValueError(f"duplicate sample for key {key} variant {s.variant!r}")
        by_key[key][s.variant] = s
    # every key must have exactly one baseline and one candidate
    for key, variants in by_key.items():
        if set(variants.keys()) != {"baseline", "candidate"}:
            raise ValueError(f"key {key} must have exactly one baseline and one candidate, got {sorted(variants.keys())}")
    # check interleaving: timed samples must be paired, not all baseline then all candidate
    # We enforce that the input list is already paired: each consecutive pair shares same (query_id, round) and has both variants
    if len(samples) % 2 != 0:
        raise ValueError("samples must be even — each (query_id, round) yields 2 samples")
    for i in range(0, len(samples), 2):
        a = samples[i]
        b = samples[i + 1]
        if (a.query_id, a.round) != (b.query_id, b.round):
            raise ValueError(f"samples not properly paired/interleaved at positions {i}/{i+1}: {(a.query_id, a.round)} vs {(b.query_id, b.round)} — expected paired interleaving, not all baseline then all candidate")
        if {a.variant, b.variant} != {"baseline", "candidate"}:
            raise ValueError(f"pair at {i}/{i+1} must be one baseline and one candidate, got {a.variant!r}/{b.variant!r}")

    by_variant: dict[str, list[float]] = {"baseline": [], "candidate": []}
    for s in samples:
        by_variant[s.variant].append(s.latency_ms)
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
