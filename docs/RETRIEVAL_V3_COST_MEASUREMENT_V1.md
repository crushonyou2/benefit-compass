# Retrieval v3 — Cost Measurement Contract V1 (D-061, pre-result)

Append-only measurement freeze. `docs/RETRIEVAL_V3_PREREG.md`,
`eval/retrieval-v3/candidate-plan/candidate-plan-v4.json`,
`eval/retrieval-v3/candidate-plan/safe-action-policy-v1.json`,
`eval/retrieval-v3/candidate-plan/production-exclusion-policy-v2.json`,
`docs/RETRIEVAL_V3_LINK_PROVENANCE_SUPERSESSION_V1.md`,
`docs/RETRIEVAL_V3_LINK_PROVENANCE_SUPERSESSION_V2.md` stay byte-identical
as history. This V1 supersedes ONLY the prior cost-HOLD measurement
unavailability (D-059 section 3 / D-060 section 6: no comparable DB
instrumentation, adapter-side counts only). Numeric gates, thresholds,
ranking, configs, and selection are unchanged.

Frozen numeric gates (prereg sections 9-10, verbatim, no relaxation):

- candidate index size <= 2x baseline corpus index;
- EVERY query DB scanned rows <= 3x baseline CANDIDATES scan;
- extra external model calls = 0 unless Candidate B admitted;
- missing measurement => HOLD, numeric failure => NO-GO.
- Treating current in-memory candidate DB rows as 0 is FORBIDDEN.

Candidate-A ranking, 18 configs (`candidate-a-01..18`), `CANDIDATES=30`,
`COSINE_MIN=0.78`, fusion/MMR, safe-action, production-exclusion-v2,
latency budget (+80ms/700ms), and `ml-service` behavior are unchanged.
D-061 creates no indexes/DDL, no model/embedding/LLM change, no Candidate B,
no threshold change. Probe output NEVER replaces or changes Python
Candidate-A ranking or quality evidence.

## A) INDEX footprint — same DB/session, catalog/OID + pg_relation_size once

Baseline corpus index set is frozen to the current shared indexes on
`policy`/`policy_chunk` (D-059 section 5 evidence, 8 names):

`idx_chunk_embedding`, `idx_policy_age`, `idx_policy_income`,
`idx_policy_region`, `policy_chunk_pkey`,
`policy_chunk_policy_id_chunk_index_key`, `policy_pkey`,
`policy_source_source_id_key`.

Measurement (same governing read-only REPEATABLE READ connection, no second
connection, no SET, SELECT-only, once per run, cached):

- `INDEX_FOOTPRINT_SQL`: `SELECT` relname + `pg_relation_size(oid)` for the
  8 frozen names in `public` with `relkind='i'`.
- `ALL_INDEXES_SQL`: `SELECT` relname + `pg_relation_size(oid)` for every
  index whose `indrelid` is `policy` or `policy_chunk` (`public` only).

Validation (fail-closed HOLD):

- returned baseline names must equal the frozen 8 exactly (missing,
  duplicate, extra-in-baseline-query, or name drift => HOLD);
- each baseline byte count must be a strict int > 0; sum baseline bytes > 0
  else HOLD (zero baseline => HOLD, never 0/1 assumed);
- candidate-only persistent auxiliary set = all-indexes minus frozen 8.
  D-061 creates no indexes/DDL, so aux is expected empty. Any aux bytes are
  summed truthfully (never ignored); aux discovery failure => HOLD.
- `candidate_bytes = baseline_bytes + aux_bytes`;
  `index_ratio = candidate_bytes / baseline_bytes`; threshold stays `<= 2`.

## B) ROWS probes — SAME governing connection, pinned date, reused qvec/terms

