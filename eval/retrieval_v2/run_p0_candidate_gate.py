"""P0 canonical regression gate — candidate-v2 pinned, production parity.

This harness evaluates the frozen lexical-rewrite-v1 candidate on the two
pinned P0 canonical sets only (no baseline DB retrieval, no tuning):

- Youth:  eval/evalset.jsonl              exactly 60, default gold_source=youth
- Gov24:  eval/expansion_evalset.jsonl    exactly 21, gold_source=gov24

All ranking inputs are production parity (D-003):
  strip_region, intfloat/multilingual-e5-base, ml_app.SQL,
  age, rp=None, youth_source_bias (with Gov24 suppression), candidate
  lexical_overlap_terms_rewrite, lexical bias 0.01, CANDIDATES 30,
  region_filter(None), COSINE_MIN 0.78.
No rank fusion, no cross-encoder, no new threshold, no public region.

Candidate pin: retrieval-v2-candidate-v2 at 5745cc3144b519da456b21030d0e0752d1d018ae
Artifact provenance: c6c082681b4f2fcd521790e50c5fd46549116307 (clean)
Output: eval/retrieval-v2/p0/p0-candidate-v2.json (canonical namespace forbidden)
Per-case output stores no query/gold_title — only case index / source / source_id / rank.

Paths are PINNED to prevent accidental tuning-set use; CLI override for
eval files is intentionally absent.
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
from source_ranking import (
    GOV24_INTENT_TERMS,
    LEXICAL_OVERLAP_BIAS,
    YOUTH_INTENT_BIAS,
    YOUTH_INTENT_TERMS,
    youth_source_bias,
)
from retrieval_v2.candidate_lexical_rewrite import (
    ADMIN_RESIDUE_PARTICLES,
    ADMIN_UNITS,
    MIN_STEM_LEN,
    PARTICLES,
    RESIDUE_PURE,
    lexical_overlap_terms_rewrite,
)
from retrieval_v2.guard import assert_not_canonical, is_canonical_path
from retrieval_v2.metrics import compute_metrics
from retrieval_v2.p0_gate import gov24_gate, p0_gate, youth_gate
from retrieval_v2.provenance import canonical_text_sha256

load_dotenv(ROOT / ".env")
DB = os.getenv("DATABASE_URL", "").strip()

# Pinned candidate identity (must match retrieval-v2-candidate-v2)
EXPECTED_CANDIDATE_COMMIT = "5745cc3144b519da456b21030d0e0752d1d018ae"
EXPECTED_CANDIDATE_TAG = "retrieval-v2-candidate-v2"
EXPECTED_ARTIFACT_COMMIT = "c6c082681b4f2fcd521790e50c5fd46549116307"

# D-003 contract for fail-fast
D003_CANDIDATES = 30
D003_COSINE_MIN = 0.78
D003_LEXICAL_BIAS = 0.01
D003_RERANK = 0
D003_EMBED_MODEL = "intfloat/multilingual-e5-base"

# Pinned P0 canonical inputs — no CLI override
YOUTH_EVAL_FILE = ROOT / "eval" / "evalset.jsonl"
GOV24_EVAL_FILE = ROOT / "eval" / "expansion_evalset.jsonl"
CANONICAL_MANIFEST_FILE = ROOT / "eval" / "canonical_manifest.json"
CANDIDATE_MANIFEST_FILE = ROOT / "eval" / "retrieval-v2" / "candidate" / "manifest.json"

EXPECTED_YOUTH_N = 60
EXPECTED_GOV24_N = 21

# Fixed output — canonical overwrite forbidden
FIXED_OUTPUT = ROOT / "eval" / "retrieval-v2" / "p0" / "p0-candidate-v2.json"
FIXED_OUTPUT_POSIX = "eval/retrieval-v2/p0/p0-candidate-v2.json"

# Candidate bundle paths for diff check
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
    assert abs(ml_app.LEXICAL_OVERLAP_BIAS - D003_LEXICAL_BIAS) < 1e-9, f"D-003 LEXICAL_OVERLAP_BIAS mismatch"
    assert ml_app.EMBED_MODEL_NAME == D003_EMBED_MODEL, f"D-003 EMBED_MODEL mismatch: {ml_app.EMBED_MODEL_NAME!r} != {D003_EMBED_MODEL!r}"
    assert ml_app.RERANK is False, f"D-003 RERANK must be False (0), got {ml_app.RERANK!r} — set RERANK=0 for prod contract"
    assert D003_RERANK == 0


def ensure_p0_output_path(output: str | pathlib.Path) -> pathlib.Path:
    p = pathlib.Path(output)
    if p.is_absolute():
        raise ValueError(f"P0 output must be relative under eval/retrieval-v2/p0/, got absolute {output!r}")
    if is_canonical_path(p):
        raise ValueError(f"refusing to write P0 output to canonical path: {output}")
    raw = str(output)
    posix = pathlib.PurePosixPath(raw.replace("\\", "/")).as_posix()
    import posixpath

    norm = posixpath.normpath(posix)
    if ".." in pathlib.PurePosixPath(norm).parts:
        raise ValueError(f"P0 output must not contain .. traversal, got {output!r}")
    if not posix.startswith("eval/retrieval-v2/p0/"):
        raise ValueError(f"P0 output must be under eval/retrieval-v2/p0/, got {output!r} -> {norm!r}")
    if not norm.startswith("eval/retrieval-v2/p0/"):
        raise ValueError(f"P0 output must be under eval/retrieval-v2/p0/, got {output!r}")
    if posix.startswith("eval/retrieval-v2/holdout"):
        raise ValueError(f"P0 output must not be under holdout namespace: {output!r}")
    if posix.startswith("eval/canonical"):
        raise ValueError(f"P0 output must not be under canonical namespace: {output!r}")
    # enforce exact fixed output for the live gate (guard against accidental path drift)
    if posix != FIXED_OUTPUT_POSIX:
        raise ValueError(f"P0 output must be exactly {FIXED_OUTPUT_POSIX!r}, got {output!r}")
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
        # git diff --quiet pinned bundle check
        subprocess.check_call(["git", "diff", "--quiet", expected_tag, "--"] + CANDIDATE_BUNDLE_PATHS, cwd=str(ROOT))
    except subprocess.CalledProcessError:
        raise SystemExit(f"candidate bundle files have diverged from tag {expected_tag}")
    return cand_manifest


def _load_p0_items(path: pathlib.Path, expected_n: int, default_source: str, label: str) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"P0 eval file not found: {path}")
    raw_lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(raw_lines) != expected_n:
        raise SystemExit(f"P0 {label} count mismatch: got {len(raw_lines)} expected {expected_n} ({path})")
    items: list[dict] = []
    for idx, line in enumerate(raw_lines, 1):
        try:
            it = json.loads(line)
        except Exception as e:
            raise SystemExit(f"P0 {label} line {idx} invalid JSON: {e}")
        q = it.get("query")
        gid = it.get("gold_source_id")
        if not isinstance(q, str) or not q.strip():
            raise SystemExit(f"P0 {label} line {idx} missing query")
        if not isinstance(gid, str) or not gid.strip():
            raise SystemExit(f"P0 {label} line {idx} missing gold_source_id")
        # gold_source: default if missing, otherwise must match expected source for this file
        gs = it.get("gold_source")
        if gs is None or gs == "":
            gs = default_source
        if gs != default_source:
            raise SystemExit(f"P0 {label} line {idx} gold_source {gs!r} != expected {default_source!r}")
        it["gold_source"] = gs
        # preserve only DB-relevant fields; category not required for P0
        items.append(it)
    return items


def rank_of(candidates, gold, topk=10):
    keys = [(c["source"], c["source_id"]) for c in candidates[:topk]]
    return keys.index(gold) + 1 if gold in keys else 0


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


def get_git_commit() -> dict:
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(ROOT)).decode().strip()
        dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=str(ROOT)).decode().strip())
        return {"commit": commit, "dirty": dirty}
    except Exception:
        return {"commit": "unknown", "dirty": None}


def main() -> None:
    # 0. output guard (fixed path)
    ensure_p0_output_path(FIXED_OUTPUT_POSIX)
    # 1. fail-fast D-003
    _assert_d003_contract()
    # 2. candidate pin
    cand_manifest = _validate_candidate_pin()
    # 3. canonical file existence + hash provenance (for sealing)
    youth_sha = canonical_text_sha256(YOUTH_EVAL_FILE)
    gov24_sha = canonical_text_sha256(GOV24_EVAL_FILE)
    manifest_sha = canonical_text_sha256(CANONICAL_MANIFEST_FILE)
    # 4. load pinned P0 sets with exact count guard
    youth_items = _load_p0_items(YOUTH_EVAL_FILE, EXPECTED_YOUTH_N, "youth", "youth")
    gov24_items = _load_p0_items(GOV24_EVAL_FILE, EXPECTED_GOV24_N, "gov24", "gov24")

    if not DB:
        raise SystemExit("DATABASE_URL 없음")

    from sentence_transformers import SentenceTransformer

    kwargs = {"local_files_only": True} if ml_app.MODEL_LOCAL_ONLY else {}
    model = SentenceTransformer(ml_app.EMBED_MODEL_NAME, **kwargs)

    conn = psycopg2.connect(DB)
    corpus = get_corpus_summary(conn)
    cur = conn.cursor()

    # P0 candidate-only retrieval — no baseline DB pass
    youth_ranks: list[int] = []
    gov24_ranks: list[int] = []
    per_case: list[dict] = []

    # Youth 60
    for idx, it in enumerate(youth_items, 1):
        q_raw = it["query"]
        q = ml_app.strip_region(q_raw)
        vec = model.encode([f"query: {q}"], normalize_embeddings=True)[0]
        vec_str = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
        lex_canon = lexical_overlap_terms_rewrite(q)
        yb = youth_source_bias(q)
        cur.execute(
            ml_app.SQL,
            {
                "vec": vec_str,
                "age": it.get("age"),
                "rp": None,
                "youth_bias": yb,
                "lexical_terms": lex_canon,
                "lexical_bias": ml_app.LEXICAL_OVERLAP_BIAS,
                "n": ml_app.CANDIDATES,
            },
        )
        cands = [dict(zip(ml_app.SEARCH_RESULT_COLUMNS, row)) for row in cur.fetchall()]
        cands = ml_app.region_filter(cands, None)
        bi = [c for c in cands if c["score"] >= ml_app.COSINE_MIN]
        gold = (it["gold_source"], it["gold_source_id"])
        r = rank_of(bi, gold, topk=10)
        youth_ranks.append(r)
        per_case.append(
            {
                "case_index": idx,
                "p0_set": "youth",
                "gold_source": it["gold_source"],
                "gold_source_id": it["gold_source_id"],
                "rank": r,
                "hit@1": r == 1,
                "hit@5": 1 <= r <= 5,
                "hit@10": 1 <= r <= 10,
            }
        )

    # Gov24 21
    offset = len(youth_items)
    for idx, it in enumerate(gov24_items, 1):
        q_raw = it["query"]
        q = ml_app.strip_region(q_raw)
        vec = model.encode([f"query: {q}"], normalize_embeddings=True)[0]
        vec_str = "[" + ",".join(f"{x:.6f}" for x in vec) + "]"
        lex_canon = lexical_overlap_terms_rewrite(q)
        yb = youth_source_bias(q)
        cur.execute(
            ml_app.SQL,
            {
                "vec": vec_str,
                "age": it.get("age"),
                "rp": None,
                "youth_bias": yb,
                "lexical_terms": lex_canon,
                "lexical_bias": ml_app.LEXICAL_OVERLAP_BIAS,
                "n": ml_app.CANDIDATES,
            },
        )
        cands = [dict(zip(ml_app.SEARCH_RESULT_COLUMNS, row)) for row in cur.fetchall()]
        cands = ml_app.region_filter(cands, None)
        bi = [c for c in cands if c["score"] >= ml_app.COSINE_MIN]
        gold = (it["gold_source"], it["gold_source_id"])
        r = rank_of(bi, gold, topk=10)
        gov24_ranks.append(r)
        per_case.append(
            {
                "case_index": offset + idx,
                "p0_set": "gov24",
                "gold_source": it["gold_source"],
                "gold_source_id": it["gold_source_id"],
                "rank": r,
                "hit@1": r == 1,
                "hit@5": 1 <= r <= 5,
                "hit@10": 1 <= r <= 10,
            }
        )

    cur.close()
    conn.close()

    # metrics per source candidate only
    all_ranks = youth_ranks + gov24_ranks
    by_source = {"youth": youth_ranks, "gov24": gov24_ranks}
    # compute_metrics expects by_source dict; overall metrics derived from all_ranks + by_source
    metrics_all = compute_metrics(all_ranks, by_source=by_source)
    youth_m = metrics_all["by_source"]["youth"]
    gov24_m = metrics_all["by_source"]["gov24"]

    # P0 gates (D-007) — hit@5 thresholds
    gate_res = p0_gate(by_source)
    youth_gate_str = gate_res["youth"]["gate"]
    gov24_gate_str = gate_res["gov24"]["gate"]
    overall_gate = gate_res["overall"]

    git_info = get_git_commit()
    # evaluator tag/commit is pinned via git describe; fallback to current HEAD
    try:
        eval_tag = "retrieval-v2-p0-evaluator-v1"
        eval_commit = subprocess.check_output(
            ["git", "rev-parse", f"{eval_tag}^{{commit}}"], cwd=str(ROOT), stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        eval_tag = "retrieval-v2-p0-evaluator-v1"
        eval_commit = git_info["commit"]

    output = {
        "role": "p0_candidate_gate",
        "contract": "D-007",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "candidate": {"commit": EXPECTED_CANDIDATE_COMMIT, "tag": EXPECTED_CANDIDATE_TAG},
        "evaluator": {
            "commit": eval_commit,
            "tag": eval_tag,
            "harness": "eval/retrieval_v2/run_p0_candidate_gate.py",
            "git_commit": git_info["commit"],
            "git_dirty": git_info["dirty"],
        },
        "canonical": {
            "manifest": "eval/canonical_manifest.json",
            "manifest_sha256": manifest_sha,
            "manifest_sha256_basis": "utf8_text_lf_normalized",
            "youth_eval": "eval/evalset.jsonl",
            "youth_sha256": youth_sha,
            "youth_sha256_basis": "utf8_text_lf_normalized",
            "youth_n": EXPECTED_YOUTH_N,
            "gov24_eval": "eval/expansion_evalset.jsonl",
            "gov24_sha256": gov24_sha,
            "gov24_sha256_basis": "utf8_text_lf_normalized",
            "gov24_n": EXPECTED_GOV24_N,
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
            "youth_intent_bias": YOUTH_INTENT_BIAS,
            "youth_intent_terms": list(YOUTH_INTENT_TERMS),
            "gov24_intent_terms": list(GOV24_INTENT_TERMS),
            "embed_model": ml_app.EMBED_MODEL_NAME,
            "lexical_terms": "lexical_overlap_terms_rewrite",
            "note": "production parity: strip_region, youth_source_bias, lexical_overlap_terms_rewrite, .01 bias, 30 candidates, region_filter None, COSINE_MIN .78, no rank fusion/cross-encoder/new threshold",
        },
        "candidate_config": {
            "name": "lexical-rewrite-v1",
            "candidate_module": "eval/retrieval_v2/candidate_lexical_rewrite.py",
            "normalization_rule": cand_manifest.get("candidate_config", {}).get("normalization_rule", ""),
            "min_stem_len": MIN_STEM_LEN,
            "particles": PARTICLES,
            "residue_pure": sorted(RESIDUE_PURE),
            "admin_units": ADMIN_UNITS,
            "admin_residue_particles": ADMIN_RESIDUE_PARTICLES,
            "lexical_terms": "lexical_overlap_terms_rewrite",
            "strip_region": "unchanged",
        },
        "corpus": corpus,
        "metrics": {
            "youth": {
                "n": youth_m["n"],
                "hit@1": youth_m["hit@1"],
                "hit@5": youth_m["hit@5"],
                "hit@10": youth_m["hit@10"],
                "recall@1": youth_m["recall@1"],
                "recall@5": youth_m["recall@5"],
                "recall@10": youth_m["recall@10"],
                "mrr@10": youth_m["mrr@10"],
            },
            "gov24": {
                "n": gov24_m["n"],
                "hit@1": gov24_m["hit@1"],
                "hit@5": gov24_m["hit@5"],
                "hit@10": gov24_m["hit@10"],
                "recall@1": gov24_m["recall@1"],
                "recall@5": gov24_m["recall@5"],
                "recall@10": gov24_m["recall@10"],
                "mrr@10": gov24_m["mrr@10"],
            },
            "overall": {
                "n": metrics_all["n"],
                "hit@1": metrics_all["hit@1"],
                "hit@5": metrics_all["hit@5"],
                "hit@10": metrics_all["hit@10"],
                "recall@1": metrics_all["recall@1"],
                "recall@5": metrics_all["recall@5"],
                "recall@10": metrics_all["recall@10"],
                "mrr@10": metrics_all["mrr@10"],
            },
        },
        "p0_gate": {
            "youth": {"hit@5": gate_res["youth"]["hit@5"], "n": 60, "gate": youth_gate_str},
            "gov24": {"hit@5": gate_res["gov24"]["hit@5"], "n": 21, "gate": gov24_gate_str},
            "overall": overall_gate,
        },
        # legacy flat for D sealing convenience
        "youth": {
            "n": youth_m["n"],
            "hit@5": youth_m["hit@5"],
            "recall@1": youth_m["recall@1"],
            "recall@5": youth_m["recall@5"],
            "recall@10": youth_m["recall@10"],
            "mrr@10": youth_m["mrr@10"],
            "gate": youth_gate_str,
        },
        "gov24": {
            "n": gov24_m["n"],
            "hit@5": gov24_m["hit@5"],
            "recall@1": gov24_m["recall@1"],
            "recall@5": gov24_m["recall@5"],
            "recall@10": gov24_m["recall@10"],
            "mrr@10": gov24_m["mrr@10"],
            "gate": gov24_gate_str,
        },
        "overall_gate": overall_gate,
        "per_case": per_case,
        "candidate_tuning_after_final_holdout": False,
        "p0_retrieval_runs_executed": 1,
    }

    FIXED_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    FIXED_OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(
        f"p0 youth {youth_m['hit@5']}/60 R@5 {youth_m['recall@5']:.4f} gate {youth_gate_str} | "
        f"gov24 {gov24_m['hit@5']}/21 R@5 {gov24_m['recall@5']:.4f} gate {gov24_gate_str} | overall {overall_gate}"
    )
    print(f"saved -> {FIXED_OUTPUT_POSIX}")


if __name__ == "__main__":
    main()
