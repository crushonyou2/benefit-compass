"""Final holdout evaluator harness — candidate-v2 pinned, holdout-only.

This harness is NOT the dev runner. It evaluates the frozen lexical-rewrite-v1
candidate on the **sealed final holdout** only when explicitly authorized.
It never falls back to dev, never writes to canonical or holdout namespaces,
and never performs tuning.

Authorization: --authorized-final-holdout is required before any DB/model load.
Without it the harness fails fast.

Paths:
- --eval-file and --holdout-manifest are required with no default real holdout path.
- --output must be under eval/retrieval-v2/final/ (no holdout/canonical, no traversal).

Validation:
- holdout manifest role==holdout, contract D-007, cases 40 Youth 20 Gov24 20, sha256 pinned to 02eb038..., eval file hash matches.
- candidate manifest candidate_frozen==true and exact candidate tag/commit pin (artifact provenance c6c0826..., freeze 5745cc3...).
- output namespace guard.
- eval_file mismatch with manifest is fatal (allow absolute only if ends with manifest relative).

Ranking:
- baseline/candidate share same q/vector/SQL/params; difference is only lexical terms
  (lexical_overlap_terms vs lexical_overlap_terms_rewrite).
- D-007 metrics: source-macro Recall@5, net hit@5, Youth/Gov24 hit@5,
  secondary R@1/R@10/MRR@10/category/per-case. No P0/hard-negative/latency.
- quality_gate: macro improved, net>=2, no Youth/Gov24 regression, overall pass.

Candidate pin: retrieval-v2-candidate-v2 at 5745cc3144b519da456b21030d0e0752d1d018ae
Artifact provenance: c6c082681b4f2fcd521790e50c5fd46549116307 (clean)
Expected holdout sealed SHA: 02eb03866f8e09b66ea7c3b83856fe939ee0b966350053277aaca3f2d7121eda
Real holdout plaintext is never read in this task; synthetic holdout only for unit tests.
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
from source_ranking import (
    GOV24_INTENT_TERMS,
    LEXICAL_OVERLAP_BIAS,
    YOUTH_INTENT_BIAS,
    YOUTH_INTENT_TERMS,
    lexical_overlap_terms,
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
from retrieval_v2.provenance import canonical_text_sha256
from retrieval_v2.schema import load_and_validate

load_dotenv(ROOT / ".env")
DB = os.getenv("DATABASE_URL", "").strip()

# Pinned candidate identity (must match retrieval-v2-candidate-v2)
EXPECTED_CANDIDATE_COMMIT = "5745cc3144b519da456b21030d0e0752d1d018ae"
EXPECTED_CANDIDATE_TAG = "retrieval-v2-candidate-v2"
EXPECTED_ARTIFACT_COMMIT = "c6c082681b4f2fcd521790e50c5fd46549116307"
EXPECTED_HOLDOUT_SHA256 = "02eb03866f8e09b66ea7c3b83856fe939ee0b966350053277aaca3f2d7121eda"

# D-003 contract for fail-fast
D003_CANDIDATES = 30
D003_COSINE_MIN = 0.78
D003_LEXICAL_BIAS = 0.01
D003_RERANK = 0
D003_EMBED_MODEL = "intfloat/multilingual-e5-base"

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
    assert abs(ml_app.COSINE_MIN - D003_COSINE_MIN) < 1e-9, f"D-003 COSINE_MIN mismatch"
    assert abs(ml_app.LEXICAL_OVERLAP_BIAS - D003_LEXICAL_BIAS) < 1e-9
    assert ml_app.EMBED_MODEL_NAME == D003_EMBED_MODEL
    assert ml_app.RERANK is False, f"D-003 RERANK must be False (0), got {ml_app.RERANK!r} — set RERANK=0 for prod contract"
    assert D003_RERANK == 0


def ensure_final_output_path(output: str | pathlib.Path) -> pathlib.Path:
    p = pathlib.Path(output)
    if p.is_absolute():
        raise ValueError(f"final holdout output must be relative under eval/retrieval-v2/final/, got absolute {output!r}")
    if is_canonical_path(p):
        raise ValueError(f"refusing to write final holdout output to canonical path: {output}")
    raw = str(output)
    posix = pathlib.PurePosixPath(raw.replace("\\", "/")).as_posix()
    import posixpath
    norm = posixpath.normpath(posix)
    if ".." in pathlib.PurePosixPath(norm).parts:
        raise ValueError(f"final output must not contain .. traversal, got {output!r}")
    if not posix.startswith("eval/retrieval-v2/final/"):
        raise ValueError(f"final holdout output must be under eval/retrieval-v2/final/, got {output!r} -> {norm!r}")
    if not norm.startswith("eval/retrieval-v2/final/"):
        raise ValueError(f"final holdout output must be under eval/retrieval-v2/final/, got {output!r}")
    if posix.startswith("eval/retrieval-v2/holdout"):
        raise ValueError(f"final output must not be under holdout namespace: {output!r}")
    if posix.startswith("eval/canonical"):
        raise ValueError(f"final output must not be under canonical namespace: {output!r}")
    return pathlib.Path(output)


def _validate_candidate_pin(candidate_manifest_path: pathlib.Path, expected_artifact_commit: str = EXPECTED_ARTIFACT_COMMIT, expected_candidate_commit: str = EXPECTED_CANDIDATE_COMMIT, expected_tag: str = EXPECTED_CANDIDATE_TAG) -> dict:
    """Validate candidate pin logic for fix #1. Returns manifest dict if ok, else raises."""
    cand_manifest = json.loads(candidate_manifest_path.read_text(encoding="utf-8"))
    if not cand_manifest.get("candidate_frozen"):
        raise SystemExit(f"candidate manifest not frozen: {candidate_manifest_path}")
    # 1. artifact provenance must be clean source commit A
    prov = cand_manifest.get("artifact_provenance", {})
    art_commit = prov.get("git_commit")
    art_dirty = prov.get("git_dirty")
    if art_commit != expected_artifact_commit:
        raise SystemExit(f"candidate artifact_provenance.git_commit mismatch: {art_commit!r} != expected {expected_artifact_commit!r}")
    if art_dirty is not False:
        raise SystemExit(f"candidate artifact_provenance.git_dirty must be false, got {art_dirty!r}")
    # 2. resolve annotated tag and require == freeze commit B
    try:
        tag_commit = subprocess.check_output(["git", "rev-parse", f"{expected_tag}^{{commit}}"], cwd=str(ROOT), stderr=subprocess.DEVNULL).decode().strip()
    except Exception as e:
        raise SystemExit(f"cannot resolve tag {expected_tag}: {e}")
    if tag_commit != expected_candidate_commit:
        raise SystemExit(f"candidate tag {expected_tag} -> {tag_commit} != expected {expected_candidate_commit}")
    # 3. require current candidate bundle hashes match manifest
    for key, rel in [("candidate_module", cand_manifest.get("candidate_module")), ("runner", cand_manifest.get("runner")), ("unit_test", cand_manifest.get("unit_test")), ("dev_result", cand_manifest.get("dev_result"))]:
        if not rel:
            continue
        cur_hash = canonical_text_sha256(ROOT / rel)
        exp_hash = cand_manifest.get("sha256", {}).get(key)
        if exp_hash and cur_hash != exp_hash:
            raise SystemExit(f"candidate bundle hash mismatch for {key} ({rel}): actual {cur_hash} != manifest {exp_hash}")
    # 4. ideally require files unchanged relative to tag (git diff --quiet)
    try:
        # Use git diff --quiet to check bundle paths unchanged vs tag
        subprocess.check_call(["git", "diff", "--quiet", expected_tag, "--"] + CANDIDATE_BUNDLE_PATHS, cwd=str(ROOT))
    except subprocess.CalledProcessError:
        raise SystemExit(f"candidate bundle files have diverged from tag {expected_tag}")
    return cand_manifest


