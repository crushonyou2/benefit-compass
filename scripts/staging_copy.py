"""
Staging DB에 production 데이터를 복제한다 — P1 검증용.

- production: .env DATABASE_URL (Neon)
- staging: postgresql://postgres:postgres@localhost:5433/benefit (local pgvector)

이 스크립트는 staging을 완전히 비우고 production을 복제한다.
policy / policy_chunk의 id를 보존해 FK를 유지한다.
"""
import os
import pathlib
import sys

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values, Json

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
PROD_URL = os.getenv("DATABASE_URL", "").strip()
STAGING_URL = os.getenv("STAGING_DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/benefit")
SCHEMA = ROOT / "db" / "schema.sql"

if not PROD_URL:
    raise SystemExit("DATABASE_URL 없음")

def copy():
    # safety: production and staging must not be the same DSN
    if PROD_URL == STAGING_URL:
        raise SystemExit("refusing to copy: PROD_URL and STAGING_URL are identical — check STAGING_DATABASE_URL")
    # minimal guard: staging should not point to Neon production host
    if "neon.tech" in STAGING_URL and "localhost" not in STAGING_URL and "127.0.0.1" not in STAGING_URL:
        # allow explicit override but warn — require localhost for this project
        raise SystemExit("refusing to copy: STAGING_URL looks like production Neon host — use local pgvector staging")
    print("prod -> staging copy")
    print("prod: [masked] (Neon)")
    print(f"staging: {STAGING_URL}")
    prod = psycopg2.connect(PROD_URL)
    staging = psycopg2.connect(STAGING_URL)
    prod.set_session(readonly=True, autocommit=True)
    staging.set_session(autocommit=False)

    # staging schema
    scur = staging.cursor()
    scur.execute(SCHEMA.read_text(encoding="utf-8"))
    staging.commit()
    # truncate staging — destructive only on staging
    scur.execute("TRUNCATE policy_chunk, policy RESTART IDENTITY CASCADE")
    staging.commit()
    print("staging truncated")
    # copy policy
    pcur = prod.cursor()
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
    # Convert raw to Json wrapper for psycopg2
    policy_rows = []
    for r in rows:
        lst = list(r)
        # raw at index 28 (0-based) when cols includes created_at/updated_at
        if lst[28] is not None:
            lst[28] = Json(lst[28])
        policy_rows.append(tuple(lst))
    print(f"copying {len(policy_rows)} policies...")
    # row-by-row to avoid mogrify batch issues
    for row in policy_rows:
        try:
            scur.execute(
                f"INSERT INTO policy ({','.join(cols)}) VALUES ({','.join(['%s']*len(cols))})",
                row,
            )
        except Exception as e:
            print(f"failed policy {row[1]}/{row[2]}: {e}")
            raise
    staging.commit()
    print(f"policies copied: {len(policy_rows)}")

    # fix sequence
    scur.execute("SELECT setval('policy_id_seq', (SELECT max(id) FROM policy))")
    staging.commit()

    # copy chunks
    pcur.execute("SELECT id, policy_id, chunk_index, content, embedding FROM policy_chunk ORDER BY id")
    chunk_rows = pcur.fetchall()
    copy_rows = []
    for cid, pid, idx, content, emb in chunk_rows:
        if emb is None:
            vec = None
        else:
            if isinstance(emb, list):
                vec = "[" + ",".join(str(x) for x in emb) + "]"
            else:
                vec = str(emb)
        copy_rows.append((cid, pid, idx, content, vec))
    print(f"copying {len(copy_rows)} chunks...")
    for row in copy_rows:
        try:
            scur.execute(
                "INSERT INTO policy_chunk (id, policy_id, chunk_index, content, embedding) VALUES (%s,%s,%s,%s,%s::vector)",
                row,
            )
        except Exception as e:
            print(f"failed chunk {row[0]}: {e}")
            raise
    staging.commit()
    scur.execute("SELECT setval('policy_chunk_id_seq', (SELECT max(id) FROM policy_chunk))")
    staging.commit()
    print(f"chunks copied: {len(copy_rows)}")

    # validate counts
    scur.execute("SELECT source, count(*) FROM policy GROUP BY source ORDER BY source")
    print("staging policy by source:", scur.fetchall())
    scur.execute("SELECT count(*) FROM policy_chunk")
    print("staging chunks:", scur.fetchone()[0])
    scur.execute("SELECT count(*) FROM policy_chunk WHERE embedding IS NULL")
    print("staging missing embeddings:", scur.fetchone()[0])

    pcur.close()
    scur.close()
    prod.close()
    staging.close()
    print("staging copy complete")

if __name__ == "__main__":
    copy()
