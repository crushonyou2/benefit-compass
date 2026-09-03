"""D-054 bounded-implementation contracts — pure/static/mock only, no real IO.

Covers the frozen safe-action-v1 + production-exclusion-v2/date-capture contract path:
effective plan-v4 pin, query-only safe action, pre-retrieval exclusion, independent
audit, capture ordering, structured evidence/result/selection, forgery rejection.

No protected dev/holdout plaintext, no real DB/network/model/embedding/protected reads.
"""
import copy
import hashlib
import inspect
import json
import pathlib
import random
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from retrieval_v3.candidate_registry import load_and_validate, validate_data, EXPECTED_SHA as REG_SHA
from retrieval_v3.safe_action import (
    classify_safe_action,
    normalize_query_v1,
    action_correct_for_role,
    U_ABSTAIN,
    G_BENEFIT,
    R_FRAME,
    POLICY_SHA256 as SA_SHA,
)
from retrieval_v3.production_exclusion import (
    classify_production_exclusion,
    filter_policies_for_retrieval,
    PRODUCTION_EXCLUDED,
    NOT_EXCLUDED,
    UNMEASURABLE_HOLD,
    POLICY_SHA256 as PE_SHA,
)
from retrieval_v3.evaluation_context import (
    capture_pinned_context,
    validate_pinned_context,
    is_valid_iso_date,
    CAPTURE_STATEMENTS,
)
from retrieval_v3.safety import (
    evaluate_owned_unsupported,
    evaluate_owned_ambiguous,
    check_production_exclusion,
    cross_check_owned_core,
)
from retrieval_v3.selection import EXPECTED_SAFETY_GATES
from retrieval_v3.result_schema import validate_complete_result
from retrieval_v3.runner import Runner
from retrieval_v3 import audit as _audit

REPO = pathlib.Path(__file__).resolve().parents[1]
PLAN_V4 = REPO / "eval" / "retrieval-v3" / "candidate-plan" / "candidate-plan-v4.json"
PLAN_V1 = REPO / "eval" / "retrieval-v3" / "candidate-plan" / "candidate-plan-v1.json"
SA_POLICY = REPO / "eval" / "retrieval-v3" / "candidate-plan" / "safe-action-policy-v1.json"
PE_POLICY = REPO / "eval" / "retrieval-v3" / "candidate-plan" / "production-exclusion-policy-v2.json"

V4_SHA = "a25d9c482094696ff7a438593979813ac568c91a977a2543a50618ca4f5177d6"
SA_EXPECTED = "c512fb5627179697a987b05a2431b8f7e30d1153af2ff6dca37995f6b232a35d"
PE_EXPECTED = "6fee9ec22d5d3ac153ff19a6b1b5d27ab6a6a43bda11e35821d689f938968fe5"

SYN_TZ = "SYNTH-TZ"
SYN_DATE = "2026-02-10"


def _sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def _fake_vec(seed):
    rnd = random.Random(seed)
    v = [rnd.uniform(-1, 1) for _ in range(768)]
    norm = (sum(x * x for x in v) ** 0.5) or 1
    return [round(x / norm, 6) for x in v]


def _fake_emb(q):
    h = hashlib.sha256(q.encode()).digest()
    return _fake_vec(int.from_bytes(h[:4], "little"))


def _policies(n, biz_end=None, start=0):
    out = []
    for i in range(start, start + n):
        out.append({
            "id": i, "source": "youth", "source_id": f"p{i}",
            "title": f"policy {i} title text", "support_content": "support words",
            "summary": "", "keywords": "", "add_qualify": "", "income_etc": "",
            "apply_method": "", "org": "org", "biz_end": biz_end,
            "chunks": [{"embedding": _fake_vec(i), "chunk_index": 0, "id": i}],
        })
    return out


def _task(tid, query, stratum, gold=True):
    golds = [{"source": "youth", "source_id": "p0", "grade": 2}] if gold else []
    return {"task_id": tid, "query": query, "golds": golds, "stratum": stratum, "location_bearing": False}


def _context_exec(tz=SYN_TZ, date=SYN_DATE, log=None):
    def fn(sql):
        if log is not None:
            log.append(sql)
        assert sql in ("SHOW TimeZone", "SELECT CURRENT_DATE"), f"capture inventory must be exactly the two statements, got {sql!r}"
        return {"SHOW TimeZone": tz, "SELECT CURRENT_DATE": date}[sql]
    return fn


def _echo_owned_adapter(biz_map, as_of, record=None):
    """Safety adapter that returns exactly the runner-owned core (honest)."""
    def fn(payload):
        if record is not None:
            record.append(payload)
        tres = payload["results"]["task_results"]
        u = [action_correct_for_role(tr["safe_action"], "unsupported") for tr in tres if tr.get("stratum") == "unsupported_no_answer"]
        a = [action_correct_for_role(tr["safe_action"], "ambiguous") for tr in tres if tr.get("stratum") == "ambiguous"]
        top5 = {tr["task_id"]: list((tr.get("retrieved_internal") or [])[:5]) for tr in tres}
        ou = evaluate_owned_unsupported(u)
        oa = evaluate_owned_ambiguous(a)
        g, d = check_production_exclusion(top5, biz_map, as_of, len(tres), len(tres) * 5)
        return {
            "unsupported": ou, "ambiguous": oa, "production_exclusion": {"gate": g, **d},
            "official_link": {"gate": "PASS", "unique": 1, "mismatches": []},
            "http_resolution": {"gate": "PASS", "unique": 100, "successes": 100, "required": 99},
            "cost": {"gate": "PASS", "index_ratio": 1.0, "rows_ratio": 1.0, "extra_model_calls": 0},
        }
    return fn


