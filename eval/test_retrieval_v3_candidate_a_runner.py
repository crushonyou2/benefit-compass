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
from retrieval_v3.metrics import success_at_5, mrr_at_10, ndcg_at_5, ndcg_at_10, success_at_1, success_at_3, success_at_5_strict_grade3, dcg_at_k, idcg_at_k, compute_headline_metrics, compute_oracle_recall, compute_slice_diagnostics
from retrieval_v3.selection import select_candidate, candidate_b_gate, EXPECTED_SAFETY_GATES
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
    # Explicit fixtures required after fail-closed fix E: missing safety/latency => HOLD
    safety_ok = {cid: {"unsupported":"PASS","ambiguous":"PASS","ineligible_expired":"PASS","official_link":"PASS","http_resolution":"PASS","cost":"PASS"} for cid in ["candidate-a-01","candidate-a-02","candidate-a-03"]}
    per=[
        {"config_id":"candidate-a-02","success_at_5":0.9,"ndcg_at_5":0.8,"mrr_at_10":0.7},
        {"config_id":"candidate-a-01","success_at_5":0.9,"ndcg_at_5":0.8,"mrr_at_10":0.7},
        {"config_id":"candidate-a-03","success_at_5":0.85,"ndcg_at_5":0.9,"mrr_at_10":0.9},
    ]
    sel=select_candidate(per, safety_per_config=safety_ok, latency_p95_per_config={"candidate-a-01":500,"candidate-a-02":500,"candidate-a-03":500})
    assert sel["chosen"]=="candidate-a-01"
    sel2=select_candidate(per, safety_per_config=safety_ok, latency_p95_per_config={"candidate-a-01":600,"candidate-a-02":500,"candidate-a-03":500})
    assert sel2["chosen"]=="candidate-a-02"
    per_low=[{"config_id":"candidate-a-01","success_at_5":0.8,"ndcg_at_5":0.9,"mrr_at_10":0.9}]
    safety_low = {"candidate-a-01": {"unsupported":"PASS","ambiguous":"PASS","ineligible_expired":"PASS","official_link":"PASS","http_resolution":"PASS","cost":"PASS"}}
    sel3=select_candidate(per_low, safety_per_config=safety_low, latency_p95_per_config={"candidate-a-01":500})
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
        e3=append_event(str(log), action="protected_access_end", set_role="dev", set_sha="a"*64, session_id="s1", outcome="success")
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

def test_runner_safety_hold_when_checkers_absent():
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
    tasks=[{"task_id":f"t{i}","query":f"정책 0","golds":[{"source":"youth","source_id":"p0","grade":2}],"stratum":"natural_needs","location_bearing":False} for i in range(5)]
    with tempfile.TemporaryDirectory() as td:
        audit_log=pathlib.Path(td)/"audit.jsonl"
        out=pathlib.Path(td)/"out.json"
        runner=Runner(candidate_plan=plan, embedding_fn=fake_emb, db_policy_loader=lambda: policies, protected_set_loader=lambda r,s: tasks, audit_log_path=audit_log)
        res=runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="safety-hold", set_role="dev", set_sha=None, audit_log=audit_log, output_path=out, skip_audit=True)
        assert res["selection"]["chosen"] is None, "without snapshot/http checker safety must be HOLD => no eligible"
        assert res["candidate_b_gate"]["instantiated"] is False

def test_runner_safety_hold_even_with_checkers_pre_dev():
    # SAME-STAGE HOLD repair: pre-dev runner has no real safety measurement from retrieval results.
    # Previous vacuous [True...] + checker-presence PASS fabricated safety; now always HOLD fail-closed.
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
    tasks=[{"task_id":f"t{i}","query":f"정책 0","golds":[{"source":"youth","source_id":"p0","grade":2}],"stratum":"natural_needs","location_bearing":False} for i in range(5)]
    with tempfile.TemporaryDirectory() as td:
        audit_log=pathlib.Path(td)/"audit.jsonl"
        out=pathlib.Path(td)/"out.json"
        cnt=[0]
        def clock():
            cnt[0]+=1000000
            return cnt[0]
        runner=Runner(candidate_plan=plan, embedding_fn=fake_emb, db_policy_loader=lambda: policies, protected_set_loader=lambda r,s: tasks, audit_log_path=audit_log, corpus_provenance_fn=lambda: {"total_policies":5, "total_chunks":5}, http_checker=lambda urls: True, clock_fn=clock)
        res=runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="safety-pass", set_role="dev", set_sha=None, audit_log=audit_log, output_path=out, skip_audit=True)
        assert len(res["per_config_metrics"])==18
        assert res["selection"]["chosen"] is None, "pre-dev no real safety measurement => HOLD, no eligible even with checkers"
        for cid, rep in res.get("safety_per_config", {}).items():
            assert rep.get("gate") == "HOLD" and rep.get("detail") == "pre_dev_no_real_measurement"
def test_runner_latency_wiring():
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
    tasks=[{"task_id":f"t{i:03d}","query":f"정책 {i}","golds":[{"source":"youth","source_id":"p0","grade":2}],"stratum":"natural_needs","location_bearing":False} for i in range(5)]
    with tempfile.TemporaryDirectory() as td:
        audit_log=pathlib.Path(td)/"audit.jsonl"
        out=pathlib.Path(td)/"out.json"
        cnt=[0]
        def clock():
            cnt[0]+=1000000
            return cnt[0]
        runner=Runner(candidate_plan=plan, embedding_fn=fake_emb, db_policy_loader=lambda: policies, protected_set_loader=lambda r,s: tasks, audit_log_path=audit_log, clock_fn=clock)
        res=runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="latency-test", set_role="dev", set_sha=None, audit_log=audit_log, output_path=out, skip_audit=True)
        assert len(res["per_config_metrics"])==18

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
def test_fusion_youth_bias_only_youth_source_gov24_zero():
    # Regression A: youth bias only source==youth, gov24 zero even with youth intent
    def fake_vec(v):
        norm = (sum(x*x for x in v)**0.5) or 1
        return [x/norm for x in v]
    qvec = fake_vec([1,0,0])
    # query contains youth term without Gov24 => bias 0.015
    query_youth = "청년 지원"
    assert youth_source_bias(query_youth) == 0.015
    # gov24 term suppresses
    assert youth_source_bias("국토교통부 청년 지원") == 0.0
    policies = [
        {"id":1,"source":"youth","source_id":"A","title":"","support_content":"","summary":"","keywords":"","add_qualify":"","income_etc":"","apply_method":"","org":"","chunks":[{"embedding":qvec,"chunk_index":0,"id":1}]},
        {"id":2,"source":"gov24","source_id":"B","title":"","support_content":"","summary":"","keywords":"","add_qualify":"","income_etc":"","apply_method":"","org":"","chunks":[{"embedding":qvec,"chunk_index":0,"id":2}]},
    ]
    d_top = dense_top100(qvec, policies)
    d_f = filter_dense_by_cosine_min(d_top, 0.78)
    config = {"sparse_weight":0.01,"dense_weight":1.0,"exact_title_boost":0.0,"exact_org_boost":0.0,"field_weight_title":1.0,"field_weight_support_content":1.0,"field_weight_eligibility":1.0,"dedup_cosine_threshold":0.98,"diversification_lambda":0.0,"fusion_method":"union"}
    s_top = sparse_top100(query_youth, policies, config)
    fused = fuse_candidates(query_youth, d_f, s_top, config, qvec=qvec)
    fy = next(e for e in fused if e["source"]=="youth")
    fg = next(e for e in fused if e["source"]=="gov24")
    # youth should have youth_score 0.015, gov24 0.0
    assert abs(fy["youth_score"] - 0.015) < 1e-9, f"youth youth_score {fy['youth_score']}"
    assert fg["youth_score"] == 0.0, f"gov24 youth_score {fg['youth_score']}"
    assert abs((fy["final_score"] - fg["final_score"]) - 0.015) < 1e-9
    # Gov24 suppressed query => both 0
    fused2 = fuse_candidates("국토교통부 청년 지원", d_f, s_top, config, qvec=qvec)
    for e in fused2:
        assert e["youth_score"] == 0.0

