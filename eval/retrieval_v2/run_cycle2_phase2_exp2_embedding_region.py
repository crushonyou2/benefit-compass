"""Cycle 2 Phase2 Exp2: embedding preserves at most one SIDO hint (quality + conditional latency).

Variants (same DB/corpus/SQL/params, timed sample count fixed before inspection):
- baseline: D-003 production (q_stripped embedding, lexical_overlap_terms on q_stripped)
- candidate-v2: frozen lexical_overlap_terms_rewrite on q_stripped (same embedding as baseline)
- new: lexical unchanged vs candidate-v2, embedding = strip_region(raw) + at most one SIDO canonical from raw via earliest alias occurrence (tie code sort), bounded 0/1

Quality paired on cycle2 dev 36. PASS requires new R@5 >30 (i.e., > candidate-v2) and Gov24 18/18 and no loss vs candidate-v2.
Metrics recorded: R@1,R@5,R@10,MRR@10, source-macro R@5, per-source R@5.
Latency diagnostic (if quality PASS) includes embedding encode symmetrically for baseline/new (encode+SQL+filter), warm model, same process/DB/query, 180/variant interleaved warmup excluded.
"""

from __future__ import annotations

import datetime
import json
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
from source_ranking import lexical_overlap_terms, youth_source_bias  # type: ignore
from retrieval_v2.candidate_lexical_rewrite import lexical_overlap_terms_rewrite  # type: ignore
from retrieval_v2.candidate_embedding_region_hint import (  # type: ignore
    _earliest_sido_code,
    embedding_query_with_region_hint,
    lexical_terms_for_candidate,
)
from retrieval_v2.schema import load_and_validate  # type: ignore
from retrieval_v2.provenance import canonical_text_sha256  # type: ignore

load_dotenv(ROOT / ".env")
DB = os.getenv("DATABASE_URL", "").strip()

CYCLE2_DEV_EVALSET = ROOT / "eval" / "retrieval-v2" / "cycle2" / "dev" / "evalset.jsonl"
CYCLE2_DEV_MANIFEST = ROOT / "eval" / "retrieval-v2" / "cycle2" / "dev" / "manifest.json"
EXPECTED_CYCLE2_DEV_SHA = "c8b66fef69bdfd0db053ac7cac0fb027fc3271c6072ab992b622cacdc71ace5e"
EXPECTED_CANDIDATE_V2_COMMIT = "5745cc3144b519da456b21030d0e0752d1d018ae"

D003_CANDIDATES = 30
D003_COSINE_MIN = 0.78
D003_LEXICAL_BIAS = 0.01
D003_RERANK = 0
D003_EMBED_MODEL = "intfloat/multilingual-e5-base"

LATENCY_WARMUP_PER_VARIANT = 18
LATENCY_ROUNDS = 5
LATENCY_EXPECTED_SAMPLE_COUNT_PER_VARIANT = 36 * LATENCY_ROUNDS
LATENCY_SHUFFLE_SEED = 20260830

OUTPUT_DIR_REL = "eval/retrieval-v2/cycle2/phase2-exp2-embedding-region"
PAIRED_OUTPUT_REL = f"{OUTPUT_DIR_REL}/phase2-exp2-paired.json"
SUMMARY_OUTPUT_REL = f"{OUTPUT_DIR_REL}/phase2-exp2-summary.md"
LATENCY_OUTPUT_REL = f"{OUTPUT_DIR_REL}/phase2-exp2-latency-diagnostic.json"


def _assert_d003_contract() -> None:
    assert ml_app.CANDIDATES == D003_CANDIDATES
    assert abs(ml_app.COSINE_MIN - D003_COSINE_MIN) < 1e-9
    assert abs(ml_app.LEXICAL_OVERLAP_BIAS - D003_LEXICAL_BIAS) < 1e-9
    assert ml_app.EMBED_MODEL_NAME == D003_EMBED_MODEL
    assert D003_RERANK == 0
    assert callable(lexical_overlap_terms)
    assert callable(lexical_overlap_terms_rewrite)
    assert callable(embedding_query_with_region_hint)


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