# ---- A) effective plan v4 pin ----

def test_d054_v4_pinned():
    assert _sha(PLAN_V4) == V4_SHA
    assert REG_SHA == V4_SHA
    data = load_and_validate()
    assert data["plan_id"] == "retrieval-v3-candidate-plan-v4"
    assert data["version"] == "4.0.0"
    assert len(data["configs"]) == 18
    assert _sha(SA_POLICY) == SA_EXPECTED == SA_SHA
    assert data["safe_action_policy"]["policy_sha256"] == SA_EXPECTED
    assert data["production_exclusion_policy"]["policy_sha256"] == PE_EXPECTED


def test_d054_18_tuples_identical_to_frozen():
    from retrieval_v3.candidate_registry import EXPECTED_CONFIGS
    v4 = json.loads(PLAN_V4.read_text(encoding="utf-8"))
    v1 = json.loads(PLAN_V1.read_text(encoding="utf-8"))
    assert v4["configs"] == EXPECTED_CONFIGS, "registry constants must equal frozen v4 tuples"
    assert v4["configs"] == v1["configs"], "v4 must preserve the exact 18 frozen tuples/order"
    assert [c["config_id"] for c in v4["configs"]] == [f"candidate-a-{i:02d}" for i in range(1, 19)]


def test_d054_v4_policy_ref_drift_rejected():
    data = load_and_validate()
    bad = copy.deepcopy(data)
    bad["safe_action_policy"]["policy_sha256"] = "0" * 64
    try:
        validate_data(bad)
        assert False, "safe-action ref drift must fail closed"
    except ValueError:
        pass
    bad = copy.deepcopy(data)
    bad["production_exclusion_policy"]["policy_sha256"] = "0" * 64
    try:
        validate_data(bad)
        assert False, "exclusion ref drift must fail closed"
    except ValueError:
        pass
    bad = copy.deepcopy(data)
    del bad["selection_rule"]["safety_gates_dev"]["production_exclusion_intrusion"]
    try:
        validate_data(bad)
        assert False, "missing effective gate must fail closed"
    except ValueError:
        pass
    bad = copy.deepcopy(data)
    bad["selection_rule"]["safety_gates_dev"]["ineligible_expired_intrusion"] = "x"
    try:
        validate_data(bad)
        assert False, "retained old gate must fail closed"
    except ValueError:
        pass
    bad = copy.deepcopy(data)
    bad["plan_id"] = "retrieval-v3-candidate-plan-v1"
    try:
        validate_data(bad)
        assert False, "v1 plan_id must fail closed"
    except ValueError:
        pass


# ---- B) safe action ----

def test_d054_normalization_exact():
    assert normalize_query_v1("  청년   지원금\t알려줘  ") == "청년 지원금 알려줘"
    assert normalize_query_v1("ABC") == "abc"
    import unicodedata
    assert normalize_query_v1(unicodedata.normalize("NFD", "é")) == "é"
    assert normalize_query_v1("") == ""
    assert normalize_query_v1("   ") == ""
    assert normalize_query_v1(None) == ""


def test_d054_lexicons_exact():
    pol = json.loads(SA_POLICY.read_text(encoding="utf-8"))
    assert list(U_ABSTAIN) == pol["lexicons"]["U_ABSTAIN"]["entries"]
    assert list(G_BENEFIT) == pol["lexicons"]["G_BENEFIT"]["entries"]
    assert list(R_FRAME) == pol["lexicons"]["R_FRAME"]["entries"]
    assert pol["normalization"]["steps"] == ["NFC normalize", "strip leading/trailing whitespace", "collapse every internal run of whitespace ([\\s]+) to one ASCII space", "casefold"]
    assert pol["pseudocode"].startswith("N = norm_v1(query_text)")


def test_d054_precedence():
    assert classify_safe_action("") == "ABSTAIN"
    assert classify_safe_action("   ") == "ABSTAIN"
    assert classify_safe_action("외국인 관광객 지원금 알려줘") == "ABSTAIN", "P_U wins overlaps"
    assert classify_safe_action("주식 투자 알려주세요") == "ABSTAIN"
    assert classify_safe_action("지원금 알려줘") == "CLARIFY"
    assert classify_safe_action("복지 혜택이 궁금해") == "CLARIFY"
    assert classify_safe_action("지원금") == "ANSWER", "G alone answers"
    assert classify_safe_action("알려줘") == "ANSWER", "R alone answers"
    assert classify_safe_action("청년 월세 지원 조건이 언제까지인가요") == "ANSWER"
    assert classify_safe_action("policy alpha 3") == "ANSWER"
    assert action_correct_for_role("ABSTAIN", "unsupported") is True
    assert action_correct_for_role("CLARIFY", "unsupported") is False
    assert action_correct_for_role("CLARIFY", "ambiguous") is True
    assert action_correct_for_role("ANSWER", "ambiguous") is False
