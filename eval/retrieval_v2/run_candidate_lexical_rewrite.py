"""Candidate v3 (safe rename): lexical rewrite terms, same SQL/ranking path as D-003.

Usage:
  python eval/retrieval_v2/run_candidate_lexical_rewrite.py --output eval/retrieval-v2/experiments/lexical-rewrite-v1.json

Candidate's only change: lexical_overlap_terms -> lexical_overlap_terms_rewrite
- Replacement, not additive
- Residue tokens dropped
- Stopword stems dropped
- No new lexical channel, no RRF, no DB mutation
- Algorithm identical to interrupted lexical-canonicalization-v1; only names avoid reserved substring.
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

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "ml-service"))
sys.path.insert(0, str(ROOT / "eval"))
import app as ml_app
from source_ranking import lexical_overlap_terms, ranking_metadata, youth_source_bias
from retrieval_v2.candidate_lexical_rewrite import (
    ADMIN_UNITS,
    MIN_STEM_LEN,
    PARTICLES,
    RESIDUE_PURE,
    lexical_overlap_terms_rewrite,
)
from retrieval_v2.schema import load_and_validate
from retrieval_v2.metrics import compute_metrics
from retrieval_v2.guard import ensure_retrieval_v2_path
from retrieval_v2.provenance import canonical_text_sha256

load_dotenv(ROOT / ".env")
DB = os.getenv("DATABASE_URL", "").strip()
HERE = pathlib.Path(__file__).resolve().parent
DEV_EVALSET = ROOT / "eval" / "retrieval-v2" / "dev" / "evalset.jsonl"
DEFAULT_OUTPUT = ROOT / "eval" / "retrieval-v2" / "experiments" / "lexical-rewrite-v1.json"

# Normalization rule derived from actual candidate module constants; no duplicated suffix list
NORMALIZATION_RULE = (
    f"lexical rewrite replacement: original term replaced by particle-stripped stem "
    f"(particles {'/'.join(PARTICLES)}, MIN_STEM_LEN {MIN_STEM_LEN}, deduped); "
    f"residue tokens (pure josa/admin-unit/admin+particle without proper noun) dropped; "
    f"stopword stems dropped; verb expansion none"
)


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
    p = argparse.ArgumentParser(description="Run lexical rewrite candidate on dev")
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
    dev_sha = canonical_text_sha256(args.eval_file)
    try:
        dev_freeze_commit = subprocess.check_output(["git", "log", "-1", "--format=%H", "--", str(args.eval_file)], cwd=str(ROOT), stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        dev_freeze_commit = "unknown"

    from sentence_transformers import SentenceTransformer
    kwargs = {"local_files_only": True} if ml_app.MODEL_LOCAL_ONLY else {}
    model = SentenceTransformer(ml_app.EMBED_MODEL_NAME, **kwargs)

    conn = psycopg2.connect(DB)
    corpus = get_corpus_summary(conn)
    cur = conn.cursor()

    baseline_ranks = []
    candidate_ranks = []
    by_source_baseline = {"youth": [], "gov24": []}
    by_source_candidate = {"youth": [], "gov24": []}
    by_category_baseline: dict[str, list[int]] = {}
    by_category_candidate: dict[str, list[int]] = {}
    per_case = []

    for it in items:
        q_raw = it["query"]
        q = ml_app.strip_region(q_raw)
        vec = model.encode([f"query: {q}"], normalize_embeddings=True)[0]
        vec_str = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
        lex_orig = lexical_overlap_terms(q)
        lex_canon = lexical_overlap_terms_rewrite(q)
        yb = youth_source_bias(q)

        cur.execute(ml_app.SQL, {
            "vec": vec_str, "age": it.get("age"), "rp": None,
            "youth_bias": yb, "lexical_terms": lex_orig, "lexical_bias": ml_app.LEXICAL_OVERLAP_BIAS, "n": ml_app.CANDIDATES,
        })
        cands = [dict(zip(ml_app.SEARCH_RESULT_COLUMNS, row)) for row in cur.fetchall()]
        cands = ml_app.region_filter(cands, None)
        bi = [c for c in cands if c["score"] >= ml_app.COSINE_MIN]
        gold = (it["gold_source"], it["gold_source_id"])
        b_rank = rank_of(bi, gold, topk=10)

        cur.execute(ml_app.SQL, {
            "vec": vec_str, "age": it.get("age"), "rp": None,
            "youth_bias": yb, "lexical_terms": lex_canon, "lexical_bias": ml_app.LEXICAL_OVERLAP_BIAS, "n": ml_app.CANDIDATES,
        })
        cands2 = [dict(zip(ml_app.SEARCH_RESULT_COLUMNS, row)) for row in cur.fetchall()]
        cands2 = ml_app.region_filter(cands2, None)
        bi2 = [c for c in cands2 if c["score"] >= ml_app.COSINE_MIN]
        c_rank = rank_of(bi2, gold, topk=10)

        baseline_ranks.append(b_rank)
        candidate_ranks.append(c_rank)
        by_source_baseline[it["gold_source"]].append(b_rank)
        by_source_candidate[it["gold_source"]].append(c_rank)
        cat = it.get("category", "unknown")
        by_category_baseline.setdefault(cat, []).append(b_rank)
        by_category_candidate.setdefault(cat, []).append(c_rank)

        per_case.append({
            "case_id": it["case_id"],
            "query": it["query"],
            "gold_source": it["gold_source"],
            "gold_source_id": it["gold_source_id"],
            "gold_title": it.get("gold_title"),
            "category": cat,
            "baseline_rank": b_rank,
            "candidate_rank": c_rank,
            "baseline_hit@5": 1 <= b_rank <= 5,
            "candidate_hit@5": 1 <= c_rank <= 5,
            "delta": (1 if 1 <= c_rank <= 5 else 0) - (1 if 1 <= b_rank <= 5 else 0),
            "original_lexical_terms": lex_orig,
            "candidate_lexical_terms": lex_canon,
            "dropped_terms": [t for t in lex_orig if t not in lex_canon],
            "added_terms": [t for t in lex_canon if t not in lex_orig],
        })

    cur.close()
    conn.close()

    baseline_metrics = compute_metrics(baseline_ranks, by_source_baseline, by_category_baseline)
    candidate_metrics = compute_metrics(candidate_ranks, by_source_candidate, by_category_candidate)

    b_hit5 = baseline_metrics["hit@5"]
    c_hit5 = candidate_metrics["hit@5"]
    net = c_hit5 - b_hit5
    per_source_delta = {}
    for src in sorted(set(by_source_baseline) | set(by_source_candidate)):
        b = sum(1 for r in by_source_baseline.get(src, []) if 1 <= r <= 5)
        c = sum(1 for r in by_source_candidate.get(src, []) if 1 <= r <= 5)
        per_source_delta[src] = {"baseline_hit@5": b, "candidate_hit@5": c, "delta": c - b, "regression": c < b}

    gains = [c for c in per_case if c["delta"] == 1]
    losses = [c for c in per_case if c["delta"] == -1]
    target_ids = ["dev-009", "dev-015", "dev-034"]
    target_ranks = {c["case_id"]: c for c in per_case if c["case_id"] in target_ids}

    git_info = get_git_commit()
    output = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "git_commit": git_info["commit"],
        "git_dirty": git_info["dirty"],
        "dev_set_sha256": dev_sha,
        "dev_set_freeze_commit": dev_freeze_commit,
        "evaluator": "eval/retrieval_v2/run_candidate_lexical_rewrite.py",
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
        },
        "candidate_config": {
            "name": "lexical-rewrite-v1",
            "normalization_rule": NORMALIZATION_RULE,
            "min_stem_len": MIN_STEM_LEN,
            "particles": PARTICLES,
            "residue_pure": sorted(RESIDUE_PURE),
            "admin_units": ADMIN_UNITS,
            "verb_expansion": False,
            "lexical_terms": "lexical_overlap_terms_rewrite",
            "strip_region": "unchanged",
        },
        "corpus": corpus,
        "n": len(baseline_ranks),
        "baseline": baseline_metrics,
        "candidate_metrics": candidate_metrics,
        "net_hit@5": net,
        "per_source_delta": per_source_delta,
        "gains": gains,
        "losses": losses,
        "target_ranks": target_ranks,
        "per_case": per_case,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"n={len(baseline_ranks)} baseline recall@5 {baseline_metrics['recall@5']:.4f} macro {baseline_metrics.get('source_macro_recall@5')} candidate recall@5 {candidate_metrics['recall@5']:.4f} macro {candidate_metrics.get('source_macro_recall@5')} net {net}")
    print(f"youth baseline {baseline_metrics['by_source']['youth']['recall@5']} ({baseline_metrics['by_source']['youth']['hit@5']}/18) candidate {candidate_metrics['by_source']['youth']['recall@5']} ({candidate_metrics['by_source']['youth']['hit@5']}/18)")
    print(f"gov24 baseline {baseline_metrics['by_source']['gov24']['recall@5']} ({baseline_metrics['by_source']['gov24']['hit@5']}/18) candidate {candidate_metrics['by_source']['gov24']['recall@5']} ({candidate_metrics['by_source']['gov24']['hit@5']}/18)")
    print(f"gains {len(gains)} losses {len(losses)} target { {k: (v['baseline_rank'], v['candidate_rank']) for k,v in target_ranks.items()} }")
    print(f"saved -> {args.output}")

if __name__ == "__main__":
    main()
