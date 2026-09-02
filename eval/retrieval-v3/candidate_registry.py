"""Candidate A registry — frozen 18 configs, MAX24, fail-closed."""
from __future__ import annotations
import hashlib
import json
import pathlib
import re

PLAN_PATH = pathlib.Path("eval/retrieval-v3/candidate-plan/candidate-plan-v1.json")
PLAN_PATH_ALT = pathlib.Path("eval/retrieval_v3/candidate-plan/candidate-plan-v1.json")
EXPECTED_SHA = "2815361a469fee9bf69f6ffdf2124d19928220535cdb08b2005ae6674ae7d17c"
EXPECTED_PREREG_SHA = "7842018613d66aa4570f4db2f8ae5a698ceb46757995a6b7e26873177b36160e"
MAX_CONFIGS = 24
EXPECTED_COUNT = 18

# Frozen 18 configs — byte-identical to candidate-plan-v1.json
EXPECTED_CONFIGS = [
    {"config_id": "candidate-a-01", "dedup_cosine_threshold": 0.98, "dense_weight": 1.0, "diversification_lambda": 0.0, "exact_org_boost": 0.0, "exact_title_boost": 0.0, "field_weight_eligibility": 1.0, "field_weight_support_content": 1.0, "field_weight_title": 1.0, "fusion_method": "hybrid_weighted_sum", "sparse_weight": 0.01},
    {"config_id": "candidate-a-02", "dedup_cosine_threshold": 0.98, "dense_weight": 1.0, "diversification_lambda": 0.0, "exact_org_boost": 0.05, "exact_title_boost": 0.07, "field_weight_eligibility": 1.0, "field_weight_support_content": 1.0, "field_weight_title": 1.0, "fusion_method": "hybrid_weighted_sum", "sparse_weight": 0.01},
    {"config_id": "candidate-a-03", "dedup_cosine_threshold": 0.97, "dense_weight": 1.0, "diversification_lambda": 0.0, "exact_org_boost": 0.0, "exact_title_boost": 0.15, "field_weight_eligibility": 1.0, "field_weight_support_content": 1.0, "field_weight_title": 1.5, "fusion_method": "hybrid_weighted_sum", "sparse_weight": 0.01},
    {"config_id": "candidate-a-04", "dedup_cosine_threshold": 0.95, "dense_weight": 1.0, "diversification_lambda": 0.3, "exact_org_boost": 0.05, "exact_title_boost": 0.07, "field_weight_eligibility": 1.0, "field_weight_support_content": 1.2, "field_weight_title": 1.5, "fusion_method": "union", "sparse_weight": 0.01},
    {"config_id": "candidate-a-05", "dedup_cosine_threshold": 0.98, "dense_weight": 1.0, "diversification_lambda": 0.0, "exact_org_boost": 0.0, "exact_title_boost": 0.0, "field_weight_eligibility": 1.0, "field_weight_support_content": 1.0, "field_weight_title": 1.0, "fusion_method": "hybrid_weighted_sum", "sparse_weight": 0.02},
    {"config_id": "candidate-a-06", "dedup_cosine_threshold": 0.98, "dense_weight": 0.9, "diversification_lambda": 0.0, "exact_org_boost": 0.1, "exact_title_boost": 0.15, "field_weight_eligibility": 1.0, "field_weight_support_content": 1.0, "field_weight_title": 1.5, "fusion_method": "hybrid_weighted_sum", "sparse_weight": 0.02},
    {"config_id": "candidate-a-07", "dedup_cosine_threshold": 0.98, "dense_weight": 1.1, "diversification_lambda": 0.0, "exact_org_boost": 0.0, "exact_title_boost": 0.07, "field_weight_eligibility": 1.0, "field_weight_support_content": 1.0, "field_weight_title": 2.0, "fusion_method": "hybrid_weighted_sum", "sparse_weight": 0.005},
    {"config_id": "candidate-a-08", "dedup_cosine_threshold": 0.97, "dense_weight": 1.0, "diversification_lambda": 0.3, "exact_org_boost": 0.05, "exact_title_boost": 0.0, "field_weight_eligibility": 1.2, "field_weight_support_content": 1.2, "field_weight_title": 1.0, "fusion_method": "union", "sparse_weight": 0.01},
    {"config_id": "candidate-a-09", "dedup_cosine_threshold": 0.98, "dense_weight": 1.0, "diversification_lambda": 0.0, "exact_org_boost": 0.0, "exact_title_boost": 0.07, "field_weight_eligibility": 1.2, "field_weight_support_content": 1.0, "field_weight_title": 1.5, "fusion_method": "hybrid_weighted_sum", "sparse_weight": 0.01},
    {"config_id": "candidate-a-10", "dedup_cosine_threshold": 0.95, "dense_weight": 1.0, "diversification_lambda": 0.0, "exact_org_boost": 0.1, "exact_title_boost": 0.0, "field_weight_eligibility": 1.0, "field_weight_support_content": 1.0, "field_weight_title": 1.0, "fusion_method": "union", "sparse_weight": 0.02},
    {"config_id": "candidate-a-11", "dedup_cosine_threshold": 0.98, "dense_weight": 0.9, "diversification_lambda": 0.3, "exact_org_boost": 0.0, "exact_title_boost": 0.15, "field_weight_eligibility": 1.2, "field_weight_support_content": 1.2, "field_weight_title": 2.0, "fusion_method": "hybrid_weighted_sum", "sparse_weight": 0.01},
    {"config_id": "candidate-a-12", "dedup_cosine_threshold": 0.97, "dense_weight": 1.1, "diversification_lambda": 0.0, "exact_org_boost": 0.05, "exact_title_boost": 0.07, "field_weight_eligibility": 1.0, "field_weight_support_content": 1.2, "field_weight_title": 1.0, "fusion_method": "hybrid_weighted_sum", "sparse_weight": 0.005},
    {"config_id": "candidate-a-13", "dedup_cosine_threshold": 0.98, "dense_weight": 1.0, "diversification_lambda": 0.0, "exact_org_boost": 0.05, "exact_title_boost": 0.15, "field_weight_eligibility": 1.0, "field_weight_support_content": 1.0, "field_weight_title": 1.0, "fusion_method": "hybrid_weighted_sum", "sparse_weight": 0.02},
    {"config_id": "candidate-a-14", "dedup_cosine_threshold": 0.95, "dense_weight": 1.0, "diversification_lambda": 0.3, "exact_org_boost": 0.0, "exact_title_boost": 0.0, "field_weight_eligibility": 1.0, "field_weight_support_content": 1.0, "field_weight_title": 2.0, "fusion_method": "union", "sparse_weight": 0.005},
    {"config_id": "candidate-a-15", "dedup_cosine_threshold": 0.97, "dense_weight": 1.0, "diversification_lambda": 0.0, "exact_org_boost": 0.1, "exact_title_boost": 0.07, "field_weight_eligibility": 1.2, "field_weight_support_content": 1.0, "field_weight_title": 1.5, "fusion_method": "hybrid_weighted_sum", "sparse_weight": 0.01},
    {"config_id": "candidate-a-16", "dedup_cosine_threshold": 0.98, "dense_weight": 0.9, "diversification_lambda": 0.0, "exact_org_boost": 0.05, "exact_title_boost": 0.0, "field_weight_eligibility": 1.0, "field_weight_support_content": 1.2, "field_weight_title": 1.0, "fusion_method": "hybrid_weighted_sum", "sparse_weight": 0.02},
    {"config_id": "candidate-a-17", "dedup_cosine_threshold": 0.98, "dense_weight": 1.1, "diversification_lambda": 0.3, "exact_org_boost": 0.0, "exact_title_boost": 0.15, "field_weight_eligibility": 1.0, "field_weight_support_content": 1.0, "field_weight_title": 1.0, "fusion_method": "union", "sparse_weight": 0.01},
    {"config_id": "candidate-a-18", "dedup_cosine_threshold": 0.98, "dense_weight": 1.0, "diversification_lambda": 0.0, "exact_org_boost": 0.0, "exact_title_boost": 0.0, "field_weight_eligibility": 1.2, "field_weight_support_content": 1.2, "field_weight_title": 1.5, "fusion_method": "hybrid_weighted_sum", "sparse_weight": 0.01},
]

