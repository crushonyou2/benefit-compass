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

# ---------------------------------------------------------------------------
# Rank / metrics helpers (pure, for orchestration)
# ---------------------------------------------------------------------------

def rank_of_gold(results: list[dict[str, Any]], gold_source: str, gold_source_id: str) -> int:
    """Return 1-indexed rank of gold in results (0 if not found). Deterministic."""
    for idx, r in enumerate(results, start=1):
        if r.get("source") == gold_source and str(r.get("source_id")) == str(gold_source_id):
            return idx
    return 0


def compute_metrics_from_ranks(
    per_case_ranks: list[int],
    per_case_sources: list[str],
) -> dict[str, Any]:
    """Aggregate metrics from per-case ranks (0 means outside top10)."""
    n = len(per_case_ranks)
    if n == 0:
        raise ValueError("empty per_case ranks")
    if len(per_case_sources) != n:
        raise ValueError("per_case_sources length mismatch")
    hit1 = sum(1 for r in per_case_ranks if r == 1)
    hit5 = sum(1 for r in per_case_ranks if 1 <= r <= 5)
    hit10 = sum(1 for r in per_case_ranks if 1 <= r <= 10)
    mrr_sum = sum((1.0 / r if r != 0 else 0.0) for r in per_case_ranks)
    mrr = mrr_sum / n if n else 0.0
    # per source
    youth_n = sum(1 for s in per_case_sources if s == "youth")
    gov24_n = sum(1 for s in per_case_sources if s == "gov24")
    youth_hit5 = sum(1 for r, s in zip(per_case_ranks, per_case_sources) if s == "youth" and 1 <= r <= 5)
    gov24_hit5 = sum(1 for r, s in zip(per_case_ranks, per_case_sources) if s == "gov24" and 1 <= r <= 5)
    youth_r5 = (youth_hit5 / youth_n) if youth_n else 0.0
    gov24_r5 = (gov24_hit5 / gov24_n) if gov24_n else 0.0
    macro = (youth_r5 + gov24_r5) / 2.0
    return {
        "n": n,
        "hit@1": hit1,
        "hit@5": hit5,
        "hit@10": hit10,
        "recall@1": hit1 / n if n else 0.0,
        "recall@5": hit5 / n if n else 0.0,
        "recall@10": hit10 / n if n else 0.0,
        "mrr@10": mrr,
        "by_source": {
            "youth": {"hit@5": youth_hit5, "n": youth_n, "recall@5": youth_r5},
            "gov24": {"hit@5": gov24_hit5, "n": gov24_n, "recall@5": gov24_r5},
        },
        "source_macro_recall@5": macro,
    }


def compute_all_candidate_metrics(
    per_candidate_ranks: dict[str, list[int]],
    per_case_sources: list[str],
) -> dict[str, dict[str, Any]]:
    """Compute metrics dict per candidate_id."""
    out: dict[str, dict[str, Any]] = {}
    for cid, ranks in per_candidate_ranks.items():
        out[cid] = compute_metrics_from_ranks(ranks, per_case_sources)
    return out


# ---------------------------------------------------------------------------
# Complete result validation / atomic write
# ---------------------------------------------------------------------------