def _validate_holdout_manifest(holdout_manifest_path: pathlib.Path, eval_file: pathlib.Path, expected_sha: str = EXPECTED_HOLDOUT_SHA256, expected_role: str = "holdout") -> dict:
    """Validate holdout manifest for real CLI path. Synthetic tests may call helper with injected expected."""
    hm = json.loads(holdout_manifest_path.read_text(encoding="utf-8"))
    if hm.get("role") != expected_role:
        raise SystemExit(f"holdout manifest role must be '{expected_role}', got {hm.get('role')!r}")
    # contract D-007 is REQUIRED (fix #1)
    if hm.get("contract") != "D-007":
        raise SystemExit(f"holdout manifest contract must be D-007, got {hm.get('contract')!r}")
    # cases 40, Youth 20 Gov24 20 are REQUIRED (fix #1) — synthetic manifests must include them
    cases = hm.get("cases")
    if cases is None:
        cases = hm.get("n") or hm.get("holdout_cases")
    if cases != 40:
        raise SystemExit(f"holdout manifest cases must be 40, got {cases!r}")
    youth = hm.get("youth")
    if youth != 20:
        raise SystemExit(f"holdout manifest youth must be 20, got {youth!r}")
    gov24 = hm.get("gov24")
    if gov24 != 20:
        raise SystemExit(f"holdout manifest gov24 must be 20, got {gov24!r}")
    # sha256 must be exactly expected
    # try multiple keys
    manifest_sha = hm.get("sha256") or hm.get("holdout_sha256") or hm.get("dev_sha256") or hm.get("expected_sha256") or hm.get("expected_holdout_sha256")
    if not manifest_sha:
        for k, v in hm.items():
            if "sha" in k.lower() and isinstance(v, str) and len(v) == 64:
                manifest_sha = v
                break
    if manifest_sha != expected_sha:
        raise SystemExit(f"holdout manifest sha256 mismatch: {manifest_sha!r} != expected {expected_sha!r}")
    # eval file hash must equal manifest SHA
    actual_sha = canonical_text_sha256(eval_file)
    if actual_sha != manifest_sha:
        raise SystemExit(f"holdout eval file hash mismatch: actual {actual_sha} != manifest {manifest_sha} (file {eval_file})")
    # eval_file mismatch fatal handling is done by caller; here we just return
    return hm


