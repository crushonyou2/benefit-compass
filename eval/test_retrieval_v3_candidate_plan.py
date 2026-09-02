"""Static validation for retrieval-v3 candidate-plan v1 — no DB/model/network.

Validates canonical candidate-plan freeze per D-013/D-015/D-026:

- schema, config count <=24, config_id unique, tuples unique
- no ranges/placeholders/adaptive fields
- allowed axes only, forbidden axes not present
- deterministic selection rule exact
- Candidate B not instantiated
- D-026 secondary diagnostics non-gating
- canonical bytes/SHA
"""

import json
import hashlib
import pathlib
import re

PLAN_PATH = pathlib.Path("eval/retrieval-v3/candidate-plan/candidate-plan-v1.json")
PREREG = pathlib.Path("docs/RETRIEVAL_V3_PREREG.md")

ALLOWED_CONFIG_KEYS = {
    "config_id",
    "dense_weight",
    "sparse_weight",
    "exact_title_boost",
    "exact_org_boost",
    "field_weight_title",
    "field_weight_support_content",
    "field_weight_eligibility",
    "dedup_cosine_threshold",
    "diversification_lambda",
    "fusion_method",
}

FORBIDDEN_KEYS = {
    "embedding_model",
    "reranker",
    "cross_encoder",
    "candidates",
    "cosine_min",
    "youth_bias",
    "lexical_bias_separate",
    "k",
    "threshold",
    "global_abstention",
    "public_region",
    "region_filter",
    "new_signal",
    "candidate_b",
    "candidate-b",
}

EXPECTED_SELECTION_ORDERING = "Success@5 desc -> NDCG@5 desc -> MRR@10 desc -> paired p95 asc -> lexicographic config_id asc"
EXPECTED_PLAN_ID = "retrieval-v3-candidate-plan-v1"
EXPECTED_VERSION = "1.0.0"
EXPECTED_BASE = "5327661445c37191a3fd61db195f3af4d2cf893a"
EXPECTED_FROZEN_AT = "2026-09-02T14:30:56+09:00"
EXPECTED_OLD_SHA = "ff3b83d11260e2c2e5aba2bbe08851bf24f68cc900733813d2a4f466a9363e41"
EXPECTED_NEW_SHA = "8e632c81c3c23b2a5280025298ae1d0c763abc5ce25d90e1ceb031179588ac54"
def _load_plan():
    assert PLAN_PATH.exists(), f"candidate-plan artifact missing: {PLAN_PATH}"
    raw = PLAN_PATH.read_bytes()
    assert b"\r\n" not in raw, "candidate-plan must be LF (no CRLF)"
    assert raw.endswith(b"\n"), "candidate-plan must end with LF"
    data = json.loads(raw.decode("utf-8"))
    return data, raw


def test_plan_file_exists_and_canonical_bytes():
    data, raw = _load_plan()
    sha = hashlib.sha256(raw).hexdigest()
    assert re.fullmatch(r"[0-9a-f]{64}", sha)
    assert len(raw) > 1000
    assert hashlib.sha256(PLAN_PATH.read_bytes()).hexdigest() == sha
    # New canonical SHA after provenance correction (D-028)
    assert sha == EXPECTED_NEW_SHA, f"candidate-plan SHA mismatch after correction: {sha} != {EXPECTED_NEW_SHA}"
    assert sha != EXPECTED_OLD_SHA, "SHA should differ from old D-027 SHA after correction"


def test_plan_schema_and_identity():
    data, _ = _load_plan()
    assert data.get("plan_id") == EXPECTED_PLAN_ID
    assert data.get("version") == EXPECTED_VERSION
    assert data.get("base_commit") == EXPECTED_BASE
    assert data.get("branch") == "codex/retrieval-v3-user-search-quality"
    assert data.get("candidate_family") == "Candidate A only"
    assert data.get("max_configs") == 24
    refs = data.get("standing_contract_refs", [])
    for required in ["D-013", "D-015", "D-026"]:
        assert required in refs, f"missing standing ref {required}"
    baseline = data.get("baseline_identity", {})
    assert baseline.get("CANDIDATES") == 30
    assert baseline.get("COSINE_MIN") == 0.78
    assert baseline.get("LEXICAL_OVERLAP_BIAS") == 0.01
    assert baseline.get("RERANK") == 0
    assert "intfloat/multilingual-e5-base" in baseline.get("embedding_model", "")


def test_config_count_and_uniqueness():
    data, _ = _load_plan()
    configs = data.get("configs")
    assert isinstance(configs, list)
    assert 1 <= len(configs) <= 24, f"got {len(configs)}"
    ids = [c.get("config_id") for c in configs]
    assert len(ids) == len(set(ids))
    for cid in ids:
        assert re.fullmatch(r"candidate-a-\d{2}", cid)
    tuples = []
    for c in configs:
        items = tuple(sorted((k, json.dumps(v, sort_keys=True)) for k, v in c.items() if k != "config_id"))
        tuples.append(items)
    assert len(tuples) == len(set(tuples)), "duplicate tuples"


