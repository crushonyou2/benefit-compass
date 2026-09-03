"""Cost measurement V1 — pure parser/counter + frozen SQL (D-061, pre-result).

No IO at import/construction. All DB touches happen via RealEvaluationSession
on the SAME governing REPEATABLE READ connection. Errors are secret-free
(type-only, no DSN/query/plaintext). Thresholds are prereg-exact (index<=2,
rows<=3, extra==0); missing=>HOLD, numeric failure=>NO-GO.
"""
from __future__ import annotations

import json
import re

# Frozen baseline corpus index set (D-059 section 5, public schema).
FROZEN_BASELINE_INDEXES = frozenset({
    "idx_chunk_embedding",
    "idx_policy_age",
    "idx_policy_income",
    "idx_policy_region",
    "policy_chunk_pkey",
    "policy_chunk_policy_id_chunk_index_key",
    "policy_pkey",
    "policy_source_source_id_key",
})

INDEX_FOOTPRINT_SQL = """
SELECT c.relname AS index_name, pg_relation_size(c.oid) AS bytes
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE n.nspname = 'public'
AND c.relkind = 'i'
AND c.relname IN ('idx_chunk_embedding', 'idx_policy_age', 'idx_policy_income', 'idx_policy_region', 'policy_chunk_pkey', 'policy_chunk_policy_id_chunk_index_key', 'policy_pkey', 'policy_source_source_id_key')
"""

ALL_INDEXES_SQL = """
SELECT c.relname AS index_name, pg_relation_size(c.oid) AS bytes
FROM pg_class c
JOIN pg_namespace n ON n.oid = c.relnamespace
JOIN pg_index i ON i.indexrelid = c.oid
WHERE n.nspname = 'public'
AND i.indrelid IN ('policy'::regclass, 'policy_chunk'::regclass)
"""

EXPLAIN_PREFIX = "EXPLAIN (ANALYZE, FORMAT JSON, TIMING OFF, SUMMARY OFF)"

# Candidate dense shadow: per-policy nearest over policy_chunk, top100, COSINE_MIN.
# Cost-work equivalence only; never feeds ranking.
CANDIDATE_DENSE_SHADOW_SQL = """
SELECT * FROM (
  SELECT p.id AS pid, MIN(c.embedding <=> %(vec)s::vector) AS dist
  FROM policy_chunk c
  JOIN policy p ON p.id = c.policy_id
  WHERE (p.biz_end IS NULL OR p.biz_end >= %(as_of)s)
  GROUP BY p.id
  ORDER BY dist
  LIMIT 100
) d WHERE 1 - d.dist >= 0.78
"""

# Candidate sparse shadow: field-weighted sparse over non-excluded policy, top100.
# Weights appear only in SELECT/ORDER BY; scans are weight-independent.
CANDIDATE_SPARSE_SHADOW_SQL = """
SELECT p.id AS pid
FROM policy p
CROSS JOIN LATERAL unnest(%(lexical_terms)s::text[]) AS term
WHERE (p.biz_end IS NULL OR p.biz_end >= %(as_of)s)
GROUP BY p.id, p.source, p.source_id
ORDER BY (
  %(fw_title)s * COUNT(DISTINCT CASE WHEN p.title ILIKE '%%' || term || '%%' THEN term END) +
  %(fw_support)s * COUNT(DISTINCT CASE WHEN concat_ws(' ', p.support_content, p.summary, p.keywords) ILIKE '%%' || term || '%%' THEN term END) +
  %(fw_elig)s * COUNT(DISTINCT CASE WHEN concat_ws(' ', p.add_qualify, p.income_etc, p.apply_method) ILIKE '%%' || term || '%%' THEN term END)
) DESC, p.source, p.source_id, p.id
LIMIT 100
"""

RECOGNIZED_SCAN_NODES = frozenset({
    "Seq Scan",
    "Index Scan",
    "Index Only Scan",
    "Bitmap Heap Scan",
    "Tid Scan",
    "Tid Range Scan",
})

TARGET_RELATIONS = frozenset({"policy", "policy_chunk"})

_LEXICAL_TERM_RE = re.compile(r"^[0-9A-Za-z가-힣]+$")


def assert_lexical_terms_safe(terms: object) -> list:
    """Validate ILIKE-safe terms (distinct alphabet, no wildcards). Fail-closed."""
    if not isinstance(terms, (list, tuple)):
        raise ValueError("lexical terms must be list (fail-closed)")
    out = list(terms)
    seen: set = set()
    for t in out:
        if not isinstance(t, str):
            raise ValueError("lexical term must be str (fail-closed)")
        if t in seen:
            raise ValueError("lexical terms must be distinct (fail-closed)")
        seen.add(t)
        if len(t) < 2:
            raise ValueError("lexical term too short (fail-closed)")
        if not _LEXICAL_TERM_RE.match(t):
            raise ValueError("lexical term alphabet violation (fail-closed)")
        if "%" in t or "_" in t or "\\" in t:
            raise ValueError("lexical term carries LIKE wildcard (fail-closed)")
    return out


