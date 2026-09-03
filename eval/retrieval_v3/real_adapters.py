"""FIRST-dev real adapters — production-faithful lazy wiring (D-056).

Replaces the D-054 fail-closed stubs with a mechanically reachable real path.
The canonical runner has a real DB session, a real embedding call, a real
D-003 production baseline, a real confined protected loader, a real safety
evidence hook, and a real nanosecond clock — all sharing ONE governing
evaluation resource.

Import and construction perform NO real IO: no DB connect, no model load,
no file read, no network. Every external touch happens inside the call that
needs it, and every missing prerequisite fails closed with an explicit
FIRST-dev preflight blocker. Readiness is never fabricated: gates without
authoritative evidence return structured HOLD.

Shared lifecycle (D-053/D-056) — ONE RealEvaluationSession governs the exact
DB connection context for capture + corpus + D-003 baseline::

    plan validation -> session -> SHOW TimeZone -> SELECT CURRENT_DATE
    (once each, same session, no SET TIME ZONE, no fallback) ->
    corpus load/provenance (same session, pinned date) ->
    protected grant verify -> protected loader -> run_start -> evaluation.

The pinned evaluation_as_of_date is immutable afterwards and governs
Candidate-A prefilter/audit and the paired D-003 baseline (explicit pinned
date parameter, never a second CURRENT_DATE lookup, no midnight drift).

Corpus identity (no DB-native snapshot is claimed): the provenance pin is a
deterministic recomputable content fingerprint (ordered identities + chunk
order + raw vector text + schema columns + captured pins). A DB-native
snapshot/transaction identity is not stable across connections, so none is
fabricated; the fingerprint is documented as the exact identity used.

Secrets: DATABASE_URL is read from the process environment only, stripped,
and never printed, logged, or interpolated into any message, result, or
audit event. Driver failures surface the error TYPE only (chain suppressed)
so host/credential text cannot leak through tracebacks.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import pathlib
import time
from typing import Any, Callable

from .evaluation_context import is_valid_iso_date, validate_pinned_context
from .normalization import (
    format_qvec,
    lexical_overlap_terms,
    strip_region,
    youth_source_bias,
)
from .safe_action import action_correct_for_role
from .safety import (
    CONNECT_TIMEOUT_S,
    MAX_ATTEMPTS,
    MAX_REDIRECTS,
    READ_TIMEOUT_S,
    check_production_exclusion,
    dedupe_official_links,
    evaluate_owned_ambiguous,
    evaluate_owned_unsupported,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]

# Exact frozen production embedding contract (ml-service/app.py EMBED_MODEL_NAME,
# /search encode call, eval normalization EMBED_MODEL). No substitution allowed.
EMBED_MODEL_ID = "intfloat/multilingual-e5-base"
EMBED_DIM = 768
EMBED_QUERY_PREFIX = "query: "

# Frozen D-003 production baseline descriptor (prereg section 9 latency gate;
# runner.D003_BASELINE). The adapter refuses any drifted descriptor.
FROZEN_D003_BASELINE = {
    "RERANK": 0,
    "CANDIDATES": 30,
    "COSINE_MIN": 0.78,
    "LEXICAL_BIAS": 0.01,
    "strip_region": True,
    "youth_bias_suppressed_for_gov24_orgs": True,
    "embedding": "intfloat/multilingual-e5-base",
}

# Corpus source-data load only (D-056): production policy/policy_chunk schema
# per db/schema.sql, deterministic order, every field the runner consumes.
# This is NOT a retrieval/ranking query: no similarity operator, no LIMIT,
# no CURRENT_DATE (expiry uses the pinned date downstream), no writes/DDL/SET.
CORPUS_COLUMNS = (
    "id", "source", "source_id", "title", "org", "support_content",
    "summary", "keywords", "add_qualify", "income_etc", "apply_method",
    "apply_url", "biz_end", "age_min", "age_max", "age_limit_yn",
)
CORPUS_SQL = """
SELECT p.id, p.source, p.source_id, p.title, p.org, p.support_content,
       p.summary, p.keywords, p.add_qualify, p.income_etc, p.apply_method,
       p.apply_url, p.biz_end,
       p.age_min, p.age_max, p.age_limit_yn,
       c.id AS chunk_id, c.chunk_index, c.embedding