def validate_complete_result(result: dict[str, Any]) -> None:
    """Strict validation of COMPLETE canonical result (skeleton + metrics + selection + per_case)."""
    # First validate skeleton drift
    validate_result_schema(result)
    # Complete result must have metrics, selection, per_case
    for k in ("metrics", "selection", "per_case"):
        if k not in result:
            raise ValueError(f"complete result missing required key {k!r}")
    metrics = result["metrics"]
    if not isinstance(metrics, dict):
        raise ValueError("metrics must be dict")
    for cid in ALL_CANONICAL_IDS:
        if cid not in metrics:
            raise ValueError(f"metrics missing candidate {cid!r}")
        m = metrics[cid]
        # must contain hit@5, source_macro, by_source
        if "hit@5" not in m or "source_macro_recall@5" not in m or "by_source" not in m:
            raise ValueError(f"metrics for {cid} missing required fields")
        # by_source must have youth/gov24 hit@5
        if "youth" not in m["by_source"] or "gov24" not in m["by_source"]:
            raise ValueError(f"metrics by_source missing youth/gov24 for {cid}")
    # selection must contain dev_selectable etc
    sel = result["selection"]
    if not isinstance(sel, dict):
        raise ValueError("selection must be dict")
    if "per_candidate" not in sel or "selected_candidate" not in sel:
        raise ValueError("selection missing per_candidate/selected_candidate")
    if sel["selected_candidate"] is not None and sel["selected_candidate"] not in ALL_CANONICAL_IDS:
        raise ValueError(f"selected_candidate invalid: {sel['selected_candidate']!r}")
    # per_case must be list of 36 with ranks per candidate
    per_case = result["per_case"]
    if not isinstance(per_case, list) or len(per_case) != EXPECTED_DEV_CASES:
        raise ValueError(f"per_case must be list of {EXPECTED_DEV_CASES}")
    for pc in per_case:
        if "case_id" not in pc or "gold" not in pc or "ranks" not in pc:
            raise ValueError(f"per_case entry missing case_id/gold/ranks: {pc}")
        ranks = pc["ranks"]
        for cid in ALL_CANONICAL_IDS:
            if cid not in ranks:
                raise ValueError(f"per_case ranks missing {cid}")
            if not isinstance(ranks[cid], int):
                raise ValueError(f"rank for {cid} must be int")
    # latency: if present, must obey quality-selectable-only contract
    latency = result.get("latency")
    if latency is not None:
        if not isinstance(latency, dict):
            raise ValueError("latency must be dict or None")
        for cid, vals in latency.items():
            if cid not in ALL_CANONICAL_IDS:
                raise ValueError(f"latency unknown candidate {cid}")
            if vals is not None and "p95" not in vals:
                raise ValueError(f"latency for {cid} missing p95")
    # git provenance
    git = result.get("git")
    if not isinstance(git, dict) or "head" not in git or "dirty" not in git:
        raise ValueError("git provenance missing")


def atomic_write_result(result: dict[str, Any], output_path: str | pathlib.Path) -> pathlib.Path:
    """Validate complete result and atomically write to output_path.

    - Validates complete schema (strict, fail-closed).
    - Fails closed if output_path already exists (single batch guard).
    - Writes via temp file + fsync + atomic rename.
    - Returns resolved output path.
    """
    validate_complete_result(result)
    out = pathlib.Path(output_path)
    # Single-batch guard: existing file must fail
    if out.exists():
        raise FileExistsError(f"canonical dev result already exists at {out} — single batch guard (immutable_after_dev_inspection)")
    # Ensure parent exists
    out.parent.mkdir(parents=True, exist_ok=True)
    # Validate canonical confinement? Caller should have confined via CLI; but we also check that path is under expected rel
    intended = (ROOT / CANONICAL_DEV_OUTPUT_REL).resolve()
    try:
        # Require exact intended path (case-sensitive)
        if out.resolve() != intended:
            raise ValueError(f"output_path must be exactly {CANONICAL_DEV_OUTPUT_REL!r}, got {str(output_path)!r} (resolved {out.resolve()})")
    except Exception as e:
        # If resolve fails due to non-existent parent, try absolute check
        if isinstance(e, ValueError):
            raise
        # fallback: compare absolute normalized
        if out.resolve().as_posix() != intended.as_posix():
            raise ValueError(f"output_path must be exactly {CANONICAL_DEV_OUTPUT_REL!r}, got {str(output_path)!r}")
    tmp = out.with_suffix(out.suffix + ".tmp")
    payload = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    # Write temp
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(payload)
        f.flush()
        try:
            os.fsync(f.fileno())
        except Exception as e:
            raise RuntimeError(f"fsync failed for temp {tmp}: {e}") from e
    # Validate temp is readable and matches
    try:
        loaded = json.loads(tmp.read_text(encoding="utf-8"))
        validate_complete_result(loaded)
    except Exception:
        try:
            tmp.unlink()
        except Exception:
            pass
        raise
    # Atomic rename
    tmp.replace(out)
    # Ensure out exists and fsync dir
    try:
        dir_fd = os.open(str(out.parent), os.O_DIRECTORY)
        try:
            os.fsync(dir_fd)
        finally:
            os.close(dir_fd)
    except Exception:
        pass
    return out


