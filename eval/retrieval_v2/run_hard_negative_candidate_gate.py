"""Hard-negative paired safety gate — retrieval-v2 candidate-v2.

D-007 blocking only:
 1. pure-positive gold hit@5 candidate < baseline  -> FAIL
 2. ineligible/excluded top5 intrusion candidate > baseline -> FAIL

No-answer diagnostics are non-blocking, no threshold/abstention logic.
Paired execution: same query strip_region + same embedding vector reused for baseline/candidate.
Ranking difference is ONLY lexical_overlap_terms vs lexical_overlap_terms_rewrite.
All other params identical: age/rp=None, youth_source_bias, ml_app.SQL, CANDIDATES 30, region_filter None, COSINE_MIN .78.

Historical canonical parity: pure 15/21 hit@5, intrusion 0/3 (from eval/canonical_hard_negative_36_production_parity.json)
If live baseline deviates, overall = HOLD_INVALID_BASELINE_PARITY (not PASS).

Input pinned: eval/expansion_api_evalset.jsonl, n=36, pure 21 / ineligible 3 / no_answer 12, LF SHA 2b56dcfd...

Candidate pinned: retrieval-v2-candidate-v2 @ 5745cc3144b519da456b21030d0e0752d1d018ae
Output pinned: eval/retrieval-v2/hard-negative/paired-candidate-v2.json (canonical overwrite forbidden)
"""

from __future__ import annotations

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
from source_ranking import LEXICAL_OVERLAP_BIAS, YOUTH_INTENT_BIAS, YOUTH_INTENT_TERMS, GOV24_INTENT_TERMS, lexical_overlap_terms, youth_source_bias
from retrieval_v2.candidate_lexical_rewrite import lexical_overlap_terms_rewrite
from retrieval_v2.candidate_lexical_rewrite import ADMIN_UNITS, ADMIN_RESIDUE_PARTICLES, RESIDUE_PURE, PARTICLES, MIN_STEM_LEN
from retrieval_v2.hard_negative import hard_negative_gate
from retrieval_v2.provenance import canonical_text_sha256
from retrieval_v2.guard import is_canonical_path

load_dotenv(ROOT / ".env")
DB = os.getenv("DATABASE_URL", "").strip()

EXPECTED_CANDIDATE_COMMIT = "5745cc3144b519da456b21030d0e0752d1d018ae"
EXPECTED_CANDIDATE_TAG = "retrieval-v2-candidate-v2"
EXPECTED_ARTIFACT_COMMIT = "c6c082681b4f2fcd521790e50c5fd46549116307"

D003_CANDIDATES = 30
D003_COSINE_MIN = 0.78
D003_LEXICAL_BIAS = 0.01
D003_RERANK = 0
D003_EMBED_MODEL = "intfloat/multilingual-e5-base"

EXPECTED_INPUT_POSIX = "eval/expansion_api_evalset.jsonl"
EXPECTED_INPUT_FILE = ROOT / "eval" / "expansion_api_evalset.jsonl"
EXPECTED_N = 36
EXPECTED_PURE = 21
EXPECTED_INELIGIBLE = 3
EXPECTED_NO_ANSWER = 12
EXPECTED_LF_SHA256 = "2b56dcfd79b14b91f719a65e3eef836cee5dff9a242277fa4148ada215521da5"

EXPECTED_CORPUS = {
    "total_policies": 13589,
    "total_chunks": 17609,
    "by_source": {
        "gov24": {"policies": 10958, "chunks": 14526},
        "youth": {"policies": 2631, "chunks": 3083},
    },
}

CANONICAL_MANIFEST_FILE = ROOT / "eval" / "canonical_manifest.json"
CANONICAL_HARD_NEGATIVE_FILE = ROOT / "eval" / "canonical_hard_negative_36_production_parity.json"
CANDIDATE_MANIFEST_FILE = ROOT / "eval" / "retrieval-v2" / "candidate" / "manifest.json"