def test_d054_query_only_signature():
    import ast
    sig = inspect.signature(classify_safe_action)
    assert list(sig.parameters) == ["query_text"], f"classifier must accept ONLY raw query_text, got {list(sig.parameters)}"
    # Identifier-level proof: code reads no stratum/gold/task/protected/retrieval/config/corpus/score
    # channel (docstrings may name the boundary; code must not touch it).
    src = pathlib.Path("eval/retrieval-v3/safe_action.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    forbidden = {"stratum", "golds", "gold", "task_id", "protected", "retrieval", "embeddings", "embedding", "config", "corpus", "scores", "results", "labels"}
    used = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used.add(node.id)
        elif isinstance(node, ast.Attribute):
            used.add(node.attr)
        elif isinstance(node, ast.arg):
            used.add(node.arg)
    hits = {u for u in used if u.lower() in forbidden}
    assert not hits, f"query-only code must not touch {hits}"
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add((node.module or "").split(".")[0])
    assert imports <= {"re", "unicodedata", "__future__"}, f"pure module imports allowlisted only, got {imports}"


def test_d054_action_once_before_retrieval_shared():
    import retrieval_v3.runner as R
    plan = load_and_validate()
    tasks = [
        _task("t0", "policy alpha 0", "natural_needs"),
        _task("t1", "policy alpha 1 외국인 관광객", "unsupported_no_answer", gold=False),
        _task("t2", "policy alpha 2 지원금 알려줘", "ambiguous"),
    ]
    policies = _policies(4)
    order = []
    real_classify = R.classify_safe_action
    calls = {"n": 0}

    def counting(q):
        calls["n"] += 1
        order.append(("action", q))
        return real_classify(q)

    def spy_emb(q):
        order.append(("retrieval", q))
        return _fake_emb(q)

    record = []
    runner = Runner(candidate_plan=plan, embedding_fn=spy_emb,
                    evaluation_context_exec_fn=_context_exec(),
                    safety_evidence_fn=_echo_owned_adapter({("youth", f"p{i}"): None for i in range(4)}, SYN_DATE, record))
    old = R.classify_safe_action
    R.classify_safe_action = counting
    try:
        with tempfile.TemporaryDirectory() as td:
            runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="s", set_role="none", set_sha=None,
                                      audit_log=pathlib.Path(td) / "a.jsonl", output_path=None, skip_audit=True)
    finally:
        R.classify_safe_action = old
    assert calls["n"] == 3, f"action must be computed once per task (3), not per config, got {calls['n']}"
    first_retrieval = next(i for i, e in enumerate(order) if e[0] == "retrieval")
    assert all(e[0] == "action" for e in order[:first_retrieval]), "every action must precede any retrieval"
    assert len(record) == 18
    per_task = {}
    for payload in record:
        for tr in payload["results"]["task_results"]:
            per_task.setdefault(tr["task_id"], set()).add(tr["safe_action"])
    assert all(len(v) == 1 for v in per_task.values()), f"identical action across all 18 configs required: {per_task}"
    assert per_task == {"t0": {"ANSWER"}, "t1": {"ABSTAIN"}, "t2": {"CLARIFY"}}


def test_d054_action_ignores_golds_config_corpus():
    assert classify_safe_action("policy alpha 0") == "ANSWER"
    # Same query, wildly different golds/strata => same action (unit level).
    import retrieval_v3.runner as R
    plan = load_and_validate()
    policies = _policies(3)
    policies[0]["title"] = "골프 회원권 외제차"  # corpus carries U markers; must not leak into action
    tasks = [_task("t0", "policy alpha 0", "natural_needs")]
    record = []
    runner = Runner(candidate_plan=plan, embedding_fn=_fake_emb,
                    evaluation_context_exec_fn=_context_exec(),
                    safety_evidence_fn=_echo_owned_adapter({("youth", f"p{i}"): None for i in range(3)}, SYN_DATE, record))
    with tempfile.TemporaryDirectory() as td:
        runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="s", set_role="none", set_sha=None,
                                  audit_log=pathlib.Path(td) / "a.jsonl", output_path=None, skip_audit=True)
    assert record[0]["results"]["task_results"][0]["safe_action"] == "ANSWER"


def test_d054_headline_non_answer_miss_visible_suppressed_internal_kept():
    plan = load_and_validate()
    policies = _policies(4)
    tasks = [_task("t0", "policy alpha 0 지원금 알려줘", "natural_needs")]  # CLARIFY forced on headline-shaped task
    record = []
    runner = Runner(candidate_plan=plan, embedding_fn=_fake_emb,
                    evaluation_context_exec_fn=_context_exec(),
                    safety_evidence_fn=_echo_owned_adapter({("youth", f"p{i}"): None for i in range(4)}, SYN_DATE, record))
    with tempfile.TemporaryDirectory() as td:
        res = runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="s", set_role="none", set_sha=None,
                                        audit_log=pathlib.Path(td) / "a.jsonl", output_path=None, skip_audit=True)
    tr = record[0]["results"]["task_results"][0]
    assert tr["safe_action"] == "CLARIFY"
    assert tr["retrieved"] == [], "non-ANSWER must expose no policy recommendation"
    assert len(tr["retrieved_internal"]) > 0, "internal ranking preserved for audit"
    assert res["per_config_metrics"][0]["success_at_5"] == 0.0, "headline non-ANSWER is a miss"


# ---- C) mechanical counts, old semantics gone ----

def test_d054_owned_gate_math():
    assert evaluate_owned_unsupported([True] * 26 + [False])["gate"] == "PASS"
    assert evaluate_owned_unsupported([True] * 25 + [False] * 2)["gate"] == "NO-GO"
    assert evaluate_owned_unsupported([True] * 26)["gate"] == "HOLD"
    assert evaluate_owned_unsupported(None)["gate"] == "HOLD"
    assert evaluate_owned_ambiguous([True] * 21 + [False] * 2)["gate"] == "PASS"
    assert evaluate_owned_ambiguous([True] * 20 + [False] * 3)["gate"] == "NO-GO"
    assert evaluate_owned_ambiguous([True] * 21)["gate"] == "HOLD"


def test_d054_old_semantics_absent_canonically():
    for rel in ("eval/retrieval-v3/runner.py", "eval/retrieval-v3/result_schema.py", "eval/retrieval-v3/selection.py"):
        src = pathlib.Path(rel).read_text(encoding="utf-8")
        assert "ineligible_expired" not in src, f"old key must not be effective in {rel}"
    src = pathlib.Path("eval/retrieval-v3/runner.py").read_text(encoding="utf-8")
    assert "abstention_credit" not in src, "canonical path must not use retrieval-emptiness credit"
    assert "check_ineligible_expired" not in src, "canonical path must not use the historical checker"