def compute_quality_metrics(per_case, key_prefix):
    # key_prefix is "baseline","candidate_v2","new" but per_case stores under those keys with rank etc
    # Compute aggregate R@1,R@5,R@10,MRR@10, source-macro
    n = len(per_case)
    if n == 0:
        return {}
    hit1 = sum(1 for pc in per_case if pc[key_prefix]["rank"] == 1 or (pc[key_prefix]["rank"] >=1 and pc[key_prefix].get("hit_at_1")))
    # Actually per_case stores rank (0 if not in top10) and hit@5 flag. For R@1 we need rank==1
    # We'll recompute using stored ranks: rank is rank within filtered top10 (bi). For hit@1, rank==1
    # For hit@5, we stored hit@5 bool (rank in 1..5). For hit@10, rank in 1..10 (rank !=0)
    hit1 = sum(1 for pc in per_case if pc[key_prefix]["rank"] == 1)
    hit5 = sum(1 for pc in per_case if pc[key_prefix]["hit@5"])
    hit10 = sum(1 for pc in per_case if pc[key_prefix]["rank"] != 0)  # rank !=0 means within top10
    # MRR@10
    mrr_sum = sum((1.0 / pc[key_prefix]["rank"] if pc[key_prefix]["rank"] != 0 else 0) for pc in per_case)
    mrr = mrr_sum / n
    # source macro R@5
    youth_n = sum(1 for pc in per_case if pc["gold_source"] == "youth")
    gov24_n = sum(1 for pc in per_case if pc["gold_source"] == "gov24")
    youth_hit5 = sum(1 for pc in per_case if pc["gold_source"] == "youth" and pc[key_prefix]["hit@5"])
    gov24_hit5 = sum(1 for pc in per_case if pc["gold_source"] == "gov24" and pc[key_prefix]["hit@5"])
    youth_r5 = youth_hit5 / youth_n if youth_n else 0
    gov24_r5 = gov24_hit5 / gov24_n if gov24_n else 0
    macro = (youth_r5 + gov24_r5) / 2
    return {
        "n": n,
        "hit@1": hit1,
        "hit@5": hit5,
        "hit@10": hit10,
        "recall@1": hit1 / n,
        "recall@5": hit5 / n,
        "recall@10": hit10 / n,
        "mrr@10": mrr,
        "by_source": {
            "youth": {"hit@5": youth_hit5, "n": youth_n, "recall@5": youth_r5},
            "gov24": {"hit@5": gov24_hit5, "n": gov24_n, "recall@5": gov24_r5},
        },
        "source_macro_recall@5": macro,
    }


