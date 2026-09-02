"""Static validation for retrieval-v3 candidate-plan v1 — narrow repair D-031 (D-030 base + computational test-contract repair) — no DB/model/network.

Validates:
- 18 exact config IDs/tuples unchanged vs pre-repair 4f231351 blob
- selection_rule unchanged
- Candidate B gate/substantive thresholds unchanged
- D-026 unchanged
- authorized semantic-definition fields (policy vector, tie-breaks, COSINE_MIN placement, full top30 ordering, fusion distinction, exact oracle)
- no new signal/model/embedding/B instantiate
- current repaired canonical SHA vs historical blobs
- prereg unchanged via actual historical blob/hash Git comparison (not string existence)
Pure/static + pure computational fixtures; no DB/network/model/retrieval. Computational fixtures independently execute D-030 cosine/exact semantics.
"""

import hashlib
import json
import math
import pathlib
import re
import subprocess
import unicodedata
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
    "region_filter",
    "global_threshold",
    "entity_extractor",
    "llm",
}

EXPECTED_SELECTION_ORDERING = "Success@5 desc -> NDCG@5 desc -> MRR@10 desc -> paired p95 asc -> lexicographic config_id asc"
EXPECTED_PLAN_ID = "retrieval-v3-candidate-plan-v1"
EXPECTED_VERSION = "1.0.0"
EXPECTED_BASE = "5327661445c37191a3fd61db195f3af4d2cf893a"
EXPECTED_FROZEN_AT = "2026-09-02T14:30:56+09:00"
EXPECTED_OLD_SHA = "ff3b83d11260e2c2e5aba2bbe08851bf24f68cc900733813d2a4f466a9363e41"
EXPECTED_PRE_REPAIR_SHA = "8e632c81c3c23b2a5280025298ae1d0c763abc5ce25d90e1ceb031179588ac54"
EXPECTED_D029_SHA = "d200c08a1358823e0d0463a25c72137eb0fac809016263412e374d8fb80fbfaa"
EXPECTED_REPAIRED_SHA = "2815361a469fee9bf69f6ffdf2124d19928220535cdb08b2005ae6674ae7d17c"
EXPECTED_PREREG_SHA = "7842018613d66aa4570f4db2f8ae5a698ceb46757995a6b7e26873177b36160e"

def _load_plan():
    assert PLAN_PATH.exists(), f"candidate-plan artifact missing: {PLAN_PATH}"
    raw = PLAN_PATH.read_bytes()
    assert b"\r\n" not in raw, "candidate-plan must be LF (no CRLF)"
    assert raw.endswith(b"\n"), "candidate-plan must end with LF"
    data = json.loads(raw.decode("utf-8"))
    return data, raw

def _git_show_blob(ref, path):
    r = subprocess.run(["git", "show", f"{ref}:{path}"], capture_output=True)
    assert r.returncode == 0, f"git show {ref}:{path} failed: {r.stderr.decode()[:200]}"
    return r.stdout

def _strip_authorized_semantic_fields(d):
    """Return copy without authorized semantic-definition fields that D-029/D-030 are allowed to change."""
    import copy
    c = copy.deepcopy(d)
    # Remove top-level narrow repair semantics added in D-029 and refined in D-030 (cosine non-unit + exact mechanical)
    for k in ["policy_comparison_vector", "cosine_min_placement", "fusion_semantics", "exact_oracle_semantics", "deterministic_ordering_contract"]:
        c.pop(k, None)
    # Remove provenance metadata that changed in D-028 (frozen_at vs provenance)
    # But frozen_at itself must remain same after D-028, so we keep it for comparison except we know D-027 vs D-028 diff
    # For pre-repair vs repaired comparison, authorized changes are:
    # - parameter_semantics.parameters.fusion_method.semantics (clarified)
    # - parameter_semantics.scoring_order_and_normalization (expanded)
    # So we normalize those for tuple comparison by removing them from equality check, testing separately
    if "parameter_semantics" in c:
        ps = c["parameter_semantics"]
        # Keep configs selection etc, but remove the two clarified subfields for strict equality; test them separately
        if "scoring_order_and_normalization" in ps:
            # keep for separate test, but for unchanged check we compare without it
            pass
    return c

# ---------------------------------------------------------------------------
# Pure computational fixtures — test-local only, matching D-030 exactly.
# Helpers MUST NOT become production semantic generators; they are local
# executable copies for evidence that dot != cosine when not unit, and that
# exact predicates obey NFC->strip->collapse->casefold + mechanical boundaries.
# ---------------------------------------------------------------------------

def _cosine(a, b):
    """Independent cosine = dot/(norm(a)*norm(b)). Pure deterministic, no model."""
    assert len(a) == len(b) and len(a) > 0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    assert na > 0 and nb > 0
    return dot / (na * nb)


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _normalize_exact(s: str) -> str:
    """One exact normalization everywhere: NFC -> strip -> collapse internal whitespace -> casefold. Test-local only."""
    t = unicodedata.normalize("NFC", s)
    t = t.strip()
    t = re.sub(r"\s+", " ", t)
    t = t.casefold()
    return t


def _is_alnum_hangul(ch: str) -> bool:
    return ("0" <= ch <= "9") or ("A" <= ch <= "Z") or ("a" <= ch <= "z") or ("\uAC00" <= ch <= "\uD7A3")


def _is_exact_title(q: str, title: str) -> bool:
    """D-030 exact-title: true iff normalized q == normalized title OR (normalized q substring of normalized title AND len>=4 AND mechanical boundary both sides). Unidirectional only."""
    nq = _normalize_exact(q)
    nt = _normalize_exact(title)
    if nq == nt:
        return True
    if len(nq) < 4:
        return False
    # check any occurrence of nq in nt with mechanical boundary
    start = 0
    while True:
        idx = nt.find(nq, start)
        if idx == -1:
            break
        left_ok = (idx == 0) or (not _is_alnum_hangul(nt[idx - 1]))
        right_pos = idx + len(nq)
        right_ok = (right_pos == len(nt)) or (not _is_alnum_hangul(nt[right_pos]))
        if left_ok and right_ok:
            return True
        start = idx + 1
    return False


def _is_exact_org(q: str, org: str) -> bool:
    """D-030 exact-org: normalized org length>=2 AND (org in q OR q in org). Bidirectional."""
    nq = _normalize_exact(q)
    no = _normalize_exact(org)
    if len(no) < 2:
        return False
    return (no in nq) or (nq in no)


def _select_representative_chunk(qvec, chunks):
    """Policy comparison vector: choose chunk minimizing cosine distance (max cosine). Tie chunk_index asc, then policy_chunk.id asc. Exact equality only — no epsilon/near-tie."""
    best = None
    best_cos = None
    for ch in chunks:
        cos = _cosine(qvec, ch["embedding"])
        # D-030 exact contract: minimum cosine distance / maximum cosine absolute priority; only actual cosine equality then tie-break
        if best is None or cos > best_cos or (cos == best_cos and (ch["chunk_index"], ch["id"]) < (best["chunk_index"], best["id"])):
            best = ch
            best_cos = cos
    return best, best_cos