def test_d054_canonical_counts_action_derived_not_empty_heuristic():
    # 180 all-ANSWER synthetic tasks, nonempty retrieval everywhere, yet 0/27 + 0/23 NO-GO.
    from retrieval_v3.runner import DEV_STRATA_EXACT
    plan = load_and_validate()
    tasks = []
    idx = 0
    for s in ("exact_navigation", "natural_needs", "exploratory_multi_valid", "multi_constraint", "short_keywords", "colloquial_typo_spacing_abbrev", "ambiguous", "unsupported_no_answer"):
        for j in range(DEV_STRATA_EXACT[s]):
            golds = [] if s == "unsupported_no_answer" else [{"source": "youth", "source_id": "p0", "grade": 1 if s == "ambiguous" else 2}]
            tasks.append({"task_id": f"c{idx:03d}", "query": f"policy alpha {idx}", "golds": golds, "stratum": s, "location_bearing": False})
            idx += 1
    _loc = 0
    for t in tasks:
        if _loc >= 54:
            break
        if t["stratum"] in ("exact_navigation", "natural_needs", "exploratory_multi_valid", "multi_constraint", "short_keywords", "colloquial_typo_spacing_abbrev"):
            t["location_bearing"] = True
            _loc += 1
    policies = _policies(6)
    biz = {("youth", f"p{i}"): None for i in range(6)}
    record = []
    sha = "d" * 64
    with tempfile.TemporaryDirectory() as td:
        log = pathlib.Path(td) / "audit.jsonl"
        _audit.append_event(str(log), action="protected_access_start", set_role="dev", set_sha=sha, session_id="s", candidate_id="v3-candidate-dev-v1", outcome="success")
        kw = {
            "safety_evidence_fn": _echo_owned_adapter(biz, SYN_DATE, record),
            "d003_baseline_fn": lambda tid, q, b, ctx=None: None,
            "clock_fn": _counter_clock(),
            "corpus_provenance_fn": lambda: {"total_policies": 6, "snapshot": "test"},
            "evaluation_context_exec_fn": _context_exec(),
        }
        runner = Runner(candidate_plan=plan, embedding_fn=_fake_emb, protected_set_loader=lambda r, s: tasks, audit_log_path=log, adapter_kind="real", **kw)
        res = runner.run_dev_evaluation(tasks=[], policies=policies, session_id="s", set_role="dev", set_sha=sha, audit_log=log, output_path=None, skip_audit=False)
    c0 = "candidate-a-01"
    assert res["safety_per_config"][c0]["unsupported"] == {"gate": "NO-GO", "success": 0, "required": 26, "denominator": 27}
    assert res["safety_per_config"][c0]["ambiguous"] == {"gate": "NO-GO", "success": 0, "required": 21, "denominator": 23}
    for payload in record:
        for tr in payload["results"]["task_results"]:
            assert len(tr["retrieved_internal"]) > 0, "retrieval ran (nonempty) yet actions earned no credit"


def _counter_clock():
    cnt = [0]

    def fn():
        cnt[0] += 1000000
        return cnt[0]
    return fn


# ---- D) production exclusion ----

def test_d054_classifier_fixtures():
    assert classify_production_exclusion("youth", "p1", "2026-02-09", SYN_DATE) == PRODUCTION_EXCLUDED
    assert classify_production_exclusion("youth", "p1", "2026-02-10", SYN_DATE) == NOT_EXCLUDED
    assert classify_production_exclusion("youth", "p1", "2026-02-11", SYN_DATE) == NOT_EXCLUDED
    assert classify_production_exclusion("youth", "p1", None, SYN_DATE) == NOT_EXCLUDED
    # Null carries NO universal not-expired/eligible claim.
    assert NOT_EXCLUDED not in ("eligible", "not expired", "not_expired", "not-expired")
    assert "eligible" not in NOT_EXCLUDED


def test_d054_classifier_hold_fixtures():
    for bad in ("2026/02/09", "", "yesterday", "2026-13-01", "2026-02-30", 20260209, " 2026-02-09"):
        assert classify_production_exclusion("youth", "p1", bad, SYN_DATE) == UNMEASURABLE_HOLD, f"malformed {bad!r} must HOLD"
    assert classify_production_exclusion("", "p1", None, SYN_DATE) == UNMEASURABLE_HOLD
    assert classify_production_exclusion("youth", "", None, SYN_DATE) == UNMEASURABLE_HOLD
    assert classify_production_exclusion("youth", "p1", None, "bad-date") == UNMEASURABLE_HOLD
    assert classify_production_exclusion("youth", "p1", None, None) == UNMEASURABLE_HOLD


def test_d054_filter_pre_retrieval():
    policies = _policies(4)
    policies[1]["biz_end"] = "2026-02-09"  # excluded
    policies[2]["biz_end"] = "2026-02-10"  # equal => kept
    policies[3]["biz_end"] = "not-a-date"  # HOLD => kept for audit, never silent PASS
    before = copy.deepcopy(policies)
    kept = filter_policies_for_retrieval(policies, SYN_DATE)
    assert [p["source_id"] for p in kept] == ["p0", "p2", "p3"]
    assert policies == before, "filter must not mutate input"
    try:
        filter_policies_for_retrieval(policies, "bad-date")
        assert False, "invalid pinned date must fail closed"
    except ValueError:
        pass


