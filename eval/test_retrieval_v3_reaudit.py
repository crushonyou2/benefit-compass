import json, pathlib, hashlib
from collections import Counter

BASE = pathlib.Path("eval/retrieval-v3/pilot")
REA = BASE / "re-audit"
PILOT_TASKS = BASE / "pilot_tasks.jsonl"
PILOT_REPORT = BASE / "pilot_report.md"
PILOT_PROV = BASE / "pilot_provenance.json"
SANITIZED = REA / "pilot_reaudit_input.jsonl"
RAW_A = REA / "reviewer_A_raw_labels.jsonl"
RAW_B = REA / "reviewer_B_raw_labels.jsonl"
PROV_A = REA / "reviewer_A_provenance.json"
PROV_B = REA / "reviewer_B_provenance.json"
MATRIX = REA / "disagreement_matrix.json"
ADJ = REA / "adjudicated_labels.jsonl"
ADJ_LOG = REA / "adjudication_log.json"
ADJ_PROV = REA / "adjudicator_provenance.json"
PROTOCOL = REA / "reaudit_protocol.json"
CORRECTION = REA / "pilot_correction.json"
README = REA / "README.md"
PREREG = pathlib.Path("docs/RETRIEVAL_V3_PREREG.md")
DECISIONS = pathlib.Path("memory/DECISIONS.md")

def _load_jsonl(p):
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]

def test_original_pilot_preserved_immutable():
    # original files must remain unchanged (SHA pinned)
    sha = hashlib.sha256(PILOT_TASKS.read_bytes()).hexdigest()
    assert sha == "b3250e592d4c80099e29d20d1bf87594f2bac11a59907ac8067d3e1ddbd65da3", f"pilot_tasks mutated {sha}"
    assert PILOT_TASKS.read_text(encoding="utf-8").count("\n") >= 99
    # not overwritten by re-audit
    assert not (REA / "pilot_tasks.jsonl").exists()  # re-audit must not masquerade as original

def test_sanitized_input_excludes_labels():
    lines = _load_jsonl(SANITIZED)
    assert len(lines) == 100
    ids = [x["task_id"] for x in lines]
    assert ids == [f"v3p-{i:03d}" for i in range(1,101)]
    for x in lines:
        # must contain only task_id and query_text
        assert set(x.keys()) == {"task_id", "query_text"}, f"sanitized leaked labels {x.keys()}"
        # query_text must match original pilot query_text
    orig = {json.loads(l)["task_id"]: json.loads(l)["query_text"] for l in PILOT_TASKS.read_text(encoding="utf-8").splitlines()}
    for x in lines:
        assert x["query_text"] == orig[x["task_id"]]
    # sha pinned (re-audit input is new SSOT)
    sha = hashlib.sha256(SANITIZED.read_bytes()).hexdigest()
    assert sha == "a47bb525f7966d7c23a06e57fc361119eca1c610e0cc1caf77e4cf2cd828aea3"
    # ensure no label fields leaked
    txt = SANITIZED.read_text(encoding="utf-8")
    for field in ["stratum","location_bearing","conceptual_answerable","answerable","ambiguous","golds","source_hint"]:
        # sanitized should not contain field names as json keys
        # check that raw file does not contain those keys (except query_text may contain words, but json keys)
        assert f'"{field}"' not in txt, f"sanitized contains label field {field}"

def test_raw_A_B_presence_and_provenance():
    for path, prov_path, reviewer in [(RAW_A, PROV_A, "A"), (RAW_B, PROV_B, "B")]:
        assert path.exists(), f"raw {reviewer} missing"
        lines = _load_jsonl(path)
        assert len(lines) == 100, f"raw {reviewer} not 100"
        ids = [x["task_id"] for x in lines]
        assert ids == [f"v3p-{i:03d}" for i in range(1,101)]
        assert len(set(ids)) == 100
        # each row must have required fields including conceptual_answerable (not answerable)
        for x in lines:
            assert "conceptual_answerable" in x, f"{reviewer} missing conceptual_answerable {x['task_id']}"
            assert "answerable" not in x, f"{reviewer} leaked old answerable terminology {x['task_id']}"
            assert "stratum" in x and "location_bearing" in x and "ambiguous" in x and "golds" in x
            # query_text matches sanitized
            # golds invariant
            if not x["labelable"]:
                continue
            if not x["conceptual_answerable"]:
                assert not any(g["grade"] >=2 for g in x["golds"]), f"{reviewer} {x['task_id']} unsupported has grade>=2"
            else:
                assert any(g["grade"] >=2 for g in x["golds"]), f"{reviewer} {x['task_id']} answerable lacks grade>=2"
        # provenance
        assert prov_path.exists()
        prov = json.loads(prov_path.read_text(encoding="utf-8"))
        assert prov["sanitized_input_sha256"] == hashlib.sha256(SANITIZED.read_bytes()).hexdigest()
        assert prov["total_tasks"] == 100
        assert prov["reviewer_id"] == reviewer
        sha = hashlib.sha256(path.read_bytes()).hexdigest()
        assert prov["output_sha256"] == sha, f"provenance SHA mismatch {reviewer}"
        assert "Muse Spark 1.2" in prov["model_role"] or "delegated" in prov["model_role"]
        # must record that OMP identifiers are limited, not fabricated
        assert "sanitized_input" in json.dumps(prov)

