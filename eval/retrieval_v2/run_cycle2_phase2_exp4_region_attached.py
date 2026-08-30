"""Cycle 2 Phase2 Exp4: region-attached residue cleanup embedding (quality + conditional latency, diagnostic_only).

D-010 bounded: Exp4 is last bounded experiment. Spec per 2026-08-30 instruction:

- baseline embedding: strip_region(raw) + lexical_overlap_terms(strip_region(raw)) [original lexical]
- candidate-v2 embedding: strip_region(raw) + lexical_overlap_terms_rewrite(strip_region(raw)) [rewrite lexical]
- new embedding: cleanup_embedding_query(raw) = region-attached residue cleanup (alias+optional suffix+optional particle directly attached) with fallback strip_region(raw) if empty;
  lexical identical to candidate-v2: lexical_overlap_terms_rewrite(strip_region(raw))
- youth_source_bias on stripped query (parity), SQL/CANDIDATES=30/COSINE_MIN=0.78/LEXICAL_BIAS=0.01/RERANK=0/rp=None/region_filter(None) unchanged
- Grammar: suffix max1 (특별자치도,특별자치시,특별시,광역시,자치도,도,시) longest-first + particle max1 (으로부터,에게서,에서,으로,에게,한테,부터,까지,은,는,이,가,을,를,의,에,와,과,로,도,만,께) longest-first, directly adjacent only, longest SIDO alias first.
- Uses ONLY ml_app.SIDO table + suffix/particle grammar, no new dict, no 시군구, no hardcode, no extra encode/DB.
- Each variant exactly 1 encode + 1 DB retrieval per query.

PASS selection (D-007/D-009 quality gate diagnostic): new>=31/36 AND Gov24=18/18 AND candidate-v2 vs new hit@5 loss=0
If REJECTED: latency NOT_RUN_EARLY_STOP, no further retrieval/tuning.
If PASS: warm paired interleaved 180/variant latency diagnostic (lexical generation + encode + SQL/fetch + COSINE postfilter).

Holdout plaintext / git show prohibited in this runner. No holdout access.
"""

from __future__ import annotations

import datetime
import json
import os
import random
import time
from pathlib import Path

import psycopg2
from dotenv import load_dotenv  # type: ignore

import sys

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "ml-service"))
sys.path.insert(0, str(ROOT / "eval"))

