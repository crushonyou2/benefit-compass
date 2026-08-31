"""Cycle3 canonical dev runner — normative implementation (D-011, prereg-v1).

This module implements the Cycle3 canonical dev batch without executing
retrieval/DB/model/embedding/benchmark. It encodes the exact prereg contracts
so that static/pure tests can verify drift before any execution.

HARD SCOPE (this logical stage is implementation + pure/static tests only):
- No real retrieval/DB/query/model/embedding/benchmark/latency execution.
- No production ml-service behavior change (diff 0).
- No new candidate/K/selection rule/threshold/SQL semantics beyond prereg.
- No result artifact generation beyond the runner's own provenance helpers.

Contracts frozen from prereg-v1.json + RETRIEVAL_V2_CYCLE3_PREREG.md:
- Baseline (D-003) + exactly c3e1-vector-pool-128 (K=128),
  c3e2-vector-pool-256 (K=256), c3e3-vector-pool-512 (K=512), final n=30.
- Exact normative SQL: bounded vector pool LIMIT K first, lexical only on that K,
  deterministic vector-pool tie-break.
- candidate-v2 lexical semantics / D-003 / D-004 / D-007 preserved.
  RERANK=0, final n=30, strip_region/lexical behavior invariant.
- Cosine threshold post-LIMIT (Python filter after LIMIT 30).
- Single canonical dev batch (baseline+3 together); single-batch identity/guard.
- Quality selection rule prereg 그대로; quality-selectable -> paired latency gate
  (predefined paired latency, but no actual latency execution in this stage).
- Cycle3 audit fail-closed integration: canonical run start/end,
  protected dev access start/end, exact set SHA/session/token verification.
  Real audit log is NOT written in this implementation stage (tests use temp audit).
- Holdout evaluation/access path blocked until candidate freeze + independent review
  + user explicit approval.

All helpers are deterministic and pure where possible.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

# Ensure ml-service and eval importable for contract checks
sys.path.insert(0, str(ROOT / "ml-service"))
sys.path.insert(0, str(ROOT / "eval"))

# ---------------------------------------------------------------------------
# Frozen constants (prereg-v1.json authoritative)
# ---------------------------------------------------------------------------

PREREG_VERSION = "v1"
PREREG_SCHEMA_VERSION = 1
PREREG_FILE = ROOT / "eval" / "retrieval-v2" / "cycle3" / "prereg-v1.json"
PREREG_SHA256 = "18b6c997eb71a8cdff36d84ff46b5bbb6b699874ff6d0fccd18636f00268e156"

# D-003 production contract
D003_CANDIDATES = 30
D003_COSINE_MIN = 0.78
D003_LEXICAL_BIAS = 0.01
D003_RERANK = 0
D003_EMBED_MODEL = "intfloat/multilingual-e5-base"

# Cycle3 canonical candidate set
BASELINE_ID = "baseline"
CANDIDATE_IDS = (
    "c3e1-vector-pool-128",
    "c3e2-vector-pool-256",
    "c3e3-vector-pool-512",
)
ALL_CANONICAL_IDS = (BASELINE_ID,) + CANDIDATE_IDS

POOL_K_BY_ID: dict[str, int] = {
    "c3e1-vector-pool-128": 128,
    "c3e2-vector-pool-256": 256,
    "c3e3-vector-pool-512": 512,
}

FINAL_N = 30

# Batch identity — single canonical dev batch only
BATCH_ID = "cycle3-canonical-dev-v1"
RUNNER_ID = "cycle3-canonical-dev-runner"
CANONICAL_DEV_OUTPUT_REL = "eval/retrieval-v2/cycle3/canonical-dev/canonical-dev-result.json"
CANONICAL_DEV_AUDIT_REL = "eval/retrieval-v2/cycle3/audit/events.jsonl"

# Fresh dev 36 provenance (aggregate only, no plaintext)
EXPECTED_DEV_SHA256 = "3791368f4722b612058b7a005e17bf5f1caae4ac0437daa9d44ff28f28ca260c"
EXPECTED_DEV_CASES = 36
EXPECTED_DEV_YOUTH = 18
EXPECTED_DEV_GOV24 = 18

# Holdout gating — blocked until freeze+review+approval
HOLDOUT_BLOCKED_MESSAGE = (
    "holdout evaluation/access blocked: candidate freeze + independent review "
    "+ user explicit approval required before any holdout plaintext open or "
    "holdout evaluation (D-011 §6-7)"
)

# ---------------------------------------------------------------------------
# Provenance / audit helpers (wrappers, no real writes in this stage)
# ---------------------------------------------------------------------------

try:
    from retrieval_v2.cycle3_audit import (
        append_event,
        verify_holdout_access_allowed,
        read_and_verify_chain,
        AuditError,
        AuditChainError,
    )
except Exception:  # pragma: no cover - importability guard
    append_event = None  # type: ignore
    verify_holdout_access_allowed = None  # type: ignore
    read_and_verify_chain = None  # type: ignore
    AuditError = RuntimeError  # type: ignore
    AuditChainError = RuntimeError  # type: ignore

try:
    from retrieval_v2.cycle3_fingerprint import FINGERPRINT_VERSION, NORMALIZATION_SPEC
except Exception:  # pragma: no cover
    FINGERPRINT_VERSION = "v1"
    NORMALIZATION_SPEC = "NFC + strip + collapse_whitespace + casefold(lower)"

# ---------------------------------------------------------------------------
# Candidate registry (immutable)
# ---------------------------------------------------------------------------

def get_candidate_registry() -> dict[str, dict[str, Any]]:
    """Return frozen registry for all canonical ids.

    Each entry contains exactly the prereg fields:
    candidate_id, pool_k (None for baseline), final_n, lexical_terms,
    youth_bias, lexical_bias, cosine_min, rerank, region_search, base.
    The returned dict is a deep-frozen snapshot; callers must not mutate
    global state (we return a copy).
    """
    reg: dict[str, dict[str, Any]] = {}
    # baseline (D-003) — lexical is original overlap terms (not rewrite)
    reg[BASELINE_ID] = {
        "candidate_id": BASELINE_ID,
        "pool_k": None,
        "final_n": FINAL_N,
        "lexical_terms": "lexical_overlap_terms(strip_region(raw))",
        "youth_bias": "youth_source_bias(strip_region(raw))",
        "lexical_bias": D003_LEXICAL_BIAS,
        "cosine_min": D003_COSINE_MIN,
        "rerank": D003_RERANK,
        "region_search": False,
        "base": "D-003 production retrieval contract",
    }
    for cid in CANDIDATE_IDS:
        reg[cid] = {
            "candidate_id": cid,
            "pool_k": POOL_K_BY_ID[cid],
            "final_n": FINAL_N,
            "lexical_terms": "lexical_overlap_terms_rewrite(strip_region(raw))",
            "youth_bias": "youth_source_bias(strip_region(raw))",
            "lexical_bias": D003_LEXICAL_BIAS,
            "cosine_min": D003_COSINE_MIN,
            "rerank": D003_RERANK,
            "region_search": False,
            "base": "candidate-v2 lexical-rewrite-v1",
        }
    return reg


def validate_candidate_registry(registry: dict[str, dict[str, Any]] | None = None) -> None:
    """Fail-closed registry validation.

    Checks:
    - exactly 4 entries (baseline + 3 pool candidates)
    - candidate_ids exact
    - pool_k exact 128/256/512, baseline None
    - final_n 30, rerank 0, lexical_bias 0.01, cosine_min 0.78
    - lexical_terms/youth_bias strings exact
    - region_search False, base correct
    """
    reg = registry if registry is not None else get_candidate_registry()
    if set(reg.keys()) != set(ALL_CANONICAL_IDS):
        raise ValueError(f"registry keys mismatch: got {sorted(reg.keys())} expected {sorted(ALL_CANONICAL_IDS)}")
    if len(reg) != 4:
        raise ValueError(f"registry must have exactly 4 entries, got {len(reg)}")
    for cid in CANDIDATE_IDS:
        ent = reg[cid]
        if ent["pool_k"] not in (128, 256, 512):
            raise ValueError(f"{cid} pool_k invalid: {ent['pool_k']}")
        if ent["pool_k"] != POOL_K_BY_ID[cid]:
            raise ValueError(f"{cid} pool_k drift: {ent['pool_k']} != {POOL_K_BY_ID[cid]}")
        _assert_common_fields(cid, ent)
        if ent["base"] != "candidate-v2 lexical-rewrite-v1":
            raise ValueError(f"{cid} base drift: {ent['base']!r}")
    # baseline
    b = reg[BASELINE_ID]
    if b["pool_k"] is not None:
        raise ValueError(f"baseline pool_k must be None, got {b['pool_k']}")
    _assert_common_fields(BASELINE_ID, b)
    if b["base"] != "D-003 production retrieval contract":
        raise ValueError(f"baseline base drift: {b['base']!r}")


def _assert_common_fields(cid: str, ent: dict[str, Any]) -> None:
    if ent["candidate_id"] != cid:
        raise ValueError(f"candidate_id field mismatch for {cid}: {ent['candidate_id']!r}")
    if ent["final_n"] != FINAL_N:
        raise ValueError(f"{cid} final_n drift: {ent['final_n']} != {FINAL_N}")
    if ent["rerank"] != D003_RERANK:
        raise ValueError(f"{cid} rerank drift: {ent['rerank']} != {D003_RERANK}")
    if ent["lexical_bias"] != D003_LEXICAL_BIAS:
        raise ValueError(f"{cid} lexical_bias drift: {ent['lexical_bias']} != {D003_LEXICAL_BIAS}")
    if ent["cosine_min"] != D003_COSINE_MIN:
        raise ValueError(f"{cid} cosine_min drift: {ent['cosine_min']} != {D003_COSINE_MIN}")
    expected_lex = "lexical_overlap_terms(strip_region(raw))" if cid == BASELINE_ID else "lexical_overlap_terms_rewrite(strip_region(raw))"
    if ent["lexical_terms"] != expected_lex:
        raise ValueError(f"{cid} lexical_terms drift: {ent['lexical_terms']!r} != {expected_lex!r}")
    if ent["youth_bias"] != "youth_source_bias(strip_region(raw))":
        raise ValueError(f"{cid} youth_bias drift: {ent['youth_bias']!r}")
    if ent["region_search"] is not False:
        raise ValueError(f"{cid} region_search must be False, got {ent['region_search']}")

# ---------------------------------------------------------------------------
# SQL semantics (normative)
# ---------------------------------------------------------------------------

# Exact normative template (must match prereg 5.2). We expose a builder that
# returns the sql with placeholders %(pool_k)s etc. Tests verify byte-patterns.

BASELINE_SQL = """WITH nearest AS (
  SELECT DISTINCT ON (p.id) p.id, p.source, p.source_id, p.title, p.org,
         p.support_content, p.apply_method, p.apply_url, p.age_min, p.age_max,
         p.income_etc, (c.embedding <=> %(vec)s::vector) AS dist
  FROM policy_chunk c
  JOIN policy p ON p.id = c.policy_id
  WHERE ( %(age)s IS NULL OR p.age_limit_yn IS NOT TRUE
          OR %(age)s BETWEEN p.age_min AND p.age_max )
    AND ( %(rp)s IS NULL
          OR EXISTS (SELECT 1 FROM unnest(p.region_codes) rc WHERE rc LIKE %(rp)s) )
    AND ( p.biz_end IS NULL OR p.biz_end >= CURRENT_DATE )
  ORDER BY p.id, c.embedding <=> %(vec)s::vector
),
lexical AS (
  SELECT p.id, count(DISTINCT term) AS lexical_overlap
  FROM policy p
  CROSS JOIN LATERAL unnest(%(lexical_terms)s::text[]) AS term
  WHERE ( %(age)s IS NULL OR p.age_limit_yn IS NOT TRUE
          OR %(age)s BETWEEN p.age_min AND p.age_max )
    AND ( %(rp)s IS NULL
          OR EXISTS (SELECT 1 FROM unnest(p.region_codes) rc WHERE rc LIKE %(rp)s) )
    AND ( p.biz_end IS NULL OR p.biz_end >= CURRENT_DATE )
    AND concat_ws(' ', p.title, p.summary, p.support_content,
                  p.add_qualify, p.keywords)
        ILIKE '%%' || term || '%%'
  GROUP BY p.id
)
SELECT t.source, t.source_id, t.title, t.org, t.support_content, t.apply_method,
       t.apply_url, t.age_min, t.age_max, t.income_etc, 1 - t.dist AS score