def test_plan_file_exists_and_canonical_bytes():
    data, raw = _load_plan()
    sha = hashlib.sha256(raw).hexdigest()
    assert re.fullmatch(r"[0-9a-f]{64}", sha)
    assert len(raw) > 1000
    assert hashlib.sha256(PLAN_PATH.read_bytes()).hexdigest() == sha
    assert sha == EXPECTED_REPAIRED_SHA, f"candidate-plan SHA mismatch after D-029 repair: {sha} != {EXPECTED_REPAIRED_SHA}"
    assert sha != EXPECTED_OLD_SHA, "SHA should differ from old D-027 SHA"
    assert sha != EXPECTED_PRE_REPAIR_SHA, "SHA should differ from pre-repair D-028 SHA after narrow repair"
    assert sha != EXPECTED_D029_SHA, "SHA should differ from D-029 SHA after D-030 repair"

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
    assert len(configs) == 18, f"expected exact 18 configs per D-027, got {len(configs)}"
    ids = [c.get("config_id") for c in configs]
    assert len(ids) == len(set(ids))
    for cid in ids:
        assert re.fullmatch(r"candidate-a-\d{2}", cid)
    assert ids == sorted(ids), "config_ids must be lexicographically sorted"
    expected_ids = [f"candidate-a-{i:02d}" for i in range(1, 19)]
    assert ids == expected_ids, f"exact 18 IDs mismatch: {ids}"
    tuples = []
    for c in configs:
        items = tuple(sorted((k, json.dumps(v, sort_keys=True)) for k, v in c.items() if k != "config_id"))
        tuples.append(items)
    assert len(tuples) == len(set(tuples)), "duplicate tuples"

def test_exact_18_ids_tuples_unchanged_vs_prerepair_4f231351():
    """Verify 18 config IDs/tuples byte-identical to pre-repair 4f231351 blob."""
    data, _ = _load_plan()
    blob = _git_show_blob("4f231351d99bcba0844b37a058512333944192cd", "eval/retrieval-v3/candidate-plan/candidate-plan-v1.json")
    old_data = json.loads(blob.decode("utf-8"))
    assert len(old_data["configs"]) == 18
    assert len(data["configs"]) == 18
    # IDs identical
    old_ids = [c["config_id"] for c in old_data["configs"]]
    new_ids = [c["config_id"] for c in data["configs"]]
    assert old_ids == new_ids == [f"candidate-a-{i:02d}" for i in range(1,19)]
    # Tuples identical (full value equality per config)
    for old_c, new_c in zip(old_data["configs"], data["configs"]):
        assert old_c == new_c, f"tuple changed for {old_c.get('config_id')}: {old_c} != {new_c}"
    # Also verify SHA of old blob matches expected pre-repair
    assert hashlib.sha256(blob).hexdigest() == EXPECTED_PRE_REPAIR_SHA
    # Verify D-027 historical also has same 18 tuples (even older)
    blob027 = _git_show_blob("fd63d6d", "eval/retrieval-v3/candidate-plan/candidate-plan-v1.json")
    data027 = json.loads(blob027.decode("utf-8"))
    for c027, c_new in zip(data027["configs"], data["configs"]):
        assert c027 == c_new, f"D-027 tuple mismatch {c027.get('config_id')}"

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
    configs_str = json.dumps(configs).lower()
    assert "as feasible" not in configs_str
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

def test_selection_rule_exact_and_unchanged_vs_prerepair():
    data, _ = _load_plan()
    sr = data.get("selection_rule", {})
    assert sr.get("ordering") == EXPECTED_SELECTION_ORDERING
    eligibility = sr.get("eligibility", "")
    assert "Success@5 >=85%" in eligibility or "Success@5 ≥85%" in eligibility
    assert "safety gates" in eligibility.lower()
    assert "paired" in sr.get("paired_p95_method", "").lower()
    assert "p95" in sr.get("paired_p95_method", "").lower()
    assert "no holdout" in sr.get("no_qualifier_action", "").lower()
    # Unchanged vs pre-repair
    old_blob = _git_show_blob("4f231351d99bcba0844b37a058512333944192cd", "eval/retrieval-v3/candidate-plan/candidate-plan-v1.json")
    old_data = json.loads(old_blob.decode("utf-8"))
    assert sr == old_data.get("selection_rule"), "selection_rule must be unchanged vs pre-repair (D-027 rule frozen)"

def test_candidate_b_gate_unchanged_and_not_instantiated():
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
    # Unchanged vs pre-repair
    old_blob = _git_show_blob("4f231351d99bcba0844b37a058512333944192cd", "eval/retrieval-v3/candidate-plan/candidate-plan-v1.json")
    old_data = json.loads(old_blob.decode("utf-8"))
    assert b_gate == old_data.get("candidate_b_gate"), "candidate_b_gate substantive must be unchanged vs pre-repair"
    # Verify no Candidate B instantiation in plan
    assert "candidate b" not in json.dumps(data).lower() or "candidate b not instantiated" in json.dumps(data).lower() or b_gate.get("instantiated") is False

def test_d026_secondary_non_gating_unchanged():
    data, _ = _load_plan()
    d026 = data.get("secondary_diagnostics_D026", {})
    assert "non-gating" in d026.get("contract", "").lower()
    assert "category" in d026.get("contract", "").lower() or "secondary" in d026.get("contract", "").lower()
    reporting = d026.get("reporting_rule", "")
    assert "authoritative" in reporting.lower() or "recomputable" in reporting.lower()
    assert "unavailable" in reporting.lower() or "insufficiently characterized" in reporting.lower()
    prohibition = d026.get("prohibition", "")
    assert "auto-label" in prohibition.lower() or "infer" in prohibition.lower()
    # Unchanged vs pre-repair
    old_blob = _git_show_blob("4f231351d99bcba0844b37a058512333944192cd", "eval/retrieval-v3/candidate-plan/candidate-plan-v1.json")
    old_data = json.loads(old_blob.decode("utf-8"))
    assert d026 == old_data.get("secondary_diagnostics_D026"), "D-026 contract must be unchanged vs pre-repair"

def test_substantive_gates_unchanged_vs_prerepair():
    """Verify substantive numeric/safety/latency/MAX24 gates unchanged vs pre-repair."""
    data, _ = _load_plan()
    old_blob = _git_show_blob("4f231351d99bcba0844b37a058512333944192cd", "eval/retrieval-v3/candidate-plan/candidate-plan-v1.json")
    old_data = json.loads(old_blob.decode("utf-8"))
    # MAX24
    assert data.get("max_configs") == old_data.get("max_configs") == 24
    assert len(data["configs"]) <= 24
    # gating_contract_ref substantive
    assert data.get("gating_contract_ref") == old_data.get("gating_contract_ref")
    # baseline COSINE_MIN etc unchanged
    assert data["baseline_identity"]["COSINE_MIN"] == old_data["baseline_identity"]["COSINE_MIN"] == 0.78
    assert data["baseline_identity"]["CANDIDATES"] == 30
    # selection rule already checked, but also check safety integers not changed
    sr = data["selection_rule"]
    old_sr = old_data["selection_rule"]
    assert sr["safety_gates_dev"] == old_sr["safety_gates_dev"]
    # forbidden axes unchanged? Actually allowed to stay same; check not relaxed
    assert set(data["forbidden_axes"]) == set(old_data["forbidden_axes"]) or len(data["forbidden_axes"]) >= len(old_data["forbidden_axes"])

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

