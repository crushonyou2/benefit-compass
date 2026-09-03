"""D-055 pinned-date persistence validator repair — adversarial regression.

Pure/static/mock only: no DB, network, model, retrieval, or protected plaintext.
Proves the SAME-STAGE Web-HOLD root cause is closed: persistence boundaries
(audit append + read/chain, canonical result validation) enforce the single
strict calendar-date semantics of evaluation_context.is_valid_iso_date, not a
weak YYYY-MM-DD shape regex.
"""

import copy
import json
import pathlib
import sys
import tempfile
import uuid

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from retrieval_v3 import audit as _audit
from retrieval_v3.evaluation_context import is_valid_iso_date
from retrieval_v3.result_schema import validate_complete_result

IMPOSSIBLE = ("2026-13-01", "2026-02-30", "2026-99-99")
LEAP = "2028-02-29"
VALID = "2026-02-10"
GIT_HEAD = "0" * 40


def _valid_append_kwargs(**over):
    kw = dict(action="run_start", set_role="none", git_head=GIT_HEAD, git_dirty=False)
    kw.update(over)
    return kw


def _raw_event(prev_hash, date):
    """Craft a hash-consistent raw chain event carrying `date` (or omitting pins)."""
    payload = {
        "schema_version": 1,
        "event_id": str(uuid.uuid4()),
        "utc_timestamp": "2026-09-04T00:00:00Z",
        "git_head": GIT_HEAD,
        "git_dirty": False,
        "process_id": 1,
        "session_id": "d055-test",
        "action": "run_start",
        "candidate_id": None,
        "set_role": "none",
        "set_sha": None,
        "command": None,
        "runner_id": None,
        "outcome": None,
        "previous_event_hash": prev_hash,
    }
    if date is not None:
        payload["evaluation_as_of_date"] = date
    event = dict(payload)
    event["event_hash"] = _audit._compute_event_hash(payload)
    return event


def _write_raw(log, events):
    with open(log, "w", encoding="utf-8", newline="\n") as f:
        for ev in events:
            f.write(json.dumps(ev, ensure_ascii=False, separators=(",", ":"), sort_keys=True) + "\n")


def test_d055_single_shared_semantics():
    assert is_valid_iso_date("2026-99-99") is False
    assert is_valid_iso_date("2026-13-01") is False
    assert is_valid_iso_date("2026-02-30") is False
    assert is_valid_iso_date(LEAP) is True
    assert is_valid_iso_date(VALID) is True
    for rel in ("eval/retrieval-v3/audit.py", "eval/retrieval-v3/result_schema.py"):
        src = pathlib.Path(rel).read_text(encoding="utf-8")
        assert "is_valid_iso_date" in src, f"{rel} must reuse the shared strict validator"
        assert r'^\d{4}-\d{2}-\d{2}$' not in src, f"{rel} must not keep a divergent weak date regex"


def test_d055_impossible_dates_rejected_at_append():
    with tempfile.TemporaryDirectory() as td:
        for bad in IMPOSSIBLE:
            log = str(pathlib.Path(td) / f"append-{bad.replace('-', '')}.jsonl")
            try:
                _audit.append_event(log, **_valid_append_kwargs(evaluation_as_of_date=bad))
                assert False, f"append must reject impossible date {bad}"
            except _audit.AuditSchemaError:
                pass


def test_d055_impossible_dates_rejected_at_read_chain():
    with tempfile.TemporaryDirectory() as td:
        for bad in IMPOSSIBLE:
            log = str(pathlib.Path(td) / f"chain-{bad.replace('-', '')}.jsonl")
            _write_raw(log, [_raw_event(_audit.GENESIS_HASH, bad)])
            try:
                _audit.read_and_verify_chain(log)
                assert False, f"read/chain must reject persisted impossible date {bad}"
            except _audit.AuditSchemaError:
                pass


