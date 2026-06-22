"""
리랭킹 적용 평가 — bi-encoder로 top-N 후보를 뽑고, cross-encoder 리랭커로 재정렬해 재측정.
run_eval.py(베이스라인)와 같은 평가셋·지표를 쓰고, results.json 이 있으면 개선폭을 함께 출력.

리랭커: BAAI/bge-reranker-v2-m3 (다국어, 로컬·무료). 첫 실행 시 모델 다운로드.
필요: DATABASE_URL
사용법: python run_eval_rerank.py
"""
import os
import json
import pathlib

from dotenv import load_dotenv
import psycopg2
from sentence_transformers import SentenceTransformer, CrossEncoder

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
DB = os.getenv("DATABASE_URL", "").strip()
HERE = pathlib.Path(__file__).resolve().parent
EVALFILE = HERE / "evalset.jsonl"
BASEFILE = HERE / "results.json"
OUTFILE = HERE / "results_rerank.json"

KS = [1, 5, 10]
CANDIDATES = 30   # bi-encoder가 뽑는 후보 수 (리랭킹 대상)
TOPK = 10

CAND_SQL = """
SELECT t.source_id, t.content FROM (
  SELECT DISTINCT ON (p.id) p.source_id, c.content,
         (c.embedding <=> %(vec)s::vector) AS dist
  FROM policy_chunk c JOIN policy p ON p.id = c.policy_id
  ORDER BY p.id, c.embedding <=> %(vec)s::vector
) t
ORDER BY t.dist
LIMIT %(n)s
"""


def metrics(ranks, n):
    out = {}
    for k in KS:
        out[f"recall@{k}"] = round(sum(1 for r in ranks if 1 <= r <= k) / n, 4)
    out["mrr@10"] = round(sum((1 / r if r else 0) for r in ranks) / n, 4)
    return out


def main():
    if not DB:
        raise SystemExit("DATABASE_URL 없음")
    items = [json.loads(l) for l in EVALFILE.open(encoding="utf-8")]

    embedder = SentenceTransformer("intfloat/multilingual-e5-base")
    print("리랭커 로드: BAAI/bge-reranker-v2-m3 (첫 실행 시 다운로드)")
    reranker = CrossEncoder("BAAI/bge-reranker-v2-m3")

    conn = psycopg2.connect(DB)
    cur = conn.cursor()
    ranks = []
    for it in items:
        qvec = embedder.encode([f"query: {it['query']}"], normalize_embeddings=True)[0]
        vec = "[" + ",".join(f"{x:.6f}" for x in qvec) + "]"
        cur.execute(CAND_SQL, {"vec": vec, "n": CANDIDATES})
        cand = cur.fetchall()  # [(source_id, content), ...]
        if not cand:
            ranks.append(0)
            continue
        scores = reranker.predict([(it["query"], content) for _, content in cand],
                                  show_progress_bar=True)
        ordered = [sid for sid, _ in sorted(zip([c[0] for c in cand], scores),
                                            key=lambda x: x[1], reverse=True)]
        gold = it["gold_source_id"]
        ranks.append(ordered.index(gold) + 1 if gold in ordered[:TOPK] else 0)
    cur.close()
    conn.close()

    n = len(ranks)
    rer = metrics(ranks, n)
    rer.update({"n": n, "candidates": CANDIDATES, "reranker": "bge-reranker-v2-m3"})

    print(f"\n평가 문항: {n}  (후보 {CANDIDATES} → 리랭킹 → top-{TOPK})")
    print("-" * 52)
    base = json.loads(BASEFILE.read_text(encoding="utf-8")) if BASEFILE.exists() else {}
    print(f"{'지표':<12}{'베이스라인':>12}{'리랭킹':>10}{'Δ':>10}")
    for key in ["recall@1", "recall@5", "recall@10", "mrr@10"]:
        b = base.get(key)
        r = rer[key]
        delta = f"{(r - b):+.3f}" if isinstance(b, (int, float)) else "-"
        bstr = f"{b:.3f}" if isinstance(b, (int, float)) else "-"
        print(f"{key:<12}{bstr:>12}{r:>10.3f}{delta:>10}")

    OUTFILE.write_text(json.dumps(rer, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장 → {OUTFILE}")


if __name__ == "__main__":
    main()
