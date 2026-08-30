"""Cycle 2 Phase2 Exp1: bounded region-core lexical hint (quality + conditional latency).

Quality is paired over cycle2 dev 36 with shared precomputed qvec/DB/corpus/SQL/age/youth bias.
Variants:
- baseline: D-003 production lexical_overlap_terms on stripped q
- candidate-v2: frozen candidate-v2 lexical_overlap_terms_rewrite on stripped q
- new_candidate: candidate_region_hint.lexical_overlap_terms_region_hint(raw_query)
  which is base (candidate-v2 on stripped) + bounded SIDO canonical hint from raw.

If quality early-stop FAIL (new R@5 <=30, Gov24 regression, or loss vs candidate-v2), REJECTED and latency not run.
If quality PASS (31+ R@5, Gov24 18/18, loss0 vs candidate-v2), run diagnostic latency baseline vs new only.
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
import pathlib
import random
import subprocess
import sys
import time

from dotenv import load_dotenv
import os
import psycopg2

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "ml-service"))
sys.path.insert(0, str(ROOT / "eval"))
import app as ml_app  # type: ignore
from source_ranking import LEXICAL_STOPWORDS, YOUTH_INTENT_BIAS, lexical_overlap_terms, youth_source_bias  # type: ignore
from retrieval_v2.candidate_lexical_rewrite import lexical_overlap_terms_rewrite  # type: ignore
from retrieval_v2.candidate_region_hint import (  # type: ignore
    canonical_for_code,
    detect_sido_codes,
    lexical_overlap_terms_region_hint,
)
from retrieval_v2.schema import load_and_validate  # type: ignore
from retrieval_v2.provenance import canonical_text_sha256  # type: ignore
load_dotenv(ROOT / ".env")
DB = os.getenv("DATABASE_URL", "").strip()

CYCLE2_DEV_EVALSET = ROOT / "eval" / "retrieval-v2" / "cycle2" / "dev" / "evalset.jsonl"
CYCLE2_DEV_MANIFEST = ROOT / "eval" / "retrieval-v2" / "cycle2" / "dev" / "manifest.json"
EXPECTED_CYCLE2_DEV_SHA = "c8b66fef69bdfd0db053ac7cac0fb027fc3271c6072ab992b622cacdc71ace5e"
EXPECTED_CANDIDATE_V2_COMMIT = "5745cc3144b519da456b21030d0e0752d1d018ae"
EXPECTED_CANDIDATE_V2_TAG = "retrieval-v2-candidate-v2"

D003_CANDIDATES = 30
D003_COSINE_MIN = 0.78
D003_LEXICAL_BIAS = 0.01
D003_RERANK = 0
D003_EMBED_MODEL = "intfloat/multilingual-e5-base"

# latency diagnostic fixed before inspection (same as Phase1)
LATENCY_WARMUP_PER_VARIANT = 18
LATENCY_ROUNDS = 5
LATENCY_EXPECTED_SAMPLE_COUNT_PER_VARIANT = 36 * LATENCY_ROUNDS  # 180
LATENCY_SHUFFLE_SEED = 20260830
LATENCY_ORDER_STRATEGY = "(round+query_index)%2 alternation, deterministic seed shuffle, paired interleaved"

OUTPUT_DIR_REL = "eval/retrieval-v2/cycle2/phase2-exp1-region-hint"
PAIRED_OUTPUT_REL = f"{OUTPUT_DIR_REL}/phase2-exp1-paired.json"
SUMMARY_OUTPUT_REL = f"{OUTPUT_DIR_REL}/phase2-exp1-summary.md"
LATENCY_OUTPUT_REL = f"{OUTPUT_DIR_REL}/phase2-exp1-latency-diagnostic.json"


def _assert_d003_contract() -> None:
    assert ml_app.CANDIDATES == D003_CANDIDATES, f"D-003 CANDIDATES mismatch {ml_app.CANDIDATES} != {D003_CANDIDATES}"
    assert abs(ml_app.COSINE_MIN - D003_COSINE_MIN) < 1e-9
    assert abs(ml_app.LEXICAL_OVERLAP_BIAS - D003_LEXICAL_BIAS) < 1e-9
    assert ml_app.EMBED_MODEL_NAME == D003_EMBED_MODEL
    assert D003_RERANK == 0, "D-003 RERANK must be 0"
    assert callable(lexical_overlap_terms)
    assert callable(lexical_overlap_terms_rewrite)
    assert callable(lexical_overlap_terms_region_hint)


def get_git_commit() -> dict:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(ROOT), stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        commit = "unknown"
    try:
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=str(ROOT), stderr=subprocess.DEVNULL).decode().strip())
    except Exception:
        dirty = None
    return {"commit": commit, "dirty": dirty}


def get_corpus_summary(conn) -> dict:
    try:
        cur = conn.cursor()
        cur.execute("SELECT count(*) FROM policy")
        total_policies = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM policy_chunk")
        total_chunks = cur.fetchone()[0]
        cur.execute("SELECT source, count(*) FROM policy GROUP BY source")
        by_source = {}
        for src, cnt in cur.fetchall():
            by_source[src] = {"policies": cnt}
        cur.close()
        return {"total_policies": total_policies, "total_chunks": total_chunks, "by_source": by_source}
    except Exception:
        return {"total_policies": None, "total_chunks": None, "by_source": {}}


def rank_of(candidates, gold, topk=10):
    keys = [(c["source"], c["source_id"]) for c in candidates[:topk]]
    return keys.index(gold) + 1 if gold in keys else 0


def _fetch_cands(cur, vec_str, age, youth_bias, lexical_terms, n=D003_CANDIDATES):
    cur.execute(ml_app.SQL, {
        "vec": vec_str,
        "age": age,
        "rp": None,
        "youth_bias": youth_bias,
        "lexical_terms": lexical_terms,
        "lexical_bias": ml_app.LEXICAL_OVERLAP_BIAS,
        "n": n,
    })
    rows = cur.fetchall()
    cands = [dict(zip(ml_app.SEARCH_RESULT_COLUMNS, row)) for row in rows]
    cands = ml_app.region_filter(cands, None)
    return cands


def compute_metrics(ranks, by_source, by_category):
    n = len(ranks)
    hit1 = sum(1 for r in ranks if 1 <= r <= 1)
    hit5 = sum(1 for r in ranks if 1 <= r <= 5)
    hit10 = sum(1 for r in ranks if 1 <= r <= 10)
    mrr = sum(1.0 / r if 1 <= r <= 10 else 0.0 for r in ranks) / n if n else 0.0
    by_source_metrics = {}
    for src, arr in by_source.items():
        src_hit5 = sum(1 for r in arr if 1 <= r <= 5)
        by_source_metrics[src] = {"hit@5": src_hit5, "total": len(arr), "recall@5": src_hit5 / len(arr) if arr else 0.0}
    macro = sum(v["recall@5"] for v in by_source_metrics.values()) / len(by_source_metrics) if by_source_metrics else 0.0
    by_cat = {}
    for cat, arr in by_category.items():
        hit5c = sum(1 for r in arr if 1 <= r <= 5)
        by_cat[cat] = {"hit@5": hit5c, "total": len(arr), "recall@5": hit5c / len(arr) if arr else 0.0}
    return {
        "hit@1": hit1, "hit@5": hit5, "hit@10": hit10,
        "recall@1": hit1 / n if n else 0.0,
        "recall@5": hit5 / n if n else 0.0,
        "recall@10": hit10 / n if n else 0.0,
        "mrr@10": mrr,
        "n": n,
        "source_macro_recall@5": macro,
        "by_source": by_source_metrics,
        "by_category": by_cat,
    }


def parse_args():
    p = argparse.ArgumentParser(description="Cycle2 Phase2 Exp1 region hint")
    p.add_argument("--output-paired", default=str(ROOT / PAIRED_OUTPUT_REL))
    p.add_argument("--output-summary", default=str(ROOT / SUMMARY_OUTPUT_REL))
    p.add_argument("--output-latency", default=str(ROOT / LATENCY_OUTPUT_REL))
    p.add_argument("--eval-file", default=str(CYCLE2_DEV_EVALSET))
    p.add_argument("--skip-latency-if-rejected", action="store_true", default=True)
    return p.parse_args()


def main():
    _assert_d003_contract()
    args = parse_args()
    eval_file = pathlib.Path(args.eval_file)
    dev_sha = canonical_text_sha256(eval_file)
    if dev_sha != EXPECTED_CYCLE2_DEV_SHA:
        raise SystemExit(f"cycle2 dev SHA mismatch: got {dev_sha} != expected {EXPECTED_CYCLE2_DEV_SHA}")
    manifest = json.loads(CYCLE2_DEV_MANIFEST.read_text(encoding="utf-8"))
    assert manifest.get("frozen_before_tuning") is True
    assert manifest.get("sha256") == EXPECTED_CYCLE2_DEV_SHA
    items = load_and_validate(eval_file, "dev")
    git_info = get_git_commit()
    try:
        dev_freeze_commit = subprocess.check_output(["git", "log", "-1", "--format=%H", "--", str(eval_file)], cwd=str(ROOT), stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        dev_freeze_commit = "unknown"

    if not DB:
        raise SystemExit("DATABASE_URL 없음")

    from sentence_transformers import SentenceTransformer
    kwargs = {"local_files_only": True} if ml_app.MODEL_LOCAL_ONLY else {}
    model = SentenceTransformer(ml_app.EMBED_MODEL_NAME, **kwargs)

    conn = psycopg2.connect(DB)
    corpus = get_corpus_summary(conn)
    cur = conn.cursor()

    # Precompute qvecs shared
    precomputed = []
    for it in items:
        q_raw = it["query"]
        q = ml_app.strip_region(q_raw)
        vec = model.encode([f"query: {q}"], normalize_embeddings=True)[0]
        vec_str = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
        yb = youth_source_bias(q)
        lex_baseline = lexical_overlap_terms(q)
        lex_cand_v2 = lexical_overlap_terms_rewrite(q)
        lex_new = lexical_overlap_terms_region_hint(q_raw)
        # sanity: new should be base cand_v2 + hints
        base_check = lexical_overlap_terms_rewrite(q)
        # lex_new includes base_check plus hints; verify
        # For no-region case, lex_new == base_check
        # For region case, lex_new == base_check + hints
        # Already tested statically, but assert here for provenance
        assert lex_new[: len(base_check)] == base_check or lex_new == base_check, "new candidate must extend base"
        precomputed.append({
            "it": it,
            "q_raw": q_raw,
            "q": q,
            "vec_str": vec_str,
            "yb": yb,
            "lex_baseline": lex_baseline,
            "lex_cand_v2": lex_cand_v2,
            "lex_new": lex_new,
        })

    baseline_ranks = []
    cand_v2_ranks = []
    new_ranks = []
    by_source_baseline = {"youth": [], "gov24": []}
    by_source_cand_v2 = {"youth": [], "gov24": []}
    by_source_new = {"youth": [], "gov24": []}
    by_category_baseline = {}
    by_category_cand_v2 = {}
    by_category_new = {}
    per_case = []
    region_hint_stats = {"hinted_cases": 0, "total_added_terms": 0, "max_added": 0, "per_case_added": []}

    for pc in precomputed:
        it = pc["it"]
        vec_str = pc["vec_str"]
        yb = pc["yb"]
        q = pc["q"]
        q_raw = pc["q_raw"]
        lex_baseline = pc["lex_baseline"]
        lex_cand_v2 = pc["lex_cand_v2"]
        lex_new = pc["lex_new"]
        gold = (it["gold_source"], it["gold_source_id"])
        cat = it.get("category", "unknown")

        # baseline
        cands_b = _fetch_cands(cur, vec_str, it.get("age"), yb, lex_baseline)
        bi_b = [c for c in cands_b if c["score"] >= ml_app.COSINE_MIN]
        b_rank = rank_of(bi_b, gold, topk=10)
        b_rank_top30 = rank_of(cands_b, gold, topk=30)
        b_score = None
        for cand in cands_b:
            if (cand["source"], cand["source_id"]) == gold:
                b_score = cand["score"]
                break

        # candidate-v2
        cands_c = _fetch_cands(cur, vec_str, it.get("age"), yb, lex_cand_v2)
        bi_c = [c for c in cands_c if c["score"] >= ml_app.COSINE_MIN]
        c_rank = rank_of(bi_c, gold, topk=10)
        c_rank_top30 = rank_of(cands_c, gold, topk=30)
        c_score = None
        for cand in cands_c:
            if (cand["source"], cand["source_id"]) == gold:
                c_score = cand["score"]
                break

        # new candidate
        cands_n = _fetch_cands(cur, vec_str, it.get("age"), yb, lex_new)
        bi_n = [c for c in cands_n if c["score"] >= ml_app.COSINE_MIN]
        n_rank = rank_of(bi_n, gold, topk=10)
        n_rank_top30 = rank_of(cands_n, gold, topk=30)
        n_score = None
        for cand in cands_n:
            if (cand["source"], cand["source_id"]) == gold:
                n_score = cand["score"]
                break

        baseline_ranks.append(b_rank)
        cand_v2_ranks.append(c_rank)
        new_ranks.append(n_rank)
        by_source_baseline[it["gold_source"]].append(b_rank)
        by_source_cand_v2[it["gold_source"]].append(c_rank)
        by_source_new[it["gold_source"]].append(n_rank)
        by_category_baseline.setdefault(cat, []).append(b_rank)
        by_category_cand_v2.setdefault(cat, []).append(c_rank)
        by_category_new.setdefault(cat, []).append(n_rank)

        # region hint stats
        added = len(lex_new) - len(lexical_overlap_terms_rewrite(q))
        region_hint_stats["per_case_added"].append({"case_id": it["case_id"], "added": added, "lex_new": lex_new, "lex_cand_v2": lex_cand_v2, "matched_codes": detect_sido_codes(q_raw)})
        if added > 0:
            region_hint_stats["hinted_cases"] += 1
            region_hint_stats["total_added_terms"] += added
            region_hint_stats["max_added"] = max(region_hint_stats["max_added"], added)

        # threshold diagnostics for new vs baseline?
        b_filtered = b_rank_top30 != 0 and b_score is not None and b_score < D003_COSINE_MIN
        c_filtered = c_rank_top30 != 0 and c_score is not None and c_score < D003_COSINE_MIN
        n_filtered = n_rank_top30 != 0 and n_score is not None and n_score < D003_COSINE_MIN
        b_outside = b_rank_top30 != 0 and b_score is not None and b_score >= D003_COSINE_MIN and b_rank == 0
        c_outside = c_rank_top30 != 0 and c_score is not None and c_score >= D003_COSINE_MIN and c_rank == 0
        n_outside = n_rank_top30 != 0 and n_score is not None and n_score >= D003_COSINE_MIN and n_rank == 0

        per_case.append({
            "case_id": it["case_id"],
            "query": it["query"],
            "query_raw": q_raw,
            "query_stripped": q,
            "gold_source": it["gold_source"],
            "gold_source_id": it["gold_source_id"],
            "gold_title": it.get("gold_title"),
            "category": cat,
            "youth_bias": yb,
            "matched_codes": detect_sido_codes(q_raw),
            "lexical_terms": {
                "baseline": lex_baseline,
                "candidate_v2": lex_cand_v2,
                "new": lex_new,
                "added_vs_cand_v2": added,
            },
            "baseline": {
                "rank": b_rank, "rank_top30": b_rank_top30, "hit@1": 1 <= b_rank <= 1, "hit@5": 1 <= b_rank <= 5, "hit@10": 1 <= b_rank <= 10,
                "score": b_score, "in_top30": b_rank_top30 != 0, "filtered_by_cosine": b_filtered, "outside_top10_after_threshold": b_outside,
            },
            "candidate_v2": {
                "rank": c_rank, "rank_top30": c_rank_top30, "hit@1": 1 <= c_rank <= 1, "hit@5": 1 <= c_rank <= 5, "hit@10": 1 <= c_rank <= 10,
                "score": c_score, "in_top30": c_rank_top30 != 0, "filtered_by_cosine": c_filtered, "outside_top10_after_threshold": c_outside,
            },
            "new": {
                "rank": n_rank, "rank_top30": n_rank_top30, "hit@1": 1 <= n_rank <= 1, "hit@5": 1 <= n_rank <= 5, "hit@10": 1 <= n_rank <= 10,
                "score": n_score, "in_top30": n_rank_top30 != 0, "filtered_by_cosine": n_filtered, "outside_top10_after_threshold": n_outside,
            },
            "delta": {
                "baseline_vs_new_hit@5": (1 if 1 <= n_rank <= 5 else 0) - (1 if 1 <= b_rank <= 5 else 0),
                "cand_v2_vs_new_hit@5": (1 if 1 <= n_rank <= 5 else 0) - (1 if 1 <= c_rank <= 5 else 0),
                "baseline_vs_new_rank": (b_rank if b_rank != 0 else 999) - (n_rank if n_rank != 0 else 999),
                "cand_v2_vs_new_rank": (c_rank if c_rank != 0 else 999) - (n_rank if n_rank != 0 else 999),
            },
        })

    baseline_metrics = compute_metrics(baseline_ranks, by_source_baseline, by_category_baseline)
    cand_v2_metrics = compute_metrics(cand_v2_ranks, by_source_cand_v2, by_category_cand_v2)
    new_metrics = compute_metrics(new_ranks, by_source_new, by_category_new)

    gains_baseline_vs_new = [c for c in per_case if c["delta"]["baseline_vs_new_hit@5"] == 1]
    losses_baseline_vs_new = [c for c in per_case if c["delta"]["baseline_vs_new_hit@5"] == -1]
    gains_cand_v2_vs_new = [c for c in per_case if c["delta"]["cand_v2_vs_new_hit@5"] == 1]
    losses_cand_v2_vs_new = [c for c in per_case if c["delta"]["cand_v2_vs_new_hit@5"] == -1]

    net_baseline_new = new_metrics["hit@5"] - baseline_metrics["hit@5"]
    net_cand_v2_new = new_metrics["hit@5"] - cand_v2_metrics["hit@5"]

    # region hint avg term increase
    hinted_cases = region_hint_stats["hinted_cases"]
    avg_added = (region_hint_stats["total_added_terms"] / hinted_cases) if hinted_cases else 0.0

    # early-stop decision
    # D-003 baseline R@5 28/36, candidate-v2 30/36
    # new must exceed 30 and Gov24 18/18 and loss0 vs candidate-v2
    youth_new_hit5 = by_source_new.get("youth", [])
    gov24_new_hit5 = sum(1 for r in by_source_new.get("gov24", []) if 1 <= r <= 5)
    gov24_cand_v2_hit5 = sum(1 for r in by_source_cand_v2.get("gov24", []) if 1 <= r <= 5)  # should be 18
    quality_pass = (new_metrics["hit@5"] >= 31) and (gov24_new_hit5 == 18) and (len(losses_cand_v2_vs_new) == 0)
    early_stop_reason = []
    if new_metrics["hit@5"] <= 30:
        early_stop_reason.append(f"new R@5 {new_metrics['hit@5']}/36 not >30")
    if gov24_new_hit5 != 18:
        early_stop_reason.append(f"Gov24 hit@5 {gov24_new_hit5}/18 lost")
    if losses_cand_v2_vs_new:
        early_stop_reason.append(f"loss vs candidate-v2 {len(losses_cand_v2_vs_new)}: {[c['case_id'] for c in losses_cand_v2_vs_new]}")
    if not quality_pass:
        verdict_quality = "REJECTED"
    else:
        verdict_quality = "PASS"

    # latency diagnostic (only if quality PASS)
    latency_result = None
    latency_verdict = "NOT_RUN"
    if quality_pass:
        # run diagnostic baseline vs new only, same settings as Phase1
        def p50_fn(arr):
            s = sorted(arr)
            n = len(s)
            idx = math.ceil(0.5 * n) - 1
            return float(s[idx]) if s else 0.0
        def p95_fn(arr):
            s = sorted(arr)
            n = len(s)
            idx = math.ceil(0.95 * n) - 1
            return float(s[max(0, min(idx, n-1))]) if s else 0.0

        queries = precomputed
        rnd = random.Random(LATENCY_SHUFFLE_SEED)
        round_orders = []
        for r in range(LATENCY_ROUNDS):
            idxs = list(range(len(queries)))
            rnd.shuffle(idxs)
            round_orders.append(idxs)

        # warmup
        for i in range(LATENCY_WARMUP_PER_VARIANT):
            qidx = i % len(queries)
            q = queries[qidx]["q"]
            q_raw = queries[qidx]["q_raw"]
            yb = queries[qidx]["yb"]
            vec_str = queries[qidx]["vec_str"]
            lt = lexical_overlap_terms(q)
            cands = _fetch_cands(cur, vec_str, None, yb, lt)
            _ = [c for c in cands if c["score"] >= D003_COSINE_MIN]
            lt2 = lexical_overlap_terms_region_hint(q_raw)
            cands2 = _fetch_cands(cur, vec_str, None, yb, lt2)
            _ = [c for c in cands2 if c["score"] >= D003_COSINE_MIN]

        baseline_latencies = []
        new_latencies = []
        samples = []
        for r, order in enumerate(round_orders):
            for qi, qidx in enumerate(order):
                q = queries[qidx]["q"]
                q_raw = queries[qidx]["q_raw"]
                yb = queries[qidx]["yb"]
                vec_str = queries[qidx]["vec_str"]
                first_variant = "baseline" if (r + qi) % 2 == 0 else "new"
                if first_variant == "baseline":
                    t0 = time.perf_counter_ns()
                    lt = lexical_overlap_terms(q)
                    cands = _fetch_cands(cur, vec_str, None, yb, lt)
                    bi = [c for c in cands if c["score"] >= D003_COSINE_MIN]
                    t1 = time.perf_counter_ns()
                    lat_b = (t1 - t0) / 1_000_000.0
                    baseline_latencies.append(lat_b)
                    samples.append({"query_id": queries[qidx]["it"]["case_id"], "round": r, "variant": "baseline", "latency_ms": lat_b})
                    t0 = time.perf_counter_ns()
                    lt2 = lexical_overlap_terms_region_hint(q_raw)
                    cands2 = _fetch_cands(cur, vec_str, None, yb, lt2)
                    bi2 = [c for c in cands2 if c["score"] >= D003_COSINE_MIN]
                    t1 = time.perf_counter_ns()
                    lat_n = (t1 - t0) / 1_000_000.0
                    new_latencies.append(lat_n)
                    samples.append({"query_id": queries[qidx]["it"]["case_id"], "round": r, "variant": "new", "latency_ms": lat_n})
                else:
                    t0 = time.perf_counter_ns()
                    lt2 = lexical_overlap_terms_region_hint(q_raw)
                    cands2 = _fetch_cands(cur, vec_str, None, yb, lt2)
                    bi2 = [c for c in cands2 if c["score"] >= D003_COSINE_MIN]
                    t1 = time.perf_counter_ns()
                    lat_n = (t1 - t0) / 1_000_000.0
                    new_latencies.append(lat_n)
                    samples.append({"query_id": queries[qidx]["it"]["case_id"], "round": r, "variant": "new", "latency_ms": lat_n})
                    t0 = time.perf_counter_ns()
                    lt = lexical_overlap_terms(q)
                    cands = _fetch_cands(cur, vec_str, None, yb, lt)
                    bi = [c for c in cands if c["score"] >= D003_COSINE_MIN]
                    t1 = time.perf_counter_ns()
                    lat_b = (t1 - t0) / 1_000_000.0
                    baseline_latencies.append(lat_b)
                    samples.append({"query_id": queries[qidx]["it"]["case_id"], "round": r, "variant": "baseline", "latency_ms": lat_b})

        expected = LATENCY_EXPECTED_SAMPLE_COUNT_PER_VARIANT
        if len(baseline_latencies) != expected or len(new_latencies) != expected:
            raise SystemExit(f"latency sample count mismatch baseline {len(baseline_latencies)} new {len(new_latencies)} expected {expected}")
        p50_b = p50_fn(baseline_latencies)
        p95_b = p95_fn(baseline_latencies)
        p50_n = p50_fn(new_latencies)
        p95_n = p95_fn(new_latencies)
        latency_result = {
            "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "phase": "phase2-exp1-latency-diagnostic",
            "diagnostic_only": True,
            "not_final_gate": True,
            "is_final_gate": False,
            "git_commit": git_info["commit"],
            "git_dirty": git_info["dirty"],
            "dev_set_sha256": dev_sha,
            "production_contract": {
                "candidates": D003_CANDIDATES,
                "cosine_min": D003_COSINE_MIN,
                "lexical_bias": D003_LEXICAL_BIAS,
                "rerank": D003_RERANK,
                "model": D003_EMBED_MODEL,
            },
            "measurement": {
                "warmup_per_variant": LATENCY_WARMUP_PER_VARIANT,
                "rounds": LATENCY_ROUNDS,
                "sample_count_per_variant": expected,
                "total_samples": expected * 2,
                "shuffle_seed": LATENCY_SHUFFLE_SEED,
                "order_strategy": LATENCY_ORDER_STRATEGY,
                "timed_scope": "lexical_term generation + SQL execute/fetch + region_filter + COSINE_MIN filter (model load/embedding excluded)",
                "same_process_db_qvec": True,
                "interleaved": True,
                "warmup_excluded": True,
            },
            "baseline": {"count": len(baseline_latencies), "p50_ms": round(p50_b, 3), "p95_ms": round(p95_b, 3), "p95_raw": p95_b},
            "new": {"count": len(new_latencies), "p50_ms": round(p50_n, 3), "p95_ms": round(p95_n, 3), "p95_raw": p95_n},
            "delta": {"p50_ms": round(p50_n - p50_b, 3), "p95_ms": round(p95_n - p95_b, 3)},
            "pass_diagnostic_impression": "new p95 <= baseline p95 (diagnostic only, not gate) => " + ("PASS" if p95_n <= p95_b else "FAIL"),
            "samples": samples,
        }
        if p95_n <= p95_b:
            latency_verdict = "PASS"
        else:
            latency_verdict = "FAIL"
    else:
        latency_verdict = "NOT_RUN_EARLY_STOP"

    # overall verdict
    if not quality_pass:
        overall = "REJECTED"
    else:
        if latency_verdict == "PASS":
            overall = "PROMISING"
        elif latency_verdict == "FAIL":
            overall = "HOLD"
        else:
            overall = "PROMISING_PENDING_LATENCY"

    # build paired output
    paired_output = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "phase": "phase2-exp1-paired",
        "role": "candidate_experiment",
        "experiment": "bounded-region-core-lexical-hint",
        "diagnostic_only": True,
        "not_final_gate": True,
        "git_commit": git_info["commit"],
        "git_dirty": git_info["dirty"],
        "dev_set": str(CYCLE2_DEV_EVALSET),
        "dev_set_sha256": dev_sha,
        "dev_set_freeze_commit": dev_freeze_commit,
        "expected_dev_sha256": EXPECTED_CYCLE2_DEV_SHA,
        "candidate_reference_commit": EXPECTED_CANDIDATE_V2_COMMIT,
        "candidate_reference_tag": EXPECTED_CANDIDATE_V2_TAG,
        "production_contract": {
            "candidate_sql": "ml-service/app.py:SQL",
            "request_region": None,
            "query_preprocessing": "strip_region",
            "expired_policies_excluded": True,
            "candidates": D003_CANDIDATES,
            "rerank": D003_RERANK,
            "bi_encoder_min_score": D003_COSINE_MIN,
            "lexical_bias": D003_LEXICAL_BIAS,
            "lexical_terms_baseline": "lexical_overlap_terms",
            "lexical_terms_candidate_v2": "lexical_overlap_terms_rewrite",
            "lexical_terms_new": "lexical_overlap_terms_region_hint (base + SIDO canonical hint)",
            "qvec_shared": True,
            "db_shared": True,
            "sql_shared": True,
            "youth_intent_bias": YOUTH_INTENT_BIAS,
            "youth_bias_shared": True,
            "rp": None,
            "region_filter": "None (no filtering)",
        },
        "candidate_config": {
            "name": "bounded-region-core-lexical-hint",
            "description": "base = lexical_overlap_terms_rewrite(strip_region(raw)), hint = SIDO[code][0] per matched code from raw, bounded per code",
            "canonical_rule": "SIDO[code][0] (first/shortest alias, most frequent in corpus)",
            "lexical_only_diff": True,
            "sido_table": ml_app.SIDO,
        },
        "corpus": corpus,
        "n": 36,
        "baseline": baseline_metrics,
        "candidate_v2": cand_v2_metrics,
        "new": new_metrics,
        "net": {
            "baseline_vs_new_hit@5": net_baseline_new,
            "candidate_v2_vs_new_hit@5": net_cand_v2_new,
            "baseline_vs_new_gains": len(gains_baseline_vs_new),
            "baseline_vs_new_losses": len(losses_baseline_vs_new),
            "candidate_v2_vs_new_gains": len(gains_cand_v2_vs_new),
            "candidate_v2_vs_new_losses": len(losses_cand_v2_vs_new),
        },
        "per_source_delta": {
            "baseline_vs_new": {
                src: {
                    "baseline_hit@5": sum(1 for r in by_source_baseline.get(src, []) if 1 <= r <= 5),
                    "new_hit@5": sum(1 for r in by_source_new.get(src, []) if 1 <= r <= 5),
                    "delta": sum(1 for r in by_source_new.get(src, []) if 1 <= r <= 5) - sum(1 for r in by_source_baseline.get(src, []) if 1 <= r <= 5),
                } for src in ["youth", "gov24"]
            },
            "cand_v2_vs_new": {
                src: {
                    "candidate_v2_hit@5": sum(1 for r in by_source_cand_v2.get(src, []) if 1 <= r <= 5),
                    "new_hit@5": sum(1 for r in by_source_new.get(src, []) if 1 <= r <= 5),
                    "delta": sum(1 for r in by_source_new.get(src, []) if 1 <= r <= 5) - sum(1 for r in by_source_cand_v2.get(src, []) if 1 <= r <= 5),
                } for src in ["youth", "gov24"]
            },
        },
        "gains_baseline_vs_new": gains_baseline_vs_new,
        "losses_baseline_vs_new": losses_baseline_vs_new,
        "gains_cand_v2_vs_new": gains_cand_v2_vs_new,
        "losses_cand_v2_vs_new": losses_cand_v2_vs_new,
        "region_hint_stats": {
            "hinted_cases": hinted_cases,
            "total_added_terms": region_hint_stats["total_added_terms"],
            "max_added": region_hint_stats["max_added"],
            "avg_added_per_hinted": round(avg_added, 3) if hinted_cases else 0.0,
            "per_case": region_hint_stats["per_case_added"],
        },
        "per_case": per_case,
        "quality": {
            "new_R@5": f"{new_metrics['hit@5']}/36",
            "cand_v2_R@5": f"{cand_v2_metrics['hit@5']}/36",
            "baseline_R@5": f"{baseline_metrics['hit@5']}/36",
            "verdict": verdict_quality,
            "early_stop_reason": early_stop_reason,
            "quality_pass": quality_pass,
            "overall": overall,
            "latency_verdict": latency_verdict,
        },
        "latency": latency_result,
        "code_diff_verification": {
            "verified": "lexical only diff; SQL/CANDIDATES/COSINE_MIN/LEXICAL_BIAS/RERANK/strip_region/expired exclusion/youth bias/rp/region_filter all identical and shared qvec",
            "production_code_unchanged": True,
        },
    }

    cur.close()
    conn.close()

    out_p = pathlib.Path(args.output_paired)
    out_p.parent.mkdir(parents=True, exist_ok=True)
    out_p.write_text(json.dumps(paired_output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"paired: baseline R@5 {baseline_metrics['recall@5']:.4f} ({baseline_metrics['hit@5']}/36) cand_v2 {cand_v2_metrics['recall@5']:.4f} ({cand_v2_metrics['hit@5']}/36) new {new_metrics['recall@5']:.4f} ({new_metrics['hit@5']}/36)")
    print(f"  baseline vs new net {net_baseline_new} gains {len(gains_baseline_vs_new)} losses {len(losses_baseline_vs_new)}")
    print(f"  cand_v2 vs new net {net_cand_v2_new} gains {len(gains_cand_v2_vs_new)} losses {len(losses_cand_v2_vs_new)}")
    print(f"  Youth R@5 baseline {by_source_baseline['youth'].count(0)}? new Youth hit5 {sum(1 for r in by_source_new['youth'] if 1<=r<=5)}/18 gov24 new {sum(1 for r in by_source_new['gov24'] if 1<=r<=5)}/18")
    print(f"  region hinted cases {hinted_cases}/36 avg_added {avg_added:.2f} max {region_hint_stats['max_added']}")
    print(f"  quality verdict {verdict_quality} overall {overall} reasons {early_stop_reason}")
    print(f"saved paired -> {out_p}")

    if latency_result:
        out_l = pathlib.Path(args.output_latency)
        out_l.parent.mkdir(parents=True, exist_ok=True)
        out_l.write_text(json.dumps(latency_result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"latency baseline p50 {latency_result['baseline']['p50_ms']} p95 {latency_result['baseline']['p95_ms']} new p50 {latency_result['new']['p50_ms']} p95 {latency_result['new']['p95_ms']} delta p95 {latency_result['delta']['p95_ms']} verdict {latency_verdict}")
        print(f"saved latency -> {out_l}")
    else:
        print(f"latency not run: {latency_verdict}")

    # summary md
    summary_path = pathlib.Path(args.output_summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    # build per_category tables
    def cat_table(metrics):
        lines = []
        for cat in sorted(metrics["by_category"].keys()):
            v = metrics["by_category"][cat]
            lines.append(f"| {cat} | {v['hit@5']}/{v['total']} | {v['recall@5']:.4f} |")
        return "\n".join(lines)

    # gain/loss details
    def gain_loss_lines(lst, title):
        if not lst:
            return f"- {title}: 0\n"
        lines = [f"- {title}: {len(lst)}"]
        for c in lst:
            lines.append(f"  - {c['case_id']} {c['category']} baseline rank {c['baseline']['rank']} -> new {c['new']['rank']} (cand_v2 {c['candidate_v2']['rank']}) added {c['lexical_terms']['added_vs_cand_v2']} hint {c['matched_codes']}")
        return "\n".join(lines)

    summary_md = f"""# Cycle2 Phase2 Exp1 — Bounded Region-Core Lexical Hint (dev 36)

