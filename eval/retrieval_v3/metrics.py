"""Metrics/diagnostics — Success@1/@3/@5, strict grade3, MRR@10, NDCG@5/@10, oracle Recall, slices. Graded multi-gold equivalence-group aware. Relevance unit = equivalence_group; members are alternatives. Group gain = max grade within group; exact identity when no equivalence_group."""

from __future__ import annotations
import math
from collections import defaultdict

def _build_groups(golds: list[dict]) -> dict:
    """Build equivalence groups.

    - If gold has equivalence_group (non-empty), key = equivalence_group string; all members sharing same group are alternatives.
    - Else key = unique per gold identity (source+source_id).
    - Group grade = max grade among members (canonical graded semantics, highest applicable).
    - Group members = set of (source, source_id).
    Returns dict group_key -> {"grade": int, "members": set}
    """
    groups = {}
    for g in golds:
        eg = g.get("equivalence_group")
        if eg is None or (isinstance(eg, str) and eg.strip() == ""):
            # exact identity per gold
            key = f"__id__:{g.get('source')}\x00{g.get('source_id')}"
        else:
            key = f"__group__:{eg}"
        grade = int(g.get("grade", 0))
        if key not in groups:
            groups[key] = {"grade": grade, "members": set()}
        else:
            if grade > groups[key]["grade"]:
                groups[key]["grade"] = grade
        groups[key]["members"].add((g.get("source"), g.get("source_id")))
    return groups

def _member_to_group_map(groups: dict) -> dict:
    """Map (source,source_id) -> group_key for quick lookup."""
    m = {}
    for gkey, info in groups.items():
        for mem in info["members"]:
            # If multiple groups share same member (should not happen), first wins
            if mem not in m:
                m[mem] = gkey
    return m

def _is_success_in_topk(retrieved: list[dict], golds: list[dict], k: int) -> bool:
    """Success if any grade>=2 group is satisfied by any retrieved member in topk."""
    if not golds:
        return False
    groups = _build_groups(golds)
    # Build set of members belonging to grade>=2 groups
    topk_ids = {(r.get("source"), r.get("source_id")) for r in retrieved[:k]}
    for gkey, info in groups.items():
        if info["grade"] >= 2:
            if info["members"] & topk_ids:
                return True
    return False

def _is_success_in_topk_strict_grade3(retrieved: list[dict], golds: list[dict], k: int) -> bool:
    """Strict grade3 success: requires grade==3 group in topk. Use max grade ==3."""
    if not golds:
        return False
    groups = _build_groups(golds)
    topk_ids = {(r.get("source"), r.get("source_id")) for r in retrieved[:k]}
    for gkey, info in groups.items():
        if info["grade"] == 3:
            if info["members"] & topk_ids:
                return True
    return False

def _first_grade_ge2_rank(retrieved: list[dict], golds: list[dict]) -> int:
    """Return 1-indexed rank of first grade>=2 group member in retrieved, or 0 if not found. Alternative member match counts."""
    if not golds:
        return 0
    groups = _build_groups(golds)
    # Build set of members for grade>=2 groups
    target_members = set()
    for info in groups.values():
        if info["grade"] >= 2:
            target_members.update(info["members"])
    for idx, r in enumerate(retrieved, start=1):
        if (r.get("source"), r.get("source_id")) in target_members:
            return idx
    return 0

def success_at_1(retrieved: list[dict], golds: list[dict]) -> int:
    return 1 if _is_success_in_topk(retrieved, golds, 1) else 0

def success_at_3(retrieved: list[dict], golds: list[dict]) -> int:
    return 1 if _is_success_in_topk(retrieved, golds, 3) else 0

def success_at_5(retrieved: list[dict], golds: list[dict]) -> int:
    return 1 if _is_success_in_topk(retrieved, golds, 5) else 0

def success_at_5_strict_grade3(retrieved: list[dict], golds: list[dict]) -> int:
    return 1 if _is_success_in_topk_strict_grade3(retrieved, golds, 5) else 0

# Backwards alias for explicit strict naming
def strict_grade3_success_at_5(retrieved: list[dict], golds: list[dict]) -> int:
    return success_at_5_strict_grade3(retrieved, golds)

def mrr_at_10(retrieved: list[dict], golds: list[dict]) -> float:
    rank = _first_grade_ge2_rank(retrieved, golds)
    if 1 <= rank <= 10:
        return 1.0 / rank
    return 0.0