def test_sparse_only_representative_query_nearest_no_chunk0_fallback():
    # Regression B: sparse-only must still pick query-nearest chunk via actual cosine/tie, not chunk0
    qvec = [0,1,0]
    # chunks: two far-ish but one nearer; both <0.78 so dense filtered will exclude, but nearest should be chunk1
    # chunk0 far [1,0,0] cos 0 ; chunk1 nearer [0.8,0.6,0] cos 0.6 (actual cosine); nearest is chunk1 (index1)
    far = [1,0,0]
    nearer = [0.8,0.6,0]  # cos with [0,1,0] is 0.6
    # normalize for actual cosine but not unit? Use as is for cosine_similarity (actual)
    policy_sparse_only = {"id":10,"source":"youth","source_id":"SP","title":"청년 지원 정책","support_content":"청년 지원","summary":"","keywords":"","add_qualify":"","income_etc":"","apply_method":"","org":"고용노동부","chunks":[{"embedding":far,"chunk_index":0,"id":100},{"embedding":nearer,"chunk_index":1,"id":101}]}
    policy_dense = {"id":11,"source":"youth","source_id":"DP","title":"","support_content":"","summary":"","keywords":"","add_qualify":"","income_etc":"","apply_method":"","org":"","chunks":[{"embedding":qvec,"chunk_index":0,"id":102}]}
    policies = [policy_sparse_only, policy_dense]
    d_top = dense_top100(qvec, policies)
    d_f = filter_dense_by_cosine_min(d_top, 0.78)
    # DP will be in dense; SP not (both chunks <0.78, nearest 0.6 <0.78) => sparse-only
    assert any(e["source_id"]=="DP" for e in d_f)
    assert not any(e["source_id"]=="SP" for e in d_f), f"SP should be sparse-only, d_f {[e['source_id'] for e in d_f]}"
    config = {"sparse_weight":0.01,"dense_weight":1.0,"exact_title_boost":0.0,"exact_org_boost":0.0,"field_weight_title":1.0,"field_weight_support_content":1.0,"field_weight_eligibility":1.0,"dedup_cosine_threshold":0.98,"diversification_lambda":0.0,"fusion_method":"union"}
    s_top = sparse_top100("청년 지원", policies, config)
    # ensure SP in sparse
    assert any(e["source_id"]=="SP" for e in s_top)
    fused = fuse_candidates("청년 지원", d_f, s_top, config, qvec=qvec)
    sp_fused = next(e for e in fused if e["source_id"]=="SP")
    # representative should be nearer chunk index 1, not 0
    rep = sp_fused["representative_chunk"]
    assert rep is not None and rep["chunk_index"] == 1 and rep["id"] == 101, f"got {rep}"
    # also test exact cosine tie: two identical embeddings different indices => smallest index wins
    same = [0.5,0.5,0]
    pol_tie = {"id":12,"source":"youth","source_id":"TIE","title":"","support_content":"","summary":"","keywords":"","add_qualify":"","income_etc":"","apply_method":"","org":"","chunks":[{"embedding":same,"chunk_index":1,"id":20},{"embedding":same,"chunk_index":0,"id":30}]}
    from retrieval_v3.dense import select_representative_chunk
    best,_ = select_representative_chunk([1,0,0], pol_tie["chunks"])
    assert best["chunk_index"] == 0, "tie must pick smallest chunk_index"
    # via dedup path also: get_representative_vector should use nearest not fallback
    from retrieval_v3.dedup import get_representative_vector
    vec = get_representative_vector(policy_sparse_only, qvec)
    assert vec == nearer

def test_oracle_union_set_and_headline130():
    # Regression C: union@K is set of dense own topK ∪ sparse own topK ∪ exact own topK, B gate headline130 only
    # Build controlled pools where set union hits but old ordered slice at K=2 would miss; we test at supported K=30
    gold = [{"source":"youth","source_id":"C","grade":2}]
    # dense top30-pool has A,B ; sparse top30-pool has C,D ; exact top30-pool has E,F
    task_oracle = {
        "dense_pool": [{"source":"youth","source_id":"A"}, {"source":"youth","source_id":"B"}],
        "sparse_pool": [{"source":"youth","source_id":"C"}, {"source":"youth","source_id":"D"}],
        "exact_pool": [{"source":"youth","source_id":"E"}, {"source":"youth","source_id":"F"}],
        "union_pool": [{"source":"youth","source_id":"A"}, {"source":"youth","source_id":"B"}, {"source":"youth","source_id":"C"}, {"source":"youth","source_id":"D"}, {"source":"youth","source_id":"E"}, {"source":"youth","source_id":"F"}],
        "golds": gold,
    }
    # At K=30, dense top30 does NOT contain C, but sparse does. Set union@30 should be 1.
    out = compute_oracle_recall([task_oracle])
    assert out["union_recall_at_30"] == 1.0, f"union@30 got {out['union_recall_at_30']}"
    assert out["dense_recall_at_30"] == 0.0
    assert out["sparse_recall_at_30"] == 1.0
    # Also test headline filtering via Runner
    plan = load_candidate_plan_or_fail()
    def fake_vec(seed):
        rnd = random.Random(seed)
        v=[rnd.uniform(-1,1) for _ in range(768)]
        norm=(sum(x*x for x in v)**0.5)or 1
        return [round(x/norm,6) for x in v]
    # policies for runner headline test: make headline tasks succeed, safety tasks fail union
    policies=[]
    for i in range(6):
        policies.append({"id":i+1,"source":"youth","source_id":f"p{i}","title":f"정책 {i}","support_content":"","summary":"","keywords":"","add_qualify":"","income_etc":"","apply_method":"","org":"고용노동부","chunks":[{"embedding":fake_vec(i),"chunk_index":0,"id":i}]})
    def fake_emb(q):
        h=hashlib.sha256(q.encode()).digest()
        return fake_vec(int.from_bytes(h[:4],"little"))
    # Create 130 headline-like tasks (natural_needs) and 50 safety tasks
    headline_tasks = [{"task_id":f"h{i:03d}","query":"정책 0","golds":[{"source":"youth","source_id":"p0","grade":2}],"stratum":"natural_needs","location_bearing":False} for i in range(3)]
    safety_tasks = [{"task_id":f"s{i:03d}","query":"정책 0","golds":[{"source":"youth","source_id":"p1","grade":2}],"stratum":"unsupported_no_answer","location_bearing":False} for i in range(2)]
    tasks = headline_tasks + safety_tasks
    with tempfile.TemporaryDirectory() as td:
        audit_log=pathlib.Path(td)/"audit.jsonl"
        outp=pathlib.Path(td)/"out.json"
        runner=Runner(candidate_plan=plan, embedding_fn=fake_emb, db_policy_loader=lambda: policies, protected_set_loader=lambda r,s: tasks, audit_log_path=audit_log, corpus_provenance_fn=lambda: {"total_policies":6,"total_chunks":6}, http_checker=lambda urls: True)
        res=runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="headline-oracle", set_role="dev", set_sha=None, audit_log=audit_log, output_path=outp, skip_audit=True)
        # per_config_metrics oracle_recall should be headline-only (h contains p0, so headline recall >0); all recall would be diluted if safety tasks miss
        pm = res["per_config_metrics"][0]
        assert "oracle_recall" in pm and "union_recall_at_100" in pm["oracle_recall"]
        # headline recall computed correctly
        assert pm["union_oracle_R100"] == pm["oracle_recall"]["union_recall_at_100"]