Same governing read-only REPEATABLE READ connection and pinned
`evaluation_as_of_date`, no second connection, no SET, no second
`CURRENT_DATE`. Reuse each run query's already-computed `qvec` (frozen
`intfloat/multilingual-e5-base`, `query: `-prefixed, 768 finite floats) and
already-computed lexical terms (`lexical_overlap_terms(stripped)`); NO extra
model call. `strip_region`, `youth_source_bias`, `lexical_overlap_terms`,
`format_qvec` are reused verbatim.

- Baseline probe: `EXPLAIN (ANALYZE, FORMAT JSON, TIMING OFF, SUMMARY OFF)`
  wrapping exact `D003_SQL` with `n=30`, pinned `as_of`, `age=None`,
  `rp=None`, `youth_bias=youth_source_bias(stripped)`,
  `lexical_terms=lexical_overlap_terms(stripped)`,
  `lexical_bias=0.01`, `vec=format_qvec(qvec)`.
- Candidate cost-only shadow probes (read-only SQL representing frozen
  Candidate-A DB retrieval work without feeding ranking):
  - Dense shadow: exact per-policy nearest over `policy_chunk`
    (`MIN(embedding <=> vec)` grouped by policy, non-production-excluded
    only via `biz_end IS NULL OR biz_end >= as_of`), ordered by distance,
    `LIMIT 100`, then `COSINE_MIN` (`1-dist >= 0.78`). Cost-work
    equivalence only, not a replacement ranker.
  - Sparse shadow: field-weighted sparse over non-production-excluded
    `policy` (`CROSS JOIN LATERAL unnest(lexical_terms)` with per-field
    `ILIKE '%' || term || '%'` counts on title / support
    (`support_content/summary/keywords`) / eligibility
    (`add_qualify/income_etc/apply_method`), grouped by policy, ordered by
    field-weighted sum, `LIMIT 100`). Weights affect only `SELECT`/`ORDER BY`.
  - Exact title/org shares the same policy pass (per-policy string checks
    over already-scanned policy rows, no additional base visit).
  - Fusion/MMR are post-DB Python and add no DB relation scan.
- `candidate_scan = dense_scan + sparse_scan` (sum of base visits across
  both shadows for that query). Probe output (rows/plans) is discarded
  except for scan counts; Python Candidate-A ranking is untouched.

## C) scan_rows parser — base visits only, secret-free, HOLD on doubt

Recursively inspect `EXPLAIN (ANALYZE, FORMAT JSON)` output
(`[{Plan: {...}}]`, `Plans` children). Count only base relation visits with
`Relation Name` in (`policy`, `policy_chunk`):

- Recognized scan nodes only: `Seq Scan`, `Index Scan`, `Index Only Scan`,
  `Bitmap Heap Scan`, `Tid Scan`, `Tid Range Scan` if encountered.
- Contribution per visit:
  `(Actual Rows + Rows Removed by Filter + Rows Removed by Index Recheck
  where present) * Actual Loops`.
- Do NOT count `Function Scan`/`CTE Scan`/sort/join/limit/aggregate outputs
  or `Bitmap Index Scan` separately (avoids double-count with its heap).
- HOLD (never PASS, never 0) on: target relation via unknown scan node,
  missing `Actual Rows`/`Actual Loops`, incomplete/malformed `EXPLAIN`,
  non-list/non-dict JSON, or `baseline_scan <= 0`.

## D) Aggregation — per-query gate, max ratio, completeness, no query text

Original gate is per-query, therefore EACH benchmark task must satisfy
`candidate_scan <= 3 * baseline_scan`.

- Per-task ratio = `candidate_scan / baseline_scan` (both from C).
- Persist only aggregates: `rows_ratio = max` per-query ratio over the
  COMPLETE denominator, plus `task_count` / `measured_count` and aggregate
  counters (`baseline_total`, `candidate_total`, `index` bytes). No protected
  query text, no per-case content, no per-task ratios in the durable result.
- Any missing task (`measured_count != task_count`), any `HOLD` probe,
  any `baseline_scan <= 0` => cost HOLD.
