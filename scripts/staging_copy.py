"""
Staging DB에 production 데이터를 복제한다 — P1 검증용.

- production: .env DATABASE_URL (Neon, 읽기 전용)
- staging: postgresql://postgres:postgres@localhost:5433/benefit (local pgvector, localhost-only)

이 스크립트는 staging을 완전히 비우고 production을 복제한다.
policy / policy_chunk의 id를 보존해 FK를 유지한다.
"""
import os
import pathlib
import urllib.parse

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import Json
from psycopg2.extensions import ISOLATION_LEVEL_REPEATABLE_READ

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
SCHEMA = ROOT / "db" / "schema.sql"

ALLOWED_STAGING_HOSTS = {"localhost", "127.0.0.1", "::1"}


def parse_dsn_host(dsn: str) -> str | None:
    try:
        parsed = urllib.parse.urlparse(dsn)
        host = parsed.hostname
        return host
    except Exception:
        return None


def is_allowed_staging_dsn(dsn: str) -> bool:
    host = parse_dsn_host(dsn)
    return host in ALLOWED_STAGING_HOSTS


def validate_copy_targets(prod_url: str, staging_url: str) -> None:
    if not prod_url:
        raise ValueError("DATABASE_URL 없음 — prod_url 비어 있음")
    if prod_url == staging_url:
        raise ValueError("refusing to copy: PROD_URL and STAGING_URL are identical — check STAGING_DATABASE_URL")
    if not is_allowed_staging_dsn(staging_url):
        host = parse_dsn_host(staging_url) or "?"
        raise ValueError(f"refusing to copy: STAGING_URL host '{host}' not in allowed {sorted(ALLOWED_STAGING_HOSTS)} — use local pgvector staging")


def mask_dsn(dsn: str) -> str:
    try:
        p = urllib.parse.urlparse(dsn)
        host = p.hostname or "?"
        port = f":{p.port}" if p.port else ""
        db = p.path.lstrip("/") or "?"
        return f"{host}{port}/{db}"
    except Exception:
        return "[masked]"


def validate_counts(prod_counts, staging_counts) -> list[str]:
    errors = []
    if prod_counts["policy_total"] != staging_counts["policy_total"]:
        errors.append(f"policy total mismatch prod={prod_counts['policy_total']} staging={staging_counts['policy_total']}")
    if prod_counts["policy_by_source"] != staging_counts["policy_by_source"]:
        errors.append(f"policy by_source mismatch prod={prod_counts['policy_by_source']} staging={staging_counts['policy_by_source']}")
    if prod_counts["chunk_total"] != staging_counts["chunk_total"]:
        errors.append(f"chunk total mismatch prod={prod_counts['chunk_total']} staging={staging_counts['chunk_total']}")
    if prod_counts["missing_embeddings"] != staging_counts["missing_embeddings"]:
        errors.append(f"missing_embeddings mismatch prod={prod_counts['missing_embeddings']} staging={staging_counts['missing_embeddings']}")
    if prod_counts["no_chunk"] != staging_counts["no_chunk"]:
        errors.append(f"policies_without_chunks mismatch prod={prod_counts['no_chunk']} staging={staging_counts['no_chunk']}")
    if prod_counts["orphan"] != staging_counts["orphan"]:
        errors.append(f"orphan_chunks mismatch prod={prod_counts['orphan']} staging={staging_counts['orphan']}")
    if prod_counts["duplicate"] != staging_counts["duplicate"]:
        errors.append(f"duplicate mismatch prod={prod_counts['duplicate']} staging={staging_counts['duplicate']}")
    return errors


def _collect_counts(cur) -> dict:
    cur.execute("SELECT count(*) FROM policy")
    total = cur.fetchone()[0]
    cur.execute("SELECT source, count(*) FROM policy GROUP BY source ORDER BY source")
    by_source = {s: c for s, c in cur.fetchall()}
    cur.execute("SELECT count(*) FROM policy_chunk")
    chunk_total = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM policy_chunk WHERE embedding IS NULL")
    missing = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM policy p WHERE NOT EXISTS (SELECT 1 FROM policy_chunk c WHERE c.policy_id=p.id)")
    no_chunk = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM policy_chunk c WHERE NOT EXISTS (SELECT 1 FROM policy p WHERE p.id=c.policy_id)")
    orphan = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM (SELECT source, source_id FROM policy GROUP BY source, source_id HAVING count(*)>1) d")
    dup = cur.fetchone()[0]
    return {"policy_total": total, "policy_by_source": by_source, "chunk_total": chunk_total, "missing_embeddings": missing, "no_chunk": no_chunk, "orphan": orphan, "duplicate": dup}


