"""Focused pure/static/mock tests for Candidate A runner — exercises real code paths via injection, no DB/model/network/protected plaintext."""
import hashlib, json, pathlib, tempfile, sys, math, random, os, re, subprocess
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from retrieval_v3.candidate_registry import load_and_validate, validate_data, EXPECTED_SHA
from retrieval_v3.dense import cosine_similarity, dot_product, select_representative_chunk, dense_top100, filter_dense_by_cosine_min
from retrieval_v3.exact import is_exact_title, is_exact_org
from retrieval_v3.normalization import normalize_exact, lexical_overlap_terms, strip_region, youth_source_bias
from retrieval_v3.dedup import dedup_greedy, mmr_select, full_top30_pipeline
from retrieval_v3.fusion import fuse_candidates
from retrieval_v3.sparse import sparse_top100, compute_weighted_lexical_overlap
from retrieval_v3.metrics import success_at_5, mrr_at_10, ndcg_at_5, compute_headline_metrics
from retrieval_v3.selection import select_candidate, candidate_b_gate
from retrieval_v3.latency import measure_paired_latency
from retrieval_v3.audit import append_event, read_and_verify_chain, verify_holdout_access_allowed
from retrieval_v3.result_schema import build_result_skeleton, validate_complete_result, atomic_write_result
from retrieval_v3.paths import validate_output_path
from retrieval_v3.runner import Runner, load_candidate_plan_or_fail

def test_18_configs_and_drift():
    data = load_and_validate()
    assert len(data["configs"]) == 18
    import copy
    bad = copy.deepcopy(data)
    bad["configs"][0]["sparse_weight"] = 0.02
    try:
        validate_data(bad)
        assert False, "drift not rejected"
    except ValueError:
        pass
    bad2 = copy.deepcopy(data)
    bad2["configs"] = bad2["configs"][:17]
    try:
        validate_data(bad2)
        assert False
    except ValueError:
        pass
    bad3 = copy.deepcopy(data)
    bad3["configs"].append(bad3["configs"][0])
    try:
        validate_data(bad3)
        assert False
    except ValueError:
        pass
    bad4 = copy.deepcopy(data)
    bad4["configs"][1] = copy.deepcopy(bad4["configs"][0])
    bad4["configs"][1]["config_id"] = "candidate-a-02"
    try:
        validate_data(bad4)
        assert False
    except ValueError:
        pass

def test_non_unit_cosine():
    a = [0.600001, 0.8, 0.0]
    b = [0.6, 0.800001, 0.0]
    dot = dot_product(a,b)
    cos = cosine_similarity(a,b)
    assert not math.isclose(dot, cos, rel_tol=1e-6)

def test_representative_tie_and_near_tie():
    qvec = [1,0,0]
    ch1 = {"embedding":[0.5,0.5,0], "chunk_index":1, "id":10}
    ch2 = {"embedding":[0.5,0.5,0], "chunk_index":0, "id":20}
    best, _ = select_representative_chunk(qvec, [ch1,ch2])
    assert best["chunk_index"] == 0
    ch_low = {"embedding":[0.5,0.5,0], "chunk_index":0, "id":1}
    ch_high = {"embedding":[0.9,0.1,0], "chunk_index":5, "id":99}
    best2, _ = select_representative_chunk([1,0,0], [ch_low, ch_high])
    assert best2["chunk_index"] == 5

def test_strict_gt_dedup_boundary():
    import math as m
    def vec_angle(theta):
        rad = m.radians(theta)
        return [m.cos(rad), m.sin(rad), 0]
    angle = m.degrees(m.acos(0.98))
    v1 = vec_angle(0)
    v2 = vec_angle(angle)
    sim = cosine_similarity(v1,v2)
    assert abs(sim-0.98) < 1e-9
    pool = [
        {"policy":{"id":1,"source":"youth","source_id":"a","chunks":[{"embedding":v1,"chunk_index":0,"id":1}]}, "final_score":0.9,"policy_id":1,"source":"youth","source_id":"a","representative_chunk":{"embedding":v1}},
        {"policy":{"id":2,"source":"youth","source_id":"b","chunks":[{"embedding":v2,"chunk_index":0,"id":2}]}, "final_score":0.8,"policy_id":2,"source":"youth","source_id":"b","representative_chunk":{"embedding":v2}},
    ]
    retained = dedup_greedy(pool, 0.98)
    assert len(retained)==2
    v3 = vec_angle(m.degrees(m.acos(0.99)))
    pool2 = [
        {"policy":{"id":1,"source":"youth","source_id":"a","chunks":[{"embedding":v1,"chunk_index":0,"id":1}]}, "final_score":0.9,"policy_id":1,"source":"youth","source_id":"a","representative_chunk":{"embedding":v1}},
        {"policy":{"id":2,"source":"youth","source_id":"b","chunks":[{"embedding":v3,"chunk_index":0,"id":2}]}, "final_score":0.8,"policy_id":2,"source":"youth","source_id":"b","representative_chunk":{"embedding":v3}},
    ]
    retained2 = dedup_greedy(pool2, 0.98)
    assert len(retained2)==1