def _node_contribution(node: dict) -> int:
    """Base-visit contribution for one recognized scan node. Raises HOLD on missing actuals."""
    if not isinstance(node, dict):
        raise ValueError("plan node must be dict (fail-closed HOLD)")
    if "Actual Rows" not in node or "Actual Loops" not in node:
        raise ValueError("missing actuals (fail-closed HOLD)")
    actual_rows = node.get("Actual Rows")
    actual_loops = node.get("Actual Loops")
    if isinstance(actual_rows, bool) or not isinstance(actual_rows, (int, float)):
        raise ValueError("Actual Rows malformed (fail-closed HOLD)")
    if isinstance(actual_loops, bool) or not isinstance(actual_loops, (int, float)):
        raise ValueError("Actual Loops malformed (fail-closed HOLD)")
    filt = node.get("Rows Removed by Filter", 0)
    recheck = node.get("Rows Removed by Index Recheck", 0)
    for v in (filt, recheck):
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            raise ValueError("removed-rows malformed (fail-closed HOLD)")
    total_per_loop = float(actual_rows) + float(filt) + float(recheck)
    if total_per_loop < 0 or float(actual_loops) < 0:
        raise ValueError("negative plan counters (fail-closed HOLD)")
    # Actual Rows/removed are per-loop averages; total = per-loop sum * loops.
    return int(round(total_per_loop * float(actual_loops)))


def count_base_scanned_rows(plan_json: object) -> int:
    """Count base relation visits for policy/policy_chunk. Raises ValueError on HOLD."""
    # Accept EXPLAIN FORMAT JSON shapes: [{Plan:...}], {Plan:...}, or bare plan dict.
    if isinstance(plan_json, list):
        if not plan_json:
            raise ValueError("empty EXPLAIN output (fail-closed HOLD)")
        if len(plan_json) == 1 and isinstance(plan_json[0], dict) and "Plan" in plan_json[0]:
            root = plan_json[0]["Plan"]
        elif len(plan_json) == 1 and isinstance(plan_json[0], dict) and "Node Type" in plan_json[0]:
            root = plan_json[0]
        else:
            # Some drivers wrap as [[{Plan}]]? Reject as incomplete.
            raise ValueError("incomplete EXPLAIN shape (fail-closed HOLD)")
    elif isinstance(plan_json, dict):
        if "Plan" in plan_json and isinstance(plan_json["Plan"], dict):
            root = plan_json["Plan"]
        elif "Node Type" in plan_json:
            root = plan_json
        else:
            raise ValueError("incomplete EXPLAIN shape (fail-closed HOLD)")
    elif isinstance(plan_json, str):
        try:
            parsed = json.loads(plan_json)
        except Exception:
            raise ValueError("EXPLAIN JSON unparseable (fail-closed HOLD)") from None
        return count_base_scanned_rows(parsed)
    else:
        raise ValueError("EXPLAIN JSON malformed (fail-closed HOLD)")
    if not isinstance(root, dict) or "Node Type" not in root:
        raise ValueError("incomplete EXPLAIN plan (fail-closed HOLD)")

    total = 0
    seen_target = False

    def _walk(node: object) -> None:
        nonlocal total, seen_target
        if not isinstance(node, dict):
            raise ValueError("plan node malformed (fail-closed HOLD)")
        node_type = node.get("Node Type")
        rel = node.get("Relation Name")
        if isinstance(rel, str) and rel in TARGET_RELATIONS:
            seen_target = True
            if node_type == "Bitmap Index Scan":
                # Counted via its heap; skip separately to avoid double-count.
                pass
            elif node_type in RECOGNIZED_SCAN_NODES:
                total += _node_contribution(node)
            elif node_type in (
                "Function Scan", "CTE Scan", "Named Tuplestore Scan",
                "Result", "Values Scan",
            ):
                # Non-base visits over CTE/functions: never count target rows here.
                # If a target relation appears via such a node, it is not a base
                # visit; ignore (CTE outputs are counted at their base scans).
                pass
            else:
                raise ValueError(f"target relation via unknown scan node {node_type!r} (fail-closed HOLD)")
        for child in node.get("Plans", []) or []:
            _walk(child)

    _walk(root)
    # Zero-target plans (e.g., empty unnest with no base visit recorded) still
    # count what the base scans report; callers treat baseline<=0 as HOLD.
    _ = seen_target
    return total


def parse_explain_rows(rows: object) -> object:
    """Extract EXPLAIN FORMAT JSON payload from DB rows. Raises HOLD on malformed."""
    if not isinstance(rows, (list, tuple)) or not rows:
        raise ValueError("empty EXPLAIN rows (fail-closed HOLD)")
    first = rows[0]
    if isinstance(first, (list, tuple)):
        if not first:
            raise ValueError("empty EXPLAIN row (fail-closed HOLD)")
        payload = first[0]
    else:
        payload = first
    if isinstance(payload, str):
        try:
            return json.loads(payload)
        except Exception:
            raise ValueError("EXPLAIN JSON unparseable (fail-closed HOLD)") from None
    if isinstance(payload, (list, dict)):
        return payload
    raise ValueError("EXPLAIN payload malformed (fail-closed HOLD)")


