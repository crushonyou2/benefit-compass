"""D-064 exact index-ratio persistence boundary — pure/static only (no protected, no model, no HTTP/DB).

Same-stage Web HOLD narrow repair, persistence validator only (both
result_schema mirrors byte-identical). D-062 used
math.isclose(persisted, candidate_bytes/baseline_bytes, rel_tol=1e-9) and gated
PASS on persisted float <=2.0. A forged persisted 2.0 within 1e-9 of a true
bytes ratio just over the <=2 gate was therefore accepted as PASS. D-064 makes
the boundary exact: persisted index_ratio must equal
candidate_bytes/baseline_bytes exactly (no tolerance), and gate truth
additionally requires the exact integer bound
candidate_bytes<=2*baseline_bytes. D-061 numeric gate (index<=2, rows<=3,
extra==0), HOLD semantics, rows_ratio handling, and all other contracts are
untouched.
"""
import math
import pathlib

from retrieval_v3.candidate_registry import EXPECTED_SHA, EXPECTED_PREREG_SHA
from retrieval_v3.result_schema import validate_complete_result

C0 = "candidate-a-01"
IDS = [f"candidate-a-{i:02d}" for i in range(1, 19)]

_HERE = pathlib.Path(__file__).parent
_SCHEMA_UNDER = _HERE / "retrieval_v3" / "result_schema.py"
_SCHEMA_HYPHEN = _HERE / "retrieval-v3" / "result_schema.py"


def _cost(gate="PASS", rows_ratio=1.0, baseline_bytes=400, aux_bytes=200,
          task_count=180, measured_count=180,
          baseline_total=5400, candidate_total=5400, extra_model_calls=0,
          index_ratio=None):
    candidate_bytes = baseline_bytes + aux_bytes
    if index_ratio is None:
        index_ratio = candidate_bytes / baseline_bytes
    return {
        "gate": gate,
        "index_ratio": index_ratio,
        "rows_ratio": rows_ratio,
        "extra_model_calls": extra_model_calls,
        "task_count": task_count,
        "measured_count": measured_count,
        "baseline_total": baseline_total,
        "candidate_total": candidate_total,
        "baseline_bytes": baseline_bytes,
        "candidate_bytes": candidate_bytes,
        "aux_bytes": aux_bytes,
    }


def _canonical_doc(cost):
    per = [{"config_id": c, "success_at_5": 0.9, "ndcg_at_5": 0.8, "mrr_at_10": 0.7} for c in IDS]
    saf = {c: {g: {"gate": "HOLD", "detail": "t"} for g in (
        "unsupported", "ambiguous", "production_exclusion", "official_link", "http_resolution", "cost")} for c in IDS}
    saf[C0] = {
        "unsupported": {"gate": "PASS", "success": 27, "required": 26, "denominator": 27},
        "ambiguous": {"gate": "PASS", "success": 23, "required": 21, "denominator": 23},
        "production_exclusion": {"gate": "PASS", "expected_tasks": 180, "expected_slots": 900,
                                 "intrusions_task": 0, "intrusions_slot": 0},
        "official_link": {"gate": "PASS", "unique": 2, "mismatches": []},
        "http_resolution": {"gate": "PASS", "unique": 100, "successes": 99, "required": 99},
        "cost": cost,
    }
    lat = {c: {"n": 180, "warmup_n": 30, "baseline": {"p50": 500, "p95": 500, "p99": 500},
                "candidate": {"p50": 570, "p95": 570, "p99": 570}, "gate": "PASS"} for c in IDS}
    ctx = {"db_session_timezone": "GMT", "evaluation_as_of_date": "2026-09-03"}
    return {"schema_version": 1, "git_head": "0" * 40, "git_dirty": False,
            "candidate_plan_sha256": EXPECTED_SHA, "prereg_sha256": EXPECTED_PREREG_SHA,
            "provenance": {"candidate_plan_sha256": EXPECTED_SHA, "prereg_sha256": EXPECTED_PREREG_SHA},
            "per_config_metrics": per, "selection": {"chosen": None, "eligible": []},
            "candidate_b_gate": {"admitted": False, "instantiated": False, "status": "not_evaluated"},
            "safety_per_config": saf, "latency_per_config": lat,
            "corpus_provenance": {"total_policies": 1, "snapshot": "test", **ctx},
            "evaluation_context": ctx,
            "set_provenance": {"set_role": "dev", "set_sha": "1" * 64, "n": 180, "headline_n": 130}}


