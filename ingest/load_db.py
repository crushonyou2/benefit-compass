"""
*_policies.jsonl + chunks.jsonl → Postgres(pgvector) 적재.
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


def validate_chunk_coverage(policies, chunks):
    policy_keys = {(policy["source"], policy["source_id"]) for policy in policies}
    chunk_keys = {(chunk["source"], chunk["source_id"]) for chunk in chunks}
    missing = policy_keys - chunk_keys
    unknown = chunk_keys - policy_keys
    if not policy_keys or missing or unknown:
        raise SystemExit(
            "정책·청크 코퍼스 불일치: "
            f"policies={len(policy_keys)}, missing_chunks={len(missing)}, "
            f"unknown_chunks={len(unknown)}"
        )


def main() -> None:
    if not DB:
        raise SystemExit("DATABASE_URL 없음 — .env 확인")

    conn = psycopg2.connect(DB)
    conn.set_session(readonly=False, autocommit=False)
    cur = conn.cursor()
    cur.execute(SCHEMA.read_text(encoding="utf-8"))
    conn.commit()

    infiles = sorted(DATA.glob("*_policies.jsonl"))
    if not infiles:
        raise SystemExit(f"{DATA}에 정책 파일 없음 — 수집 스크립트를 먼저 실행")
    policies = [
        json.loads(line)
        for infile in infiles
        for line in infile.open(encoding="utf-8")
    ]
    chunks = [json.loads(line) for line in (DATA / "chunks.jsonl").open(encoding="utf-8")]
    validate_chunk_coverage(policies, chunks)
    updates = ",".join(
        f"{column}=EXCLUDED.{column}"
        for column in COLS if column not in {"source", "source_id"}
    )
    policy_rows = [
        tuple(Json(policy.get("raw")) if column == "raw" else policy.get(column)
              for column in COLS)
        for policy in policies
    ]
    returned = execute_values(
        cur,
        f"INSERT INTO policy ({','.join(COLS)}) VALUES %s "
        "ON CONFLICT (source, source_id) DO UPDATE "
        f"SET {updates}, updated_at = now() RETURNING source, source_id, id",
        policy_rows,
        page_size=500,
        fetch=True,
    )
    id_map = {(source, source_id): policy_id for source, source_id, policy_id in returned}
    print(f"정책 {len(policies)}건 적재")

    rows = []
    for c in chunks:
        pid = id_map.get((c["source"], c["source_id"]))
        if pid is None:
            continue
        vec = "[" + ",".join(str(x) for x in c["embedding"]) + "]"
        rows.append((pid, c["chunk_index"], c["content"], vec))
    # 이번 코퍼스의 정책 청크를 한 트랜잭션에서 교체해 짧아진 문서의 낡은 청크도 남기지 않는다.
    if id_map:
        cur.execute("DELETE FROM policy_chunk WHERE policy_id = ANY(%s)",
                    (list(id_map.values()),))
    if rows:
        execute_values(
            cur,
            "INSERT INTO policy_chunk (policy_id, chunk_index, content, embedding) VALUES %s",
            rows,
            template="(%s,%s,%s,%s::vector)",
        )
    conn.commit()
    print(f"청크 {len(rows)}건 적재 완료")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