FROM nearest t
LEFT JOIN lexical l ON l.id = t.id
ORDER BY t.dist - CASE WHEN t.source = 'youth' THEN %(youth_bias)s ELSE 0 END
             - %(lexical_bias)s * coalesce(l.lexical_overlap, 0),
         t.dist, t.source, t.source_id
LIMIT %(n)s"""

VECTOR_POOL_SQL_TEMPLATE = """WITH nearest AS (
  SELECT DISTINCT ON (p.id) p.id, p.source, p.source_id, p.title, p.org,
         p.support_content, p.apply_method, p.apply_url, p.age_min, p.age_max,
         p.income_etc, (c.embedding <=> %(vec)s::vector) AS dist
  FROM policy_chunk c
  JOIN policy p ON p.id = c.policy_id
  WHERE ( %(age)s IS NULL OR p.age_limit_yn IS NOT TRUE
          OR %(age)s BETWEEN p.age_min AND p.age_max )
    AND ( %(rp)s IS NULL
          OR EXISTS (SELECT 1 FROM unnest(p.region_codes) rc WHERE rc LIKE %(rp)s) )
    AND ( p.biz_end IS NULL OR p.biz_end >= CURRENT_DATE )
  ORDER BY p.id, c.embedding <=> %(vec)s::vector
),
vector_pool AS (
  SELECT * FROM nearest ORDER BY dist ASC LIMIT %(pool_k)s
),
lexical AS (
  SELECT p.id, count(DISTINCT term) AS lexical_overlap
  FROM policy p
  JOIN vector_pool vp ON vp.id = p.id
  CROSS JOIN LATERAL unnest(%(lexical_terms)s::text[]) AS term
  WHERE concat_ws(' ', p.title, p.summary, p.support_content,
                  p.add_qualify, p.keywords)
        ILIKE '%%' || term || '%%'
  GROUP BY p.id
)
SELECT t.source, t.source_id, t.title, t.org, t.support_content, t.apply_method,
       t.apply_url, t.age_min, t.age_max, t.income_etc, 1 - t.dist AS score