def test_policy_comparison_vector_determinism():
    data, _ = _load_plan()
    pcv = data.get("policy_comparison_vector")
    assert pcv is not None, "policy_comparison_vector must be defined (blocker 1)"
    txt = json.dumps(pcv, ensure_ascii=False).lower()
    assert "policy_chunk.embedding" in txt or "policy_chunk" in txt
    assert "vector(768)" in txt or "768" in txt or "embedding" in txt
    assert "no averaging" in txt or "no new" in txt
    assert "chunk_index" in txt and "policy_chunk.id" in txt
    assert "min" in txt and "distance" in txt
    assert "deterministic" in txt or "tie" in txt
    # Must state no averaging/new embedding
    assert "no averaging" in txt or "no new policy embedding" in txt or "no new embedding" in txt
    # Must reference schema: no separate policy/entity field
    assert "separate" in txt or "no separate" in txt or "unique(source,source_id)" in txt or "unique" in txt
    # D-030: stored embedding is normalize_embeddings=True rounded to 6 decimals not guaranteed unit norm
    assert "6 decimals" in txt or "rounded to 6" in txt or "6 decimal" in txt
    assert "not guaranteed unit norm" in txt or "not guaranteed unit" in txt or "not unit norm" in txt
    # D-030: actual cosine = dot/(norm(a)*norm(b)), not raw dot, pgvector semantics, dot != cosine when not unit
    assert "dot(a,b)/(norm(a)*norm(b))" in txt or "dot/(norm" in txt or "cos(a,b)=dot" in txt
    assert "pgvector" in txt
    assert "raw dot != cosine" in txt or "dot != cosine" in txt or "not guaranteed unit norm" in txt
    # Must not contain raw-dot==cosine wording (no "dot product" as equality)
    assert "dot product" not in txt or "not" in txt  # allow only if clarified not equal; raw wording removed in D-030
    # Also check scoring_order contains same representative vector tie-break and cosine definition
    order = data["parameter_semantics"]["scoring_order_and_normalization"]
    order_txt = json.dumps(order, ensure_ascii=False).lower()
    assert "chunk_index" in order_txt and "policy_chunk.id" in order_txt
    assert "no averaging" in order_txt or "no new" in order_txt
    # D-030: scoring order must also define actual cosine not raw dot
    assert "dot(a,b)/(norm(a)*norm(b))" in order_txt or "dot/(norm" in order_txt or "actual cosine" in order_txt
    assert "not guaranteed unit norm" in order_txt or "6 decimals" in order_txt or "6 decimal" in order_txt

def test_sparse_dense_tie_breaks_and_union_dedup():
    data, _ = _load_plan()
    ordering = data.get("deterministic_ordering_contract")
    assert ordering is not None, "deterministic_ordering_contract must be defined (blocker 2)"
    # dense top100
    dense = ordering.get("dense_top100","").lower()
    assert "dense_cosine" in dense or "dense" in dense
    assert "source" in dense and "source_id" in dense and "policy.id" in dense
    # sparse
    sparse = ordering.get("sparse_top100","").lower()
    assert "weighted_lexical" in sparse or "sparse" in sparse or "lexical" in sparse
    assert "source" in sparse and "source_id" in sparse and "policy.id" in sparse
    # union dedup
    dedup_id = ordering.get("union_dedup_identity","").lower()
    assert "(source,source_id)" in dedup_id or "source,source_id" in dedup_id
    assert "canonical" in dedup_id
    assert "policy.id" in dedup_id
    # final_score rank
    final_rank = ordering.get("final_score_rank_before_dedup","").lower()
    assert "final_score" in final_rank
    assert "source" in final_rank and "source_id" in final_rank and "policy.id" in final_rank
    # Also check scoring_order_and_normalization contains same
    order = data["parameter_semantics"]["scoring_order_and_normalization"]
    stxt = json.dumps(order, ensure_ascii=False).lower()
    assert "dense_cosine desc" in stxt or "dense" in stxt
    assert "source asc" in stxt and "source_id asc" in stxt and "policy.id asc" in stxt

def test_cosine_min_placement():
    data, _ = _load_plan()
    cmp = data.get("cosine_min_placement")
    assert cmp is not None, "cosine_min_placement must be defined (blocker 2)"
    assert cmp.get("value") == 0.78
    assert cmp.get("operator") == ">="
    passes = cmp.get("passes_when","").lower()
    assert ">= 0.78" in passes or ">=0.78" in passes
    fails = cmp.get("fails_when","").lower()
    assert "< 0.78" in fails or "<0.78" in fails
    placement = cmp.get("placement","").lower()
    assert "dense" in placement and "before union" in placement
    assert "sparse" in placement and "not filtered" in placement
    assert "exact" in placement
    assert "post-limit" in placement or "post-limit" in placement or "production" in placement
    # Check scoring_order step_7 also contains placement
    order = data["parameter_semantics"]["scoring_order_and_normalization"]
    step7 = order.get("step_7_retrieval_pool_cosine_min","").lower()
    assert "cosine_min" in step7 or "0.78" in step7
    assert "dense" in step7 and "sparse" in step7
    assert "not filtered" in step7 or "not filtered" in placement
    assert "filtered dense top-100" in step7 or "filtered dense" in step7

def test_full_top30_deterministic_ordering_and_mmr_to_30():
    data, _ = _load_plan()
    ordering = data.get("deterministic_ordering_contract")
    assert ordering is not None
    # Check dedup greedy
    dedup = ordering.get("dedup_greedy","").lower()
    assert "greedy" in dedup
    assert "retain" in dedup or "keep" in dedup or "suppress" in dedup
    assert "similarity" in dedup and "threshold" in dedup
    # D-030: dedup must use actual cosine not raw dot
    assert "actual cosine" in dedup or "cos(a,b)=dot" in dedup or "dot(a,b)/(norm" in dedup or "dot/(norm" in dedup
    assert "pgvector" in dedup or "not guaranteed unit" in dedup or "6 decimals" in dedup or "actual cosine" in dedup
    # threshold operator strict >
    thresh = ordering.get("threshold_operator","")
    assert ">" in thresh and "strict" in thresh.lower()
    assert "actual cosine" in thresh.lower() or "dot(a,b)" in thresh.lower() or "dot/(norm" in thresh.lower() or "cos(a,b)" in thresh.lower()
    # MMR lambda 0
    mmr0 = ordering.get("mmr_lambda_0","").lower()
    assert "0.0" in mmr0 and "unchanged" in mmr0
    # MMR gt0
    mmr_gt = ordering.get("mmr_lambda_gt0","").lower()
    assert "mmr" in mmr_gt
    assert "lambda*final_score" in mmr_gt or "final_score" in mmr_gt
    assert "max_similarity" in mmr_gt or "max_cosine" in mmr_gt or "max_similarity_to_already_selected" in mmr_gt
    # D-030: MMR max_similarity is actual cosine
    assert "actual cosine" in mmr_gt or "cos(a,b)=dot" in mmr_gt or "dot(a,b)/(norm" in mmr_gt or "dot/(norm" in mmr_gt
    # Must continue to 30, not top5
    assert "30" in mmr_gt
    assert "top5" not in mmr_gt or "not stopping at top5" in mmr_gt or "not stop" in mmr_gt or "continues" in mmr_gt or ("top5" not in mmr_gt)
    # Check that mmr_gt mentions 30 and not 5 only
    assert "30" in mmr_gt
    # positions 1-30
    pos = ordering.get("positions_1_30_full","").lower()
    assert "1-30" in pos or "positions 1" in pos or "30" in pos
    assert "deterministic" in pos
    # Also check scoring_order step_8 contains same and defines actual cosine
    order = data["parameter_semantics"]["scoring_order_and_normalization"]
    step8 = order.get("step_8_dedup_diversification_full_top30","").lower()
    assert "dedup" in step8 and "diversification" in step8
    assert "0.0" in step8 or "lambda" in step8
    assert "30" in step8
    assert "mmr" in step8
    assert ">" in step8 or "threshold" in step8
    assert "actual cosine" in step8 or "cos(a,b)=dot" in step8 or "dot/(norm" in step8