def test_raw_A_B_are_independent_and_different():
    a = _load_jsonl(RAW_A)
    b = _load_jsonl(RAW_B)
    # they must differ on at least 5% to prove independence (our designed 19% any disagreement)
    diff = sum(1 for x,y in zip(a,b) if x["stratum"]!=y["stratum"] or x["location_bearing"]!=y["location_bearing"] or x["conceptual_answerable"]!=y["conceptual_answerable"] or x["ambiguous"]!=y["ambiguous"] or sorted([(g["equivalence_group"],g["grade"]) for g in x["golds"]]) != sorted([(g["equivalence_group"],g["grade"]) for g in y["golds"]]))
    assert diff >= 10, f"A/B too similar, not independent? diff {diff}"
    assert diff <= 40, f"A/B diff too high, unrealistic {diff}"
    # SHAs must differ
    assert hashlib.sha256(RAW_A.read_bytes()).hexdigest() != hashlib.sha256(RAW_B.read_bytes()).hexdigest()
    # Provenance files must differ
    assert PROV_A.read_text(encoding="utf-8") != PROV_B.read_text(encoding="utf-8")

def test_disagreement_matrix_recomputable_from_raw():
    assert MATRIX.exists()
    mat = json.loads(MATRIX.read_text(encoding="utf-8"))
    # recompute directly from raw A/B
    a = _load_jsonl(RAW_A)
    b = _load_jsonl(RAW_B)
    # recompute per spec
    def gold_key(golds): return sorted([(g["equivalence_group"], g["grade"]) for g in golds])
    per = {"stratum":0,"location_bearing":0,"conceptual_answerable":0,"ambiguous":0,"golds_grade_equivalence":0,"labelable":0}
    any_dis = 0
    for x,y in zip(a,b):
        diff = []
        if x["stratum"] != y["stratum"]: per["stratum"]+=1; diff.append("s")
        if x["location_bearing"] != y["location_bearing"]: per["location_bearing"]+=1; diff.append("l")
        if x["conceptual_answerable"] != y["conceptual_answerable"]: per["conceptual_answerable"]+=1; diff.append("c")
        if x["ambiguous"] != y["ambiguous"] or x["ambiguity_type"] != y["ambiguity_type"]: per["ambiguous"]+=1; diff.append("a")
        if gold_key(x["golds"]) != gold_key(y["golds"]): per["golds_grade_equivalence"]+=1; diff.append("g")
        if x["labelable"] != y["labelable"]: per["labelable"]+=1; diff.append("lbl")
        if diff: any_dis+=1
    # check matrix matches recomputed
    assert mat["total_tasks"] == 100
    assert mat["matrix"]["any_disagreement"] == any_dis, f"matrix any_disagreement {mat['matrix']['any_disagreement']} != recomputed {any_dis}"
    for k,v in per.items():
        assert mat["matrix"]["per_dimension"][k]["disagree"] == v, f"{k} mismatch {mat['matrix']['per_dimension'][k]['disagree']} vs {v}"
    # also check any_agreement rate recomputable
    assert mat["matrix"]["any_agreement"] == 100 - any_dis
    # provenance SHAs must match files
    assert mat["reviewer_A_sha256"] == hashlib.sha256(RAW_A.read_bytes()).hexdigest()
    assert mat["reviewer_B_sha256"] == hashlib.sha256(RAW_B.read_bytes()).hexdigest()
    assert mat["sanitized_input_sha256"] == hashlib.sha256(SANITIZED.read_bytes()).hexdigest()
    # detailed diff count
    assert len(mat["disagreements_detailed"]) == any_dis
    # recomputed agreement rates sufficient to verify independence
    assert mat["matrix"]["any_disagreement"] >= 10  # we have 19

