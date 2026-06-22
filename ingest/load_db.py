"""
youth_policies.jsonl + chunks.jsonl → Postgres(pgvector) 적재.
schema.sql 자동 적용(멱등). 재실행 시 UPSERT.

필요: DATABASE_URL (Neon 등 무료 Postgres, pgvector 지원)
사용법: python load_db.py
"""
import os
import json
import pathlib

from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import execute_values, Json

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
DB = os.getenv("DATABASE_URL", "").strip()
DATA = pathlib.Path(__file__).resolve().parent / "data"
SCHEMA = ROOT / "db" / "schema.sql"

COLS = ["source", "source_id", "title", "summary", "support_content", "keywords",
        "category_large", "category_mid", "org", "apply_method", "screening_method",
        "apply_url", "submit_docs", "etc_note", "biz_start", "biz_end", "apply_period",
        "age_min", "age_max", "age_limit_yn", "income_min", "income_max", "income_cond",
        "income_etc", "marriage_status", "region_codes", "add_qualify", "raw"]


def main() -> None:
    if not DB:
        raise SystemExit("DATABASE_URL 없음 — .env 확인")

    conn = psycopg2.connect(DB)
    cur = conn.cursor()
    cur.execute(SCHEMA.read_text(encoding="utf-8"))
    conn.commit()

    policies = [json.loads(l) for l in (DATA / "youth_policies.jsonl").open(encoding="utf-8")]
    id_map = {}
    for p in policies:
        vals = [Json(p.get("raw")) if c == "raw" else p.get(c) for c in COLS]
        cur.execute(
            f"INSERT INTO policy ({','.join(COLS)}) "
            f"VALUES ({','.join(['%s'] * len(COLS))}) "
            "ON CONFLICT (source, source_id) DO UPDATE "
            "SET title = EXCLUDED.title, updated_at = now() RETURNING id",
            vals,
        )
        id_map[(p["source"], p["source_id"])] = cur.fetchone()[0]
    conn.commit()
    print(f"정책 {len(policies)}건 적재")

    chunks = [json.loads(l) for l in (DATA / "chunks.jsonl").open(encoding="utf-8")]
    rows = []
    for c in chunks:
        pid = id_map.get((c["source"], c["source_id"]))
        if pid is None:
            continue
        vec = "[" + ",".join(str(x) for x in c["embedding"]) + "]"
        rows.append((pid, c["chunk_index"], c["content"], vec))
    execute_values(
        cur,
        "INSERT INTO policy_chunk (policy_id, chunk_index, content, embedding) VALUES %s "
        "ON CONFLICT (policy_id, chunk_index) DO UPDATE "
        "SET content = EXCLUDED.content, embedding = EXCLUDED.embedding",
        rows,
        template="(%s,%s,%s,%s::vector)",
    )
    conn.commit()
    print(f"청크 {len(rows)}건 적재 완료")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
