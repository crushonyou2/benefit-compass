"""
지역 필터 진단 — 함안/창업 관련 정책의 지역 관련 필드를 덤프해서
왜 서울 필터를 통과하는지 확인한다.
사용법: python inspect_region.py
"""
import os
import pathlib

from dotenv import load_dotenv
import psycopg2

load_dotenv(pathlib.Path(__file__).resolve().parent.parent / ".env")
conn = psycopg2.connect(os.getenv("DATABASE_URL", "").strip())
cur = conn.cursor()
cur.execute(
    """
    SELECT title, org,
           raw->>'pvsnInstGroupCd' AS grp,
           raw->>'rgtrInstCdNm'    AS rgtr_inst,
           region_codes
    FROM policy
    WHERE title LIKE %s OR org LIKE %s OR title LIKE %s
    LIMIT 30
    """,
    ('%함안%', '%함안%', '%창업%'),
)
for title, org, grp, rgtr, codes in cur.fetchall():
    head = codes[:4] if codes else codes
    print(f"grp={grp} | codes(n={len(codes) if codes else 0})={head} | rgtr={rgtr} | {title} | {org}")
cur.close()
conn.close()
