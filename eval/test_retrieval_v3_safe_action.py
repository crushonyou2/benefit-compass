"""Retrieval v3 safe-action freeze tests (pure/static only).

Proves for the D-049 DESIGN/FREEZE stage (no runner/safety/production change):
- candidate-plan-v2 preserves every v1 ranking tuple, ranking/final-pool/selection semantic,
  MAX24 cap, D-003 baseline, embedding, Candidate-B gate, and integer/latency/audit contracts;
- exactly ONE action policy exists, fixed and common to all 18 configs (not a tuning axis,
  MAX24 not expanded);
- the policy JSON is machine-recomputable (reference evaluator is built FROM the artifact),
  deterministic, reads only query_text (forbidden eval-label inputs absent), and uses no
  score/threshold cutoff;
- representative PURE fixtures cover ANSWER/ABSTAIN/CLARIFY and precedence. Fixtures prove
  mechanics only — they do NOT claim protected safety performance.

No DB, no network, no model/embedding, no retrieval execution, no protected plaintext.
"""
from __future__ import annotations

import hashlib
import json
import unicodedata
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PLAN_V1 = REPO / "eval" / "retrieval-v3" / "candidate-plan" / "candidate-plan-v1.json"
PLAN_V2 = REPO / "eval" / "retrieval-v3" / "candidate-plan" / "candidate-plan-v2.json"
POLICY = REPO / "eval" / "retrieval-v3" / "candidate-plan" / "safe-action-policy-v1.json"

EXPECTED_POLICY_SHA = "c512fb5627179697a987b05a2431b8f7e30d1153af2ff6dca37995f6b232a35d"
EXPECTED_V1_SHA = "2815361a469fee9bf69f6ffdf2124d19928220535cdb08b2005ae6674ae7d17c"
EXPECTED_PREREG_SHA = "7842018613d66aa4570f4db2f8ae5a698ceb46757995a6b7e26873177b36160e"

# Keys that must be value-identical between v1 and v2 (everything except the
# version-identity metadata and the newly added freeze blocks).
PRESERVED_KEYS = [
    "allowed_axes", "assertions", "base_commit", "base_commit_tag", "baseline_identity",
    "branch", "candidate_b_gate", "candidate_family", "configs", "cosine_min_placement",
    "deterministic_ordering_contract", "exact_oracle_semantics", "forbidden_axes",
    "fusion_semantics", "gating_contract_ref", "max_configs", "parameter_semantics",
    "policy_comparison_vector", "secondary_diagnostics_D026", "selection_rule",
    "standing_contract_refs",
]


def _load(path: Path) -> dict:
    return json.loads(path.read_bytes().decode("utf-8"))


def _norm(q: str, steps: list[str]) -> str:
    # norm-v1 reference: NFC -> strip -> collapse whitespace -> casefold.
    assert steps == ["NFC normalize", "strip leading/trailing whitespace",
                     "collapse every internal run of whitespace ([\\s]+) to one ASCII space",
                     "casefold"], "normalization steps changed — policy no longer machine-recomputable"
    import re
    n = unicodedata.normalize("NFC", q)
    n = n.strip()
    n = re.sub(r"[\s]+", " ", n)
    return n.casefold()


def _decide(policy: dict, query_text: str) -> str:
    """Reference evaluator built strictly FROM the frozen artifact (proves recomputability)."""
    assert set(policy["allowed_input_schema"].keys()) == {"query_text"}
    n = _norm(query_text, policy["normalization"]["steps"])
    if n == "":
        return "ABSTAIN"
    lex = policy["lexicons"]
    if any(u in n for u in lex["U_ABSTAIN"]["entries"]):
        return "ABSTAIN"
    if any(g in n for g in lex["G_BENEFIT"]["entries"]) and any(
            r in n for r in lex["R_FRAME"]["entries"]):
        return "CLARIFY"
    return "ANSWER"


def test_policy_artifact_sha_pinned():
    sha = hashlib.sha256(POLICY.read_bytes()).hexdigest()
    assert sha == EXPECTED_POLICY_SHA, f"policy bytes changed: {sha}"


def test_plan_v1_untouched():
    sha = hashlib.sha256(PLAN_V1.read_bytes()).hexdigest()
    assert sha == EXPECTED_V1_SHA, f"plan-v1 must stay immutable: {sha}"


def test_v2_parents_and_identity():
    v2 = _load(PLAN_V2)
    assert v2["plan_id"] == "retrieval-v3-candidate-plan-v2"
    assert v2["parents"]["prereg_sha256"] == EXPECTED_PREREG_SHA
    assert v2["parents"]["candidate_plan_v1_sha256"] == EXPECTED_V1_SHA
    assert v2["safe_action_policy"]["policy_sha256"] == EXPECTED_POLICY_SHA
    assert v2["safe_action_policy"]["policy_id"] == "retrieval-v3-safe-action-policy-v1"


