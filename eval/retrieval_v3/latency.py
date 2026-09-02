"""Paired latency harness — deterministic warmup, interleaved, nearest-rank."""
from __future__ import annotations
import math
from typing import Callable, Any

def _percentile_nearest_rank(data: list[float], p: float) -> float:
    """Nearest-rank p-th percentile (p in 0-100)."""
    if not data:
        raise ValueError("empty data")
    sorted_data = sorted(data)
    n = len(sorted_data)
    # rank = ceil(p/100 * n)
    rank = math.ceil(p / 100 * n)
    rank = max(1, min(rank, n))
    return sorted_data[rank - 1]

def measure_paired_latency(
    tasks_sorted: list[str],
    baseline_fn: Callable[[str], Any],
    candidate_fn: Callable[[str], Any],
    clock_fn: Callable[[], int] | None = None,  # returns ns
    warmup_n: int = 30,
) -> dict:
    """
    Paired warm, interleaved measurement.
    - warmup first 30 canonical sorted task IDs (or fewer if tasks <30)
    - same env/DB/corpus (caller ensures)
    - warm/interleaved; cold/model-load excluded (warmup not timed)
    - exactly one timed sample/task/variant
    - alternate variant order by task index
    - nearest-rank p50/p95/p99
    Gate: candidate p95 <= baseline p95 +80ms AND candidate p95 <=700ms

    clock_fn: should return perf_counter_ns; if None, uses time.perf_counter_ns()
    baseline_fn/candidate_fn: callable(task_id) -> maybe result (ignored), but must be called exactly once per task per variant
    Returns dict with baseline/candidate p50/p95/p99 and gate result.
    """
    import time as _time
    if clock_fn is None:
        clock_fn = _time.perf_counter_ns

    # Canonical sorted already; but ensure sorted
    tasks = sorted(tasks_sorted)
    warmup_tasks = tasks[:min(warmup_n, len(tasks))]

    # Warmup — not timed, but must call both variants
    for tid in warmup_tasks:
        baseline_fn(tid)
        candidate_fn(tid)

    baseline_latencies = []
    candidate_latencies = []

    for idx, tid in enumerate(tasks):
        if idx % 2 == 0:
            # baseline first
            t0 = clock_fn()
            baseline_fn(tid)
            t1 = clock_fn()
            baseline_latencies.append((t1 - t0) / 1e6)  # ms

            t0 = clock_fn()
            candidate_fn(tid)
            t1 = clock_fn()
            candidate_latencies.append((t1 - t0) / 1e6)
        else:
            # candidate first (alternate)
            t0 = clock_fn()
            candidate_fn(tid)
            t1 = clock_fn()
            candidate_latencies.append((t1 - t0) / 1e6)

            t0 = clock_fn()
            baseline_fn(tid)
            t1 = clock_fn()
            baseline_latencies.append((t1 - t0) / 1e6)

    if len(baseline_latencies) != len(tasks) or len(candidate_latencies) != len(tasks):
        raise RuntimeError("latency sample count mismatch (fail-closed)")

    # nearest-rank
    baseline_p50 = _percentile_nearest_rank(baseline_latencies, 50)
    baseline_p95 = _percentile_nearest_rank(baseline_latencies, 95)
    baseline_p99 = _percentile_nearest_rank(baseline_latencies, 99)
    candidate_p50 = _percentile_nearest_rank(candidate_latencies, 50)
    candidate_p95 = _percentile_nearest_rank(candidate_latencies, 95)
    candidate_p99 = _percentile_nearest_rank(candidate_latencies, 99)

    gate = (candidate_p95 <= baseline_p95 + 80) and (candidate_p95 <= 700)

    return {
        "n": len(tasks),
        "warmup_n": len(warmup_tasks),
        "baseline": {"p50": baseline_p50, "p95": baseline_p95, "p99": baseline_p99, "samples": baseline_latencies},
        "candidate": {"p50": candidate_p50, "p95": candidate_p95, "p99": candidate_p99, "samples": candidate_latencies},
        "gate": "PASS" if gate else "NO-GO",
        "gate_detail": f"candidate p95 {candidate_p95:.2f} <= baseline p95 {baseline_p95:.2f}+80 and <=700 : {gate}",
        "method": "paired warm interleaved, warmup 30 sorted, alternate order, one sample/task/variant, nearest-rank",
    }

def evaluate_latency_gate(candidate_p95: float, baseline_p95: float) -> bool:
    return (candidate_p95 <= baseline_p95 + 80) and (candidate_p95 <= 700)
