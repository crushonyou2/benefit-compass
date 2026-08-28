"""
검색 테스트 — 이원 구조(구조적 자격필터 + 벡터 검색) 동작 확인.

  python search.py "전세 보증금 지원 받고 싶어"
  python search.py "청년 월세 지원" --age 28 --region 11 --k 5

--age    : 연령 자격필터 (해당 연령이 정책 대상 범위 안인 것만)
--region : 법정동코드 앞자리 prefix (서울=11, 경기=41 ...) 자격필터
"""
import os
import argparse
import pathlib
import sys

from dotenv import load_dotenv
import psycopg2
from sentence_transformers import SentenceTransformer

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ml-service"))
from source_ranking import youth_source_bias
load_dotenv(ROOT / ".env")
DB = os.getenv("DATABASE_URL", "").strip()

SQL = """
SELECT t.source, t.title, t.org, t.summary, t.age_min, t.age_max,
       1 - t.dist AS score, t.content, t.apply_url
FROM (
  SELECT DISTINCT ON (p.id) p.source, p.source_id, p.title, p.org, p.summary,
         p.age_min, p.age_max, c.content, p.apply_url,
         (c.embedding <=> %(vec)s::vector) AS dist
  FROM policy_chunk c
  JOIN policy p ON p.id = c.policy_id
  WHERE ( %(age)s IS NULL OR p.age_limit_yn IS NOT TRUE
          OR %(age)s BETWEEN p.age_min AND p.age_max )
    AND ( %(rp)s IS NULL OR cardinality(p.region_codes) = 0
          OR EXISTS (SELECT 1 FROM unnest(p.region_codes) rc WHERE rc LIKE %(rp)s) )
    AND ( p.biz_end IS NULL OR p.biz_end >= CURRENT_DATE )
  ORDER BY p.id, c.embedding <=> %(vec)s::vector
) t
ORDER BY t.dist - CASE WHEN t.source = 'youth' THEN %(youth_bias)s ELSE 0 END,
         t.dist, t.source, t.source_id
LIMIT %(k)s
"""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--age", type=int, default=None)
    ap.add_argument("--region", default=None, help="법정동코드 앞자리 (서울=11)")
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args()

    if not DB:
        raise SystemExit("DATABASE_URL 없음 — .env 확인")

    model = SentenceTransformer("intfloat/multilingual-e5-base")
    qvec = model.encode([f"query: {args.query}"], normalize_embeddings=True)[0]
    vec = "[" + ",".join(f"{x:.6f}" for x in qvec) + "]"

    conn = psycopg2.connect(DB)
    cur = conn.cursor()
    cur.execute(SQL, {
        "vec": vec,
        "age": args.age,
        "rp": (f"{args.region}%" if args.region else None),
        "youth_bias": youth_source_bias(args.query),
        "k": args.k,
    })
    rows = cur.fetchall()
    cur.close()
    conn.close()

    flt = []
    if args.age is not None:
        flt.append(f"연령 {args.age}세")
    if args.region:
        flt.append(f"지역 {args.region}*")
    print(f'질의: "{args.query}"' + (f"  [필터: {', '.join(flt)}]" if flt else ""))
    print("-" * 70)
    for i, (source, title, org, summary, amin, amax, score, content, url) in enumerate(rows, 1):
        age = f"{amin}~{amax}세" if amin is not None else "연령무관"
        print(f"{i}. [{score:.3f}] {title}  ({source} / {org}, {age})")
        if summary:
            print(f"   {summary}")
        if url:
            print(f"   공식 링크: {url}")


if __name__ == "__main__":
    main()
