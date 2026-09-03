"""Production-exclusion v2 — pure classifier, pre-retrieval filter, audit (D-052/D-053/D-054).

Frozen contract: eval/retrieval-v3/candidate-plan/production-exclusion-policy-v2.json
(gate production_exclusion; claim boundary D-003 parity only, never universal
expired/eligible/user-specific).

Allowed classification inputs ONLY: source, source_id, biz_end + pinned
evaluation_as_of_date. No raw text, no 신청기한 parsing, no age/income/region
inference, no LLM/model, no score, no protected labels/results, no
source-specific guesswork.

Predicate: production_excluded iff biz_end non-null AND biz_end <
evaluation_as_of_date. Null => not_production_excluded_by_D003_predicate with
NO universal not-expired/eligible claim. Missing identity/lookup, malformed
non-null date, missing/invalid context => UNMEASURABLE_HOLD; never default
eligible=true.

Pure: no IO, no clock, no randomness. ISO dates compare lexicographically.
"""

from __future__ import annotations

from .evaluation_context import is_valid_iso_date

POLICY_ID = "retrieval-v3-production-exclusion-policy-v2"
POLICY_SHA256 = "6fee9ec22d5d3ac153ff19a6b1b5d27ab6a6a43bda11e35821d689f938968fe5"

PRODUCTION_EXCLUDED = "production_excluded"
NOT_EXCLUDED = "not_production_excluded_by_D003_predicate"
UNMEASURABLE_HOLD = "UNMEASURABLE_HOLD"

DEV_TASKS = 180
DEV_SLOTS = 900
HOLDOUT_TASKS = 250
HOLDOUT_SLOTS = 1250


def classify_production_exclusion(
    source: object,
    source_id: object,
    biz_end: object,
    evaluation_as_of_date: object,
) -> str:
    """Pure D-003-parity classifier. Only the four allowed inputs are read."""
    if not isinstance(source, str) or not source:
        return UNMEASURABLE_HOLD
    if not isinstance(source_id, str) or not source_id:
        return UNMEASURABLE_HOLD
    if not is_valid_iso_date(evaluation_as_of_date):
        return UNMEASURABLE_HOLD
    if biz_end is None:
        return NOT_EXCLUDED
    if not is_valid_iso_date(biz_end):
        return UNMEASURABLE_HOLD
    if biz_end < evaluation_as_of_date:
        return PRODUCTION_EXCLUDED
    return NOT_EXCLUDED


def filter_policies_for_retrieval(policies: list, evaluation_as_of_date: object) -> list:
    """Pre-retrieval D-003 exclusion: rows classified production_excluded cannot
    enter dense/sparse/exact/final pools. Definite exclusions are removed;
    not-excluded and unmeasurable rows pass through (unmeasurable rows are
    reported HOLD by the independent audit, never silent PASS). Pure; input
    list is not mutated."""
    if not is_valid_iso_date(evaluation_as_of_date):
        raise ValueError(f"evaluation_as_of_date invalid {evaluation_as_of_date!r} (fail-closed)")
    kept = []
    for p in policies:
        if not isinstance(p, dict):
            raise ValueError("policy row must be dict (fail-closed)")
        verdict = classify_production_exclusion(
            p.get("source"), p.get("source_id"), p.get("biz_end"), evaluation_as_of_date
        )
        if verdict != PRODUCTION_EXCLUDED:
            kept.append(p)
    return kept


