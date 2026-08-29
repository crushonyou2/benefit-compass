"""P0 regression gate — D-007 Youth >=28/60, Gov24 >=15/21.

Frozen P0 artifacts are read-only; this helper is pure and testable.

 youth: 28/60 PASS, 27/60 HOLD, <=26/60 NO-GO
 gov24: 15/21 PASS, 14/21 HOLD, <=13/21 NO-GO
"""
from __future__ import annotations

def youth_gate(hit5: int, n: int = 60) -> str:
    if n != 60:
        raise ValueError("youth n must be 60 for P0 gate (use 60 even for dev/holdout P0 check)")
    if not (0 <= hit5 <= n):
        raise ValueError(f"youth hit5 {hit5} out of range 0..{n}")
    if hit5 >= 28:
        return "PASS"
    if hit5 == 27:
        return "HOLD"
    return "NO-GO"


def gov24_gate(hit5: int, n: int = 21) -> str:
    if n != 21:
        raise ValueError("gov24 n must be 21 for P0 gate")
    if not (0 <= hit5 <= n):
        raise ValueError(f"gov24 hit5 {hit5} out of range 0..{n}")
    if hit5 >= 15:
        return "PASS"
    if hit5 == 14:
        return "HOLD"
    return "NO-GO"


def _overall(y: str, g: str) -> str:
    if y == "PASS" and g == "PASS":
        return "PASS"
    if y == "NO-GO" or g == "NO-GO":
        return "NO-GO"
    return "HOLD"


def p0_gate(by_source: dict[str, list[int]]) -> dict:
    """by_source: {"youth": ranks, "gov24": ranks} where ranks are gold ranks (0 = miss)."""
    if "youth" not in by_source or "gov24" not in by_source:
        raise ValueError("by_source must contain youth and gov24")
    if len(by_source["youth"]) != 60:
        raise ValueError(f"youth len {len(by_source['youth'])} != 60 — P0 set size must be 60")
    if len(by_source["gov24"]) != 21:
        raise ValueError(f"gov24 len {len(by_source['gov24'])} != 21 — P0 set size must be 21")
    y_hit5 = sum(1 for r in by_source["youth"] if 1 <= r <= 5)
    g_hit5 = sum(1 for r in by_source["gov24"] if 1 <= r <= 5)
    y = youth_gate(y_hit5)
    g = gov24_gate(g_hit5)
    overall = _overall(y, g)
    return {
        "youth": {"hit@5": y_hit5, "n": 60, "gate": y},
        "gov24": {"hit@5": g_hit5, "n": 21, "gate": g},
        "overall": overall,
    }


def p0_gate_from_metrics(metrics: dict) -> dict:
    """metrics is the output of metrics.compute_metrics with by_source."""
    by_source = metrics.get("by_source")
    if not by_source:
        raise ValueError("metrics missing by_source")
    y_hit5 = by_source["youth"]["hit@5"]
    g_hit5 = by_source["gov24"]["hit@5"]
    y_n = by_source["youth"]["n"]
    g_n = by_source["gov24"]["n"]
    if y_n != 60:
        raise ValueError(f"youth n {y_n} != 60")
    if g_n != 21:
        raise ValueError(f"gov24 n {g_n} != 21")
    y = youth_gate(y_hit5)
    g = gov24_gate(g_hit5)
    return {
        "youth": y,
        "gov24": g,
        "youth_hit5": y_hit5,
        "gov24_hit5": g_hit5,
        "overall": _overall(y, g),
    }