def test_metrics_graded_strict_and_ndcg():
    # Regression D: graded multi-gold equivalence-group, S1/S3/S5, strict grade3 S5, MRR@10, NDCG@5/@10
    retrieved = [{"source":"youth","source_id":"p1"}, {"source":"youth","source_id":"p2"}, {"source":"gov24","source_id":"p3"}, {"source":"youth","source_id":"p4"}, {"source":"youth","source_id":"p5"}, {"source":"youth","source_id":"p6"},{"source":"youth","source_id":"p7"},{"source":"youth","source_id":"p8"},{"source":"youth","source_id":"p9"},{"source":"youth","source_id":"p10"}, {"source":"youth","source_id":"p11"}]
    # Golds: p1 grade3 perfect, p2 grade2 acceptable, p11 grade2 far
    golds = [{"source":"youth","source_id":"p1","grade":3,"equivalence_group":"A"}, {"source":"youth","source_id":"p2","grade":2,"equivalence_group":"B"}, {"source":"youth","source_id":"p11","grade":2,"equivalence_group":"C"}]
    assert success_at_5(retrieved, golds) == 1
    assert success_at_1(retrieved, golds) == 1  # p1 in top1
    assert success_at_3(retrieved, golds) == 1
    assert success_at_5_strict_grade3(retrieved, golds) == 1  # p1 grade3 in top5
    assert mrr_at_10(retrieved, golds) == 1.0  # first grade>=2 at rank1
    # NDCG: grade-weighted
    n5 = ndcg_at_5(retrieved, golds)
    n10 = ndcg_at_10(retrieved, golds)
    assert 0 < n5 <= 1.0 and 0 < n10 <= 1.0
    # Strict case: only grade2 in top5, no grade3 => success 1 but strict 0
    retrieved2 = [{"source":"youth","source_id":"p2"}, {"source":"youth","source_id":"x"}]
    assert success_at_5(retrieved2, golds) == 1
    assert success_at_5_strict_grade3(retrieved2, golds) == 0
    # Grade 1 should not count for success
    golds3 = [{"source":"youth","source_id":"p2","grade":1}]
    assert success_at_5(retrieved2, golds3) == 0
    # Headline metrics aggregation includes all new fields
    tr = [{"retrieved": retrieved, "golds": golds}]
    hm = compute_headline_metrics(tr)
    assert "success_at_1" in hm and "success_at_3" in hm and "success_at_5_strict_grade3" in hm and "ndcg_at_10" in hm
    assert hm["success_at_1"] == 1.0 and hm["mrr_at_10"] == 1.0

def test_metrics_equivalence_group_no_double_count():
    # Regression D: two grade3 gold IDs share one equivalence_group => one relevance unit, retrieving both cannot yield two gains
    golds_same_group = [
        {"source":"youth","source_id":"p1","grade":3,"equivalence_group":"A"},
        {"source":"youth","source_id":"p2","grade":3,"equivalence_group":"A"},
    ]
    # Retrieved contains both p1 and p2 at ranks 1 and 2
    retrieved_both = [{"source":"youth","source_id":"p1"},{"source":"youth","source_id":"p2"}, {"source":"youth","source_id":"p3"}]
    retrieved_one = [{"source":"youth","source_id":"p1"}, {"source":"youth","source_id":"p3"}]
    retrieved_alt = [{"source":"youth","source_id":"p2"}, {"source":"youth","source_id":"p3"}]
    # Success should be 1 for any single member
    assert success_at_5(retrieved_one, golds_same_group) == 1
    assert success_at_5(retrieved_alt, golds_same_group) == 1
    # DCG: group gain counted once, not twice. DCG for both should equal DCG for one (only first rank counts)
    dcg_both = dcg_at_k(retrieved_both, golds_same_group, 5)
    dcg_one = dcg_at_k(retrieved_one, golds_same_group, 5)
    # Both should be equal because second member of same group not double counted (first rank 1 gain=3, second rank 2 would be ignored)
    assert abs(dcg_both - dcg_one) < 1e-9, f"dcg double count {dcg_both} vs {dcg_one}"
    # IDCG: with same group, only one grade3 gain, not two. So IDCG@5 with two members same group should be grade 3 at rank1 only, not 3+3
    idcg = idcg_at_k(golds_same_group, 5)
    # Expected idcg = 3 / log2(2) = 3.0 (only one group)
    import math
    expected = 3 / math.log2(2)
    assert abs(idcg - expected) < 1e-9, f"idcg double count {idcg} vs {expected}"
    # If we had two distinct groups, idcg would be 3/log2(2) + 3/log2(3)
    golds_two_groups = [
        {"source":"youth","source_id":"p1","grade":3,"equivalence_group":"A"},
        {"source":"youth","source_id":"p2","grade":3,"equivalence_group":"B"},
    ]
    idcg2 = idcg_at_k(golds_two_groups, 5)
    expected2 = 3/math.log2(2) + 3/math.log2(3)
    assert abs(idcg2 - expected2) < 1e-9
    # NDCG for both same group should be 1.0 when retrieving one member at rank1, not <1 due to missing second
    ndcg_one = ndcg_at_5(retrieved_one, golds_same_group)
    assert abs(ndcg_one - 1.0) < 1e-9
    # Alternative member also 1.0
    ndcg_alt = ndcg_at_5(retrieved_alt, golds_same_group)
    assert abs(ndcg_alt - 1.0) < 1e-9
    # Success/MRR with equivalence_group also via alternative member
    retrieved_none = [{"source":"youth","source_id":"x"}]
    assert success_at_5(retrieved_none, golds_same_group) == 0
    assert mrr_at_10(retrieved_alt, golds_same_group) == 1.0


def test_slice_diagnostics_unavailable():
    # Regression D secondary: missing metadata => unavailable, not synthesized
    tr = [{"retrieved":[{"source":"youth","source_id":"p1"}],"golds":[{"source":"youth","source_id":"p1","grade":2}],"source":"youth","stratum":"natural_needs","location_bearing":False,"task_id":"t1"}]
    sd_source = compute_slice_diagnostics(tr, "source")
    assert isinstance(sd_source, dict) and "youth" in sd_source
    sd_cat = compute_slice_diagnostics(tr, "category")
    assert sd_cat == "unavailable", f"expected unavailable, got {sd_cat}"
    sd_fresh = compute_slice_diagnostics(tr, "freshness")
    assert sd_fresh == "unavailable"
    sd_cvr = compute_slice_diagnostics(tr, "common_vs_rare")
    assert sd_cvr == "unavailable"
    # when present, should group
    tr2 = [{"retrieved":[{"source":"youth","source_id":"p1"}],"golds":[{"source":"youth","source_id":"p1","grade":2}],"category":"housing_finance","freshness":"stable","common_vs_rare":"common","source":"youth","stratum":"natural_needs","location_bearing":True,"task_id":"t1"}]
    sd_cat2 = compute_slice_diagnostics(tr2, "category")
    assert isinstance(sd_cat2, dict) and "housing_finance" in sd_cat2

def test_selection_fail_closed_missing_gates():
    # Regression E: missing safety or expected gates => ineligible/HOLD, explicit fixtures, exact order
    per = [
        {"config_id":"candidate-a-01","success_at_5":0.9,"ndcg_at_5":0.8,"mrr_at_10":0.7},
        {"config_id":"candidate-a-02","success_at_5":0.9,"ndcg_at_5":0.8,"mrr_at_10":0.7},
    ]
    # Missing cost gate
    safety_missing = {
        "candidate-a-01": {"unsupported":"PASS","ambiguous":"PASS","ineligible_expired":"PASS","official_link":"PASS","http_resolution":"PASS","cost":"PASS"},
        "candidate-a-02": {"unsupported":"PASS","ambiguous":"PASS","ineligible_expired":"PASS","official_link":"PASS","http_resolution":"PASS"},  # missing cost
    }
    sel = select_candidate(per, safety_per_config=safety_missing, latency_p95_per_config={"candidate-a-01":500,"candidate-a-02":500})
    assert sel["chosen"] == "candidate-a-01", "missing cost gate should make a-02 ineligible"
    assert "candidate-a-02" not in sel["eligible"]
    # Missing safety dict entirely for a config => HOLD
    safety_partial = {"candidate-a-01": {"unsupported":"PASS","ambiguous":"PASS","ineligible_expired":"PASS","official_link":"PASS","http_resolution":"PASS","cost":"PASS"}}
    sel2 = select_candidate(per, safety_per_config=safety_partial, latency_p95_per_config={"candidate-a-01":500,"candidate-a-02":500})
    assert sel2["chosen"] == "candidate-a-01" and "candidate-a-02" not in sel2["eligible"]
    # HOLD gate also ineligible
    safety_hold = {
        "candidate-a-01": {"unsupported":"HOLD","ambiguous":"PASS","ineligible_expired":"PASS","official_link":"PASS","http_resolution":"PASS","cost":"PASS"},
        "candidate-a-02": {"unsupported":"PASS","ambiguous":"PASS","ineligible_expired":"PASS","official_link":"PASS","http_resolution":"PASS","cost":"PASS"},
    }
    sel3 = select_candidate(per, safety_per_config=safety_hold, latency_p95_per_config={"candidate-a-01":500,"candidate-a-02":500})
    assert sel3["chosen"] == "candidate-a-02"