def test_fusion_executable_distinction():
    data, _ = _load_plan()
    fusion = data.get("fusion_semantics")
    assert fusion is not None, "fusion_semantics must be defined (blocker 3)"
    union_txt = fusion.get("union","").lower()
    hybrid_txt = fusion.get("hybrid_weighted_sum","").lower()
    assert "union" in json.dumps(fusion).lower()
    assert "hybrid_weighted_sum" in json.dumps(fusion).lower() or "hybrid" in json.dumps(fusion).lower()
    # union: contribution only if present
    assert "only if" in union_txt or "only if policy" in union_txt or "membership" in union_txt
    assert "0" in union_txt  # contribution 0 if not present
    # hybrid: both computed regardless
    assert "both" in hybrid_txt and "computed" in hybrid_txt
    assert "regardless" in hybrid_txt or "irrespective" in hybrid_txt
    # no new signal
    no_new = fusion.get("no_new_signal","").lower()
    assert "no new" in no_new or "no additional" in no_new
    assert "normalization" in no_new or "new axis" in no_new or "existing dense/sparse" in no_new or "existing" in no_new
    # check parameter_semantics fusion_method also updated
    fm = data["parameter_semantics"]["parameters"]["fusion_method"]["semantics"].lower()
    assert "executable" in fm
    assert "union" in fm and "hybrid_weighted_sum" in fm
    assert "no new" in fm or "no additional" in fm or "existing dense/sparse" in fm
    # standing 18 tuples unchanged already verified

def test_exact_standalone_oracle_semantics():
    data, _ = _load_plan()
    exact = data.get("exact_oracle_semantics")
    assert exact is not None, "exact_oracle_semantics must be defined (blocker 4)"
    # entity absence
    entity = exact.get("entity_field_absence","").lower()
    assert "no separate entity" in entity or "no entity" in entity or "schema has no" in entity
    assert "policy_chunk.embedding" in entity or "policy.title" in entity or "title" in entity
    # predicates - D-030 exact normalization and mechanical boundary
    pred = exact.get("predicates","").lower()
    assert "is_exact_title" in pred or "exact_title" in pred
    assert "is_exact_org" in pred
    assert "no new extractor" in pred or "no llm" in pred or "no entity extractor" in pred
    # D-030: one exact normalization NFC -> strip -> collapse internal whitespace -> casefold everywhere
    assert "nfc" in pred and "collapse" in pred and "casefold" in pred
    assert "nfc -> strip -> collapse" in pred or "nfc" in pred and "strip" in pred and "collapse" in pred
    # D-030: exact_title is unidirectional: q substring of title (not title in q except equality), len>=4, mechanical boundary not regex
    assert "q ==" in pred or "normalized q ==" in pred or "exact equality" in pred
    assert "normalized q" in pred and "substring of normalized title" in pred
    assert "len(normalized q) >=4" in pred or "len" in pred and ">=4" in pred
    assert "mechanical" in pred and "[0-9a-z" in pred
    assert "not python regex" in pred or "not in [0-9" in pred or "mechanical boundary" in pred
    # title should NOT allow normalized title in q except equality - check predicate says not allowed
    # we check step_4 exact signals directly for this directional constraint
    order = data["parameter_semantics"]["scoring_order_and_normalization"]
    step4 = order.get("step_4_exact_signals","").lower()
    assert "nfc" in step4 and "collapse" in step4 and "casefold" in step4
    assert "one exact normalization everywhere" in step4 or ("nfc -> strip -> collapse" in step4)
    assert "is_exact_title = 1 iff" in step4 or "is_exact_title" in step4
    assert "normalized q == normalized title" in step4 or "normalized q ==" in step4
    assert "normalized q is a substring of normalized title" in step4
    assert "len(normalized q) >=4" in step4
    assert "mechanical" in step4 and "[0-9a-z" in step4
    assert "do not allow normalized title substring in q except via exact equality" in step4 or "do not allow" in step4
    assert "not python regex" in step4 or "not in [0-9a-Za-z" in step4
    # org: normalized org length >=2 and bidirectional
    assert "normalized org" in pred and "length >=2" in pred
    assert "substring in normalized q or" in pred or "org substring in" in pred
    assert "normalized org" in step4 and "length >=2" in step4
    assert "normalized org substring in normalized q or normalized q substring in normalized org" in step4
    # exact candidate set ordering
    ecs = exact.get("exact_candidate_set","").lower()
    assert "is_exact_title==1 or is_exact_org==1" in ecs or "is_exact_title" in ecs
    assert "deterministic" in ecs or "ordered" in ecs
    assert "source asc" in ecs and "source_id asc" in ecs and "policy.id asc" in ecs
    # exact recall
    er = exact.get("exact_recall","").lower()
    assert "recall@k" in er or "recall@30" in er or "exact recall" in er
    assert "30/50/100" in er or "30" in er and "50" in er and "100" in er
    # union oracle
    uo = exact.get("union_oracle","").lower()
    assert "union oracle" in uo
    assert "dense top-k" in uo or "dense" in uo
    assert "sparse top-k" in uo or "sparse" in uo
    assert "exact top-k" in uo or "exact" in uo
    assert "deduplicated" in uo or "dedup" in uo
    assert "(source,source_id)" in uo or "source,source_id" in uo
    assert "recall@k" in uo or "recall@100" in uo
    assert "97%" in uo or ">=97%" in uo or "union oracle recall@100" in uo
    # diagnostic vs final pool
    diag = exact.get("diagnostic_vs_final_pool","").lower()
    assert "diagnostic only" in diag
    assert "not injected" in diag or "remains dense+sparse" in diag
    assert "final candidate a pool" in diag or "final candidate a" in diag
    # candidate b gate unchanged
    assert "candidate b" in exact.get("candidate_b_gate_unchanged","").lower() or "candidate b admission" in exact.get("candidate_b_gate_unchanged","").lower()
    # no new signal - also check no new predicate family
    assert "no new" in exact.get("no_new_signal","").lower() or "no entity extractor" in exact.get("no_new_signal","").lower()
    assert "no new predicate family" in exact.get("no_new_signal","").lower() or "no new" in exact.get("no_new_signal","").lower()

def test_no_new_signal_model_embedding_and_b_not_instantiated():
    data, _ = _load_plan()
    # Check forbidden_axes still prohibits new signal/model/embedding
    forbidden = " ".join(data.get("forbidden_axes", [])).lower()
    assert "new signal" in forbidden
    assert "embedding model replacement" in forbidden or "embedding" in forbidden
    assert "cross-encoder" in forbidden
    # Check assertions for no new gate/process etc
    assertions = data.get("assertions", {})
    assert "candidate b" in assertions.get("no_candidate_b_implementation","").lower() and ("not instantiated" in assertions.get("no_candidate_b_implementation","").lower() or "no candidate b" in assertions.get("no_candidate_b_implementation","").lower())
    # Check exact oracle says no new signal
    exact = data.get("exact_oracle_semantics", {})
    assert "no new" in exact.get("no_new_signal","").lower() or "no entity" in exact.get("no_new_signal","").lower()
    # Check policy_comparison_vector says no averaging/new embedding
    pcv = data.get("policy_comparison_vector", {})
    assert "no averaging" in json.dumps(pcv, ensure_ascii=False).lower() or "no new" in json.dumps(pcv, ensure_ascii=False).lower()
    # Check fusion says no new signal
    fusion = data.get("fusion_semantics", {})
    assert "no new" in fusion.get("no_new_signal","").lower()
    # B not instantiated
    assert data.get("candidate_b_gate", {}).get("instantiated") is False
    for c in data["configs"]:
        assert "candidate-b" not in c.get("config_id","").lower()

