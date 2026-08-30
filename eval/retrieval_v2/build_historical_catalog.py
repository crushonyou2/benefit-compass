"""Historical protected-set fingerprint catalog builder (Cycle3, D-011)."""
from __future__ import annotations
import datetime, hashlib, json, os, pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / "eval"))
from retrieval_v2.cycle3_fingerprint import FINGERPRINT_VERSION, NORMALIZATION_SPEC, gold_fingerprint, query_fingerprint, validate_fingerprint_manifest, manifest_with_fingerprints, check_overlap
from retrieval_v2.cycle3_audit import append_event, read_and_verify_chain
CATALOG_DIR = ROOT / "eval" / "retrieval-v2" / "cycle3" / "catalog"
AUDIT_LOG = ROOT / "eval" / "retrieval-v2" / "cycle3" / "audit" / "events.jsonl"
SESSION_ID = f"catalog-freeze-20260831-{os.getpid()}"
def _git_head(): return subprocess.check_output(["git","rev-parse","HEAD"], cwd=str(ROOT)).decode().strip().lower()
def _lf_sha(data: bytes): return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()
def _lf_sha_file(p: pathlib.Path): return _lf_sha(p.read_bytes())
def _git_show_bytes(ref: str):
    r=subprocess.run(["git","show",ref], capture_output=True, check=False)
    if r.returncode!=0: raise RuntimeError(f"git show failed {ref}: {r.stderr.decode('utf-8', errors='replace')[:500]}")
    if not r.stdout: raise RuntimeError(f"git show empty {ref}")
    return r.stdout
def _load_jsonl_bytes(data: bytes):
    items=[]
    for line in data.decode("utf-8").splitlines():
        if not line.strip(): continue
        items.append(json.loads(line))
    return items
def _append_protected_start(role, sha, outcome="success"):
    return append_event(AUDIT_LOG, action="protected_access_start", set_role=role, set_sha=sha, session_id=SESSION_ID, outcome=outcome, candidate_id=None, command="build_historical_catalog", runner_id="historical-catalog-builder")
def _append_protected_end(role, sha, outcome="success"):
    return append_event(AUDIT_LOG, action="protected_access_end", set_role=role, set_sha=sha, session_id=SESSION_ID, outcome=outcome, candidate_id=None, command="build_historical_catalog", runner_id="historical-catalog-builder")