def test_selection_fail_closed_missing_latency():
    per = [
        {"config_id":"candidate-a-01","success_at_5":0.9,"ndcg_at_5":0.8,"mrr_at_10":0.7},
        {"config_id":"candidate-a-02","success_at_5":0.9,"ndcg_at_5":0.8,"mrr_at_10":0.7},
    ]
    safety_ok = {
        "candidate-a-01": {"unsupported":"PASS","ambiguous":"PASS","ineligible_expired":"PASS","official_link":"PASS","http_resolution":"PASS","cost":"PASS"},
        "candidate-a-02": {"unsupported":"PASS","ambiguous":"PASS","ineligible_expired":"PASS","official_link":"PASS","http_resolution":"PASS","cost":"PASS"},
    }
    # latency dict missing entry for a-02 => HOLD
    sel = select_candidate(per, safety_per_config=safety_ok, latency_p95_per_config={"candidate-a-01":500})
    assert sel["chosen"] == "candidate-a-01"
    assert "candidate-a-02" not in sel["eligible"]
    # latency None value => HOLD
    sel2 = select_candidate(per, safety_per_config=safety_ok, latency_p95_per_config={"candidate-a-01":500,"candidate-a-02": None})
    assert sel2["chosen"] == "candidate-a-01"
    # non-finite latency (inf/nan) => HOLD
    sel_inf = select_candidate(per, safety_per_config=safety_ok, latency_p95_per_config={"candidate-a-01":500,"candidate-a-02": float("inf")})
    assert sel_inf["chosen"] == "candidate-a-01"
    sel_nan = select_candidate(per, safety_per_config=safety_ok, latency_p95_per_config={"candidate-a-01":500,"candidate-a-02": float("nan")})
    assert sel_nan["chosen"] == "candidate-a-01"
    # ordering exact: S5 desc -> NDCG5 desc -> MRR10 desc -> p95 asc -> config_id asc
    per_order = [
        {"config_id":"candidate-a-02","success_at_5":0.9,"ndcg_at_5":0.8,"mrr_at_10":0.7},
        {"config_id":"candidate-a-01","success_at_5":0.9,"ndcg_at_5":0.8,"mrr_at_10":0.7},
        {"config_id":"candidate-a-03","success_at_5":0.9,"ndcg_at_5":0.9,"mrr_at_10":0.5},
    ]
    sel3 = select_candidate(per_order, safety_per_config={"candidate-a-01": {"unsupported":"PASS","ambiguous":"PASS","ineligible_expired":"PASS","official_link":"PASS","http_resolution":"PASS","cost":"PASS"},"candidate-a-02": {"unsupported":"PASS","ambiguous":"PASS","ineligible_expired":"PASS","official_link":"PASS","http_resolution":"PASS","cost":"PASS"},"candidate-a-03": {"unsupported":"PASS","ambiguous":"PASS","ineligible_expired":"PASS","official_link":"PASS","http_resolution":"PASS","cost":"PASS"}}, latency_p95_per_config={"candidate-a-01":600,"candidate-a-02":500,"candidate-a-03":500})
    # Among 0.9 S5, higher NDCG5 (a-03) should win? Check: a-03 has NDCG 0.9 >0.8 so should be first
    assert sel3["eligible"][0] == "candidate-a-03"
    # Between a-01 and a-02 same S5/NDCG/MRR, lower p95 wins => a-02
    assert sel3["eligible"][1] == "candidate-a-02"
    assert sel3["eligible"][2] == "candidate-a-01"
    # exact string
    assert sel3["ordering"] == "Success@5 desc -> NDCG@5 desc -> MRR@10 desc -> paired p95 asc -> lexicographic config_id asc"

def test_execution_lifecycle_audit_closure_on_failure():
    import pathlib, tempfile, hashlib, random
    from retrieval_v3.runner import Runner
    from retrieval_v3.candidate_registry import load_and_validate
    from retrieval_v3.audit import read_and_verify_chain
    plan = load_and_validate()
    def fake_vec(seed):
        rnd = random.Random(seed)
        v = [rnd.uniform(-1,1) for _ in range(768)]
        norm = (sum(x*x for x in v)**0.5) or 1
        return [x/norm for x in v]
    def failing_emb(q):
        raise RuntimeError("injected embedding failure for lifecycle test")
    policies = []
    for i in range(5):
        policies.append({"id": i+1, "source": "youth", "source_id": f"p{i}", "title": f"정책 {i}", "support_content": "", "summary": "", "keywords": "", "add_qualify": "", "income_etc": "", "apply_method": "", "org": "고용노동부", "chunks": [{"embedding": fake_vec(i), "chunk_index": 0, "id": i}]})
    tasks = [{"task_id": f"t{i}", "query": f"정책 0", "golds": [{"source": "youth", "source_id": "p0", "grade": 2}], "stratum": "natural_needs", "location_bearing": False} for i in range(5)]
    with tempfile.TemporaryDirectory() as td:
        audit_log = pathlib.Path(td) / "audit.jsonl"
        out = pathlib.Path(td) / "out.json"
        runner = Runner(candidate_plan=plan, embedding_fn=failing_emb, db_policy_loader=lambda: policies, protected_set_loader=lambda r,s: tasks, audit_log_path=audit_log)
        # Use set_sha=None to avoid protected_access grant gating, but still exercise audit run_start/run_end lifecycle (set_role dev, set_sha None)
        test_sha = "a"*64
        # For this pure lifecycle test, we use skip_audit=False with a valid sha but we first create a grant via direct audit append to satisfy validate_protected_access if needed
        # Instead, use set_sha=None to cleanly test run_start/run_end without grant complexity; rerun detection still works per (role,sha) pair
        try:
            runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="fail-session", set_role="dev", set_sha=test_sha, audit_log=audit_log, output_path=out, skip_audit=True)
            assert False, "should have raised"
        except Exception as e:
            # When skip_audit=True, no audit events are written — verify output cleaned and no audit
            assert not out.exists(), "output must be removed on failure"
            # Now test with audit enabled but without grant gating (set_sha None) to verify closure
            pass
        # Now audit-enabled failure path — use set_role none (no grant needed) to verify run_start/run_end closure
        audit_log2 = pathlib.Path(td) / "audit2.jsonl"
        out2 = pathlib.Path(td) / "out2.json"
        runner2 = Runner(candidate_plan=plan, embedding_fn=failing_emb, db_policy_loader=lambda: policies, protected_set_loader=lambda r,s: tasks, audit_log_path=audit_log2)
        try:
            runner2.run_dev_evaluation(tasks=tasks, policies=policies, session_id="fail-session2", set_role="none", set_sha=None, audit_log=audit_log2, output_path=out2, skip_audit=False)
            assert False, "should have raised"
        except Exception as e:
            chain = read_and_verify_chain(str(audit_log2))
            assert len(chain) == 2, f"expected 2 audit events on failure, got {len(chain)}: {chain}"
            assert chain[0]["action"] == "run_start"
            assert chain[1]["action"] == "run_end"
            assert not out2.exists(), "output must be removed on failure"
        # Second run with same (role,sha) should be blocked by rerun detection (none/None)
        def good_emb(q):
            h = hashlib.sha256(q.encode()).digest()
            return fake_vec(int.from_bytes(h[:4], "little"))
        runner3 = Runner(candidate_plan=plan, embedding_fn=good_emb, db_policy_loader=lambda: policies, protected_set_loader=lambda r,s: tasks, audit_log_path=audit_log2)
        try:
            runner3.run_dev_evaluation(tasks=tasks, policies=policies, session_id="second-session", set_role="none", set_sha=None, audit_log=audit_log2, output_path=pathlib.Path(td)/"out3.json", skip_audit=False)
            assert False, "rerun should be blocked"
        except RuntimeError as e:
            assert "rerun" in str(e).lower()