EXPECTED_CANONICAL_HARD_NEGATIVE = "canonical_hard_negative_36_production_parity.json"
HISTORICAL_PURE_HIT5 = 15
HISTORICAL_PURE_N = 21
HISTORICAL_INTRUSION = 0
HISTORICAL_INELIGIBLE_N = 3

FIXED_OUTPUT_POSIX = "eval/retrieval-v2/hard-negative/paired-candidate-v2.json"
FIXED_OUTPUT = ROOT / FIXED_OUTPUT_POSIX

CANDIDATE_BUNDLE_PATHS = [
    "eval/retrieval_v2/candidate_lexical_rewrite.py",
    "eval/retrieval_v2/run_candidate_lexical_rewrite.py",
    "eval/test_candidate_lexical_rewrite.py",
    "eval/retrieval-v2/candidate/manifest.json",
    "eval/retrieval-v2/experiments/lexical-rewrite-v1.json",
]


def _assert_d003_contract() -> None:
    assert ml_app.CANDIDATES == D003_CANDIDATES, f"D-003 CANDIDATES mismatch: {ml_app.CANDIDATES} != {D003_CANDIDATES}"
    assert abs(ml_app.COSINE_MIN - D003_COSINE_MIN) < 1e-9, f"D-003 COSINE_MIN mismatch: {ml_app.COSINE_MIN} != {D003_COSINE_MIN}"
    assert abs(ml_app.LEXICAL_OVERLAP_BIAS - D003_LEXICAL_BIAS) < 1e-9, "D-003 LEXICAL_OVERLAP_BIAS mismatch"
    assert ml_app.EMBED_MODEL_NAME == D003_EMBED_MODEL, f"D-003 EMBED_MODEL mismatch: {ml_app.EMBED_MODEL_NAME!r} != {D003_EMBED_MODEL!r}"
    assert ml_app.RERANK is False, f"D-003 RERANK must be False (0), got {ml_app.RERANK!r} — set RERANK=0 for prod contract"
    assert D003_RERANK == 0


def ensure_hard_negative_output_path(output: str | pathlib.Path) -> pathlib.Path:
    p = pathlib.Path(output)
    if p.is_absolute():
        raise ValueError(f"Hard-negative output must be relative under eval/retrieval-v2/hard-negative/, got absolute {output!r}")
    if is_canonical_path(p):
        raise ValueError(f"refusing to write hard-negative output to canonical path: {output}")
    raw = str(output)
    posix = pathlib.PurePosixPath(raw.replace("\\", "/")).as_posix()
    import posixpath

    norm = posixpath.normpath(posix)
    if ".." in pathlib.PurePosixPath(norm).parts:
        raise ValueError(f"Hard-negative output must not contain .. traversal, got {output!r}")
    if not posix.startswith("eval/retrieval-v2/hard-negative/"):
        raise ValueError(f"Hard-negative output must be under eval/retrieval-v2/hard-negative/, got {output!r} -> {norm!r}")
    if not norm.startswith("eval/retrieval-v2/hard-negative/"):
        raise ValueError(f"Hard-negative output must be under eval/retrieval-v2/hard-negative/, got {output!r}")
    if posix != FIXED_OUTPUT_POSIX:
        raise ValueError(f"Hard-negative output must be exactly {FIXED_OUTPUT_POSIX!r}, got {output!r}")
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
        tag_commit = subprocess.check_output(
            ["git", "rev-parse", f"{expected_tag}^{{commit}}"], cwd=str(ROOT), stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception as e:
        raise SystemExit(f"cannot resolve tag {expected_tag}: {e}")
    if tag_commit != expected_candidate_commit:
        raise SystemExit(f"candidate tag {expected_tag} -> {tag_commit} != expected {expected_candidate_commit}")
    for key, rel in [
        ("candidate_module", cand_manifest.get("candidate_module")),
        ("runner", cand_manifest.get("runner")),
        ("unit_test", cand_manifest.get("unit_test")),
        ("dev_result", cand_manifest.get("dev_result")),
    ]:
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
    return cand_manifest


def _validate_input_pin(path: pathlib.Path = EXPECTED_INPUT_FILE) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"input file not found: {path}")
    if not str(path).replace("\\", "/").endswith(EXPECTED_INPUT_POSIX):
        raise SystemExit(f"input path must be exactly {EXPECTED_INPUT_POSIX!r}, got {path!r}")
    lf_sha = canonical_text_sha256(path)
    if lf_sha != EXPECTED_LF_SHA256:
        raise SystemExit(f"input LF SHA256 mismatch: {lf_sha} != expected {EXPECTED_LF_SHA256}")
    raw_lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(raw_lines) != EXPECTED_N:
        raise SystemExit(f"input n mismatch: got {len(raw_lines)} expected {EXPECTED_N}")
    items: list[dict] = []
    pure = inelig = noans = 0
    for idx, line in enumerate(raw_lines, 1):
        try:
            it = json.loads(line)
        except Exception as e:
            raise SystemExit(f"input line {idx} invalid JSON: {e}")
        q = it.get("query")
        if not isinstance(q, str) or not q.strip():
            raise SystemExit(f"input line {idx} missing query")
        has_gold = bool(it.get("gold_source_id"))
        has_excl = bool(it.get("excluded_source_id"))
        is_noans = bool(it.get("expected_no_results"))
        if has_gold and not has_excl and not is_noans:
            pure += 1
        elif has_excl:
            inelig += 1
        elif is_noans:
            noans += 1
        else:
            raise SystemExit(f"input line {idx} unclassified case: gold={has_gold} excl={has_excl} noans={is_noans}")
        items.append(it)
    if pure != EXPECTED_PURE or inelig != EXPECTED_INELIGIBLE or noans != EXPECTED_NO_ANSWER:
        raise SystemExit(f"input slice mismatch: pure {pure}/21 ineligible {inelig}/3 no_answer {noans}/12")
    return items