def test_mmr_actual_cosine_and_full_top30():
    pool = [
        {"policy":{"id":1},"final_score":1.0,"policy_id":1,"source":"a","source_id":"1","representative_chunk":{"embedding":[1,0,0]}},
        {"policy":{"id":2},"final_score":0.9,"policy_id":2,"source":"a","source_id":"2","representative_chunk":{"embedding":[0.99,0.1,0]}},
        {"policy":{"id":3},"final_score":0.8,"policy_id":3,"source":"a","source_id":"3","representative_chunk":{"embedding":[0,1,0]}},
    ]
    sel = mmr_select(pool, 0.3, top_k=3)
    assert [s["policy_id"] for s in sel]==[1,3,2]
    def fake_vec(seed):
        rnd = random.Random(seed)
        v=[rnd.uniform(-1,1) for _ in range(3)]
        norm=(sum(x*x for x in v)**0.5) or 1
        return [x/norm for x in v]
    big=[]
    for i in range(35):
        vec=fake_vec(i+1000)
        big.append({"policy":{"id":i},"final_score":1.0-i*0.01,"policy_id":i,"source":"s","source_id":f"id{i}","representative_chunk":{"embedding":vec}})
    ret = full_top30_pipeline(big, 0.99, 0.0)
    assert len(ret)<=30
    ret2 = full_top30_pipeline(big, 0.99, 0.3)
    assert len(ret2)<=30

def test_exact_normalization_and_boundaries():
    assert is_exact_title("  청년   지원  ","청년 지원")==True
    assert is_exact_title("청년지원","청년지원(서류)")==True
    assert is_exact_title("서울","서울시")==False
    assert is_exact_title("서울특별시","서울특별시청")==False
    assert is_exact_title("청년지원","청년지원시")==False
    assert is_exact_title("청년지원","청년지원 시")==True
    assert is_exact_title("test","test123")==False
    assert is_exact_title("청년지원금","청년지원")==False
    assert is_exact_title("청년지원","청년지원")==True
    assert is_exact_title("abc","abc def")==False
    assert is_exact_title("test","test def")==True
    assert is_exact_org("고용노동부 문의","고용노동부")==True
    assert is_exact_org("고용노동부","고용노동부 문의")==True
    assert is_exact_org("A","A")==False
    assert is_exact_org("Seoul City","seoul")==True

def test_cosine_min_placement():
    def fake_vec(seed):
        rnd=random.Random(seed)
        v=[rnd.uniform(-1,1) for _ in range(3)]
        norm=(sum(x*x for x in v)**0.5)or 1
        return [x/norm for x in v]
    policies=[]
    for i in range(150):
        chunks=[{"embedding": fake_vec(i),"chunk_index":0,"id":i}]
        policies.append({"id":i,"source":"youth","source_id":f"p{i:03d}","title":f"정책 {i}","support_content":"","summary":"","keywords":"","add_qualify":"","income_etc":"","apply_method":"","org":"고용노동부","chunks":chunks})
    qvec=policies[0]["chunks"][0]["embedding"][:]
    d_top=dense_top100(qvec, policies)
    d_filt=filter_dense_by_cosine_min(d_top,0.78)
    assert all(e["dense_cosine"]>=0.78 for e in d_filt)
    assert len(d_filt) <= len(d_top)
    config={"sparse_weight":0.01,"dense_weight":1.0,"exact_title_boost":0.0,"exact_org_boost":0.0,"field_weight_title":1.0,"field_weight_support_content":1.0,"field_weight_eligibility":1.0,"dedup_cosine_threshold":0.98,"diversification_lambda":0.0,"fusion_method":"union"}
    s_top=sparse_top100("청년", policies, config)
    assert len(s_top)==100
    fused=fuse_candidates("청년", d_filt, s_top, {**config,"fusion_method":"union"}, qvec=qvec)
    expected_keys=set((e["source"],e["source_id"]) for e in d_filt) | set((e["source"],e["source_id"]) for e in s_top)
    assert len(fused)==len(expected_keys)