def test_execution_lifecycle_path_and_result_os_agnostic():
    import pathlib
    from retrieval_v3.paths import validate_output_path
    from retrieval_v3.result_schema import atomic_write_result, build_result_skeleton
    # Windows backslash traversal must fail even on POSIX host
    try:
        validate_output_path("eval\\retrieval-v3\\results\\..\\..\\etc\\passwd")
        assert False
    except ValueError:
        pass
    # .git with backslash must fail
    try:
        validate_output_path("eval\\retrieval-v3\\results\\..\\.git\\config")
        assert False
    except ValueError:
        pass
    # Canonical path with backslashes should be recognized as canonical via as_posix
    # Use PurePath.as_posix check — ensure atomic_write_result accepts both slash styles for canonical detection (no throw before file existence guard)
    # For temp output, test that atomic_write_result uses as_posix for canonical comparison (pure logic, no real canonical file)
    import tempfile, hashlib, json
    from retrieval_v3.candidate_registry import load_and_validate
    plan = load_and_validate()
    # Build minimal valid result for temp output
    per = [{"config_id": f"candidate-a-{i:02d}", "success_at_5": 0.9, "ndcg_at_5": 0.8, "mrr_at_10": 0.7, "success_at_1": 0.9, "success_at_3": 0.9, "success_at_5_strict_grade3": 0.5, "success_at_5_grade3": 0.5, "ndcg_at_10": 0.8, "n": 5, "success_count": 4, "success_at_1_count": 4, "success_at_3_count": 4, "success_at_5_strict_grade3_count": 2, "oracle_recall": {}, "oracle_recall_all": {}, "union_oracle_R100": 0.9, "slice_diagnostics": {}} for i in range(1,19)]
    sel = {"eligible": ["candidate-a-01"], "eligible_details": per[:1], "chosen": "candidate-a-01", "ordering": "Success@5 desc -> NDCG@5 desc -> MRR@10 desc -> paired p95 asc -> lexicographic config_id asc", "reason": "selected"}
    bg = {"admitted": False, "headroom_pp": 0, "union_recall": 0.9, "reason": "test", "instantiated": False}
    prov = {"candidate_plan_sha256": "a"*64, "prereg_sha256": "b"*64, "git_head": "c"*40, "git_dirty": False, "created_at": "2026-09-02T00:00:00Z"}
    result = build_result_skeleton(per_config_metrics=per, selection=sel, candidate_b_gate=bg, provenance=prov, git_head="c"*40, git_dirty=False, corpus_provenance={"total_policies":5}, set_provenance={"set_role":"dev","set_sha":None,"n":5,"headline_n":5}, audit_head="d"*64)
    with tempfile.TemporaryDirectory() as td:
        out = pathlib.Path(td) / "nested" / "out.json"
        written = atomic_write_result(result, out)
        assert written.exists()
        # Second write to same path must fail (rerun prevention)
        try:
            atomic_write_result(result, out)
            assert False
        except FileExistsError:
            pass
        # Validate that result_schema canonical as_posix check handles backslash canonical without misclassifying temp
        win_path = "eval\\retrieval-v3\\results\\v3-candidate-dev-result.json"
        canon_posix = pathlib.PurePath(win_path).as_posix()
        assert canon_posix == "eval/retrieval-v3/results/v3-candidate-dev-result.json"

def test_mirror_hyphen_underscore_identity():
    # Keep hyphen/underscore touched mirrors byte-identical
    import pathlib, hashlib
    repo = pathlib.Path(__file__).resolve().parents[1]
    touched = ["fusion.py","dedup.py","metrics.py","selection.py","runner.py","dense.py","sparse.py","exact.py","normalization.py","latency.py","candidate_registry.py","result_schema.py","paths.py","audit.py"]
    for name in touched:
        p1 = repo / "eval" / "retrieval-v3" / name
        p2 = repo / "eval" / "retrieval_v3" / name
        if p1.exists() and p2.exists():
            h1 = hashlib.sha256(p1.read_bytes()).hexdigest()
            h2 = hashlib.sha256(p2.read_bytes()).hexdigest()
            assert h1 == h2, f"mirror mismatch {name}: {h1[:8]} vs {h2[:8]}"
def test_headline_no_silent_fallback_safety_only():
    # SAME-STAGE: safety-only tasks must NOT silently become headline; headline stays empty (n=0 -> HOLD).
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
    tasks=[
        {"task_id":"u0","query":"정책 0","golds":[],"stratum":"unsupported_no_answer","location_bearing":False},
        {"task_id":"u1","query":"정책 1","golds":[],"stratum":"unsupported_no_answer","location_bearing":False},
        {"task_id":"a0","query":"정책 2","golds":[{"source":"youth","source_id":"p0","grade":2}],"stratum":"ambiguous","location_bearing":False},
    ]
    with tempfile.TemporaryDirectory() as td:
        audit_log=pathlib.Path(td)/"audit.jsonl"
        out=pathlib.Path(td)/"out.json"
        runner=Runner(candidate_plan=plan, embedding_fn=fake_emb, db_policy_loader=lambda: policies, protected_set_loader=lambda r,s: tasks, audit_log_path=audit_log)
        res=runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="headline-failclosed", set_role="dev", set_sha=None, audit_log=audit_log, output_path=out, skip_audit=True)
        for m in res["per_config_metrics"]:
            assert m["n"] == 0, f"headline must stay empty for safety-only tasks, got n={m['n']}"
            assert m["success_at_5"] == 0.0
        assert res["selection"]["chosen"] is None

def test_gold_missing_grade_fail_closed():
    plan=load_candidate_plan_or_fail()
    def fake_vec(seed):
        rnd=random.Random(seed)
        v=[rnd.uniform(-1,1) for _ in range(768)]
        norm=(sum(x*x for x in v)**0.5)or 1
        return [round(x/norm,6) for x in v]
    policies=[{"id":1,"source":"youth","source_id":"p0","title":"정책 0","support_content":"","summary":"","keywords":"","add_qualify":"","income_etc":"","apply_method":"","org":"고용노동부","chunks":[{"embedding":fake_vec(0),"chunk_index":0,"id":0}]}]
    def fake_emb(q):
        h=hashlib.sha256(q.encode()).digest()
        return fake_vec(int.from_bytes(h[:4],"little"))
    tasks=[{"task_id":"t0","query":"정책 0","golds":[{"source":"youth","source_id":"p0"}],"stratum":"natural_needs","location_bearing":False}]
    with tempfile.TemporaryDirectory() as td:
        audit_log=pathlib.Path(td)/"audit.jsonl"
        out=pathlib.Path(td)/"out.json"
        runner=Runner(candidate_plan=plan, embedding_fn=fake_emb, db_policy_loader=lambda: policies, protected_set_loader=lambda r,s: tasks, audit_log_path=audit_log)
        try:
            runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="gold-grade", set_role="dev", set_sha=None, audit_log=audit_log, output_path=out, skip_audit=True)
            assert False, "missing gold grade must fail-closed"
        except ValueError as e:
            assert "grade" in str(e).lower()

def test_empty_query_fail_closed():
    plan=load_candidate_plan_or_fail()
    def fake_vec(seed):
        rnd=random.Random(seed)
        v=[rnd.uniform(-1,1) for _ in range(768)]
        norm=(sum(x*x for x in v)**0.5)or 1
        return [round(x/norm,6) for x in v]
    policies=[{"id":1,"source":"youth","source_id":"p0","title":"정책 0","support_content":"","summary":"","keywords":"","add_qualify":"","income_etc":"","apply_method":"","org":"고용노동부","chunks":[{"embedding":fake_vec(0),"chunk_index":0,"id":0}]}]
    def fake_emb(q):
        h=hashlib.sha256(q.encode()).digest()
        return fake_vec(int.from_bytes(h[:4],"little"))
    tasks=[{"task_id":"t0","query":"   ","golds":[{"source":"youth","source_id":"p0","grade":2}],"stratum":"natural_needs","location_bearing":False}]
    with tempfile.TemporaryDirectory() as td:
        audit_log=pathlib.Path(td)/"audit.jsonl"
        out=pathlib.Path(td)/"out.json"
        runner=Runner(candidate_plan=plan, embedding_fn=fake_emb, db_policy_loader=lambda: policies, protected_set_loader=lambda r,s: tasks, audit_log_path=audit_log)
        try:
            runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="empty-q", set_role="dev", set_sha=None, audit_log=audit_log, output_path=out, skip_audit=True)
            assert False, "empty query must fail-closed"
        except ValueError as e:
            assert "empty query" in str(e).lower()

