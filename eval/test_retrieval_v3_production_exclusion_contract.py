"""Retrieval v3 production-exclusion contract tests (pure/static only).

Proves for the D-052 DESIGN/FREEZE stage (no runner/safety/production change,
no DB/network/model/retrieval/protected execution):
- prereg, plan-v1, plan-v2, safe-action policy, safe-action supersession doc, and
  eligibility evidence bytes/SHAs unchanged;
- v2->v3 keeps all 18 configs and all ranking/action semantics identical; only the
  authorized gating-contract fields plus parent/version/provenance/supersession
  metadata differ (ineligible_expired -> production_exclusion);
- the exact production_exclusion predicate on pure fixtures (before/equal/after,
  null, malformed/missing fail-closed) with no free-text/eligible/default semantics;
- exact 180/900 and 250/1250 denominators with the gate truth table
  (zero => PASS, any intrusion => NO-GO, missing => HOLD);
- as-of date pin semantics with the Asia/Seoul label explicit and no dynamic
  current time in the pure evaluator;
- `eligible` absent from normative machine-readable gate inputs/decision keys.

No DB, no network, no model/embedding, no retrieval execution, no protected plaintext.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PREREG = REPO / "docs" / "RETRIEVAL_V3_PREREG.md"
PLAN_V1 = REPO / "eval" / "retrieval-v3" / "candidate-plan" / "candidate-plan-v1.json"
PLAN_V2 = REPO / "eval" / "retrieval-v3" / "candidate-plan" / "candidate-plan-v2.json"
PLAN_V3 = REPO / "eval" / "retrieval-v3" / "candidate-plan" / "candidate-plan-v3.json"
POLICY = REPO / "eval" / "retrieval-v3" / "candidate-plan" / "production-exclusion-policy-v1.json"
SAFE_POLICY = REPO / "eval" / "retrieval-v3" / "candidate-plan" / "safe-action-policy-v1.json"
SAFE_DOC = REPO / "docs" / "RETRIEVAL_V3_SAFE_ACTION_SUPERSESSION_V1.md"
ELIG_DOC = REPO / "docs" / "RETRIEVAL_V3_ELIGIBILITY_EVIDENCE_V1.md"
SUPER_DOC = REPO / "docs" / "RETRIEVAL_V3_PRODUCTION_EXCLUSION_SUPERSESSION_V1.md"

EXPECTED_PREREG_SHA = "7842018613d66aa4570f4db2f8ae5a698ceb46757995a6b7e26873177b36160e"
EXPECTED_V1_SHA = "2815361a469fee9bf69f6ffdf2124d19928220535cdb08b2005ae6674ae7d17c"
EXPECTED_V2_SHA = "d233f5c4d912e4d0856d89213d6392fbf44494f5538d018e7412f61781ae6cc6"
EXPECTED_SAFE_POLICY_SHA = "c512fb5627179697a987b05a2431b8f7e30d1153af2ff6dca37995f6b232a35d"
EXPECTED_SAFE_DOC_SHA = "472b6183114a0ebf4d22e9b22c03bb9233b15a736587e29a917aa49113502364"
EXPECTED_ELIG_DOC_SHA = "eea3c5ce393f1f3c9563983df16f4648e9c005fd4f317b44cd168b082af91d32"

EXPECTED_POLICY_SHA = "3bcfc5b8360af28ccd7ea9018f3e3ffda73fba7744ba33bbfb83446235284608"
EXPECTED_SUPER_DOC_SHA = "63cdc4325b10c75cdb468ce775043c351ec22326642b70f0763189b846936fdc"
EXPECTED_V3_SHA = "665771f991a3891869f7d27658eedacbed28ba522afdcadcf8edd4d62b412681"
EXPECTED_V3_FROZEN_AT = "2026-09-04T00:51:16+09:00"

OLD_GATE_KEY = "ineligible_expired_intrusion"
NEW_GATE_KEY = "production_exclusion_intrusion"
OLD_GATE_PHRASE = "ineligible/expired 0/250 & 0/1250 holdout 0/180 & 0/900 dev"
NEW_GATE_PHRASE = "production_exclusion 0/250 & 0/1250 holdout 0/180 & 0/900 dev"

# v2 keys that must be value-identical in v3. Stage-local plan_id/version/parents,
# the two authorized gating-contract fields, and provenance/assertions/supersession/
# frozen_at are deliberately EXCLUDED and pinned by dedicated tests below.
PRESERVED_V2_V3 = [
    "allowed_axes", "base_commit", "base_commit_tag", "baseline_identity",
    "branch", "candidate_b_gate", "candidate_family", "configs", "cosine_min_placement",
    "deterministic_ordering_contract", "exact_oracle_semantics", "forbidden_axes",
    "fusion_semantics", "max_configs", "parameter_semantics",
    "policy_comparison_vector", "safe_action_policy", "secondary_diagnostics_D026",
    "standing_contract_refs",
]

HOLD_SENTINEL = "UNMEASURABLE_HOLD"


def _load(path: Path) -> dict:
    return json.loads(path.read_bytes().decode("utf-8"))


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _valid_iso_date(s: object) -> bool:
    if not isinstance(s, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return False
    try:
        date.fromisoformat(s)
    except ValueError:
        return False
    return True


def _classify(policy: dict, row: object, as_of_date: object,
              corpus_pinned: bool = True, checker_executed: bool = True) -> str:
    """Reference evaluator built strictly FROM the frozen artifact.

    Returns one of policy["predicate"]["decision_values"]. Fail-closed inputs
    yield UNMEASURABLE_HOLD (gate HOLD, never PASS). The as-of date is an
    explicit parameter: no dynamic current time exists in this evaluator.
    """
    allowed = policy["classification_inputs"]["corpus_row_fields"]
    assert allowed == ["source", "source_id", "biz_end"], "allowed inputs changed"
    if not checker_executed or not corpus_pinned:
        return HOLD_SENTINEL
    if not _valid_iso_date(as_of_date):
        return HOLD_SENTINEL
    if not isinstance(row, dict) or row.get("source") is None or row.get("source_id") is None:
        return HOLD_SENTINEL
    biz_end = row.get("biz_end")
    if biz_end is None:
        return "not_production_excluded_by_D003_predicate"
    if not _valid_iso_date(biz_end):
        return HOLD_SENTINEL
    assert isinstance(as_of_date, str)
    return "production_excluded" if biz_end < as_of_date else "not_production_excluded_by_D003_predicate"


def _gate(policy: dict, intrusion_tasks: int, intrusion_slots: int, measured: bool = True) -> str:
    if not measured:
        return "HOLD"
    tt = policy["gate_truth_table"]
    assert set(tt) == {"PASS", "NO-GO", "HOLD"}, "truth-table verdicts changed"
    if intrusion_tasks == 0 and intrusion_slots == 0:
        return "PASS"
    return "NO-GO"


def _walk_keys(node: object):
    if isinstance(node, dict):
        for k, v in node.items():
            yield k
            yield from _walk_keys(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk_keys(v)


def test_old_bytes_immutable():
    assert _sha(PREREG) == EXPECTED_PREREG_SHA, "prereg must stay immutable"
    assert _sha(PLAN_V1) == EXPECTED_V1_SHA, "plan-v1 must stay immutable"
    assert _sha(PLAN_V2) == EXPECTED_V2_SHA, "plan-v2 must stay immutable"
    assert _sha(SAFE_POLICY) == EXPECTED_SAFE_POLICY_SHA, "safe-action policy must stay immutable"
    assert _sha(SAFE_DOC) == EXPECTED_SAFE_DOC_SHA, "safe-action supersession doc must stay immutable"
    assert _sha(ELIG_DOC) == EXPECTED_ELIG_DOC_SHA, "eligibility evidence doc must stay immutable"


def test_new_artifact_shas_pinned():
    assert _sha(POLICY) == EXPECTED_POLICY_SHA, "production-exclusion policy bytes changed"
    assert _sha(SUPER_DOC) == EXPECTED_SUPER_DOC_SHA, "supersession doc bytes changed"
    assert _sha(PLAN_V3) == EXPECTED_V3_SHA, "plan-v3 bytes changed"


def test_v3_parents_carry_all_six_identities():
    v3 = _load(PLAN_V3)
    assert v3["plan_id"] == "retrieval-v3-candidate-plan-v3"
    assert v3["version"] == "3.0.0"
    parents = v3["parents"]
    assert parents["prereg_sha256"] == EXPECTED_PREREG_SHA
    assert parents["candidate_plan_v1_sha256"] == EXPECTED_V1_SHA
    assert parents["candidate_plan_v2_sha256"] == EXPECTED_V2_SHA
    assert parents["safe_action_policy_sha256"] == EXPECTED_SAFE_POLICY_SHA
    assert parents["production_exclusion_policy_sha256"] == EXPECTED_POLICY_SHA
    assert parents["supersession_doc_sha256"] == EXPECTED_SUPER_DOC_SHA
    assert _sha(REPO / parents["production_exclusion_policy"]) == EXPECTED_POLICY_SHA
    assert _sha(REPO / parents["supersession_doc"]) == EXPECTED_SUPER_DOC_SHA


def test_v2_to_v3_substantive_identity():
    v2 = _load(PLAN_V2)
    v3 = _load(PLAN_V3)
    for key in PRESERVED_V2_V3:
        assert v3[key] == v2[key], f"v2->v3 must preserve {key}"
    assert len(v3["configs"]) == 18 == len(v2["configs"])
    assert [c["config_id"] for c in v3["configs"]] == [c["config_id"] for c in v2["configs"]]
    assert v3["safe_action_policy"]["policy_sha256"] == EXPECTED_SAFE_POLICY_SHA
    assert v3["safe_action_policy"]["common_to_all_configs"] is True
    assert v3["safe_action_policy"]["not_a_tuning_axis"] is True


def test_gating_contract_authorized_diff_only():
    v2 = _load(PLAN_V2)
    v3 = _load(PLAN_V3)
    old_dev, new_dev = v2["gating_contract_ref"]["dev"], v3["gating_contract_ref"]["dev"]
    assert OLD_GATE_PHRASE in old_dev
    assert new_dev == old_dev.replace(OLD_GATE_PHRASE, NEW_GATE_PHRASE), \
        "gating_contract_ref differs outside the single authorized gate rename"
    assert OLD_GATE_PHRASE not in new_dev
    assert v3["gating_contract_ref"]["holdout_note"] == v2["gating_contract_ref"]["holdout_note"]


def test_selection_rule_authorized_diff_only():
    v2 = _load(PLAN_V2)
    v3 = _load(PLAN_V3)
    old_sel, new_sel = v2["selection_rule"], v3["selection_rule"]
    assert set(new_sel) == set(old_sel), "selection_rule fields must not grow/shrink"
    for key in old_sel:
        if key != "safety_gates_dev":
            assert new_sel[key] == old_sel[key], f"selection_rule.{key} must stay identical"
    old_gates, new_gates = old_sel["safety_gates_dev"], new_sel["safety_gates_dev"]
    assert OLD_GATE_KEY in old_gates and OLD_GATE_KEY not in new_gates
    assert NEW_GATE_KEY in new_gates
    assert set(new_gates) == (set(old_gates) - {OLD_GATE_KEY}) | {NEW_GATE_KEY}
    for key in old_gates:
        if key != OLD_GATE_KEY:
            assert new_gates[key] == old_gates[key], f"safety gate {key} must stay identical"
    gate_text = new_gates[NEW_GATE_KEY]
    assert "0/180" in gate_text and "0/900" in gate_text
    assert "NO-GO" in gate_text and "HOLD" in gate_text
    assert "production-exclusion-policy-v1" in gate_text
    assert "eligible" not in gate_text, "new gate text must not use the removed eligible boolean"


def test_production_exclusion_policy_block():
    v3 = _load(PLAN_V3)
    block = v3["production_exclusion_policy"]
    assert block["policy_id"] == "retrieval-v3-production-exclusion-policy-v1"
    assert block["policy_sha256"] == EXPECTED_POLICY_SHA
    assert block["common_to_all_configs"] is True
    assert block["not_a_tuning_axis"] is True
    assert block["does_not_expand_max24"] is True


def test_gate_id_and_predicate_exact():
    policy = _load(POLICY)
    assert policy["gate"]["id"] == "production_exclusion"
    assert policy["gate"]["name"] == "production_exclusion"
    assert policy["predicate"]["production_excluded"] == \
        "biz_end is not null AND biz_end < evaluation_as_of_date"
    assert policy["d003_runtime_reference"]["predicate_sql"] == \
        "(biz_end IS NULL OR biz_end >= CURRENT_DATE)"
    assert policy["predicate"]["decision_values"] == [
        "production_excluded",
        "not_production_excluded_by_D003_predicate",
        "UNMEASURABLE_HOLD",
    ]


def test_predicate_fixtures_before_equal_after_null():
    policy = _load(POLICY)
    as_of = "2026-09-04"
    row = {"source": "gov24", "source_id": "G-1", "biz_end": "2026-09-03"}
    assert _classify(policy, row, as_of) == "production_excluded"
    row = {"source": "gov24", "source_id": "G-2", "biz_end": "2026-09-04"}
    assert _classify(policy, row, as_of) == "not_production_excluded_by_D003_predicate"
    row = {"source": "youth", "source_id": "Y-1", "biz_end": "2026-09-05"}
    assert _classify(policy, row, as_of) == "not_production_excluded_by_D003_predicate"
    row = {"source": "youth", "source_id": "Y-2", "biz_end": None}
    assert _classify(policy, row, as_of) == "not_production_excluded_by_D003_predicate"
    # null is explicitly NOT a claim of not-expired/eligible: decision value differs
    assert "not_production_excluded_by_D003_predicate" not in ("not expired", "eligible")


def test_current_date_confined_to_d003_reference():
    policy = _load(POLICY)
    ref = policy["d003_runtime_reference"]
    assert "CURRENT_DATE" in json.dumps(ref, ensure_ascii=False), \
        "D-003 runtime reference must quote the production predicate"
    rest = {k: v for k, v in policy.items() if k != "d003_runtime_reference"}
    assert "CURRENT_DATE" not in json.dumps(rest, ensure_ascii=False), \
        "CURRENT_DATE must appear only in the D-003 runtime reference"

def test_fail_closed_fixtures():
    policy = _load(POLICY)
    as_of = "2026-09-04"
    base = {"source": "gov24", "source_id": "G-1", "biz_end": "2026-01-01"}
    assert _classify(policy, {**base, "biz_end": "2026.01.01"}, as_of) == HOLD_SENTINEL
    assert _classify(policy, {**base, "biz_end": "상시"}, as_of) == HOLD_SENTINEL
    assert _classify(policy, {**base, "biz_end": ""}, as_of) == HOLD_SENTINEL
    assert _classify(policy, {**base, "biz_end": "2026-13-40"}, as_of) == HOLD_SENTINEL
    assert _classify(policy, {"source": "gov24", "biz_end": "2026-01-01"}, as_of) == HOLD_SENTINEL
    assert _classify(policy, {"source_id": "G-1", "biz_end": "2026-01-01"}, as_of) == HOLD_SENTINEL
    assert _classify(policy, base, "04/09/2026") == HOLD_SENTINEL
    assert _classify(policy, base, None) == HOLD_SENTINEL
    assert _classify(policy, base, as_of, corpus_pinned=False) == HOLD_SENTINEL
    assert _classify(policy, base, as_of, checker_executed=False) == HOLD_SENTINEL


def test_no_free_text_eligible_default_semantics():
    policy = _load(POLICY)
    assert policy["classification_inputs"]["corpus_row_fields"] == ["source", "source_id", "biz_end"]
    note = policy["classification_inputs"]["corpus_note"]
    for forbidden in ["신청기한", "add_qualify", "LLM", "protected labels"]:
        assert forbidden in note, f"forbidden-input exclusion must be explicit: {forbidden}"
    assert policy["removal_no_default_replacement"] is True
    for key in _walk_keys(policy):
        assert "eligib" not in key.lower(), f"normative key must not use eligible: {key}"


def test_denominators_and_gate_truth_table():
    policy = _load(POLICY)
    den = policy["audit_scope"]["denominators"]
    assert (den["dev_tasks"], den["dev_slots"]) == (180, 900)
    assert (den["holdout_tasks"], den["holdout_slots"]) == (250, 1250)
    assert "ABSTAIN" in policy["audit_scope"]["coverage"] and "CLARIFY" in policy["audit_scope"]["coverage"]
    assert _gate(policy, 0, 0) == "PASS"
    assert _gate(policy, 1, 1) == "NO-GO"
    assert _gate(policy, 0, 3) == "NO-GO"
    assert _gate(policy, 0, 0, measured=False) == "HOLD"


def test_as_of_pin_semantics_explicit():
    policy = _load(POLICY)
    pin = policy["evaluation_as_of_date"]
    assert pin["format"] == "YYYY-MM-DD"
    assert pin["timezone"] == "Asia/Seoul"
    assert "run_start" in pin["capture"] and "BEFORE" in pin["capture"]
    assert "Immutable" in pin["mutability"] or "immutable" in pin["mutability"]
    assert "paired D-003 baseline" in pin["mutability"]
    # this freeze sets no value: the artifact carries semantics only, never a date value
    assert "value" not in pin, "freeze must not pin an evaluation date value"


def test_eligible_absent_from_normative_gate_keys():
    policy = _load(POLICY)
    assert policy["removed_from_gate_semantics"] == ["eligible"]
    assert policy["removal_no_default_replacement"] is True
    # historical prose may reference the removed boolean only as superseded history
    assert "eligible" in policy["removal_note"] or "eligible" in policy["supersedes"]["gate"]


def test_no_dynamic_time_or_side_effect_imports_in_this_test():
    own = Path(__file__).read_text(encoding="utf-8")
    for dynamic in ["datetime" + ".now", "timezone" + ".now", "time" + ".now", "clock" + "()", "today" + "()"]:
        assert dynamic not in own, f"pure evaluator must not use dynamic time: {dynamic}"
    for mod in ["subprocess", "sqlite3", "requests", "httpx", "urllib", "http.client",
                "torch", "transformers", "sklearn", "psycopg", "asyncpg", "socket"]:
        assert f"import {mod}" not in own and f"from {mod}" not in own, \
            f"pure contract test must not import {mod}"


def test_v3_stage_local_truth():
    v3 = _load(PLAN_V3)
    assert v3["frozen_at"] == EXPECTED_V3_FROZEN_AT
    assert "Muse Spark 1.3" in v3["provenance"]["created_by"]
    assert "no DB query" in v3["provenance"]["investigation_basis"]
    assert "no DB query of any kind" in v3["assertions"]["no_retrieval_execution"]
    assert "No evaluation_as_of_date value set" in v3["assertions"]["no_as_of_date_set"]
    assert v3["supersession"]["decision"] == "D-052"
    assert "not result-driven relaxation" in v3["supersession"]["not_result_driven"]