def _validate_canonical_pin() -> dict:
    if not CANONICAL_MANIFEST_FILE.exists():
        raise SystemExit(f"canonical manifest not found: {CANONICAL_MANIFEST_FILE}")
    manifest = json.loads(CANONICAL_MANIFEST_FILE.read_text(encoding="utf-8"))
    hard_neg = manifest.get("production_baselines", {}).get("hard_negative")
    if hard_neg != EXPECTED_CANONICAL_HARD_NEGATIVE:
        raise SystemExit(f"canonical_manifest hard_negative mismatch: {hard_neg!r} != {EXPECTED_CANONICAL_HARD_NEGATIVE!r}")
    if not CANONICAL_HARD_NEGATIVE_FILE.exists():
        raise SystemExit(f"canonical hard-negative artifact not found: {CANONICAL_HARD_NEGATIVE_FILE}")
    artifact = json.loads(CANONICAL_HARD_NEGATIVE_FILE.read_text(encoding="utf-8"))
    # verify artifact provenance n and lexical bias etc. not strictly required, but we verify blocking counts
    cases = artifact.get("cases", [])
    if len(cases) != EXPECTED_N:
        raise SystemExit(f"canonical artifact n mismatch: {len(cases)} != {EXPECTED_N}")
    # independently derive historical canonical blocking counts
    pure_cases = [c for c in cases if c.get("gold_source_id") and not c.get("excluded_source_id") and not c.get("expected_no_results")]
    inelig_cases = [c for c in cases if c.get("excluded_source_id")]
    if len(pure_cases) != EXPECTED_PURE or len(inelig_cases) != EXPECTED_INELIGIBLE:
        raise SystemExit(f"canonical artifact slice mismatch: pure {len(pure_cases)} inel {len(inelig_cases)}")
    # gold_rank_top5 hit counting
    pure_hits = sum(1 for c in pure_cases if c.get("gold_rank_top5") is not None and 1 <= c.get("gold_rank_top5") <= 5)
    if pure_hits != HISTORICAL_PURE_HIT5:
        raise SystemExit(f"canonical stored blocking pure hit@5 mismatch: derived {pure_hits}/21 != stored {HISTORICAL_PURE_HIT5}/21")
    intrusions = 0
    for c in inelig_cases:
        excl = (c.get("excluded_source"), c.get("excluded_source_id"))
        top5 = [(t[0], t[1]) for t in c.get("top_k_ids", [])[:5]]
        if excl in top5:
            intrusions += 1
    if intrusions != HISTORICAL_INTRUSION:
        raise SystemExit(f"canonical stored blocking intrusion mismatch: derived {intrusions}/3 != stored {HISTORICAL_INTRUSION}/3")
    return {"manifest": manifest, "artifact": artifact}