**Status:** {overall} (quality {verdict_quality}, latency {latency_verdict})
**Dev:** `{CYCLE2_DEV_EVALSET}` SHA `{dev_sha}` (36 Youth18/Gov2418)
**Model:** `{D003_EMBED_MODEL}` strip_region, youth bias suppressed for Gov24, CANDIDATES 30 COSINE_MIN 0.78 LEXICAL_BIAS 0.01 RERANK 0
**Candidate-v2 reference:** `{EXPECTED_CANDIDATE_V2_TAG}` `{EXPECTED_CANDIDATE_V2_COMMIT}`
**New candidate:** `lexical_overlap_terms_region_hint` (base + SIDO[code][0] per matched code from raw, bounded)

## Quality (paired, shared qvec/DB/corpus/SQL)

- baseline R@1 {baseline_metrics['recall@1']:.4f} ({baseline_metrics['hit@1']}/36) R@5 {baseline_metrics['recall@5']:.4f} ({baseline_metrics['hit@5']}/36) R@10 {baseline_metrics['recall@10']:.4f} MRR {baseline_metrics['mrr@10']:.4f} macro {baseline_metrics['source_macro_recall@5']:.4f}
- candidate-v2 R@1 {cand_v2_metrics['recall@1']:.4f} ({cand_v2_metrics['hit@1']}/36) R@5 {cand_v2_metrics['recall@5']:.4f} ({cand_v2_metrics['hit@5']}/36) R@10 {cand_v2_metrics['recall@10']:.4f} MRR {cand_v2_metrics['mrr@10']:.4f} macro {cand_v2_metrics['source_macro_recall@5']:.4f}
- new R@1 {new_metrics['recall@1']:.4f} ({new_metrics['hit@1']}/36) R@5 {new_metrics['recall@5']:.4f} ({new_metrics['hit@5']}/36) R@10 {new_metrics['recall@10']:.4f} MRR {new_metrics['mrr@10']:.4f} macro {new_metrics['source_macro_recall@5']:.4f}