- Any per-query ratio `> 3` => NO-GO; `index_ratio > 2` => NO-GO;
  `extra_model_calls != 0` => NO-GO. Else PASS (all thresholds met).
- Sharing across all 18 configs is permitted ONLY because base visits are
  statically config-independent (section F): weights/fusion change
  scores/order, not `FROM`/`WHERE`/`JOIN`/scan counts. One measurement per
  task is cached and shared identically; otherwise no shortcut (per-config
  probes required).

## E) Placement — outside timed samples, same snapshot, 0 extra calls

Deterministic placement: after retrieval pools and before safety
aggregation, strictly outside `measure_paired_latency` timed closures
(`baseline_fn`/`candidate_fn` clock regions), while the same
REPEATABLE READ session/snapshot remains open (before deterministic close).
No second connection. Cached `qvec` per task from the already-executed
retrieval (first config's `qvec`, identical across configs for the same
stripped query) is reused, so `extra_model_calls` stays 0. Lexical terms are
pure recomputation (no model). Probes never alter ranking inputs/outputs.

## F) Lexical equivalence + dense equivalence + config-independence

- Lexical terms are `re.findall(r"[0-9A-Za-z가-힣]+", query)`, distinct,
  `len >= 2`, minus frozen stopwords. Alphabet contains no LIKE wildcards
  (`%`/`_`/`\`), so `'%' || term || '%'` has no pattern injection.
  Case behavior is meaning-preserving for this alphabet: Hangul and digits
  have no case; ASCII letters compare case-insensitively in both Python
  `casefold` substring and SQL `ILIKE`. SQL `ILIKE` substring therefore
  matches exactly the Python distinct-term field-substring semantics for
  cost-scan purposes (scores may differ by weighting; scans do not).
- Dense shadow `MIN(distance)` equals Python max-cosine representative
  (`distance = 1 - cosine` for pgvector cosine ops) as cost-work
  equivalence; it is never used as a ranker.
- Config-independence (static): dense shadow references no config weights;
  sparse shadow weights appear only in `SELECT`/`ORDER BY`, never in
  `FROM`/`WHERE`/`JOIN`/`GROUP BY`; exact shares the policy pass;
  fusion (`union`/`hybrid_weighted_sum`), exact boosts, dedup threshold,
  and diversification lambda are post-DB Python score/order only. Hence base
  relation visits are identical across the 18 configs for the same
  `(qvec, lexical_terms, as_of)`. If a truthful shadow cannot be
  established, STOP/HOLD D-061; DO NOT weaken thresholds or claim DB=0.

## Implementation surface (meaning-preserving only)

- New pure module `eval/retrieval-v3/cost.py` (mirrored to
  `eval/retrieval_v3/cost.py` byte-identical): frozen index set, footprint
  SQLs, shadow SQLs, `EXPLAIN` prefix, secret-free plan parser/counter,
  index-ratio and max-ratio aggregation. No IO at import/construction.
- Narrow same-session `EXPLAIN` executor on `RealEvaluationSession`
  (`SELECT`/`WITH` remainder only, forbidden writes/DDL/SET rejected,
  type-only errors, cached footprint + per-task probe cache, no second
  `connect`).
- Canonical runner wiring/caching once per task (reuse first-config `qvec`,
  pure terms, outside timed samples, same session).
- `RealSafetyAdapter` returns structured `PASS`/`NO-GO`/`HOLD` with
  `index_ratio`, `rows_ratio` (max), `extra_model_calls=0`,
  `task_count`/`measured_count`/aggregate counters only. Normal ranking
  outputs/configs unchanged. Result schema thresholds unchanged.

Truth table: `HOLD` on missing/incomplete/zero-baseline/unknown-node;
`NO-GO` on `index_ratio > 2`, any per-query `> 3`, or `extra != 0`;
else `PASS`. Pre-dev/mock sessions without `EXPLAIN` capability stay HOLD
with `extra_model_calls=0` and no assumed ratios.

— END COST MEASUREMENT V1 (D-061 pre-result) —