def test_d054_excluded_cannot_rank():
    import retrieval_v3.runner as R
    plan = load_and_validate()
    policies = _policies(4)
    policies[0]["biz_end"] = "2020-01-01"  # excluded, exact-title match would rank it first if present
    policies[0]["title"] = "policy alpha 0"
    tasks = [_task(f"t{i}", "policy alpha 0", "natural_needs") for i in range(3)]
    seen = []

    orig_dense = R.dense_top100
    orig_sparse = R.sparse_top100

    def spy_dense(qvec, pols):
        seen.append(("dense", [(p.get("source"), p.get("source_id")) for p in pols]))
        return orig_dense(qvec, pols)

    def spy_sparse(q, pols, cfg):
        seen.append(("sparse", [(p.get("source"), p.get("source_id")) for p in pols]))
        return orig_sparse(q, pols, cfg)

    record = []
    runner = Runner(candidate_plan=plan, embedding_fn=_fake_emb,
                    evaluation_context_exec_fn=_context_exec(),
                    safety_evidence_fn=_echo_owned_adapter({("youth", f"p{i}"): policies[i].get("biz_end") for i in range(4)}, SYN_DATE, record))
    R.dense_top100 = spy_dense
    R.sparse_top100 = spy_sparse
    try:
        with tempfile.TemporaryDirectory() as td:
            runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="s", set_role="none", set_sha=None,
                                      audit_log=pathlib.Path(td) / "a.jsonl", output_path=None, skip_audit=True)
    finally:
        R.dense_top100 = orig_dense
        R.sparse_top100 = orig_sparse
    assert seen, "retrieval must have run"
    for channel, ids in seen:
        assert ("youth", "p0") not in ids, f"excluded row reached {channel}"
    for payload in record:
        for tr in payload["results"]["task_results"]:
            assert all((d.get("source"), d.get("source_id")) != ("youth", "p0") for d in tr["retrieved_internal"])


# ---- E) independent audit ----

def _top5(n, ids=("youth", "p0")):
    return {f"t{i:03d}": [{"source": ids[0], "source_id": ids[1]} for _ in range(5)] for i in range(n)}


def test_d054_audit_exact_180_900():
    look = {("youth", "p0"): None}
    g, d = check_production_exclusion(_top5(180), look, SYN_DATE, 180, 900)
    assert g == "PASS" and d["intrusions_task"] == 0 and d["intrusions_slot"] == 0
    assert d["expected_tasks"] == 180 and d["expected_slots"] == 900
    bad = _top5(180)
    bad["t007"] = [{"source": "youth", "source_id": "px"} for _ in range(5)]
    look2 = {("youth", "p0"): None, ("youth", "px"): "2020-05-05"}
    g, d = check_production_exclusion(bad, look2, SYN_DATE, 180, 900)
    assert g == "NO-GO" and d["intrusions_task"] == 1 and d["intrusions_slot"] == 5
    g, _ = check_production_exclusion(_top5(180), {}, SYN_DATE, 180, 900)
    assert g == "HOLD", "missing lookup must HOLD"
    g, _ = check_production_exclusion(_top5(179), look, SYN_DATE, 180, 900)
    assert g == "HOLD", "count mismatch must HOLD"
    short = _top5(180)
    short["t003"] = short["t003"][:4]
    g, _ = check_production_exclusion(short, look, SYN_DATE, 180, 900)
    assert g == "HOLD", "short top5 must HOLD"
    g, _ = check_production_exclusion(_top5(180), look, "bad-date", 180, 900)
    assert g == "HOLD", "bad pinned date must HOLD"
    both = _top5(2)
    both["t000"] = [{"source": "youth", "source_id": "px"} for _ in range(5)]
    look3 = {("youth", "p0"): None, ("youth", "px"): "2020-05-05"}
    del look3[("youth", "p0")]
    g, _ = check_production_exclusion(both, look3, SYN_DATE, 2, 10)
    assert g == "HOLD", "HOLD takes precedence on incomplete measurement"


def test_d054_audit_runs_for_non_answer_internal():
    # All queries ABSTAIN => visible all empty; audit of INTERNAL top5 must still PASS/HOLD/NO-GO.
    plan = load_and_validate()
    policies = _policies(8)
    biz = {("youth", f"p{i}"): None for i in range(8)}
    tasks = [
        _task("t0", "policy alpha 0 외국인 관광객", "unsupported_no_answer", gold=False),
        _task("t1", "policy alpha 1 지원금 알려줘", "ambiguous"),
        _task("t2", "policy alpha 2 외국인 관광객", "unsupported_no_answer", gold=False),
        _task("t3", "policy alpha 3 지원금 알려줘", "ambiguous"),
    ]
    record = []
    runner = Runner(candidate_plan=plan, embedding_fn=_fake_emb,
                    evaluation_context_exec_fn=_context_exec(),
                    safety_evidence_fn=_echo_owned_adapter(biz, SYN_DATE, record))
    with tempfile.TemporaryDirectory() as td:
        res = runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="s", set_role="none", set_sha=None,
                                        audit_log=pathlib.Path(td) / "a.jsonl", output_path=None, skip_audit=True)
    tr0 = record[0]["results"]["task_results"][0]
    assert tr0["retrieved"] == [] and len(tr0["retrieved_internal"]) > 0
    pe = res["safety_per_config"]["candidate-a-01"]["production_exclusion"]
    assert pe["gate"] == "PASS", f"internal audit must PASS on clean corpus despite suppression: {pe}"
    assert pe["expected_tasks"] == 4 and pe["expected_slots"] == 20