def test_union_vs_hybrid():
    def fake_vec(seed):
        rnd=random.Random(seed)
        v=[rnd.uniform(-1,1) for _ in range(3)]
        norm=(sum(x*x for x in v)**0.5)or 1
        return [x/norm for x in v]
    qvec=[1,0,0]
    policies=[
        {"id":1,"source":"youth","source_id":"A","title":"일반","support_content":"","summary":"","keywords":"","add_qualify":"","income_etc":"","apply_method":"","org":"고용노동부","chunks":[{"embedding":qvec,"chunk_index":0,"id":1}]},
        {"id":2,"source":"youth","source_id":"B","title":"청년 지원 정책 B","support_content":"청년 지원","summary":"","keywords":"","add_qualify":"","income_etc":"","apply_method":"","org":"고용노동부","chunks":[{"embedding":[0,1,0],"chunk_index":0,"id":2}]},
    ]
    d_top=dense_top100(qvec, policies)
    d_filt=filter_dense_by_cosine_min(d_top,0.78)
    assert len(d_filt)==1 and d_filt[0]["source_id"]=="A"
    config={"sparse_weight":0.01,"dense_weight":1.0,"exact_title_boost":0.0,"exact_org_boost":0.0,"field_weight_title":1.0,"field_weight_support_content":1.0,"field_weight_eligibility":1.0,"dedup_cosine_threshold":0.98,"diversification_lambda":0.0,"fusion_method":"union"}
    s_top=sparse_top100("청년 지원", policies, config)
    fused_union=fuse_candidates("청년 지원", d_filt, s_top, {**config,"fusion_method":"union"}, qvec=qvec)
    fused_hybrid=fuse_candidates("청년 지원", d_filt, s_top, {**config,"fusion_method":"hybrid_weighted_sum"}, qvec=qvec)
    union_b=next(e for e in fused_union if e["source_id"]=="B")
    hybrid_b=next(e for e in fused_hybrid if e["source_id"]=="B")
    assert union_b["dense_score"]==0.0
    assert hybrid_b["dense_score"] >=0.0
    qvec2=[1,0,0]
    policies2=[
        {"id":1,"source":"youth","source_id":"A","title":"일반","support_content":"","summary":"","keywords":"","add_qualify":"","income_etc":"","apply_method":"","org":"고용노동부","chunks":[{"embedding":[1,0,0],"chunk_index":0,"id":1}]},
        {"id":2,"source":"youth","source_id":"B","title":"청년 지원 정책 B","support_content":"청년 지원","summary":"","keywords":"","add_qualify":"","income_etc":"","apply_method":"","org":"고용노동부","chunks":[{"embedding":[0.6,0.8,0],"chunk_index":0,"id":2}]},
    ]
    d2=dense_top100(qvec2, policies2)
    d2_f=filter_dense_by_cosine_min(d2,0.78)
    s2=sparse_top100("청년 지원", policies2, config)
    fu=fuse_candidates("청년 지원", d2_f, s2, {**config,"fusion_method":"union"}, qvec=qvec2)
    fh=fuse_candidates("청년 지원", d2_f, s2, {**config,"fusion_method":"hybrid_weighted_sum"}, qvec=qvec2)
    fu_b=next(e for e in fu if e["source_id"]=="B")
    fh_b=next(e for e in fh if e["source_id"]=="B")
    assert fu_b["dense_score"]==0.0
    assert fh_b["dense_score"]>0
    assert abs(fh_b["dense_score"]-0.6) <0.01

