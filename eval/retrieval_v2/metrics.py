"""Metrics for Retrieval v2 — D-007 primary is source-macro Recall@5.

Computes:
- raw hit@1/5/10 per case (gold rank in top-k)
- Recall@1/5/10, MRR@10
- per-source raw hits and metrics
- category diagnostic breakdown
- source-macro Recall@5 = (Youth Recall@5 + Gov24 Recall@5) / 2

Reuse of eval/run_eval.py's rank_of/top-k logic is intentional,
but this module is DB-free and works on ranks already computed.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Iterable


def recall_at_k(ranks: Iterable[int], k: int) -> float:
    ranks = list(ranks)
    if not ranks:
        return 0.0
    hits = sum(1 for r in ranks if 1 <= r <= k)
    return hits / len(ranks)


def mrr_at_k(ranks: Iterable[int], k: int = 10) -> float:
    ranks = list(ranks)
    if not ranks:
        return 0.0
    return sum((1 / r if 1 <= r <= k else 0) for r in ranks) / len(ranks)


def compute_metrics(ranks: list[int], by_source: dict[str, list[int]] | None = None, by_category: dict[str, list[int]] | None = None) -> dict:
    """ranks: list of gold ranks (0 = not in top-k, 1..TOPK = rank)."""
    if not ranks:
        raise ValueError("ranks empty")
    out: dict = {
        "n": len(ranks),
        "recall@1": round(recall_at_k(ranks, 1), 4),
        "recall@5": round(recall_at_k(ranks, 5), 4),
        "recall@10": round(recall_at_k(ranks, 10), 4),
        "mrr@10": round(mrr_at_k(ranks, 10), 4),
        "hit@1": sum(1 for r in ranks if r == 1),
        "hit@5": sum(1 for r in ranks if 1 <= r <= 5),
        "hit@10": sum(1 for r in ranks if 1 <= r <= 10),
    }
    if by_source is not None:
        out["by_source"] = {}
        for src, rs in sorted(by_source.items()):
            out["by_source"][src] = {
                "n": len(rs),
                "hit@1": sum(1 for r in rs if r == 1),
                "hit@5": sum(1 for r in rs if 1 <= r <= 5),
                "hit@10": sum(1 for r in rs if 1 <= r <= 10),
                "recall@1": round(recall_at_k(rs, 1), 4),
                "recall@5": round(recall_at_k(rs, 5), 4),
                "recall@10": round(recall_at_k(rs, 10), 4),
                "mrr@10": round(mrr_at_k(rs, 10), 4),
            }
        # source-macro Recall@5
        if "youth" in by_source and "gov24" in by_source:
            y = recall_at_k(by_source["youth"], 5)
            g = recall_at_k(by_source["gov24"], 5)
            out["source_macro_recall@5"] = round((y + g) / 2, 4)
            out["source_macro_hit@5"] = {
                "youth": sum(1 for r in by_source["youth"] if 1 <= r <= 5),
                "gov24": sum(1 for r in by_source["gov24"] if 1 <= r <= 5),
            }
    if by_category is not None:
        out["by_category"] = {}
        for cat, rs in sorted(by_category.items()):
            out["by_category"][cat] = {
                "n": len(rs),
                "hit@5": sum(1 for r in rs if 1 <= r <= 5),
                "recall@5": round(recall_at_k(rs, 5), 4),
            }
    return out


def macro_recall_at_5(by_source: dict[str, list[int]]) -> float:
    if "youth" not in by_source or "gov24" not in by_source:
        raise ValueError("by_source must contain both youth and gov24")
    return round((recall_at_k(by_source["youth"], 5) + recall_at_k(by_source["gov24"], 5)) / 2, 4)