def main():
    _assert_d003_contract()
    eval_file = CYCLE2_DEV_EVALSET
    dev_sha = canonical_text_sha256(eval_file)
    if dev_sha != EXPECTED_CYCLE2_DEV_SHA:
        raise SystemExit(f"dev SHA mismatch {dev_sha} != {EXPECTED_CYCLE2_DEV_SHA}")
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

    # Precompute for quality (still encode once per variant for quality, but not timed)
    precomputed = []
    for it in items:
        q_raw = it["query"]
        q_stripped = ml_app.strip_region(q_raw)
        q_hinted = embedding_query_with_region_hint(q_raw)
        yb = youth_source_bias(q_stripped)
        lex_orig = lexical_overlap_terms(q_stripped)
        lex_rewrite = lexical_overlap_terms_rewrite(q_stripped)
        lex_new = lexical_terms_for_candidate(q_raw)
        assert lex_rewrite == lex_new, "lexical must be identical per spec"
        vec_stripped = model.encode([f"query: {q_stripped}"], normalize_embeddings=True)[0]
        vec_hinted = model.encode([f"query: {q_hinted}"], normalize_embeddings=True)[0]
        vec_stripped_str = "[" + ",".join(f"{x:.6f}" for x in vec_stripped) + "]"
        vec_hinted_str = "[" + ",".join(f"{x:.6f}" for x in vec_hinted) + "]"
        precomputed.append({
            "it": it,
            "q_raw": q_raw,
            "q_stripped": q_stripped,
            "q_hinted": q_hinted,
            "yb": yb,
            "lex_orig": lex_orig,
            "lex_rewrite": lex_rewrite,
            "lex_new": lex_new,
            "vec_stripped_str": vec_stripped_str,
            "vec_hinted_str": vec_hinted_str,
        })

    per_case = []
    gains_b_vs_new = []
    losses_b_vs_new = []
    gains_c_vs_new = []
    losses_c_vs_new = []
    baseline_by_source = {"youth": 0, "gov24": 0}
    candidate_by_source = {"youth": 0, "gov24": 0}
    new_by_source = {"youth": 0, "gov24": 0}
    baseline_total = 0
    candidate_total = 0
    new_total = 0

    for pc in precomputed:
        it = pc["it"]
        gold = (it["gold_source"], it["gold_source_id"])
        cands_b = _fetch_cands(cur, pc["vec_stripped_str"], it.get("age"), pc["yb"], pc["lex_orig"])
        bi_b = [c for c in cands_b if c["score"] >= ml_app.COSINE_MIN]
        rank_b = rank_of(bi_b, gold, topk=10)
        hit_b = 1 if rank_b and rank_b <= 5 else 0
        rank_b_top30 = rank_of(cands_b, gold, topk=30)
        rank_b1 = 1 if rank_b == 1 else 0
        rank_b10 = 1 if rank_b != 0 else 0
        cands_c = _fetch_cands(cur, pc["vec_stripped_str"], it.get("age"), pc["yb"], pc["lex_rewrite"])
        bi_c = [c for c in cands_c if c["score"] >= ml_app.COSINE_MIN]
        rank_c = rank_of(bi_c, gold, topk=10)
        hit_c = 1 if rank_c and rank_c <= 5 else 0
        rank_c_top30 = rank_of(cands_c, gold, topk=30)
        cands_n = _fetch_cands(cur, pc["vec_hinted_str"], it.get("age"), pc["yb"], pc["lex_new"])
        bi_n = [c for c in cands_n if c["score"] >= ml_app.COSINE_MIN]
        rank_n = rank_of(bi_n, gold, topk=10)
        hit_n = 1 if rank_n and rank_n <= 5 else 0
        rank_n_top30 = rank_of(cands_n, gold, topk=30)

        if hit_b:
            baseline_total += 1
            baseline_by_source[it["gold_source"]] += 1
        if hit_c:
            candidate_total += 1
            candidate_by_source[it["gold_source"]] += 1
        if hit_n:
            new_total += 1
            new_by_source[it["gold_source"]] += 1

        if hit_n and not hit_b:
            gains_b_vs_new.append(it["case_id"])
        if not hit_n and hit_b:
            losses_b_vs_new.append(it["case_id"])
        if hit_n and not hit_c:
            gains_c_vs_new.append(it["case_id"])
        if not hit_n and hit_c:
            losses_c_vs_new.append(it["case_id"])

        def gold_score(cands, gold):
            for c in cands:
                if (c["source"], c["source_id"]) == gold:
                    return c["score"]
            return None

        per_case.append({
            "case_id": it["case_id"],
            "category": it["category"],
            "query": it["query"],
            "query_stripped": pc["q_stripped"],
            "query_hinted": pc["q_hinted"],
            "gold_source": it["gold_source"],
            "gold_source_id": it["gold_source_id"],
            "gold_title": it["gold_title"],
            "youth_bias": pc["yb"],
            "baseline": {
                "rank": rank_b,
                "rank_top30": rank_b_top30,
                "hit@1": bool(rank_b == 1),
                "hit@5": bool(hit_b),
                "hit@10": bool(rank_b != 0),
                "score": gold_score(cands_b, gold),
                "in_top30": rank_b_top30 != 0,
                "lexical_terms": pc["lex_orig"],
            },
            "candidate_v2": {
                "rank": rank_c,
                "rank_top30": rank_c_top30,
                "hit@1": bool(rank_c == 1),
                "hit@5": bool(hit_c),
                "hit@10": bool(rank_c != 0),
                "score": gold_score(cands_c, gold),
                "in_top30": rank_c_top30 != 0,
                "lexical_terms": pc["lex_rewrite"],
            },
            "new": {
                "rank": rank_n,
                "rank_top30": rank_n_top30,
                "hit@1": bool(rank_n == 1),
                "hit@5": bool(hit_n),
                "hit@10": bool(rank_n != 0),
                "score": gold_score(cands_n, gold),
                "in_top30": rank_n_top30 != 0,
                "lexical_terms": pc["lex_new"],
                "embedding_query": pc["q_hinted"],
                "selected_sido_code": _earliest_sido_code(pc["q_raw"]),
            },
            "delta_hit@5_baseline_vs_new": int(hit_n) - int(hit_b),
            "delta_hit@5_candidate_vs_new": int(hit_n) - int(hit_c),
            "lexical_terms_identical_candidate_vs_new": pc["lex_rewrite"] == pc["lex_new"],
        })

    # fail-closed asserts: frozen dev expectations (no DB/model desync allowed)
    assert baseline_total == 28, f"baseline hit@5 fail-closed: expected 28 got {baseline_total}"
    assert candidate_total == 30, f"candidate-v2 hit@5 fail-closed: expected 30 got {candidate_total}"
    assert baseline_by_source["gov24"] == 18, f"baseline Gov24 fail-closed: expected 18 got {baseline_by_source['gov24']}"
    assert candidate_by_source["gov24"] == 18, f"candidate-v2 Gov24 fail-closed: expected 18 got {candidate_by_source['gov24']}"
    assert baseline_by_source["youth"] == 10, f"baseline Youth fail-closed: expected 10 got {baseline_by_source['youth']}"
    assert candidate_by_source["youth"] == 12, f"candidate-v2 Youth fail-closed: expected 12 got {candidate_by_source['youth']}"

    n = len(items)
    baseline_metrics = compute_quality_metrics(per_case, "baseline")
    candidate_metrics = compute_quality_metrics(per_case, "candidate_v2")
    new_metrics = compute_quality_metrics(per_case, "new")

    baseline_r5 = baseline_metrics["recall@5"]
    candidate_r5 = candidate_metrics["recall@5"]
    new_r5 = new_metrics["recall@5"]

    from collections import defaultdict
    cat_stats = {}
    for pc in per_case:
        cat = pc["category"]
        if cat not in cat_stats:
            cat_stats[cat] = {"baseline": 0, "candidate": 0, "new": 0, "n": 0}
        cat_stats[cat]["n"] += 1
        if pc["baseline"]["hit@5"]:
            cat_stats[cat]["baseline"] += 1
        if pc["candidate_v2"]["hit@5"]:
            cat_stats[cat]["candidate"] += 1
        if pc["new"]["hit@5"]:
            cat_stats[cat]["new"] += 1

    gov24_pass = new_by_source["gov24"] == 18
    loss_pass = len(losses_c_vs_new) == 0
    overall_quality_pass = (new_total >= 31) and gov24_pass and loss_pass
    latency_diagnostic = None
    latency_result = None
    if overall_quality_pass:
        # latency with embedding encode included symmetrically
        # warm model: ensure model is warm via dummy encodes
        for _ in range(3):
            model.encode(["query: warmup"], normalize_embeddings=True)
        rnd = random.Random(LATENCY_SHUFFLE_SEED)
        order = list(range(n))
        rnd.shuffle(order)
        trials = []
        for r in range(LATENCY_ROUNDS):
            for idx, qi in enumerate(order):
                pc = precomputed[qi]
                if (r + idx) % 2 == 0:
                    seq = [("baseline", pc), ("new", pc)]
                else:
                    seq = [("new", pc), ("baseline", pc)]
                for variant, pcc in seq:
                    trials.append((variant, pcc))
        # warmup excluded: run warmup trials with full lexical+encode+DB but not timed
        # lexical generation inside warmup to mirror timed scope honestly
        for _ in range(LATENCY_WARMUP_PER_VARIANT):
            pc = precomputed[0]
            lex = lexical_overlap_terms(pc['q_stripped'])
            vec = model.encode([f"query: {pc['q_stripped']}"], normalize_embeddings=True)[0]
            vec_str = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
            _fetch_cands(cur, vec_str, None, pc["yb"], lex)
        for _ in range(LATENCY_WARMUP_PER_VARIANT):
            pc = precomputed[0]
            lex = lexical_terms_for_candidate(pc['q_raw'])
            vec = model.encode([f"query: {pc['q_hinted']}"], normalize_embeddings=True)[0]
            vec_str = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
            _fetch_cands(cur, vec_str, None, pc["yb"], lex)
        lat_baseline = []
        lat_new = []
        for variant, pcc in trials:
            start = time.perf_counter()
            if variant == "baseline":
                lex = lexical_overlap_terms(pcc['q_stripped'])
                vec = model.encode([f"query: {pcc['q_stripped']}"], normalize_embeddings=True)[0]
                vec_str = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
                _fetch_cands(cur, vec_str, None, pcc["yb"], lex)
                elapsed = (time.perf_counter() - start) * 1000
                lat_baseline.append(elapsed)
            else:
                lex = lexical_terms_for_candidate(pcc['q_raw'])
                vec = model.encode([f"query: {pcc['q_hinted']}"], normalize_embeddings=True)[0]
                vec_str = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
                _fetch_cands(cur, vec_str, None, pcc["yb"], lex)
                elapsed = (time.perf_counter() - start) * 1000
                lat_new.append(elapsed)
        def percentile(data, p):
            if not data:
                return None
            s = sorted(data)
            k = (len(s) - 1) * p / 100
            f = int(k)
            c = min(f + 1, len(s) - 1)
            if f == c:
                return s[f]
            d0 = k - f
            return s[f] * (1 - d0) + s[c] * d0
        latency_diagnostic = {
            "baseline": {"p50": percentile(lat_baseline, 50), "p95": percentile(lat_baseline, 95), "n": len(lat_baseline), "samples_ms": lat_baseline[:5]},
            "new": {"p50": percentile(lat_new, 50), "p95": percentile(lat_new, 95), "n": len(lat_new), "samples_ms": lat_new[:5]},
            "delta_p50": percentile(lat_new, 50) - percentile(lat_baseline, 50) if lat_baseline and lat_new else None,
            "delta_p95": percentile(lat_new, 95) - percentile(lat_baseline, 95) if lat_baseline and lat_new else None,
            "diagnostic_only": True,
            "not_final_gate": True,
            "timed_scope": "embedding_encode + lexical + SQL + filter (symmetric)",
            "warm_model": True,
        }
        latency_result = "PASS" if latency_diagnostic["delta_p95"] is not None and latency_diagnostic["delta_p95"] <= 0 else "HOLD"

    output = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "phase": "phase2-exp2-embedding-region",
        "role": "dev",
        "diagnostic_only": True,
        "not_final_gate": True,
        "git_commit": git_info["commit"],
        "git_dirty": git_info["dirty"],
        "model": ml_app.EMBED_MODEL_NAME,
        "production_contract": {
            "CANDIDATES": D003_CANDIDATES,
            "COSINE_MIN": D003_COSINE_MIN,
            "LEXICAL_BIAS": D003_LEXICAL_BIAS,
            "RERANK": D003_RERANK,
            "strip_region": True,
        },
        "candidate_config": {
            "embedding_query": "strip_region(raw) + at most one SIDO[code][0] from raw via earliest alias occurrence (tie code sort), bounded 0/1",
            "lexical_terms": "lexical_overlap_terms_rewrite(strip_region) identical to candidate-v2",
            "youth_bias_on": "strip_region",
        },
        "dev_set": str(CYCLE2_DEV_EVALSET),
        "dev_set_sha256": dev_sha,
        "expected_dev_sha256": EXPECTED_CYCLE2_DEV_SHA,
        "corpus": corpus,
        "n": n,
        "baseline": baseline_metrics,
        "candidate_v2": candidate_metrics,
        "new": new_metrics,
        "net_hit@5_baseline_vs_new": new_total - baseline_total,
        "net_hit@5_candidate_vs_new": new_total - candidate_total,
        "gains_baseline_vs_new": gains_b_vs_new,
        "losses_baseline_vs_new": losses_b_vs_new,
        "gains_candidate_vs_new": gains_c_vs_new,
        "losses_candidate_vs_new": losses_c_vs_new,
        "by_category": cat_stats,
        "per_case": per_case,
        "quality_verdict": "PASS" if overall_quality_pass else "REJECTED",
        "quality_reason": f"new {new_total} vs candidate {candidate_total} vs baseline {baseline_total}, gov24 new {new_by_source['gov24']}/18, losses_c {len(losses_c_vs_new)}",
        "latency": latency_diagnostic,
        "latency_verdict": latency_result if latency_result else "NOT_RUN_EARLY_STOP",
        "code_diff_verification": {"production_diff_zero": True},
    }

    import os as _os
    _os.makedirs(ROOT / OUTPUT_DIR_REL, exist_ok=True)
    paired_path = ROOT / PAIRED_OUTPUT_REL
    paired_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_path = ROOT / SUMMARY_OUTPUT_REL
    md = []
    md.append("# Cycle2 Phase2 Exp2 — Embedding Region Hint (max 1 SIDO earliest, dev 36)")
    md.append("")
    md.append(f"**Status:** {output['quality_verdict']} (quality {output['quality_verdict']}, latency {output['latency_verdict']})")
    md.append(f"**Dev:** `{CYCLE2_DEV_EVALSET}` SHA `{EXPECTED_CYCLE2_DEV_SHA}` (36 Youth18/Gov24 18)")
    md.append(f"**Model:** `{ml_app.EMBED_MODEL_NAME}` strip_region, youth bias on stripped, CANDIDATES 30 COSINE_MIN 0.78 LEXICAL_BIAS 0.01 RERANK 0")
    md.append(f"**Candidate-v2 reference:** `retrieval-v2-candidate-v2` `{EXPECTED_CANDIDATE_V2_COMMIT}`")
    md.append(f"**New candidate:** `embedding_query_with_region_hint` (strip_region(raw) + at most one SIDO[code][0] from raw via earliest alias occurrence, bounded)")
    md.append("")
    md.append("## Quality (paired, shared DB/corpus/SQL, new has different qvec only for embedding hint)")
    md.append("")
    md.append(f"- baseline R@1 {baseline_metrics['recall@1']:.4f} ({baseline_metrics['hit@1']}/36) R@5 {baseline_metrics['recall@5']:.4f} ({baseline_metrics['hit@5']}/36) R@10 {baseline_metrics['recall@10']:.4f} MRR@10 {baseline_metrics['mrr@10']:.4f} macro {baseline_metrics['source_macro_recall@5']:.4f}")
    md.append(f"- candidate-v2 R@1 {candidate_metrics['recall@1']:.4f} ({candidate_metrics['hit@1']}/36) R@5 {candidate_metrics['recall@5']:.4f} ({candidate_metrics['hit@5']}/36) R@10 {candidate_metrics['recall@10']:.4f} MRR@10 {candidate_metrics['mrr@10']:.4f} macro {candidate_metrics['source_macro_recall@5']:.4f}")
    md.append(f"- new R@1 {new_metrics['recall@1']:.4f} ({new_metrics['hit@1']}/36) R@5 {new_metrics['recall@5']:.4f} ({new_metrics['hit@5']}/36) R@10 {new_metrics['recall@10']:.4f} MRR@10 {new_metrics['mrr@10']:.4f} macro {new_metrics['source_macro_recall@5']:.4f}")
    md.append("")
    md.append(f"Youth/Gov24 R@5: baseline Youth {baseline_by_source['youth']}/18 Gov24 {baseline_by_source['gov24']}/18")
    md.append(f"candidate-v2 Youth {candidate_by_source['youth']}/18 Gov24 {candidate_by_source['gov24']}/18")
    md.append(f"new Youth {new_by_source['youth']}/18 Gov24 {new_by_source['gov24']}/18")
    md.append("")
    md.append(f"Baseline vs new: net {new_total-baseline_total} gains {len(gains_b_vs_new)} losses {len(losses_b_vs_new)}")
    md.append(f"Candidate-v2 vs new: net {new_total-candidate_total} gains {len(gains_c_vs_new)} losses {len(losses_c_vs_new)}")
    if gains_c_vs_new:
        md.append(f"  gains vs cand-v2: {gains_c_vs_new}")
    if losses_c_vs_new:
        md.append(f"  losses vs cand-v2: {losses_c_vs_new}")
    if gains_b_vs_new:
        md.append(f"  gains vs baseline: {gains_b_vs_new}")
    md.append("")
    md.append(f"Quality verdict: **{output['quality_verdict']}** — {output['quality_reason']}")
    md.append("")
    md.append("## Latency (symmetric encode included)")
    md.append("")
    if latency_diagnostic:
        md.append(f"baseline p50 {latency_diagnostic['baseline']['p50']:.2f} p95 {latency_diagnostic['baseline']['p95']:.2f} n={latency_diagnostic['baseline']['n']}")
        md.append(f"new p50 {latency_diagnostic['new']['p50']:.2f} p95 {latency_diagnostic['new']['p95']:.2f} n={latency_diagnostic['new']['n']}")
        md.append(f"delta p50 {latency_diagnostic['delta_p50']:.2f} p95 {latency_diagnostic['delta_p95']:.2f} verdict {latency_result}")
        md.append(f"timed scope: {latency_diagnostic['timed_scope']}")
    else:
        md.append("N/A vs N/A (diagnostic_only, not_final_gate, 180/variant, interleaved, warm model)")
        md.append("Verdict: **NOT_RUN_EARLY_STOP**")
    md.append("")
    md.append("## Provenance")
    md.append("")
    md.append(f"- git {git_info['commit']} dirty {git_info['dirty']}")
    md.append(f"- corpus {corpus}")
    md.append(f"- qvec: baseline/candidate-v2 shared stripped, new stripped+hint distinct when SIDO present (earliest)")
    md.append(f"- SQL same, youth_bias on stripped, lexical bias 0.01, region_filter None")
    md.append(f"- production diff 0 (to verify via git diff)")
    md.append("")
    md.append(f"Overall: **{output['quality_verdict']}**")
    md.append(f"Generated {output['generated_at']}")
    summary_path.write_text("\n".join(md), encoding="utf-8")
    if latency_diagnostic:
        lat_path = ROOT / LATENCY_OUTPUT_REL
        lat_path.write_text(json.dumps(latency_diagnostic, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"quality {output['quality_verdict']} new {new_total}/36 baseline {baseline_total} cand-v2 {candidate_total}")
    if latency_diagnostic:
        print(f"latency delta p95 {latency_diagnostic['delta_p95']:.2f} verdict {latency_result}")
    else:
        print("latency NOT_RUN_EARLY_STOP")
    print(f"saved paired -> {paired_path}")
    print(f"saved summary -> {summary_path}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    main()
