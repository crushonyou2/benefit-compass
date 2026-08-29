"""Warm paired latency gate — retrieval-v2 candidate-v2 / D-007.

D-007 primary latency gate: candidate p95 <= paired baseline p95 (warm paired same-environment retrieval/search).

Design (mandatory):
- Same process/DB connection/corpus/query set/precomputed qvec.
- Model load and embedding encode are EXCLUDED from timed section; qvec fully precomputed.
- Timed section is variant lexical term generation (lexical_overlap_terms vs lexical_overlap_terms_rewrite)
  through same ml_app.SQL execute+fetch, region_filter(None), COSINE_MIN post-filter.
  Candidate rewrite CPU cost is INCLUDED. age/rp=None, youth bias, lexical_bias=.01,
  CANDIDATES=30, SQL/post-filter identical — only lexical term function differs.
- Warm-up: 36 queries each baseline+candidate once untimed (excluded from samples).
- Timed: 5 rounds x 36 = 180 observations per variant (total 360 samples interleaved).
- Each (case_id,round) baseline/candidate immediately paired interleaved.
  Order per pair: (round+query_index)%2 ==0 => B->C else C->B. All-A-then-B forbidden.
- Round query order is deterministic seed shuffle (seed fixed, recorded).
- time.perf_counter_ns() and latency.summarize(samples, expected_sample_count=180)
- Primary gate unchanged: candidate p95 <= baseline p95.
- Explicit --authorized-latency-gate required BEFORE model/DB load; otherwise fail fast.
- Live preflight: runtime D-003, candidate tag/hash, dev hash, corpus
  (13589 policies / 17609 chunks, gov24 10958/14526 youth 2631/3083) mismatch => fail.
- Output strictly under eval/retrieval-v2/latency/ ; holdout access forbidden.
- Samples contain only case_id/round/order/variant/latency_ms; query/gold/top-k/quality forbidden.
- Benchmark queries are frozen dev 36 only; not used for quality analysis/tuning.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import pathlib
import random
import subprocess
import sys
import time

import os
from dotenv import load_dotenv
import psycopg2

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "ml-service"))
sys.path.insert(0, str(ROOT / "eval"))
import app as ml_app
from retrieval_v2.candidate_lexical_rewrite import lexical_overlap_terms_rewrite
from retrieval_v2.latency import Sample, summarize
from retrieval_v2.provenance import canonical_text_sha256
from source_ranking import lexical_overlap_terms, youth_source_bias

load_dotenv(ROOT / ".env")
DB = os.getenv("DATABASE_URL", "").strip()

EXPECTED_CANDIDATE_COMMIT = "5745cc3144b519da456b21030d0e0752d1d018ae"
EXPECTED_CANDIDATE_TAG = "retrieval-v2-candidate-v2"
EXPECTED_ARTIFACT_COMMIT = "c6c082681b4f2fcd521790e50c5fd46549116307"

EXPECTED_DEV_SHA256 = "e9510203cb26bb9db5598b1cd284398ba226460437a396e72906aa6505aff56e"
DEV_MANIFEST_FILE = ROOT / "eval" / "retrieval-v2" / "dev" / "manifest.json"
DEV_EVALSET_FILE = ROOT / "eval" / "retrieval-v2" / "dev" / "evalset.jsonl"
CANDIDATE_MANIFEST_FILE = ROOT / "eval" / "retrieval-v2" / "candidate" / "manifest.json"

FIXED_OUTPUT_POSIX = "eval/retrieval-v2/latency/latency-candidate-v2.json"
FIXED_OUTPUT = ROOT / FIXED_OUTPUT_POSIX

D003_CANDIDATES = 30
D003_COSINE_MIN = 0.78
D003_LEXICAL_BIAS = 0.01
D003_RERANK = 0
D003_EMBED_MODEL = "intfloat/multilingual-e5-base"

EXPECTED_CORPUS = {
    "total_policies": 13589,
    "total_chunks": 17609,
    "by_source": {
        "gov24": {"policies": 10958, "chunks": 14526},
        "youth": {"policies": 2631, "chunks": 3083},
    },
}

CANDIDATE_BUNDLE_PATHS = [
    "eval/retrieval_v2/candidate_lexical_rewrite.py",
    "eval/retrieval_v2/run_candidate_lexical_rewrite.py",
    "eval/test_candidate_lexical_rewrite.py",
    "eval/retrieval-v2/candidate/manifest.json",
    "eval/retrieval-v2/experiments/lexical-rewrite-v1.json",
]

WARMUP_PER_VARIANT = 36
ROUNDS = 5
EXPECTED_SAMPLE_COUNT = 180
SHUFFLE_SEED = 20260830
ORDER_STRATEGY = "(round+query_index)%2 alternation, deterministic seed shuffle, paired interleaved immediately"


def _assert_d003_contract() -> None:
    assert ml_app.CANDIDATES == D003_CANDIDATES, f"D-003 CANDIDATES mismatch: {ml_app.CANDIDATES} != {D003_CANDIDATES}"
    assert abs(ml_app.COSINE_MIN - D003_COSINE_MIN) < 1e-9, f"D-003 COSINE_MIN mismatch: {ml_app.COSINE_MIN} != {D003_COSINE_MIN}"
    assert abs(ml_app.LEXICAL_OVERLAP_BIAS - D003_LEXICAL_BIAS) < 1e-9, f"D-003 LEXICAL_OVERLAP_BIAS mismatch: {ml_app.LEXICAL_OVERLAP_BIAS} != {D003_LEXICAL_BIAS}"
    assert ml_app.EMBED_MODEL_NAME == D003_EMBED_MODEL, f"D-003 EMBED_MODEL mismatch: {ml_app.EMBED_MODEL_NAME} != {D003_EMBED_MODEL}"
    assert ml_app.RERANK is False, f"D-003 RERANK must be False (0), got {ml_app.RERANK!r} — run with RERANK=0"
    assert D003_RERANK == 0


def ensure_latency_output_path(output: str | pathlib.Path) -> pathlib.Path:
    p = pathlib.Path(output)
    if p.is_absolute():
        raise ValueError(f"latency output must be relative under eval/retrieval-v2/latency/, got absolute {output!r}")
    raw = str(output)
    posix = pathlib.PurePosixPath(raw.replace("\\", "/")).as_posix()
    import posixpath
    norm = posixpath.normpath(posix)
    if ".." in pathlib.PurePosixPath(norm).parts:
        raise ValueError(f"latency output must not contain .. traversal, got {output!r}")
    if not posix.startswith("eval/retrieval-v2/latency/"):
        raise ValueError(f"latency output must be under eval/retrieval-v2/latency/, got {output!r} -> {norm!r}")
    if not norm.startswith("eval/retrieval-v2/latency/"):
        raise ValueError(f"latency output must be under eval/retrieval-v2/latency/, got {output!r}")
    # forbid canonical/holdout namespaces
    if "canonical" in posix:
        raise ValueError(f"refusing to write latency output to canonical path: {output!r}")
    if "holdout" in posix:
        raise ValueError(f"refusing to write latency output to holdout path: {output!r}")
    return pathlib.Path(output)


def _validate_candidate_pin(
    candidate_manifest_path: pathlib.Path = CANDIDATE_MANIFEST_FILE,
    expected_artifact_commit: str = EXPECTED_ARTIFACT_COMMIT,
    expected_candidate_commit: str = EXPECTED_CANDIDATE_COMMIT,
    expected_tag: str = EXPECTED_CANDIDATE_TAG,
) -> dict:
    cand_manifest = json.loads(candidate_manifest_path.read_text(encoding="utf-8"))
    if not cand_manifest.get("candidate_frozen"):
        raise SystemExit(f"candidate manifest not frozen: {candidate_manifest_path}")
    prov = cand_manifest.get("artifact_provenance", {})
    art_commit = prov.get("git_commit")
    art_dirty = prov.get("git_dirty")
    if art_commit != expected_artifact_commit:
        raise SystemExit(f"candidate artifact_provenance.git_commit mismatch: {art_commit!r} != expected {expected_artifact_commit!r}")
    if art_dirty is not False:
        raise SystemExit(f"candidate artifact_provenance.git_dirty must be false, got {art_dirty!r}")
    try:
        tag_commit = subprocess.check_output(["git", "rev-parse", f"{expected_tag}^{{commit}}"], cwd=str(ROOT), stderr=subprocess.DEVNULL).decode().strip()
    except Exception as e:
        raise SystemExit(f"cannot resolve tag {expected_tag}: {e}")
    if tag_commit != expected_candidate_commit:
        raise SystemExit(f"candidate tag {expected_tag} -> {tag_commit} != expected {expected_candidate_commit}")
    for key, rel in [("candidate_module", cand_manifest.get("candidate_module")), ("runner", cand_manifest.get("runner")), ("unit_test", cand_manifest.get("unit_test")), ("dev_result", cand_manifest.get("dev_result"))]:
        if not rel:
            continue
        cur_hash = canonical_text_sha256(ROOT / rel)
        exp_hash = cand_manifest.get("sha256", {}).get(key)
        if exp_hash and cur_hash != exp_hash:
            raise SystemExit(f"candidate bundle hash mismatch for {key} ({rel}): actual {cur_hash} != manifest {exp_hash}")
    try:
        subprocess.check_call(["git", "diff", "--quiet", expected_tag, "--"] + CANDIDATE_BUNDLE_PATHS, cwd=str(ROOT))
    except subprocess.CalledProcessError:
        raise SystemExit(f"candidate bundle files have diverged from tag {expected_tag}")
    # also verify dev_sha256 pinned in candidate manifest
    dev_sha = cand_manifest.get("dev_sha256")
    if dev_sha != EXPECTED_DEV_SHA256:
        raise SystemExit(f"candidate manifest dev_sha256 mismatch: {dev_sha!r} != {EXPECTED_DEV_SHA256!r}")
    return cand_manifest


def _validate_dev_pin(
    dev_manifest_path: pathlib.Path = DEV_MANIFEST_FILE,
    dev_evalset_path: pathlib.Path = DEV_EVALSET_FILE,
    expected_sha: str = EXPECTED_DEV_SHA256,
) -> dict:
    if not dev_manifest_path.exists():
        raise SystemExit(f"dev manifest missing: {dev_manifest_path}")
    m = json.loads(dev_manifest_path.read_text(encoding="utf-8"))
    if m.get("role") != "dev":
        raise SystemExit(f"dev manifest role must be 'dev', got {m.get('role')!r}")
    if m.get("cases") != 36:
        raise SystemExit(f"dev manifest cases must be 36, got {m.get('cases')!r}")
    manifest_sha = m.get("sha256")
    if manifest_sha != expected_sha:
        raise SystemExit(f"dev manifest sha256 mismatch: {manifest_sha!r} != expected {expected_sha!r}")
    if not dev_evalset_path.exists():
        raise SystemExit(f"dev evalset missing: {dev_evalset_path}")
    actual_sha = canonical_text_sha256(dev_evalset_path)
    if actual_sha != expected_sha:
        raise SystemExit(f"dev evalset LF hash mismatch: actual {actual_sha} != expected {expected_sha} (file {dev_evalset_path})")
    # also verify eval_file field matches
    eval_file_field = m.get("eval_file")
    if eval_file_field and pathlib.PurePosixPath(eval_file_field).as_posix() != pathlib.PurePosixPath("eval/retrieval-v2/dev/evalset.jsonl").as_posix():
        raise SystemExit(f"dev manifest eval_file must be eval/retrieval-v2/dev/evalset.jsonl, got {eval_file_field!r}")
    return m


def get_corpus_summary(conn) -> dict:
    try:
        cur = conn.cursor()
        cur.execute("SELECT source, count(*) FROM policy GROUP BY source")
        by_src = dict(cur.fetchall())
        cur.execute("SELECT count(*) FROM policy")
        total_policies = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM policy_chunk")
        total_chunks = cur.fetchone()[0]
        cur.execute("SELECT p.source, count(*) FROM policy_chunk c JOIN policy p ON p.id=c.policy_id GROUP BY p.source")
        chunk_by = dict(cur.fetchall())
        cur.close()
        return {
            "total_policies": total_policies,
            "total_chunks": total_chunks,
            "by_source": {
                "gov24": {"policies": by_src.get("gov24", 0), "chunks": chunk_by.get("gov24", 0)},
                "youth": {"policies": by_src.get("youth", 0), "chunks": chunk_by.get("youth", 0)},
            },
        }
    except Exception:
        return {"total_policies": None, "total_chunks": None, "by_source": {}}


def assert_corpus_preflight(corpus: dict) -> None:
    if corpus.get("total_policies") != EXPECTED_CORPUS["total_policies"]:
        raise SystemExit(f"corpus total_policies mismatch: got {corpus.get('total_policies')} != expected {EXPECTED_CORPUS['total_policies']}")
    if corpus.get("total_chunks") != EXPECTED_CORPUS["total_chunks"]:
        raise SystemExit(f"corpus total_chunks mismatch: got {corpus.get('total_chunks')} != expected {EXPECTED_CORPUS['total_chunks']}")
    for src in ("gov24", "youth"):
        exp = EXPECTED_CORPUS["by_source"][src]
        got = corpus.get("by_source", {}).get(src, {})
        if got.get("policies") != exp["policies"] or got.get("chunks") != exp["chunks"]:
            raise SystemExit(f"corpus {src} mismatch: got {got} != expected {exp}")


def get_git_commit() -> dict:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(ROOT), stderr=subprocess.DEVNULL).decode().strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=str(ROOT), stderr=subprocess.DEVNULL).decode().strip())
        return {"commit": commit, "dirty": dirty}
    except Exception:
        return {"commit": "unknown", "dirty": None}


def parse_args():
    p = argparse.ArgumentParser(description="Warm paired latency gate — candidate-v2 D-007")
    p.add_argument("--authorized-latency-gate", action="store_true", help="explicit authorization for latency gate (required before DB/model load)")
    p.add_argument("--output", type=pathlib.Path, default=pathlib.Path(FIXED_OUTPUT_POSIX), help="output under eval/retrieval-v2/latency/")
    p.add_argument("--expected-candidate-commit", type=str, default=EXPECTED_CANDIDATE_COMMIT)
    p.add_argument("--expected-candidate-tag", type=str, default=EXPECTED_CANDIDATE_TAG)
    return p.parse_args()


def main() -> None:
    args = parse_args()

    # 1. authorization guard BEFORE any DB/model load
    if not args.authorized_latency_gate:
        raise SystemExit("Missing --authorized-latency-gate: warm paired latency gate requires explicit authorization before model/DB load")

    # 2. output namespace guard
    ensure_latency_output_path(args.output)
    ensure_latency_output_path(FIXED_OUTPUT_POSIX)
    if pathlib.PurePosixPath(str(args.output).replace("\\", "/")).as_posix() != pathlib.PurePosixPath(FIXED_OUTPUT_POSIX).as_posix():
        raise SystemExit(f"output must be exactly {FIXED_OUTPUT_POSIX!r}, got {str(args.output)!r}")

    # 3. fail-fast D-003 runtime contract
    _assert_d003_contract()

    # 4. candidate pin (before heavy work)
    cand_manifest = _validate_candidate_pin(
        CANDIDATE_MANIFEST_FILE,
        expected_artifact_commit=EXPECTED_ARTIFACT_COMMIT,
        expected_candidate_commit=args.expected_candidate_commit,
        expected_tag=args.expected_candidate_tag,
    )

    # 5. dev manifest + evalset LF hash pin
    dev_manifest = _validate_dev_pin(DEV_MANIFEST_FILE, DEV_EVALSET_FILE, expected_sha=EXPECTED_DEV_SHA256)

    # 6. load model (warm) — excluded from timed section
    from sentence_transformers import SentenceTransformer
    kwargs = {"local_files_only": True} if ml_app.MODEL_LOCAL_ONLY else {}
    model = SentenceTransformer(ml_app.EMBED_MODEL_NAME, **kwargs)

    # 7. DB connection — single connection enforced
    if not DB:
        raise SystemExit("DATABASE_URL missing")
    conn = psycopg2.connect(DB)
    corpus = get_corpus_summary(conn)
    assert_corpus_preflight(corpus)

    # 8. load dev queries (benchmark queries only, not for quality analysis)
    items: list[dict] = []
    with DEV_EVALSET_FILE.open(encoding="utf-8") as f:
        for line in f:
            line=line.strip()
            if not line:
                continue
            obj=json.loads(line)
            items.append(obj)
    if len(items) != 36:
        raise SystemExit(f"dev evalset must have 36 cases, got {len(items)}")
    # verify all have case_id
    for it in items:
        if "case_id" not in it or "query" not in it:
            raise SystemExit(f"dev item missing case_id/query: {it}")

    # 9. precompute qvec for each case — embedding excluded from timed section
    vec_by_case: dict[str, str] = {}
    query_by_case: dict[str, str] = {}
    for it in items:
        case_id = it["case_id"]
        q_raw = it["query"]
        q = ml_app.strip_region(q_raw)
        query_by_case[case_id] = q
        qvec = model.encode([f"query: {q}"], normalize_embeddings=True)[0]
        vec_str = "[" + ",".join(f"{x:.6f}" for x in qvec) + "]"
        vec_by_case[case_id] = vec_str

    # Single cursor for entire run — same DB connection/corpus
    cur = conn.cursor()

    # 10. warm-up: 36 queries each baseline+candidate once untimed (excluded)
    for it in items:
        case_id = it["case_id"]
        q = query_by_case[case_id]
        vec_str = vec_by_case[case_id]
        # baseline warm-up
        b_terms = lexical_overlap_terms(q)
        b_youth = youth_source_bias(q)
        cur.execute(ml_app.SQL, {
            "vec": vec_str,
            "age": None,
            "rp": None,
            "youth_bias": b_youth,
            "lexical_terms": b_terms,
            "lexical_bias": D003_LEXICAL_BIAS,
            "n": D003_CANDIDATES,
        })
        rows = cur.fetchall()
        cands = [dict(zip(ml_app.SEARCH_RESULT_COLUMNS, row)) for row in rows]
        cands = ml_app.region_filter(cands, None)
        cands = [c for c in cands if c["score"] >= D003_COSINE_MIN]
        # candidate warm-up
        c_terms = lexical_overlap_terms_rewrite(q)
        c_youth = youth_source_bias(q)
        cur.execute(ml_app.SQL, {
            "vec": vec_str,
            "age": None,
            "rp": None,
            "youth_bias": c_youth,
            "lexical_terms": c_terms,
            "lexical_bias": D003_LEXICAL_BIAS,
            "n": D003_CANDIDATES,
        })
        rows = cur.fetchall()
        cands = [dict(zip(ml_app.SEARCH_RESULT_COLUMNS, row)) for row in rows]
        cands = ml_app.region_filter(cands, None)
        cands = [c for c in cands if c["score"] >= D003_COSINE_MIN]

    # 11. timed: 5 rounds x 36 = 180 per variant, paired interleaved
    samples: list[Sample] = []
    raw_samples: list[dict] = []  # for JSON output with order
    # deterministic shuffle per round using seed
    for rnd in range(ROUNDS):
        # deterministic shuffle: fresh Random with seed + rnd for reproducibility
        shuffled = list(items)
        rng = random.Random(SHUFFLE_SEED + rnd)
        rng.shuffle(shuffled)
        for q_idx, it in enumerate(shuffled):
            case_id = it["case_id"]
            q = query_by_case[case_id]
            vec_str = vec_by_case[case_id]
            # decide order for this pair
            baseline_first = ((rnd + q_idx) % 2 == 0)
            if baseline_first:
                order_variants = [
                    ("baseline", lexical_overlap_terms),
                    ("candidate", lexical_overlap_terms_rewrite),
                ]
            else:
                order_variants = [
                    ("candidate", lexical_overlap_terms_rewrite),
                    ("baseline", lexical_overlap_terms),
                ]
            # Ensure immediate pairing: baseline and candidate for same (case_id,round) are consecutive
            pair_start = len(samples)
            for order_pos, (variant, term_fn) in enumerate(order_variants, start=1):
                t0 = time.perf_counter_ns()
                # --- timed section start: lexical term generation ---
                lexical_terms = term_fn(q)
                youth_bias = youth_source_bias(q)
                cur.execute(ml_app.SQL, {
                    "vec": vec_str,
                    "age": None,
                    "rp": None,
                    "youth_bias": youth_bias,
                    "lexical_terms": lexical_terms,
                    "lexical_bias": D003_LEXICAL_BIAS,
                    "n": D003_CANDIDATES,
                })
                rows = cur.fetchall()
                cands = [dict(zip(ml_app.SEARCH_RESULT_COLUMNS, row)) for row in rows]
                cands = ml_app.region_filter(cands, None)
                cands = [c for c in cands if c["score"] >= D003_COSINE_MIN]
                # --- timed section end ---
                t1 = time.perf_counter_ns()
                latency_ms = (t1 - t0) / 1_000_000.0
                # record for summarize
                samples.append(Sample(query_id=case_id, round=rnd, variant=variant, latency_ms=latency_ms))
                # raw for output (with order)
                raw_samples.append({
                    "case_id": case_id,
                    "round": rnd,
                    "order": order_pos,
                    "variant": variant,
                    "latency_ms": round(float(latency_ms), 3),
                })
            # verify pairing invariant immediately: the two samples just added share same (case_id,round)
            assert samples[pair_start].query_id == samples[pair_start + 1].query_id == case_id
            assert samples[pair_start].round == samples[pair_start + 1].round == rnd
            assert {samples[pair_start].variant, samples[pair_start + 1].variant} == {"baseline", "candidate"}

    cur.close()
    conn.close()

    # 12. summarize via latency.summarize (validates pairing/interleaving/count)
    summary = summarize(samples, expected_sample_count=EXPECTED_SAMPLE_COUNT)

    # also verify not all baseline then all candidate (interleaving check already in summarize, but extra explicit)
    half = len(samples) // 2
    # if all baseline then all candidate, then samples[0:half] would be all same variant
    # Our pairing forbids that; the summarize check for pair at i/i+1 already covers it.
    # Extra safety: ensure not first 180 all baseline
    first_half_variants = {s.variant for s in samples[:half]}
    if first_half_variants == {"baseline"} or first_half_variants == {"candidate"}:
        raise SystemExit("timed samples are all-A-then-B, not interleaved paired — violates D-007")

    baseline_p95 = summary["baseline"]["p95"]
    candidate_p95 = summary["candidate"]["p95"]
    gate = summary["gate"]
    delta_p95 = summary["delta_p95"]

    git_info = get_git_commit()

    # For evaluator provenance: current harness file hash via canonical_text_sha256 if available
    try:
        harness_sha = canonical_text_sha256(ROOT / "eval" / "retrieval_v2" / "run_latency_candidate_gate.py")
    except Exception:
        harness_sha = "unknown"

    # Build output — strictly in eval/retrieval-v2/latency/, no holdout, no query/gold leakage
    # raw_samples already sanitized: only case_id/round/order/variant/latency_ms
    # Ensure no forbidden fields leak
    for s in raw_samples:
        if any(k in s for k in ("query", "gold", "title", "source_id", "gold_source", "gold_title", "top_k", "rank", "hit", "score")):
            raise SystemExit(f"sample contains forbidden field: {s}")

    output = {
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "contract": "D-007",
        "production_contract": {
            "candidates": D003_CANDIDATES,
            "cosine_min": D003_COSINE_MIN,
            "lexical_bias": D003_LEXICAL_BIAS,
            "rerank": D003_RERANK,
            "embed_model": D003_EMBED_MODEL,
            "strip_region": True,
            "expired_exclusion": True,
            "youth_intent_bias": True,
            "gov24_org_suppression": True,
            "lexical_terms_baseline": "lexical_overlap_terms",
            "lexical_terms_candidate": "lexical_overlap_terms_rewrite",
            "request_region": None,
            "age": None,
            "rp": None,
        },
        "candidate": {
            "tag": EXPECTED_CANDIDATE_TAG,
            "commit": EXPECTED_CANDIDATE_COMMIT,
            "artifact_commit": EXPECTED_ARTIFACT_COMMIT,
            "manifest": "eval/retrieval-v2/candidate/manifest.json",
            "manifest_sha256": cand_manifest.get("sha256", {}).get("candidate_manifest") or canonical_text_sha256(CANDIDATE_MANIFEST_FILE) if CANDIDATE_MANIFEST_FILE.exists() else None,
        },
        "dev": {
            "manifest": "eval/retrieval-v2/dev/manifest.json",
            "evalset": "eval/retrieval-v2/dev/evalset.jsonl",
            "role": "dev",
            "cases": 36,
            "sha256": EXPECTED_DEV_SHA256,
            "sha256_basis": "utf8_text_lf_normalized",
            "evalset_lf_hash_verified": True,
        },
        "evaluator": {
            "harness": "eval/retrieval_v2/run_latency_candidate_gate.py",
            "harness_sha256": harness_sha,
            "commit": git_info["commit"],
            "dirty": git_info["dirty"],
            "tag": "retrieval-v2-latency-evaluator-v2",
        },
        "corpus": corpus,
        "timed_scope": "lexical term generation (lexical_overlap_terms vs lexical_overlap_terms_rewrite) through same SQL execute+fetch, region_filter(None), COSINE_MIN post-filter; model load and embedding encode excluded; qvec precomputed; youth_bias/lexical_bias=.01/CANDIDATES=30/SQL/post-filter identical",
        "benchmark_queries": {
            "source": "frozen dev 36",
            "role": "dev",
            "cases": 36,
            "note": "benchmark queries only; not used for quality analysis/tuning",
        },
        "design": {
            "same_process": True,
            "same_db_connection": True,
            "same_corpus": True,
            "same_query_set": True,
            "precomputed_qvec": True,
            "model_load_excluded": True,
            "embedding_encode_excluded": True,
            "timed_section": "variant lexical term generation through SQL execute+fetch, region_filter(None), COSINE_MIN post-filter",
            "warmup_per_variant": WARMUP_PER_VARIANT,
            "warmup_total": WARMUP_PER_VARIANT * 2,
            "rounds": ROUNDS,
            "observations_per_variant": EXPECTED_SAMPLE_COUNT,
            "total_samples": EXPECTED_SAMPLE_COUNT * 2,
            "order_strategy": ORDER_STRATEGY,
            "shuffle_seed": SHUFFLE_SEED,
            "pairing": "immediate (case_id,round) baseline/candidate paired; (round+query_index)%2 alternation B->C/C->B; not all-A-then-B",
            "timer": "time.perf_counter_ns()",
            "summarize": "latency.summarize(samples, expected_sample_count=180)",
        },
        "warmup": WARMUP_PER_VARIANT,
        "rounds": ROUNDS,
        "order_strategy": ORDER_STRATEGY,
        "shuffle_seed": SHUFFLE_SEED,
        "expected_sample_count": EXPECTED_SAMPLE_COUNT,
        "summary": summary,
        "baseline": summary["baseline"],
        "candidate": summary["candidate"],
        "baseline_p50": summary["baseline"]["p50"],
        "baseline_p95": summary["baseline"]["p95"],
        "candidate_p50": summary["candidate"]["p50"],
        "candidate_p95": summary["candidate"]["p95"],
        "count": EXPECTED_SAMPLE_COUNT,
        "delta_p95": delta_p95,
        "gate": gate,
        "samples": raw_samples,
        "latency_retrieval_runs_executed": 1,
        "candidate_tuning_after_final_holdout": False,
        "holdout_accessed": False,
        "output_path": FIXED_OUTPUT_POSIX,
        "notes": "D-007 warm paired same-environment retrieval/search p95: candidate <= paired D-003 baseline; live timing executed exactly once even on failure; candidate/dev tuning after final holdout remains prohibited",
    }

    # ensure output dir
    FIXED_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    # strict fixed path guard
    if pathlib.PurePosixPath(str(args.output).replace("\\", "/")).as_posix() != FIXED_OUTPUT_POSIX:
        raise SystemExit(f"output must be {FIXED_OUTPUT_POSIX!r}")
    FIXED_OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"warm paired latency: baseline p50 {summary['baseline']['p50']:.2f} p95 {summary['baseline']['p95']:.2f} candidate p50 {summary['candidate']['p50']:.2f} p95 {summary['candidate']['p95']:.2f} delta_p95 {delta_p95:.2f} gate {gate} count {EXPECTED_SAMPLE_COUNT} warmup {WARMUP_PER_VARIANT}/variant rounds {ROUNDS} seed {SHUFFLE_SEED}")
    print(f"saved -> {FIXED_OUTPUT_POSIX}")


if __name__ == "__main__":
    main()