FROM vector_pool t
LEFT JOIN lexical l ON l.id = t.id
ORDER BY t.dist - CASE WHEN t.source = 'youth' THEN %(youth_bias)s ELSE 0 END
             - %(lexical_bias)s * coalesce(l.lexical_overlap, 0),
         t.dist, t.source, t.source_id
LIMIT %(n)s"""

# Alternative acceptable formulation notes (prereg 5.2 Notes):
# lexical that re-applies eligible filters AND p.id IN (SELECT id FROM vector_pool)
# is acceptable if byte-identical semantics. We keep the join form as canonical.


def get_sql_for_candidate(candidate_id: str) -> str:
    """Return exact normative SQL for candidate_id.

    - baseline -> BASELINE_SQL (eligible-full lexical)
    - c3e* -> VECTOR_POOL_SQL_TEMPLATE (bounded pool then lexical on pool only)
    Fail-closed on unknown id or K drift.
    """
    validate_candidate_registry()
    if candidate_id == BASELINE_ID:
        return BASELINE_SQL
    if candidate_id not in POOL_K_BY_ID:
        raise ValueError(f"unknown candidate_id {candidate_id!r}; must be one of {ALL_CANONICAL_IDS}")
    # Validate requested K exact
    k = POOL_K_BY_ID[candidate_id]
    if k not in (128, 256, 512):
        raise ValueError(f"candidate {candidate_id} K drift: {k}")
    return VECTOR_POOL_SQL_TEMPLATE


def validate_sql_semantics(sql: str, candidate_id: str) -> None:
    """Fail-closed SQL semantics validator.

    Ensures for vector-pool candidates:
    - nearest CTE present with DISTINCT ON (p.id) + ORDER BY p.id, c.embedding <=> ...
    - vector_pool CTE present with ORDER BY dist ASC LIMIT %(pool_k)s
    - lexical CTE joins vector_pool (JOIN vector_pool vp ON vp.id = p.id)
      and does NOT re-apply eligible on full eligible (lexical only on pool)
    - no region_filter / reranker / threshold in SQL
    - final ORDER BY includes youth_bias/lexical_bias/dist/source/source_id and LIMIT %(n)s
    - pool K placeholder present
    - For baseline, no vector_pool, lexical is full-eligible cross-join.
    """
    if candidate_id == BASELINE_ID:
        if "vector_pool" in sql:
            raise ValueError("baseline SQL must not contain vector_pool")
        if "SELECT DISTINCT ON (p.id)" not in sql:
            raise ValueError("baseline SQL missing DISTINCT ON")
        if "FROM nearest t" not in sql:
            raise ValueError("baseline SQL final FROM must be nearest")
        if "count(DISTINCT term)" not in sql:
            raise ValueError("baseline SQL missing lexical count(DISTINCT term)")
        if "ORDER BY t.dist - CASE WHEN t.source = 'youth'" not in sql:
            raise ValueError("baseline SQL missing youth/lexical ordering")
        if "LIMIT %(n)s" not in sql:
            raise ValueError("baseline SQL missing LIMIT %(n)s")
        if "ILIKE '%%' || term || '%%'" not in sql:
            raise ValueError("baseline SQL missing ILIKE lexical join")
        return
    # vector-pool candidates
    if candidate_id not in POOL_K_BY_ID:
        raise ValueError(f"unknown candidate {candidate_id!r}")
    if "vector_pool AS (" not in sql:
        raise ValueError(f"{candidate_id} SQL missing vector_pool CTE")
    if "ORDER BY dist ASC LIMIT %(pool_k)s" not in sql:
        raise ValueError(f"{candidate_id} SQL missing bounded pool LIMIT")
    if "JOIN vector_pool vp ON vp.id = p.id" not in sql:
        raise ValueError(f"{candidate_id} SQL lexical must join vector_pool (K-only)")
    if "CROSS JOIN LATERAL unnest(%(lexical_terms)s" not in sql:
        raise ValueError(f"{candidate_id} SQL missing lexical LATERAL unnest")
    if "count(DISTINCT term)" not in sql:
        raise ValueError(f"{candidate_id} SQL missing count(DISTINCT term)")
    if "FROM vector_pool t" not in sql:
        raise ValueError(f"{candidate_id} SQL final FROM must be vector_pool")
    if "ORDER BY t.dist - CASE WHEN t.source = 'youth' THEN %(youth_bias)s" not in sql:
        raise ValueError(f"{candidate_id} SQL missing youth/lexical ordering")
    if "t.dist, t.source, t.source_id" not in sql:
        raise ValueError(f"{candidate_id} SQL missing deterministic tie-break (dist, source, source_id)")
    if "LIMIT %(n)s" not in sql:
        raise ValueError(f"{candidate_id} SQL missing final LIMIT %(n)s")
    if sql.count("vector_pool") < 3:
        raise ValueError(f"{candidate_id} SQL vector_pool reference count too low (expected >=3)")
    # Lexical must NOT be computed on full eligible for pool candidates (ensured by join)
    # No region_filter / reranker in SQL
    if "region_filter" in sql.lower() or "rerank" in sql.lower():
        raise ValueError(f"{candidate_id} SQL must not contain region_filter/rerank")


def get_pool_k(candidate_id: str) -> int | None:
    if candidate_id == BASELINE_ID:
        return None
    if candidate_id not in POOL_K_BY_ID:
        raise ValueError(f"unknown candidate {candidate_id!r}")
    return POOL_K_BY_ID[candidate_id]


def assert_rp_is_null(rp_value: Any) -> None:
    if rp_value is not None:
        raise ValueError(f"public region search disabled: rp must be NULL, got {rp_value!r}")


# ---------------------------------------------------------------------------
# Query preprocessing (strip_region / lexical) — delegate to canonical impl
# ---------------------------------------------------------------------------

def strip_region_for_runner(raw: str) -> str:
    """Delegate to ml-service/app.py:strip_region (never reimplement)."""
    import app as ml_app  # type: ignore
    return ml_app.strip_region(raw)


def lexical_terms_for_runner(raw: str, candidate_id: str | None = None) -> list[str]:
    """Lexical terms = rewrite for candidates, original for baseline.

    - baseline (candidate_id == 'baseline' or is_baseline) -> lexical_overlap_terms(strip_region(raw))
    - candidates (c3e*) -> lexical_overlap_terms_rewrite(strip_region(raw))
    Delegates to canonical impls, never reimplements.
    Default (candidate_id None) returns rewrite (candidate) for backward compatibility.
    """
    stripped = strip_region_for_runner(raw)
    if candidate_id == BASELINE_ID:
        from source_ranking import lexical_overlap_terms  # type: ignore
        return lexical_overlap_terms(stripped)
    from retrieval_v2.candidate_lexical_rewrite import lexical_overlap_terms_rewrite  # type: ignore
    return lexical_overlap_terms_rewrite(stripped)


def baseline_lexical_terms_for_runner(raw: str) -> list[str]:
    """Explicit baseline helper (original terms)."""
    return lexical_terms_for_runner(raw, candidate_id=BASELINE_ID)


def youth_bias_for_runner(raw: str) -> float:
    """Youth bias = youth_source_bias(strip_region(raw)) (Gov24 suppressed)."""
    from source_ranking import youth_source_bias  # type: ignore
    stripped = strip_region_for_runner(raw)
    return youth_source_bias(stripped)


def validate_lexical_terms_semantics(terms: list[str], raw: str, candidate_id: str | None = None) -> None:
    """Ensure terms are exactly expected helper for candidate_id."""
    expected = lexical_terms_for_runner(raw, candidate_id=candidate_id)
    if terms != expected:
        raise ValueError(f"lexical_terms drift for raw={raw!r} candidate={candidate_id!r}: got {terms!r} expected {expected!r}")


# ---------------------------------------------------------------------------
# Post-LIMIT cosine filter (prereg-fixed: post-LIMIT, not SQL WHERE)
# ---------------------------------------------------------------------------

def apply_cosine_filter(
    candidates: list[dict[str, Any]],
    cosine_min: float = D003_COSINE_MIN,
) -> list[dict[str, Any]]:
    """Post-LIMIT cosine filter: filter LIMIT-30 results by 1-dist >= cosine_min.

    `candidates` is the LIMIT 30 batch (each has 'score' = 1 - dist or 'dist').
    Returns filtered list preserving deterministic order (no reorder).
    This must be called AFTER LIMIT, never inside SQL.
    """
    out: list[dict[str, Any]] = []
    for c in candidates:
        score = c.get("score")
        if score is None:
            # derive from dist if score missing
            dist = c.get("dist")
            if dist is None:
                raise ValueError(f"candidate missing score/dist: {c!r}")
            score = 1.0 - float(dist)
        if float(score) >= float(cosine_min):
            out.append(c)
    return out


def validate_cosine_filter_position(sql: str) -> None:
    """Ensure SQL does NOT contain cosine threshold WHERE (post-LIMIT contract)."""
    lowered = sql.lower()
    if "cosine_min" in lowered or "score >=" in lowered or "1 - t.dist >=" in lowered:
        # SQL itself must not filter by cosine; allow only python postfilter
        # But sql contains `1 - t.dist AS score` which is ok; check for WHERE score
        if "where" in lowered and "0.78" in lowered:
            raise ValueError("cosine filter must be post-LIMIT python, not SQL WHERE")
    # Also ensure no `AND 1 -` in WHERE
    if re.search(r"WHERE.*1\s*-\s*t\.dist", lowered):
        raise ValueError("cosine filter must be post-LIMIT, not SQL WHERE 1 - dist")


# ---------------------------------------------------------------------------
# Deterministic ordering helper (mirrors final ORDER BY)
# ---------------------------------------------------------------------------

def ordering_key(item: dict[str, Any], youth_bias: float, lexical_bias: float, lexical_overlap: int) -> tuple:
    """Return tuple for ORDER BY:

    ORDER BY t.dist - youth_bias*is_youth - lexical_bias*overlap,
             t.dist, t.source, t.source_id

    item must contain 'dist' or 'score' (score = 1 - dist) and 'source','source_id'.
    """
    dist = item.get("dist")
    if dist is None:
        score = item.get("score")
        if score is None:
            raise ValueError(f"item missing dist/score: {item!r}")
        dist = 1.0 - float(score)
    dist = float(dist)
    is_youth = 1 if item.get("source") == "youth" else 0
    primary = dist - (youth_bias if is_youth else 0.0) - lexical_bias * int(lexical_overlap or 0)
    return (primary, dist, str(item.get("source", "")), str(item.get("source_id", "")))


# ---------------------------------------------------------------------------
# Selection rule (prereg §7) — pure
# ---------------------------------------------------------------------------

def quality_selectable(
    baseline_metrics: dict[str, Any],
    candidate_metrics: dict[str, Any],
) -> tuple[bool, dict[str, Any]]:
    """Evaluate prereg quality-selectable (all 4 required).

    baseline_metrics / candidate_metrics are dicts from compute_metrics
    (or paired_result) containing hit@5 / by_source / source_macro_recall@5.
    Returns (is_quality_selectable, diagnostics).
    """
    diag: dict[str, Any] = {}
    # Fail-closed: by_source must contain both youth and gov24 with hit@5
    for name, m in [("baseline", baseline_metrics), ("candidate", candidate_metrics)]:
        if not isinstance(m.get("by_source"), dict):
            raise ValueError(f"{name} metrics missing by_source (fail-closed)")
        if "youth" not in m["by_source"] or "gov24" not in m["by_source"]:
            raise ValueError(f"{name} by_source must contain youth and gov24")
        for src in ("youth", "gov24"):
            if "hit@5" not in m["by_source"][src]:
                raise ValueError(f"{name} by_source[{src}] missing hit@5")
    if "source_macro_recall@5" not in baseline_metrics or "source_macro_recall@5" not in candidate_metrics:
        raise ValueError("metrics missing source_macro_recall@5 (fail-closed)")

    b_macro = float(baseline_metrics["source_macro_recall@5"])
    c_macro = float(candidate_metrics["source_macro_recall@5"])

    b_hit5 = int(baseline_metrics.get("hit@5", 0))
    c_hit5 = int(candidate_metrics.get("hit@5", 0))
    net_hit5 = c_hit5 - b_hit5

    b_youth_hit5 = int(baseline_metrics["by_source"]["youth"]["hit@5"])
    c_youth_hit5 = int(candidate_metrics["by_source"]["youth"]["hit@5"])
    b_gov24_hit5 = int(baseline_metrics["by_source"]["gov24"]["hit@5"])
    c_gov24_hit5 = int(candidate_metrics["by_source"]["gov24"]["hit@5"])
    cond_macro = float(c_macro) > float(b_macro)
    cond_net = net_hit5 >= 2
    cond_youth = c_youth_hit5 >= b_youth_hit5
    cond_gov24 = c_gov24_hit5 >= b_gov24_hit5

    diag.update({
        "baseline_macro_R5": float(b_macro),
        "candidate_macro_R5": float(c_macro),
        "baseline_hit5": b_hit5,
        "candidate_hit5": c_hit5,
        "net_hit5": net_hit5,
        "baseline_youth_hit5": b_youth_hit5,
        "candidate_youth_hit5": c_youth_hit5,
        "baseline_gov24_hit5": b_gov24_hit5,
        "candidate_gov24_hit5": c_gov24_hit5,
        "checks": {
            "macro_gt": bool(cond_macro),
            "net_ge_2": bool(cond_net),
            "youth_no_regression": bool(cond_youth),
            "gov24_no_regression": bool(cond_gov24),
        },
    })
    is_q = bool(cond_macro and cond_net and cond_youth and cond_gov24)
    diag["quality_selectable"] = is_q
    return is_q, diag


def paired_net_from_ranks(baseline_ranks: list[int], candidate_ranks: list[int], k: int = 5) -> tuple[int, int, int]:
    """Compute gains/losses/net for hit@k (paired)."""
    if len(baseline_ranks) != len(candidate_ranks):
        raise ValueError("rank length mismatch")
    gains = sum(1 for b, c in zip(baseline_ranks, candidate_ranks) if (b == 0 or b > k) and (1 <= c <= k))
    losses = sum(1 for b, c in zip(baseline_ranks, candidate_ranks) if (1 <= b <= k) and (c == 0 or c > k))
    return gains, losses, gains - losses


def dev_selectable(
    baseline_metrics: dict[str, Any],
    candidate_metrics: dict[str, Any],
    baseline_p95: float | None,
    candidate_p95: float | None,
) -> tuple[bool, dict[str, Any]]:
    """Full DEV_SELECTABLE = quality_selectable AND latency_gate.

    latency_gate: candidate p95 <= baseline p95, same dev query set.
    Applies only to quality-selectable candidates; if not quality_selectable,
    dev_selectable is False regardless of latency (code boundary).
    This stage does NOT execute real latency; callers pass pre-measured or None.
    If either p95 is None, latency_gate is considered NOT EVALUATED and
    dev_selectable is False with diagnostic.
    """
    is_q, qdiag = quality_selectable(baseline_metrics, candidate_metrics)
    diag: dict[str, Any] = {"quality": qdiag}
    if not is_q:
        diag["latency_gate"] = {"applicable": False, "reason": "not quality-selectable, latency not evaluated (boundary)"}
        diag["dev_selectable"] = False
        return False, diag
    # quality-selectable -> latency gate required
    if baseline_p95 is None or candidate_p95 is None:
        diag["latency_gate"] = {
            "applicable": True,
            "baseline_p95": baseline_p95,
            "candidate_p95": candidate_p95,
            "pass": False,
            "reason": "latency not measured in this stage (no real benchmark) or missing; dev_selectable false",
        }
        diag["dev_selectable"] = False
        return False, diag
    latency_pass = float(candidate_p95) <= float(baseline_p95)
    diag["latency_gate"] = {
        "applicable": True,
        "baseline_p95": float(baseline_p95),
        "candidate_p95": float(candidate_p95),
        "pass": bool(latency_pass),
        "delta_p95": float(candidate_p95) - float(baseline_p95),
    }
    is_dev = bool(is_q and latency_pass)
    diag["dev_selectable"] = is_dev
    return is_dev, diag


def tie_break_sort_key(
    candidate_id: str,
    net_hit5: int,
    macro_r5: float,
    p95_delta: float,
) -> tuple:
    """Return sort key for prereg tie-break (smaller is better for final pick).

    Tie-break order (prereg §7):
    1. higher net hit@5  -> sort -net
    2. higher macro R@5  -> sort -macro
    3. lower p95 delta   -> sort delta
    4. smaller K         -> sort K
    """
    k = POOL_K_BY_ID.get(candidate_id, 9999)
    return (-int(net_hit5), -float(macro_r5), float(p95_delta), int(k), candidate_id)


# ---------------------------------------------------------------------------
# Batch identity / single-batch guard
# ---------------------------------------------------------------------------

def validate_single_batch_request(
    requested_ids: list[str],
    output_path: str | pathlib.Path | None = None,
) -> None:
    """Fail-closed single-batch guard.

    - requested_ids must be exactly ALL_CANONICAL_IDS (order-insensitive, but
      canonical order is enforced for provenance).
    - No subset, no extra, no new K, no individual rerun.
    - If output_path exists on filesystem, raise (already executed batch).
    - This prevents result-post individual re-execution / new K / new candidate.
    """
    req_set = set(requested_ids)
    expected_set = set(ALL_CANONICAL_IDS)
    if req_set != expected_set:
        raise ValueError(
            f"single canonical batch must request exactly {sorted(expected_set)}, "
            f"got {sorted(req_set)} — individual rerun / new K / new candidate not allowed (batch identity guard)"
        )
    if len(requested_ids) != len(ALL_CANONICAL_IDS):
        raise ValueError(f"batch must have exactly {len(ALL_CANONICAL_IDS)} entries, got {len(requested_ids)}")
    # Enforce canonical order for deterministic provenance (optional strict)
    # Allow any order for guard but log canonical order
    if output_path is not None:
        p = pathlib.Path(output_path)
        if p.exists():
            raise FileExistsError(
                f"canonical dev result already exists at {p} — single batch guard: "
                "result after inspection forbids re-execution / new K / new candidate (prereg immutable_after_dev_inspection)"
            )


def get_batch_provenance() -> dict[str, Any]:
    """Return batch identity provenance snippet (for result file)."""
    return {
        "batch_id": BATCH_ID,
        "runner_id": RUNNER_ID,
        "prereg_version": PREREG_VERSION,
        "prereg_file_sha256": PREREG_SHA256,
        "candidate_ids": list(ALL_CANONICAL_IDS),
        "pool_k_by_id": dict(POOL_K_BY_ID),
        "final_n": FINAL_N,
        "single_batch": True,
        "immutable_after_dev_inspection": True,
    }


# ---------------------------------------------------------------------------
# Audit integration (fail-closed, temp-audit for tests)
# ---------------------------------------------------------------------------

def require_protected_dev_access_grant(
    log_path: str | pathlib.Path,
    set_sha: str,
    session_id: str,
    expected_event_hash: str | None = None,
) -> dict[str, Any]:
    """Demand verified protected_access grant before dev plaintext open.

    Wraps cycle3_audit.verify_holdout_access_allowed(dev) with fail-closed.
    - set_sha must be exactly EXPECTED_DEV_SHA256 (pinned, not caller arbitrary).
    - session_id must be non-empty exact.
    - expected_event_hash if supplied must match latest grant's event_hash.
    - Raises AuditError / AuditChainError on stale/failure/no-grant.
    This is called IMMEDIATELY before opening dev evalset.jsonl (real path).
    Tests exercise stale/failure/no-grant as mock fail-closed.
    """
    if verify_holdout_access_allowed is None:
        raise RuntimeError("cycle3_audit not importable")
    # Pin to expected dev SHA — caller cannot supply arbitrary SHA to bypass freeze
    if str(set_sha).lower() != EXPECTED_DEV_SHA256.lower():
        raise AuditError(
            f"protected dev access denied: set_sha {str(set_sha)[:8]}... does not match pinned EXPECTED_DEV_SHA256 {EXPECTED_DEV_SHA256[:8]}... (fail-closed pinning)"
        )
    return verify_holdout_access_allowed(
        log_path,
        set_role="dev",
        set_sha=set_sha,
        session_id=session_id,
        expected_event_hash=expected_event_hash,
    )

def append_canonical_run_start(
    log_path: str | pathlib.Path,
    candidate_id: str,
    set_sha: str | None = None,
    runner_id: str | None = None,
    command: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Append run_start event (for real canonical run; NOT called in this stage).

    Tests must use temp log_path + synthetic values; this stage must NOT call
    this function against the real audit log (see HOLDOUT_CANONICAL_RUN guard).
    """
    if append_event is None:
        raise RuntimeError("cycle3_audit not importable")
    return append_event(
        log_path,
        action="run_start",
        candidate_id=candidate_id,
        set_role="dev" if set_sha else "none",
        set_sha=set_sha,
        command=command or f"cycle3-canonical-dev:{candidate_id}",
        runner_id=runner_id or RUNNER_ID,
        outcome="started",
        session_id=session_id,
    )


