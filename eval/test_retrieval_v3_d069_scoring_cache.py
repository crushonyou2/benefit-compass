"""D-069 pure/synthetic proofs for scoring-phase invariant cache — no protected data/model/DB/network."""
import hashlib
import pathlib
import random
import tempfile

import pytest

import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from retrieval_v3.runner import Runner, load_candidate_plan_or_fail


def _fake_vec(seed):
    rnd = random.Random(seed)
    v = [rnd.uniform(-1, 1) for _ in range(768)]
    norm = (sum(x * x for x in v) ** 0.5) or 1
    return [round(x / norm, 6) for x in v]


def _fake_emb_factory(counter=None):
    def fake_emb(q):
        if counter is not None:
            counter["n"] += 1
        h = hashlib.sha256(q.encode()).digest()
        return _fake_vec(int.from_bytes(h[:4], "little"))
    return fake_emb


def _synthetic_policies(n=8):
    titles = [
        "청년 지원 정책", "주거 지원", "고용 지원 센터",
        "복지 혜택 안내", "문화 지원", "농업 지원",
        "정책 0", "alpha beta",
    ]
    orgs = ["고용노동부", "보건복지부", "서울시", "o", "org"]
    pols = []
    for i in range(n):
        pols.append({
            "id": i + 1,
            "source": "youth" if i % 2 == 0 else "gov24",
            "source_id": f"p{i}",
            "title": titles[i % len(titles)],
            "support_content": f"support {i} alpha",
            "summary": f"summary {i}",
            "keywords": "alpha beta" if i % 3 == 0 else f"kw{i}",
            "add_qualify": "",
            "income_etc": "",
            "apply_method": "",
            "org": orgs[i % len(orgs)],
            "chunks": [{"embedding": _fake_vec(1000 + i), "chunk_index": 0, "id": i}],
        })
    return pols


def _representative_configs(plan):
    by_id = {c["config_id"]: c for c in plan["configs"]}
    # Cover union/hybrid, field-weight, dedup/diversification, exact-boost differences.
    picks = ["candidate-a-01", "candidate-a-02", "candidate-a-03",
             "candidate-a-04", "candidate-a-06", "candidate-a-08",
             "candidate-a-10", "candidate-a-11"]
    return [by_id[c] for c in picks]


def _strip_result(res):
    # Compare full semantics; policy dicts compared by identity-free projection.
    def proj_top(lst, keys):
        return [{k: e.get(k) for k in keys} for e in lst]
    return {
        "qvec": res["qvec"],
        "q_stripped": res["q_stripped"],
        "final": [(e["source"], e["source_id"], e["final_score"]) for e in res["final_top30"]],
        "dense_top": [(e["source"], e["source_id"], e["dense_cosine"]) for e in res["dense_top100"]],
        "dense_filt": [(e["source"], e["source_id"], e["dense_cosine"]) for e in res["dense_filtered"]],
        "sparse_top": [(e["source"], e["source_id"], e["weighted_overlap"]) for e in res["sparse_top100"]],
        "exact": [(e["source"], e["source_id"], e["is_exact_title"], e["is_exact_org"]) for e in res["exact_candidates"]],
        "union": list(res["union_ordered"]),
        "dense_pool": list(res["dense_oracle_pool"]),
        "sparse_pool": list(res["sparse_oracle_pool"]),
        "exact_pool": list(res["exact_oracle_pool"]),
        "union_pool": list(res["union_oracle_pool"]),
    }


def test_d069_cached_equals_uncached_across_representative_configs():
    plan = load_candidate_plan_or_fail()
    cfgs = _representative_configs(plan)
    pols = _synthetic_policies(8)
    runner = Runner(candidate_plan=plan, embedding_fn=_fake_emb_factory())
    queries = ["청년 지원 정책", "주거 지원 alpha", "query 7 content", "alpha beta"]
    for q in queries:
        state = runner._compute_scoring_invariants(q, pols)
        for cfg in cfgs:
            uncached = runner._retrieve_for_query(q, pols, cfg)
            cached = runner._retrieve_for_query(q, pols, cfg, _scoring_state=state)
            assert _strip_result(cached) == _strip_result(uncached), f"mismatch {q} {cfg['config_id']}"
    # Same qvec path: explicit qvec uncached equals cached qvec reuse.
    q = queries[0]
    state = runner._compute_scoring_invariants(q, pols)
    for cfg in cfgs:
        a = runner._retrieve_for_query(q, pols, cfg, qvec=list(state["qvec"]))
        b = runner._retrieve_for_query(q, pols, cfg, _scoring_state=state)
        assert _strip_result(a) == _strip_result(b)