def build():
    CATALOG_DIR.mkdir(parents=True, exist_ok=True)
    git_head=_git_head()
    git_dirty=bool(subprocess.check_output(["git","status","--porcelain"], cwd=str(ROOT)).decode().strip())
    generated_at=datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z")
    read_and_verify_chain(AUDIT_LOG)
    historical_sets=[]
    # P0
    p0_youth_path=ROOT/"eval"/"evalset.jsonl"; p0_gov24_path=ROOT/"eval"/"expansion_evalset.jsonl"; p0_manifest_path=ROOT/"eval"/"canonical_manifest.json"
    p0_youth_sha=_lf_sha_file(p0_youth_path); p0_gov24_sha=_lf_sha_file(p0_gov24_path); p0_manifest_sha=_lf_sha_file(p0_manifest_path)
    append_event(AUDIT_LOG, action="run_start", set_role="none", set_sha=None, session_id=SESSION_ID, outcome="success", candidate_id=None, command="build_historical_catalog:p0", runner_id="historical-catalog-builder")
    p0_items=[]
    for line in p0_youth_path.read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        j=json.loads(line)
        if "gold_source" not in j or j["gold_source"] is None: j["gold_source"]="youth"
        p0_items.append(j)
    for line in p0_gov24_path.read_text(encoding="utf-8").splitlines():
        if not line.strip(): continue
        j=json.loads(line); p0_items.append(j)
    assert len(p0_items)==81
    p0_qfps=[query_fingerprint(it["query"]) for it in p0_items]
    p0_gfps=[gold_fingerprint(it["gold_source"], str(it["gold_source_id"])) for it in p0_items]
    p0_manifest=manifest_with_fingerprints(role="p0", cycle=0, cases=81, query_fingerprints=p0_qfps, gold_fingerprints=p0_gfps, extra={"id":"p0","display_name":"P0 canonical (Youth 60 + Gov24 21)","provenance":{"decision":"D-002/D-007","manifest_file":"eval/canonical_manifest.json","manifest_sha256":p0_manifest_sha,"manifest_sha256_basis":"utf8_text_lf_normalized","youth_evalset":"eval/evalset.jsonl","youth_sha256":p0_youth_sha,"gov24_evalset":"eval/expansion_evalset.jsonl","gov24_sha256":p0_gov24_sha,"sha256_basis":"utf8_text_lf_normalized","evaluator_commit":"58dff80d41be9f60b60b8ea7858a839f90d8563b","note":"Youth 60 gold_source inferred as youth where missing; Gov24 21 explicit gov24"},"generated_at":generated_at,"git_head":git_head})
    validate_fingerprint_manifest(p0_manifest); (CATALOG_DIR/"p0.json").write_text(json.dumps(p0_manifest, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8"); historical_sets.append(("p0", p0_manifest, 81))
    # hard-negative
    hn_path=ROOT/"eval"/"expansion_api_evalset.jsonl"; hn_sha=_lf_sha_file(hn_path)
    append_event(AUDIT_LOG, action="run_start", set_role="none", set_sha=None, session_id=SESSION_ID, outcome="success", candidate_id=None, command="build_historical_catalog:hard_negative", runner_id="historical-catalog-builder")
    hn_items_raw=[json.loads(l) for l in hn_path.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(hn_items_raw)==36
    hn_qfps=[]; hn_gfps=[]
    for it in hn_items_raw:
        q=it["query"]; hn_qfps.append(query_fingerprint(q))
        if it.get("gold_source") and it.get("gold_source_id"):
            hn_gfps.append(gold_fingerprint(str(it["gold_source"]), str(it["gold_source_id"])))
        elif it.get("excluded_source") and it.get("excluded_source_id"):
            qfp=query_fingerprint(q)
            synthetic_id=f"hard_negative_ineligible_{it['excluded_source_id']}_{qfp[:8]}"
            hn_gfps.append(gold_fingerprint("gov24", synthetic_id))
        else:
            qfp=query_fingerprint(q)
            synthetic_id=f"hard_negative_no_answer_{qfp[:16]}"
            hn_gfps.append(gold_fingerprint("gov24", synthetic_id))
    assert len(hn_qfps)==len(set(s.lower() for s in hn_qfps)), "hn query duplicate"
    assert len(hn_gfps)==len(set(s.lower() for s in hn_gfps)), "hn gold duplicate"
    hn_manifest=manifest_with_fingerprints(role="hard_negative", cycle=0, cases=36, query_fingerprints=hn_qfps, gold_fingerprints=hn_gfps, extra={"id":"hard_negative","display_name":"hard-negative 36 (pure 21 + ineligible 3 + no_answer 12) — gold placeholder for no-gold cases","provenance":{"decision":"D-007","evalset":"eval/expansion_api_evalset.jsonl","sha256":hn_sha,"sha256_basis":"utf8_text_lf_normalized","canonical_artifact":"eval/canonical_hard_negative_36_production_parity.json","canonical_artifact_sha256":_lf_sha_file(ROOT/"eval"/"canonical_hard_negative_36_production_parity.json"),"manifest_file":"eval/canonical_manifest.json","manifest_sha256":p0_manifest_sha,"slices":{"pure_positive":21,"ineligible":3,"no_answer":12},"gold_handling":"gold_source/gold_source_id where present; synthetic gov24+hash for ineligible/no_answer to avoid duplicate and satisfy 36/36 (pure gold already protects real policy id)"},"generated_at":generated_at,"git_head":git_head})
    validate_fingerprint_manifest(hn_manifest); (CATALOG_DIR/"hard_negative.json").write_text(json.dumps(hn_manifest, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8"); historical_sets.append(("hard_negative", hn_manifest, 36))
    def process_cycle_set(set_id, role, cycle, ref_path, sha_expected, display_name, provenance_extra):
        ev_start=_append_protected_start(role, sha_expected, outcome="success")
        from retrieval_v2.cycle3_audit import verify_holdout_access_allowed
        verify_holdout_access_allowed(AUDIT_LOG, set_role=role, set_sha=sha_expected, session_id=SESSION_ID, expected_event_hash=ev_start["event_hash"])
        data=_git_show_bytes(ref_path)
        actual_sha=_lf_sha(data)
        if actual_sha!=sha_expected.lower(): raise ValueError(f"SHA mismatch for {set_id}: expected {sha_expected} got {actual_sha}")
        items=_load_jsonl_bytes(data)
        qfps=[query_fingerprint(it["query"]) for it in items]
        gfps=[gold_fingerprint(str(it["gold_source"]), str(it["gold_source_id"])) for it in items]
        cases=len(items)
        manifest=manifest_with_fingerprints(role=role, cycle=cycle, cases=cases, query_fingerprints=qfps, gold_fingerprints=gfps, extra={"id":set_id,"display_name":display_name,"provenance":provenance_extra,"generated_at":generated_at,"git_head":git_head})
        validate_fingerprint_manifest(manifest)
        (CATALOG_DIR/f"{set_id}.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")
        _append_protected_end(role, sha_expected, outcome="success")
        historical_sets.append((set_id, manifest, cases))
        return manifest
    c1_dev_sha="e9510203cb26bb9db5598b1cd284398ba226460437a396e72906aa6505aff56e"
    process_cycle_set("cycle1_dev","dev",1,"12515a20758265b0b5a5f52acef5aa40de3b6253:eval/retrieval-v2/dev/evalset.jsonl",c1_dev_sha,"Cycle1 dev 36 (Youth 18 / Gov24 18)",{"decision":"D-007","ref":"12515a20758265b0b5a5f52acef5aa40de3b6253","tag":"retrieval-v2-holdout-v1 (also contains dev)","tag_object":"12515a20758265b0b5a5f52acef5aa40de3b6253","path":"eval/retrieval-v2/dev/evalset.jsonl","sha256":c1_dev_sha,"sha256_basis":"utf8_text_lf_normalized","cases":36,"balance":{"youth":18,"gov24":18},"manifest":"eval/retrieval-v2/dev/manifest.json"})
    c1_holdout_sha="02eb03866f8e09b66ea7c3b83856fe939ee0b966350053277aaca3f2d7121eda"
    process_cycle_set("cycle1_holdout","holdout",1,"12515a20758265b0b5a5f52acef5aa40de3b6253:eval/retrieval-v2/holdout/evalset.jsonl",c1_holdout_sha,"Cycle1 holdout 40 (Youth 20 / Gov24 20)",{"decision":"D-007","ref":"12515a20758265b0b5a5f52acef5aa40de3b6253","tag":"retrieval-v2-holdout-v1","path":"eval/retrieval-v2/holdout/evalset.jsonl","sha256":c1_holdout_sha,"sha256_basis":"utf8_text_lf_normalized","cases":40,"balance":{"youth":20,"gov24":20},"manifest":"eval/retrieval-v2/holdout/manifest.json"})
    c2_dev_sha="c8b66fef69bdfd0db053ac7cac0fb027fc3271c6072ab992b622cacdc71ace5e"
    process_cycle_set("cycle2_dev","dev",2,"372ed686579b4e8e2b9854d297e44fee18775352:eval/retrieval-v2/cycle2/dev/evalset.jsonl",c2_dev_sha,"Cycle2 dev 36 (Youth 18 / Gov24 18, balanced 6x6)",{"decision":"D-009/D-010 (retained as tuning set)","ref":"372ed686579b4e8e2b9854d297e44fee18775352","tag":"retrieval-v2-cycle2-dev-v1","tag_object":"500beadae11ddb423cc2ea4d46494c0a9f2b1173","path":"eval/retrieval-v2/cycle2/dev/evalset.jsonl","sha256":c2_dev_sha,"sha256_basis":"utf8_text_lf_normalized","cases":36,"manifest":"eval/retrieval-v2/cycle2/dev/manifest.json"})
    c2_holdout_sha="cf003bab7713138fbd9c4622addeeb886c01f401aeab3d43b1144ae6e4c79727"
    process_cycle_set("cycle2_holdout_disqualified","holdout",2,"9e2cd6ea4b8203b474d7d6a6a69a088763284043:eval/retrieval-v2/cycle2/holdout/evalset.jsonl",c2_holdout_sha,"Cycle2 disqualified holdout 40 (Youth 20 / Gov24 20) — D-010 disqualified for final evaluation but historical protected",{"decision":"D-009/D-010 (disqualified for final evaluation, immutable history)","ref":"9e2cd6ea4b8203b474d7d6a6a69a088763284043","tag":"retrieval-v2-cycle2-holdout-v1","tag_object":"03da4cc28d1bb324f5176efb500dfeaa1684b3fa","path":"eval/retrieval-v2/cycle2/holdout/evalset.jsonl","sha256":c2_holdout_sha,"sha256_basis":"utf8_text_lf_normalized","cases":40,"disqualified_reason":"HARD SEAL violation post-tuning candidate session process-level git show (D-010)"})
    for sid,m,_ in historical_sets: validate_fingerprint_manifest(m)
    all_q=set(); all_g=set()
    for _,m,_ in historical_sets:
        all_q.update(s.lower() for s in m["query_fingerprints"]); all_g.update(s.lower() for s in m["gold_fingerprints"])
    union_q_sorted=sorted(all_q); union_g_sorted=sorted(all_g)
    pairs=[]; overall_pass=True
    for i in range(len(historical_sets)):
        for j in range(i+1, len(historical_sets)):
            a_id,a_m,_=historical_sets[i]; b_id,b_m,_=historical_sets[j]
            res=check_overlap(a_m,b_m,strict=False)
            expected=False; note=""
            if {a_id,b_id}=={"p0","hard_negative"}:
                if res["query_overlap"]==21 and res["gold_overlap"]==21:
                    expected=True; note="expected: hard_negative pure 21 reuses Gov24 21 queries/golds; allowed per design, not fail-closed"
                else: note=f"unexpected counts for p0 vs hard_negative: q{res['query_overlap']} g{res['gold_overlap']}"; overall_pass=False
            else:
                if res["query_overlap"]!=0 or res["gold_overlap"]!=0: overall_pass=False; note="FAIL: overlap must be 0 per existing contract"
                else: note="pass: 0 overlap"
            pairs.append({"a":a_id,"b":b_id,"query_overlap":res["query_overlap"],"gold_overlap":res["gold_overlap"],"query_examples":res["query_overlap_examples"],"gold_examples":res["gold_overlap_examples"],"status":"expected_allowed" if expected else ("pass" if (res["query_overlap"]==0 and res["gold_overlap"]==0) else "FAIL"),"note":note})
            if (res["query_overlap"]!=0 or res["gold_overlap"]!=0) and not expected: print(f"WARNING overlap {a_id} vs {b_id}: q{res['query_overlap']} g{res['gold_overlap']}")
    if not overall_pass: raise ValueError(f"historical inter-set overlap fail-closed: {pairs}")
    catalog={"catalog_version":"v1","fingerprint_version":FINGERPRINT_VERSION,"normalization_spec":NORMALIZATION_SPEC,"generated_at":generated_at,"git_head":git_head,"git_dirty":git_dirty,"decision":"D-011","description":"Historical protected-set fingerprint catalog — fingerprint-only, no plaintext. Fresh builders can read this single file (or catalog dir) to enforce overlap 0 without reopening protected plaintext.","historical_sets":[{"id":sid,"role":m.get("role"),"cycle":m.get("cycle"),"cases":m["cases"],"provenance":m.get("provenance") or m.get("extra",{}).get("provenance"),"manifest_path":f"{sid}.json","query_count":len(m["query_fingerprints"]),"gold_count":len(m["gold_fingerprints"]),"sha256":m.get("sha256")} for sid,m,_ in historical_sets],"union":{"query_fingerprints":union_q_sorted,"gold_fingerprints":union_g_sorted,"query_count":len(union_q_sorted),"gold_count":len(union_g_sorted),"query_union_hash":hashlib.sha256("".join(union_q_sorted).encode()).hexdigest() if union_q_sorted else None,"gold_union_hash":hashlib.sha256("".join(union_g_sorted).encode()).hexdigest() if union_g_sorted else None,"note":"Union of all historical query/gold fingerprints (deduped by hex lower). Fresh dev/holdout must have 0 overlap with this union (both query and gold). P0 vs hard_negative 21 overlap already deduped in union."},"inter_overlap":{"pairs":pairs,"overall_pass":True,"expected_allowed_pair":"p0 vs hard_negative 21/21 is expected Gov24 reuse, not a violation"},"entrypoint":"catalog.json","catalog_dir":"eval/retrieval-v2/cycle3/catalog","loader":"eval/retrieval_v2/cycle3_historical_catalog.py","fingerprint_helper":"eval/retrieval_v2/cycle3_fingerprint.py","audit":{"log_path":str(AUDIT_LOG.relative_to(ROOT)),"session_id":SESSION_ID,"events":[e for e in read_and_verify_chain(AUDIT_LOG) if e.get("session_id")==SESSION_ID],"chain_verified":True,"schema_limitation":"P0/hard-negative use set_role none run events (existing schema has no p0/hard_negative role); no false dev/holdout role used; plaintext-free run event + catalog provenance used instead — documented per stage spec"},"usage":{"fresh_builder_single_file":"read eval/retrieval-v2/cycle3/catalog/catalog.json and use union.query_fingerprints / union.gold_fingerprints for check_overlap without plaintext","fresh_builder_dir":"or read all *.json per-set manifests in catalog dir","helper_example":"from retrieval_v2.cycle3_historical_catalog import load_historical_catalog, get_union, check_fresh_no_overlap; catalog=load_historical_catalog(); check_fresh_no_overlap(fresh_manifest, catalog)"},"counts":{sid:m["cases"] for sid,m,_ in historical_sets},"counts_detail":{"p0":81,"cycle1_dev":36,"cycle1_holdout":40,"cycle2_dev":36,"cycle2_holdout_disqualified":40,"hard_negative":36,"union_query":len(union_q_sorted),"union_gold":len(union_g_sorted),"sum_cases_query":sum(m["cases"] for _,m,_ in historical_sets),"sum_cases_gold":sum(m["cases"] for _,m,_ in historical_sets)}}
    (CATALOG_DIR/"catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2, sort_keys=True)+"\n", encoding="utf-8")
    for p in CATALOG_DIR.iterdir():
        if p.suffix==".json":
            txt=p.read_text(encoding="utf-8")
            if "의성군" in txt: raise ValueError(f"plaintext leak in {p}")
            data=json.loads(txt)
            if p.name=="catalog.json":
                for fp in data["union"]["query_fingerprints"]:
                    if not isinstance(fp,str) or len(fp)!=64 or not all(c in "0123456789abcdef" for c in fp.lower()): raise ValueError(f"invalid union query fp {fp}")
            else: validate_fingerprint_manifest(data)
    verified=read_and_verify_chain(AUDIT_LOG)
    print(f"Catalog built: {len(historical_sets)} sets, union q {len(union_q_sorted)} g {len(union_g_sorted)}")
    print(f"Audit events for this session: {len([e for e in verified if e.get('session_id')==SESSION_ID])}")
    return catalog
if __name__=="__main__": build()