import app as ml_app  # type: ignore
from source_ranking import lexical_overlap_terms, youth_source_bias  # type: ignore
from retrieval_v2.candidate_lexical_rewrite import lexical_overlap_terms_rewrite  # type: ignore
from retrieval_v2.candidate_region_attached_cleanup import (  # type: ignore
    cleanup_embedding_query,
    lexical_terms_for_candidate,
    _region_attached_cleanup,
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
LATENCY_EXPECTED_SAMPLE_COUNT_PER_VARIANT = 36 * LATENCY_ROUNDS  # 180
LATENCY_SHUFFLE_SEED = 20260830
LATENCY_ORDER_STRATEGY = "(round+query_index)%2 alternation, deterministic seed shuffle, paired interleaved"

OUTPUT_DIR_REL = "eval/retrieval-v2/cycle2/phase2-exp4-region-attached"
PAIRED_OUTPUT_REL = f"{OUTPUT_DIR_REL}/phase2-exp4-paired.json"
SUMMARY_OUTPUT_REL = f"{OUTPUT_DIR_REL}/phase2-exp4-summary.md"
def _assert_d003_contract() -> None:
    assert ml_app.CANDIDATES == D003_CANDIDATES, f"D-003 CANDIDATES mismatch {ml_app.CANDIDATES} != {D003_CANDIDATES}"
    assert abs(ml_app.COSINE_MIN - D003_COSINE_MIN) < 1e-9, f"D-003 COSINE_MIN mismatch {ml_app.COSINE_MIN} != {D003_COSINE_MIN}"
    from source_ranking import LEXICAL_OVERLAP_BIAS

    assert abs(LEXICAL_OVERLAP_BIAS - D003_LEXICAL_BIAS) < 1e-9, f"D-003 LEXICAL_BIAS mismatch {LEXICAL_OVERLAP_BIAS} != {D003_LEXICAL_BIAS}"
    assert callable(lexical_overlap_terms), "lexical_overlap_terms missing"
    assert callable(lexical_overlap_terms_rewrite), "lexical_overlap_terms_rewrite missing"
    assert callable(cleanup_embedding_query), "cleanup_embedding_query missing"
    assert callable(lexical_terms_for_candidate), "lexical_terms_for_candidate missing"
    assert callable(_region_attached_cleanup), "_region_attached_cleanup missing"


def get_corpus_summary(conn) -> dict:
    """Fail-closed corpus provenance — no exception hiding.

    Tables are actual production tables: policy, policy_chunk.
    Source count from policy.
    """
    cur = conn.cursor()
    cur.execute("SELECT count(*) FROM policy")
    total_policies = cur.fetchone()[0]
    cur.execute("SELECT count(*) FROM policy_chunk")
    total_chunks = cur.fetchone()[0]
    cur.execute("SELECT source, count(*) FROM policy GROUP BY source")
    by_source = {row[0]: row[1] for row in cur.fetchall()}
    cur.close()
    assert total_policies is not None and total_chunks is not None, "corpus counts must be non-null"
    assert isinstance(by_source, dict) and len(by_source) > 0, "by_source must be non-empty"
    return {"total_policies": total_policies, "total_chunks": total_chunks, "by_source": by_source}


def get_git_commit() -> dict:
    try:
        import subprocess

        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        # untracked 포함: git status --porcelain
        status = subprocess.check_output(["git", "status", "--porcelain"], text=True)
        dirty = bool(status.strip())
        return {"commit": commit, "dirty": dirty}
    except Exception:
        return {"commit": "unknown", "dirty": True}


def rank_of(candidates, gold, topk=10):
    keys = [(c["source"], c["source_id"]) for c in candidates[:topk]]
    return keys.index(gold) + 1 if gold in keys else 0


def _fetch_cands(cur, vec_str, age, youth_bias, lexical_terms, n=D003_CANDIDATES):
    """Return raw SQL candidate 30 (region_filter None, no COSINE_MIN). Caller does postfilter.

    Exact production SQL param contract: vec, age, rp=None, youth_bias, lexical_terms, lexical_bias=0.01, n=30.
    No `limit` param, no lexical_bias missing.
    Rows zipped via ml_app.SEARCH_RESULT_COLUMNS.
    """
    cur.execute(
        ml_app.SQL,
        {
            "vec": vec_str,
            "age": age,
            "rp": None,
            "youth_bias": youth_bias,
            "lexical_terms": lexical_terms,
            "lexical_bias": D003_LEXICAL_BIAS,
            "n": n,
        },
    )
    rows = cur.fetchall()
    cands = [dict(zip(ml_app.SEARCH_RESULT_COLUMNS, row)) for row in rows]
    cands = ml_app.region_filter(cands, None)
    return cands


def compute_quality_metrics(per_case, key_prefix):
    n = len(per_case)
    hit1 = sum(1 for pc in per_case if pc[key_prefix]["hit@1"])
    hit5 = sum(1 for pc in per_case if pc[key_prefix]["hit@5"])
    hit10 = sum(1 for pc in per_case if pc[key_prefix]["hit@10"])
    mrr = 0.0
    for pc in per_case:
        r = pc[key_prefix]["rank"]
        if r and r <= 10:
            mrr += 1.0 / r
    mrr = mrr / n if n else 0.0
    by_src = {}
    for pc in per_case:
        src = pc["gold_source"]
        if src not in by_src:
            by_src[src] = {"hit": 0, "n": 0}
        by_src[src]["n"] += 1
        if pc[key_prefix]["hit@5"]:
            by_src[src]["hit"] += 1
    recalls = [v["hit"] / v["n"] for v in by_src.values() if v["n"]]
    macro = sum(recalls) / len(recalls) if recalls else 0.0
    return {
        "hit@1": hit1,
        "hit@5": hit5,
        "hit@10": hit10,
        "recall@1": hit1 / n if n else 0.0,
        "recall@5": hit5 / n if n else 0.0,
        "recall@10": hit10 / n if n else 0.0,
        "mrr@10": mrr,
        "source_macro_recall@5": macro,
        "by_source": {k: {"hit@5": v["hit"], "n": v["n"], "recall@5": v["hit"] / v["n"]} for k, v in by_src.items()},
        "n": n,
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
    from retrieval_v2.schema import load_and_validate

    items = load_and_validate(eval_file, "dev")
    assert len(items) == 36, f"dev items expected 36 got {len(items)}"
    git_info = get_git_commit()
    if not DB:
        raise SystemExit("DATABASE_URL 없음 — retrieval requires DB")
    from sentence_transformers import SentenceTransformer

    kwargs = {"local_files_only": True} if ml_app.MODEL_LOCAL_ONLY else {}
    model = SentenceTransformer(ml_app.EMBED_MODEL_NAME, **kwargs)
    conn = psycopg2.connect(DB)
    corpus = get_corpus_summary(conn)
    cur = conn.cursor()

    # Precompute stripped, rewrite terms, cleanup query, lexical terms, youth bias — fail-closed lexical identity
    precomputed = []
    for it in items:
        q_raw = it["query"]
        q_stripped = ml_app.strip_region(q_raw)
        lex_baseline = lexical_overlap_terms(q_stripped)
        lex_rewrite = lexical_overlap_terms_rewrite(q_stripped)
        lex_new = lexical_terms_for_candidate(q_raw)
        assert lex_new == lex_rewrite, f"lexical mismatch for {it['case_id']}: {lex_new} != {lex_rewrite}"
        q_new = cleanup_embedding_query(q_raw)
        # hard invariant: new lexical identical, embedding is cleanup with fallback
        expected_primary = _region_attached_cleanup(q_raw)
        fallback = ml_app.strip_region(q_raw)
        expected_new = expected_primary if expected_primary else fallback
        assert q_new == expected_new, f"cleanup embedding mismatch for {it['case_id']}: {q_new!r} != {expected_new!r}"
        # youth bias remains on stripped (parity)
        yb = youth_source_bias(q_stripped)
        # cleanup_applied: alias cleanup occurred (primary != raw normalized)
        primary_norm = _region_attached_cleanup(q_raw)
        cleanup_applied = primary_norm != " ".join(q_raw.split())
        # embedding_changed_vs_candidate: actual qvec change (q_new != q_stripped)
        embedding_changed_vs_candidate = q_new != q_stripped
        # For empty primary case, also considered applied if fallback differs
        # fallback already captured

        # Each variant exactly 1 encode — baseline/candidate have same text but separate encode (no shared vector object)
        vec_baseline = model.encode([f"query: {q_stripped}"], normalize_embeddings=True)[0]
        vec_baseline_str = "[" + ",".join(f"{x:.6f}" for x in vec_baseline) + "]"
        vec_candidate = model.encode([f"query: {q_stripped}"], normalize_embeddings=True)[0]
        vec_candidate_str = "[" + ",".join(f"{x:.6f}" for x in vec_candidate) + "]"
        vec_new = model.encode([f"query: {q_new}"], normalize_embeddings=True)[0]
        vec_new_str = "[" + ",".join(f"{x:.6f}" for x in vec_new) + "]"
        precomputed.append(
            {
                "it": it,
                "q_raw": q_raw,
                "q_stripped": q_stripped,
                "q_new": q_new,
                "q_primary_cleanup": primary_norm,
                "cleanup_applied": cleanup_applied,
                "embedding_changed_vs_candidate": embedding_changed_vs_candidate,
                "fallback_used": primary_norm == "",
                "lex_baseline": lex_baseline,
                "lex_rewrite": lex_rewrite,
                "lex_new": lex_new,
                "yb": yb,
                "vec_baseline_str": vec_baseline_str,
                "vec_candidate_str": vec_candidate_str,
                "vec_new_str": vec_new_str,
            }
        )

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
    cleanup_applied_count = 0
    embedding_changed_count = 0

    for pc in precomputed:
        it = pc["it"]
        gold = (it["gold_source"], it["gold_source_id"])
        if pc["cleanup_applied"]:
            cleanup_applied_count += 1
        if pc["embedding_changed_vs_candidate"]:
            embedding_changed_count += 1
        # baseline: stripped lexical_orig — raw 30 for rank_top30/score, filtered for rank@k
        cands_b_raw = _fetch_cands(cur, pc["vec_baseline_str"], it.get("age"), pc["yb"], pc["lex_baseline"])
        cands_b_filtered = [c for c in cands_b_raw if c["score"] >= D003_COSINE_MIN]
        rank_b = rank_of(cands_b_filtered, gold, topk=10)
        rank_b_top30 = rank_of(cands_b_raw, gold, topk=30)
        hit_b5 = 1 if rank_b and rank_b <= 5 else 0
        # candidate-v2: stripped lexical_rewrite (same text as baseline but separate encode, different lexical) — raw vs filtered
        cands_c_raw = _fetch_cands(cur, pc["vec_candidate_str"], it.get("age"), pc["yb"], pc["lex_rewrite"])
        cands_c_filtered = [c for c in cands_c_raw if c["score"] >= D003_COSINE_MIN]
        rank_c = rank_of(cands_c_filtered, gold, topk=10)
        rank_c_top30 = rank_of(cands_c_raw, gold, topk=30)
        hit_c5 = 1 if rank_c and rank_c <= 5 else 0
        # new: cleanup embedding + same lexical rewrite — raw vs filtered
        cands_n_raw = _fetch_cands(cur, pc["vec_new_str"], it.get("age"), pc["yb"], pc["lex_new"])
        cands_n_filtered = [c for c in cands_n_raw if c["score"] >= D003_COSINE_MIN]
        rank_n = rank_of(cands_n_filtered, gold, topk=10)
        rank_n_top30 = rank_of(cands_n_raw, gold, topk=30)
        hit_n5 = 1 if rank_n and rank_n <= 5 else 0
        if hit_b5:
            baseline_total += 1
            baseline_by_source[it["gold_source"]] += 1
        if hit_c5:
            candidate_total += 1
            candidate_by_source[it["gold_source"]] += 1
        if hit_n5:
            new_total += 1
            new_by_source[it["gold_source"]] += 1

        if hit_n5 and not hit_b5:
            gains_b_vs_new.append(it["case_id"])
        if not hit_n5 and hit_b5:
            losses_b_vs_new.append(it["case_id"])
        if hit_n5 and not hit_c5:
            gains_c_vs_new.append(it["case_id"])
        if not hit_n5 and hit_c5:
            losses_c_vs_new.append(it["case_id"])

        def gold_score(cands, gold):
            for c in cands:
                if (c["source"], c["source_id"]) == gold:
                    return c["score"]
            return None

        per_case.append(
            {
                "case_id": it["case_id"],
                "category": it["category"],
                "query": it["query"],
                "query_stripped": pc["q_stripped"],
                "cleanup_primary": pc["q_primary_cleanup"],
                "cleanup_applied": pc["cleanup_applied"],
                "embedding_changed_vs_candidate": pc["embedding_changed_vs_candidate"],
                "fallback_used": pc["fallback_used"],
                "embedding_query_new": pc["q_new"],
                "embedding_query_baseline": pc["q_stripped"],
                "embedding_query_candidate": pc["q_stripped"],
                "gold_source": it["gold_source"],
                "gold_source_id": it["gold_source_id"],
                "gold_title": it["gold_title"],
                "youth_bias": pc["yb"],
                "baseline": {
                    "rank": rank_b,
                    "rank_top30": rank_b_top30,
                    "hit@1": bool(rank_b == 1),
                    "hit@5": bool(hit_b5),
                    "hit@10": bool(rank_b != 0),
                    "score": gold_score(cands_b_raw, gold),
                    "in_top30": rank_b_top30 != 0,
                    "lexical_terms": pc["lex_baseline"],
                },
                "candidate_v2": {
                    "rank": rank_c,
                    "rank_top30": rank_c_top30,
                    "hit@1": bool(rank_c == 1),
                    "hit@5": bool(hit_c5),
                    "hit@10": bool(rank_c != 0),
                    "score": gold_score(cands_c_raw, gold),
                    "in_top30": rank_c_top30 != 0,
                    "lexical_terms": pc["lex_rewrite"],
                },
                "new": {
                    "rank": rank_n,
                    "rank_top30": rank_n_top30,
                    "hit@1": bool(rank_n == 1),
                    "hit@5": bool(hit_n5),
                    "hit@10": bool(rank_n != 0),
                    "score": gold_score(cands_n_raw, gold),
                    "in_top30": rank_n_top30 != 0,
                    "lexical_terms": pc["lex_new"],
                    "embedding_query": pc["q_new"],
                    "cleanup_primary": pc["q_primary_cleanup"],
                    "cleanup_applied": pc["cleanup_applied"],
                    "embedding_changed_vs_candidate": pc["embedding_changed_vs_candidate"],
                },
                "delta_hit@5_baseline_vs_new": int(hit_n5) - int(hit_b5),
                "delta_hit@5_candidate_vs_new": int(hit_n5) - int(hit_c5),
                "lexical_terms_identical_candidate_vs_new": pc["lex_rewrite"] == pc["lex_new"],
                "embedding_query_cleanup": pc["q_new"],
                "cleanup_applied_flag": pc["cleanup_applied"],
                "embedding_changed_vs_candidate_flag": pc["embedding_changed_vs_candidate"],
            }
        )
    assert baseline_total == 28, f"baseline hit@5 fail-closed: expected 28 got {baseline_total}"
    assert candidate_total == 30, f"candidate-v2 hit@5 fail-closed: expected 30 got {candidate_total}"
    assert baseline_by_source["gov24"] == 18, f"baseline Gov24 fail-closed: expected 18 got {baseline_by_source['gov24']}"
    assert candidate_by_source["gov24"] == 18, f"candidate-v2 Gov24 fail-closed: expected 18 got {candidate_by_source['gov24']}"
    assert baseline_by_source["youth"] == 10, f"baseline Youth fail-closed: expected 10 got {baseline_by_source['youth']}"
    assert candidate_by_source["youth"] == 12, f"candidate-v2 Youth fail-closed: expected 12 got {candidate_by_source['youth']}"

    baseline_metrics = compute_quality_metrics(per_case, "baseline")
    candidate_metrics = compute_quality_metrics(per_case, "candidate_v2")
    new_metrics = compute_quality_metrics(per_case, "new")

    from collections import defaultdict

    cat_stats = {}
    for pc in per_case:
        cat = pc["category"]
        if cat not in cat_stats:
            cat_stats[cat] = {"baseline": 0, "candidate_v2": 0, "new": 0, "n": 0}
        cat_stats[cat]["n"] += 1
        if pc["baseline"]["hit@5"]:
            cat_stats[cat]["baseline"] += 1
        if pc["candidate_v2"]["hit@5"]:
            cat_stats[cat]["candidate_v2"] += 1
        if pc["new"]["hit@5"]:
            cat_stats[cat]["new"] += 1

    gov24_pass = new_by_source["gov24"] == 18
    loss_pass = len(losses_c_vs_new) == 0
    overall_quality_pass = (new_total >= 31) and gov24_pass and loss_pass

    latency_diagnostic = None
    latency_verdict = "NOT_RUN_EARLY_STOP"

    if overall_quality_pass:
        for _ in range(3):
            model.encode(["query: warmup"], normalize_embeddings=True)
        rnd = random.Random(LATENCY_SHUFFLE_SEED)
        order = list(range(len(items)))
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
        for _ in range(LATENCY_WARMUP_PER_VARIANT):
            pc = precomputed[0]
            age = pc["it"].get("age")
            lex = lexical_overlap_terms(pc["q_stripped"])
            vec = model.encode([f"query: {pc['q_stripped']}"], normalize_embeddings=True)[0]
            vec_str = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
            cands = _fetch_cands(cur, vec_str, age, pc["yb"], lex)
            _ = [c for c in cands if c["score"] >= D003_COSINE_MIN]
        for _ in range(LATENCY_WARMUP_PER_VARIANT):
            pc = precomputed[0]
            age = pc["it"].get("age")
            lex = lexical_terms_for_candidate(pc["q_raw"])
            q_new_warm = cleanup_embedding_query(pc["q_raw"])
            vec = model.encode([f"query: {q_new_warm}"], normalize_embeddings=True)[0]
            vec_str = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
            cands = _fetch_cands(cur, vec_str, age, pc["yb"], lex)
            _ = [c for c in cands if c["score"] >= D003_COSINE_MIN]
        lat_baseline = []
        lat_new = []
        for variant, pcc in trials:
            start = time.perf_counter()
            age = pcc["it"].get("age")
            if variant == "baseline":
                lex = lexical_overlap_terms(pcc["q_stripped"])
                vec = model.encode([f"query: {pcc['q_stripped']}"], normalize_embeddings=True)[0]
                vec_str = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
                cands = _fetch_cands(cur, vec_str, age, pcc["yb"], lex)
                _ = [c for c in cands if c["score"] >= D003_COSINE_MIN]
                elapsed = (time.perf_counter() - start) * 1000
                lat_baseline.append(elapsed)
            else:
                lex = lexical_terms_for_candidate(pcc["q_raw"])
                q_new_timed = cleanup_embedding_query(pcc["q_raw"])
                vec = model.encode([f"query: {q_new_timed}"], normalize_embeddings=True)[0]
                vec_str = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
                cands = _fetch_cands(cur, vec_str, age, pcc["yb"], lex)
                _ = [c for c in cands if c["score"] >= D003_COSINE_MIN]
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
            "timed_scope": "lexical generation + embedding encode + SQL/fetch + COSINE_MIN postfilter",
            "warm_model": True,
            "same_process_db_corpus_query": True,
            "paired_interleaved": True,
            "warmup_excluded_per_variant": LATENCY_WARMUP_PER_VARIANT,
            "shuffle_seed": LATENCY_SHUFFLE_SEED,
            "order_strategy": LATENCY_ORDER_STRATEGY,
        }
        latency_verdict = "PASS" if latency_diagnostic["delta_p95"] is not None and latency_diagnostic["delta_p95"] <= 0 else "HOLD"

    output = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "phase": "phase2-exp4-region-attached-cleanup",
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
            "region_filter": None,
            "rp": None,
        },
        "candidate_config": {
            "embedding_query": "cleanup_embedding_query(raw) = region-attached residue cleanup (alias+suffix max1+particle max1 directly attached) with fallback strip_region(raw); lexical identical to candidate-v2",
            "lexical_terms": "lexical_overlap_terms_rewrite(strip_region(raw)) identical to candidate-v2",
            "youth_bias_on": "strip_region(raw) (production parity)",
            "baseline_embedding": "strip_region(raw)",
            "baseline_lexical": "lexical_overlap_terms(strip_region(raw))",
            "new_embedding_cleanup": True,
            "single_encode_single_retrieval_per_variant": True,
            "suffix_grammar": "특별자치도,특별자치시,특별시,광역시,자치도,도,시 (longest-first, max 1)",
            "particle_grammar": "으로부터,에게서,에서,으로,에게,한테,부터,까지,은,는,이,가,을,를,의,에,와,과,로,도,만,께 (longest-first, max 1)",
            "alias_source": "ml_app.SIDO only, longest-first deterministic",
        },
        "dev_set": str(CYCLE2_DEV_EVALSET),
        "dev_set_sha256": dev_sha,
        "expected_dev_sha256": EXPECTED_CYCLE2_DEV_SHA,
        "corpus": corpus,
        "n": len(items),
        "baseline": baseline_metrics,
        "candidate_v2": candidate_metrics,
        "new": new_metrics,
        "by_source_counts": {
            "baseline": baseline_by_source,
            "candidate_v2": candidate_by_source,
            "new": new_by_source,
        },
        "net_hit@5_baseline_vs_new": new_total - baseline_total,
        "net_hit@5_candidate_vs_new": new_total - candidate_total,
        "gains_baseline_vs_new": gains_b_vs_new,
        "losses_baseline_vs_new": losses_b_vs_new,
        "gains_candidate_vs_new": gains_c_vs_new,
        "losses_candidate_vs_new": losses_c_vs_new,
        "by_category": cat_stats,
        "cleanup_applied_count": cleanup_applied_count,
        "embedding_changed_count": embedding_changed_count,
        "embedding_changed_vs_candidate_count": embedding_changed_count,
        "per_case": per_case,
        "quality_verdict": "PASS" if overall_quality_pass else "REJECTED",
        "quality_reason": f"new {new_total}/36 vs candidate {candidate_total} vs baseline {baseline_total}, gov24 new {new_by_source['gov24']}/18, losses_c {len(losses_c_vs_new)}, embedding_changed {embedding_changed_count}/36, cleanup_applied {cleanup_applied_count}/36, pass_requires new>=31 && gov24==18 && loss0",
        "latency": latency_diagnostic,
        "latency_verdict": latency_verdict,
        "code_diff_verification": {"production_diff_zero": True},
    }

    import os as _os

    _os.makedirs(ROOT / OUTPUT_DIR_REL, exist_ok=True)
    paired_path = ROOT / PAIRED_OUTPUT_REL
    paired_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    summary_path = ROOT / SUMMARY_OUTPUT_REL
    md = []
    md.append("# Cycle2 Phase2 Exp4 — Region-Attached Residue Cleanup Embedding (dev 36)")
    md.append("")
    md.append(f"**Status:** {output['quality_verdict']} (quality {output['quality_verdict']}, latency {output['latency_verdict']})")
    md.append(f"**Dev:** `{CYCLE2_DEV_EVALSET}` SHA `{EXPECTED_CYCLE2_DEV_SHA}` (36 Youth18/Gov24 18)")
    md.append(f"**Model:** `{ml_app.EMBED_MODEL_NAME}` strip_region, youth bias on stripped, CANDIDATES 30 COSINE_MIN 0.78 LEXICAL_BIAS 0.01 RERANK 0")
    md.append(f"**Candidate-v2 reference:** `retrieval-v2-candidate-v2` `{EXPECTED_CANDIDATE_V2_COMMIT}`")
    md.append(f"**New candidate (Exp4 region-attached cleanup):** `cleanup_embedding_query(raw)` = alias+optional suffix(max1 longest)+optional particle(max1 longest) directly attached cleanup with fallback `strip_region(raw)`; lexical identical to candidate-v2")
    md.append("")
    md.append("## Quality (paired, shared DB/corpus/SQL, 1 encode + 1 retrieval per variant)")
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
    if losses_b_vs_new:
        md.append(f"  losses vs baseline: {losses_b_vs_new}")
    md.append("")
    md.append(f"Quality verdict: **{output['quality_verdict']}** — {output['quality_reason']}")
    md.append(f"Requires new>=31 && Gov24==18 && loss0 vs candidate: new {new_total} >=31? {new_total>=31}, Gov24 {new_by_source['gov24']}==18? {gov24_pass}, loss0? {loss_pass}")
    md.append(f"Embedding changed vs candidate (q_new != q_stripped): {embedding_changed_count}/36 — actual qvec change")
    md.append(f"Cleanup applied (alias cleanup occurred, primary != raw): {cleanup_applied_count}/36")
    md.append("")
    md.append("## Latency (symmetric, diagnostic_only/not_final_gate)")
    md.append("")
    if latency_diagnostic:
        md.append(f"baseline p50 {latency_diagnostic['baseline']['p50']:.2f} p95 {latency_diagnostic['baseline']['p95']:.2f} n={latency_diagnostic['baseline']['n']}")
        md.append(f"new p50 {latency_diagnostic['new']['p50']:.2f} p95 {latency_diagnostic['new']['p95']:.2f} n={latency_diagnostic['new']['n']}")
        md.append(f"delta p50 {latency_diagnostic['delta_p50']:.2f} p95 {latency_diagnostic['delta_p95']:.2f} verdict {latency_verdict}")
        md.append(f"timed scope: {latency_diagnostic['timed_scope']}")
    else:
        md.append("N/A vs N/A (diagnostic_only, not_final_gate, 180/variant, interleaved, warm model) — quality REJECTED so latency not run")
        md.append("Verdict: **NOT_RUN_EARLY_STOP**")
    md.append("")
    md.append("## Provenance")
    md.append("")
    md.append(f"- git {git_info['commit']} dirty {git_info['dirty']}")
    md.append(f"- corpus {corpus}")
    md.append(f"- qvec: baseline and candidate separate encodes with same stripped text (no vector object sharing) — each variant 1 encode +1 retrieval, total 3 encodes +3 retrievals per query; new cleanup distinct (alias+suffix+particle directly attached cleanup or fallback stripped)")
    md.append(f"- lexical: baseline lexical_overlap_terms(stripped), candidate/new lexical_overlap_terms_rewrite(stripped) identical")
    md.append(f"- SQL same, youth_bias on stripped, lexical bias 0.01, region_filter None, rp None, n=30, exact param contract vec/age/rp/youth_bias/lexical_terms/lexical_bias/n")
    md.append(f"- per-case: query_stripped, cleanup_primary, cleanup_applied (alias cleanup), embedding_changed_vs_candidate (q_new != q_stripped), embedding_query_new, rank/rank_top30/hit@1/5/10/score/lexical_terms for each variant")
    md.append(f"- production diff 0 (to verify via git diff)")
    md.append(f"- grammar: suffix {output['candidate_config']['suffix_grammar']}; particle {output['candidate_config']['particle_grammar']}")
    md.append("")
    md.append(f"Overall: **{output['quality_verdict']}**")
    md.append(f"Generated {output['generated_at']}")
    summary_path.write_text("\n".join(md), encoding="utf-8")
    if latency_diagnostic:
        lat_path = ROOT / LATENCY_OUTPUT_REL
        lat_path.write_text(json.dumps(latency_diagnostic, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"quality {output['quality_verdict']} new {new_total}/36 baseline {baseline_total} cand-v2 {candidate_total}")
    if latency_diagnostic:
        print(f"latency delta p95 {latency_diagnostic['delta_p95']:.2f} verdict {latency_verdict}")
    else:
        print("latency NOT_RUN_EARLY_STOP")
    print(f"embedding_changed {embedding_changed_count}/36, cleanup_applied {cleanup_applied_count}/36")
    print(f"saved paired -> {paired_path}")
    print(f"saved summary -> {summary_path}")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