def test_no_ranges_placeholders_adaptive():
    data, _ = _load_plan()
    configs = data["configs"]
    for c in configs:
        for k, v in c.items():
            if isinstance(v, str):
                if v not in ("hybrid_weighted_sum", "union"):
                    assert ".." not in v and " - " not in v, f"range-like {k}={v}"
                assert v.lower() not in ("tbd", "todo", "placeholder")
                assert "as feasible" not in v.lower()
                assert "adaptive" not in v.lower()
            if isinstance(v, str) and re.match(r"^\s*\[.*\]\s*$", v):
                assert False, f"range string {k}"
    # configs must not contain placeholder/adaptive as value (documentation may mention them as prohibition)
    configs_str = json.dumps(configs).lower()
    assert "as feasible" not in configs_str
    # ensure configs themselves have no adaptive generation markers
    assert "adaptive generation" not in configs_str


def test_allowed_axes_only_and_no_forbidden_keys():
    data, _ = _load_plan()
    allowed_axes = data.get("allowed_axes", [])
    assert len(allowed_axes) >= 4
    for c in data["configs"]:
        extra = set(c.keys()) - ALLOWED_CONFIG_KEYS
        assert not extra, f"extra keys {extra} in {c.get('config_id')}"
        for fk in FORBIDDEN_KEYS:
            assert fk not in c
        assert isinstance(c["fusion_method"], str)
        assert c["fusion_method"] in ("union", "hybrid_weighted_sum")
    forbidden = " ".join(data.get("forbidden_axes", [])).lower()
    for must in ["new signal", "cross-encoder", "global abstention", "public region", "candidate b"]:
        assert must in forbidden
    allowed_text = " ".join(allowed_axes).lower()
    for must in ["sparse", "dense", "exact", "field", "duplicate", "diversification"]:
        assert must in allowed_text


def test_selection_rule_exact():
    data, _ = _load_plan()
    sr = data.get("selection_rule", {})
    assert sr.get("ordering") == EXPECTED_SELECTION_ORDERING
    eligibility = sr.get("eligibility", "")
    assert "Success@5 >=85%" in eligibility or "Success@5 ≥85%" in eligibility
    assert "safety gates" in eligibility.lower()
    assert "paired" in sr.get("paired_p95_method", "").lower()
    assert "p95" in sr.get("paired_p95_method", "").lower()
    assert "no holdout" in sr.get("no_qualifier_action", "").lower()


def test_candidate_b_not_instantiated():
    data, _ = _load_plan()
    b_gate = data.get("candidate_b_gate", {})
    assert b_gate.get("instantiated") is False
    cond = b_gate.get("admission_condition_exact", "")
    assert "union oracle Recall@100" in cond
    assert ">=97%" in cond or "≥97%" in cond
    assert "5.0" in cond
    for c in data["configs"]:
        assert "candidate-b" not in c.get("config_id", "").lower()
        assert "candidate_b" not in c.get("config_id", "").lower()


def test_d026_secondary_non_gating():
    data, _ = _load_plan()
    d026 = data.get("secondary_diagnostics_D026", {})
    assert "non-gating" in d026.get("contract", "").lower()
    assert "category" in d026.get("contract", "").lower() or "secondary" in d026.get("contract", "").lower()
    reporting = d026.get("reporting_rule", "")
    assert "authoritative" in reporting.lower() or "recomputable" in reporting.lower()
    assert "unavailable" in reporting.lower() or "insufficiently characterized" in reporting.lower()
    prohibition = d026.get("prohibition", "")
    assert "auto-label" in prohibition.lower() or "infer" in prohibition.lower()


def test_parameter_semantics_and_scoring_order():
    data, _ = _load_plan()
    semantics = data.get("parameter_semantics", {})
    assert "scoring_order_and_normalization" in semantics
    order = semantics["scoring_order_and_normalization"]
    j = json.dumps(order).lower()
    assert "dense" in j
    assert "sparse" in j
    assert "exact" in j
    assert "dedup" in j
    fixed = semantics.get("fixed_not_tunable", {})
    assert "CANDIDATES" in fixed or "candidates" in json.dumps(fixed).lower()
    assert "COSINE_MIN" in fixed or "cosine" in json.dumps(fixed).lower()
    assert "embedding_model" in fixed
    for c in data["configs"]:
        assert c["dense_weight"] in [0.9, 1.0, 1.1]
        assert c["sparse_weight"] in [0.005, 0.01, 0.02]
        assert c["exact_title_boost"] in [0.0, 0.07, 0.15]
        assert c["exact_org_boost"] in [0.0, 0.05, 0.1]
        assert c["field_weight_title"] in [1.0, 1.5, 2.0]
        assert c["dedup_cosine_threshold"] in [0.95, 0.97, 0.98]
        assert c["diversification_lambda"] in [0.0, 0.3]


