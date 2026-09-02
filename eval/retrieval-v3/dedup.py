"""Dedup and diversification — greedy, strict > threshold, actual cosine, MMR."""
from __future__ import annotations
import math
from .dense import cosine_similarity

def _actual_cosine(a_vec, b_vec) -> float:
    return cosine_similarity(a_vec, b_vec)

def get_representative_vector(policy: dict, qvec) -> list[float] | None:
    """Get stored representative vector for policy (already selected per query).

    Regression fix B: when qvec is provided, always compute query-nearest chunk
    via actual cosine (select_representative_chunk) with deterministic tie break
    (chunk_index asc, id asc); never fallback to chunk0. Chunk0 fallback only
    when qvec is None. This ensures sparse-only policies use true nearest.
    """
    chunks = policy.get("chunks", [])
    if chunks:
        if qvec is not None:
            from .dense import select_representative_chunk
            best, _ = select_representative_chunk(qvec, chunks)
            return best["embedding"] if best else None
    # Check for precomputed representative only when qvec is None or no chunks
    if "_representative_embedding" in policy:
        return policy["_representative_embedding"]
    if "representative_chunk" in policy and policy["representative_chunk"]:
        ch = policy["representative_chunk"]
        if isinstance(ch, dict) and "embedding" in ch:
            return ch["embedding"]
    if not chunks:
        return None
    # fallback: first chunk only when qvec is None
    return chunks[0].get("embedding")
def dedup_greedy(ranked_pool: list[dict], threshold: float, qvec=None) -> list[dict]:
    """
    Greedy dedup: iterate base final order, retain first, suppress later if max actual cosine > threshold (strict >).
    ranked_pool: list ordered by base final order (final_score desc, source asc, etc.)
    Each entry must have policy with chunks or representative vector.
    threshold: 0.95/0.97/0.98 strict >
    qvec: needed to select representative vector per policy (if not precomputed)
    Returns deduped list in base order (retained only).
    """
    retained = []
    retained_vecs = []  # parallel
    for entry in ranked_pool:
        policy = entry.get("policy") or entry
        # Regression fix B: when qvec is provided, sparse-only must use query-nearest chunk (actual cosine)
        # Never use chunk0 fallback. So prioritize recomputed vector via get_representative_vector when qvec present.
        vec = None
        if qvec is not None:
            vec = get_representative_vector(policy, qvec)
            if vec is None and "representative_chunk" in entry and entry["representative_chunk"] and isinstance(entry["representative_chunk"], dict):
                vec = entry["representative_chunk"].get("embedding")
        else:
            if "representative_chunk" in entry and entry["representative_chunk"] and isinstance(entry["representative_chunk"], dict):
                vec = entry["representative_chunk"].get("embedding")
            if vec is None:
                vec = get_representative_vector(policy, qvec)
        if vec is None:
            # also fallback to entry's policy vector annotation
            if "embedding" in entry:
                vec = entry["embedding"]
        if vec is None:
            # No vector: cannot dedup, retain
            retained.append(entry)
            retained_vecs.append(None)
            continue
        # Check against retained
        suppress = False
        for rv in retained_vecs:
            if rv is None:
                continue
            sim = _actual_cosine(vec, rv)
            if sim > threshold:  # strict >
                suppress = True
                break
        if not suppress:
            retained.append(entry)
            retained_vecs.append(vec)
    return retained

def mmr_select(ranked_pool_deduped: list[dict], lambda_val: float, top_k: int = 30, qvec=None) -> list[dict]:
    """
    MMR greedy selection to top_k.
    If lambda==0.0: unchanged dedup-ordered base final order.
    If lambda==0.3: diversification_score = lambda*final_score - (1-lambda)*max_similarity
    where max_similarity is actual cosine to already selected.
    Tie break by base final rank (smaller base rank wins).
    MMR continues to top_k or exhaustion.
    ranked_pool_deduped: already deduped, ordered by base final order.
    """
    if lambda_val == 0.0:
        return ranked_pool_deduped[:top_k]
    # For lambda >0
    # Need base rank for tie break: index in ranked_pool_deduped
    base_rank = {id(entry): idx for idx, entry in enumerate(ranked_pool_deduped)}
    # Also map entry to vector — regression fix B: qvec present => recomputed nearest
    vec_map = {}
    for entry in ranked_pool_deduped:
        policy = entry.get("policy") or entry
        vec = None
        if qvec is not None:
            vec = get_representative_vector(policy, qvec)
            if vec is None and "representative_chunk" in entry and entry["representative_chunk"] and isinstance(entry["representative_chunk"], dict):
                vec = entry["representative_chunk"].get("embedding")
        else:
            if "representative_chunk" in entry and entry["representative_chunk"] and isinstance(entry["representative_chunk"], dict):
                vec = entry["representative_chunk"].get("embedding")
            if vec is None:
                vec = get_representative_vector(policy, qvec)
        if vec is None and "embedding" in entry:
            vec = entry["embedding"]
        vec_map[id(entry)] = vec

    selected = []
    selected_vecs = []
    candidates = list(ranked_pool_deduped)

    while candidates and len(selected) < top_k:
        best = None
        best_score = None
        best_base_rank = None
        for cand in candidates:
            # compute max similarity to already selected
            vec = vec_map.get(id(cand))
            if not selected:
                max_sim = 0.0
            else:
                if vec is None:
                    max_sim = 0.0
                else:
                    sims = []
                    for sv in selected_vecs:
                        if sv is None or vec is None:
                            sims.append(0.0)
                        else:
                            sims.append(_actual_cosine(vec, sv))
                    max_sim = max(sims) if sims else 0.0
            # diversification_score
            final_score = cand.get("final_score", 0.0)
            # Note: entry may have 'final_score' or 'score'
            div_score = lambda_val * final_score - (1 - lambda_val) * max_sim
            cand_rank = base_rank[id(cand)]
            if best is None or div_score > best_score or (div_score == best_score and cand_rank < best_base_rank):
                best = cand
                best_score = div_score
                best_base_rank = cand_rank
        # select best
        selected.append(best)
        selected_vecs.append(vec_map.get(id(best)))
        candidates.remove(best)
    return selected

def full_top30_pipeline(ranked_pool: list[dict], dedup_threshold: float, lambda_val: float, qvec=None) -> list[dict]:
    """Combine dedup then MMR to produce final top30."""
    deduped = dedup_greedy(ranked_pool, dedup_threshold, qvec=qvec)
    final = mmr_select(deduped, lambda_val, top_k=30, qvec=qvec)
    return final