def test_latency_no_fabricated_default_static():
    # Static: runner must not fabricate p95 (500.0) nor silently fall back to tasks[0] on id miss.
    import pathlib as _pl
    src=(_pl.Path(__file__).resolve().parent / "retrieval_v3" / "runner.py").read_text(encoding="utf-8")
    assert "500.0" not in src, "fabricated latency default 500.0 forbidden"
    assert ", tasks[0]" not in src, "silent tasks[0] fallback forbidden (fail-closed required)"
    assert "headline_tasks = tasks" not in src
    assert "headline_results = task_results" not in src
    assert "headline_oracle_tasks = oracle_tasks" not in src

def _make_canonical_180():
    from retrieval_v3.runner import DEV_STRATA_EXACT
    strata_order = ["exact_navigation", "natural_needs", "exploratory_multi_valid", "multi_constraint", "short_keywords", "colloquial_typo_spacing_abbrev", "ambiguous", "unsupported_no_answer"]
    tasks = []
    loc_need = 54
    loc_made = 0
    idx = 0
    for s in strata_order:
        for j in range(DEV_STRATA_EXACT[s]):
            loc = loc_made < loc_need and s in ("exact_navigation", "natural_needs", "multi_constraint")
            if loc:
                loc_made += 1
            if s == "unsupported_no_answer":
                golds = []
            elif s == "ambiguous":
                golds = [{"source": "youth", "source_id": f"p{idx}", "grade": 1}]
            else:
                golds = [{"source": "youth", "source_id": f"p{idx}", "grade": 2}]
            tasks.append({"task_id": f"c{idx:03d}", "query": f"query {idx} content", "golds": golds, "stratum": s, "location_bearing": loc if not (s in ("exact_navigation", "natural_needs", "multi_constraint") and not loc and loc_made < loc_need) else loc})
            idx += 1
    # Top up location cross-cutting to exactly 54 across headline strata
    for t in tasks:
        if loc_made >= 54:
            break
        if t["stratum"] in ("exploratory_multi_valid", "short_keywords", "colloquial_typo_spacing_abbrev") and not t["location_bearing"]:
            t["location_bearing"] = True
            loc_made += 1
    return tasks

def test_selection_http_resolution_required():
    per = [{"config_id": "candidate-a-01", "success_at_5": 0.9, "ndcg_at_5": 0.8, "mrr_at_10": 0.7}]
    no_http = {"candidate-a-01": {"unsupported": "PASS", "ambiguous": "PASS", "ineligible_expired": "PASS", "official_link": "PASS", "cost": "PASS"}}
    sel = select_candidate(per, safety_per_config=no_http, latency_p95_per_config={"candidate-a-01": 500})
    assert sel["chosen"] is None, "missing http_resolution must be ineligible (D-039)"
    hold_http = {"candidate-a-01": {"unsupported": "PASS", "ambiguous": "PASS", "ineligible_expired": "PASS", "official_link": "PASS", "http_resolution": "HOLD", "cost": "PASS"}}
    sel2 = select_candidate(per, safety_per_config=hold_http, latency_p95_per_config={"candidate-a-01": 500})
    assert sel2["chosen"] is None
    full = {"candidate-a-01": {"unsupported": "PASS", "ambiguous": "PASS", "ineligible_expired": "PASS", "official_link": "PASS", "http_resolution": "PASS", "cost": "PASS"}}
    sel3 = select_candidate(per, safety_per_config=full, latency_p95_per_config={"candidate-a-01": 500})
    assert sel3["chosen"] == "candidate-a-01"

def test_headline_missing_stratum_not_headline():
    plan = load_candidate_plan_or_fail()
    def fake_vec(seed):
        rnd = random.Random(seed)
        v = [rnd.uniform(-1, 1) for _ in range(768)]
        norm = (sum(x * x for x in v) ** 0.5) or 1
        return [round(x / norm, 6) for x in v]
    policies = [{"id": 1, "source": "youth", "source_id": "p0", "title": "policy 0", "support_content": "", "summary": "", "keywords": "", "add_qualify": "", "income_etc": "", "apply_method": "", "org": "org", "chunks": [{"embedding": fake_vec(0), "chunk_index": 0, "id": 0}]}]
    def fake_emb(q):
        h = hashlib.sha256(q.encode()).digest()
        return fake_vec(int.from_bytes(h[:4], "little"))
    tasks = [
        {"task_id": "m0", "query": "query m0", "golds": [{"source": "youth", "source_id": "p0", "grade": 2}], "location_bearing": False},
        {"task_id": "m1", "query": "query m1", "golds": [{"source": "youth", "source_id": "p0", "grade": 2}], "stratum": "fictional_stratum", "location_bearing": False},
    ]
    with tempfile.TemporaryDirectory() as td:
        audit_log = pathlib.Path(td) / "audit.jsonl"
        out = pathlib.Path(td) / "out.json"
        runner = Runner(candidate_plan=plan, embedding_fn=fake_emb, db_policy_loader=lambda: policies, protected_set_loader=lambda r, s: tasks, audit_log_path=audit_log)
        res = runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="missing-stratum", set_role="dev", set_sha=None, audit_log=audit_log, output_path=out, skip_audit=True)
        for m in res["per_config_metrics"]:
            assert m["n"] == 0, "missing/unknown stratum must never be headline"
        assert res["selection"]["chosen"] is None

def test_headline_empty_golds_fail_closed():
    plan = load_candidate_plan_or_fail()
    def fake_vec(seed):
        rnd = random.Random(seed)
        v = [rnd.uniform(-1, 1) for _ in range(768)]
        norm = (sum(x * x for x in v) ** 0.5) or 1
        return [round(x / norm, 6) for x in v]
    policies = [{"id": 1, "source": "youth", "source_id": "p0", "title": "policy 0", "support_content": "", "summary": "", "keywords": "", "add_qualify": "", "income_etc": "", "apply_method": "", "org": "org", "chunks": [{"embedding": fake_vec(0), "chunk_index": 0, "id": 0}]}]
    def fake_emb(q):
        h = hashlib.sha256(q.encode()).digest()
        return fake_vec(int.from_bytes(h[:4], "little"))
    tasks = [{"task_id": "h0", "query": "query h0", "golds": [], "stratum": "natural_needs", "location_bearing": False}]
    with tempfile.TemporaryDirectory() as td:
        audit_log = pathlib.Path(td) / "audit.jsonl"
        out = pathlib.Path(td) / "out.json"
        runner = Runner(candidate_plan=plan, embedding_fn=fake_emb, db_policy_loader=lambda: policies, protected_set_loader=lambda r, s: tasks, audit_log_path=audit_log)
        try:
            runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="headline-empty-gold", set_role="dev", set_sha=None, audit_log=audit_log, output_path=out, skip_audit=True)
            assert False, "headline empty golds must fail-closed"
        except ValueError as e:
            assert "golds" in str(e).lower()

def test_retrieve_blank_fail_closed_lowest():
    from retrieval_v3.runner import Runner as _R
    plan = load_candidate_plan_or_fail()
    r = _R(candidate_plan=plan)
    cfg = plan["configs"][0]
    for bad in ["", "   ", "  \t "]:
        try:
            r._retrieve_for_query(bad, [], cfg)
            assert False, "blank query must fail at lowest level"
        except ValueError as e:
            assert "empty query" in str(e).lower()