def test_d054_audit_catches_intrusion_on_non_answer():
    import retrieval_v3.runner as R
    plan = load_and_validate()
    policies = _policies(8, biz_end="2020-01-01")  # every row excluded
    biz = {("youth", f"p{i}"): "2020-01-01" for i in range(8)}
    tasks = [
        _task("t0", "policy alpha 0 외국인 관광객", "unsupported_no_answer", gold=False),
        _task("t1", "policy alpha 1 지원금 알려줘", "ambiguous"),
    ]
    record = []
    runner = Runner(candidate_plan=plan, embedding_fn=_fake_emb,
                    evaluation_context_exec_fn=_context_exec(),
                    safety_evidence_fn=_echo_owned_adapter(biz, SYN_DATE, record))
    old = R.filter_policies_for_retrieval
    R.filter_policies_for_retrieval = lambda ps, d: list(ps)  # bypass filter: audit must still catch it
    try:
        with tempfile.TemporaryDirectory() as td:
            res = runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="s", set_role="none", set_sha=None,
                                            audit_log=pathlib.Path(td) / "a.jsonl", output_path=None, skip_audit=True)
    finally:
        R.filter_policies_for_retrieval = old
    pe = res["safety_per_config"]["candidate-a-01"]["production_exclusion"]
    assert pe["gate"] == "NO-GO" and pe["intrusions_task"] >= 1, f"bypassed exclusion must be caught: {pe}"


# ---- F) capture ordering ----

def test_d054_capture_once_exact_inventory_and_pins():
    plan = load_and_validate()
    tasks = [_task("t0", "policy alpha 0", "natural_needs")]
    policies = _policies(3)
    log = []
    record = []
    runner = Runner(candidate_plan=plan, embedding_fn=_fake_emb,
                    corpus_provenance_fn=lambda: {"total_policies": 3, "snapshot": "test"},
                    evaluation_context_exec_fn=_context_exec(log=log),
                    safety_evidence_fn=_echo_owned_adapter({("youth", f"p{i}"): None for i in range(3)}, SYN_DATE, record))
    with tempfile.TemporaryDirectory() as td:
        audit_log = pathlib.Path(td) / "a.jsonl"
        res = runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="s", set_role="none", set_sha=None,
                                        audit_log=audit_log, output_path=None, skip_audit=False)
        chain = _audit.read_and_verify_chain(str(audit_log))
    assert log == ["SHOW TimeZone", "SELECT CURRENT_DATE"], f"capture must run exactly once in order, got {log}"
    assert res["evaluation_context"] == {"db_session_timezone": SYN_TZ, "evaluation_as_of_date": SYN_DATE}
    assert res["corpus_provenance"]["db_session_timezone"] == SYN_TZ
    assert res["corpus_provenance"]["evaluation_as_of_date"] == SYN_DATE
    starts = [e for e in chain if e.get("action") == "run_start"]
    assert len(starts) == 1
    assert starts[0].get("db_session_timezone") == SYN_TZ and starts[0].get("evaluation_as_of_date") == SYN_DATE


def test_d054_capture_before_loader_and_run_start():
    plan = load_and_validate()
    tasks = [_task("t0", "policy alpha 0", "natural_needs")]
    policies = _policies(2)
    order = []

    def exec_fn(sql):
        order.append("capture:" + sql)
        return {"SHOW TimeZone": SYN_TZ, "SELECT CURRENT_DATE": SYN_DATE}[sql]

    def loader(role, sha):
        order.append("loader")
        return tasks

    def emb(q):
        order.append("retrieval")
        return _fake_emb(q)

    runner = Runner(candidate_plan=plan, embedding_fn=emb, protected_set_loader=loader,
                    evaluation_context_exec_fn=exec_fn)
    with tempfile.TemporaryDirectory() as td:
        runner.run_dev_evaluation(tasks=[], policies=policies, session_id="s", set_role="none", set_sha=None,
                                  audit_log=pathlib.Path(td) / "a.jsonl", output_path=None, skip_audit=False)
    assert order[0] == "capture:SHOW TimeZone" and order[1] == "capture:SELECT CURRENT_DATE"
    assert order.index("loader") > 1, f"loader must run after capture: {order}"
    assert order.index("retrieval") > order.index("loader")


def test_d054_capture_failure_closes_nothing_runs_nothing():
    plan = load_and_validate()
    loader_calls = []

    def bad_exec(sql):
        return {"SHOW TimeZone": "", "SELECT CURRENT_DATE": "not-a-date"}[sql]

    runner = Runner(candidate_plan=plan, embedding_fn=_fake_emb,
                    protected_set_loader=lambda r, s: (loader_calls.append(1), [])[1],
                    safety_evidence_fn=lambda payload: (_ for _ in ()).throw(AssertionError("must not reach safety")),
                    d003_baseline_fn=lambda *a: None, clock_fn=_counter_clock(),
                    corpus_provenance_fn=lambda: {"total_policies": 1, "snapshot": "t"},
                    evaluation_context_exec_fn=bad_exec, adapter_kind="real")
    sha = "e" * 64
    with tempfile.TemporaryDirectory() as td:
        log = pathlib.Path(td) / "audit.jsonl"
        _audit.append_event(str(log), action="protected_access_start", set_role="dev", set_sha=sha, session_id="s", candidate_id="v3-candidate-dev-v1", outcome="success")
        try:
            runner.run_dev_evaluation(tasks=[], policies=[], session_id="s", set_role="dev", set_sha=sha, audit_log=log, output_path=None, skip_audit=False)
            assert False, "malformed capture must fail closed"
        except RuntimeError as e:
            assert "evaluation-context capture failed" in str(e)
        assert loader_calls == [], "protected loader must never run after capture failure"
        chain = _audit.read_and_verify_chain(str(log))
        assert [e["action"] for e in chain] == ["protected_access_start"], "no grant close on pre-grant failure"
        assert not [e for e in chain if e.get("action") == "run_start"]


    for rel in ("eval/retrieval-v3/evaluation_context.py", "eval/retrieval-v3/production_exclusion.py", "eval/retrieval-v3/safe_action.py"):
        for line in pathlib.Path(rel).read_text(encoding="utf-8").splitlines():
            if "SET TIME ZONE" in line.upper():
                low = line.lower()
                assert ("no " in low and "set" in low) or "not " in low or "without" in low or "prohibit" in low, f"SET TIME ZONE mention must be a prohibition, not a statement: {rel}: {line.strip()}"
    src = pathlib.Path("eval/retrieval-v3/runner.py").read_text(encoding="utf-8")
    assert "SET TIME ZONE" not in src
    import ast
    for rel in ("eval/retrieval-v3/evaluation_context.py", "eval/retrieval-v3/production_exclusion.py", "eval/retrieval-v3/safe_action.py"):
        tree = ast.parse(pathlib.Path(rel).read_text(encoding="utf-8"))
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add((node.module or "").split(".")[0])
        assert imports.isdisjoint({"datetime", "time", "os", "socket", "urllib", "sqlite3"}), f"{rel} must not import clock/IO: {imports}"
    # Behavioral: malformed capture raises instead of falling back to any local date.
    try:
        capture_pinned_context(lambda sql: "garbage")
        assert False, "must fail closed, never fall back"
    except (RuntimeError, ValueError):
        pass
    assert is_valid_iso_date("2026-02-30") is False and is_valid_iso_date("2026-02-10") is True


