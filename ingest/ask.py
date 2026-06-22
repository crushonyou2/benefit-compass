"""
RAG 완성 — 검색(R) + 근거 기반 답변 생성(G).

  python ask.py "28살 서울 사는데 월세 지원 받을 수 있어?" --age 28 --region 11

검색으로 찾은 정책만 근거로 Gemini가 답하고, 정책명을 인용한다(할루시네이션 방지).
필요: DATABASE_URL, GEMINI_API_KEY
"""
import os
import argparse
import pathlib

from dotenv import load_dotenv
import psycopg2
from sentence_transformers import SentenceTransformer
from google import genai

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
DB = os.getenv("DATABASE_URL", "").strip()
GEN_MODEL = "gemini-3.5-flash"  # 현행 stable flash (답변 생성)

RETRIEVE = """
SELECT t.title, t.org, t.support_content, t.apply_method, t.apply_url,
       t.age_min, t.age_max, t.income_etc, 1 - t.dist AS score
FROM (
  SELECT DISTINCT ON (p.id) p.id, p.title, p.org, p.support_content,
         p.apply_method, p.apply_url, p.age_min, p.age_max, p.income_etc,
         (c.embedding <=> %(vec)s::vector) AS dist
  FROM policy_chunk c
  JOIN policy p ON p.id = c.policy_id
  WHERE ( %(age)s IS NULL OR p.age_limit_yn IS NOT TRUE
          OR %(age)s BETWEEN p.age_min AND p.age_max )
    AND ( %(rp)s IS NULL OR cardinality(p.region_codes) = 0
          OR EXISTS (SELECT 1 FROM unnest(p.region_codes) rc WHERE rc LIKE %(rp)s) )
  ORDER BY p.id, c.embedding <=> %(vec)s::vector
) t
ORDER BY t.dist
LIMIT %(k)s
"""

PROMPT = """너는 정부 지원금 안내 도우미다. 아래 [정책 목록]에 있는 내용만 근거로 답해라.
목록에 없는 내용은 지어내지 말고, 관련 정책이 없으면 "해당하는 정책을 찾지 못했어요"라고 말해라.
답변에는 반드시 근거가 된 정책명을 함께 언급해라.

[사용자 질문]
{question}

[정책 목록]
{context}

[답변]"""


def retrieve(query, age, region, k=5):
    model = SentenceTransformer("intfloat/multilingual-e5-base")
    qvec = model.encode([f"query: {query}"], normalize_embeddings=True)[0]
    vec = "[" + ",".join(f"{x:.6f}" for x in qvec) + "]"
    conn = psycopg2.connect(DB)
    cur = conn.cursor()
    cur.execute(RETRIEVE, {"vec": vec, "age": age,
                           "rp": (f"{region}%" if region else None), "k": k})
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def build_context(rows):
    blocks = []
    for title, org, support, apply_m, url, amin, amax, income, score in rows:
        age = f"{amin}~{amax}세" if amin is not None else "연령무관"
        blocks.append(
            f"- 정책명: {title} ({org})\n"
            f"  지원대상 연령: {age} / 소득조건: {income or '명시 없음'}\n"
            f"  지원내용: {support or '명시 없음'}\n"
            f"  신청방법: {apply_m or '명시 없음'}\n"
            f"  신청링크: {url or '명시 없음'}"
        )
    return "\n".join(blocks)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("query")
    ap.add_argument("--age", type=int, default=None)
    ap.add_argument("--region", default=None)
    ap.add_argument("--k", type=int, default=5)
    args = ap.parse_args()
    if not DB or not os.getenv("GEMINI_API_KEY", "").strip():
        raise SystemExit("DATABASE_URL / GEMINI_API_KEY 확인")

    rows = retrieve(args.query, args.age, args.region, args.k)
    if not rows:
        print("자격 조건에 맞는 정책이 없습니다.")
        return
    context = build_context(rows)

    client = genai.Client(api_key=os.getenv("GEMINI_API_KEY").strip())
    resp = client.models.generate_content(
        model=GEN_MODEL,
        contents=PROMPT.format(question=args.query, context=context),
    )
    print(f'질문: {args.query}\n' + "=" * 70)
    print(resp.text)
    print("=" * 70)
    print("근거 정책:", ", ".join(r[0] for r in rows))


if __name__ == "__main__":
    main()
