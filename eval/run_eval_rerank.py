"""
Production `/search`와 같은 후보 SQL·질의 전처리·score cut으로 bi-encoder와
cross-encoder를 함께 평가한다.

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

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ml-service"))
import app as ml_app
from source_ranking import lexical_overlap_terms, ranking_metadata, youth_source_bias

load_dotenv(ROOT / ".env")
DB = os.getenv("DATABASE_URL", "").strip()
HERE = pathlib.Path(__file__).resolve().parent

KS = [1, 5, 10]
TOPK = 10


def metrics(ranks):
    n = len(ranks)
    out = {}
    for k in KS:
        out[f"recall@{k}"] = round(sum(1 for rank in ranks if 1 <= rank <= k) / n, 4)
    out["mrr@10"] = round(sum((1 / rank if rank else 0) for rank in ranks) / n, 4)
    return out


def parse_args():
    parser = argparse.ArgumentParser(
        description="production 검색 계약으로 bi-encoder와 cross-encoder를 평가합니다"
    )
    parser.add_argument("--eval-file", type=pathlib.Path, default=HERE / "evalset.jsonl")
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=HERE / "results_after_source_bias_rerank.json",
    )
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


def rank_of(candidates, gold):
    keys = [(candidate["source"], candidate["source_id"]) for candidate in candidates[:TOPK]]
    return keys.index(gold) + 1 if gold in keys else 0


def evaluate_items(items, embedder, reranker, cursor):
    ranked = []
    for index, item in enumerate(items, 1):
        gold = (item.get("gold_source", "youth"), item["gold_source_id"])
        query = ml_app.strip_region(item["query"])
        query_vector = embedder.encode(
            [f"query: {query}"], normalize_embeddings=True)[0]
        vector = "[" + ",".join(f"{value:.6f}" for value in query_vector) + "]"
        cursor.execute(ml_app.SQL, {
            "vec": vector,
            "age": item.get("age"),
            "rp": None,
            "youth_bias": youth_source_bias(query),
            "lexical_terms": lexical_overlap_terms(query),
            "lexical_bias": ml_app.LEXICAL_OVERLAP_BIAS,
            "n": ml_app.CANDIDATES,
        })
        candidates = [
            dict(zip(ml_app.SEARCH_RESULT_COLUMNS, row))
            for row in cursor.fetchall()
        ]
        candidates = ml_app.region_filter(candidates, None)

        bi_encoder = [
            candidate for candidate in candidates
            if candidate["score"] >= ml_app.COSINE_MIN
        ]
        reranked = ml_app.rerank_candidates(
            query,
            [candidate.copy() for candidate in candidates],
            reranker,
            ml_app.DEFAULT_RERANK_MIN_SCORE,
        ) if candidates else []
        ranked.append({
            "source": gold[0],
            "bi_encoder": rank_of(bi_encoder, gold),
            "rerank": rank_of(reranked, gold),
        })
        print(f"\r리랭킹 {index}/{len(items)}", end="", flush=True)
    if items:
        print()
    return ranked


def metric_block(ranked, rank_key):
    block = metrics([item[rank_key] for item in ranked])
    block["by_source"] = {}
    for source in sorted({item["source"] for item in ranked}):
        source_ranks = [
            item[rank_key] for item in ranked if item["source"] == source
        ]
        block["by_source"][source] = {"n": len(source_ranks), **metrics(source_ranks)}
    return block


def main():
    args = parse_args()
    if not DB:
        raise SystemExit("DATABASE_URL 없음")
    items = load_items(args.eval_file)
    from sentence_transformers import CrossEncoder, SentenceTransformer
    kwargs = {"local_files_only": True} if ml_app.MODEL_LOCAL_ONLY else {}
    embedder = SentenceTransformer(ml_app.EMBED_MODEL_NAME, **kwargs)
    print(f"리랭커 로드: {ml_app.RERANK_MODEL_NAME}")
    reranker = CrossEncoder(ml_app.RERANK_MODEL_NAME, **kwargs)

    conn = psycopg2.connect(DB)
    cur = conn.cursor()
    try:
        ranked = evaluate_items(items, embedder, reranker, cur)
    finally:
        cur.close()
        conn.close()

    eval_file = args.eval_file.resolve()
    try:
        eval_file = eval_file.relative_to(ROOT)
    except ValueError:
        pass

    results = {
        "n": len(ranked),
        "eval_file": str(eval_file),
        "embedder": ml_app.EMBED_MODEL_NAME,
        "reranker": ml_app.RERANK_MODEL_NAME,
        "candidates": ml_app.CANDIDATES,
        "top_k": TOPK,
        "source_ranking": ranking_metadata(),
        "production_contract": {
            "candidate_sql": "ml-service/app.py:SQL",
            "request_region": None,
            "query_preprocessing": "strip_region",
            "expired_policies_excluded": True,
            "bi_encoder_min_score": ml_app.COSINE_MIN,
            "rerank_text": "title + support_content",
            "rerank_text_limit": ml_app.RERANK_TEXT_LIMIT,
            "rerank_min_score": ml_app.DEFAULT_RERANK_MIN_SCORE,
        },
        "bi_encoder": metric_block(ranked, "bi_encoder"),
        "rerank": metric_block(ranked, "rerank"),
    }

    print(f"\n평가 문항: {len(ranked)}  (production 후보 {ml_app.CANDIDATES} → top-{TOPK})")
    print("-" * 54)
    print(f"{'지표':<12}{'bi-encoder':>14}{'리랭킹':>10}{'Δ':>10}")
    for key in ["recall@1", "recall@5", "recall@10", "mrr@10"]:
        baseline = results["bi_encoder"][key]
        reranked = results["rerank"][key]
        print(f"{key:<12}{baseline:>14.3f}{reranked:>10.3f}{reranked - baseline:>+10.3f}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n저장 → {args.output}")


if __name__ == "__main__":
    main()
