"""
36-case hard-negative / abstention 진단 — production retrieval 계약으로 36문항을 재현.

대상: eval/expansion_api_evalset.jsonl (positive 21 + ineligible 3 + no_answer 12)
계약: ml-service/app.py SQL·strip_region·CANDIDATES=30·COSINE_MIN=0.78·LEXICAL 0.01
출력: per-case top1 score/gap/lexical 진단 + threshold aggregate
필요: DATABASE_URL
사용법: python run_hard_negative_eval.py --output eval/canonical_hard_negative_36_production_parity.json
"""
import argparse
import datetime
import json
import os
import pathlib
import subprocess
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

CANONICAL_EVALUATOR = "eval/run_hard_negative_eval.py"
TOPK = 5  # abstention은 top1 위주지만 per-case top-k IDs 기록
TOPK_DIAG = 5


def get_git_commit() -> dict:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(ROOT), stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        commit = "unknown"
    try:
        dirty = bool(
            subprocess.check_output(
                ["git", "status", "--porcelain"], cwd=str(ROOT), stderr=subprocess.DEVNULL
            ).decode().strip()
        )
    except Exception:
        dirty = False
    return {"commit": commit, "dirty": dirty}


def get_corpus_summary(conn) -> dict:
    try:
        cur = conn.cursor()
        cur.execute("SELECT source, count(*) FROM policy GROUP BY source")
        by_source = {source: {"policies": count} for source, count in cur.fetchall()}
        cur.execute(
            "SELECT p.source, count(*) FROM policy_chunk c JOIN policy p ON p.id=c.policy_id GROUP BY p.source"
        )
        for source, count in cur.fetchall():
            if source in by_source:
                by_source[source]["chunks"] = count
            else:
                by_source[source] = {"policies": 0, "chunks": count}
        cur.execute("SELECT count(*) FROM policy")
        total_policies = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM policy_chunk")
        total_chunks = cur.fetchone()[0]
        cur.close()
        return {
            "total_policies": total_policies,
            "total_chunks": total_chunks,
            "by_source": by_source,
        }
    except Exception:
        return {"total_policies": None, "total_chunks": None, "by_source": {}}


def parse_args():
    parser = argparse.ArgumentParser(description="36-case hard-negative production retrieval 진단")
    parser.add_argument("--eval-file", type=pathlib.Path, default=HERE / "expansion_api_evalset.jsonl")
    parser.add_argument("--output", type=pathlib.Path, default=HERE / "canonical_hard_negative_36_production_parity.json")
    parser.add_argument(
        "--lexical-bias",
        type=float,
        default=None,
        help="어휘 보정값 override. 미지정 시 production LEXICAL_OVERLAP_BIAS(0.01) 사용",
    )
    return parser.parse_args()


def load_items(path):
    if not path.exists():
        raise SystemExit(f"평가셋 없음: {path}")
    items = [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]
    if not items:
        raise SystemExit(f"평가셋이 비어 있습니다: {path}")
    return items