def dcg_at_k(retrieved: list[dict], golds: list[dict], k: int) -> float:
    """DCG with gain = group grade (max within equivalence_group), discount log2(rank+1). No double-count for same group."""
    if not golds:
        return 0.0
    groups = _build_groups(golds)
    member_to_group = _member_to_group_map(groups)
    dcg = 0.0
    seen_groups = set()
    for idx, r in enumerate(retrieved[:k], start=1):
        mem = (r.get("source"), r.get("source_id"))
        gkey = member_to_group.get(mem)
        if gkey is None:
            continue
        if gkey in seen_groups:
            continue
        grade = groups[gkey]["grade"]
        if grade > 0:
            dcg += grade / math.log2(idx + 1)
            seen_groups.add(gkey)
    return dcg

def idcg_at_k(golds: list[dict], k: int) -> float:
    """Ideal DCG sorted by group grade desc. One gain per equivalence group, not per gold member."""
    if not golds:
        return 0.0
    groups = _build_groups(golds)
    grades = sorted([info["grade"] for info in groups.values() if info["grade"] > 0], reverse=True)
    idcg = 0.0
    for idx, grade in enumerate(grades[:k], start=1):
        idcg += grade / math.log2(idx + 1)
    return idcg

def ndcg_at_5(retrieved: list[dict], golds: list[dict]) -> float:
    dcg = dcg_at_k(retrieved, golds, 5)
    idcg = idcg_at_k(golds, 5)
    if idcg == 0:
        return 0.0
    return dcg / idcg

def ndcg_at_10(retrieved: list[dict], golds: list[dict]) -> float:
    dcg = dcg_at_k(retrieved, golds, 10)
    idcg = idcg_at_k(golds, 10)
    if idcg == 0:
        return 0.0
    return dcg / idcg

def recall_at_k_oracle(oracle_pool: list[dict], golds: list[dict], k: int) -> int:
    """Oracle Recall@k: whether any grade>=2 group appears in first k of oracle_pool (unordered set existence if pool is set). Group-aware."""
    if not golds:
        return 0
    groups = _build_groups(golds)
    topk = oracle_pool[:k]
    pool_ids = {(r.get("source"), r.get("source_id")) for r in topk}
    for gkey, info in groups.items():
        if info["grade"] >= 2:
            if info["members"] & pool_ids:
                return 1
    return 0

def _union_recall_at_k(task_oracle: dict, k: int) -> int:
    """Union oracle Recall@K = set(dense own topK) ∪ set(sparse own topK) ∪ set(exact own topK). Group-aware."""
    golds = task_oracle.get("golds", [])
    if not golds:
        return 0
    groups = _build_groups(golds)
    dense_ids = {(d.get("source"), d.get("source_id")) for d in task_oracle.get("dense_pool", [])[:k]}
    sparse_ids = {(s.get("source"), s.get("source_id")) for s in task_oracle.get("sparse_pool", [])[:k]}
    exact_ids = {(e.get("source"), e.get("source_id")) for e in task_oracle.get("exact_pool", [])[:k]}
    if not dense_ids and not sparse_ids and not exact_ids:
        union_pool = task_oracle.get("union_pool", [])
        pool_ids = {(r.get("source"), r.get("source_id")) for r in union_pool[:k]}
    else:
        pool_ids = dense_ids | sparse_ids | exact_ids
    for gkey, info in groups.items():
        if info["grade"] >= 2:
            if info["members"] & pool_ids:
                return 1
    return 0

def compute_headline_metrics(task_results: list[dict]) -> dict:
    """
    task_results: list of {retrieved: [...], golds: [...], source, stratum, location_bearing, ...}
    Computes Success@1/@3/@5, strict grade3 Success@5, NDCG@5/@10, MRR@10 over headline tasks.
    Graded multi-gold equivalence-group aware: grade>=2 is success, grade==3 strict separately, group relevance unit.
    """
    n = len(task_results)
    if n == 0:
        return {
            "n": 0,
            "success_at_1": 0.0, "success_at_3": 0.0, "success_at_5": 0.0,
            "success_at_5_strict_grade3": 0.0, "success_at_5_grade3": 0.0,
            "ndcg_at_5": 0.0, "ndcg_at_10": 0.0, "mrr_at_10": 0.0,
            "success_at_5_count": 0, "success_at_1_count": 0, "success_at_3_count": 0, "success_at_5_strict_grade3_count": 0,
        }
    s1 = sum(success_at_1(tr["retrieved"], tr["golds"]) for tr in task_results)
    s3 = sum(success_at_3(tr["retrieved"], tr["golds"]) for tr in task_results)
    s5 = sum(success_at_5(tr["retrieved"], tr["golds"]) for tr in task_results)
    s5_g3 = sum(success_at_5_strict_grade3(tr["retrieved"], tr["golds"]) for tr in task_results)
    ndcg5s = [ndcg_at_5(tr["retrieved"], tr["golds"]) for tr in task_results]
    ndcg10s = [ndcg_at_10(tr["retrieved"], tr["golds"]) for tr in task_results]
    mrrs = [mrr_at_10(tr["retrieved"], tr["golds"]) for tr in task_results]
    return {
        "n": n,
        "success_at_1": s1 / n,
        "success_at_3": s3 / n,
        "success_at_5": s5 / n,
        "success_at_5_strict_grade3": s5_g3 / n,
        "success_at_5_grade3": s5_g3 / n,
        "success_at_1_count": s1,
        "success_at_3_count": s3,
        "success_at_5_count": s5,
        "success_at_5_strict_grade3_count": s5_g3,
        "ndcg_at_5": sum(ndcg5s) / n,
        "ndcg_at_10": sum(ndcg10s) / n,
        "mrr_at_10": sum(mrrs) / n,
        "mrr_at_10_raw": sum(mrrs) / n,
    }

