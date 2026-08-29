"""Eval-only lexical rewrite terms for candidate v3 (safe rename of canonical v3).

- Replacement, not additive: if particle stripping succeeds, use rewrite stem only.
- If rewrite stem is stopword, drop the term entirely.
- Pure administrative/josa residue tokens are dropped (see RESIDUE_*).
- strip_region is still used for query, no raw region re-addition.
- Algorithm identical to interrupted v3 candidate_lexical_canonicalization.py;
  only file/function names avoid the reserved substring.
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "ml-service"))
from source_ranking import LEXICAL_STOPWORDS

PARTICLES = [
    "에게서", "으로부터", "에게", "한테", "께", "에서", "으로", "로",
    "은", "는", "이", "가", "을", "를", "의", "에", "와", "과", "도", "만", "부터", "까지",
]
PARTICLES_SORTED = sorted(PARTICLES, key=len, reverse=True)
MIN_STEM_LEN = 2

# Residue classes: pure josa, admin-unit only, admin+particle without proper noun prefix
RESIDUE_PURE = {"에서", "에", "의", "으로", "로", "와", "과", "도", "만", "부터", "까지", "에게", "한테", "께", "에게서", "으로부터"}
ADMIN_UNITS = ["특별자치도", "특별자치시", "특별시", "광역시", "자치도", "도", "시", "군", "구"]

# Build admin+particle residue set: admin alone, admin+particle
RESIDUE_ADMIN = set(ADMIN_UNITS)
for admin in ADMIN_UNITS:
    for p in ["에서", "에", "의", "으로", "로"]:
        RESIDUE_ADMIN.add(admin + p)

# Note: "태안군에서" is NOT in RESIDUE_ADMIN because "태안군" is not in ADMIN_UNITS
# Only pure admin like "시에서" is in there (admin "시" + "에서")


def is_residue(term: str) -> bool:
    if term in RESIDUE_PURE:
        return True
    if term in RESIDUE_ADMIN:
        return True
    return False


def rewrite_term(term: str) -> str | None:
    """Return rewrite stem or None if dropped.

    - If term is residue, drop (return None).
    - Else try particle stripping once; if stem valid (>=2, not stopword) return stem,
      else keep original if not stopword and len>=2 and not residue.
    - If stripped stem is stopword, drop entirely (do not keep original either).
    """
    if is_residue(term):
        return None
    # Try particle stripping
    for p in PARTICLES_SORTED:
        if term.endswith(p) and len(term) > len(p):
            stem = term[: -len(p)]
            if len(stem) >= MIN_STEM_LEN and stem not in LEXICAL_STOPWORDS:
                return stem
            # If stem is stopword, drop the whole term (do not keep original either)
            if stem in LEXICAL_STOPWORDS:
                return None
            # Stripping would make stem too short or stopword, so don't strip, but keep original if valid
            break
    # No stripping or stripping not valid: keep original if valid
    if len(term) >= 2 and term not in LEXICAL_STOPWORDS and not is_residue(term):
        return term
    return None


# Backwards-compatible alias (algorithm identical, name without reserved substring preferred)
canonicalize_term = rewrite_term


def lexical_overlap_terms_rewrite(query: str) -> list[str]:
    """Rewrite terms, deduped, order preserved, no double-counting."""
    terms = re.findall(r"[0-9A-Za-z가-힣]+", query)
    # Filter and rewrite
    rewritten = []
    seen = set()
    for term in terms:
        if len(term) < 2:
            continue
        if term in LEXICAL_STOPWORDS:
            continue
        if is_residue(term):
            continue
        can = rewrite_term(term)
        if can is None:
            continue
        if can not in seen:
            seen.add(can)
            rewritten.append(can)
    return rewritten


# Alias for verification against interrupted v3
lexical_overlap_terms_canonical = lexical_overlap_terms_rewrite