def get_corpus_summary(conn) -> dict:
    try:
        cur = conn.cursor()
        cur.execute("SELECT source, count(*) FROM policy GROUP BY source")
        by_src = {row[0]: row[1] for row in cur.fetchall()}
        cur.execute("SELECT count(*) FROM policy")
        total_policies = cur.fetchone()[0]
        cur.execute("SELECT count(*) FROM policy_chunk")
        total_chunks = cur.fetchone()[0]
        cur.execute("SELECT p.source, count(*) FROM policy_chunk c JOIN policy p ON p.id=c.policy_id GROUP BY p.source")
        by_src_chunks = {row[0]: row[1] for row in cur.fetchall()}
        cur.close()
        return {
            "total_policies": total_policies,
            "total_chunks": total_chunks,
            "by_source": {
                "gov24": {"policies": by_src.get("gov24", 0), "chunks": by_src_chunks.get("gov24", 0)},
                "youth": {"policies": by_src.get("youth", 0), "chunks": by_src_chunks.get("youth", 0)},
            },
        }
    except Exception:
        return {"total_policies": None, "total_chunks": None, "by_source": {}}


def assert_corpus_preflight(corpus: dict) -> None:
    if corpus.get("total_policies") != EXPECTED_CORPUS["total_policies"]:
        raise SystemExit(f"corpus total_policies mismatch: {corpus.get('total_policies')} != {EXPECTED_CORPUS['total_policies']}")
    if corpus.get("total_chunks") != EXPECTED_CORPUS["total_chunks"]:
        raise SystemExit(f"corpus total_chunks mismatch: {corpus.get('total_chunks')} != {EXPECTED_CORPUS['total_chunks']}")
    for src in ("gov24", "youth"):
        exp = EXPECTED_CORPUS["by_source"][src]
        got = corpus.get("by_source", {}).get(src, {})
        if got.get("policies") != exp["policies"] or got.get("chunks") != exp["chunks"]:
            raise SystemExit(f"corpus {src} mismatch: got {got} != expected {exp}")


def get_git_commit() -> dict:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(ROOT)).decode().strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=str(ROOT)).decode().strip())
        return {"commit": commit, "dirty": dirty}
    except Exception:
        return {"commit": "unknown", "dirty": None}


def rank_of(candidates, gold: tuple[str, str] | None, topk: int = 5) -> int:
    if gold is None:
        return 0
    keys = [(c["source"], c["source_id"]) for c in candidates[:topk]]
    return keys.index(gold) + 1 if gold in keys else 0


def intrusion_of(candidates, excluded: tuple[str, str] | None, topk: int = 5) -> bool:
    if excluded is None:
        return False
    keys = [(c["source"], c["source_id"]) for c in candidates[:topk]]
    return excluded in keys