def append_canonical_run_end(
    log_path: str | pathlib.Path,
    candidate_id: str,
    set_sha: str | None = None,
    runner_id: str | None = None,
    command: str | None = None,
    outcome: str = "success",
    session_id: str | None = None,
) -> dict[str, Any]:
    if append_event is None:
        raise RuntimeError("cycle3_audit not importable")
    return append_event(
        log_path,
        action="run_end",
        candidate_id=candidate_id,
        set_role="dev" if set_sha else "none",
        set_sha=set_sha,
        command=command or f"cycle3-canonical-dev:{candidate_id}",
        runner_id=runner_id or RUNNER_ID,
        outcome=outcome,
        session_id=session_id,
    )


# ---------------------------------------------------------------------------
# Holdout gating
# ---------------------------------------------------------------------------

def assert_holdout_blocked(*, allow_token: str | None = None) -> None:
    """Always raise unless explicit freeze+review+approval token supplied.

    The canonical holdout path is blocked until candidate freeze + independent
    review + user explicit approval (D-011 §6-7). This function enforces it.

    - Without a valid allow_token (and approved marker file), it raises
      RuntimeError with HOLDOUT_BLOCKED_MESSAGE.
    - The allow_token check is intentionally strict: even if caller passes a
      token, we still verify a durable marker file exists. In this repo the
      marker file does NOT exist, so all calls fail-closed as required.
    Tests verify that holdout access without approval raises.
    """
    # Expected approval marker (does not exist in this stage)
    approved_marker = ROOT / "eval" / "retrieval-v2" / "cycle3" / "holdout" / "APPROVED"
    # Also check env explicitly
    env_approved = os.getenv("CYCLE3_HOLDOUT_APPROVED") == "1"
    if allow_token is not None and env_approved and approved_marker.exists():
        # In a real approved stage, caller would supply token = file content
        try:
            expected = approved_marker.read_text(encoding="utf-8").strip()
            if allow_token.strip() == expected and expected:
                return
        except Exception:
            pass
    raise RuntimeError(HOLDOUT_BLOCKED_MESSAGE)


