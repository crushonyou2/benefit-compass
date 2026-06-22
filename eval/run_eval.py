"""
검색 품질 평가 — evalset.jsonl 의 각 질문으로 검색해, 정답 정책이 상위 k에 있는지 측정.
지표: recall@1/5/10, MRR@10. (질문당 정답 1개이므로 recall@k = hit@k)

이게 포트폴리오의 '수치'. 이후 리랭킹/청킹 변경 전후로 다시 돌려 개선폭을 기록한다.

필요: DATABASE_URL
사용법: python run_eval.py
"""
import os
import json
import pathlib

from dotenv import load_dotenv
import psycopg2
from sentence_transformers import SentenceTransformer

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
DB = os.getenv("DATABASE_URL", "").strip()
EVALFILE = pathlib.Path(__file__).resolve().parent / "evalset.jsonl"
RESULTFILE = pathlib.Path(__file__).resolve().parent / "results.json"

KS = [1, 5, 10]
TOPK = 10

SQL = """
SELECT t.source_id FROM (
  SELECT DISTINCT ON (p.id) p.source_id, (c.embedding <=> %(vec)s::vector) AS dist
  FROM policy_chunk c JOIN policy p ON p.id = c.policy_id
  ORDER BY p.id, c.embedding <=> %(vec)s::vector
) t
ORDER BY t.dist
LIMIT %(k)s
"""


def main():
    if not DB:
        raise SystemExit("DATABASE_URL 없음")
    if not EVALFILE.exists():
        raise SystemExit("evalset.jsonl 없음 — 먼저 make_evalset.py 실행")

    items = [json.loads(l) for l in EVALFILE.open(encoding="utf-8")]
    model = SentenceTransformer("intfloat/multilingual-e5-base")
    conn = psycopg2.connect(DB)
    cur = conn.cursor()

    ranks = []
    for it in items:
        qvec = model.encode([f"query: {it['query']}"], normalize_embeddings=True)[0]
        vec = "[" + ",".join(f"{x:.6f}" for x in qvec) + "]"
        cur.execute(SQL, {"vec": vec, "k": TOPK})
        ids = [r[0] for r in cur.fetchall()]
        rank = ids.index(it["gold_source_id"]) + 1 if it["gold_source_id"] in ids else 0
        ranks.append(rank)
    cur.close()
    conn.close()

    n = len(ranks)
    results = {"n": n, "model": "multilingual-e5-base", "top_k": TOPK}
    print(f"평가 문항: {n}")
    print("-" * 40)
    for k in KS:
        recall = sum(1 for r in ranks if 1 <= r <= k) / n
        results[f"recall@{k}"] = round(recall, 4)
        print(f"recall@{k:<2}: {recall:.3f}")
    mrr = sum((1 / r if r else 0) for r in ranks) / n
    results["mrr@10"] = round(mrr, 4)
    print(f"MRR@{TOPK} : {mrr:.3f}")
    print(f"top-{TOPK} 내 정답 포함: {sum(1 for r in ranks if r)}/{n}")

    RESULTFILE.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장 → {RESULTFILE}")


if __name__ == "__main__":
    main()