def test_d055_leap_day_accepted_and_history_without_pins_valid():
    with tempfile.TemporaryDirectory() as td:
        log = str(pathlib.Path(td) / "leap.jsonl")
        ev = _audit.append_event(log, **_valid_append_kwargs(evaluation_as_of_date=LEAP))
        assert ev["evaluation_as_of_date"] == LEAP
        assert len(_audit.read_and_verify_chain(log)) == 1
        log2 = str(pathlib.Path(td) / "nopins.jsonl")
        ev2 = _audit.append_event(log2, **_valid_append_kwargs())
        assert "evaluation_as_of_date" not in ev2 and "db_session_timezone" not in ev2
        assert len(_audit.read_and_verify_chain(log2)) == 1
        log3 = str(pathlib.Path(td) / "raw-nopins.jsonl")
        _write_raw(log3, [_raw_event(_audit.GENESIS_HASH, None)])
        assert len(_audit.read_and_verify_chain(log3)) == 1


def _canonical_base():
    from retrieval_v3.candidate_registry import EXPECTED_SHA, EXPECTED_PREREG_SHA

    ids = [f"candidate-a-{i:02d}" for i in range(1, 19)]
    per = [{"config_id": c, "success_at_5": 0.9, "ndcg_at_5": 0.8, "mrr_at_10": 0.7} for c in ids]
    saf = {c: {g: {"gate": "HOLD", "detail": "t"} for g in (
        "unsupported", "ambiguous", "production_exclusion", "official_link", "http_resolution", "cost")} for c in ids}
    lat = {c: {"n": 180, "warmup_n": 30, "baseline": {"p50": 500, "p95": 500, "p99": 500},
                "candidate": {"p50": 570, "p95": 570, "p99": 570}, "gate": "PASS"} for c in ids}
    return {"schema_version": 1, "git_head": GIT_HEAD, "git_dirty": False,
            "candidate_plan_sha256": EXPECTED_SHA, "prereg_sha256": EXPECTED_PREREG_SHA,
            "provenance": {"candidate_plan_sha256": EXPECTED_SHA, "prereg_sha256": EXPECTED_PREREG_SHA},
            "per_config_metrics": per, "selection": {"chosen": None, "eligible": []},
            "candidate_b_gate": {"admitted": False, "instantiated": False, "status": "not_evaluated"},
            "safety_per_config": saf, "latency_per_config": lat,
            "corpus_provenance": {"total_policies": 1, "snapshot": "t",
                                  "db_session_timezone": "SYNTH-TZ", "evaluation_as_of_date": VALID},
            "evaluation_context": {"db_session_timezone": "SYNTH-TZ", "evaluation_as_of_date": VALID},
            "set_provenance": {"set_role": "dev", "set_sha": "1" * 64, "n": 180, "headline_n": 130}}


def test_d055_canonical_result_rejects_impossible_dates():
    for bad in IMPOSSIBLE:
        doc = _canonical_base()
        doc["evaluation_context"] = {"db_session_timezone": "SYNTH-TZ", "evaluation_as_of_date": bad}
        doc["corpus_provenance"] = {"total_policies": 1, "snapshot": "t",
                                    "db_session_timezone": "SYNTH-TZ", "evaluation_as_of_date": bad}
        try:
            validate_complete_result(doc)
            assert False, f"canonical result must reject impossible date {bad}"
        except ValueError:
            pass


def test_d055_canonical_result_accepts_leap_day():
    doc = _canonical_base()
    doc["evaluation_context"] = {"db_session_timezone": "SYNTH-TZ", "evaluation_as_of_date": LEAP}
    doc["corpus_provenance"] = {"total_policies": 1, "snapshot": "t",
                                "db_session_timezone": "SYNTH-TZ", "evaluation_as_of_date": LEAP}
    validate_complete_result(doc)


D055_TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_d055_")]

if __name__ == "__main__":
    n = 0
    for name in sorted(k for k in globals() if k.startswith("test_d055_")):
        globals()[name]()
        n += 1
        print(f"PASS {name}")
    print(f"ALL {n} D-055 focused tests PASS")