def test_d069_scoring_phase_counts_N_not_18N():
    import retrieval_v3.runner as R
    plan = load_candidate_plan_or_fail()
    pols = _synthetic_policies(6)
    N = 6
    tasks = [{"task_id": f"t{i:03d}", "query": f"query {i} content alpha",
              "golds": [{"source": "youth", "source_id": "p0", "grade": 2}],
              "stratum": "natural_needs", "location_bearing": False} for i in range(N)]
    emb_counter = {"n": 0}
    dense_counter = {"n": 0}
    exact_counter = {"n": 0}
    orig_dense = R.dense_top100
    orig_title = R.is_exact_title
    orig_org = R.is_exact_org

    def counting_dense(qvec, policies):
        dense_counter["n"] += 1
        return orig_dense(qvec, policies)

    def counting_title(q, t):
        exact_counter["n"] += 1
        return orig_title(q, t)

    def counting_org(q, o):
        exact_counter["n"] += 1
        return orig_org(q, o)

    R.dense_top100 = counting_dense
    R.is_exact_title = counting_title
    R.is_exact_org = counting_org
    try:
        with tempfile.TemporaryDirectory() as td:
            audit_log = pathlib.Path(td) / "audit.jsonl"
            out = pathlib.Path(td) / "out.json"
            runner = Runner(candidate_plan=plan, embedding_fn=_fake_emb_factory(emb_counter),
                            db_policy_loader=lambda: pols,
                            protected_set_loader=lambda r, s: tasks,
                            audit_log_path=audit_log)
            res = runner.run_dev_evaluation(tasks=tasks, policies=pols, session_id="d069-count",
                                            set_role="dev", set_sha=None,
                                            audit_log=audit_log, output_path=out, skip_audit=True)
            assert len(res["per_config_metrics"]) == 18
    finally:
        R.dense_top100 = orig_dense
        R.is_exact_title = orig_title
        R.is_exact_org = orig_org
    assert emb_counter["n"] == N, f"scoring embedding must be N={N}, got {emb_counter['n']} (18N={18 * N})"
    assert dense_counter["n"] == N, f"dense invariant must be N={N}, got {dense_counter['n']}"
    # Exact discovery: once per task => N * len(pols) predicate calls per fn (not 18x).
    assert exact_counter["n"] == 2 * N * len(pols), f"exact predicates must be once/task, got {exact_counter['n']}"


def test_d069_cache_task_query_safe_and_blank_fail_closed():
    plan = load_candidate_plan_or_fail()
    pols = _synthetic_policies(6)
    runner = Runner(candidate_plan=plan, embedding_fn=_fake_emb_factory())
    cfg = plan["configs"][0]
    qa, qb = "청년 지원 정책", "주거 지원 alpha"
    state_a = runner._compute_scoring_invariants(qa, pols)
    # Mismatched query must NOT cross-contaminate: falls back to fresh B semantics.
    mixed = runner._retrieve_for_query(qb, pols, cfg, _scoring_state=state_a)
    fresh_b = runner._retrieve_for_query(qb, pols, cfg)
    fresh_a = runner._retrieve_for_query(qa, pols, cfg)
    assert _strip_result(mixed) == _strip_result(fresh_b)
    assert _strip_result(mixed) != _strip_result(fresh_a)
    # Malformed state must fall back fresh, never reuse another task's vectors.
    bad_state = {"query": qb, "q_stripped": "bad", "qvec": [0.0] * 768,
                 "dense_top100": [], "dense_filtered": [], "exact_candidates": []}
    recovered = runner._retrieve_for_query(qb, pols, cfg, _scoring_state=bad_state)
    assert _strip_result(recovered) == _strip_result(fresh_b)
    # Blank queries fail closed on every entry point.
    for bad in ["", "   ", "  \t "]:
        with pytest.raises(ValueError):
            runner._compute_scoring_invariants(bad, pols)
        with pytest.raises(ValueError):
            runner._retrieve_for_query(bad, pols, cfg)
        with pytest.raises(ValueError):
            runner._retrieve_for_query(bad, pols, cfg, _scoring_state=state_a)