def assert_not_holdout_path(path: str | pathlib.Path) -> None:
    """Fail-closed if path looks like holdout plaintext access."""
    p = str(path)
    if "holdout" in p.lower() and ("evalset" in p.lower() or "plaintext" in p.lower()):
        raise RuntimeError(f"holdout plaintext path blocked in this stage: {p!r} — {HOLDOUT_BLOCKED_MESSAGE}")


# ---------------------------------------------------------------------------
# D-003 contract check
# ---------------------------------------------------------------------------

def assert_d003_contract() -> None:
    """Fail-closed check that ml-service/app.py still satisfies D-003.

    Verifies CANDIDATES, COSINE_MIN, LEXICAL_BIAS, EMBED_MODEL are frozen.
    RERANK is env-controlled (default 1 in local dev); canonical requires 0
    at execution time, but import-time value may be True. We therefore verify
    the frozen canonical constant D003_RERANK == 0 and that ml-service's
    default EMBED_MODEL and thresholds match, without failing on local
    RERANK env default. The runner's execution path must explicitly enforce
    RERANK=0 (e.g., via env or runtime flag) — checked by provenance, not here.
    """
    import app as ml_app  # type: ignore
    from source_ranking import LEXICAL_OVERLAP_BIAS, YOUTH_INTENT_BIAS  # type: ignore

    if ml_app.CANDIDATES != D003_CANDIDATES:
        raise AssertionError(f"D-003 CANDIDATES drift: {ml_app.CANDIDATES} != {D003_CANDIDATES}")
    if D003_RERANK != 0:
        raise AssertionError(f"D-003 RERANK canonical constant drift: {D003_RERANK} != 0")
    if abs(float(ml_app.COSINE_MIN) - D003_COSINE_MIN) > 1e-9:
        raise AssertionError(f"D-003 COSINE_MIN drift: {ml_app.COSINE_MIN} != {D003_COSINE_MIN}")
    if abs(float(LEXICAL_OVERLAP_BIAS) - D003_LEXICAL_BIAS) > 1e-9:
        raise AssertionError(f"D-003 LEXICAL_BIAS drift: {LEXICAL_OVERLAP_BIAS} != {D003_LEXICAL_BIAS}")
    if ml_app.EMBED_MODEL_NAME != D003_EMBED_MODEL:
        raise AssertionError(f"D-003 EMBED_MODEL drift: {ml_app.EMBED_MODEL_NAME!r} != {D003_EMBED_MODEL!r}")
    _ = YOUTH_INTENT_BIAS  # ensure importable