ALLOWED_KEYS = {"config_id", "dedup_cosine_threshold", "dense_weight", "diversification_lambda", "exact_org_boost", "exact_title_boost", "field_weight_eligibility", "field_weight_support_content", "field_weight_title", "fusion_method", "sparse_weight"}

ALLOWED_VALUES = {
    "sparse_weight": {0.005, 0.01, 0.02},
    "dense_weight": {0.9, 1.0, 1.1},
    "exact_title_boost": {0.0, 0.07, 0.15},
    "exact_org_boost": {0.0, 0.05, 0.1},
    "field_weight_title": {1.0, 1.5, 2.0},
    "field_weight_support_content": {1.0, 1.2},
    "field_weight_eligibility": {1.0, 1.2},
    "dedup_cosine_threshold": {0.95, 0.97, 0.98},
    "diversification_lambda": {0.0, 0.3},
    "fusion_method": {"union", "hybrid_weighted_sum"},
}

EXPECTED_IDS = [f"candidate-a-{i:02d}" for i in range(1, 19)]

def _load_raw(path: pathlib.Path) -> tuple[dict, bytes]:
    raw = path.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    return data, raw

def load_and_validate(path: str | pathlib.Path | None = None) -> dict:
    """Load candidate plan and validate exactly 18 frozen configs. Fail-closed."""
    p = pathlib.Path(path) if path else PLAN_PATH
    if not p.exists():
        # try alt
        alt = PLAN_PATH_ALT
        if alt.exists():
            p = alt
        else:
            raise FileNotFoundError(f"candidate plan not found: {p}")
    data, raw = _load_raw(p)
    # SHA check
    sha = hashlib.sha256(raw).hexdigest()
    if sha != EXPECTED_SHA:
        raise ValueError(f"candidate plan SHA mismatch: got {sha} expected {EXPECTED_SHA} (config drift or file modified)")
    return validate_data(data, raw)