def test_exact_not_injected():
    def fake_vec(seed):
        rnd=random.Random(seed)
        v=[rnd.uniform(-1,1) for _ in range(3)]
        norm=(sum(x*x for x in v)**0.5)or 1
        return [x/norm for x in v]
    qvec=[1,0,0]
    policies=[
        {"id":1,"source":"youth","source_id":"A","title":"일반","support_content":"","summary":"","keywords":"","add_qualify":"","income_etc":"","apply_method":"","org":"고용노동부","chunks":[{"embedding":qvec,"chunk_index":0,"id":1}]},
        {"id":2,"source":"youth","source_id":"B","title":"청년 지원","support_content":"","summary":"","keywords":"","add_qualify":"","income_etc":"","apply_method":"","org":"고용노동부","chunks":[{"embedding":[0,1,0],"chunk_index":0,"id":2}]},
    ]
    d_top=dense_top100(qvec, policies)
    d_f=filter_dense_by_cosine_min(d_top,0.78)
    config={"sparse_weight":0.01,"dense_weight":1.0,"exact_title_boost":0.07,"exact_org_boost":0.05,"field_weight_title":1.0,"field_weight_support_content":1.0,"field_weight_eligibility":1.0,"dedup_cosine_threshold":0.98,"diversification_lambda":0.0,"fusion_method":"union"}
    s_top=sparse_top100("청년 지원", policies, config)
    fused=fuse_candidates("청년 지원", d_f, s_top, config, qvec=qvec)
    expected_len=len(set((e["source"],e["source_id"]) for e in d_f) | set((e["source"],e["source_id"]) for e in s_top))
    assert len(fused)==expected_len

def test_deterministic_ordering():
    def fake_vec(val):
        v=[val, 0, 0]
        norm=(sum(x*x for x in v)**0.5)or 1
        return [x/norm for x in v]
    policies=[
        {"id":2,"source":"gov24","source_id":"a","title":"","support_content":"","summary":"","keywords":"","add_qualify":"","income_etc":"","apply_method":"","org":"","chunks":[{"embedding":fake_vec(1),"chunk_index":0,"id":1}]},
        {"id":1,"source":"youth","source_id":"a","title":"","support_content":"","summary":"","keywords":"","add_qualify":"","income_etc":"","apply_method":"","org":"","chunks":[{"embedding":fake_vec(1),"chunk_index":0,"id":2}]},
        {"id":3,"source":"youth","source_id":"b","title":"","support_content":"","summary":"","keywords":"","add_qualify":"","income_etc":"","apply_method":"","org":"","chunks":[{"embedding":fake_vec(1),"chunk_index":0,"id":3}]},
    ]
    qvec=fake_vec(1)
    d_top=dense_top100(qvec, policies)
    assert d_top[0]["source"]=="gov24"
    assert d_top[1]["policy_id"]==1
    config={"sparse_weight":0.01,"dense_weight":1.0,"exact_title_boost":0.0,"exact_org_boost":0.0,"field_weight_title":1.0,"field_weight_support_content":1.0,"field_weight_eligibility":1.0,"dedup_cosine_threshold":0.98,"diversification_lambda":0.0,"fusion_method":"union"}
    d_f=filter_dense_by_cosine_min(d_top,0.78)
    s_top=sparse_top100("청년", policies, config)
    fused=fuse_candidates("청년", d_f, s_top, config, qvec=qvec)
    for i in range(len(fused)-1):
        a=fused[i]
        b=fused[i+1]
        assert (a["final_score"] > b["final_score"]) or (a["final_score"]==b["final_score"] and (a["source"], a["source_id"], a["policy_id"]) < (b["source"], b["source_id"], b["policy_id"]))

def test_metrics_mrr_rank_gt10():
    retrieved=[{"source":"youth","source_id":f"p{i}"} for i in range(15)]
    golds=[{"source":"youth","source_id":"p11","grade":2}]
    assert mrr_at_10(retrieved, golds)==0.0
    golds2=[{"source":"youth","source_id":"p5","grade":2}]
    assert abs(mrr_at_10(retrieved, golds2)-1/6) <1e-9

def test_selection_ordering_and_zero():
    per=[
        {"config_id":"candidate-a-02","success_at_5":0.9,"ndcg_at_5":0.8,"mrr_at_10":0.7},
        {"config_id":"candidate-a-01","success_at_5":0.9,"ndcg_at_5":0.8,"mrr_at_10":0.7},
        {"config_id":"candidate-a-03","success_at_5":0.85,"ndcg_at_5":0.9,"mrr_at_10":0.9},
    ]
    sel=select_candidate(per)
    assert sel["chosen"]=="candidate-a-01"
    sel2=select_candidate(per, latency_p95_per_config={"candidate-a-01":600,"candidate-a-02":500})
    assert sel2["chosen"]=="candidate-a-02"
    per_low=[{"config_id":"candidate-a-01","success_at_5":0.8,"ndcg_at_5":0.9,"mrr_at_10":0.9}]
    sel3=select_candidate(per_low)
    assert sel3["chosen"] is None

