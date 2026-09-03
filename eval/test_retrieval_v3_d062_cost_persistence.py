"""D-062 cost persistence completeness — pure/static only (no protected, no model, no HTTP/DB).

WEB HOLD blocker repair: canonical validate_complete_result previously ACCEPTED a
forged cost PASS carrying only {gate, index_ratio, rows_ratio, extra_model_calls}
with no D-061 denominator/aggregate evidence behind it. D-061 requires complete
measurement; missing measurement must be HOLD, never PASS/NO-GO.

This file proves the forged minimal PASS is rejected, each completeness field is
required for PASS and NO-GO, masquerading/denominator/totals/bytes/ratio forgeries
are rejected, a complete valid PASS and a complete genuine NO-GO validate, and
HOLD with missing measurement stays valid structured HOLD.
"""
import copy

from retrieval_v3.candidate_registry import EXPECTED_SHA, EXPECTED_PREREG_SHA
from retrieval_v3.result_schema import validate_complete_result

C0 = "candidate-a-01"
IDS = [f"candidate-a-{i:02d}" for i in range(1, 19)]


def _complete_cost(gate="PASS", rows_ratio=2.0, baseline_bytes=400, aux_bytes=200,
                   task_count=180, measured_count=180,
                   baseline_total=5400, candidate_total=10800, extra_model_calls=0):
    candidate_bytes = baseline_bytes + aux_bytes
    return {
        "gate": gate,
        "index_ratio": (candidate_bytes / baseline_bytes) if baseline_bytes > 0 else 1.0,
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


def _canonical_doc(cost=None):
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
        "cost": cost if cost is not None else _complete_cost(),
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
    raise AssertionError(f"forged/incomplete cost must fail: {name}")


def _with_cost(mut):
    doc = _canonical_doc()
    mut(doc["safety_per_config"][C0]["cost"])
    return doc


def test_d062_forged_minimal_pass_rejected():
    # The exact previously accepted forgery: bare ratios with no measurement.
    _must_reject(_canonical_doc({"gate": "PASS", "index_ratio": 1.0, "rows_ratio": 1.0,
                                 "extra_model_calls": 0}), "forged-minimal-PASS")
    _must_reject(_canonical_doc({"gate": "NO-GO", "index_ratio": 2.5, "rows_ratio": 1.0,
                                 "extra_model_calls": 0}), "bare-NO-GO-without-evidence")


def test_d062_missing_each_completeness_field_rejects():
    for gate in ("PASS", "NO-GO"):
        rows = 2.0 if gate == "PASS" else 3.5
        for field in ("task_count", "measured_count", "baseline_total", "candidate_total",
                      "baseline_bytes", "aux_bytes", "candidate_bytes",
                      "index_ratio", "rows_ratio", "extra_model_calls"):
            cost = _complete_cost(gate=gate, rows_ratio=rows)
            del cost[field]
            _must_reject(_canonical_doc(cost), f"missing-{field}-{gate}")


def test_d062_bool_float_masquerade_rejects():
    for field, bad in (("task_count", True), ("measured_count", 180.0),
                       ("baseline_total", 5400.0), ("candidate_total", False),
                       ("baseline_bytes", 400.0), ("aux_bytes", True),
                       ("candidate_bytes", 600.0), ("extra_model_calls", 0.0),
                       ("extra_model_calls", False)):
        _must_reject(_with_cost(lambda c, f=field, b=bad: c.update({f: b})),
                     f"masquerade-{field}={bad!r}")


def test_d062_denominator_mismatch_rejects():
    _must_reject(_canonical_doc(_complete_cost(measured_count=179)), "measured179-task180")
    _must_reject(_canonical_doc(_complete_cost(task_count=179, measured_count=179)), "task179")
    _must_reject(_canonical_doc(_complete_cost(task_count=181, measured_count=181)), "task181")

def test_d062_totals_rejects():
    _must_reject(_canonical_doc(_complete_cost(baseline_total=179)), "baseline_total-below-denominator")
    _must_reject(_canonical_doc(_complete_cost(baseline_total=0)), "baseline_total-zero")
    _must_reject(_canonical_doc(_complete_cost(candidate_total=-1)), "candidate_total-negative")
    # candidate_total==0 with rows_ratio 0.0 is structurally complete (all-zero candidate scans).
    validate_complete_result(_canonical_doc(_complete_cost(candidate_total=0, rows_ratio=0.0)))


def test_d062_bytes_rejects():
    _must_reject(_canonical_doc(_complete_cost(baseline_bytes=0)), "baseline_bytes-zero")
    _must_reject(_canonical_doc(_complete_cost(baseline_bytes=-400)), "baseline_bytes-negative")
    _must_reject(_canonical_doc(_complete_cost(aux_bytes=-1)), "aux_bytes-negative")
    doc = _canonical_doc()
    doc["safety_per_config"][C0]["cost"]["candidate_bytes"] = 601
    _must_reject(doc, "candidate_bytes-equation-mismatch")
    doc = _canonical_doc()
    doc["safety_per_config"][C0]["cost"]["candidate_bytes"] = 0
    _must_reject(doc, "candidate_bytes-zero")


def test_d062_index_ratio_bytes_mismatch_rejects():
    _must_reject(_with_cost(lambda c: c.update({"index_ratio": 1.6})), "index_ratio-mismatch")
    _must_reject(_with_cost(lambda c: c.update({"index_ratio": 2.0})), "index_ratio-at-gate-but-unmeasured")
    # Gate truth itself stays exact: complete evidence with rows<=3/index<=2/extra==0
    # but gate NO-GO is inconsistent and must fail.
    _must_reject(_canonical_doc(_complete_cost(gate="NO-GO", rows_ratio=2.0)), "complete-PASS-numbers-with-NO-GO-gate")
    _must_reject(_canonical_doc(_complete_cost(gate="PASS", rows_ratio=3.5)), "complete-NO-GO-numbers-with-PASS-gate")


def test_d062_complete_valid_pass_accepts():
    validate_complete_result(_canonical_doc(_complete_cost()))
    # aux_bytes==0 (no aux indexes) is complete: candidate==baseline, ratio 1.0.
    validate_complete_result(_canonical_doc(_complete_cost(aux_bytes=0)))


def test_d062_complete_genuine_no_go_accepts():
    # Genuine NO-GO via rows_ratio>3 with all completeness evidence present.
    validate_complete_result(_canonical_doc(_complete_cost(gate="NO-GO", rows_ratio=3.5)))
    # Genuine NO-GO via index_ratio>2 with consistent bytes (900/400=2.25).
    validate_complete_result(_canonical_doc(_complete_cost(gate="NO-GO", rows_ratio=2.0,
                                                           baseline_bytes=400, aux_bytes=500)))


def test_d062_hold_with_missing_measurement_stays_valid():
    doc = _canonical_doc({"gate": "HOLD", "detail": "missing cost measurement"})
    validate_complete_result(doc)
    base = _canonical_doc()
    base["safety_per_config"][C0]["cost"] = {"gate": "HOLD", "detail": "t"}
    validate_complete_result(base)


D062_TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_d062_")]
