"""
검색 품질 평가 — evalset.jsonl 의 각 질문으로 검색해, 정답 정책이 상위 k에 있는지 측정.
지표: recall@1/5/10, MRR@10. (질문당 정답 1개이므로 recall@k = hit@k)

이게 포트폴리오의 '수치'. 이후 리랭킹/청킹 변경 전후로 다시 돌려 개선폭을 기록한다.

필요: DATABASE_URL
사용법: python run_eval.py
"""
import argparse
import json
import os
import pathlib
import sys

from dotenv import load_dotenv
import psycopg2
from sentence_transformers import SentenceTransformer

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ml-service"))
from source_ranking import ranking_metadata, youth_source_bias
load_dotenv(ROOT / ".env")
DB = os.getenv("DATABASE_URL", "").strip()
HERE = pathlib.Path(__file__).resolve().parent

KS = [1, 5, 10]
TOPK = 10

SQL = """
SELECT t.source, t.source_id FROM (
  SELECT DISTINCT ON (p.id) p.source, p.source_id,
         (c.embedding <=> %(vec)s::vector) AS dist
  FROM policy_chunk c JOIN policy p ON p.id = c.policy_id
  ORDER BY p.id, c.embedding <=> %(vec)s::vector
) t
ORDER BY t.dist - CASE WHEN t.source = 'youth' THEN %(youth_bias)s ELSE 0 END,
         t.dist, t.source, t.source_id
LIMIT %(k)s
"""


def parse_args():
    parser = argparse.ArgumentParser(description="정답 정책의 검색 순위를 평가합니다")
    parser.add_argument("--eval-file", type=pathlib.Path, default=HERE / "evalset.jsonl")
    parser.add_argument("--output", type=pathlib.Path, default=HERE / "results.json")
    return parser.parse_args()


def load_items(path):
    if not path.exists():
        raise SystemExit(f"평가셋 없음: {path}")
    items = [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]
    if not items:
        raise SystemExit(f"평가셋이 비어 있습니다: {path}")
    for line_number, item in enumerate(items, 1):
        missing = [key for key in ("query", "gold_source_id") if not item.get(key)]
        if missing:
            raise SystemExit(f"평가셋 {line_number}행 필수값 누락: {', '.join(missing)}")
    return items


def main():
    args = parse_args()
    if not DB:
        raise SystemExit("DATABASE_URL 없음")
    items = load_items(args.eval_file)
    model = SentenceTransformer("intfloat/multilingual-e5-base")
    conn = psycopg2.connect(DB)
    cur = conn.cursor()

    ranked = []
    for it in items:
        qvec = model.encode([f"query: {it['query']}"], normalize_embeddings=True)[0]
        vec = "[" + ",".join(f"{x:.6f}" for x in qvec) + "]"
        cur.execute(SQL, {
            "vec": vec,
            "youth_bias": youth_source_bias(it["query"]),
            "k": TOPK,
        })
        ids = cur.fetchall()
        gold = (it.get("gold_source", "youth"), it["gold_source_id"])
        rank = ids.index(gold) + 1 if gold in ids else 0
        ranked.append((gold[0], rank))
    cur.close()
    conn.close()

    n = len(ranked)
    ranks = [rank for _, rank in ranked]
    eval_file = args.eval_file.resolve()
    try:
        eval_file = eval_file.relative_to(ROOT)
    except ValueError:
        pass
    results = {
        "n": n,
        "eval_file": str(eval_file),
        "model": "multilingual-e5-base",
        "top_k": TOPK,
        "source_ranking": ranking_metadata(),
    }
    print(f"평가 문항: {n}")
    print("-" * 40)
    for k in KS:
        recall = sum(1 for r in ranks if 1 <= r <= k) / n
        results[f"recall@{k}"] = round(recall, 4)
        print(f"recall@{k:<2}: {recall:.3f}")
    mrr = sum((1 / r if r else 0) for r in ranks) / n
    results["mrr@10"] = round(mrr, 4)
    results["by_source"] = {}
    for source in sorted({source for source, _ in ranked}):
        source_ranks = [rank for item_source, rank in ranked if item_source == source]
        results["by_source"][source] = {
            "n": len(source_ranks),
            "recall@1": round(sum(1 for rank in source_ranks if rank == 1) / len(source_ranks), 4),
            "recall@5": round(sum(1 for rank in source_ranks if 1 <= rank <= 5) / len(source_ranks), 4),
            "mrr@10": round(sum((1 / rank if rank else 0) for rank in source_ranks)
                            / len(source_ranks), 4),
        }
    print(f"MRR@{TOPK} : {mrr:.3f}")
    print(f"top-{TOPK} 내 정답 포함: {sum(1 for r in ranks if r)}/{n}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장 → {args.output}")


if __name__ == "__main__":
    main()