def test_d054_same_date_everywhere_and_immutable():
    plan = load_and_validate()
    tasks = [_task(f"t{i}", f"policy alpha {i}", "natural_needs") for i in range(3)]
    policies = _policies(4)
    seen_ctx = []

    def d003(tid, q, b, ctx=None):
        seen_ctx.append(copy.deepcopy(ctx))
        return None

    runner = Runner(candidate_plan=plan, embedding_fn=_fake_emb, clock_fn=_counter_clock(), d003_baseline_fn=d003,
                    evaluation_context_exec_fn=_context_exec())
    with tempfile.TemporaryDirectory() as td:
        runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="s", set_role="none", set_sha=None,
                                  audit_log=pathlib.Path(td) / "a.jsonl", output_path=None, skip_audit=True)
    assert seen_ctx, "baseline must be consulted"
    assert all(c == {"db_session_timezone": SYN_TZ, "evaluation_as_of_date": SYN_DATE} for c in seen_ctx), "one pinned date for candidate + baseline"


# ---- G) evidence / result / selection ----

def test_d054_effective_six_gates_old_key_ignored():
    assert EXPECTED_SAFETY_GATES == {"unsupported", "ambiguous", "production_exclusion", "official_link", "http_resolution", "cost"}
    from retrieval_v3.candidate_registry import EXPECTED_SHA, EXPECTED_PREREG_SHA
    per = [{"config_id": f"candidate-a-{i:02d}", "success_at_5": 0.9, "ndcg_at_5": 0.8, "mrr_at_10": 0.7} for i in range(1, 19)]
    ids = [f"candidate-a-{i:02d}" for i in range(1, 19)]
    saf = {c: {
        "unsupported": {"gate": "HOLD", "detail": "t"},
        "ambiguous": {"gate": "HOLD", "detail": "t"},
        "production_exclusion": {"gate": "HOLD", "detail": "t"},
        "ineligible_expired": {"gate": "NO-GO", "detail": "stale ignored"},
        "official_link": {"gate": "HOLD", "detail": "t"},
        "http_resolution": {"gate": "HOLD", "detail": "t"},
        "cost": {"gate": "HOLD", "detail": "t"},
    } for c in ids}
    lat = {c: {"n": 180, "warmup_n": 30, "baseline": {"p50": 500, "p95": 500, "p99": 500}, "candidate": {"p50": 570, "p95": 570, "p99": 570}, "gate": "PASS"} for c in ids}
    ctx = {"db_session_timezone": SYN_TZ, "evaluation_as_of_date": SYN_DATE}
    doc = {"schema_version": 1, "git_head": "0" * 40, "git_dirty": False, "candidate_plan_sha256": EXPECTED_SHA, "prereg_sha256": EXPECTED_PREREG_SHA,
           "provenance": {"candidate_plan_sha256": EXPECTED_SHA, "prereg_sha256": EXPECTED_PREREG_SHA}, "per_config_metrics": per,
           "selection": {"chosen": None, "eligible": []}, "candidate_b_gate": {"admitted": False, "instantiated": False, "status": "not_evaluated"},
           "safety_per_config": saf, "latency_per_config": lat,
           "corpus_provenance": {"total_policies": 1, "snapshot": "t", **ctx}, "evaluation_context": ctx,
           "set_provenance": {"set_role": "dev", "set_sha": "1" * 64, "n": 180, "headline_n": 130}}
    validate_complete_result(doc), "old key present must not disturb effective validation"
    bad = copy.deepcopy(doc)
    del bad["safety_per_config"]["candidate-a-01"]["production_exclusion"]
    try:
        validate_complete_result(bad)
        assert False, "missing effective gate must fail"
    except ValueError:
        pass
    bad = copy.deepcopy(doc)
    bad["evaluation_context"] = {"db_session_timezone": SYN_TZ, "evaluation_as_of_date": "bad"}
    try:
        validate_complete_result(bad)
        assert False, "malformed pinned date must fail"
    except ValueError:
        pass
    bad = copy.deepcopy(doc)
    bad["corpus_provenance"] = {"total_policies": 1, "snapshot": "t"}
    try:
        validate_complete_result(bad)
        assert False, "missing corpus pins must fail"
    except ValueError:
        pass