def test_d069_timed_latency_path_not_cached():
    import pathlib as _pl
    repo = _pl.Path(__file__).resolve().parents[1]
    src = (repo / "eval" / "retrieval-v3" / "runner.py").read_text(encoding="utf-8")
    # Scoring cache exists and is used in the scoring loop only.
    assert "_compute_scoring_invariants" in src
    assert "_scoring_invariant_cache" in src
    assert "_scoring_state" in src
    # Timed closures remain standalone: no cache identifiers inside _candidate_fn/_baseline_fn segment.
    seg = src[src.index("def _baseline_fn"):src.index("measure_paired_latency(task_ids_sorted")]
    assert "_scoring_state" not in seg
    assert "_scoring_invariant_cache" not in seg
    assert "_compute_scoring_invariants" not in seg
    assert "self._retrieve_for_query(q, retrieval_policies, _cfg)" in seg
    # D-041 evidence contract intact: 18-config loop, warmup 30, full task set.
    assert "warmup_n=30" in src
    assert "measure_paired_latency(task_ids_sorted" in src
    # Runtime: timed candidate calls add standalone embedding calls beyond scoring N.
    plan = load_candidate_plan_or_fail()
    pols = _synthetic_policies(5)
    N = 5
    tasks = [{"task_id": f"t{i:03d}", "query": f"query {i} content",
              "golds": [{"source": "youth", "source_id": "p0", "grade": 2}],
              "stratum": "natural_needs", "location_bearing": False} for i in range(N)]
    from retrieval_v3.runner import D003_BASELINE
    emb_counter = {"n": 0}
    cnt = [0]

    def clock():
        cnt[0] += 1000000
        return cnt[0]

    def d003_fn(tid, query, baseline, evaluation_context=None):
        assert baseline == D003_BASELINE

    with tempfile.TemporaryDirectory() as td:
        audit_log = pathlib.Path(td) / "audit.jsonl"
        out = pathlib.Path(td) / "out.json"
        runner = Runner(candidate_plan=plan, embedding_fn=_fake_emb_factory(emb_counter),
                        db_policy_loader=lambda: pols,
                        protected_set_loader=lambda r, s: tasks,
                        audit_log_path=audit_log, clock_fn=clock,
                        d003_baseline_fn=d003_fn)
        res = runner.run_dev_evaluation(tasks=tasks, policies=pols, session_id="d069-lat",
                                        set_role="dev", set_sha=None,
                                        audit_log=audit_log, output_path=out, skip_audit=True)
        assert len(res["per_config_metrics"]) == 18
        warmup = min(30, N)
        # Scoring N + per-config timed candidate (warmup + N); baseline uses d003 fn (no embedding).
        expected = N + 18 * (warmup + N)
        assert emb_counter["n"] == expected, f"timed path must be standalone: got {emb_counter['n']}, want {expected}"
        # Latency evidence still spans 18 configs with complete samples.
        assert sorted(res["latency_per_config"].keys()) == sorted(f"candidate-a-{i:02d}" for i in range(1, 19)) or len(res.get("latency_per_config", {})) == 18


def test_d069_frozen_six_audit_result_mlservice_mirrors():
    import pathlib as _pl
    import subprocess
    repo = _pl.Path(__file__).resolve().parents[1]
    expected = {
        "docs/RETRIEVAL_V3_PREREG.md": "7842018613d66aa4570f4db2f8ae5a698ceb46757995a6b7e26873177b36160e",
        "eval/retrieval-v3/candidate-plan/candidate-plan-v4.json": "a25d9c482094696ff7a438593979813ac568c91a977a2543a50618ca4f5177d6",
        "eval/retrieval-v3/candidate-plan/safe-action-policy-v1.json": "c512fb5627179697a987b05a2431b8f7e30d1153af2ff6dca37995f6b232a35d",
        "eval/retrieval-v3/candidate-plan/production-exclusion-policy-v2.json": "6fee9ec22d5d3ac153ff19a6b1b5d27ab6a6a43bda11e35821d689f938968fe5",
        "docs/RETRIEVAL_V3_LINK_PROVENANCE_SUPERSESSION_V2.md": "f028ce4697f1a19e8d37e9048f6d7cd07d87c35ad68478d0efa968b7c62a7e71",
        "docs/RETRIEVAL_V3_COST_MEASUREMENT_V1.md": "5891b0bab0621da71499c5c2c6a21a6ac6692bd3ee94d6cb5342adc480958323",
    }
    for rel, sha in expected.items():
        assert hashlib.sha256((repo / rel).read_bytes()).hexdigest() == sha, rel
    assert hashlib.sha256((repo / "eval" / "retrieval-v3" / "audit" / "events.jsonl").read_bytes()).hexdigest() == "90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506"
    assert not (repo / "eval" / "retrieval-v3" / "results" / "v3-candidate-dev-result.json").exists()
    r = subprocess.run(["git", "diff", "5327661445c37191a3fd61db195f3af4d2cf893a", "--", "ml-service/"],
                       capture_output=True, text=True, cwd=str(repo))
    assert r.stdout.strip() == "", "ml-service must stay diff 0"
    for name in ["runner.py", "fusion.py", "dedup.py", "metrics.py", "selection.py", "dense.py",
                 "sparse.py", "exact.py", "normalization.py", "latency.py", "candidate_registry.py",
                 "result_schema.py", "paths.py", "audit.py", "real_adapters.py"]:
        p1, p2 = repo / "eval" / "retrieval-v3" / name, repo / "eval" / "retrieval_v3" / name
        if p1.exists() and p2.exists():
            assert hashlib.sha256(p1.read_bytes()).hexdigest() == hashlib.sha256(p2.read_bytes()).hexdigest(), name
