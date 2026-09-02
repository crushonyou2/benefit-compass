"""Exact title/org predicates — frozen semantics."""
from __future__ import annotations
from .normalization import normalize_exact, is_alnum_hangul

def is_exact_title(query: str, title: str) -> bool:
    """
    Frozen: title = equality OR (normalized q substring of title AND len(q)>=4 AND mechanical boundary).
    Mechanical boundary: both sides of match span in title are string boundary or NOT in [0-9A-Za-z가-힣].
    Reverse title-in-query forbidden except equality.
    Single normalization NFC->strip->collapse->casefold applied to both.
    """
    nq = normalize_exact(query)
    nt = normalize_exact(title)
    if nq == nt:
        return True
    if len(nq) < 4:
        return False
    # q must be substring of title
    if nq not in nt:
        return False
    # Check mechanical boundary for any occurrence
    # Search all occurrences
    start = 0
    while True:
        idx = nt.find(nq, start)
        if idx == -1:
            break
        end = idx + len(nq)
        left_ok = (idx == 0) or (not is_alnum_hangul(nt[idx - 1]))
        right_ok = (end == len(nt)) or (not is_alnum_hangul(nt[end]))
        if left_ok and right_ok:
            return True
        start = idx + 1
    return False

def is_exact_org(query: str, org: str) -> bool:
    """
    Frozen: normalized org length>=2 and bidirectional substring (org in q OR q in org).
    Single normalization.
    """
    nq = normalize_exact(query)
    no = normalize_exact(org)
    if len(no) < 2:
        return False
    # Note: if nq is empty after normalization? Then not match (q length may be <2 but org<->q bidirectional)
    # Spec says normalized org length>=2, then bidirectional. No len check on q.
    # But if nq empty, nq in no would be True (empty substring) — avoid.
    if not nq:
        return False
    return (no in nq) or (nq in no)

def exact_scores(query: str, title: str, org: str, title_boost: float, org_boost: float) -> tuple[int, int, float]:
    """Return (is_title, is_org, exact_score)."""
    it = 1 if is_exact_title(query, title) else 0
    io = 1 if is_exact_org(query, org) else 0
    score = title_boost * it + org_boost * io
    return it, io, score