def main() -> None:
    ensure_hard_negative_output_path(FIXED_OUTPUT_POSIX)
    _assert_d003_contract()
    cand_manifest = _validate_candidate_pin()
    items = _validate_input_pin()
    canonical_info = _validate_canonical_pin()

    if not DB:
        raise SystemExit("DATABASE_URL 없음")

    from sentence_transformers import SentenceTransformer

    kwargs = {"local_files_only": True} if ml_app.MODEL_LOCAL_ONLY else {}
    model = SentenceTransformer(ml_app.EMBED_MODEL_NAME, **kwargs)

    conn = psycopg2.connect(DB)
    corpus = get_corpus_summary(conn)
    assert_corpus_preflight(corpus)
    cur = conn.cursor()

    per_case: list[dict] = []
    baseline_pure_hits = 0
    candidate_pure_hits = 0
    baseline_intrusions = 0
    candidate_intrusions = 0

    # no-answer diagnostics
    no_answer_baseline_counts: list[int] = []
    no_answer_candidate_counts: list[int] = []
    no_answer_baseline_top1_scores: list[float | None] = []
    no_answer_candidate_top1_scores: list[float | None] = []

    for idx, it in enumerate(items, 1):
        q_raw = it["query"]
        q = ml_app.strip_region(q_raw)
        # single vector reused for both
        qvec = model.encode([f"query: {q}"], normalize_embeddings=True)[0]
        vec_str = "[" + ",".join(f"{x:.6f}" for x in qvec) + "]"
        youth_bias = youth_source_bias(q)
        lex_baseline = lexical_overlap_terms(q)
        lex_candidate = lexical_overlap_terms_rewrite(q)

        # baseline retrieval
        cur.execute(
            ml_app.SQL,
            {
                "vec": vec_str,
                "age": it.get("age"),
                "rp": None,
                "youth_bias": youth_bias,
                "lexical_terms": lex_baseline,
                "lexical_bias": ml_app.LEXICAL_OVERLAP_BIAS,
                "n": ml_app.CANDIDATES,
            },
        )
        cands_b = [dict(zip(ml_app.SEARCH_RESULT_COLUMNS, row)) for row in cur.fetchall()]
        cands_b = ml_app.region_filter(cands_b, None)
        bi_b = [c for c in cands_b if c["score"] >= ml_app.COSINE_MIN]

        # candidate retrieval — same vector, same bias, same n, same filter
        cur.execute(
            ml_app.SQL,
            {
                "vec": vec_str,
                "age": it.get("age"),
                "rp": None,
                "youth_bias": youth_bias,
                "lexical_terms": lex_candidate,
                "lexical_bias": ml_app.LEXICAL_OVERLAP_BIAS,
                "n": ml_app.CANDIDATES,
            },
        )
        cands_c = [dict(zip(ml_app.SEARCH_RESULT_COLUMNS, row)) for row in cur.fetchall()]
        cands_c = ml_app.region_filter(cands_c, None)
        bi_c = [c for c in cands_c if c["score"] >= ml_app.COSINE_MIN]

        # determine case type for blocking
        has_gold = bool(it.get("gold_source_id"))
        has_excl = bool(it.get("excluded_source_id"))
        is_noans = bool(it.get("expected_no_results"))

        # slots for per_case
        baseline_rank = 0
        candidate_rank = 0
        baseline_intrusion: bool | None = False
        candidate_intrusion: bool | None = False
        case_type_label: str

        if has_gold and not has_excl and not is_noans:
            case_type_label = "pure_positive"
            gold = (it.get("gold_source"), it["gold_source_id"])
            baseline_rank = rank_of(bi_b, gold, topk=5)
            candidate_rank = rank_of(bi_c, gold, topk=5)
            # hit if 1..5
            if 1 <= baseline_rank <= 5:
                baseline_pure_hits += 1
            if 1 <= candidate_rank <= 5:
                candidate_pure_hits += 1
            baseline_intrusion = False
            candidate_intrusion = False
        elif has_excl:
            case_type_label = "ineligible"
            excluded = (it.get("excluded_source"), it.get("excluded_source_id"))
            baseline_intrusion = intrusion_of(bi_b, excluded, topk=5)
            candidate_intrusion = intrusion_of(bi_c, excluded, topk=5)
            if baseline_intrusion:
                baseline_intrusions += 1
            if candidate_intrusion:
                candidate_intrusions += 1
            # ranks for excluded not used for gate, but keep as  rank of excluded if present
            baseline_rank = rank_of(bi_b, excluded, topk=5)
            candidate_rank = rank_of(bi_c, excluded, topk=5)
        elif is_noans:
            case_type_label = "no_answer"
            # gate-not-used; record diagnostics only
            baseline_rank = 0
            candidate_rank = 0
            baseline_intrusion = False
            candidate_intrusion = False
            no_answer_baseline_counts.append(len(bi_b))
            no_answer_candidate_counts.append(len(bi_c))
            # top1 score diagnostics (if any)
            b_top1 = float(bi_b[0]["score"]) if bi_b else None
            c_top1 = float(bi_c[0]["score"]) if bi_c else None
            no_answer_baseline_top1_scores.append(b_top1)
            no_answer_candidate_top1_scores.append(c_top1)
        else:
            # should not happen due to input validation, but handle
            case_type_label = "unknown"
            baseline_intrusion = False
            candidate_intrusion = False

        per_case.append(
            {
                "index": idx,
                "case_type": case_type_label,
                "baseline_rank_top5": baseline_rank,
                "candidate_rank_top5": candidate_rank,
                "baseline_intrusion_top5": bool(baseline_intrusion),
                "candidate_intrusion_top5": bool(candidate_intrusion),
            }
        )

    cur.close()
    conn.close()

    gate = hard_negative_gate(
        baseline_pure_hit5=baseline_pure_hits,
        candidate_pure_hit5=candidate_pure_hits,
        baseline_intrusion=baseline_intrusions,
        candidate_intrusion=candidate_intrusions,
    )

    # baseline parity against historical canonical
    baseline_canonical_parity = (
        baseline_pure_hits == HISTORICAL_PURE_HIT5 and baseline_intrusions == HISTORICAL_INTRUSION
    )

    # overall with parity invalid handling
    if not baseline_canonical_parity:
        overall = "HOLD_INVALID_BASELINE_PARITY"
        adoption = "HOLD"
        gate_status = gate["gate"]
    else:
        overall = gate["overall"]
        adoption = gate["adoption"]
        gate_status = gate["gate"]

    git_info = get_git_commit()
    try:
        eval_tag = "retrieval-v2-hard-negative-evaluator-v1"
        eval_commit = subprocess.check_output(
            ["git", "rev-parse", f"{eval_tag}^{{commit}}"], cwd=str(ROOT), stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        eval_tag = "retrieval-v2-hard-negative-evaluator-v1"
        eval_commit = git_info["commit"]

    input_sha = canonical_text_sha256(EXPECTED_INPUT_FILE)
    manifest_sha = canonical_text_sha256(CANONICAL_MANIFEST_FILE)
    artifact_sha = canonical_text_sha256(CANONICAL_HARD_NEGATIVE_FILE)
    candidate_manifest_sha = canonical_text_sha256(CANDIDATE_MANIFEST_FILE)

    # no_answer diagnostics summary (non-blocking)
    def _score_range(scores: list[float | None]) -> dict:
        valid = [s for s in scores if s is not None]
        if not valid:
            return {"min": None, "max": None, "count": len(scores)}
        return {"min": min(valid), "max": max(valid), "count": len(valid)}

    no_answer_diagnostics = {
        "note": "nonblocking diagnostic only — not used for gate or threshold",
        "baseline": {
            "retrieved_counts": no_answer_baseline_counts,
            "top1_score_range": _score_range(no_answer_baseline_top1_scores),
        },
        "candidate": {
            "retrieved_counts": no_answer_candidate_counts,
            "top1_score_range": _score_range(no_answer_candidate_top1_scores),
        },
    }

    output = {
        "role": "hard_negative_candidate_gate",
        "contract": "D-007",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "candidate": {
            "commit": EXPECTED_CANDIDATE_COMMIT,
            "tag": EXPECTED_CANDIDATE_TAG,
            "manifest": "eval/retrieval-v2/candidate/manifest.json",
            "manifest_sha256": candidate_manifest_sha,
            "manifest_sha256_basis": "utf8_text_lf_normalized",
            "module": "eval/retrieval_v2/candidate_lexical_rewrite.py",
            "module_sha256": canonical_text_sha256(ROOT / "eval/retrieval_v2/candidate_lexical_rewrite.py"),
            "config": cand_manifest.get("candidate_config", {}),
        },
        "evaluator": {
            "commit": eval_commit,
            "tag": eval_tag,
            "harness": "eval/retrieval_v2/run_hard_negative_candidate_gate.py",
            "git_commit": git_info["commit"],
            "git_dirty": git_info["dirty"],
        },
        "input": {
            "path": EXPECTED_INPUT_POSIX,
            "lf_sha256": input_sha,
            "sha256_basis": "utf8_text_lf_normalized",
            "n": EXPECTED_N,
            "slices": {
                "pure_positive": EXPECTED_PURE,
                "ineligible": EXPECTED_INELIGIBLE,
                "no_answer": EXPECTED_NO_ANSWER,
            },
        },
        "canonical": {
            "manifest": "eval/canonical_manifest.json",
            "manifest_sha256": manifest_sha,
            "manifest_sha256_basis": "utf8_text_lf_normalized",
            "artifact": "eval/canonical_hard_negative_36_production_parity.json",
            "artifact_sha256": artifact_sha,
            "artifact_sha256_basis": "utf8_text_lf_normalized",
            "historical_blocking": {
                "pure_hit@5": f"{HISTORICAL_PURE_HIT5}/{HISTORICAL_PURE_N}",
                "intrusion_top5": f"{HISTORICAL_INTRUSION}/{HISTORICAL_INELIGIBLE_N}",
            },
            "verified_blocking": {
                "pure_hit@5": HISTORICAL_PURE_HIT5,
                "intrusion_top5": HISTORICAL_INTRUSION,
            },
        },
        "production_contract": {
            "candidate_sql": "ml-service/app.py:SQL",
            "request_region": None,
            "query_preprocessing": "strip_region",
            "expired_policies_excluded": True,
            "candidates": ml_app.CANDIDATES,
            "rerank": 0,
            "bi_encoder_min_score": ml_app.COSINE_MIN,
            "lexical_bias": ml_app.LEXICAL_OVERLAP_BIAS,
            "lexical_terms_baseline": "lexical_overlap_terms",
            "lexical_terms_candidate": "lexical_overlap_terms_rewrite",
            "youth_intent_bias": YOUTH_INTENT_BIAS,
            "youth_intent_terms": list(YOUTH_INTENT_TERMS),
            "gov24_intent_terms": list(GOV24_INTENT_TERMS),
            "embed_model": ml_app.EMBED_MODEL_NAME,
            "note": "paired: same vector reuse; ranking diff only lexical terms; no threshold/abstention logic",
        },
        "corpus": corpus,
        "results": {
            "baseline_pure_hit@5": baseline_pure_hits,
            "candidate_pure_hit@5": candidate_pure_hits,
            "baseline_intrusion_top5": baseline_intrusions,
            "candidate_intrusion_top5": candidate_intrusions,
            "pure_fail": gate["pure_fail"],
            "intrusion_fail": gate["intrusion_fail"],
            "gate": gate_status,
            "overall": overall,
            "adoption": adoption,
            "baseline_canonical_parity": baseline_canonical_parity,
            "hard_negative_gate": gate,
        },
        "baseline_canonical_parity": baseline_canonical_parity,
        "no_answer_diagnostics": no_answer_diagnostics,
        "per_case": per_case,
        "candidate_tuning_after_final_holdout": False,
        "hard_negative_retrieval_runs_executed": 1,
    }

    FIXED_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    FIXED_OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"hard-negative baseline pure {baseline_pure_hits}/21 hit@5 vs candidate {candidate_pure_hits}/21 | "
        f"intrusion baseline {baseline_intrusions}/3 vs candidate {candidate_intrusions}/3 | "
        f"parity {baseline_canonical_parity} gate {gate_status} overall {overall}"
    )
    print(f"saved -> {FIXED_OUTPUT_POSIX}")


if __name__ == "__main__":
    main()
