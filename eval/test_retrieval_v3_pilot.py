
import json, pathlib
from collections import Counter

PILOT = pathlib.Path("eval/retrieval-v3/pilot/pilot_tasks.jsonl")

def test_pilot_exact_count_100():
    lines = PILOT.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 100, f"expected 100 got {len(lines)}"
    ids = [json.loads(l)["task_id"] for l in lines]
    assert ids == [f"v3p-{i:03d}" for i in range(1,101)]
    assert len(set(ids)) == 100

def test_pilot_no_duplicate_queries():
    lines = [json.loads(l) for l in PILOT.read_text(encoding="utf-8").splitlines()]
    qs = [x["query_text"] for x in lines]
    assert len(qs) == len(set(qs)), "duplicate query_text"

def test_pilot_strata_all_present():
    lines = [json.loads(l) for l in PILOT.read_text(encoding="utf-8").splitlines()]
    c = Counter(x["stratum"] for x in lines)
    required = ["exact_navigation","natural_needs","exploratory_multi_valid","multi_constraint","short_keywords","colloquial_typo_spacing_abbrev","ambiguous","unsupported_no_answer"]
    for r in required:
        assert r in c, f"missing {r}"
        assert c[r] >= 10, f"{r} <10 got {c[r]}"
    assert sum(c.values()) == 100

def test_pilot_location_30():
    lines = [json.loads(l) for l in PILOT.read_text(encoding="utf-8").splitlines()]
    assert sum(1 for x in lines if x["location_bearing"]) == 30

def test_pilot_labelability_answerability():
    lines = [json.loads(l) for l in PILOT.read_text(encoding="utf-8").splitlines()]
    labelable = sum(1 for x in lines if x["labelable"])
    assert labelable == 99
    answerable = sum(1 for x in lines if x["answerable"])
    assert answerable == 85
    # unsupported have no grade2/3 golds
    for x in lines:
        if not x["answerable"]:
            grades = [g["grade"] for g in x["golds"]]
            assert not any(g >=2 for g in grades), f"unsupported has grade>=2 {x['task_id']}"

def test_pilot_gold_graded_equivalence():
    lines = [json.loads(l) for l in PILOT.read_text(encoding="utf-8").splitlines()]
    for x in lines:
        for g in x["golds"]:
            assert g["grade"] in (1,2,3)
            assert "equivalence_group" in g
            assert g["equivalence_group"]

def test_pilot_sha_pinned():
    import hashlib
    sha = hashlib.sha256(PILOT.read_bytes()).hexdigest()
    assert sha == "b3250e592d4c80099e29d20d1bf87594f2bac11a59907ac8067d3e1ddbd65da3"

def test_pilot_no_protected_access():
    # placeholder: pilot must not have been derived from protected evalset plaintext; provenance asserts this
    prov = pathlib.Path("eval/retrieval-v3/pilot/pilot_provenance.json")
    assert prov.exists()
    data = json.loads(prov.read_text(encoding="utf-8"))
    assert data["total_tasks"] == 100
    assert "protected" not in json.dumps(data).lower() or "not_performed" in json.dumps(data).lower()