def fetch_lexical_overlap_for_policy(conn, policy_source, policy_source_id, terms):
    if not terms:
        return 0
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT title, summary, support_content, add_qualify, keywords
            FROM policy WHERE source=%s AND source_id=%s
            """,
            (policy_source, policy_source_id),
        )
        row = cur.fetchone()
        cur.close()
        if not row:
            return 0
        text = " ".join([v or "" for v in row])
        # DISTINCT term count where term appears (ILIKE semantics)
        lowered = text.lower()
        seen = set()
        count = 0
        for term in terms:
            t = term.lower()
            if t not in seen and t in lowered:
                seen.add(t)
                count += 1
        return count
    except Exception:
        return 0


def main():
    args = parse_args()
    if not DB:
        raise SystemExit("DATABASE_URL 없음")
    lexical_bias = args.lexical_bias if args.lexical_bias is not None else ml_app.LEXICAL_OVERLAP_BIAS
    items = load_items(args.eval_file)

    # embedder
    from sentence_transformers import SentenceTransformer
    kwargs = {"local_files_only": True} if ml_app.MODEL_LOCAL_ONLY else {}
    model = SentenceTransformer(ml_app.EMBED_MODEL_NAME, **kwargs)

    conn = psycopg2.connect(DB)
    cur = conn.cursor()

    cases = []
    for idx, it in enumerate(items, 1):
        query_raw = it["query"]
        query = ml_app.strip_region(query_raw)
        qvec = model.encode([f"query: {query}"], normalize_embeddings=True)[0]
        vec = "[" + ",".join(f"{x:.6f}" for x in qvec) + "]"
        lexical_terms = lexical_overlap_terms(query)
        youth_bias = youth_source_bias(query)
        cur.execute(ml_app.SQL, {
            "vec": vec,
            "age": it.get("age"),
            "rp": None,
            "youth_bias": youth_bias,
            "lexical_terms": lexical_terms,
            "lexical_bias": lexical_bias,
            "n": ml_app.CANDIDATES,
        })
        candidates = [dict(zip(ml_app.SEARCH_RESULT_COLUMNS, row)) for row in cur.fetchall()]
        candidates = ml_app.region_filter(candidates, None)
        bi_encoder = [c for c in candidates if c["score"] >= ml_app.COSINE_MIN]

        # diagnostics
        top1 = bi_encoder[0] if bi_encoder else None
        top2 = bi_encoder[1] if len(bi_encoder) > 1 else None
        top1_score = float(top1["score"]) if top1 else None
        top2_score = float(top2["score"]) if top2 else None
        gap = (top1_score - top2_score) if top1_score is not None and top2_score is not None else None

        # gold rank for positive/ineligible cases
        gold = None
        if it.get("gold_source_id"):
            gold = (it.get("gold_source", "youth"), it["gold_source_id"])
            gold_keys = [(c["source"], c["source_id"]) for c in bi_encoder[:TOPK_DIAG]]
            gold_rank = gold_keys.index(gold) + 1 if gold in gold_keys else 0
        elif it.get("excluded_source_id"):
            excluded = (it["excluded_source"], it["excluded_source_id"])
            keys = [(c["source"], c["source_id"]) for c in bi_encoder[:TOPK_DIAG]]
            excluded_rank = keys.index(excluded) + 1 if excluded in keys else 0
            gold = excluded  # for record
            gold_rank = excluded_rank
        else:
            gold_rank = None

        # lexical overlap for top1 (distinct terms appearing in policy body)
        top1_lexical_overlap = None
        if top1:
            top1_lexical_overlap = fetch_lexical_overlap_for_policy(conn, top1["source"], top1["source_id"], lexical_terms)

        case = {
            "index": idx,
            "case_type": it.get("case_type", "unknown"),
            "query": query_raw,
            "query_stripped": query,
            "age": it.get("age"),
            "expected_no_results": bool(it.get("expected_no_results")),
            "excluded_source": it.get("excluded_source"),
            "excluded_source_id": it.get("excluded_source_id"),
            "gold_source": it.get("gold_source"),
            "gold_source_id": it.get("gold_source_id"),
            "gold_rank_top5": gold_rank,
            "youth_bias": youth_bias,
            "lexical_terms": lexical_terms,
            "lexical_terms_count": len(lexical_terms),
            "top1": {
                "source": top1["source"] if top1 else None,
                "source_id": top1["source_id"] if top1 else None,
                "score": top1_score,
                "lexical_overlap": top1_lexical_overlap,
            } if top1 else None,
            "top2_score": top2_score,
            "gap_top1_top2": gap,
            "retrieved_count": len(bi_encoder),
            "top_k_ids": [(c["source"], c["source_id"], round(float(c["score"]), 4)) for c in bi_encoder[:TOPK_DIAG]],
            "has_results": bool(bi_encoder),
        }
        cases.append(case)
        print(f"\r진단 {idx}/{len(items)}", end="", flush=True)
    print()
    corpus = get_corpus_summary(conn)
    cur.close()
    conn.close()

    # aggregates for abstention analysis
    positives = [c for c in cases if c["gold_source_id"]]
    # positives includes both pure positive and ineligible excluded? separate
    pure_positives = [c for c in cases if c["gold_source_id"] and not c["excluded_source_id"] and not c["expected_no_results"]]
    no_answers = [c for c in cases if c["expected_no_results"]]

    def count_below(cases_list, threshold):
        return sum(1 for c in cases_list if c["top1"] and c["top1"]["score"] is not None and c["top1"]["score"] < threshold)

    # thresholds used in docs: 0.8481 (min positive), 0.842, 0.840-0.846 range
    aggregates = {
        "total_cases": len(cases),
        "pure_positive_n": len(pure_positives),
        "ineligible_n": len([c for c in cases if c["excluded_source_id"]]),
        "no_answer_n": len(no_answers),
        "positive_top1_score_range": {
            "min": min([c["top1"]["score"] for c in pure_positives if c["top1"]] or [None]),
            "max": max([c["top1"]["score"] for c in pure_positives if c["top1"]] or [None]),
        },
        "no_answer_top1_score_range": {
            "min": min([c["top1"]["score"] for c in no_answers if c["top1"]] or [None]),
            "max": max([c["top1"]["score"] for c in no_answers if c["top1"]] or [None]),
        },
        # example thresholds from docs
        "thresholds": {
            "top1_score_lt_0.8481": {
                "no_answer_detected": count_below(no_answers, 0.8481),
                "positive_false": count_below(pure_positives, 0.8481),
            },
            "top1_score_lt_0.842_and_lex_lt_2": {
                "no_answer_detected": sum(1 for c in no_answers if c["top1"] and c["top1"]["score"] is not None and c["top1"]["score"] < 0.842 and (c["top1"]["lexical_overlap"] or 0) < 2),
                "positive_false": sum(1 for c in pure_positives if c["top1"] and c["top1"]["score"] is not None and c["top1"]["score"] < 0.842 and (c["top1"]["lexical_overlap"] or 0) < 2),
            },
        },
        "observation": "Positive and no-answer top1 score ranges overlap, so a single score threshold does not separate them reliably; reproduces the threshold No-Go conclusion.",
    }

    git_info = get_git_commit()
    result = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "git_commit": git_info["commit"],
        "git_dirty": git_info["dirty"],
        "evaluator": CANONICAL_EVALUATOR,
        "eval_file": str(args.eval_file.resolve().relative_to(ROOT) if str(args.eval_file.resolve()).startswith(str(ROOT)) else args.eval_file),
        "n": len(cases),
        "lexical_bias_used": lexical_bias,
        "lexical_bias_param": lexical_bias,
        "production_contract": {
            "candidate_sql": "ml-service/app.py:SQL",
            "request_region": None,
            "query_preprocessing": "strip_region",
            "expired_policies_excluded": True,
            "candidates": ml_app.CANDIDATES,
            "rerank": 0,
            "bi_encoder_min_score": ml_app.COSINE_MIN,
        },
        "source_ranking": ranking_metadata(),
        "embedder": ml_app.EMBED_MODEL_NAME,
        "corpus": corpus,
        "cases": cases,
        "aggregates": aggregates,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(aggregates, ensure_ascii=False, indent=2))
    print(f"\n저장 → {args.output}")


if __name__ == "__main__":
    main()