def copy():
    prod_url = os.getenv("DATABASE_URL", "").strip()
    staging_url = os.getenv("STAGING_DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/benefit").strip()
    validate_copy_targets(prod_url, staging_url)
    print("prod -> staging copy")
    print(f"prod: [masked] ({mask_dsn(prod_url)})")
    print(f"staging: {mask_dsn(staging_url)}")

    prod = psycopg2.connect(prod_url)
    staging = psycopg2.connect(staging_url)
    prod.set_isolation_level(ISOLATION_LEVEL_REPEATABLE_READ)
    prod.set_session(readonly=True, autocommit=False)
    staging.set_session(autocommit=False)

    try:
        pcur = prod.cursor()
        pcur.execute("BEGIN;")

        scur = staging.cursor()
        scur.execute(SCHEMA.read_text(encoding="utf-8"))
        staging.commit()
        scur.execute("TRUNCATE policy_chunk, policy RESTART IDENTITY CASCADE")
        staging.commit()
        print("staging truncated")

        pcur.execute("""
            SELECT id, source, source_id, title, summary, support_content, keywords,
                   category_large, category_mid, org, apply_method, screening_method,
                   apply_url, submit_docs, etc_note, biz_start, biz_end, apply_period,
                   age_min, age_max, age_limit_yn, income_min, income_max, income_cond,
                   income_etc, marriage_status, region_codes, add_qualify, raw,
                   created_at, updated_at
            FROM policy ORDER BY id
        """)
        rows = pcur.fetchall()
        cols = ["id", "source", "source_id", "title", "summary", "support_content", "keywords",
                "category_large", "category_mid", "org", "apply_method", "screening_method",
                "apply_url", "submit_docs", "etc_note", "biz_start", "biz_end", "apply_period",
                "age_min", "age_max", "age_limit_yn", "income_min", "income_max", "income_cond",
                "income_etc", "marriage_status", "region_codes", "add_qualify", "raw",
                "created_at", "updated_at"]
        policy_rows = []
        for r in rows:
            lst = list(r)
            if lst[28] is not None:
                lst[28] = Json(lst[28])
            policy_rows.append(tuple(lst))
        print(f"copying {len(policy_rows)} policies...")
        for row in policy_rows:
            scur.execute(
                f"INSERT INTO policy ({','.join(cols)}) VALUES ({','.join(['%s']*len(cols))})",
                row,
            )
        staging.commit()
        print(f"policies copied: {len(policy_rows)}")
        scur.execute("SELECT setval('policy_id_seq', (SELECT max(id) FROM policy))")
        staging.commit()

        pcur.execute("SELECT id, policy_id, chunk_index, content, embedding FROM policy_chunk ORDER BY id")
        chunk_rows = pcur.fetchall()
        copy_rows = []
        for cid, pid, idx, content, emb in chunk_rows:
            vec = None if emb is None else (f"[{','.join(str(x) for x in emb)}]" if isinstance(emb, list) else str(emb))
            copy_rows.append((cid, pid, idx, content, vec))
        print(f"copying {len(copy_rows)} chunks...")
        for row in copy_rows:
            scur.execute(
                "INSERT INTO policy_chunk (id, policy_id, chunk_index, content, embedding) VALUES (%s,%s,%s,%s,%s::vector)",
                row,
            )
        staging.commit()
        scur.execute("SELECT setval('policy_chunk_id_seq', (SELECT max(id) FROM policy_chunk))")
        staging.commit()
        print(f"chunks copied: {len(copy_rows)}")

        # collect source counts within same snapshot (before rollback)
        prod_counts = _collect_counts(pcur)
        prod_counts["label"] = "prod"
        # end snapshot
        prod.rollback()

        # collect staging counts
        staging_counts = _collect_counts(scur)
        staging_counts["label"] = "staging"
        print(f"prod counts: {prod_counts}")
        print(f"staging counts: {staging_counts}")
        errors = validate_counts(prod_counts, staging_counts)
        if errors:
            print("VALIDATION FAILED:")
            for e in errors:
                print(f"  - {e}")
            raise SystemExit(f"staging validation failed: {'; '.join(errors)}")
        print("staging validation ok — source and staging counts/coverage match")

        pcur.close()
        scur.close()
        prod.close()
        staging.close()
        print("staging copy complete")
    except Exception:
        try:
            staging.rollback()
        except Exception:
            pass
        try:
            prod.rollback()
        except Exception:
            pass
        raise

if __name__ == "__main__":
    copy()