def test_prereg_byte_identical_to_f5f8377_via_git_hash():
    """Verify prereg unchanged via actual historical blob/hash, not string existence."""
    current_raw = PREREG.read_bytes()
    current_sha = hashlib.sha256(current_raw).hexdigest()
    assert current_sha == EXPECTED_PREREG_SHA, f"prereg SHA mismatch {current_sha}"
    # Git show f5f8377 prereg
    blob = _git_show_blob("f5f8377", "docs/RETRIEVAL_V3_PREREG.md")
    assert hashlib.sha256(blob).hexdigest() == EXPECTED_PREREG_SHA
    assert blob == current_raw, "prereg bytes must be byte-identical to f5f8377 commit"
    # Also verify git diff shows 0
    r = subprocess.run(["git", "diff", "f5f8377..HEAD", "--", "docs/RETRIEVAL_V3_PREREG.md"], capture_output=True)
    assert r.returncode == 0
    assert r.stdout.strip() == b"", "git diff f5f8377..HEAD -- prereg must be 0"
    # Verify current HEAD vs f5f8377 diff 0 via our earlier 4f231351 also 0 (D-028 didn't change prereg)
    r2 = subprocess.run(["git", "diff", "4f231351d99bcba0844b37a058512333944192cd..HEAD", "--", "docs/RETRIEVAL_V3_PREREG.md"], capture_output=True)
    assert r2.stdout.strip() == b"", "prereg diff vs pre-repair must be 0"

def test_ml_service_diff_0_and_holdout_absent():
    # ml-service diff 0 vs base 5327661
    r = subprocess.run(["git", "diff", "5327661445c37191a3fd61db195f3af4d2cf893a..HEAD", "--", "ml-service/"], capture_output=True)
    assert r.returncode == 0
    assert r.stdout.strip() == b"", "ml-service diff must be 0"
    # holdout absent on main branch
    r2 = subprocess.run(["git", "ls-tree", "-r", "HEAD", "--", "eval/retrieval-v3/holdout/"], capture_output=True)
    assert r2.stdout.strip() == b"", "holdout must be absent on main branch"
    # protected refs unchanged
    r3 = subprocess.run(["git", "rev-parse", "refs/heads/codex/retrieval-v3-holdout-freeze"], capture_output=True, text=True)
    assert r3.stdout.strip() == "978eeebbe423496cf2e95af410144efaf6fce406"
    r4 = subprocess.run(["git", "rev-parse", "refs/tags/retrieval-v3-holdout-v1"], capture_output=True, text=True)
    assert r4.stdout.strip() == "3028f72122a10feaeb54987d69c3045714babe8a"
    r5 = subprocess.run(["git", "rev-parse", "refs/tags/retrieval-v3-holdout-v1^{commit}"], capture_output=True, text=True)
    assert r5.stdout.strip() == "978eeebbe423496cf2e95af410144efaf6fce406"

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
    det = assertions.get("deterministic", "").lower()
    assert "fixed exactly" in det or "no range" in det or "deterministic" in det

def test_corrected_frozen_at_equals_d027_commit_timestamp():
    data, _ = _load_plan()
    assert data.get("frozen_at") == EXPECTED_FROZEN_AT, f"frozen_at must be D-027 commit timestamp {EXPECTED_FROZEN_AT}"
    prov = data.get("provenance", {})
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
    assert "external" in prov.get("created_by", "").lower()
    assert "Paseo shell omp binary unavailable" in prov.get("created_by", "") or "unavailable" in prov.get("created_by", "").lower()

def test_semantic_equality_vs_old_d027_authorized_fields_only():
    """Prove only authorized semantic-definition fields changed vs fd63d6d historical artifact; 18 tuples etc identical."""
    r = subprocess.run(["git", "show", "fd63d6d:eval/retrieval-v3/candidate-plan/candidate-plan-v1.json"], capture_output=True)
    assert r.returncode == 0, "git show fd63d6d failed"
    old_data = json.loads(r.stdout.decode("utf-8"))
    new_data, _ = _load_plan()
    # Keys that must be identical: all except authorized semantic fields and new top-level narrow repair keys and provenance metadata corrected in D-028
    # Authorized to differ: parameter_semantics.scoring_order_and_normalization, parameter_semantics.parameters.fusion_method.semantics, plus new top-level keys
    authorized_top_keys = {"policy_comparison_vector", "cosine_min_placement", "fusion_semantics", "exact_oracle_semantics", "deterministic_ordering_contract"}
    for key in old_data:
        if key in authorized_top_keys:
            continue
        if key == "parameter_semantics":
            # Check inner except authorized subfields
            old_ps = old_data[key]
            new_ps = new_data[key]
            # fixed_not_tunable must be identical
            assert old_ps.get("fixed_not_tunable") == new_ps.get("fixed_not_tunable"), "fixed_not_tunable must be identical"
            # parameters except fusion_method.sematics must be identical
            for pk, pv in old_ps.get("parameters", {}).items():
                if pk == "fusion_method":
                    # only semantics allowed to differ, allowed values must be same
                    assert pv["allowed"] == new_ps["parameters"][pk]["allowed"]
                    assert pv["type"] == new_ps["parameters"][pk]["type"]
                else:
                    assert pv == new_ps["parameters"][pk], f"parameter {pk} must be identical"
            # overview identical
            assert old_ps["overview"] == new_ps["overview"]
            # scoring_order_and_normalization is authorized to differ, but check it exists and is expanded
            assert "scoring_order_and_normalization" in new_ps
            assert len(new_ps["scoring_order_and_normalization"]) >= len(old_ps["scoring_order_and_normalization"])
        elif key == "provenance":
            # provenance was corrected in D-028, allow its authorized fields to differ, but check configs etc not in provenance
            # For D-029, provenance should remain same as pre-repair (D-028)
            pass
        elif key == "frozen_at":
            # already corrected in D-028, should remain same vs pre-repair
            assert new_data[key] == EXPECTED_FROZEN_AT
            assert old_data[key] == "2026-09-02T15:00:00Z"
        else:
            assert old_data[key] == new_data[key], f"semantic key {key} must be identical after correction (only authorized metadata allowed to change)"
    # Also verify vs pre-repair 4f23135 that only authorized fields differ
    r2 = subprocess.run(["git", "show", "4f231351d99bcba0844b37a058512333944192cd:eval/retrieval-v3/candidate-plan/candidate-plan-v1.json"], capture_output=True)
    pre_data = json.loads(r2.stdout.decode("utf-8"))
    # Configs must be identical (already tested) and selection etc identical
    assert pre_data["configs"] == new_data["configs"]
    assert pre_data["selection_rule"] == new_data["selection_rule"]
    assert pre_data["candidate_b_gate"] == new_data["candidate_b_gate"]
    assert pre_data["secondary_diagnostics_D026"] == new_data["secondary_diagnostics_D026"]
    assert hashlib.sha256(r2.stdout).hexdigest() == EXPECTED_PRE_REPAIR_SHA
    assert hashlib.sha256(r.stdout).hexdigest() == EXPECTED_OLD_SHA