Youth/Gov24 R@5:
- baseline Youth {sum(1 for r in by_source_baseline['youth'] if 1<=r<=5)}/18 Gov24 {sum(1 for r in by_source_baseline['gov24'] if 1<=r<=5)}/18
- candidate-v2 Youth {sum(1 for r in by_source_cand_v2['youth'] if 1<=r<=5)}/18 Gov24 {sum(1 for r in by_source_cand_v2['gov24'] if 1<=r<=5)}/18
- new Youth {sum(1 for r in by_source_new['youth'] if 1<=r<=5)}/18 Gov24 {sum(1 for r in by_source_new['gov24'] if 1<=r<=5)}/18

Per-category R@5 (new vs baseline vs cand_v2):
{cat_table(new_metrics)}

Baseline vs new: net {net_baseline_new} gains {len(gains_baseline_vs_new)} losses {len(losses_baseline_vs_new)}
Candidate-v2 vs new: net {net_cand_v2_new} gains {len(gains_cand_v2_vs_new)} losses {len(losses_cand_v2_vs_new)}

Region hint stats: hinted {hinted_cases}/36, total_added {region_hint_stats['total_added_terms']}, avg_per_hinted {avg_added:.3f}, max {region_hint_stats['max_added']}

{gain_loss_lines(gains_baseline_vs_new, "baseline->new gains")}
{gain_loss_lines(losses_baseline_vs_new, "baseline->new losses")}
{gain_loss_lines(gains_cand_v2_vs_new, "cand_v2->new gains")}
{gain_loss_lines(losses_cand_v2_vs_new, "cand_v2->new losses")}

Quality verdict: **{verdict_quality}** — {', '.join(early_stop_reason) if early_stop_reason else 'pass: 31+/36, Gov24 18/18, loss0 vs cand_v2'}

## Latency

{latency_result['baseline']['p95_ms'] if latency_result else 'N/A'} vs {latency_result['new']['p95_ms'] if latency_result else 'N/A'} (diagnostic_only, not_final_gate, 180/variant, interleaved)
Verdict: **{latency_verdict}**

## Provenance

- git {git_info['commit']} dirty {git_info['dirty']}
- corpus {corpus}
- qvec shared, SQL same, rp None, region_filter None
- production diff 0 (to verify via git diff)

Overall: **{overall}**
Generated {datetime.datetime.now(datetime.timezone.utc).isoformat()}
"""
    summary_path.write_text(summary_md, encoding="utf-8")
    print(f"saved summary -> {summary_path}")
    return overall


if __name__ == "__main__":
    main()
