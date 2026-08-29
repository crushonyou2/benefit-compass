"""Dev baseline runner — current D-003 production retrieval on frozen dev set.

Usage:
  python eval/retrieval_v2/run_dev_baseline.py --output eval/retrieval-v2/dev/baseline.json

This runner is D-003 parity: same SQL, strip_region, youth_source_bias,
lexical_overlap_terms, LEXICAL 0.01, CANDIDATES 30, COSINE_MIN 0.78,
region_filter(None), top-10 source-aware rank.

It does NOT implement any Retrieval v2 candidate algorithm.
"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import subprocess
import sys

from dotenv import load_dotenv
import psycopg2

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "ml-service"))
sys.path.insert(0, str(ROOT / "eval"))
import app as ml_app
from source_ranking import lexical_overlap_terms, ranking_metadata, youth_source_bias
from retrieval_v2.schema import load_and_validate
from retrieval_v2.metrics import compute_metrics
from retrieval_v2.guard import ensure_retrieval_v2_path

load_dotenv(ROOT / ".env")
DB = os.getenv("DATABASE_URL", "").strip()
HERE = pathlib.Path(__file__).resolve().parent
DEV_EVALSET = ROOT / "eval" / "retrieval-v2" / "dev" / "evalset.jsonl"
DEFAULT_OUTPUT = ROOT / "eval" / "retrieval-v2" / "dev" / "baseline.json"


def get_git_commit() -> dict:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(ROOT), stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        commit = "unknown"
    try:
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=str(ROOT), stderr=subprocess.DEVNULL).decode().strip())
    except Exception:
        dirty = False
    return {"commit": commit, "dirty": dirty}


def get_corpus_summary(conn) -> dict:
    try:
        cur = conn.cursor()
        cur.execute("SELECT source, count(*) FROM policy GROUP BY source")
        by_source = {s: {"policies": c} for s, c in cur.fetchall()}
        cur.execute("SELECT p.source, count(*) FROM policy_chunk c JOIN policy p ON p.id=c.policy_id GROUP BY p.source")
        for s, c in cur.fetchall():
            if s in by_source:
                by_source[s]["chunks"] = c
            else:
                by_source[s] = {"policies": 0, "chunks": c}
        cur.execute("SELECT count(*) FROM policy")
        total_policies = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM policy_chunk")
        total_chunks = cur.fetchone()[0]
        cur.close()
        return {"total_policies": total_policies, "total_chunks": total_chunks, "by_source": by_source}
    except Exception:
        return {"total_policies": None, "total_chunks": None, "by_source": {}}


def parse_args():
    p = argparse.ArgumentParser(description="Run D-003 baseline on dev set")
    p.add_argument("--eval-file", type=pathlib.Path, default=DEV_EVALSET)
    p.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUTPUT)
    return p.parse_args()


def rank_of(candidates, gold, topk=10):
    keys = [(c["source"], c["source_id"]) for c in candidates[:topk]]
    return keys.index(gold) + 1 if gold in keys else 0


def main():
    args = parse_args()
    if not DB:
        raise SystemExit("DATABASE_URL 없음")
    ensure_retrieval_v2_path(args.output)
    items = load_and_validate(args.eval_file, "dev")
    dev_sha = hashlib.sha256(args.eval_file.read_bytes()).hexdigest()
    try:
        dev_freeze_commit = subprocess.check_output(["git", "log", "--oneline", "--all", "--", str(args.eval_file)], cwd=str(ROOT), stderr=subprocess.DEVNULL).decode().splitlines()[0].split()[0]
    except Exception:
        dev_freeze_commit = "unknown"
    manifest_path = args.eval_file.parent / "manifest.json"
    if manifest_path.exists():
        try:
            m = json.loads(manifest_path.read_text(encoding="utf-8"))
            dev_freeze_commit = m.get("base_commit", dev_freeze_commit)
        except Exception:
            pass

    from sentence_transformers import SentenceTransformer
    kwargs = {"local_files_only": True} if ml_app.MODEL_LOCAL_ONLY else {}
    model = SentenceTransformer(ml_app.EMBED_MODEL_NAME, **kwargs)

    conn = psycopg2.connect(DB)
    corpus = get_corpus_summary(conn)
    cur = conn.cursor()

    ranks = []
    by_source_ranks = {"youth": [], "gov24": []}
    by_category_ranks: dict[str, list[int]] = {}
    per_case = []

    for it in items:
        q_raw = it["query"]
        q = ml_app.strip_region(q_raw)
        vec = model.encode([f"query: {q}"], normalize_embeddings=True)[0]
        vec_str = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
        cur.execute(ml_app.SQL, {
            "vec": vec_str,
            "age": it.get("age"),
            "rp": None,
            "youth_bias": youth_source_bias(q),
            "lexical_terms": lexical_overlap_terms(q),
            "lexical_bias": ml_app.LEXICAL_OVERLAP_BIAS,
            "n": ml_app.CANDIDATES,
        })
        cands = [dict(zip(ml_app.SEARCH_RESULT_COLUMNS, row)) for row in cur.fetchall()]
        cands = ml_app.region_filter(cands, None)
        bi = [c for c in cands if c["score"] >= ml_app.COSINE_MIN]
        gold = (it["gold_source"], it["gold_source_id"])
        rank = rank_of(bi, gold, topk=10)
        ranks.append(rank)
        by_source_ranks[it["gold_source"]].append(rank)
        cat = it.get("category", "unknown")
        by_category_ranks.setdefault(cat, []).append(rank)
        per_case.append({
            "case_id": it["case_id"],
            "query": it["query"],
            "gold_source": it["gold_source"],
            "gold_source_id": it["gold_source_id"],
            "gold_title": it.get("gold_title"),
            "category": cat,
            "rank": rank,
            "hit@1": 1 <= rank <= 1,
            "hit@5": 1 <= rank <= 5,
            "hit@10": 1 <= rank <= 10,
        })

    cur.close()
    conn.close()

    metrics = compute_metrics(ranks, by_source_ranks, by_category_ranks)
    git_info = get_git_commit()

    from retrieval_v2.metrics import macro_recall_at_5
    assert abs(metrics.get("source_macro_recall@5", 0) - macro_recall_at_5(by_source_ranks)) < 1e-6

    output = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "git_commit": git_info["commit"],
        "git_dirty": git_info["dirty"],
        "dev_set_sha256": dev_sha,
        "dev_set_freeze_commit": dev_freeze_commit,
        "evaluator": "eval/retrieval_v2/run_dev_baseline.py",
        "model": ml_app.EMBED_MODEL_NAME,
        "production_contract": {
            "candidate_sql": "ml-service/app.py:SQL",
            "request_region": None,
            "query_preprocessing": "strip_region",
            "expired_policies_excluded": True,
            "candidates": ml_app.CANDIDATES,
            "rerank": 0,
            "bi_encoder_min_score": ml_app.COSINE_MIN,
            "lexical_bias": ml_app.LEXICAL_OVERLAP_BIAS,
            "youth_bias": "source_ranking.youth_source_bias",
        },
        "source_ranking": ranking_metadata(),
        "corpus": corpus,
        "n": len(ranks),
        "youth_n": len(by_source_ranks["youth"]),
        "gov24_n": len(by_source_ranks["gov24"]),
        "recall@1": metrics["recall@1"],
        "recall@5": metrics["recall@5"],
        "recall@10": metrics["recall@10"],
        "mrr@10": metrics["mrr@10"],
        "source_macro_recall@5": metrics.get("source_macro_recall@5"),
        "by_source": metrics.get("by_source"),
        "by_category": metrics.get("by_category"),
        "per_case": per_case,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"n={len(ranks)} recall@1 {output['recall@1']:.4f} recall@5 {output['recall@5']:.4f} recall@10 {output['recall@10']:.4f} mrr {output['mrr@10']:.4f} macro@5 {output['source_macro_recall@5']}")
    print(f"by_source youth {output['by_source']['youth']['recall@5']} ({output['by_source']['youth']['hit@5']}/{output['by_source']['youth']['n']}) gov24 {output['by_source']['gov24']['recall@5']} ({output['by_source']['gov24']['hit@5']}/{output['by_source']['gov24']['n']})")
    print(f"saved -> {args.output}")

if __name__ == "__main__":
    main()