def compute_index_ratio(baseline_rows: object, all_rows: object) -> dict:
    """Validate footprint sets and compute bytes/ratio. Raises HOLD on drift/zero."""
    def _to_map(rows: object, label: str) -> dict:
        if not isinstance(rows, (list, tuple)) or not rows:
            raise ValueError(f"{label} footprint empty (fail-closed HOLD)")
        out: dict = {}
        for r in rows:
            if not isinstance(r, (list, tuple)) or len(r) != 2:
                raise ValueError(f"{label} footprint row malformed (fail-closed HOLD)")
            name, nbytes = r
            if not isinstance(name, str) or not name.strip():
                raise ValueError(f"{label} footprint name malformed (fail-closed HOLD)")
            if isinstance(nbytes, bool) or not isinstance(nbytes, (int, float)):
                raise ValueError(f"{label} footprint bytes malformed (fail-closed HOLD)")
            if name in out:
                raise ValueError(f"{label} footprint duplicate {name!r} (fail-closed HOLD)")
            if nbytes <= 0:
                # Zero/negative per-index bytes cannot authorize a ratio; HOLD.
                # (Sum-zero is also HOLD below; per-index zero is HOLD to avoid
                # masking a missing/corrupt entry.)
                raise ValueError(f"{label} footprint zero bytes (fail-closed HOLD)")
            out[name] = int(nbytes)
        return out

    base_map = _to_map(baseline_rows, "baseline")
    if set(base_map.keys()) != set(FROZEN_BASELINE_INDEXES):
        raise ValueError("baseline index set drift (fail-closed HOLD)")
    all_map = _to_map(all_rows, "all") if all_rows is not None else {}
    # All-indexes must at least contain the frozen baseline set; extras are aux.
    for name in FROZEN_BASELINE_INDEXES:
        if name not in all_map:
            raise ValueError("all-indexes missing frozen baseline entry (fail-closed HOLD)")
        # Cross-check bytes consistency for frozen entries when both queries
        # report them (same snapshot/OID/size => equal). Mismatch => HOLD.
        if all_map[name] != base_map[name]:
            raise ValueError("index footprint mismatch across queries (fail-closed HOLD)")
    aux_names = sorted(set(all_map.keys()) - set(FROZEN_BASELINE_INDEXES))
    baseline_bytes = sum(base_map.values())
    aux_bytes = sum(all_map[n] for n in aux_names)
    if baseline_bytes <= 0:
        raise ValueError("zero baseline bytes (fail-closed HOLD)")
    candidate_bytes = baseline_bytes + aux_bytes
    ratio = candidate_bytes / baseline_bytes
    return {
        "baseline_bytes": baseline_bytes,
        "aux_bytes": aux_bytes,
        "aux_indexes": aux_names,
        "candidate_bytes": candidate_bytes,
        "index_ratio": float(ratio),
    }


def aggregate_task_ratios(per_task: object, task_count: object) -> dict:
    """Max-ratio aggregation over COMPLETE denominator. Raises HOLD/returns NO-GO signal.

    Returns {"rows_ratio": max_ratio, "measured_count": n, ...}.
    Raises ValueError on HOLD (missing/incomplete/nonpositive baseline).
    Caller maps max_ratio>3 to NO-GO (numeric failure), else PASS when complete.
    """
    if isinstance(task_count, bool) or not isinstance(task_count, int) or task_count <= 0:
        raise ValueError("task_count malformed (fail-closed HOLD)")
    if not isinstance(per_task, (list, tuple)):
        raise ValueError("per-task scans malformed (fail-closed HOLD)")
    if len(per_task) != task_count:
        raise ValueError("missing task measurement (fail-closed HOLD)")
    max_ratio = 0.0
    baseline_total = 0
    candidate_total = 0
    for entry in per_task:
        if not isinstance(entry, dict):
            raise ValueError("per-task entry malformed (fail-closed HOLD)")
        b = entry.get("baseline_scan")
        c = entry.get("candidate_scan")
        if isinstance(b, bool) or not isinstance(b, (int, float)):
            raise ValueError("baseline_scan malformed (fail-closed HOLD)")
        if isinstance(c, bool) or not isinstance(c, (int, float)):
            raise ValueError("candidate_scan malformed (fail-closed HOLD)")
        if b <= 0:
            raise ValueError("baseline_scan nonpositive (fail-closed HOLD)")
        if c < 0:
            raise ValueError("candidate_scan negative (fail-closed HOLD)")
        baseline_total += int(b)
        candidate_total += int(c)
        r = float(c) / float(b)
        if r > max_ratio:
            max_ratio = r
    return {
        "rows_ratio": float(max_ratio),
        "measured_count": len(per_task),
        "task_count": task_count,
        "baseline_total": baseline_total,
        "candidate_total": candidate_total,
    }