def audit_internal_top5(
    top5_by_task: dict,
    biz_end_lookup: dict | None,
    evaluation_as_of_date: object,
    expected_tasks: int,
    expected_slots: int,
) -> tuple[str, dict]:
    """Independent Candidate-A INTERNAL final-top-5 audit over EVERY task,
    regardless of visible ANSWER/ABSTAIN/CLARIFY. Consumes the pinned corpus
    lookup (unfiltered input-side evidence), never only the filtered output.

    PASS iff 0 intrusion tasks AND 0 slots. Any intrusion => NO-GO. Missing or
    unmeasurable (count shape, identity, lookup, date, checker) => HOLD.
    HOLD takes precedence over NO-GO on incomplete measurement (fail-closed:
    neither PASS nor a partial NO-GO is certified without full evidence).
    """
    details: dict = {}
    if not is_valid_iso_date(evaluation_as_of_date):
        details["error"] = "missing/invalid evaluation_as_of_date (fail-closed HOLD)"
        details["gate"] = "HOLD"
        return "HOLD", details
    if not isinstance(top5_by_task, dict) or len(top5_by_task) != expected_tasks:
        got = len(top5_by_task) if isinstance(top5_by_task, dict) else type(top5_by_task).__name__
        details["error"] = f"task count mismatch: got {got} expected {expected_tasks} (fail-closed HOLD)"
        details["gate"] = "HOLD"
        return "HOLD", details
    if biz_end_lookup is None or not isinstance(biz_end_lookup, dict):
        details["error"] = "missing corpus biz_end lookup (fail-closed HOLD)"
        details["gate"] = "HOLD"
        return "HOLD", details
    intrusions_task = 0
    intrusions_slot = 0
    unmeasurable: list = []
    for task_id, docs in top5_by_task.items():
        if not isinstance(docs, list) or len(docs) != 5:
            details["error"] = f"task {task_id} has {len(docs) if isinstance(docs, list) else type(docs).__name__} docs, expected 5 (fail-closed HOLD)"
            details["gate"] = "HOLD"
            return "HOLD", details
        task_intrusion = False
        for doc in docs:
            if isinstance(doc, dict):
                src, sid = doc.get("source"), doc.get("source_id")
            elif isinstance(doc, (list, tuple)) and len(doc) == 2:
                src, sid = doc[0], doc[1]
            else:
                details["error"] = f"task {task_id} doc {doc!r} not (source, source_id) (fail-closed HOLD)"
                details["gate"] = "HOLD"
                return "HOLD", details
            if not isinstance(src, str) or not isinstance(sid, str):
                details["error"] = f"task {task_id} doc ({src!r}, {sid!r}) not str (fail-closed HOLD)"
                details["gate"] = "HOLD"
                return "HOLD", details
            key = (src, sid)
            biz_end = biz_end_lookup.get(key)
            if biz_end is None and f"{src}\x00{sid}" in biz_end_lookup:
                biz_end = biz_end_lookup.get(f"{src}\x00{sid}")
            if key not in biz_end_lookup and f"{src}\x00{sid}" not in biz_end_lookup:
                unmeasurable.append((task_id, src, sid, "missing-lookup"))
                continue
            verdict = classify_production_exclusion(src, sid, biz_end, evaluation_as_of_date)
            if verdict == UNMEASURABLE_HOLD:
                unmeasurable.append((task_id, src, sid, "unmeasurable"))
            elif verdict == PRODUCTION_EXCLUDED:
                intrusions_slot += 1
                task_intrusion = True
        if task_intrusion:
            intrusions_task += 1
    details["expected_tasks"] = expected_tasks
    details["expected_slots"] = expected_slots
    details["intrusions_task"] = intrusions_task
    details["intrusions_slot"] = intrusions_slot
    details["denominators"] = f"{expected_tasks} tasks / {expected_slots} slots"
    details["evaluation_as_of_date"] = evaluation_as_of_date
    if unmeasurable:
        details["unmeasurable"] = unmeasurable[:5]
        details["unmeasurable_count"] = len(unmeasurable)
        details["gate"] = "HOLD"
        details["error"] = f"unmeasurable production-exclusion evidence: {len(unmeasurable)} slots (fail-closed HOLD)"
        return "HOLD", details
    if intrusions_task == 0 and intrusions_slot == 0:
        details["gate"] = "PASS"
        return "PASS", details
    details["gate"] = "NO-GO"
    details["error"] = f"production-excluded intrusion found: {intrusions_task}/{expected_tasks} tasks, {intrusions_slot}/{expected_slots} slots"
    return "NO-GO", details