def test_v1_to_v2_18_tuple_identity():
    v1 = _load(PLAN_V1)
    v2 = _load(PLAN_V2)
    assert [c["config_id"] for c in v2["configs"]] == [f"candidate-a-{i:02d}" for i in range(1, 19)]
    assert v2["configs"] == v1["configs"], "all 18 ranking tuples must be exactly identical"


def test_v1_to_v2_contracts_preserved():
    v1 = _load(PLAN_V1)
    v2 = _load(PLAN_V2)
    for key in PRESERVED_KEYS:
        assert v2[key] == v1[key], f"contract key changed in v2: {key}"
    assert v2["max_configs"] == 24, "MAX24 must not expand"


def test_single_common_action_policy_not_tuning_axis():
    v2 = _load(PLAN_V2)
    sap = v2["safe_action_policy"]
    assert sap["common_to_all_configs"] is True
    assert sap["not_a_tuning_axis"] is True
    assert sap["does_not_expand_max24"] is True
    for c in v2["configs"]:
        assert "action" not in json.dumps(c), f"per-config action variant forbidden: {c['config_id']}"

def test_policy_uses_no_score_threshold():
    policy = _load(POLICY)
    # Structural (not prose-substring): no numeric cutoff can hide in the artifact because
    # the artifact carries no numeric JSON values at all, and no key names a score family.
    def walk(node):
        if isinstance(node, dict):
            for k, v in node.items():
                yield ("key", k)
                yield from walk(v)
        elif isinstance(node, list):
            for v in node:
                yield from walk(v)
        elif isinstance(node, (int, float)) and not isinstance(node, bool):
            yield ("number", node)
        elif isinstance(node, str):
            yield ("string", node)
    kinds = list(walk(policy))
    assert not [v for k, v in kinds if k == "number"], "policy must carry no numeric cutoff values"
    for k, v in kinds:
        if k == "key":
            low = v.lower()
            for banned in ("cosine", "threshold", "cutoff", "score", "embedding", "rerank"):
                assert banned not in low, f"score/threshold/model key in policy: {v}"
    for _name, lex in policy["lexicons"].items():
        assert all(isinstance(e, str) for e in lex["entries"]), "lexicons are finite string sets only"
    assert set(policy["allowed_input_schema"].keys()) == {"query_text"}
    forbidden = " ".join(policy["forbidden_input_schema"]).lower()
    for required in ("stratum", "gold", "task id", "annotation", "protected metadata",
                     "labels", "results", "score", "embedding", "retrieval"):
        assert required in forbidden, f"forbidden-input schema must name: {required}"


def test_policy_deterministic():
    policy = _load(POLICY)
    queries = ["서울 지원금 받고 싶어요", "서울 청년 월세", "외국인 관광객 교통비 지원",
               "청년 혜택 뭐 있죠", "햇살론유스 어디서 신청함", ""]
    for q in queries:
        assert _decide(policy, q) == _decide(policy, q)
    # Normalization invariance: surrounding space / case must not change the action.
    assert _decide(policy, "  서울 지원금 받고 싶어요 ") == _decide(policy, "서울 지원금 받고 싶어요")


def test_fixtures_abstain():
    policy = _load(POLICY)
    for q in ("외국인 관광객 교통비 지원 신청 방법",
              "암호화폐 투자 지원금 있나요",
              "골프 회원권 지원 사업 알려줘"):
        assert _decide(policy, q) == "ABSTAIN", q


def test_fixtures_clarify():
    policy = _load(POLICY)
    for q in ("서울 지원금 받고 싶어요",
              "청년 혜택 뭐 있죠",
              "주거 지원 알려줘요"):
        assert _decide(policy, q) == "CLARIFY", q


def test_fixtures_answer():
    policy = _load(POLICY)
    for q in ("서울 청년 월세",
              "햇살론유스 어디서 신청함",
              "청년수당 신청기간 언제까지에요",
              "육아휴직 급여"):
        assert _decide(policy, q) == "ANSWER", q


def test_fixture_precedence_and_blank():
    policy = _load(POLICY)
    # U_ABSTAIN wins over a simultaneous G+R match.
    assert _decide(policy, "암호화폐 투자 지원금 있나요") == "ABSTAIN"
    assert _decide(policy, "골프 회원권 지원 사업 알려줘") == "ABSTAIN"
    # Blank fails closed (unreachable on frozen dev, which validates non-blank).
    assert _decide(policy, "") == "ABSTAIN"
    assert _decide(policy, "   ") == "ABSTAIN"
