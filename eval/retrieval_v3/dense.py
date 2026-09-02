"""Dense retrieval — actual cosine, representative chunk, top100, COSINE_MIN placement."""
from __future__ import annotations
import math
from typing import Any

COSINE_MIN = 0.78

def cosine_similarity(a, b) -> float:
    """Actual cosine = dot/(norm(a)*norm(b)). Not raw dot. Handles non-unit vectors."""
    if len(a) != len(b):
        raise ValueError("vector length mismatch")
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)

def dot_product(a, b) -> float:
    return sum(x * y for x, y in zip(a, b))

def select_representative_chunk(qvec, chunks: list[dict]) -> tuple[dict, float]:
    """
    Per-policy representative: chunk minimizing cosine distance (max cosine).
    chunks: list of {embedding, chunk_index, id}
    Tie: smallest chunk_index asc, then smallest id asc. Exact equality only — no epsilon.
    Returns (best_chunk, best_cosine)
    """
    best = None
    best_cos = None
    for ch in chunks:
        emb = ch["embedding"]
        cos = cosine_similarity(qvec, emb)
        if best is None or cos > best_cos:
            best = ch
            best_cos = cos
        elif cos == best_cos:
            # tie break deterministic
            # need to compare chunk_index then id
            if ch.get("chunk_index", 0) < best.get("chunk_index", 0):
                best = ch
                best_cos = cos
            elif ch.get("chunk_index", 0) == best.get("chunk_index", 0):
                if ch.get("id", 0) < best.get("id", 0):
                    best = ch
                    best_cos = cos
    return best, best_cos

def compute_dense_scores(qvec, policies: list[dict]) -> list[dict]:
    """
    policies: list of {id, source, source_id, title, ... , chunks: [{embedding, chunk_index, id}]}
    Returns per-policy dense entries: {policy, dense_cosine, representative_chunk}
    """
    out = []
    for p in policies:
        chunks = p.get("chunks", [])
        if not chunks:
            continue
        best_ch, best_cos = select_representative_chunk(qvec, chunks)
        out.append({
            "policy": p,
            "dense_cosine": best_cos,
            "representative_chunk": best_ch,
            "policy_id": p["id"],
            "source": p["source"],
            "source_id": p["source_id"],
        })
    return out

def dense_top100(qvec, policies: list[dict]) -> list[dict]:
    """Deterministic dense top100: dense_cosine desc, source asc, source_id asc, policy.id asc."""
    scores = compute_dense_scores(qvec, policies)
    scores.sort(key=lambda x: (-x["dense_cosine"], x["source"], x["source_id"], x["policy_id"]))
    return scores[:100]

def filter_dense_by_cosine_min(dense_top100_list: list[dict], threshold: float = COSINE_MIN) -> list[dict]:
    """Apply COSINE_MIN >=0.78 only after dense top100 before union. Strict < removal."""
    # passes when dense_cosine >= threshold
    return [e for e in dense_top100_list if e["dense_cosine"] >= threshold]

def dense_retrieval_pipeline(qvec, policies: list[dict], threshold: float = COSINE_MIN) -> list[dict]:
    """Full pipeline: top100 then filter."""
    top = dense_top100(qvec, policies)
    filtered = filter_dense_by_cosine_min(top, threshold)
    return filtered
