"""Retrieval v3 production-exclusion timezone parity contract tests (pure/static only).

D-053 SAME-STAGE Web-HOLD narrow repair: D-052 policy-v1 froze evaluation_as_of_date as
Asia/Seoul and called it the explicit-date equivalent of D-003 CURRENT_DATE, but Web
independent-review read-only DB evidence showed SHOW TimeZone = GMT with
SELECT CURRENT_DATE = 2026-09-03 while the Asia/Seoul local date was already 2026-09-04.
Policy-v2 supersedes ONLY the timezone/as-of capture semantics; plan-v4 is an append-only
deep copy of plan-v3 with only the authorized capture-reference updates.

Proves (no DB/network/model/retrieval/protected execution):
- D-052 and older artifacts byte/SHA unchanged (policy-v1, doc-v1, plan-v3, prereg,
  plan-v2, safe-action policy/doc, eligibility doc).
- v3 -> v4 configs/ranking/action/selection/gate thresholds identical except the
  authorized policy ref/prose + identity/parent/provenance/supersession metadata.
- Policy-v2 has no normative hardcoded timezone and no local-date fallback; observed
  values appear only as non-normative historical/evidence prose.
- Capture contract requires exactly SHOW TimeZone + SELECT CURRENT_DATE once, before
  protected access/run_start, on the governing connection, with no timezone override, one
  pinned date shared by candidate + paired baseline, and HOLD on missing/error.
- Predicate fixtures, denominators, and truth table unchanged.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PREREG = REPO / "docs" / "RETRIEVAL_V3_PREREG.md"
PLAN_V1 = REPO / "eval" / "retrieval-v3" / "candidate-plan" / "candidate-plan-v1.json"
PLAN_V2 = REPO / "eval" / "retrieval-v3" / "candidate-plan" / "candidate-plan-v2.json"
PLAN_V3 = REPO / "eval" / "retrieval-v3" / "candidate-plan" / "candidate-plan-v3.json"
PLAN_V4 = REPO / "eval" / "retrieval-v3" / "candidate-plan" / "candidate-plan-v4.json"
POLICY_V1 = REPO / "eval" / "retrieval-v3" / "candidate-plan" / "production-exclusion-policy-v1.json"
POLICY_V2 = REPO / "eval" / "retrieval-v3" / "candidate-plan" / "production-exclusion-policy-v2.json"
SAFE_POLICY = REPO / "eval" / "retrieval-v3" / "candidate-plan" / "safe-action-policy-v1.json"
SAFE_DOC = REPO / "docs" / "RETRIEVAL_V3_SAFE_ACTION_SUPERSESSION_V1.md"
ELIG_DOC = REPO / "docs" / "RETRIEVAL_V3_ELIGIBILITY_EVIDENCE_V1.md"
SUPER_DOC_V1 = REPO / "docs" / "RETRIEVAL_V3_PRODUCTION_EXCLUSION_SUPERSESSION_V1.md"
SUPER_DOC_V2 = REPO / "docs" / "RETRIEVAL_V3_PRODUCTION_EXCLUSION_SUPERSESSION_V2.md"

EXPECTED_PREREG_SHA = "7842018613d66aa4570f4db2f8ae5a698ceb46757995a6b7e26873177b36160e"
EXPECTED_V1_SHA = "2815361a469fee9bf69f6ffdf2124d19928220535cdb08b2005ae6674ae7d17c"
EXPECTED_V2_SHA = "d233f5c4d912e4d0856d89213d6392fbf44494f5538d018e7412f61781ae6cc6"
EXPECTED_SAFE_POLICY_SHA = "c512fb5627179697a987b05a2431b8f7e30d1153af2ff6dca37995f6b232a35d"
EXPECTED_SAFE_DOC_SHA = "472b6183114a0ebf4d22e9b22c03bb9233b15a736587e29a917aa49113502364"
EXPECTED_ELIG_DOC_SHA = "eea3c5ce393f1f3c9563983df16f4648e9c005fd4f317b44cd168b082af91d32"

EXPECTED_POLICY_V1_SHA = "3bcfc5b8360af28ccd7ea9018f3e3ffda73fba7744ba33bbfb83446235284608"
EXPECTED_SUPER_V1_SHA = "63cdc4325b10c75cdb468ce775043c351ec22326642b70f0763189b846936fdc"
EXPECTED_V3_SHA = "665771f991a3891869f7d27658eedacbed28ba522afdcadcf8edd4d62b412681"

EXPECTED_POLICY_V2_SHA = "6fee9ec22d5d3ac153ff19a6b1b5d27ab6a6a43bda11e35821d689f938968fe5"
EXPECTED_SUPER_V2_SHA = "9767b6c79e08a992a687db033e3eb63b7fdd3c7eb9b7c5013e1afc6eefd4ca7b"
EXPECTED_V4_SHA = "a25d9c482094696ff7a438593979813ac568c91a977a2543a50618ca4f5177d6"
EXPECTED_V4_FROZEN_AT = "2026-09-04T01:27:33+09:00"

# v3 top-level keys that must be value-identical in v4. Stage-local plan_id/version/parents,
# the authorized policy-ref fields, and provenance/assertions/supersession/frozen_at are
# deliberately EXCLUDED and pinned by dedicated tests below.
PRESERVED_V3_V4 = [
    "allowed_axes", "baseline_identity", "base_commit", "base_commit_tag", "branch",
    "candidate_b_gate", "candidate_family", "configs", "cosine_min_placement",
    "deterministic_ordering_contract", "exact_oracle_semantics", "forbidden_axes",
    "fusion_semantics", "gating_contract_ref", "max_configs", "parameter_semantics",
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
        y, m, d = (int(x) for x in s.split("-"))
        if not (1 <= m <= 12 and 1 <= d <= 31 and 1900 <= y <= 2100):
            return False
    except ValueError:
        return False
    return True


def _classify(policy: dict, row: object, as_of_date: object,
              corpus_pinned: bool = True, checker_executed: bool = True) -> str:
    """Reference evaluator built strictly FROM the frozen artifact.

    Mirrors the predicate/null/fail-closed/as-of semantics without adding rules.
    """
    if not corpus_pinned or not checker_executed:
        return HOLD_SENTINEL
    if not isinstance(row, dict):
        return HOLD_SENTINEL
    if row.get("source") is None or row.get("source_id") is None:
        return HOLD_SENTINEL
    if not _valid_iso_date(as_of_date):
        return HOLD_SENTINEL
    biz_end = row.get("biz_end")
    if biz_end is None:
        assert policy["null_rule"]["classification"] == "not_production_excluded_by_D003_predicate"
        return "not_production_excluded_by_D003_predicate"
    if not _valid_iso_date(biz_end):
        return HOLD_SENTINEL
    as_of = policy.get("evaluation_as_of_date", {})
    assert isinstance(as_of.get("mutability"), str) and "Immutable" in as_of["mutability"]
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
    assert _sha(SAFE_DOC) == EXPECTED_SAFE_DOC_SHA, "safe-action doc must stay immutable"
    assert _sha(ELIG_DOC) == EXPECTED_ELIG_DOC_SHA, "eligibility evidence doc must stay immutable"
    assert _sha(POLICY_V1) == EXPECTED_POLICY_V1_SHA, "D-052 policy-v1 must stay immutable"
    assert _sha(SUPER_DOC_V1) == EXPECTED_SUPER_V1_SHA, "D-052 supersession V1 doc must stay immutable"
    assert _sha(PLAN_V3) == EXPECTED_V3_SHA, "plan-v3 must stay immutable"


def test_new_artifact_shas_pinned():
    assert _sha(POLICY_V2) == EXPECTED_POLICY_V2_SHA, "policy-v2 bytes changed"
    assert _sha(SUPER_DOC_V2) == EXPECTED_SUPER_V2_SHA, "supersession V2 doc bytes changed"
    assert _sha(PLAN_V4) == EXPECTED_V4_SHA, "plan-v4 bytes changed"


def test_v4_parents_carry_all_identities():
    v4 = _load(PLAN_V4)
    parents = v4["parents"]
    assert parents["prereg_sha256"] == EXPECTED_PREREG_SHA
    assert parents["candidate_plan_v1_sha256"] == EXPECTED_V1_SHA
    assert parents["candidate_plan_v2_sha256"] == EXPECTED_V2_SHA
    assert parents["candidate_plan_v3_sha256"] == EXPECTED_V3_SHA
    assert parents["safe_action_policy_sha256"] == EXPECTED_SAFE_POLICY_SHA
    assert parents["production_exclusion_policy_sha256"] == EXPECTED_POLICY_V2_SHA
    assert parents["supersession_doc_sha256"] == EXPECTED_SUPER_V2_SHA
    assert _sha(REPO / parents["prereg"]) == EXPECTED_PREREG_SHA
    assert _sha(REPO / parents["candidate_plan_v3"]) == EXPECTED_V3_SHA
    assert _sha(REPO / parents["production_exclusion_policy"]) == EXPECTED_POLICY_V2_SHA
    assert _sha(REPO / parents["supersession_doc"]) == EXPECTED_SUPER_V2_SHA


def test_v3_to_v4_substantive_identity():
    v3 = _load(PLAN_V3)
    v4 = _load(PLAN_V4)
    for key in PRESERVED_V3_V4:
        assert v4[key] == v3[key], f"v4 must preserve v3[{key}]"
    assert len(v4["configs"]) == 18
    for c3, c4 in zip(v3["configs"], v4["configs"]):
        assert c4 == c3, "all 18 ranking configs must be identical"
    assert v4["safe_action_policy"]["not_a_tuning_axis"] is True


def test_v4_selection_rule_authorized_diff_only():
    v3 = _load(PLAN_V3)
    v4 = _load(PLAN_V4)
    s3, s4 = v3["selection_rule"], v4["selection_rule"]
    for key in s3:
        if key != "safety_gates_dev":
            assert s4[key] == s3[key], f"selection_rule[{key}] must be identical"
    g3, g4 = s3["safety_gates_dev"], s4["safety_gates_dev"]
    for key in g3:
        if key != "production_exclusion_intrusion":
            assert g4[key] == g3[key], f"safety gate [{key}] must be identical"
    assert "production-exclusion-policy-v1" in g3["production_exclusion_intrusion"]
    assert "production-exclusion-policy-v2" in g4["production_exclusion_intrusion"]
    assert g4["production_exclusion_intrusion"].replace(
        "production-exclusion-policy-v2", "production-exclusion-policy-v1") == g3["production_exclusion_intrusion"]
    assert "0/180" in g4["production_exclusion_intrusion"] and "0/900" in g4["production_exclusion_intrusion"]
    assert "NO-GO" in g4["production_exclusion_intrusion"] and "HOLD" in g4["production_exclusion_intrusion"]


def test_v4_policy_block_and_identity():
    v3 = _load(PLAN_V3)
    v4 = _load(PLAN_V4)
    assert v4["plan_id"] == "retrieval-v3-candidate-plan-v4"
    assert v4["version"] == "4.0.0"
    block = v4["production_exclusion_policy"]
    assert block["policy_id"] == "retrieval-v3-production-exclusion-policy-v2"
    assert block["policy_sha256"] == EXPECTED_POLICY_V2_SHA
    assert block["policy_artifact"].endswith("production-exclusion-policy-v2.json")
    assert block["supersession_artifact"].endswith("SUPERSESSION_V2.md")
    assert block["common_to_all_configs"] is True
    assert block["not_a_tuning_axis"] is True
    assert block["does_not_expand_max24"] is True
    assert block["scope"] == v3["production_exclusion_policy"]["scope"]
    assert v4["assertions"]["deterministic"] == v3["assertions"]["deterministic"]
    assert v4["assertions"]["production_diff"] == v3["assertions"]["production_diff"]
    assert "D-053" in v4["assertions"]["no_retrieval_execution"]
    assert "no DB query of any kind" in v4["assertions"]["no_retrieval_execution"]


def test_v4_no_seoul_date_source():
    v4 = _load(PLAN_V4)
    rest = {k: v for k, v in v4.items() if k not in ("provenance", "supersession")}
    rest_text = json.dumps(rest, ensure_ascii=False)
    assert "Asia/Seoul" not in rest_text, \
        "plan-v4 must not claim Asia/Seoul as production-exclusion date source"
    assert "GMT" not in rest_text, \
        "GMT may appear only as quoted Web evidence in stage-local provenance"
    sup_text = json.dumps(v4["supersession"], ensure_ascii=False)
    assert "Asia/Seoul" in sup_text and "policy-v1" in sup_text, \
        "supersession must name the superseded v1 claim explicitly as history"
    prov_text = json.dumps(v4["provenance"], ensure_ascii=False)
    assert "GMT" in prov_text and "2026-09-03" in prov_text and "2026-09-04" in prov_text, \
        "provenance must quote the Web mismatch evidence truthfully"


def test_policy_v2_capture_contract_exact():
    policy = _load(POLICY_V2)
    pin = policy["evaluation_as_of_date"]
    assert pin["format"] == "YYYY-MM-DD"
    assert pin["capture_statements"] == ["SHOW TimeZone", "SELECT CURRENT_DATE"], \
        "allowed capture SQL inventory is exactly these two statements"
    assert "run_start" in pin["capture_timing"] and "BEFORE" in pin["capture_timing"]
    assert "protected plaintext access" in pin["capture_timing"]
    assert "exactly once" in pin["capture_timing"]
    assert "governing the pinned evaluation corpus" in pin["capture_connection"]
    assert "paired D-003 baseline" in pin["capture_connection"]
    assert "SET TIME ZONE" in pin["capture_override_prohibition"]
    assert "Do NOT" in pin["capture_override_prohibition"]
    assert "db_session_timezone" in pin["pin"] and "as returned" in pin["pin"]
    assert "Immutable" in pin["mutability"]
    assert "Candidate A and the paired D-003 baseline" in pin["mutability"]
    assert ":evaluation_as_of_date" in pin["mutability"], \
        "both sides must use the explicit pinned date to avoid midnight drift"
    assert "HOLD" in pin["fail_closed"] and "never fall back" in pin["fail_closed"]
    assert "value" not in pin, "freeze must not pin an evaluation date value"
    conds = " | ".join(policy["fail_closed"]["conditions"])
    assert "SHOW TimeZone / SELECT CURRENT_DATE" in conds, \
        "capture failure must fail closed"
    assert policy["fail_closed"]["result"] == "HOLD/fail-closed, never PASS"


def test_policy_v2_no_normative_timezone_or_fallback():
    policy = _load(POLICY_V2)
    normative = {k: v for k, v in policy.items() if k not in ("supersedes", "provenance")}
    normative_text = json.dumps(normative, ensure_ascii=False)
    assert "Asia/Seoul" not in normative_text, \
        "no normative hardcoded timezone allowed; history lives in supersedes only"
    assert "GMT" not in normative_text, \
        "observed GMT is evidence only; it must not appear in normative contract text"
    assert normative_text.count("UTC") == 1 and "never fall back to OS/user/local/UTC" in normative_text, \
        "UTC may appear only in the never-fallback prohibition"
    hist = json.dumps(policy["supersedes"], ensure_ascii=False)
    assert "Asia/Seoul" in hist and "superseded" in hist.lower() or "historical/superseded" in hist, \
        "v1 timezone claim must be marked historical/superseded"
    assert "timezone" in policy["db_session_timezone"]["role"].lower() or \
        "Provenance only" in policy["db_session_timezone"]["role"]
    assert policy["db_session_timezone"]["recording"].startswith("Recorded as returned")


def test_policy_v2_preserved_semantics_vs_v1():
    v1 = _load(POLICY_V1)
    v2 = _load(POLICY_V2)
    assert v2["gate"] == v1["gate"]
    assert v2["safety_claim_boundary"] == v1["safety_claim_boundary"]
    assert v2["classification_inputs"]["corpus_row_fields"] == ["source", "source_id", "biz_end"]
    assert v2["classification_inputs"]["corpus_note"] == v1["classification_inputs"]["corpus_note"]
    assert v2["predicate"]["production_excluded"] == v1["predicate"]["production_excluded"]
    assert v2["predicate"]["decision_values"] == v1["predicate"]["decision_values"]
    assert v2["null_rule"] == v1["null_rule"]
    assert v2["audit_scope"] == v1["audit_scope"]
    assert v2["gate_truth_table"] == v1["gate_truth_table"]
    assert v2["removed_from_gate_semantics"] == ["eligible"]
    assert v2["removal_no_default_replacement"] is True
    assert v2["removal_note"] == v1["removal_note"]
    assert v2["youth_diagnostic_note"] == v1["youth_diagnostic_note"]
    assert v2["d003_runtime_reference"]["predicate_sql"] == "(biz_end IS NULL OR biz_end >= CURRENT_DATE)"
    assert v2["supersedes"]["policy_sha256"] == EXPECTED_POLICY_V1_SHA
    assert v2["parents"]["production_exclusion_policy_v1_sha256"] == EXPECTED_POLICY_V1_SHA
    assert v2["parents"]["supersession_doc_v1_sha256"] == EXPECTED_SUPER_V1_SHA


def test_current_date_confined_to_capture_and_d003_reference():
    policy = _load(POLICY_V2)
    ref = policy["d003_runtime_reference"]
    assert "CURRENT_DATE" in json.dumps(ref, ensure_ascii=False), \
        "D-003 runtime reference must quote the production predicate"
    # v2 legitimately names SELECT CURRENT_DATE in the capture contract it freezes;
    # every other occurrence must live in one of these expected sections.
    allowed = {"d003_runtime_reference", "evaluation_as_of_date", "db_session_timezone",
               "predicate", "fail_closed", "supersedes", "provenance"}
    for key, value in policy.items():
        if key not in allowed:
            assert "CURRENT_DATE" not in json.dumps(value, ensure_ascii=False), \
                f"CURRENT_DATE outside capture/D-003 sections: {key}"


def test_predicate_fixtures_before_equal_after_null():
    policy = _load(POLICY_V2)
    as_of = "2026-09-04"
    base = {"source": "gov24", "source_id": "G-1", "biz_end": "2026-01-01"}
    assert _classify(policy, base, as_of) == "production_excluded"
    assert _classify(policy, {**base, "biz_end": "2026-09-03"}, as_of) == "production_excluded"
    assert _classify(policy, {**base, "biz_end": "2026-09-04"}, as_of) == "not_production_excluded_by_D003_predicate"
    assert _classify(policy, {**base, "biz_end": "2026-09-05"}, as_of) == "not_production_excluded_by_D003_predicate"
    assert _classify(policy, {**base, "biz_end": None}, as_of) == "not_production_excluded_by_D003_predicate"
    assert "not_production_excluded_by_D003_predicate" not in ("not expired", "eligible")


def test_fail_closed_fixtures():
    policy = _load(POLICY_V2)
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


def test_denominators_and_gate_truth_table():
    policy = _load(POLICY_V2)
    den = policy["audit_scope"]["denominators"]
    assert (den["dev_tasks"], den["dev_slots"]) == (180, 900)
    assert (den["holdout_tasks"], den["holdout_slots"]) == (250, 1250)
    assert "ABSTAIN" in policy["audit_scope"]["coverage"] and "CLARIFY" in policy["audit_scope"]["coverage"]
    assert _gate(policy, 0, 0) == "PASS"
    assert _gate(policy, 1, 1) == "NO-GO"
    assert _gate(policy, 0, 3) == "NO-GO"
    assert _gate(policy, 0, 0, measured=False) == "HOLD"


def test_eligible_absent_from_normative_gate_keys():
    policy = _load(POLICY_V2)
    for key in _walk_keys(policy):
        assert "eligib" not in key.lower(), f"normative key must not use eligible: {key}"
    assert "eligible" in policy["removal_note"] or "eligible" in policy["supersedes"]["policy"]


def test_doc_v2_records_evidence_truthfully():
    doc = SUPER_DOC_V2.read_text(encoding="utf-8")
    for required in ["SHOW TimeZone", "SELECT CURRENT_DATE", "GMT", "2026-09-03",
                     "2026-09-04", "D-052", "D-053", "policy-v2", "plan-v4",
                     "STOP for Web", "6fee9ec2", "3bcfc5b8", "665771f9"]:
        assert required in doc, f"V2 doc must record: {required}"
    assert "Asia/Seoul" in doc, "V2 doc must name the superseded v1 claim explicitly"


def test_v4_stage_local_truth():
    v4 = _load(PLAN_V4)
    assert v4["frozen_at"] == EXPECTED_V4_FROZEN_AT
    assert "Muse Spark 1.3" in v4["provenance"]["created_by"]
    assert "no live DB probe" in v4["provenance"]["investigation_basis"]
    assert "no DB query of any kind" in v4["assertions"]["no_retrieval_execution"]
    assert "No evaluation_as_of_date value set" in v4["assertions"]["no_as_of_date_set"]
    assert v4["supersession"]["decision"] == "D-053"
    assert "not result-driven relaxation" in v4["supersession"]["not_result_driven"]


def test_no_dynamic_time_or_side_effect_imports_in_this_test():
    own = Path(__file__).read_text(encoding="utf-8")
    for dynamic in ["datetime" + ".now", "timezone" + ".now", "time" + ".now", "clock" + "()", "today" + "()"]:
        assert dynamic not in own, f"pure evaluator must not use dynamic time: {dynamic}"
    for mod in ["subprocess", "sqlite3", "requests", "httpx", "urllib", "http.client",
                "torch", "transformers", "sklearn", "psycopg", "asyncpg", "socket"]:
        assert f"import {mod}" not in own and f"from {mod}" not in own, \
            f"pure contract test must not import {mod}"