FROM policy p LEFT JOIN policy_chunk c ON c.policy_id = p.id
ORDER BY p.source, p.source_id, c.chunk_index, c.id
"""

# Production D-003 baseline SQL (ml-service/app.py SQL) with the runtime
# CURRENT_DATE in BOTH expiry predicates replaced by the explicit pinned
# date parameter %(as_of)s. No other token differs (parity-tested).
D003_SQL = """
WITH nearest AS (
  SELECT DISTINCT ON (p.id) p.id, p.source, p.source_id, p.title, p.org,
         p.support_content, p.apply_method, p.apply_url, p.age_min, p.age_max,
         p.income_etc, (c.embedding <=> %(vec)s::vector) AS dist
  FROM policy_chunk c
  JOIN policy p ON p.id = c.policy_id
  WHERE ( %(age)s IS NULL OR p.age_limit_yn IS NOT TRUE
          OR %(age)s BETWEEN p.age_min AND p.age_max )
    AND ( %(rp)s IS NULL
          OR EXISTS (SELECT 1 FROM unnest(p.region_codes) rc WHERE rc LIKE %(rp)s) )
    AND ( p.biz_end IS NULL OR p.biz_end >= %(as_of)s )   -- pinned evaluation date
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
    AND ( p.biz_end IS NULL OR p.biz_end >= %(as_of)s )
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
LIMIT %(n)s
"""

D003_RESULT_COLUMNS = (
    "source", "source_id", "title", "org", "support_content", "apply_method",
    "apply_url", "age_min", "age_max", "income_etc", "score",
)

# Official-link source-match mapping is NOT established in any frozen artifact:
# db/schema.sql carries apply_url (application link) but no official_link
# column and no claimed-source <-> domain/path mapping, and inventing a
# heuristic/domain mapping is forbidden. The adapter therefore measures the
# prereg-exact URL denominator over the schema-authoritative apply_url field
# but returns official_link/http_resolution HOLD with this precise blocker.
OFFICIAL_LINK_MAPPING_BLOCKER = (
    "no authoritative official_link/source-match mapping established: "
    "policy schema (db/schema.sql) carries apply_url only, no official_link "
    "column and no frozen claimed-source domain/path map (fail-closed HOLD)"
)

# Baseline cost counters do not exist until the paired FIRST-dev measurement
# runs on the same env/DB/corpus. Ratios are never assumed (not 1, not 0).
COST_BASELINE_BLOCKER = (
    "baseline index/rows counters unavailable until the paired FIRST-dev "
    "measurement on the same env/DB/corpus; adapter-side counts measured, "
    "ratios never assumed (fail-closed HOLD)"
)


def read_database_url(env: Any = None) -> str:
    """Read DATABASE_URL from the environment mapping (default process env).

    Fail-closed on missing/empty. The value is returned, never printed or
    interpolated into any message.
    """
    mapping = os.environ if env is None else env
    try:
        value = mapping.get("DATABASE_URL", "")
    except Exception as e:
        raise RuntimeError(
            "DATABASE_URL unreadable from environment "
            f"({type(e).__name__}, fail-closed)"
        ) from None
    if not isinstance(value, str) or not value.strip():
        raise RuntimeError(
            "DATABASE_URL missing or empty (fail-closed FIRST-dev preflight "
            "blocker: no production database configured)"
        )
    return value.strip()


def parse_pgvector(raw: object) -> list[float]:
    """Parse a pgvector value to 768 finite floats (fail-closed)."""
    if isinstance(raw, (list, tuple)):
        items = list(raw)
    elif isinstance(raw, str):
        text = raw.strip()
        if not (text.startswith("[") and text.endswith("]")):
            raise ValueError("vector text must be bracketed (fail-closed)")
        items = text[1:-1].split(",")
    else:
        raise ValueError(f"vector must be text or sequence, got {type(raw).__name__}")
    try:
        vals = [float(x) for x in items]
    except Exception as e:
        raise ValueError(f"vector has non-numeric entries ({type(e).__name__}, fail-closed)") from None
    if len(vals) != EMBED_DIM:
        raise ValueError(f"vector dim must be {EMBED_DIM}, got {len(vals)} (fail-closed)")
    for v in vals:
        if not math.isfinite(v):
            raise ValueError("vector has non-finite entries (fail-closed)")
    return vals


class RealEvaluationSession:
    """ONE governing read-only DB resource for an evaluation run (D-056).

    Owns the exact connection context for SHOW TimeZone + SELECT CURRENT_DATE
    capture, corpus source-data load/provenance, and D-003 baseline queries.
    Lazy: construction and import perform no IO; the connection opens on
    first use. Read-only: real connections use readonly + autocommit sessions;
    this class never issues writes, DDL, temp mutation, or SET TIME ZONE.
    Close is exact-once (second close raises); is_closed guards ownership
    transfer to the runner wrapper.
    """

    def __init__(self, env: Any = None, connect_fn: Callable[[str], Any] | None = None):
        self._env = env
        self._connect_fn = connect_fn
        self._conn: Any = None
        self._closed = False
        self._timezone_seen = False
        self._date_seen = False
        self._tz_value: str | None = None
        self._date_value: str | None = None
        self._pinned: dict | None = None
        self._policies: list[dict] | None = None
        self._fingerprint: str | None = None
        self._rows_scanned = 0
        self._d003_queries = 0

    @property
    def is_closed(self) -> bool:
        return self._closed

    @property
    def rows_scanned(self) -> int:
        return self._rows_scanned

    @property
    def d003_queries(self) -> int:
        return self._d003_queries

    def _ensure_conn(self) -> Any:
        if self._closed:
            raise RuntimeError("evaluation DB session is closed (fail-closed)")
        if self._conn is not None:
            return self._conn
        dsn = read_database_url(self._env)
        if self._connect_fn is not None:
            try:
                self._conn = self._connect_fn(dsn)
            except Exception as e:
                raise RuntimeError(
                    "evaluation DB connect failed "
                    f"({type(e).__name__}, fail-closed)"
                ) from None
            return self._conn
        try:
            import psycopg2  # lazy: no driver import at module import

            conn = psycopg2.connect(dsn)
            conn.set_session(readonly=True, autocommit=True)
        except Exception as e:
            raise RuntimeError(
                "evaluation DB connect failed "
                f"({type(e).__name__}, fail-closed FIRST-dev preflight blocker)"
            ) from None
        self._conn = conn
        return self._conn

    def _run_capture_statement(self, sql: str) -> Any:
        conn = self._ensure_conn()
        try:
            cur = conn.cursor()
            try:
                cur.execute(sql)
                row = cur.fetchone()
            finally:
                cur.close()
        except Exception as e:
            raise RuntimeError(
                f"evaluation-context capture failed on {sql} "
                f"({type(e).__name__}, fail-closed, no fallback)"
            ) from None
        return row[0] if isinstance(row, (list, tuple)) else row

    @staticmethod
    def _coerce_date(value: object) -> str:
        if isinstance(value, str):
            candidate = value.strip()
        elif hasattr(value, "isoformat"):
            try:
                candidate = str(value.isoformat())[:10]
            except Exception:
                raise ValueError(f"CURRENT_DATE uncoercible ({type(value).__name__}, fail-closed)") from None
        else:
            raise ValueError(f"CURRENT_DATE must be ISO date, got {type(value).__name__} (fail-closed)")
        if not is_valid_iso_date(candidate):
            raise ValueError(f"evaluation_as_of_date missing/malformed {candidate!r} (fail-closed, no fallback)")
        return candidate

    def capture_executor(self, sql: str) -> Any:
        """Exact-statement capture executor: SHOW TimeZone then SELECT CURRENT_DATE, once each."""
        if self._closed:
            raise RuntimeError("capture on closed session (fail-closed)")
        if sql == "SHOW TimeZone":
            if self._timezone_seen:
                raise ValueError("SHOW TimeZone already captured (exact-once, fail-closed)")
            if self._date_seen:
                raise ValueError("SHOW TimeZone must precede SELECT CURRENT_DATE (fail-closed)")
            value = self._run_capture_statement(sql)
            if not isinstance(value, str) or not value.strip():
                raise ValueError("db_session_timezone missing/malformed (fail-closed, no fallback)")
            self._timezone_seen = True
            self._tz_value = value
        elif sql == "SELECT CURRENT_DATE":
            if not self._timezone_seen:
                raise ValueError("SELECT CURRENT_DATE before SHOW TimeZone (fail-closed)")
            if self._date_seen:
                raise ValueError("SELECT CURRENT_DATE already captured (exact-once, fail-closed)")
            value = self._coerce_date(self._run_capture_statement(sql))
            self._date_seen = True
            self._date_value = value
        else:
            raise ValueError(f"capture executor rejects statement {sql!r} (allowlist: SHOW TimeZone, SELECT CURRENT_DATE)")
        if self._timezone_seen and self._date_seen and self._pinned is None:
            assert self._tz_value is not None and self._date_value is not None
            self._pinned = {"db_session_timezone": self._tz_value, "evaluation_as_of_date": self._date_value}
        return value

    @property
    def pinned_context(self) -> dict:
        """Pinned context; requires both capture statements (fail-closed otherwise)."""
        if self._pinned is not None:
            return dict(self._pinned)
        raise RuntimeError("pinned context unavailable before capture completes (fail-closed)")

    def execute_readonly(self, sql: str, params: dict | None = None) -> list[tuple]:
        """Read-only SELECT execution on the governing connection (no writes/DDL/SET)."""
        if self._closed:
            raise RuntimeError("query on closed session (fail-closed)")
        head = " ".join(sql.split()).upper()
        if not (head.startswith("SELECT") or head.startswith("WITH")):
            raise ValueError("session executes SELECT/WITH only (fail-closed)")
        for forbidden in ("INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE", "GRANT", "COPY", "VACUUM", "SET TIME ZONE", "SET SESSION", "SET LOCAL"):
            if forbidden in head:
                raise ValueError(f"session rejects {forbidden} (read-only, fail-closed)")
        conn = self._ensure_conn()
        try:
            cur = conn.cursor()
            try:
                cur.execute(sql, params or {})
                rows = cur.fetchall()
            finally:
                cur.close()
        except Exception as e:
            raise RuntimeError(
                f"evaluation DB read failed ({type(e).__name__}, fail-closed)"
            ) from None
        self._rows_scanned += len(rows)
        return [tuple(r) for r in rows]

    @staticmethod
    def _coerce_biz_end(value: object) -> str | None:
        if value is None:
            return None
        if isinstance(value, str):
            return value.strip()
        if hasattr(value, "isoformat"):
            try:
                return str(value.isoformat())[:10]
            except Exception:
                raise ValueError("biz_end uncoercible (fail-closed)") from None
        raise ValueError(f"biz_end must be date or text, got {type(value).__name__} (fail-closed)")

    def load_corpus_policies(self) -> list[dict]:
        """Load + validate the pinned corpus (requires completed capture)."""
        if self._closed:
            raise RuntimeError("corpus load on closed session (fail-closed)")
        if self._policies is not None:
            return self._policies
        if self._pinned is None:
            raise RuntimeError("corpus load before capture completion is forbidden (fail-closed)")
        rows = self.execute_readonly(CORPUS_SQL)
        if not rows:
            raise ValueError("corpus empty (fail-closed: no policies)")
        policies: list[dict] = []
        by_identity: dict[tuple, dict] = {}
        fingerprint = hashlib.sha256()
        fingerprint.update(b"retrieval-v3-corpus-v1\n")
        fingerprint.update(("columns:" + ",".join(CORPUS_COLUMNS) + "\n").encode("utf-8"))
        last_order: tuple | None = None
        for row in rows:
            (pid, source, source_id, title, org, support_content, summary,
             keywords, add_qualify, income_etc, apply_method, apply_url,
             biz_end, age_min, age_max, age_limit_yn,
             chunk_id, chunk_index, embedding_raw) = row
            if not isinstance(source, str) or not source.strip():
                raise ValueError("corpus policy missing source identity (fail-closed)")
            if not isinstance(source_id, str) or not source_id.strip():
                raise ValueError("corpus policy missing source_id identity (fail-closed)")
            if isinstance(pid, bool) or not isinstance(pid, int):
                raise ValueError("corpus policy missing stable integer id (fail-closed)")
            identity = (source, source_id)
            order_key = (source, source_id)
            if last_order is not None and order_key < last_order:
                raise ValueError("corpus row order not deterministic (fail-closed)")
            last_order = order_key
            entry = by_identity.get(identity)
            if entry is None:
                entry = {
                    "id": pid, "source": source, "source_id": source_id,
                    "title": title, "org": org, "support_content": support_content,
                    "summary": summary, "keywords": keywords,
                    "add_qualify": add_qualify, "income_etc": income_etc,
                    "apply_method": apply_method, "apply_url": apply_url,
                    "biz_end": self._coerce_biz_end(biz_end),
                    "age_min": age_min, "age_max": age_max,
                    "age_limit_yn": age_limit_yn, "chunks": [],
                }
                by_identity[identity] = entry
                policies.append(entry)
                fingerprint.update(f"{source}\x00{source_id}\x00{pid}\n".encode("utf-8"))
            elif entry["id"] != pid:
                raise ValueError(f"duplicate corpus identity {identity} with divergent ids (fail-closed)")
            if chunk_id is not None:
                if isinstance(chunk_id, bool) or not isinstance(chunk_id, int):
                    raise ValueError(f"corpus chunk id malformed for {identity} (fail-closed)")
                if isinstance(chunk_index, bool) or not isinstance(chunk_index, int) or chunk_index < 0:
                    raise ValueError(f"corpus chunk_index malformed for {identity} (fail-closed)")
                prev = entry["chunks"][-1] if entry["chunks"] else None
                if prev is not None and (chunk_index, chunk_id) <= (prev["chunk_index"], prev["id"]):
                    raise ValueError(f"corpus chunk order not deterministic for {identity} (fail-closed)")
                if embedding_raw is None:
                    raise ValueError(f"corpus chunk missing vector for {identity} (fail-closed)")
                vector = parse_pgvector(embedding_raw)
                entry["chunks"].append({"id": chunk_id, "chunk_index": chunk_index, "embedding": vector})
                raw_text = embedding_raw if isinstance(embedding_raw, str) else json.dumps(embedding_raw)
                fingerprint.update(f"{chunk_index}\x00{chunk_id}\x00{raw_text.strip()}\n".encode("utf-8"))
        pins = self._pinned
        fingerprint.update(f"pins:{pins['db_session_timezone']}\x00{pins['evaluation_as_of_date']}\n".encode("utf-8"))
        self._fingerprint = fingerprint.hexdigest()
        self._policies = policies
        return policies

    def corpus_provenance(self) -> dict:
        """Truthful recomputable provenance (requires loaded corpus)."""
        if self._closed:
            raise RuntimeError("corpus provenance on closed session (fail-closed)")
        if self._policies is None or self._pinned is None or self._fingerprint is None:
            raise RuntimeError("corpus provenance before corpus load (fail-closed)")
        sources: dict[str, int] = {}
        total_chunks = 0
        chunkless = 0
        for p in self._policies:
            sources[p["source"]] = sources.get(p["source"], 0) + 1
            total_chunks += len(p["chunks"])
            if not p["chunks"]:
                chunkless += 1
        return {
            "total_policies": len(self._policies),
            "total_chunks": total_chunks,
            "chunkless_policies": chunkless,
            "sources": sources,
            "corpus_rows_scanned": self._rows_scanned,
            "schema_columns": list(CORPUS_COLUMNS),
            "db_session_timezone": self._pinned["db_session_timezone"],
            "evaluation_as_of_date": self._pinned["evaluation_as_of_date"],
            "snapshot": {
                "kind": "recomputable-content-fingerprint",
                "corpus_sha256": self._fingerprint,
                "evaluation_as_of_date": self._pinned["evaluation_as_of_date"],
            },
        }

    @property
    def biz_end_lookup(self) -> dict:
        if self._policies is None:
            raise RuntimeError("biz_end lookup before corpus load (fail-closed)")
        return {(p["source"], p["source_id"]): p.get("biz_end") for p in self._policies}

    @property
    def official_url_lookup(self) -> dict:
        """Schema-authoritative apply_url per identity (NOT an official_link map)."""
        if self._policies is None:
            raise RuntimeError("URL lookup before corpus load (fail-closed)")
        return {(p["source"], p["source_id"]): p.get("apply_url") for p in self._policies}

    def note_d003_query(self) -> None:
        self._d003_queries += 1

    def close(self) -> None:
        """Deterministic exact-once cleanup (second close raises)."""
        if self._closed:
            raise RuntimeError("evaluation DB session already closed (exact-one violation, fail-closed)")
        self._closed = True
        conn, self._conn = self._conn, None
        if conn is not None:
            try:
                conn.close()
            except Exception as e:
                raise RuntimeError(
                    f"evaluation DB close failed ({type(e).__name__}, fail-closed)"
                ) from None


class RealEmbeddingAdapter:
    """Exact frozen multilingual-e5-base query embedding (D-056).

    Lazy: no model load at import or construction. Offline-first: the exact
    weights must already be cached locally (local_files_only); a missing
    model is a truthful FIRST-dev preflight blocker, never a download or a
    substituted model. The runner supplies the "query: " prefix; the adapter
    enforces it fail-closed. Output is normalized 768-dim finite floats.
    """

    def __init__(self, model_loader: Callable[[], Any] | None = None):
        self._model_loader = model_loader
        self._model: Any = None
        self.__real_adapter__ = True

    def _load_model(self) -> Any:
        if self._model is not None:
            return self._model
        if self._model_loader is not None:
            try:
                self._model = self._model_loader()
            except Exception as e:
                raise RuntimeError(
                    "embedding model load failed "
                    f"({type(e).__name__}, fail-closed)"
                ) from None
            return self._model
        try:
            import sentence_transformers  # lazy: no model import at module import

            self._model = sentence_transformers.SentenceTransformer(
                EMBED_MODEL_ID, local_files_only=True
            )
        except Exception as e:
            raise RuntimeError(
                "exact embedding weights intfloat/multilingual-e5-base not "
                "locally available offline (fail-closed FIRST-dev preflight "
                "blocker: no download, no substitute model, "
                f"{type(e).__name__})"
            ) from None
        return self._model

    @property
    def model_id(self) -> str:
        return EMBED_MODEL_ID

    def __call__(self, query: str) -> list[float]:
        if not isinstance(query, str) or not query.startswith(EMBED_QUERY_PREFIX):
            raise ValueError(
                f"embedding requires frozen {EMBED_QUERY_PREFIX!r}-prefixed query (fail-closed)"
            )
        if not query[len(EMBED_QUERY_PREFIX):].strip():
            raise ValueError("embedding refuses blank query (fail-closed)")
        model = self._load_model()
        try:
            raw = model.encode([query], normalize_embeddings=True)[0]
            vals = [float(x) for x in list(raw)]
        except Exception as e:
            raise RuntimeError(
                f"embedding encode failed ({type(e).__name__}, fail-closed)"
            ) from None
        if len(vals) != EMBED_DIM:
            raise ValueError(f"embedding dim must be {EMBED_DIM}, got {len(vals)} (fail-closed)")
        for v in vals:
            if not math.isfinite(v):
                raise ValueError("embedding has non-finite entries (fail-closed)")
        return vals


class RealProtectedLoader:
    """Fail-closed confined loader for the MATERIALIZED dev evalset (D-056).

    Opens NO protected plaintext in D-056: without an explicit
    already-authorized materialized path supplied at FIRST-dev time, every
    call fails closed (recorded FIRST-dev pre-gate blocker). The runner
    verifies the protected_access grant BEFORE invoking this loader; the
    loader additionally requires dev role, exact byte SHA256 equality to the
    passed set_sha (no normalization of the bytes), and path confinement
    (no traversal/symlink escape, no Git recovery of any kind).
    """

    def __init__(self, materialized_path: str | pathlib.Path | None = None, allowed_base: str | pathlib.Path | None = None):
        self._materialized_path = str(materialized_path) if materialized_path is not None else None
        self._allowed_base = pathlib.Path(allowed_base) if allowed_base is not None else REPO_ROOT
        self.__real_adapter__ = True

    def __call__(self, set_role: str, set_sha: str) -> list[dict]:
        if set_role != "dev":
            raise ValueError(
                f"protected loader forbids role {set_role!r} (dev only; holdout never materialized here, fail-closed)"
            )
        if not isinstance(set_sha, str) or len(set_sha) != 64:
            raise ValueError("protected loader requires 64-hex set_sha (fail-closed)")
        try:
            int(set_sha, 16)
        except Exception:
            raise ValueError("protected loader requires 64-hex set_sha (fail-closed)") from None
        if not self._materialized_path:
            raise RuntimeError(
                "no authorized materialized dev evalset path supplied "
                "(FIRST-dev pre-gate blocker: refusing to discover, access, "
                "or recover protected plaintext, fail-closed)"
            )
        base = self._allowed_base.resolve()
        try:
            resolved = pathlib.Path(self._materialized_path).resolve()
        except Exception as e:
            raise RuntimeError(
                f"materialized path unresolvable ({type(e).__name__}, fail-closed)"
            ) from None
        if resolved != base and base not in resolved.parents:
            raise ValueError(f"materialized path escapes the authorized base (fail-closed): {resolved}")
        if not resolved.is_file():
            raise ValueError("materialized dev evalset path is not a file (fail-closed)")
        try:
            raw = resolved.read_bytes()
        except Exception as e:
            raise RuntimeError(
                f"materialized dev evalset unreadable ({type(e).__name__}, fail-closed)"
            ) from None
        digest = hashlib.sha256(raw).hexdigest()
        if digest != set_sha.lower():
            raise ValueError(
                f"materialized dev evalset SHA mismatch: got {digest[:8]}... "
                f"expected {set_sha.lower()[:8]}... (fail-closed)"
            )
        try:
            text = raw.decode("utf-8")
        except Exception as e:
            raise ValueError(
                f"materialized dev evalset not strict UTF-8 ({type(e).__name__}, fail-closed)"
            ) from None
        tasks: list[dict] = []
        for lineno, line in enumerate(text.splitlines(), start=1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except Exception as e:
                raise ValueError(
                    f"materialized dev evalset line {lineno} invalid JSONL ({type(e).__name__}, fail-closed)"
                ) from None
            if not isinstance(obj, dict):
                raise ValueError(f"materialized dev evalset line {lineno} must be an object (fail-closed)")
            if not (obj.get("task_id") or obj.get("id")):
                raise ValueError(f"materialized dev evalset line {lineno} missing task id (fail-closed)")
            if not isinstance(obj.get("query") or obj.get("query_text"), str):
                raise ValueError(f"materialized dev evalset line {lineno} missing query text (fail-closed)")
            tasks.append(obj)
        if not tasks:
            raise ValueError("materialized dev evalset empty (fail-closed)")
        return tasks


class RealClock:
    """Monotonic high-resolution nanosecond clock (import-safe, no fabrication)."""

    def __init__(self) -> None:
        self.__real_adapter__ = True

    def __call__(self) -> int:
        value = time.perf_counter_ns()
        if isinstance(value, bool) or not isinstance(value, int):
            raise RuntimeError("clock must return int nanoseconds (fail-closed)")
        if value < 0:
            raise RuntimeError("clock must be monotonic non-negative (fail-closed)")
        return value


class RealD003Baseline:
    """Frozen D-003 production baseline on the governing session (D-056).

    Exact production semantics from ml-service/app.py without modifying it:
    strip_region, youth production bias (suppressed for Gov24 orgs via the
    frozen youth_source_bias), lexical bias 0.01, RERANK=0 with COSINE_MIN
    0.78, CANDIDATES=30, exact multilingual-e5-base query embedding.
    Region behavior matches the standing contract: production rejects region
    filters, so the baseline never filters by region (rp always None).
    Benchmark tasks carry no age, so age is None (production NULL parity).
    The ONLY semantic replacement is the pinned evaluation_as_of_date in
    BOTH expiry predicates instead of runtime CURRENT_DATE.
    """

    def __init__(self, session: RealEvaluationSession, embedding_fn: Callable[[str], list[float]]):
        self._session = session
        self._embedding_fn = embedding_fn
        self.__real_adapter__ = True

    def __call__(self, task_id: str, query: str, baseline: dict, evaluation_context: dict | None = None) -> dict:
        if not isinstance(baseline, dict) or dict(baseline) != dict(FROZEN_D003_BASELINE):
            raise ValueError("D-003 descriptor drift rejected (fail-closed: exact frozen baseline only)")
        pinned = validate_pinned_context(evaluation_context) if evaluation_context is not None else self._session.pinned_context
        as_of = pinned["evaluation_as_of_date"]
        if not isinstance(query, str) or not query.strip():
            raise ValueError("D-003 baseline refuses blank query (fail-closed)")
        q_stripped = strip_region(query)
        if not q_stripped.strip():
            raise ValueError("D-003 baseline refuses blank query after strip_region (fail-closed)")
        qvec = self._embedding_fn(f"{EMBED_QUERY_PREFIX}{q_stripped}")
        if len(qvec) != EMBED_DIM:
            raise ValueError(f"D-003 embedding dim must be {EMBED_DIM}, got {len(qvec)} (fail-closed)")
        rows = self._session.execute_readonly(D003_SQL, {
            "vec": format_qvec(qvec),
            "age": None,
            "rp": None,
            "youth_bias": youth_source_bias(q_stripped),
            "lexical_terms": lexical_overlap_terms(q_stripped),
            "lexical_bias": FROZEN_D003_BASELINE["LEXICAL_BIAS"],
            "n": FROZEN_D003_BASELINE["CANDIDATES"],
            "as_of": as_of,
        })
        self._session.note_d003_query()
        cands = [dict(zip(D003_RESULT_COLUMNS, r)) for r in rows]
        floor = FROZEN_D003_BASELINE["COSINE_MIN"]
        kept = [c for c in cands if isinstance(c.get("score"), (int, float)) and c["score"] >= floor]
        return {
            "task_id": task_id,
            "n": len(kept),
            "descriptor": dict(FROZEN_D003_BASELINE),
            "evaluation_as_of_date": as_of,
        }


class TransportOutcome:
    """Single HTTP attempt outcome (status XOR error; redirect carries location)."""

    def __init__(self, status: int | None = None, location: str | None = None, error: str | None = None):
        if status is not None and error is not None:
            raise ValueError("transport outcome carries status XOR error (fail-closed)")
        if error is not None and error not in ("network", "tls", "timeout"):
            raise ValueError(f"unknown transport error {error!r} (fail-closed)")
        self.status = status
        self.location = location
        self.error = error


def check_url_with_transport(url: str, transport: Callable[[str, str, tuple], TransportOutcome]) -> bool:
    """Frozen prereg section 9 HTTP state machine driven by an injectable transport.

    HEAD first with the fixed timeout pair, 1 retry (max 2 attempts) per
    request URL/method with no backoff, <=3 redirects preserving method,
    GET fallback only on HEAD 405/501 or exhausted network/TLS cause,
    timeout/5xx retry-only, ordinary 4xx immediate fail, 2xx success.
    Pure logic over the transport callable; no network here.
    """
    timeout = (CONNECT_TIMEOUT_S, READ_TIMEOUT_S)

    def run_method(method: str, start_url: str) -> tuple[bool, bool]:
        current = start_url
        redirects = 0
        saw_fallback_cause = False
        while True:
            for _ in range(MAX_ATTEMPTS):
                try:
                    out = transport(current, method, timeout)
                except Exception:
                    return False, False
                if not isinstance(out, TransportOutcome):
                    return False, False
                status, location, error = out.status, out.location, out.error
                if status is not None and 200 <= status <= 299:
                    return True, saw_fallback_cause
                if status is not None and 300 <= status <= 399:
                    break
                if status in (405, 501):
                    if method == "HEAD":
                        return False, True
                    if status == 501:
                        saw_fallback_cause = False
                        continue
                    return False, False
                if status is not None and 400 <= status <= 499:
                    return False, False
                if status is not None and 500 <= status <= 599:
                    saw_fallback_cause = False
                    continue
                if error in ("network", "tls"):
                    saw_fallback_cause = True
                    continue
                saw_fallback_cause = False
                continue
            else:
                return False, saw_fallback_cause
            redirects += 1
            if redirects > MAX_REDIRECTS:
                return False, False
            if not isinstance(location, str) or not location.strip():
                return False, False
            saw_fallback_cause = False
            current = location.strip()
    if not isinstance(url, str) or not url.strip():
        return False
    head_ok, head_fallback = run_method("HEAD", url.strip())
    if head_ok:
        return True
    if head_fallback:
        get_ok, _ = run_method("GET", url.strip())
        return get_ok
    return False


def http_client_transport(url: str, method: str = "HEAD", timeout: tuple = (CONNECT_TIMEOUT_S, READ_TIMEOUT_S)) -> TransportOutcome:
    """Real HTTP transport for FIRST-dev (implemented, NOT executed in D-056).

    Manual redirect handling (<=3 hops, method preserved) over http.client so
    the frozen per-hop attempt budget stays exact. The stdlib exposes a single
    timeout knob: the read bound (10s) is used per attempt and documented as
    such; the connect bound is not separately enforceable here.
    """
    import http.client
    import socket
    import ssl
    import urllib.parse

    try:
        parts = urllib.parse.urlparse(url)
    except Exception:
        return TransportOutcome(error="network")
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return TransportOutcome(error="network")
    path = parts.path or "/"
    if parts.query:
        path += "?" + parts.query
    if method not in ("HEAD", "GET"):
        return TransportOutcome(error="network")
    current_host, current_port, current_path = parts.hostname, parts.port, path
    use_tls = parts.scheme == "https"
    hops = 0
    while True:
        try:
            if use_tls:
                conn = http.client.HTTPSConnection(
                    current_host, current_port, timeout=timeout[1],
                    context=ssl.create_default_context(),
                )
            else:
                conn = http.client.HTTPConnection(current_host, current_port, timeout=timeout[1])
            try:
                conn.request(method, current_path, headers={"User-Agent": "benefit-compass-retrieval-v3-eval"})
                resp = conn.getresponse()
                status = resp.status
                location = resp.getheader("Location")
                try:
                    resp.read()
                except Exception:
                    pass
            finally:
                conn.close()
        except (socket.timeout, TimeoutError):
            return TransportOutcome(error="timeout")
        except (ssl.SSLError, ssl.CertificateError):
            return TransportOutcome(error="tls")
        except Exception:
            return TransportOutcome(error="network")
        if status is not None and 300 <= status <= 399:
            hops += 1
            if hops > MAX_REDIRECTS or not location:
                return TransportOutcome(status=status)
            nxt = urllib.parse.urljoin(f"{parts.scheme}://{current_host}{current_path}", location)
            try:
                nparts = urllib.parse.urlparse(nxt)
            except Exception:
                return TransportOutcome(status=status)
            if nparts.scheme not in ("http", "https") or not nparts.hostname:
                return TransportOutcome(status=status)
            use_tls = nparts.scheme == "https"
            current_host, current_port = nparts.hostname, nparts.port
            current_path = (nparts.path or "/") + (("?" + nparts.query) if nparts.query else "")
            continue
        return TransportOutcome(status=status, location=location)


class RealSafetyAdapter:
    """Real six-gate safety evidence over the pinned session corpus (D-056).

    The runner OWNS unsupported/ambiguous/production_exclusion and
    cross-checks them exactly: this adapter recomputes those three with the
    frozen functions over the same inputs (identical values or the runner
    fails closed to HOLD). The adapter measures only official_link,
    http_resolution, and cost — and returns structured HOLD wherever
    authoritative evidence is unavailable (never fabricated PASS).
    """

    def __init__(self, session: RealEvaluationSession, http_transport: Callable | None = None):
        self._session = session
        self._http_transport = http_transport if http_transport is not None else http_client_transport
        self.__real_adapter__ = True

    @staticmethod
    def _task_role(stratum: object) -> str | None:
        # Same role rule as the runner (stratum-carried for canonical sets;
        # any divergence fails closed at the runner cross-check, never PASS).
        if stratum == "unsupported_no_answer":
            return "unsupported"
        if stratum == "ambiguous":
            return "ambiguous"
        return None

    def __call__(self, payload: dict) -> dict:
        if not isinstance(payload, dict):
            raise ValueError("safety payload must be dict (fail-closed)")
        results = payload.get("results")
        if not isinstance(results, dict):
            raise ValueError("safety payload missing results (fail-closed)")
        task_results = results.get("task_results")
        if not isinstance(task_results, list) or not task_results:
            raise ValueError("safety payload missing task_results (fail-closed)")
        pinned = self._session.pinned_context
        as_of = pinned["evaluation_as_of_date"]
        unsupported_bools = []
        ambiguous_bools = []
        for tr in task_results:
            if not isinstance(tr, dict):
                raise ValueError("task result must be dict (fail-closed)")
            role = self._task_role(tr.get("stratum"))
            action = tr.get("safe_action")
            if role == "unsupported":
                unsupported_bools.append(action_correct_for_role(action, "unsupported"))
            elif role == "ambiguous":
                ambiguous_bools.append(action_correct_for_role(action, "ambiguous"))
        owned_unsupported = evaluate_owned_unsupported(unsupported_bools or None)
        owned_ambiguous = evaluate_owned_ambiguous(ambiguous_bools or None)
        internal_top5 = {
            tr.get("task_id"): [(d.get("source"), d.get("source_id")) for d in (tr.get("retrieved_internal") or [])[:5]]
            for tr in task_results
        }
        pe_gate, pe_det = check_production_exclusion(
            internal_top5, self._session.biz_end_lookup, as_of, len(task_results), len(task_results) * 5
        )
        owned_pe = {"gate": pe_gate, **pe_det}
        url_lookup = self._session.official_url_lookup
        collected: list[str] = []
        missing_url = 0
        visible_slots = 0
        for tr in task_results:
            for doc in (tr.get("retrieved") or [])[:5]:
                if not isinstance(doc, dict):
                    continue
                visible_slots += 1
                raw_url = url_lookup.get((doc.get("source"), doc.get("source_id")))
                if isinstance(raw_url, str) and raw_url.strip():
                    collected.append(raw_url.strip())
                else:
                    missing_url += 1
        unique_urls = dedupe_official_links(collected)
        url_diagnostics = {
            "visible_slots": visible_slots,
            "collected_urls": len(collected),
            "unique_urls": len(unique_urls),
            "missing_url_fields": missing_url,
            "url_field": "apply_url",
        }
        official_link = {"gate": "HOLD", "detail": OFFICIAL_LINK_MAPPING_BLOCKER, **url_diagnostics}
        http_resolution = {
            "gate": "HOLD",
            "detail": "official_link denominator has no authoritative source-match map; benchmark HTTP not executed (fail-closed HOLD)",
            **url_diagnostics,
        }
        cost = {
            "gate": "HOLD",
            "detail": COST_BASELINE_BLOCKER,
            "policies": len(self._session._policies or []),
            "corpus_rows_scanned": self._session.rows_scanned,
            "d003_queries": self._session.d003_queries,
            "extra_model_calls": 0,
        }
        return {
            "unsupported": owned_unsupported,
            "ambiguous": owned_ambiguous,
            "production_exclusion": owned_pe,
            "official_link": official_link,
            "http_resolution": http_resolution,
            "cost": cost,
        }


def build_real_adapters(
    session: RealEvaluationSession,
    *,
    model_loader: Callable[[], Any] | None = None,
    materialized_path: str | pathlib.Path | None = None,
    evalset_base: str | pathlib.Path | None = None,
    http_transport: Callable | None = None,
) -> dict:
    """Bind all eight real adapter surfaces to ONE governing session (D-056).

    Construction performs no IO. Every returned callable carries
    __real_adapter__ = True. The embedding instance is shared between the
    Candidate-A path and the D-003 baseline (single model load).
    """
    if not isinstance(session, RealEvaluationSession):
        raise ValueError("real adapters require the governing RealEvaluationSession (fail-closed)")

    embedding = RealEmbeddingAdapter(model_loader=model_loader)
    protected_loader = RealProtectedLoader(materialized_path=materialized_path, allowed_base=evalset_base)
    safety = RealSafetyAdapter(session, http_transport=http_transport)
    d003 = RealD003Baseline(session, embedding)
    clock = RealClock()

    def _mark(fn: Callable, name: str) -> Callable:
        fn.__real_adapter__ = True  # type: ignore[attr-defined]
        fn.__real_adapter_name__ = name  # type: ignore[attr-defined]
        return fn

    def evaluation_context_fn(sql: str) -> Any:
        return session.capture_executor(sql)

    def policy_loader() -> list[dict]:
        return session.load_corpus_policies()

    def corpus_provenance_fn() -> dict:
        return session.corpus_provenance()

    return {
        "embedding_fn": embedding,
        "policy_loader": _mark(policy_loader, "policy_loader"),
        "protected_loader": protected_loader,
        "safety_evidence_fn": safety,
        "d003_baseline_fn": d003,
        "evaluation_context_fn": _mark(evaluation_context_fn, "evaluation_context"),
        "clock_fn": clock,
        "corpus_provenance_fn": _mark(corpus_provenance_fn, "corpus_provenance"),
    }