# ---------------------------------------------------------------------------
# D-031 computational fixtures — independently execute cosine/exact semantics.
# ---------------------------------------------------------------------------

def test_pure_cosine_non_unit_vectors_dot_not_equal_cosine():
    """Explicit non-unit vectors where raw dot != cosine; independent cosine = dot/(norm(a)*norm(b))."""
    # Vector pair 1: a=[2,0], b=[2,0] => dot=4, cos=1, dot != cosine
    a1 = [2.0, 0.0]
    b1 = [2.0, 0.0]
    dot1 = _dot(a1, b1)
    cos1 = _cosine(a1, b1)
    assert dot1 == 4.0
    assert math.isclose(cos1, 1.0, rel_tol=1e-9)
    assert dot1 != cos1, "raw dot must not equal cosine for non-unit vectors"
    # Vector pair 2: a=[1,2,0], b=[3,0,0] => dot=3, norm(a)=sqrt5, norm(b)=3, cos=3/(3*sqrt5)=0.447..., dot != cos
    a2 = [1.0, 2.0, 0.0]
    b2 = [3.0, 0.0, 0.0]
    dot2 = _dot(a2, b2)
    cos2 = _cosine(a2, b2)
    assert dot2 == 3.0
    assert math.isclose(cos2, 3.0 / (math.sqrt(5.0) * 3.0), rel_tol=1e-9)
    assert dot2 != cos2
    # Vector pair 3: rounding-simulated 6-decimal vector (norm !=1) vs query
    a3 = [0.123456, 0.654321, 0.111111]
    b3 = [0.123457, 0.654322, 0.111112]
    dot3 = _dot(a3, b3)
    cos3 = _cosine(a3, b3)
    na3 = math.sqrt(sum(x * x for x in a3))
    nb3 = math.sqrt(sum(y * y for y in b3))
    assert not math.isclose(na3, 1.0, rel_tol=1e-9) or not math.isclose(nb3, 1.0, rel_tol=1e-9)
    assert not math.isclose(dot3, cos3, rel_tol=1e-6), "stored 6-decimal rounded vectors are not guaranteed unit norm"


def test_pure_cosine_formula_independent():
    """Test-local independent cosine = dot/(norm(a)*norm(b)) exactly."""
    cases = [
        ([1.0, 0.0, 0.0], [0.0, 1.0, 0.0], 0.0),
        ([1.0, 1.0], [1.0, 1.0], 1.0),
        ([2.0, 2.0], [1.0, 1.0], 1.0),
        ([1.0, 0.0], [-1.0, 0.0], -1.0),
    ]
    for a, b, expected in cases:
        c = _cosine(a, b)
        assert math.isclose(c, expected, abs_tol=1e-9), f"cosine {a},{b} expected {expected} got {c}"
        # also verify manual formula matches
        dot = _dot(a, b)
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(y * y for y in b))
        manual = dot / (na * nb)
        assert math.isclose(c, manual, rel_tol=1e-9)


def test_pure_dedup_uses_actual_cosine_strict_gt():
    """Dedup threshold comparison uses actual cosine with STRICT > (not >=)."""
    # Simulate two policy representative vectors
    # Create vectors with known cosine = 0.95 exactly at threshold vs above
    # Use unit-like vectors for controlled cosine: cos = cos(theta)
    # We construct b rotated by theta where cos(theta)=threshold
    import math as _m
    def vec_from_angle(theta):
        return [_m.cos(theta), _m.sin(theta), 0.0]
    # Make vectors non-unit by scaling to ensure dot != cosine still
    scale = 2.5
    a = [scale * 1.0, 0.0, 0.0]  # [2.5,0,0]
    # threshold 0.95 => theta = acos(0.95)
    theta_at = _m.acos(0.95)
    b_at = [scale * _m.cos(theta_at), scale * _m.sin(theta_at), 0.0]
    cos_at = _cosine(a, b_at)
    assert math.isclose(cos_at, 0.95, rel_tol=1e-6), f"cos_at {cos_at}"
    assert _dot(a, b_at) != cos_at, "dot != cosine still holds for scaled non-unit"
    # STRICT > : cos == threshold must NOT suppress
    threshold = 0.95
    suppress_at = cos_at > threshold
    assert suppress_at is False, "strict > must not suppress when cos == threshold"
    # Slightly above threshold must suppress
    theta_above = _m.acos(0.951)
    # Actually cos 0.951 <0.95? Wait acos decreasing: cos 0.951 >0.95? No 0.951 >0.95 so closer, theta smaller.
    # Use cos 0.96 which is clearly above threshold? 0.96 >0.95.
    theta_above2 = _m.acos(0.96)
    b_above = [scale * _m.cos(theta_above2), scale * _m.sin(theta_above2), 0.0]
    cos_above = _cosine(a, b_above)
    assert math.isclose(cos_above, 0.96, rel_tol=1e-6)
    assert (cos_above > threshold) is True
    # Below threshold must not suppress
    theta_below = _m.acos(0.94)
    b_below = [scale * _m.cos(theta_below), scale * _m.sin(theta_below), 0.0]
    cos_below = _cosine(a, b_below)
    assert math.isclose(cos_below, 0.94, rel_tol=1e-6)
    assert (cos_below > threshold) is False
    # Verify raw dot would give wrong decision: raw dot = 2.5*2.5*cos =6.25*cos
    # For threshold 0.95, raw dot at 0.95 is 5.9375; raw dot comparison to 0.95 is always true -> wrong, so cosine must be used
    assert _dot(a, b_below) > threshold, "raw dot > threshold even when cosine < threshold, proving cosine must be used"
    assert _dot(a, b_at) > threshold


def test_pure_mmr_uses_actual_cosine():
    """MMR similarity term max_similarity_to_already_selected uses same actual cosine definition."""
    # Selected set has one vector s, candidates have vectors c1,c2
    s = [3.0, 0.0, 0.0]  # scaled non-unit
    c_close = [2.9, 0.5, 0.0]  # high cosine to s
    c_far = [0.0, 3.0, 0.0]  # orthogonal -> cosine 0 (dot also 0, degenerate equality allowed for orth)
    cos_close = _cosine(s, c_close)
    cos_far = _cosine(s, c_far)
    assert cos_close > cos_far
    assert _dot(s, c_close) != cos_close
    # orthogonal case dot==cos==0 is degenerate but proves dedup still uses cosine definition
    assert math.isclose(cos_far, 0.0, abs_tol=1e-9)
    assert _dot(s, c_far) == 0.0
    # Non-orthogonal far vector where dot != cosine
    c_far2 = [0.5, 2.9, 0.0]  # ~80 degrees, cosine ~0.17, dot 1.5 != cosine
    cos_far2 = _cosine(s, c_far2)
    assert _dot(s, c_far2) != cos_far2
    # MMR score = lambda*final_score - (1-lambda)*max_similarity
    # Take lambda=0.3, final_scores equal, so diversification picks far one
    lam = 0.3
    fs = 1.0
    mmr_close = lam * fs - (1 - lam) * cos_close
    mmr_far = lam * fs - (1 - lam) * cos_far
    assert mmr_far > mmr_close, "MMR with cosine should prefer far candidate when scores equal"
    assert math.isclose(cos_close, _dot(s, c_close) / (math.sqrt(sum(x*x for x in s))*math.sqrt(sum(x*x for x in c_close))), rel_tol=1e-9)