def _must_reject(doc, name):
    try:
        validate_complete_result(doc)
    except ValueError:
        return
    raise AssertionError(f"exact-boundary forgery must fail: {name}")


def test_d064_old_tolerance_gate_forgery_rejected():
    # True bytes ratio just over the gate but inside the old 1e-9 tolerance:
    # baseline 2e9, aux 2e9+1 -> candidate 4000000001, true 2.0000000005.
    base, aux = 2_000_000_000, 2_000_000_001
    true_ratio = (base + aux) / base
    assert true_ratio > 2.0
    assert math.isclose(2.0, true_ratio, rel_tol=1e-9, abs_tol=0.0), \
        "fixture must sit inside the old tolerance hole (else it proves nothing)"
    forged = _cost(gate="PASS", baseline_bytes=base, aux_bytes=aux, index_ratio=2.0)
    _must_reject(_canonical_doc(forged), "forged-2.0-PASS-inside-old-tolerance")


def test_d064_within_tolerance_drift_rejected():
    # Exact-persistence hole even far from the gate: true 1.0, persisted
    # 1.0+5e-10 is inside old rel_tol=1e-9 yet not the measured value.
    drifted = 1.0 + 5e-10
    assert drifted != 1.0
    assert math.isclose(drifted, 1.0, rel_tol=1e-9, abs_tol=0.0)
    forged = _cost(gate="PASS", baseline_bytes=2_000_000_000, aux_bytes=0, index_ratio=drifted)
    _must_reject(_canonical_doc(forged), "drifted-ratio-PASS-inside-old-tolerance")


def test_d064_exact_boundary_pass_accepts():
    # Exactly 2x bytes is exactly at the gate: ratio exactly 2.0, PASS valid.
    validate_complete_result(_canonical_doc(_cost(gate="PASS", baseline_bytes=400, aux_bytes=400)))

def test_d064_exact_over_boundary_pass_rejected_no_go_accepts():
    # One byte over 2x: true 801/400=2.0025. Exact persisted ratio + PASS rejects;
    # the same evidence with NO-GO validates.
    true_ratio = 801 / 400
    assert true_ratio > 2.0
    _must_reject(_canonical_doc(_cost(gate="PASS", baseline_bytes=400, aux_bytes=401,
                                        index_ratio=true_ratio)), "801/400-PASS")
    validate_complete_result(_canonical_doc(_cost(gate="NO-GO", baseline_bytes=400, aux_bytes=401,
                                                  index_ratio=true_ratio, rows_ratio=1.0)))


def test_d064_large_exact_pass_accepts():
    # Exact equality holds at scale for honest writers (no false rejection).
    validate_complete_result(_canonical_doc(
        _cost(gate="PASS", baseline_bytes=2_000_000_000, aux_bytes=1_000_000_000)))


def test_d064_hold_with_missing_measurement_stays_valid():
    doc = _canonical_doc({"gate": "HOLD", "detail": "missing cost measurement"})
    validate_complete_result(doc)


def test_d064_validator_is_exact_and_mirrors_identical():
    a = _SCHEMA_UNDER.read_bytes()
    b = _SCHEMA_HYPHEN.read_bytes()
    assert a == b, "result_schema mirrors must stay byte-identical"
    text = a.decode("utf-8")
    assert "math.isclose" not in text, "no tolerance comparison may remain in the persistence validator"
    assert 'if _cg.get("index_ratio") != _expect_ratio:' in text
    assert '_cg.get("candidate_bytes") <= 2 * _cg.get("baseline_bytes")' in text


D064_TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_d064_")]