def validate_data(data: dict, raw: bytes | None = None) -> dict:
    # basic identity
    if data.get("plan_id") != "retrieval-v3-candidate-plan-v1":
        raise ValueError(f"plan_id mismatch: {data.get('plan_id')!r}")
    if data.get("version") != "1.0.0":
        raise ValueError("version mismatch")
    if data.get("max_configs") != MAX_CONFIGS:
        raise ValueError(f"max_configs must be {MAX_CONFIGS}, got {data.get('max_configs')}")
    if data.get("branch") != "codex/retrieval-v3-user-search-quality":
        raise ValueError("branch mismatch")
    configs = data.get("configs")
    if not isinstance(configs, list):
        raise ValueError("configs must be list")
    if len(configs) != EXPECTED_COUNT:
        raise ValueError(f"exact 18 configs required, got {len(configs)} (fail-closed duplicate/missing/extra)")
    if len(configs) > MAX_CONFIGS:
        raise ValueError(f"exceeds MAX24: {len(configs)}")
    ids = [c.get("config_id") for c in configs]
    if ids != sorted(ids):
        raise ValueError(f"configs not lexicographically sorted: {ids}")
    if ids != EXPECTED_IDS:
        raise ValueError(f"config IDs must be exactly {EXPECTED_IDS}, got {ids}")
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate config_id")
    # Check each config tuple exact match expected
    for idx, cfg in enumerate(configs):
        exp = EXPECTED_CONFIGS[idx]
        if set(cfg.keys()) != ALLOWED_KEYS:
            raise ValueError(f"{cfg.get('config_id')} keys mismatch: got {set(cfg.keys())} expected {ALLOWED_KEYS}")
        for k, allowed in ALLOWED_VALUES.items():
            v = cfg.get(k)
            if v not in allowed:
                raise ValueError(f"{cfg.get('config_id')}.{k}={v!r} not in allowed {allowed}")
        # exact tuple match
        if cfg != exp:
            raise ValueError(f"config drift for {cfg.get('config_id')}: got {cfg} expected {exp}")
    # Check duplicate tuples (already checked via cfg equality but also tuple uniqueness)
    tuples = [tuple(sorted(c.items())) for c in configs]
    if len(set(tuples)) != len(tuples):
        raise ValueError("duplicate config tuples")
    # Check candidate B not instantiated
    b_gate = data.get("candidate_b_gate", {})
    if b_gate.get("instantiated") is not False:
        raise ValueError("candidate_b_gate.instantiated must be false (Candidate B not instantiated)")
    # Check selection rule exact
    sel = data.get("selection_rule", {})
    ordering = sel.get("ordering", "")
    expected_ordering = "Success@5 desc -> NDCG@5 desc -> MRR@10 desc -> paired p95 asc -> lexicographic config_id asc"
    if ordering != expected_ordering:
        raise ValueError(f"selection ordering mismatch: {ordering!r}")
    # No adaptive generation check removed — plan assertions themselves contain the phrase; validation is via exact tuple equality instead.
    return data

def get_config_by_id(data: dict, config_id: str) -> dict:
    for c in data["configs"]:
        if c["config_id"] == config_id:
            return c
    raise KeyError(f"config_id {config_id} not found")

def list_configs(data: dict) -> list[dict]:
    return list(data["configs"])