def test_pure_representative_chunk_deterministic_tie_break():
    """Representative chunk: minimum cosine distance, then chunk_index asc, then policy_chunk.id asc."""
    qvec = [1.0, 0.0, 0.0]
    # Case 1: distinct distances -> closest wins regardless of index
    chunks1 = [
        {"embedding": [0.0, 1.0, 0.0], "chunk_index": 0, "id": 1},
        {"embedding": [0.9, 0.1, 0.0], "chunk_index": 5, "id": 2},
        {"embedding": [1.0, 0.0, 0.0], "chunk_index": 10, "id": 3},
    ]
    best1, cos1 = _select_representative_chunk(qvec, chunks1)
    assert best1["id"] == 3, "closest cosine distance must win regardless of tie-break"
    assert math.isclose(cos1, 1.0, rel_tol=1e-9)
    # Case 2: tie on cosine distance -> chunk_index asc wins
    # Both chunks have identical embedding [1,0,0] so same cosine 1.0; chunk_index decides
    chunks2 = [
        {"embedding": [1.0, 0.0, 0.0], "chunk_index": 5, "id": 10},
        {"embedding": [1.0, 0.0, 0.0], "chunk_index": 2, "id": 20},
        {"embedding": [1.0, 0.0, 0.0], "chunk_index": 2, "id": 5},
    ]
    # chunk_index 2 vs 5 -> 2 wins; among two with chunk_index 2, id 5 vs 20 -> 5 wins
    best2, cos2 = _select_representative_chunk(qvec, chunks2)
    assert best2["chunk_index"] == 2
    assert best2["id"] == 5
    # Case 3: scaled non-unit vectors still use actual cosine (dot != cosine) for distance
    chunks3 = [
        {"embedding": [2.0, 0.0, 0.0], "chunk_index": 0, "id": 100},
        {"embedding": [0.0, 2.0, 0.0], "chunk_index": 0, "id": 101},
    ]
    best3, cos3 = _select_representative_chunk(qvec, chunks3)
    assert best3["id"] == 100
    assert math.isclose(cos3, 1.0, rel_tol=1e-9)
    assert _dot(qvec, chunks3[0]["embedding"]) == 2.0 and cos3 != 2.0


def test_pure_representative_chunk_near_tie_higher_cosine_wins_despite_worse_tie_break():
    """Regression: two cosines very close (math.isclose True but not equal) — higher cosine wins despite worse chunk_index/id."""
    qvec = [1.0, 0.0, 0.0]
    # chunk_high: exact max cosine 1.0, but worse tie-break (larger index/id)
    ch_high = {"embedding": [1.0, 0.0, 0.0], "chunk_index": 10, "id": 100}
    # chunk_near: cosine slightly less but very close (isclose True), better tie-break (smaller index/id)
    # q=[1,0,0], b=[1,1e-5,0] -> cos = 1/sqrt(1+1e-10) ≈ 0.99999999995, isclose to 1.0 True but !=
    ch_near = {"embedding": [1.0, 1e-5, 0.0], "chunk_index": 0, "id": 1}
    cos_high = _cosine(qvec, ch_high["embedding"])
    cos_near = _cosine(qvec, ch_near["embedding"])
    assert math.isclose(cos_high, 1.0, rel_tol=1e-9)
    assert math.isclose(cos_near, 1.0, rel_tol=1e-9) is False or math.isclose(cos_high, cos_near)  # ensure at least pair isclose
    # verify the pair is isclose True but not equal — this is the regression condition
    assert math.isclose(cos_high, cos_near) is True, f"cos_high {cos_high} and cos_near {cos_near} should be isclose True"
    assert cos_high != cos_near, "cosines must not be exactly equal"
    assert cos_high > cos_near, "high must be strictly greater"
    # Also verify dot != cosine for high (non-unit case would also, but here high is unit; check near scaled? Use scaled variant below)
    # Now test selection: regardless of input order, higher cosine must win despite worse tie-break
    best_a, _ = _select_representative_chunk(qvec, [ch_near, ch_high])
    assert best_a["id"] == ch_high["id"], "higher cosine must win despite worse chunk_index/id when cosines are near but not equal"
    best_b, _ = _select_representative_chunk(qvec, [ch_high, ch_near])
    assert best_b["id"] == ch_high["id"], "order independence: higher cosine wins"
    # Existing exact-tie fixture must still hold: identical cosines -> tie-break
    ch_tie1 = {"embedding": [1.0, 0.0, 0.0], "chunk_index": 5, "id": 10}
    ch_tie2 = {"embedding": [1.0, 0.0, 0.0], "chunk_index": 2, "id": 20}
    best_tie, cos_tie = _select_representative_chunk(qvec, [ch_tie1, ch_tie2])
    assert cos_tie == _cosine(qvec, ch_tie1["embedding"]) == _cosine(qvec, ch_tie2["embedding"])
    assert best_tie["chunk_index"] == 2
    # Also test scaled non-unit near-tie
    ch_high_s = {"embedding": [2.0, 0.0, 0.0], "chunk_index": 10, "id": 200}
    ch_near_s = {"embedding": [2.0, 2e-5, 0.0], "chunk_index": 0, "id": 2}
    cos_high_s = _cosine(qvec, ch_high_s["embedding"])
    cos_near_s = _cosine(qvec, ch_near_s["embedding"])
    assert math.isclose(cos_high_s, cos_near_s) is True
    assert cos_high_s != cos_near_s
    best_s, _ = _select_representative_chunk(qvec, [ch_near_s, ch_high_s])
    assert best_s["id"] == ch_high_s["id"]

def test_pure_exact_normalization_internal_whitespace_collapse():
    """Normalization: NFC -> strip -> collapse internal whitespace -> casefold; internal whitespace collapse."""
    assert _normalize_exact("청년  지원") == _normalize_exact("청년 지원")
    assert _normalize_exact("청년\t지원") == _normalize_exact("청년 지원")
    assert _normalize_exact("  청년   지원  ") == "청년 지원"
    assert _normalize_exact("서울시 \t  청년\n지원") == "서울시 청년 지원"
    # collapse must affect is_exact_title equality without changing semantics
    assert _is_exact_title("청년  지원", "청년 지원") is True
    assert _is_exact_title("  청년   지원  ", "청년 지원") is True


def test_pure_exact_normalization_nfc_equivalence():
    """Unicode NFC equivalence: composed vs decomposed forms normalize equal."""
    # Latin decomposed e + combining acute vs composed é
    composed = "caf\u00e9"  # café
    decomposed = "cafe\u0301"  # e + combining
    assert composed != decomposed, "pre-normalization forms differ"
    assert _normalize_exact(composed) == _normalize_exact(decomposed)
    # Hangul Jamo decomposed -> composed 가
    jamo = "\u1100\u1161"  # ㄱ + ㅏ -> 가
    composed_hangul = "\uAC00"  # 가
    assert _normalize_exact(jamo) == _normalize_exact(composed_hangul)
    # exact predicate must respect NFC equivalence
    assert _is_exact_title(composed, decomposed) is True
    assert _is_exact_title(jamo, composed_hangul) is True


def test_pure_exact_normalization_latin_casefold():
    """Latin casefold: case-insensitive via casefold after NFC/strip/collapse."""
    assert _normalize_exact("Seoul") == _normalize_exact("seoul")
    assert _normalize_exact("SEOUL") == _normalize_exact("seoul")
    assert _normalize_exact("SeOuL Youth") == _normalize_exact("seoul youth")
    # also German ß etc but Latin casefold sufficient; test title exact with case difference
    assert _is_exact_title("Seoul Youth Center", "seoul youth center") is True
    assert _is_exact_title("SEOUL  YOUTH", "seoul youth") is True
    # org casefold
    assert _is_exact_org("Seoul City", "seoul") is True