def test_canonical_dev_mode_grant_before_loader_and_counts():
    from retrieval_v3.runner import validate_canonical_dev_tasks
    tasks180 = _make_canonical_180()
    rep = validate_canonical_dev_tasks(tasks180)
    assert rep == {"n": 180, "headline_n": 130, "location_n": 54, "strata": {k: v for k, v in rep["strata"].items()}}
    assert rep["n"] == 180 and rep["headline_n"] == 130 and rep["location_n"] == 54
    plan = load_candidate_plan_or_fail()
    sha = "a" * 64
    called = {"n": 0}
    def loader(role, sh):
        called["n"] += 1
        return tasks180
    with tempfile.TemporaryDirectory() as td:
        audit_log = pathlib.Path(td) / "audit.jsonl"
        runner = Runner(candidate_plan=plan, protected_set_loader=loader, audit_log_path=audit_log)
        try:
            runner.run_dev_evaluation(tasks=[], policies=[], session_id="no-grant", set_role="dev", set_sha=sha, audit_log=audit_log, output_path=None, skip_audit=False)
            assert False, "canonical without grant must fail before loader"
        except RuntimeError as e:
            assert "grant" in str(e).lower()
        assert called["n"] == 0, "loader must never run without grant"
        runner2 = Runner(candidate_plan=plan, protected_set_loader=loader, audit_log_path=audit_log)
        try:
            runner2.run_dev_evaluation(tasks=[{"task_id": "x"}], policies=[], session_id="direct", set_role="dev", set_sha=sha, audit_log=audit_log, output_path=None, skip_audit=False)
            assert False, "canonical direct tasks must be rejected (no fake adapters)"
        except ValueError as e:
            assert "fake adapters" in str(e).lower() or "directly injected" in str(e).lower()

def test_canonical_counts_mismatch_fail_closed():
    from retrieval_v3.runner import validate_canonical_dev_tasks
    try:
        validate_canonical_dev_tasks([{"task_id": "only"}])
        assert False, "wrong n must fail"
    except ValueError as e:
        assert "180" in str(e)
    tasks180 = _make_canonical_180()
    tasks180[0] = dict(tasks180[0], stratum="unsupported_no_answer", golds=[])
    try:
        validate_canonical_dev_tasks(tasks180)
        assert False, "strata drift must fail"
    except ValueError:
        pass

def test_safety_real_interfaces():
    from retrieval_v3.safety import evaluate_full_dev_safety, MockHttpResponse
    got = evaluate_full_dev_safety(None, None, None, None, None, None, None, None, None)
    assert all(v["gate"] == "HOLD" for v in got.values()), "missing evidence must HOLD all six"
    assert set(got) == {"unsupported", "ambiguous", "ineligible_expired", "official_link", "http_resolution", "cost"}
    top5 = {f"t{i:03d}": [("youth", f"p{i}_{k}") for k in range(5)] for i in range(180)}
    emap = {}
    for docs in top5.values():
        for src, sid in docs:
            emap[(src, sid)] = {"eligible": True, "expired": False}
    pin = "b" * 64
    snap = {"sha256": pin, "snapshot_id": "dev-snap", "eligible_map": emap}
    urls = ["https://youth.example/policy", "https://gov24.example/service"]
    exp = {u: ("youth.example" if "youth" in u else "gov24.example") for u in urls}
    mocks = {u: ([MockHttpResponse(status=200)], []) for u in urls}
    full = evaluate_full_dev_safety([True] * 27, [True] * 23, top5, snap, pin, urls, exp, mocks, {"index_ratio": 1.5, "rows_ratio": 2.0, "extra_model_calls": 0})
    assert all(v["gate"] == "PASS" for v in full.values()), f"complete evidence must PASS all six: {full}"

def test_d003_baseline_forbids_candidate_a01():
    import pathlib as _pl
    src = (_pl.Path(__file__).resolve().parent / "retrieval_v3" / "runner.py").read_text(encoding="utf-8")
    assert "d003_baseline_fn" in src
    assert "baseline_cfg = self.plan_data" not in src, "candidate-a-01 must not be baseline"
    assert "D003_BASELINE" in src
    plan = load_candidate_plan_or_fail()
    def fake_vec(seed):
        rnd = random.Random(seed)
        v = [rnd.uniform(-1, 1) for _ in range(768)]
        norm = (sum(x * x for x in v) ** 0.5) or 1
        return [round(x / norm, 6) for x in v]
    policies = [{"id": 1, "source": "youth", "source_id": "p0", "title": "policy 0", "support_content": "", "summary": "", "keywords": "", "add_qualify": "", "income_etc": "", "apply_method": "", "org": "org", "chunks": [{"embedding": fake_vec(0), "chunk_index": 0, "id": 0}]}]
    def fake_emb(q):
        h = hashlib.sha256(q.encode()).digest()
        return fake_vec(int.from_bytes(h[:4], "little"))
    tasks = [{"task_id": f"t{i}", "query": f"query {i}", "golds": [{"source": "youth", "source_id": "p0", "grade": 2}], "stratum": "natural_needs", "location_bearing": False} for i in range(5)]
    with tempfile.TemporaryDirectory() as td:
        cnt = [0]
        def clock():
            cnt[0] += 1000000
            return cnt[0]
        audit_log = pathlib.Path(td) / "audit.jsonl"
        out = pathlib.Path(td) / "out.json"
        runner = Runner(candidate_plan=plan, embedding_fn=fake_emb, db_policy_loader=lambda: policies, protected_set_loader=lambda r, s: tasks, audit_log_path=audit_log, clock_fn=clock)
        res = runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="no-d003", set_role="dev", set_sha=None, audit_log=audit_log, output_path=out, skip_audit=True)
        assert res["selection"]["chosen"] is None, "missing D-003 baseline must HOLD"
        calls = {"n": 0}
        def d003(tid):
            calls["n"] += 1
        audit_log2 = pathlib.Path(td) / "audit2.jsonl"
        out2 = pathlib.Path(td) / "out2.json"
        runner2 = Runner(candidate_plan=plan, embedding_fn=fake_emb, db_policy_loader=lambda: policies, protected_set_loader=lambda r, s: tasks, audit_log_path=audit_log2, clock_fn=clock, d003_baseline_fn=d003)
        runner2.run_dev_evaluation(tasks=tasks, policies=policies, session_id="with-d003", set_role="dev", set_sha=None, audit_log=audit_log2, output_path=out2, skip_audit=True)
        assert calls["n"] > 0, "D-003 baseline fn must be invoked for paired latency"

def test_audit_preflight_no_duplicate_run_start():
    from retrieval_v3 import audit as _audit
    from retrieval_v3.runner import Runner as _R
    plan = load_candidate_plan_or_fail()
    def fake_vec(seed):
        rnd = random.Random(seed)
        v = [rnd.uniform(-1, 1) for _ in range(768)]
        norm = (sum(x * x for x in v) ** 0.5) or 1
        return [round(x / norm, 6) for x in v]
    policies = [{"id": 1, "source": "youth", "source_id": "p0", "title": "policy 0", "support_content": "", "summary": "", "keywords": "", "add_qualify": "", "income_etc": "", "apply_method": "", "org": "org", "chunks": [{"embedding": fake_vec(0), "chunk_index": 0, "id": 0}]}]
    def fake_emb(q):
        h = hashlib.sha256(q.encode()).digest()
        return fake_vec(int.from_bytes(h[:4], "little"))
    tasks = [{"task_id": "t0", "query": "query t0 content", "golds": [{"source": "youth", "source_id": "p0", "grade": 2}], "stratum": "natural_needs", "location_bearing": False}]
    with tempfile.TemporaryDirectory() as td:
        audit_log = pathlib.Path(td) / "audit.jsonl"
        runner = _R(candidate_plan=plan, embedding_fn=fake_emb, db_policy_loader=lambda: policies, protected_set_loader=lambda r, s: tasks, audit_log_path=audit_log)
        runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="preflight", set_role="none", set_sha=None, audit_log=audit_log, output_path=None, skip_audit=False)
        chain1 = _audit.read_and_verify_chain(str(audit_log))
        assert [e["action"] for e in chain1] == ["run_start", "run_end"], "first run actions must be exactly [run_start, run_end]"
        try:
            runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="preflight", set_role="none", set_sha=None, audit_log=audit_log, output_path=None, skip_audit=False)
            assert False, "second run_start must be blocked by preflight"
        except RuntimeError as e:
            assert "rerun" in str(e).lower() or "preflight" in str(e).lower()
        chain2 = _audit.read_and_verify_chain(str(audit_log))
        assert [e["action"] for e in chain2] == ["run_start", "run_end"], "rerun actions must remain exactly [run_start, run_end]"