def compute_oracle_recall(tasks_oracles: list[dict]) -> dict:
    """
    tasks_oracles: list of {dense_pool, sparse_pool, exact_pool, union_pool, golds}
    each pool is ordered list.
    Union@K is set union of per-signal own topK (regression fix C), group-aware.
    Returns dict per signal per k.
    """
    out = {}
    n = len(tasks_oracles)
    for k in [30, 50, 100]:
        for signal in ["dense", "sparse", "exact"]:
            hits = sum(recall_at_k_oracle(t.get(f"{signal}_pool", []), t["golds"], k) for t in tasks_oracles)
            out[f"{signal}_recall_at_{k}"] = hits / n if n else 0.0
            out[f"{signal}_recall_at_{k}_count"] = hits
        union_hits = sum(_union_recall_at_k(t, k) for t in tasks_oracles)
        out[f"union_recall_at_{k}"] = union_hits / n if n else 0.0
        out[f"union_recall_at_{k}_count"] = union_hits
    return out

def compute_slice_diagnostics(task_results: list[dict], slice_key: str) -> dict | str:
    """Per-slice Success@5. slice_key in source/stratum/location. Returns 'unavailable' string if metadata absent (D-026)."""
    has_metadata = False
    for tr in task_results:
        if slice_key == "location_bearing":
            if "location_bearing" in tr and tr["location_bearing"] is not None:
                has_metadata = True
                break
        elif slice_key == "location":
            if "location_bearing" in tr:
                has_metadata = True
                break
        else:
            if slice_key in tr and tr[slice_key] is not None:
                has_metadata = True
                break
            if tr.get(slice_key) is not None:
                has_metadata = True
                break
    if not has_metadata:
        return "unavailable"
    by_slice = defaultdict(list)
    for tr in task_results:
        key = tr.get(slice_key)
        if slice_key == "location_bearing" or slice_key == "location":
            key = "location" if tr.get("location_bearing") else "non_location"
        elif key is None:
            key = "unknown"
        by_slice[str(key)].append(tr)
    out = {}
    for k, lst in sorted(by_slice.items()):
        m = compute_headline_metrics(lst)
        out[k] = {
            "n": m["n"],
            "success_at_1": m["success_at_1"],
            "success_at_3": m["success_at_3"],
            "success_at_5": m["success_at_5"],
            "success_at_5_strict_grade3": m["success_at_5_strict_grade3"],
            "ndcg_at_5": m["ndcg_at_5"],
            "ndcg_at_10": m["ndcg_at_10"],
            "mrr_at_10": m["mrr_at_10"],
        }
    return out

def wilson_interval(p_hat: float, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval without continuity correction."""
    if n == 0:
        return (0.0, 0.0)
    denom = 1 + z*z/n
    centre = p_hat + z*z/(2*n)
    adj = z * math.sqrt(p_hat*(1-p_hat)/n + z*z/(4*n*n))
    lower = (centre - adj) / denom
    upper = (centre + adj) / denom
    return (max(0.0, lower), min(1.0, upper))

def clopper_pearson_interval(successes: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Clopper-Pearson exact via beta quantiles (approx). For tests we use simple."""
    if n == 0:
        return (0.0, 0.0)
    try:
        from scipy.stats import beta as beta_dist
        lower = beta_dist.ppf(alpha/2, successes, n - successes + 1) if successes >0 else 0.0
        upper = beta_dist.ppf(1 - alpha/2, successes + 1, n - successes) if successes < n else 1.0
        return (float(lower), float(upper))
    except Exception:
        return wilson_interval(successes/n, n)