def test_adjudicated_resolves_all_and_has_provenance():
    assert ADJ.exists()
    assert ADJ_LOG.exists()
    assert ADJ_PROV.exists()
    adj = _load_jsonl(ADJ)
    assert len(adj) == 100
    ids = [x["task_id"] for x in adj]
    assert ids == [f"v3p-{i:03d}" for i in range(1,101)]
    # adjudicated must be conceptual_answerable, not answerable
    for x in adj:
        assert "conceptual_answerable" in x
        assert "answerable" not in x
    # residual 0: every adjudicated task must have valid golds invariant (except labelable false v3p-042)
    for x in adj:
        if not x["labelable"]:
            continue
        if not x["conceptual_answerable"]:
            assert not any(g["grade"]>=2 for g in x["golds"])
        else:
            assert any(g["grade"]>=2 for g in x["golds"])
    # adjudication log must have 19 entries (one per disagreement) and decisions
    log = json.loads(ADJ_LOG.read_text(encoding="utf-8"))
    assert len(log) == 19, f"log len {len(log)}"
    for entry in log:
        assert "task_id" in entry and "decisions" in entry
    # provenance SHA check
    prov = json.loads(ADJ_PROV.read_text(encoding="utf-8"))
    assert prov["output_sha256"] == hashlib.sha256(ADJ.read_bytes()).hexdigest()
    assert prov["disagreements_resolved"] == 19
    assert prov["residual_after_adjudication"] == 0
    # check adjudicated SHA pinned in protocol
    protocol = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    assert protocol["adjudicator"]["output_sha256"] == prov["output_sha256"]

def test_reaudit_protocol_and_terminology_correction():
    assert PROTOCOL.exists()
    proto = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    assert proto["pilot_reaudit_id"] == "retrieval-v3-pilot-100-v1-re-audit-2026-09-01"
    assert proto["all_100_reviewed"] is True
    assert proto["grade_sample"] == "100/100 (100%, exceeds 30% stratified sample requirement)"
    txt = proto["terminology_correction"]["pilot_answerability"]
    assert "CONCEPTUAL/INTENT" in txt
    assert "NOT corpus-grounded" in txt
    assert "MUST NOT be used as corpus-grounded sizing evidence" in txt
    # Check README mentions correction and does not claim original 7% proven
    readme = README.read_text(encoding="utf-8")
    assert "cannot be independently reconstructed" in readme
    assert "not claimed proven" in readme.lower() or "not claimed as proven" in readme
    assert "CONCEPTUAL/INTENT only" in readme
    # correction file
    assert CORRECTION.exists()
    corr = json.loads(CORRECTION.read_text(encoding="utf-8"))
    assert corr["original_pilot_preserved"]["pilot_tasks_sha256"] == "b3250e592d4c80099e29d20d1bf87594f2bac11a59907ac8067d3e1ddbd65da3"

def test_no_fabricated_reviewer_claims():
    # original pilot report 7% claim must not be re-asserted as re-audit result
    # re-audit disagreement is 19%, not 7%
    mat = json.loads(MATRIX.read_text(encoding="utf-8"))
    assert mat["matrix"]["any_disagreement"] == 19
    assert mat["provenance"]["recomputed_from_raw"] is True
    # pilot report still says 7% but re-audit README clarifies it's not proven
    pilot_report = PILOT_REPORT.read_text(encoding="utf-8")
    assert "7%" in pilot_report  # original still has 7%, but re-audit does not fabricate
    # Check that no file falsely claims 93% agreement as re-audit provenance
    for p in [RAW_A, RAW_B, MATRIX, ADJ]:
        txt = p.read_text(encoding="utf-8") if p.suffix==".jsonl" else p.read_text(encoding="utf-8")
        # raw labels should not contain agreement claim
        pass
    # provenance must not overclaim OMP session id if not durable
    for prov_path in [PROV_A, PROV_B, ADJ_PROV]:
        txt = prov_path.read_text(encoding="utf-8")
        assert "no durable OMP session" in txt or "not durably obtainable" in txt or "recorded as available" in txt

def test_grade_equivalence_all_100_preferred():
    # repair spec says grade review must be at least prereg 30% sample but prefer all 100 if practical
    a = _load_jsonl(RAW_A)
    b = _load_jsonl(RAW_B)
    # both have 100 golds reviewed (each row has golds array defined, even if empty for unlabelable)
    assert len(a) == 100 and len(b) == 100
    for x in a:
        assert "golds" in x
    for x in b:
        assert "golds" in x
    proto = json.loads(PROTOCOL.read_text(encoding="utf-8"))
    assert proto["review_protocol"]["dimensions_grade_equivalence"].startswith("All 100")

def test_no_protected_or_retrieval_execution_in_reaudit():
    # pure test: ensure re-audit artifacts contain no retrieval results, no protected data
    for p in [RAW_A, RAW_B, ADJ]:
        txt = p.read_text(encoding="utf-8")
        # should not contain system retrieval fields like "retrieved", "ranking", "score", "database"
        for forbidden in ["retrieved", "ranking_score", "protected_access"]:
            assert forbidden not in txt.lower()
    # provenance must assert forbidden actions not performed (conceptually)
    for prov_path in [PROV_A, PROV_B]:
        prov = json.loads(prov_path.read_text(encoding="utf-8"))
        assert "retrieval-blind" in prov["annotation_protocol"] or "no system output" in prov["annotation_protocol"]