def test_b_gate_no_impl():
    bg=candidate_b_gate(0.97,0.85)
    assert bg["admitted"]==True and bg["instantiated"]==False
    bg2=candidate_b_gate(0.96,0.85)
    assert not bg2["admitted"]
    bg3=candidate_b_gate(0.98,0.94)
    assert not bg3["admitted"]

def test_latency_harness():
    tasks=[f"task-{i:03d}" for i in range(35)]
    log=[]
    def base(t): log.append(("base",t))
    def cand(t): log.append(("cand",t))
    cnt=[0]
    def clock():
        cnt[0]+=1000000
        return cnt[0]
    res=measure_paired_latency(tasks, base, cand, clock_fn=clock, warmup_n=30)
    assert len(log)==130
    warm=sorted(tasks)[:30]
    for i,tid in enumerate(warm):
        assert log[i*2]==("base",tid)
        assert log[i*2+1]==("cand",tid)
    timed=log[60:]
    for idx,tid in enumerate(sorted(tasks)):
        exp=[("base",tid),("cand",tid)] if idx%2==0 else [("cand",tid),("base",tid)]
        assert timed[idx*2:idx*2+2]==exp
    assert res["gate"]=="PASS"

def test_audit_lifecycle():
    import tempfile, pathlib
    with tempfile.TemporaryDirectory() as td:
        log=pathlib.Path(td)/"events.jsonl"
        e1=append_event(str(log), action="run_start", set_role="dev", set_sha="a"*64, candidate_id="v3", session_id="s1")
        e2=append_event(str(log), action="protected_access_start", set_role="dev", set_sha="a"*64, session_id="s1", outcome="success")
        granted=verify_holdout_access_allowed(str(log), set_role="dev", set_sha="a"*64, session_id="s1", expected_event_hash=e2["event_hash"])
        assert granted["event_hash"]==e2["event_hash"]
        try:
            verify_holdout_access_allowed(str(log), set_role="dev", set_sha="a"*64, session_id="s1", expected_event_hash=e1["event_hash"])
            assert False
        except Exception:
            pass
        e3=append_event(str(log), action="protected_access_end", set_role="dev", set_sha="a"*64, session_id="s1")
        try:
            verify_holdout_access_allowed(str(log), set_role="dev", set_sha="a"*64, session_id="s1")
            assert False
        except Exception:
            pass
        e4=append_event(str(log), action="protected_access_start", set_role="dev", set_sha="a"*64, session_id="s1", outcome="success")
        verify_holdout_access_allowed(str(log), set_role="dev", set_sha="a"*64, session_id="s1", expected_event_hash=e4["event_hash"])
        e5=append_event(str(log), action="run_end", set_role="dev", set_sha="a"*64, candidate_id="v3", session_id="s1")
        chain=read_and_verify_chain(str(log))
        assert len(chain)==5