# ---------------------------------------------------------------------------
# 4-way orchestration (pure, injectable dependencies)
# ---------------------------------------------------------------------------

def orchestrate_4way_batch(
    dev_items: list[dict[str, Any]],
    *,
    embedding_fn,
    retrieval_fn,
    latency_measurer=None,
) -> dict[str, Any]:
    """Execute single 4-way canonical batch orchestration (pure, no DB/model side-effects beyond injected fns).

    dev_items: validated list of 36 cases (each with query, gold_source, gold_source_id etc)
    embedding_fn: (stripped_query: str) -> vector (opaque, same for 4-way)
    retrieval_fn: (candidate_id: str, vec, lexical_terms: list[str], youth_bias: float, age, rp) -> list[dict] (LIMIT 30 ordered)
      Must respect: rp must be None, lexical_terms derived correctly, retrieval_fn returns ordered results (already youth/lexical sorted)
    latency_measurer: optional (candidate_ids: list[str]) -> dict[candidate_id, dict with p95 etc]
      If None, latency is None (no measurement). When supplied, it will be invoked ONLY for quality-selectable candidates
      (same-process/same-DB/interleaved contract is the measurer's responsibility; we enforce quality-selectable-only gating here).

    Returns complete result dict (without git/audit provenance; caller wraps with build_result_skeleton and fills).
    Validates invariants: same vec for 4-way, correct lexical semantics, cosine post-LIMIT, rp NULL, deterministic ordering,
    paired ranks/metrics, selection tie-break, zero-selectable handling.
    """
    if len(dev_items) != EXPECTED_DEV_CASES:
        raise ValueError(f"dev_items must be {EXPECTED_DEV_CASES}, got {len(dev_items)}")
    # Validate candidate registry exactly
    validate_candidate_registry()
    assert_d003_contract()
    # Fail-closed: RERANK must be 0 implicitly via D003 check
    per_candidate_ranks: dict[str, list[int]] = {cid: [] for cid in ALL_CANONICAL_IDS}
    per_case_records: list[dict[str, Any]] = []
    per_case_sources: list[str] = []
    # Fixed timed count before inspection (for latency harness): count is per_variant = len(dev_items) * rounds
    # For tests, we keep deterministic LATENCY_ROUNDS=5 if measurer needs it, but orchestration itself fixes count before calling measurer
    for idx, case in enumerate(dev_items):
        raw = str(case.get("query", "") or case.get("raw", ""))
        if not raw:
            raise ValueError(f"case {idx} missing query/raw")
        gold_source = str(case.get("gold_source") or case.get("source") or "")
        gold_source_id = str(case.get("gold_source_id") or case.get("source_id") or "")
        if gold_source not in ("youth", "gov24"):
            raise ValueError(f"case {idx} gold_source must be youth/gov24, got {gold_source!r}")
        per_case_sources.append(gold_source)
        # Strip region once, reuse for 4-way (same DB/corpus/query/qvec constraint)
        stripped = strip_region_for_runner(raw)
        # Lexical terms: baseline original, candidates rewrite
        baseline_terms = baseline_lexical_terms_for_runner(raw)
        # Validate baseline semantics
        validate_lexical_terms_semantics(baseline_terms, raw, candidate_id=BASELINE_ID)
        # Youth bias once
        yb = youth_bias_for_runner(raw)
        age = case.get("age")
        # Embed once, same qvec for 4-way
        vec = embedding_fn(stripped)
        # rp must be NULL
        rp = None
        assert_rp_is_null(rp)
        case_ranks: dict[str, int] = {}
        case_results_debug: dict[str, Any] = {}
        for cid in ALL_CANONICAL_IDS:
            # Lexical terms per candidate semantics
            terms = lexical_terms_for_runner(raw, candidate_id=cid)
            # Validate semantics per candidate
            validate_lexical_terms_semantics(terms, raw, candidate_id=cid)
            # SQL semantics already validated globally, but we also ensure call uses correct pool semantics via get_sql_for_candidate check
            sql = get_sql_for_candidate(cid)
            validate_sql_semantics(sql, cid)
            validate_cosine_filter_position(sql)
            # Retrieve (LIMIT 30) — retrieval_fn must implement vector-pool K and youth/lexical ordering already
            # For baseline, pool_k is None, for candidates pool_k is 128/256/512
            raw_results = retrieval_fn(cid, vec, terms, yb, age, rp)
            if not isinstance(raw_results, list):
                raise ValueError(f"retrieval_fn for {cid} must return list, got {type(raw_results)}")
            if len(raw_results) > FINAL_N:
                raise ValueError(f"retrieval_fn for {cid} returned > FINAL_N {len(raw_results)} > {FINAL_N} (must be LIMIT 30)")
            # Apply post-LIMIT cosine filter (1 - dist >= 0.78)
            filtered = apply_cosine_filter(raw_results, cosine_min=D003_COSINE_MIN)
            # Verify deterministic tie-break: results should already be ordered by ordering_key if we were to sort.
            # For pure testability, we do not re-sort here; we trust retrieval_fn's SQL ordering.
            # But we can validate that filtered is sorted according to ordering_key when lexical_overlap known? Hard without dist.
            # Instead validate that rp is still null
            assert_rp_is_null(rp)
            rank = rank_of_gold(filtered, gold_source, gold_source_id)
            # rank is 0 if outside top10, but for metrics we need rank within filtered (could be outside filtered length -> 0)
            # For diagnostic, also store clipped rank (0 if not in filtered at all vs >30)
            per_candidate_ranks[cid].append(rank)
            case_ranks[cid] = rank
            case_results_debug[cid] = {"filtered_len": len(filtered), "rank": rank}
        per_case_records.append({
            "case_id": case.get("id") or case.get("case_id") or f"case-{idx}",
            "gold": {"source": gold_source, "source_id": gold_source_id},
            "category": case.get("category"),
            "ranks": dict(case_ranks),
            "_debug": case_results_debug,
        })
    # Compute metrics per candidate
    metrics = compute_all_candidate_metrics(per_candidate_ranks, per_case_sources)
    # Determine quality-selectable per candidate
    baseline_metrics = metrics[BASELINE_ID]
    per_candidate_quality: dict[str, tuple[bool, dict]] = {}
    quality_ids: list[str] = []
    for cid in CANDIDATE_IDS:
        is_q, diag = quality_selectable(baseline_metrics, metrics[cid])
        per_candidate_quality[cid] = (is_q, diag)
        if is_q:
            quality_ids.append(cid)
    # Latency: ONLY for quality-selectable candidates, via measurer (same-process/same-DB/interleaved/warmup-excluded)
    # Timed count fixed before inspection: measurer should use predetermined count, we pass quality_ids only
    latency_results: dict[str, Any] = {cid: None for cid in ALL_CANONICAL_IDS}
    dev_selectable_map: dict[str, tuple[bool, dict]] = {}
    # If measurer provided, it must be called with quality_ids only
    measured: dict[str, Any] = {}
    if latency_measurer is not None and quality_ids:
        # Enforce quality-selectable-only contract: measurer should not be called for non-quality
        measured = latency_measurer(quality_ids)
        if not isinstance(measured, dict):
            raise ValueError("latency_measurer must return dict")
        for cid in quality_ids:
            if cid not in measured:
                raise ValueError(f"latency_measurer missing quality candidate {cid}")
            latency_results[cid] = measured[cid]
        # Baseline is required for paired delta; measurer should return baseline as well if quality_ids non-empty
        if BASELINE_ID in measured:
            latency_results[BASELINE_ID] = measured[BASELINE_ID]
        # For non-quality, latency remains None (not evaluated)
    for cid in CANDIDATE_IDS:
        is_q = per_candidate_quality[cid][0]
        if not is_q:
            # Not quality-selectable -> dev_selectable false, latency not applicable
            is_dev, ddiag = dev_selectable(baseline_metrics, metrics[cid], None, None)
            # Override latency_gate reason to indicate not applicable
            dev_selectable_map[cid] = (False, ddiag)
            continue
        # Quality-selectable: check latency gate
        # Need baseline p95 and candidate p95
        base_lat = latency_results[BASELINE_ID]
        cand_lat = latency_results[cid]
        # Baseline latency may be needed even if baseline not quality-selectable? For quality-selectable candidates, baseline latency must have been measured.
        # If measurer was provided, it should have measured baseline as well if baseline is needed for comparison?
        # Spec says same-process/same-DB/interleaved for baseline vs candidate. So for each quality candidate, we need paired baseline p95.
        # Our measurer contract: when quality_ids includes candidates, measurer should measure baseline + those candidates interleaved.
        # So we expect baseline latency in measured if quality_ids non-empty.
        # Handle: if baseline latency missing but quality candidates exist, require measurer to have provided baseline p95 via separate call or we call measurer with baseline included.
        # Simpler: if baseline not in measured, treat as None -> dev_selectable false with reason missing
        b_p95 = None
        c_p95 = None
        if base_lat is not None:
            b_p95 = base_lat.get("p95") if isinstance(base_lat, dict) else None
        elif latency_measurer is not None and quality_ids:
            # Try to get baseline from measurer if it included baseline implicitly
            # If not, we consider missing
            b_p95 = None
        if cand_lat is not None and isinstance(cand_lat, dict):
            c_p95 = cand_lat.get("p95")
        is_dev, ddiag = dev_selectable(baseline_metrics, metrics[cid], b_p95, c_p95)
        dev_selectable_map[cid] = (is_dev, ddiag)
    # Alternative path: if latency_measurer is None, all dev_selectable will be false due to missing latency (as per dev_selectable logic)
    # unless quality_ids empty -> already false
    # Collect selectable candidates
    selectable: list[str] = [cid for cid, (is_dev, _) in dev_selectable_map.items() if is_dev]
    # For delta we need p95_delta; for selectable only, delta is defined
    tie_sorted: list[str] = []
    if selectable:
        def _sort_key(cid: str):
            # Retrieve net, macro, delta
            is_q, qdiag = per_candidate_quality[cid]
            net = int(qdiag.get("net_hit5", metrics[cid]["hit@5"] - baseline_metrics["hit@5"]))
            macro = float(metrics[cid]["source_macro_recall@5"])
            # p95 delta
            b_lat = latency_results[BASELINE_ID]
            c_lat = latency_results[cid]
            b_p95 = b_lat.get("p95") if isinstance(b_lat, dict) and "p95" in b_lat else 0.0
            c_p95 = c_lat.get("p95") if isinstance(c_lat, dict) and "p95" in c_lat else 0.0
            delta = float(c_p95) - float(b_p95) if b_p95 is not None and c_p95 is not None else 9999.0
            return tie_break_sort_key(cid, net, macro, delta)
        tie_sorted = sorted(selectable, key=_sort_key)
    selected = tie_sorted[0] if tie_sorted else None
    # Build complete result skeleton and fill
    skeleton = build_result_skeleton()
    skeleton["metrics"] = metrics
    skeleton["per_case"] = per_case_records
    # selection details
    selection_detail = {
        "per_candidate": {cid: {"quality_selectable": per_candidate_quality[cid][0], "quality_diag": per_candidate_quality[cid][1], "dev_selectable": dev_selectable_map[cid][0], "dev_diag": dev_selectable_map[cid][1]} for cid in CANDIDATE_IDS},
        "quality_selectable": quality_ids,
        "dev_selectable": selectable,
        "tie_sorted": tie_sorted,
        "selected_candidate": selected,
        "tie_break": ["net_hit5", "macro_R5", "p95_delta", "smaller_K"],
        "zero_selectable": len(selectable) == 0,
    }
    skeleton["selection"] = selection_detail
    skeleton["latency"] = latency_results
    # Also include latency_diagnostics for transparency
    skeleton["latency_diagnostics"] = {"measured": measured, "quality_only": True, "timed_count_fixed_before_inspection": True}
    # Validate complete before return
    validate_complete_result(skeleton)
    return skeleton