def test_d054_forgery_rejected_hold():
    # Forged full-PASS adapter against all-ANSWER tasks: owned 0/27 + 0/23 mismatch => HOLD everywhere.
    plan = load_and_validate()
    tasks = [_task(f"t{i}", f"policy alpha {i}", "natural_needs") for i in range(4)]
    policies = _policies(4)
    forged = {
        "unsupported": {"gate": "PASS", "success": 26, "required": 26, "denominator": 27},
        "ambiguous": {"gate": "PASS", "success": 21, "required": 21, "denominator": 23},
        "production_exclusion": {"gate": "PASS", "expected_tasks": 4, "expected_slots": 20, "intrusions_task": 0, "intrusions_slot": 0},
        "official_link": {"gate": "PASS", "unique": 1, "mismatches": []},
        "http_resolution": {"gate": "PASS", "unique": 100, "successes": 100, "required": 100},
        "cost": {"gate": "PASS", "index_ratio": 1.0, "rows_ratio": 1.0, "extra_model_calls": 0},
    }
    runner = Runner(candidate_plan=plan, embedding_fn=_fake_emb,
                    evaluation_context_exec_fn=_context_exec(),
                    safety_evidence_fn=lambda payload: copy.deepcopy(forged))
    with tempfile.TemporaryDirectory() as td:
        res = runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="s", set_role="none", set_sha=None,
                                        audit_log=pathlib.Path(td) / "a.jsonl", output_path=None, skip_audit=True)
    for cid, rep in res["safety_per_config"].items():
        assert rep["unsupported"]["gate"] == "HOLD", f"forgery must not PASS: {cid}"
    assert res["selection"]["eligible"] == [] and res["selection"]["chosen"] is None


def test_d054_audit_pins_backward_compatible_no_plaintext():
    plan = load_and_validate()
    tasks = [_task("t0", "policy alpha CANARY_Q", "natural_needs", gold=True)]
    tasks[0]["golds"] = [{"source": "youth", "source_id": "CANARY_GX1", "grade": 2}]
    policies = _policies(3)
    policies[0]["source_id"] = "CANARY_PX"
    biz = {("youth", "CANARY_PX"): None, ("youth", "p1"): None, ("youth", "p2"): None}
    record = []
    runner = Runner(candidate_plan=plan, embedding_fn=_fake_emb,
                    evaluation_context_exec_fn=_context_exec(),
                    safety_evidence_fn=_echo_owned_adapter(biz, SYN_DATE, record))
    with tempfile.TemporaryDirectory() as td:
        audit_log = pathlib.Path(td) / "a.jsonl"
        res = runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="s", set_role="none", set_sha=None,
                                        audit_log=audit_log, output_path=None, skip_audit=False)
        chain = _audit.read_and_verify_chain(str(audit_log))
        audit_text = audit_log.read_text(encoding="utf-8")
    assert "CANARY" not in json.dumps(res, ensure_ascii=False), "no protected plaintext in result"
    assert "CANARY" not in audit_text, "no protected plaintext in audit"
    kinds = {e["action"] for e in chain}
    assert {"run_start", "run_end"} <= kinds
    for e in chain:
        if e["action"] in ("run_start", "run_end"):
            assert e.get("evaluation_as_of_date") == SYN_DATE and e.get("db_session_timezone") == SYN_TZ
    # Old events without pins stay valid.
    with tempfile.TemporaryDirectory() as td:
        log2 = pathlib.Path(td) / "old.jsonl"
        _audit.append_event(str(log2), action="run_start", set_role="none", set_sha=None, session_id="s")
        _audit.append_event(str(log2), action="run_end", set_role="none", set_sha=None, session_id="s")
        chain2 = _audit.read_and_verify_chain(str(log2))
        assert len(chain2) == 2
        try:
            _audit.append_event(str(log2), action="run_end", set_role="none", set_sha=None, session_id="s", evaluation_as_of_date="bad")
            assert False, "tampered pin must be rejected"
        except Exception:
            pass


# ---- H) no real IO ----

def test_d054_no_real_io_import_hook():
    import sys

    class Blocker:
        BLOCKED = {"socket", "ssl", "urllib.request", "http.client", "sqlite3", "psycopg", "psycopg2", "sentence_transformers", "torch", "requests", "httpx"}

        def find_spec(self, name, path=None, target=None):
            if name.split(".")[0] in self.BLOCKED:
                raise ImportError(f"D-054: real IO module blocked in mock test: {name}")
            return None

    plan = load_and_validate()
    tasks = [_task(f"t{i}", f"policy alpha {i}", "natural_needs") for i in range(3)]
    policies = _policies(3)
    runner = Runner(candidate_plan=plan, embedding_fn=_fake_emb, evaluation_context_exec_fn=_context_exec())
    blocker = Blocker()
    sys.meta_path.insert(0, blocker)
    try:
        with tempfile.TemporaryDirectory() as td:
            res = runner.run_dev_evaluation(tasks=tasks, policies=policies, session_id="s", set_role="none", set_sha=None,
                                            audit_log=pathlib.Path(td) / "a.jsonl", output_path=None, skip_audit=True)
    finally:
        sys.meta_path.remove(blocker)
    assert len(res["per_config_metrics"]) == 18


D054_TESTS = [v for k, v in sorted(globals().items()) if k.startswith("test_d054_")]

if __name__ == "__main__":
    n = 0
    for t in D054_TESTS:
        try:
            t()
            print(f"PASS {t.__name__}")
            n += 1
        except Exception as e:
            print(f"FAIL {t.__name__}: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)
    print(f"ALL {n} D-054 focused tests PASS")