def parse_args():
    p = argparse.ArgumentParser(description="Final holdout evaluator harness (candidate-v2 pinned)")
    p.add_argument("--authorized-final-holdout", action="store_true", help="explicit authorization to run final holdout evaluation")
    p.add_argument("--eval-file", type=pathlib.Path, required=True, help="explicit holdout evalset path (no default)")
    p.add_argument("--holdout-manifest", type=pathlib.Path, required=True, help="explicit holdout manifest path (no default)")
    p.add_argument("--candidate-manifest", type=pathlib.Path, default=ROOT / "eval" / "retrieval-v2" / "candidate" / "manifest.json", help="candidate manifest path")
    p.add_argument("--expected-candidate-commit", type=str, default=EXPECTED_CANDIDATE_COMMIT, help="pinned candidate commit for verification")
    p.add_argument("--expected-candidate-tag", type=str, default=EXPECTED_CANDIDATE_TAG, help="pinned candidate tag for verification")
    p.add_argument("--output", type=pathlib.Path, required=True, help="output under eval/retrieval-v2/final/")
    return p.parse_args()


def rank_of(candidates, gold, topk=10):
    keys = [(c["source"], c["source_id"]) for c in candidates[:topk]]
    return keys.index(gold) + 1 if gold in keys else 0


def main():
    args = parse_args()
    # 1. authorization guard BEFORE DB/model
    if not args.authorized_final_holdout:
        raise SystemExit("Missing --authorized-final-holdout: final holdout evaluation requires explicit authorization")

    # 2. output namespace guard
    ensure_final_output_path(args.output)

    # 3. fail-fast D-003
    _assert_d003_contract()

    # 4. candidate pin (fix #1)
    cand_manifest = _validate_candidate_pin(args.candidate_manifest, expected_artifact_commit=EXPECTED_ARTIFACT_COMMIT, expected_candidate_commit=args.expected_candidate_commit, expected_tag=args.expected_candidate_tag)

    # 5. holdout manifest validation (fix #3) — CLI uses real pinned expected
    holdout_manifest = _validate_holdout_manifest(args.holdout_manifest, args.eval_file, expected_sha=EXPECTED_HOLDOUT_SHA256, expected_role="holdout")

    # 6. eval_file mismatch with manifest is fatal (fix #4)
    manifest_eval = holdout_manifest.get("eval_file") or holdout_manifest.get("holdout_eval_file") or holdout_manifest.get("evalset") or holdout_manifest.get("path")
    if manifest_eval:
        manifest_posix = pathlib.PurePosixPath(str(manifest_eval).replace("\\", "/")).as_posix()
        # Normalize supplied eval path
        supplied = pathlib.PurePosixPath(str(args.eval_file).replace("\\", "/")).as_posix()
        supplied_norm = pathlib.PurePosixPath(supplied).as_posix()
        manifest_norm = pathlib.PurePosixPath(manifest_posix).as_posix()
        # Allow absolute materialized/worktree paths only when normalized path ends with manifest's relative eval_file
        if supplied != manifest_norm and supplied_norm != manifest_norm:
            # Check if supplied is absolute and ends with manifest relative
            if pathlib.Path(args.eval_file).is_absolute():
                if not supplied_norm.endswith(manifest_norm):
                    raise SystemExit(f"eval-file mismatch: supplied {args.eval_file!r} does not end with manifest eval_file {manifest_eval!r}")
            else:
                # relative mismatch is fatal
                raise SystemExit(f"eval-file mismatch: supplied {args.eval_file!r} != manifest eval_file {manifest_eval!r}")

    if not DB:
        raise SystemExit("DATABASE_URL 없음")
    items = load_and_validate(args.eval_file, "holdout")
    holdout_sha = canonical_text_sha256(args.eval_file)

    try:
        holdout_freeze_commit = subprocess.check_output(["git", "log", "-1", "--format=%H", "--", str(args.eval_file)], cwd=str(ROOT), stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        holdout_freeze_commit = "unknown"

    from sentence_transformers import SentenceTransformer
    kwargs = {"local_files_only": True} if ml_app.MODEL_LOCAL_ONLY else {}
    model = SentenceTransformer(ml_app.EMBED_MODEL_NAME, **kwargs)

    conn = psycopg2.connect(DB)
    def get_corpus_summary(conn):
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
        lex_cand = lexical_overlap_terms_rewrite(q)
        yb = youth_source_bias(q)

        cur.execute(ml_app.SQL, {
            "vec": vec_str, "age": it.get("age"), "rp": None,
            "youth_bias": yb, "lexical_terms": lex_orig, "lexical_bias": LEXICAL_OVERLAP_BIAS, "n": ml_app.CANDIDATES,
        })
        cands = [dict(zip(ml_app.SEARCH_RESULT_COLUMNS, row)) for row in cur.fetchall()]
        cands = ml_app.region_filter(cands, None)
        bi = [c for c in cands if c["score"] >= ml_app.COSINE_MIN]
        gold = (it["gold_source"], it["gold_source_id"])
        b_rank = rank_of(bi, gold, topk=10)

        cur.execute(ml_app.SQL, {
            "vec": vec_str, "age": it.get("age"), "rp": None,
            "youth_bias": yb, "lexical_terms": lex_cand, "lexical_bias": LEXICAL_OVERLAP_BIAS, "n": ml_app.CANDIDATES,
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
            "case_id": it.get("case_id", f"holdout-{len(per_case)+1}"),
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
            "candidate_lexical_terms": lex_cand,
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

    # D-007 quality_gate (fix #4) — record without treating failure as error
    macro_improved = (candidate_metrics.get("source_macro_recall@5", 0) > baseline_metrics.get("source_macro_recall@5", 0))
    net_ge_2 = net >= 2
    youth_regression = per_source_delta.get("youth", {}).get("regression", False)
    gov24_regression = per_source_delta.get("gov24", {}).get("regression", False)
    no_regression = not youth_regression and not gov24_regression
    quality_pass = macro_improved and net_ge_2 and no_regression
    quality_gate = {
        "macro_improved": macro_improved,
        "net_ge_2": net_ge_2,
        "no_youth_gov24_regression": no_regression,
        "youth_regression": youth_regression,
        "gov24_regression": gov24_regression,
        "overall_quality_pass": quality_pass,
        "note": "D-007 final holdout quality gate: source-macro improved, net>=2, no Youth/Gov24 regression",
    }

    git_commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=str(ROOT), stderr=subprocess.DEVNULL).decode().strip()
    output = {
        "role": "holdout",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "git_commit": git_commit,
        "candidate_commit": EXPECTED_CANDIDATE_COMMIT,
        "candidate_tag": EXPECTED_CANDIDATE_TAG,
        "artifact_commit": EXPECTED_ARTIFACT_COMMIT,
        "model": ml_app.EMBED_MODEL_NAME,
        "production_contract": {
            "candidate_sql": "ml-service/app.py:SQL",
            "query_preprocessing": "strip_region",
            "candidates": ml_app.CANDIDATES,
            "rerank": D003_RERANK,
            "bi_encoder_min_score": ml_app.COSINE_MIN,
            "lexical_bias": LEXICAL_OVERLAP_BIAS,
            "youth_intent_bias": YOUTH_INTENT_BIAS,
            "gov24_org_suppression": True,
        },
        "candidate_config": {
            "name": "lexical-rewrite-v1",
            "particles": PARTICLES,
            "min_stem_len": MIN_STEM_LEN,
            "residue_pure": sorted(RESIDUE_PURE),
            "admin_units": ADMIN_UNITS,
            "admin_residue_particles": ADMIN_RESIDUE_PARTICLES,
            "lexical_terms": "lexical_overlap_terms_rewrite",
        },
        "holdout": {
            "eval_file": str(args.eval_file),
            "holdout_manifest": str(args.holdout_manifest),
            "sha256": holdout_sha,
            "n": len(items),
            "expected_sha256": EXPECTED_HOLDOUT_SHA256,
        },
        "corpus": corpus,
        "baseline": baseline_metrics,
        "candidate_metrics": candidate_metrics,
        "net_hit@5": net,
        "source_macro_recall@5": candidate_metrics.get("source_macro_recall@5"),
        "per_source_delta": per_source_delta,
        "gains": gains,
        "losses": losses,
        "per_case": per_case,
        "quality_gate": quality_gate,
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"holdout n={len(items)} baseline R@5 {baseline_metrics['recall@5']:.4f} candidate R@5 {candidate_metrics['recall@5']:.4f} net {net} gov24 {candidate_metrics['by_source']['gov24']['hit@5']}/{len(by_source_candidate['gov24'])} youth {candidate_metrics['by_source']['youth']['hit@5']}/{len(by_source_candidate['youth'])} quality_pass={quality_pass}")
    print(f"saved -> {args.output}")


if __name__ == "__main__":
    main()