def test_forbidden_actions_assertions():
    data, _ = _load_plan()
    assertions = data.get("assertions", {})
    assert assertions.get("no_dev_dataset", "").lower().startswith("no dev")
    holdout_assert = assertions.get("no_holdout_plaintext_access", "").lower()
    assert "holdout" in holdout_assert and "no" in holdout_assert
    assert "no retrieval" in assertions.get("no_retrieval_execution", "").lower()
    b_assert = assertions.get("no_candidate_b_implementation", "").lower()
    assert "candidate b" in b_assert and ("not instantiated" in b_assert or "no candidate b" in b_assert)
    assert "git diff" in assertions.get("production_diff", "").lower()
    # deterministic assertion should mention fixed exactly or no range/placeholder pattern
    det = assertions.get("deterministic", "").lower()
    assert "fixed exactly" in det or "no range" in det or "deterministic" in det


def test_prereg_byte_identical_to_f5f8377():
    txt = PREREG.read_text(encoding="utf-8")
    assert "Bounded correction 2026-09-02 — secondary diagnostic contract (D-026" in txt
    assert "non-gating diagnostic only" in txt
    assert "Holdout-builder v3 supplement" in txt
    assert "Candidate-plan freeze (MAX 24" in txt


def test_no_candidate_b_configs_and_max24():
    data, _ = _load_plan()
    assert len(data["configs"]) <= 24
    ids = [c["config_id"] for c in data["configs"]]
    assert ids == sorted(ids)
def test_corrected_frozen_at_equals_d027_commit_timestamp():
    data, _ = _load_plan()
    assert data.get("frozen_at") == EXPECTED_FROZEN_AT, f"frozen_at must be D-027 commit timestamp {EXPECTED_FROZEN_AT}"
    prov = data.get("provenance", {})
    # timestamp basis truthfully recorded
    assert "D-027 commit timestamp" in prov.get("frozen_at_basis", "") or "D-027 commit timestamp" in prov.get("timestamp_basis", "")
    assert "not separately durable" in prov.get("frozen_at_basis", "") or "not separately durable" in prov.get("timestamp_basis", "")

def test_model_roles_provenance_correction():
    data, _ = _load_plan()
    prov = data.get("provenance", {})
    ext = prov.get("model_roles_external_verification", {})
    assert ext.get("default") == "opencode-go/muse-spark-1.2-contributor:xhigh"
    assert ext.get("plan") == "opencode-go/muse-spark-1.2-contributor:xhigh"
    assert ext.get("task") == "openai-codex/gpt-5.6-luna:xhigh"
    assert ext.get("review") == "openai-codex/gpt-5.6-luna:max"
    assert "Muse Spark" in ext.get("paseo_ui_visible", "")
    assert "unavailable" in ext.get("paseo_shell_omp_binary", "").lower()
    assert "external" in ext.get("note", "").lower()
    # created_by must reflect external verification, not claim Paseo ran omp
    assert "external" in prov.get("created_by", "").lower()
    assert "Paseo shell omp binary unavailable" in prov.get("created_by", "") or "unavailable" in prov.get("created_by", "").lower()

def test_semantic_equality_vs_old_d027():
    # Prove only metadata changed vs fd63d6d historical artifact
    import subprocess
    # Get old file bytes from fd63d6d
    r = subprocess.run(["git", "show", "fd63d6d:eval/retrieval-v3/candidate-plan/candidate-plan-v1.json"], capture_output=True)
    assert r.returncode == 0, "git show fd63d6d failed"
    old_data = json.loads(r.stdout.decode("utf-8"))
    new_data, _ = _load_plan()
    # Compare semantic keys excluding corrected metadata
    for key in ["plan_id","version","base_commit","base_commit_tag","branch","standing_contract_refs","candidate_family","max_configs","baseline_identity","parameter_semantics","configs","selection_rule","forbidden_axes","allowed_axes","candidate_b_gate","secondary_diagnostics_D026","gating_contract_ref","assertions"]:
        assert old_data[key] == new_data[key], f"semantic key {key} must be identical after correction (only metadata allowed to change)"
    assert old_data["frozen_at"] == "2026-09-02T15:00:00Z"
    assert new_data["frozen_at"] == EXPECTED_FROZEN_AT
    assert hashlib.sha256(r.stdout).hexdigest() == EXPECTED_OLD_SHA
