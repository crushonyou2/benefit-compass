"""통합 적재 데이터의 출처·링크·지역·임베딩 품질을 JSON으로 기록한다."""
import json
import os
import pathlib

from dotenv import load_dotenv
import psycopg2

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
DB = os.getenv("DATABASE_URL", "").strip()
OUTFILE = pathlib.Path(__file__).resolve().parent / "data_quality.json"

SQL = """
SELECT source,
       count(*) AS policies,
       count(*) FILTER (WHERE apply_url IS NULL OR apply_url !~ '^https?://') AS missing_links,
       count(*) FILTER (WHERE cardinality(region_codes) > 0) AS region_coded
FROM policy
GROUP BY source
ORDER BY source
"""


def main():
    if not DB:
        raise SystemExit("DATABASE_URL 없음")
    conn = psycopg2.connect(DB)
    cur = conn.cursor()
    cur.execute(SQL)
    by_source = {
        source: {"policies": policies, "missing_links": missing, "region_coded": region}
        for source, policies, missing, region in cur.fetchall()
    }
    cur.execute("SELECT count(*) FROM policy_chunk WHERE embedding IS NULL")
    missing_embeddings = cur.fetchone()[0]
    cur.execute("""
        SELECT count(*) FROM (
          SELECT title FROM policy GROUP BY title HAVING count(DISTINCT source) > 1
        ) duplicated
    """)
    cross_source_same_title = cur.fetchone()[0]
    cur.close()
    conn.close()

    result = {
        "by_source": by_source,
        "missing_embeddings": missing_embeddings,
        "cross_source_same_title": cross_source_same_title,
        "region_filter_exposed": False,
    }
    OUTFILE.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"저장 → {OUTFILE}")


if __name__ == "__main__":
    main()