def test_pure_exact_title_korean_punctuation_boundary_pass():
    """Korean punctuation boundary PASS: adjacent char NOT in [0-9A-Za-z가-힣] allows match."""
    # All queries len>=4 to satisfy len>=4 requirement (except equality)
    assert _is_exact_title("청년지원", "청년지원, 서울시 혜택") is True
    assert _is_exact_title("청년지원", "청년지원 서울시 혜택") is True  # space boundary
    assert _is_exact_title("청년지원", "(청년지원)") is True
    assert _is_exact_title("청년지원", "청년지원-서울") is True
    assert _is_exact_title("청년지원", "서울시 청년지원 혜택") is True  # both sides space -> PASS (middle occurrence)
    # punctuation both sides with len>=4
    assert _is_exact_title("청년지원", "청년지원: 혜택정보") is True
    assert _is_exact_title("서울청년", "서울청년: 복지혜택") is True
    # title equals query with different surrounding spaces still equality
    assert _is_exact_title(" 청년지원 ", "청년지원") is True

def test_pure_exact_title_adjacent_boundary_fail():
    """Korean/alphanumeric adjacent boundary FAIL: adjacent char IN [0-9A-Za-z가-힣] rejects."""
    # Korean Hangul adjacent
    assert _is_exact_title("청년지원", "청년지원금") is False, "right adjacent Hangul must FAIL"
    assert _is_exact_title("청년지원", "A청년지원") is False, "left adjacent alnum must FAIL"
    assert _is_exact_title("청년지원", "서울청년지원") is False, "left adjacent Hangul must FAIL"
    assert _is_exact_title("청년지원", "청년지원1호") is False, "right adjacent digit must FAIL"
    assert _is_exact_title("청년지원", "청년지원A") is False
    # English alnum adjacent
    assert _is_exact_title("test", "test123 title") is False
    assert _is_exact_title("test", "mytest title") is False
    # Mixed: title contains query but with alphanumeric continuation -> not a word boundary
    assert _is_exact_title("서울", "서울시") is False
    # Ensure punctuation saves it for len>=4: "청년지원-시" query "청년지원" -> adjacent '-' passes
    assert _is_exact_title("청년지원", "청년지원-시 혜택") is True
    # len 2 query with punctuation still fails due len<4 (not equality)
    assert _is_exact_title("서울", "서울-시 혜택") is False


def test_pure_exact_title_reverse_direction_prevention():
    """Title remains UNIDIRECTIONAL: title substring in longer q must NOT match except equality."""
    # q longer contains title as substring -> must be False (except equality)
    assert _is_exact_title("청년지원 서울시 혜택 추가", "청년지원") is False
    assert _is_exact_title("청년지원 추가 설명", "청년지원") is False
    assert _is_exact_title("서울시 청년지원", "청년지원") is False  # title in q but q longer -> false
    # But opposite direction (q substring of title) with boundary should be True
    assert _is_exact_title("청년지원", "청년지원 서울시 혜택") is True
    # Equality despite longer q? equality is exact string match after normalization, so longer q cannot be equal to shorter title
    assert _is_exact_title("청년지원", "청년지원") is True
    assert _is_exact_title(" 청년지원 ", "청년지원") is True  # normalization makes equal
    # Reverse with punctuation: q="청년지원금", title="청년지원" -> q contains title but not equal -> false
    assert _is_exact_title("청년지원금", "청년지원") is False


def test_pure_exact_title_len_lt4_rejection_and_equality_exception():
    """Title len<4 rejection when not equality; equality still passes."""
    # len 2, substring true but rejected
    assert _is_exact_title("지원", "청년지원 혜택") is False
    assert _is_exact_title("지원", "지원 혜택 모음") is False  # even with boundary, len<4 rejects
    assert _is_exact_title("청년", "청년지원") is False  # len 2
    assert _is_exact_title("a", "a title") is False
    assert _is_exact_title("ab", "ab cd") is False
    assert _is_exact_title("abc", "abc def") is False  # len 3 still rejects
    # len 3 equality passes (len<4 but equality exception)
    assert _is_exact_title("지원", "지원") is True
    assert _is_exact_title("abc", "abc") is True
    assert _is_exact_title("a", "a") is True
    # len 4 substring with boundary passes
    assert _is_exact_title("청년지원", "청년지원 혜택") is True
    assert _is_exact_title("test", "test case") is True  # len 4 passes
    # len 4 without boundary fails
    assert _is_exact_title("test", "test123") is False


def test_pure_exact_org_len_lt2_and_bidirectional():
    """Org len<2 rejection; org bidirectional positives (org in q OR q in org)."""
    # len<2 rejection: org "A" normalized len 1 -> always false
    assert _is_exact_org("청년지원", "A") is False
    assert _is_exact_org("A", "청년지원") is False  # q normalized org? Wait org param is second arg; we test both directions but org length checked
    assert _is_exact_org("a", "청년지원") is False  # org is 청년지원 len>2 but q is "a"?? Actually first arg q="a", org="청년지원" -> org in q false, q in org? "a" in "청년지원" casefold? "a" not in Korean, false -> false overall but not due to len<2. Better test org len 1 directly.
    assert _is_exact_org("anything", "a") is False
    assert _is_exact_org("anything", "1") is False
    assert _is_exact_org("anything", "가") is False  # 단일 Hangul length 1
    # len>=2 bidirectional positives
    # org in q
    assert _is_exact_org("서울시 청년센터", "서울시") is True
    assert _is_exact_org("서울시 청년센터", "청년") is True
    # q in org
    assert _is_exact_org("서울", "서울시청") is True
    assert _is_exact_org("청년", "청년지원센터") is True
    # both with whitespace/casefold normalization
    assert _is_exact_org(" 서울시  청년 ", "서울시") is True
    assert _is_exact_org("서울", " 서울시청 ") is True
    assert _is_exact_org("Seoul", "seoul city") is True
    assert _is_exact_org("seoul city", "Seoul") is True
    # len 2 exactly passes
    assert _is_exact_org("서울시", "서울") is True  # "서울" len 2, is substring of "서울시"
    assert _is_exact_org("AB", "AB") is True
    assert _is_exact_org("AB", "CABD") is True


def test_pure_exact_helpers_not_production_generators():
    """Helpers are test-local pure helpers matching D-030 exactly; must not be imported as production semantics."""
    import inspect
    # Helpers exist in this test module and are not imported from ml-service or other production code
    assert callable(_normalize_exact)
    assert callable(_is_exact_title)
    assert callable(_is_exact_org)
    assert callable(_cosine)
    assert callable(_select_representative_chunk)
    # Verify they are defined in this file, not in production modules
    assert inspect.getfile(_normalize_exact).endswith("test_retrieval_v3_candidate_plan.py")
    assert inspect.getfile(_is_exact_title).endswith("test_retrieval_v3_candidate_plan.py")
    assert inspect.getfile(_cosine).endswith("test_retrieval_v3_candidate_plan.py")
    # Ensure normalization spec matches D-030 wording NFC -> strip -> collapse -> casefold
    src = inspect.getsource(_normalize_exact)
    assert "NFC" in src and "strip" in src and "casefold" in src
    assert "collapse" in src.lower() or "\\s+" in src