# ---------------------------------------------------------------------------
# Result schema / provenance
# ---------------------------------------------------------------------------

def build_result_skeleton(
    dev_sha256: str = EXPECTED_DEV_SHA256,
    git_head: str | None = None,
    git_dirty: bool | None = None,
) -> dict[str, Any]:
    """Return canonical result skeleton (no per-case metrics yet).

    Includes provenance fields that must be present in final artifact.
    Actual dev batch execution fills per-candidate metrics + per_case ranks.
    """
    # Resolve git provenance lazily
    if git_head is None or git_dirty is None:
        try:
            import subprocess

            head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
            dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], text=True).strip())
            if git_head is None:
                git_head = head
            if git_dirty is None:
                git_dirty = dirty
        except Exception:
            if git_head is None:
                git_head = "unknown"
            if git_dirty is None:
                git_dirty = True

    return {
        "schema_version": 1,
        "prereg_version": PREREG_VERSION,
        "prereg_file_sha256": PREREG_SHA256,
        "batch": get_batch_provenance(),
        "production_contract": {
            "candidates": D003_CANDIDATES,
            "rerank": D003_RERANK,
            "cosine_min": D003_COSINE_MIN,
            "lexical_bias": D003_LEXICAL_BIAS,
            "embed_model": D003_EMBED_MODEL,
            "strip_region": "ml-service/app.py:strip_region",
            "lexical_terms": "eval/retrieval_v2/candidate_lexical_rewrite.py:lexical_overlap_terms_rewrite(strip_region(raw))",
            "youth_bias": "ml-service/source_ranking.py:youth_source_bias(strip_region(raw))",
            "region_search": False,
        },
        "sql_semantics": {
            "eligible_condition": "( %(age)s IS NULL OR p.age_limit_yn IS NOT TRUE OR %(age)s BETWEEN p.age_min AND p.age_max ) AND ( %(rp)s IS NULL OR EXISTS (SELECT 1 FROM unnest(p.region_codes) rc WHERE rc LIKE %(rp)s) ) AND ( p.biz_end IS NULL OR p.biz_end >= CURRENT_DATE )",
            "nearest": "SELECT DISTINCT ON (p.id) ... ORDER BY p.id, c.embedding <=> %(vec)s::vector",
            "vector_pool": "SELECT * FROM nearest ORDER BY dist ASC LIMIT %(pool_k)s",
            "lexical": "SELECT p.id, count(DISTINCT term) AS lexical_overlap FROM policy p JOIN vector_pool vp ON vp.id=p.id CROSS JOIN LATERAL unnest(%(lexical_terms)s::text[]) AS term WHERE ... ILIKE ... GROUP BY p.id",
            "final_order": "ORDER BY t.dist - CASE WHEN t.source='youth' THEN %(youth_bias)s ELSE 0 END - %(lexical_bias)s * coalesce(l.lexical_overlap,0), t.dist, t.source, t.source_id LIMIT %(n)s -- n=30",
            "cosine_filter": "post-LIMIT python apply_cosine_filter (1 - dist >= 0.78)",
        },
        "dev_set": {
            "cases": EXPECTED_DEV_CASES,
            "youth": EXPECTED_DEV_YOUTH,
            "gov24": EXPECTED_DEV_GOV24,
            "sha256": dev_sha256,
            "expected_sha256": EXPECTED_DEV_SHA256,
        },
        "git": {"head": git_head, "dirty": bool(git_dirty)},
        "candidates": list(ALL_CANONICAL_IDS),
        "pool_k_by_id": dict(POOL_K_BY_ID),
        "final_n": FINAL_N,
        # Placeholders filled by real execution:
        "metrics": None,
        "selection": None,
        "latency": None,
    }


