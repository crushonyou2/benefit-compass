"""
리랭킹 적용 평가 — bi-encoder로 top-N 후보를 뽑고, cross-encoder 리랭커로 재정렬해 재측정.
run_eval.py(베이스라인)와 같은 평가셋·지표를 쓰고, results.json 이 있으면 개선폭을 함께 출력.

리랭커: BAAI/bge-reranker-v2-m3 (다국어, 로컬·무료). 첫 실행 시 모델 다운로드.
필요: DATABASE_URL
사용법: python run_eval_rerank.py
"""
import argparse
import json
import os
import pathlib
import sys

from dotenv import load_dotenv
import psycopg2
from sentence_transformers import SentenceTransformer, CrossEncoder

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ml-service"))
from source_ranking import ranking_metadata, youth_source_bias
load_dotenv(ROOT / ".env")
DB = os.getenv("DATABASE_URL", "").strip()
HERE = pathlib.Path(__file__).resolve().parent

KS = [1, 5, 10]
CANDIDATES = 30   # bi-encoder가 뽑는 후보 수 (리랭킹 대상)
TOPK = 10

CAND_SQL = """
SELECT t.source, t.source_id, t.content FROM (
  SELECT DISTINCT ON (p.id) p.source, p.source_id, c.content,
         (c.embedding <=> %(vec)s::vector) AS dist
  FROM policy_chunk c JOIN policy p ON p.id = c.policy_id
  ORDER BY p.id, c.embedding <=> %(vec)s::vector
) t
ORDER BY t.dist - CASE WHEN t.source = 'youth' THEN %(youth_bias)s ELSE 0 END,
         t.dist, t.source, t.source_id
LIMIT %(n)s
"""


def metrics(ranks, n):
    out = {}
    for k in KS:
        out[f"recall@{k}"] = round(sum(1 for r in ranks if 1 <= r <= k) / n, 4)
    out["mrr@10"] = round(sum((1 / r if r else 0) for r in ranks) / n, 4)
    return out


def parse_args():
    parser = argparse.ArgumentParser(description="교차 인코더 리랭킹 검색 품질을 평가합니다")
    parser.add_argument("--eval-file", type=pathlib.Path, default=HERE / "evalset.jsonl")
    parser.add_argument("--baseline", type=pathlib.Path, default=HERE / "results.json")
    parser.add_argument("--output", type=pathlib.Path, default=HERE / "results_rerank.json")
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

    embedder = SentenceTransformer("intfloat/multilingual-e5-base")
    print("리랭커 로드: BAAI/bge-reranker-v2-m3 (첫 실행 시 다운로드)")
    reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")

    conn = psycopg2.connect(DB)
    cur = conn.cursor()
    ranked = []
    for it in items:
        gold = (it.get("gold_source", "youth"), it["gold_source_id"])
        qvec = embedder.encode([f"query: {it['query']}"], normalize_embeddings=True)[0]
        vec = "[" + ",".join(f"{x:.6f}" for x in qvec) + "]"
        cur.execute(CAND_SQL, {
            "vec": vec,
            "youth_bias": youth_source_bias(it["query"]),
            "n": CANDIDATES,
        })
        cand = cur.fetchall()  # [(source, source_id, content), ...]
        if not cand:
            ranked.append((gold[0], 0))
            continue
        scores = reranker.predict([(it["query"], content) for _, _, content in cand],
                                  show_progress_bar=True)
        ordered = [key for key, _ in sorted(
            zip([(c[0], c[1]) for c in cand], scores), key=lambda x: x[1], reverse=True)]
        ranked.append((gold[0], ordered.index(gold) + 1 if gold in ordered[:TOPK] else 0))
    cur.close()
    conn.close()

    ranks = [rank for _, rank in ranked]
    n = len(ranks)
    rer = metrics(ranks, n)
    eval_file = args.eval_file.resolve()
    try:
        eval_file = eval_file.relative_to(ROOT)
    except ValueError:
        pass
    rer.update({
        "n": n,
        "eval_file": str(eval_file),
        "candidates": CANDIDATES,
        "reranker": "bge-reranker-v2-m3",
        "source_ranking": ranking_metadata(),
    })
    rer["by_source"] = {}
    for source in sorted({source for source, _ in ranked}):
        source_ranks = [rank for item_source, rank in ranked if item_source == source]
        rer["by_source"][source] = {"n": len(source_ranks), **metrics(source_ranks, len(source_ranks))}

    print(f"\n평가 문항: {n}  (후보 {CANDIDATES} → 리랭킹 → top-{TOPK})")
    print("-" * 52)
    base = json.loads(args.baseline.read_text(encoding="utf-8")) if args.baseline.exists() else {}
    print(f"{'지표':<12}{'베이스라인':>12}{'리랭킹':>10}{'Δ':>10}")
    for key in ["recall@1", "recall@5", "recall@10", "mrr@10"]:
        b = base.get(key)
        r = rer[key]
        delta = f"{(r - b):+.3f}" if isinstance(b, (int, float)) else "-"
        bstr = f"{b:.3f}" if isinstance(b, (int, float)) else "-"
        print(f"{key:<12}{bstr:>12}{r:>10.3f}{delta:>10}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(rer, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장 → {args.output}")


if __name__ == "__main__":
    main()