def test_audit_windows_lock_serialized():
    from retrieval_v3 import audit as _audit
    import threading
    with tempfile.TemporaryDirectory() as td:
        log = pathlib.Path(td) / "audit.jsonl"
        errs = []
        def w(i):
            try:
                _audit.append_event(str(log), action="run_start", set_role="none", session_id=f"lock-{i}")
            except Exception as e:
                errs.append(e)
        ths = [threading.Thread(target=w, args=(i,)) for i in range(4)]
        for t in ths:
            t.start()
        for t in ths:
            t.join()
        assert not errs, f"serialized appends must all succeed: {errs[:1]}"
        chain = _audit.read_and_verify_chain(str(log))
        assert len(chain) == 4
        assert not pathlib.Path(str(log) + ".lock").exists(), "lockfile must be released"

def test_path_sibling_rejected():
    from retrieval_v3.paths import validate_output_path, REPO_ROOT
    sibling = REPO_ROOT.parent / (REPO_ROOT.name + "-escape") / "eval" / "retrieval-v3" / "results" / "o.json"
    try:
        validate_output_path(sibling, strict_canonical=False)
        assert False, "benefit-compass-escape sibling must be rejected (component-aware)"
    except ValueError:
        pass
    ok = REPO_ROOT / "eval" / "retrieval-v3" / "results" / "o.json"
    validate_output_path(ok, strict_canonical=False)

def test_candidate_b_no_finalist_not_evaluated():
    import pathlib as _pl
    src = (_pl.Path(__file__).resolve().parent / "retrieval_v3" / "runner.py").read_text(encoding="utf-8")
    assert "not_evaluated" in src
    assert "max_union" not in src and "max_success" not in src, "max-of-all B fallback forbidden"
    plan = load_candidate_plan_or_fail()
    def fake_vec(seed):
        rnd = random.Random(seed)
        v = [rnd.uniform(-1, 1) for _ in range(768)]
        norm = (sum(x * x for x in v) ** 0.5) or 1
        return [round(x / norm, 6) for x in v]
    policies = [{"id": 1, "source": "youth", "source_id": "p0", "title": "policy 0", "support_content": "", "summary": "", "keywords": "", "add_qualify": "", "income_etc": "", "apply_method": "", "org": "org", "chunks": [{"embedding": fake_vec(0), "chunk_index": 0, "id": 0}]}]
    def fake_emb(q):
        h = hashlib.sha256(q.encode()).digest()
        return fake_vec(int.from_bytes(h[:4], "little"))
    tasks = [{"task_id": "t0", "query": "query t0 content", "golds": [{"source": "youth", "source_id": "p0", "grade": 2}], "stratum": "natural_needs", "location_bearing": False}]
    with tempfile.TemporaryDirectory() as td:
        audit_log = pathlib.Path(td) / "audit.jsonl"
        out = pathlib.Path(td) / "out.json"
        runner = Runner(candidate_plan=plan, embedding_fn=fake_emb, db_policy_loader=lambda: policies, protected_set_loader=lambda r, s: tasks, audit_log_path=audit_log)
        res = runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="b-none", set_role="dev", set_sha=None, audit_log=audit_log, output_path=out, skip_audit=True)
        assert res["selection"]["chosen"] is None
        bg = res["candidate_b_gate"]
        assert bg["admitted"] is False and bg["instantiated"] is False and bg.get("status") == "not_evaluated"

def test_canonical_result_n_headline():
    from retrieval_v3.result_schema import validate_complete_result
    from retrieval_v3.candidate_registry import EXPECTED_SHA, EXPECTED_PREREG_SHA
    per = [{"config_id": f"candidate-a-{i:02d}", "success_at_5": 0.9, "ndcg_at_5": 0.8, "mrr_at_10": 0.7} for i in range(1, 19)]
    base = {"schema_version": 1, "git_head": "0" * 40, "git_dirty": False, "candidate_plan_sha256": EXPECTED_SHA, "prereg_sha256": EXPECTED_PREREG_SHA, "provenance": {"candidate_plan_sha256": EXPECTED_SHA, "prereg_sha256": EXPECTED_PREREG_SHA}, "per_config_metrics": per, "selection": {"chosen": None}, "candidate_b_gate": {"admitted": False, "instantiated": False, "status": "not_evaluated"}}
    bad = dict(base, set_provenance={"set_role": "dev", "set_sha": "1" * 64, "n": 5, "headline_n": 5})
    try:
        validate_complete_result(bad)
        assert False, "canonical n/headline mismatch must fail"
    except ValueError as e:
        assert "180" in str(e) or "130" in str(e)
    ok = dict(base, set_provenance={"set_role": "dev", "set_sha": "1" * 64, "n": 180, "headline_n": 130})
    validate_complete_result(ok)

def test_protected_access_end_exact_outcome():
    from retrieval_v3 import audit as _audit
    with tempfile.TemporaryDirectory() as td:
        log = pathlib.Path(td) / "audit.jsonl"
        sha = "c" * 64
        _audit.append_event(str(log), action="protected_access_start", set_role="dev", set_sha=sha, session_id="s1", outcome="success")
        try:
            _audit.append_event(str(log), action="protected_access_end", set_role="dev", set_sha=sha, session_id="s1")
            assert False, "end without outcome must fail"
        except Exception:
            pass
        _audit.append_event(str(log), action="protected_access_end", set_role="dev", set_sha=sha, session_id="s1", outcome="failure")
        try:
            _audit.verify_holdout_access_allowed(str(log), set_role="dev", set_sha=sha, session_id="s1")
            assert False, "closed grant must be denied"
        except Exception:
            pass

if __name__=="__main__":
    tests=[test_18_configs_and_drift, test_non_unit_cosine, test_representative_tie_and_near_tie, test_strict_gt_dedup_boundary, test_mmr_actual_cosine_and_full_top30, test_exact_normalization_and_boundaries, test_cosine_min_placement, test_union_vs_hybrid, test_exact_not_injected, test_deterministic_ordering, test_metrics_mrr_rank_gt10, test_selection_ordering_and_zero, test_b_gate_no_impl, test_latency_harness, test_audit_lifecycle, test_atomic_rerun_concurrent, test_path_confinement, test_runner_safety_hold_when_checkers_absent, test_runner_safety_hold_even_with_checkers_pre_dev, test_runner_latency_wiring, test_cli_orchestrator_e2e, test_fusion_youth_bias_only_youth_source_gov24_zero, test_sparse_only_representative_query_nearest_no_chunk0_fallback, test_oracle_union_set_and_headline130, test_metrics_graded_strict_and_ndcg, test_metrics_equivalence_group_no_double_count, test_slice_diagnostics_unavailable, test_selection_fail_closed_missing_gates, test_selection_fail_closed_missing_latency, test_execution_lifecycle_audit_closure_on_failure, test_execution_lifecycle_path_and_result_os_agnostic, test_headline_no_silent_fallback_safety_only, test_gold_missing_grade_fail_closed, test_empty_query_fail_closed, test_latency_no_fabricated_default_static, test_mirror_hyphen_underscore_identity, test_selection_http_resolution_required, test_headline_missing_stratum_not_headline, test_headline_empty_golds_fail_closed, test_retrieve_blank_fail_closed_lowest, test_canonical_dev_mode_grant_before_loader_and_counts, test_canonical_counts_mismatch_fail_closed, test_safety_real_interfaces, test_d003_baseline_forbids_candidate_a01, test_audit_preflight_no_duplicate_run_start, test_audit_windows_lock_serialized, test_path_sibling_rejected, test_candidate_b_no_finalist_not_evaluated, test_canonical_result_n_headline, test_protected_access_end_exact_outcome]
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception as e:
            print(f"FAIL {t.__name__}: {e}")
            import traceback; traceback.print_exc()
            sys.exit(1)
    print("ALL 50 focused tests PASS")
