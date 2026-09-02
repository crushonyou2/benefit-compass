"""Sparse field-weighted retrieval — frozen tokenization, per-field distinct counts."""
from __future__ import annotations
from .normalization import lexical_overlap_terms

def _count_distinct_terms_in_field(terms: list[str], field_text: str) -> int:
    """Distinct term ILIKE field_text (casefold substring)."""
    if not field_text:
        return 0
    ft = field_text.casefold()
    # distinct terms already deduped in input, but ensure
    seen = set()
    count = 0
    for t in terms:
        if t in seen:
            continue
        seen.add(t)
        # ILIKE: term substring in field case-insensitive
        if t.casefold() in ft:
            count += 1
    return count

def compute_weighted_lexical_overlap(terms: list[str], policy: dict, field_weights: dict) -> tuple[int, int, int, float]:
    """
    Returns (count_title, count_support, count_eligibility, weighted_overlap)
    field_weights: {field_weight_title, field_weight_support_content, field_weight_eligibility}
    """
    title = policy.get("title") or ""
    # support_content || ' ' || summary || ' ' || keywords per plan
    support_parts = [policy.get("support_content") or "", policy.get("summary") or "", policy.get("keywords") or ""]
    support_text = " ".join(p for p in support_parts if p)
    # add_qualify || ' ' || income_etc || ' ' || apply_method
    elig_parts = [policy.get("add_qualify") or "", policy.get("income_etc") or "", policy.get("apply_method") or ""]
    eligibility_text = " ".join(p for p in elig_parts if p)

    ct = _count_distinct_terms_in_field(terms, title)
    cs = _count_distinct_terms_in_field(terms, support_text)
    ce = _count_distinct_terms_in_field(terms, eligibility_text)
    w = (field_weights.get("field_weight_title", 1.0) * ct +
         field_weights.get("field_weight_support_content", 1.0) * cs +
         field_weights.get("field_weight_eligibility", 1.0) * ce)
    return ct, cs, ce, w

def compute_sparse_scores(query: str, policies: list[dict], config: dict) -> list[dict]:
    """Per-policy sparse scores using config field_weights and sparse_weight."""
    terms = lexical_overlap_terms(query)  # uses stripped? Caller should pass stripped query; but we also handle raw
    # Actually caller should pre strip_region; we accept whatever query given and compute terms on it
    field_weights = {
        "field_weight_title": config.get("field_weight_title", 1.0),
        "field_weight_support_content": config.get("field_weight_support_content", 1.0),
        "field_weight_eligibility": config.get("field_weight_eligibility", 1.0),
    }
    sparse_weight = config.get("sparse_weight", 0.01)
    out = []
    for p in policies:
        ct, cs, ce, w = compute_weighted_lexical_overlap(terms, p, field_weights)
        sparse_score = sparse_weight * w
        out.append({
            "policy": p,
            "weighted_overlap": w,
            "sparse_score": sparse_score,
            "count_title": ct,
            "count_support": cs,
            "count_eligibility": ce,
            "policy_id": p["id"],
            "source": p["source"],
            "source_id": p["source_id"],
        })
    return out

def sparse_top100(query: str, policies: list[dict], config: dict) -> list[dict]:
    """Deterministic sparse top100: weighted_lexical_overlap desc, source asc, source_id asc, policy.id asc."""
    scores = compute_sparse_scores(query, policies, config)
    scores.sort(key=lambda x: (-x["weighted_overlap"], x["source"], x["source_id"], x["policy_id"]))
    return scores[:100]