def validate_result_schema(result: dict[str, Any]) -> None:
    """Fail-closed validation of canonical result schema (pure)."""
    required_top = ["schema_version", "prereg_version", "batch", "production_contract", "sql_semantics", "dev_set", "candidates", "pool_k_by_id", "final_n"]
    for k in required_top:
        if k not in result:
            raise ValueError(f"result missing required key {k!r}")
    if result["schema_version"] != 1:
        raise ValueError(f"schema_version drift: {result['schema_version']} != 1")
    if result["prereg_version"] != PREREG_VERSION:
        raise ValueError(f"prereg_version drift: {result['prereg_version']!r} != {PREREG_VERSION!r}")
    if result["prereg_file_sha256"] != PREREG_SHA256:
        raise ValueError(f"prereg sha drift: {result['prereg_file_sha256']} != {PREREG_SHA256}")
    batch = result["batch"]
    if batch.get("batch_id") != BATCH_ID:
        raise ValueError(f"batch_id drift: {batch.get('batch_id')!r} != {BATCH_ID!r}")
    if set(batch.get("candidate_ids", [])) != set(ALL_CANONICAL_IDS):
        raise ValueError(f"batch candidate_ids drift: {batch.get('candidate_ids')}")
    if result["final_n"] != FINAL_N:
        raise ValueError(f"final_n drift: {result['final_n']} != {FINAL_N}")
    if result["pool_k_by_id"] != POOL_K_BY_ID:
        raise ValueError(f"pool_k drift: {result['pool_k_by_id']} != {POOL_K_BY_ID}")
    pc = result["production_contract"]
    if pc.get("candidates") != D003_CANDIDATES or pc.get("rerank") != D003_RERANK:
        raise ValueError(f"production_contract drift: {pc}")
    if abs(float(pc.get("cosine_min", -1)) - D003_COSINE_MIN) > 1e-9:
        raise ValueError(f"cosine_min drift: {pc.get('cosine_min')}")
    if abs(float(pc.get("lexical_bias", -1)) - D003_LEXICAL_BIAS) > 1e-9:
        raise ValueError(f"lexical_bias drift: {pc.get('lexical_bias')}")
    if pc.get("embed_model") != D003_EMBED_MODEL:
        raise ValueError(f"embed_model drift: {pc.get('embed_model')}")
    if pc.get("region_search") is not False:
        raise ValueError(f"region_search must be False, got {pc.get('region_search')}")
    ds = result["dev_set"]
    if int(ds.get("cases", -1)) != EXPECTED_DEV_CASES:
        raise ValueError(f"dev cases drift: {ds.get('cases')} != {EXPECTED_DEV_CASES}")
    if str(ds.get("sha256", "")).lower() != EXPECTED_DEV_SHA256.lower():
        raise ValueError(f"dev sha drift: got {ds.get('sha256')!r} expected {EXPECTED_DEV_SHA256!r}")
    if str(ds.get("expected_sha256", "")).lower() != EXPECTED_DEV_SHA256.lower():
        raise ValueError(f"expected_sha256 drift: got {ds.get('expected_sha256')!r} expected {EXPECTED_DEV_SHA256!r}")