def test_atomic_rerun_concurrent():
    per=[{"config_id":f"candidate-a-{i:02d}","success_at_5":0.9,"ndcg_at_5":0.8,"mrr_at_10":0.7} for i in range(1,19)]
    git_head=subprocess.run(["git","rev-parse","HEAD"], capture_output=True, text=True).stdout.strip().lower()
    plan_sha=hashlib.sha256(pathlib.Path("eval/retrieval-v3/candidate-plan/candidate-plan-v1.json").read_bytes()).hexdigest()
    prereg_sha=hashlib.sha256(pathlib.Path("docs/RETRIEVAL_V3_PREREG.md").read_bytes()).hexdigest()
    sel={"chosen":"candidate-a-01","eligible":["candidate-a-01"],"ordering":"Success@5 desc -> NDCG@5 desc -> MRR@10 desc -> paired p95 asc -> lexicographic config_id asc","reason":"selected","eligible_details":[]}
    bg={"union_oracle_recall_100":0.97,"candidate_a_success_5":0.85,"union_pp":97,"candidate_pp":85,"headroom_pp":12,"admitted":True,"instantiated":False}
    prov={"candidate_plan_sha256":plan_sha,"prereg_sha256":prereg_sha}
    result=build_result_skeleton(per_config_metrics=per, selection=sel, candidate_b_gate=bg, provenance=prov, git_head=git_head, git_dirty=False)
    out=pathlib.Path("eval/retrieval_v3/results/test-atomic-temp.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    atomic_write_result(result, str(out))
    assert out.exists()
    try:
        atomic_write_result(result, str(out))
        assert False
    except FileExistsError:
        pass
    content=out.read_text(encoding="utf-8")
    assert "candidate-a-01" in content
    out.unlink()

def test_path_confinement():
    try:
        validate_output_path("eval/retrieval-v3/results/../../etc/passwd")
        assert False
    except ValueError:
        pass
    validate_output_path("eval/retrieval-v3/results/v3-candidate-dev-result.json")
    try:
        validate_output_path("eval/retrieval-v3/results/../.git/config")
        assert False
    except ValueError:
        pass

def test_cli_orchestrator_e2e():
    plan=load_candidate_plan_or_fail()
    def fake_vec(seed):
        rnd=random.Random(seed)
        v=[rnd.uniform(-1,1) for _ in range(768)]
        norm=(sum(x*x for x in v)**0.5)or 1
        return [round(x/norm,6) for x in v]
    policies=[]
    for i in range(5):
        chunks=[{"embedding": fake_vec(i),"chunk_index":0,"id":i}]
        policies.append({"id":i+1,"source":"youth","source_id":f"p{i}","title":f"정책 {i}","support_content":"","summary":"","keywords":"","add_qualify":"","income_etc":"","apply_method":"","org":"고용노동부","chunks":chunks})
    def fake_emb(q):
        h=hashlib.sha256(q.encode()).digest()
        return fake_vec(int.from_bytes(h[:4],"little"))
    tasks=[{"task_id":f"t{i}","query":f"청년 {i}","golds":[{"source":"youth","source_id":"p0","grade":2}],"stratum":"natural_needs","location_bearing":False} for i in range(5)]
    with tempfile.TemporaryDirectory() as td:
        audit_log=pathlib.Path(td)/"audit.jsonl"
        out=pathlib.Path(td)/"out.json"
        runner=Runner(candidate_plan=plan, embedding_fn=fake_emb, db_policy_loader=lambda: policies, protected_set_loader=lambda r,s: tasks, audit_log_path=audit_log)
        res=runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="cli-test", set_role="dev", set_sha=None, audit_log=audit_log, output_path=out, skip_audit=True)
        assert len(res["per_config_metrics"])==18
        assert all("candidate-b" not in m["config_id"] for m in res["per_config_metrics"])
        assert out.exists()
        tasks_path=pathlib.Path(td)/"tasks.jsonl"
        policies_path=pathlib.Path(td)/"policies.json"
        with open(tasks_path,"w", encoding="utf-8") as f:
            for t in tasks:
                f.write(json.dumps(t, ensure_ascii=False)+"\n")
        with open(policies_path,"w", encoding="utf-8") as f:
            f.write(json.dumps(policies, ensure_ascii=False))
        out2=pathlib.Path(td)/"out2.json"
        audit2=pathlib.Path(td)/"audit2.jsonl"
        cmd=[sys.executable, "-m", "eval.retrieval_v3.runner", "--tasks", str(tasks_path), "--policies", str(policies_path), "--output", str(out2), "--audit-log", str(audit2), "--session-id", "cli-e2e", "--skip-audit"]
        r=subprocess.run(cmd, capture_output=True, text=True, cwd=str(pathlib.Path(__file__).resolve().parents[1]))
        assert r.returncode==0, f"CLI failed: {r.stderr[:500]}"
        assert out2.exists()

if __name__=="__main__":
    tests=[test_18_configs_and_drift, test_non_unit_cosine, test_representative_tie_and_near_tie, test_strict_gt_dedup_boundary, test_mmr_actual_cosine_and_full_top30, test_exact_normalization_and_boundaries, test_cosine_min_placement, test_union_vs_hybrid, test_exact_not_injected, test_deterministic_ordering, test_metrics_mrr_rank_gt10, test_selection_ordering_and_zero, test_b_gate_no_impl, test_latency_harness, test_audit_lifecycle, test_atomic_rerun_concurrent, test_path_confinement, test_cli_orchestrator_e2e]
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception as e:
            print(f"FAIL {t.__name__}: {e}")
            import traceback; traceback.print_exc()
            sys.exit(1)
    print("ALL 18 focused tests PASS")
