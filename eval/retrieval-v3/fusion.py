"""Fusion — union vs hybrid_weighted_sum, canonical dedup, exact not injected."""
from __future__ import annotations
from .normalization import youth_source_bias

def _dedup_by_canonical(entries: list[dict]) -> dict[tuple, dict]:
    """Dedup by (source, source_id). Keep first encountered (caller ensures order)."""
    dedup = {}
    for e in entries:
        key = (e["source"], e["source_id"])
        if key not in dedup:
            dedup[key] = e
    return dedup

def fuse_candidates(
    query: str,
    dense_filtered: list[dict],  # already filtered by COSINE_MIN, contains dense_cosine, policy
    sparse_top100: list[dict],   # contains weighted_overlap, sparse_score, policy
    config: dict,
    qvec=None,
    policies_by_key: dict | None = None,  # for hybrid recomputation: map (source,source_id) -> policy + maybe dense_cosine lookup
    # exact boosts computed per policy via exact module; we compute here if needed
    exact_fn=None,
    dense_lookup: dict | None = None,  # map key -> dense_cosine
    sparse_lookup: dict | None = None, # map key -> weighted_overlap etc
) -> list[dict]:
    """
    Returns final pool = (filtered dense top100 UNION sparse top100) deduped, ranked by final_score.
    Fusion distinction:
      union: channel contribution 0 if policy not in that channel's top100
      hybrid_weighted_sum: both dense_cosine and weighted lexical counts computed for every policy in union regardless of origin
    exact/youth always added.
    dense_lookup/sparse_lookup: precomputed maps for fallback when channel missing but hybrid needs recomputation.
    For pure tests without recomputation, hybrid will recompute via provided policies_by_key and helpers if needed; otherwise fallback to 0.
    """
    from .exact import exact_scores as _exact_scores
    from .dense import cosine_similarity
    from .sparse import compute_weighted_lexical_overlap

    exact_title_boost = config.get("exact_title_boost", 0.0)
    exact_org_boost = config.get("exact_org_boost", 0.0)
    dense_weight = config.get("dense_weight", 1.0)
    sparse_weight = config.get("sparse_weight", 0.01)
    fusion_method = config.get("fusion_method", "union")

    # Build union keys
    dense_keys = {(e["source"], e["source_id"]): e for e in dense_filtered}
    sparse_keys = {(e["source"], e["source_id"]): e for e in sparse_top100}

    union_keys = set(dense_keys.keys()) | set(sparse_keys.keys())

    # For hybrid recomputation, need policy objects
    # Build policy map if not supplied: use whichever entry contains policy
    if policies_by_key is None:
        policies_by_key = {}
        for e in dense_filtered:
            policies_by_key[(e["source"], e["source_id"])] = e["policy"]
        for e in sparse_top100:
            policies_by_key[(e["source"], e["source_id"])] = e["policy"]

    # Prepare lookups for dense_cosine and weighted_overlap if not supplied
    if dense_lookup is None:
        dense_lookup = {k: v["dense_cosine"] for k, v in dense_keys.items()}
    if sparse_lookup is None:
        # Use weighted_overlap from sparse entries
        sparse_lookup = {k: v["weighted_overlap"] for k, v in sparse_keys.items()}

    # For hybrid, if policy in union but missing from dense/sparse, we need to compute missing scores
    # We have qvec and policies_by_key to recompute dense_cosine if needed; and for sparse we need query terms
    # If qvec is None or recomputation not possible, we treat missing as 0 for both methods (union behavior)
    # But for hybrid, we attempt recomputation if possible

    # Determine if we can recompute
    can_recompute_dense = qvec is not None
    # For sparse recomputation we need field weights; we can recompute via compute_weighted_lexical_overlap if we have query
    from .normalization import lexical_overlap_terms
    query_terms = lexical_overlap_terms(query) if query else []

    field_weights = {
        "field_weight_title": config.get("field_weight_title", 1.0),
        "field_weight_support_content": config.get("field_weight_support_content", 1.0),
        "field_weight_eligibility": config.get("field_weight_eligibility", 1.0),
    }

    youth_bias = youth_source_bias(query)  # fixed, added to final_score

    fused = []
    for key in union_keys:
        policy = policies_by_key.get(key)
        if policy is None:
            continue
        source, source_id = key
        # dense component
        if fusion_method == "union":
            dense_cos = dense_lookup.get(key, None)
            if dense_cos is None:
                dense_score = 0.0
            else:
                dense_score = dense_weight * dense_cos
            # sparse component
            w_overlap = sparse_lookup.get(key, None)
            if w_overlap is None:
                sparse_score = 0.0
            else:
                sparse_score = sparse_weight * w_overlap
        elif fusion_method == "hybrid_weighted_sum":
            # Both computed regardless of origin
            # Dense: if not in lookup but can recompute, compute actual cosine via representative
            dense_cos = dense_lookup.get(key)
            if dense_cos is None and can_recompute_dense:
                # Recompute per-policy dense cosine from policy chunks
                from .dense import select_representative_chunk
                chunks = policy.get("chunks", [])
                if chunks:
                    _, dense_cos = select_representative_chunk(qvec, chunks)
                else:
                    dense_cos = 0.0
            elif dense_cos is None:
                dense_cos = 0.0
            dense_score = dense_weight * dense_cos

            # Sparse: recompute weighted_overlap irrespective of presence
            w_overlap = sparse_lookup.get(key)
            # For hybrid, recompute always if possible to ensure complete sum (even if present, use provided? But spec says both computed irrespective, so for present we could keep same but recomputed should equal)
            # To satisfy spec, we recompute for all keys when hybrid
            # Compute fresh
            ct, cs, ce, w_recomputed = compute_weighted_lexical_overlap(query_terms, policy, field_weights)
            w_overlap = w_recomputed
            sparse_score = sparse_weight * w_overlap
        else:
            raise ValueError(f"unknown fusion_method {fusion_method!r}")

        # exact
        title = policy.get("title") or ""
        org = policy.get("org") or ""
        if exact_fn:
            it, io, exact_score = exact_fn(query, title, org, exact_title_boost, exact_org_boost)
        else:
            it, io, exact_score = _exact_scores(query, title, org, exact_title_boost, exact_org_boost)

        final_score = dense_score + sparse_score + exact_score + youth_bias

        fused.append({
            "policy": policy,
            "policy_id": policy["id"],
            "source": source,
            "source_id": source_id,
            "dense_cosine": dense_lookup.get(key, dense_cos if fusion_method=="hybrid_weighted_sum" else None),
            "dense_score": dense_score,
            "sparse_score": sparse_score,
            "weighted_overlap": sparse_lookup.get(key, w_overlap if fusion_method=="hybrid_weighted_sum" else None),
            "exact_title": it,
            "exact_org": io,
            "exact_score": exact_score,
            "youth_score": youth_bias,
            "final_score": final_score,
            # preserve representative chunk for dedup later if needed
            "representative_chunk": next((e.get("representative_chunk") for e in dense_filtered if (e["source"], e["source_id"])==key), None)
                      or next((policy.get("chunks", [{}])[0] if policy.get("chunks") else None for _ in [1]), None),
        })

    # Dedup already via union keys; but ensure canonical dedup (already)
    # Ranking before dedup/diversification: final_score desc, source asc, source_id asc, policy.id asc
    fused.sort(key=lambda x: (-x["final_score"], x["source"], x["source_id"], x["policy_id"]))
    return fused
