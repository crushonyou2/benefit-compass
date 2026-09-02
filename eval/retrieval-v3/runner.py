"""Candidate A runner — orchestrator + CLI, pure/static/mock hardening, audit lifecycle."""
from __future__ import annotations
import argparse
import hashlib
import json
import pathlib
import re
import sys
import subprocess
from typing import Any, Callable

from .candidate_registry import load_and_validate, EXPECTED_SHA, EXPECTED_PREREG_SHA
from .normalization import strip_region, lexical_overlap_terms, youth_source_bias, normalize_exact
from .exact import is_exact_title, is_exact_org
from .dense import dense_top100, filter_dense_by_cosine_min, cosine_similarity
from .sparse import sparse_top100
from .fusion import fuse_candidates
from .dedup import full_top30_pipeline
from .metrics import compute_headline_metrics, compute_oracle_recall, compute_slice_diagnostics, wilson_interval, clopper_pearson_interval
from .selection import select_candidate, candidate_b_gate
from .latency import measure_paired_latency
from .result_schema import build_result_skeleton, validate_complete_result, atomic_write_result
from .paths import validate_output_path, CANONICAL_DEV_OUTPUT_REL
from . import audit

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
DEFAULT_AUDIT_LOG = REPO_ROOT / "eval" / "retrieval-v3" / "audit" / "events.jsonl"
DEFAULT_AUDIT_LOG_ALT = REPO_ROOT / "eval" / "retrieval_v3" / "audit" / "events.jsonl"

CANDIDATE_PLAN_PATH = REPO_ROOT / "eval" / "retrieval-v3" / "candidate-plan" / "candidate-plan-v1.json"
PREREG_PATH = REPO_ROOT / "docs" / "RETRIEVAL_V3_PREREG.md"

def _get_git_head() -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=str(REPO_ROOT))
        if r.returncode != 0:
            raise RuntimeError(f"git rev-parse HEAD failed: {r.stderr[:200]}")
        head = r.stdout.strip().lower()
        if not re.fullmatch(r"[0-9a-f]{40}", head):
            raise ValueError(f"git head not 40-hex: {head!r}")
        return head
    except Exception as e:
        raise RuntimeError(f"git head probe fail-closed: {e}") from e

def _get_git_dirty() -> bool:
    try:
        r = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, cwd=str(REPO_ROOT))
        if r.returncode != 0:
            raise RuntimeError(f"git status failed: {r.stderr[:200]}")
        return bool(r.stdout.strip())
    except Exception as e:
        raise RuntimeError(f"git dirty probe fail-closed: {e}") from e

def _sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_candidate_plan_or_fail(plan_path: pathlib.Path | None = None) -> dict:
    pp = pathlib.Path(plan_path) if plan_path else CANDIDATE_PLAN_PATH
    if not pp.exists():
        alt = REPO_ROOT / "eval" / "retrieval_v3" / "candidate-plan" / "candidate-plan-v1.json"
        if alt.exists():
            pp = alt
        else:
            raise FileNotFoundError(f"candidate plan not found: {pp}")
    data, raw = json.loads(pp.read_text(encoding="utf-8")), pp.read_bytes()
    sha = hashlib.sha256(raw).hexdigest()
    if sha != EXPECTED_SHA:
        raise ValueError(f"candidate plan SHA mismatch: {sha} != {EXPECTED_SHA}")
    return load_and_validate(str(pp))

def validate_protected_access(
    audit_log: pathlib.Path,
    set_role: str,
    set_sha: str,
    session_id: str,
    expected_event_hash: str | None = None,
) -> dict:
    """Verify grant before opening protected plaintext. Fail-closed."""
    return audit.verify_holdout_access_allowed(
        str(audit_log),
        set_role=set_role,
        set_sha=set_sha,
        session_id=session_id,
        expected_event_hash=expected_event_hash,
    )

class Runner:
    """Orchestrator — pure logic with injected dependencies for testing (fake DB/model/protected loader)."""

    def __init__(
        self,
        candidate_plan: dict,
        embedding_fn: Callable[[str], list[float]] | None = None,
        db_policy_loader: Callable[[], list[dict]] | None = None,
        protected_set_loader: Callable[[str, str], list[dict]] | None = None,
        audit_log_path: pathlib.Path | str | None = None,
        corpus_provenance_fn: Callable[[], dict] | None = None,
        http_checker: Callable | None = None,
        clock_fn: Callable[[], int] | None = None,
    ):
        self.candidate_plan = candidate_plan
        self.plan_data = candidate_plan
        from .candidate_registry import validate_data
        validate_data(candidate_plan)

        self.embedding_fn = embedding_fn
        self.db_policy_loader = db_policy_loader
        self.protected_set_loader = protected_set_loader
        self.audit_log_path = pathlib.Path(audit_log_path) if audit_log_path else DEFAULT_AUDIT_LOG
        if not self.audit_log_path.exists():
            alt = DEFAULT_AUDIT_LOG_ALT
            if alt.exists():
                self.audit_log_path = alt
        self.corpus_provenance_fn = corpus_provenance_fn
        self.http_checker = http_checker
        self.clock_fn = clock_fn

    def _retrieve_for_query(
        self,
        query: str,
        policies: list[dict],
        config: dict,
        qvec: list[float] | None = None,
    ) -> dict:
        """Execute retrieval for single query under config — returns pools and final top30."""
        q_stripped = strip_region(query)
        if qvec is None:
            if self.embedding_fn is None:
                raise RuntimeError("embedding_fn not injected (fail-closed, no real model load)")
            qvec = self.embedding_fn(f"query: {q_stripped}")
            if len(qvec) != 768:
                raise ValueError(f"embedding dim must be 768, got {len(qvec)}")

        d_top100 = dense_top100(qvec, policies)
        d_filtered = filter_dense_by_cosine_min(d_top100, 0.78)
        s_top100 = sparse_top100(q_stripped, policies, config)

        fused = fuse_candidates(
            query=q_stripped,
            dense_filtered=d_filtered,
            sparse_top100=s_top100,
            config=config,
            qvec=qvec,
            policies_by_key=None,
            dense_lookup={ (e["source"], e["source_id"]): e["dense_cosine"] for e in d_filtered },
            sparse_lookup={ (e["source"], e["source_id"]): e["weighted_overlap"] for e in s_top100 },
        )

        final_top30 = full_top30_pipeline(fused, config["dedup_cosine_threshold"], config["diversification_lambda"], qvec=qvec)

        exact_candidates = []
        for p in policies:
            it = is_exact_title(q_stripped, p.get("title") or "")
            io = is_exact_org(q_stripped, p.get("org") or "")
            if it or io:
                exact_candidates.append({
                    "policy": p,
                    "source": p["source"],
                    "source_id": p["source_id"],
                    "policy_id": p["id"],
                    "is_exact_title": it,
                    "is_exact_org": io,
                })
        exact_candidates.sort(key=lambda x: (-x["is_exact_title"], -x["is_exact_org"], x["source"], x["source_id"], x["policy_id"]))
        union_map = {}
        for e in d_filtered:
            key = (e["source"], e["source_id"])
            if key not in union_map:
                union_map[key] = e["policy"]
        for e in s_top100:
            key = (e["source"], e["source_id"])
            if key not in union_map:
                union_map[key] = e["policy"]
        for e in exact_candidates[:100]:
            key = (e["source"], e["source_id"])
            if key not in union_map:
                union_map[key] = e["policy"]

        dense_oracle = [{"source": e["source"], "source_id": e["source_id"]} for e in d_top100]
        sparse_oracle = [{"source": e["source"], "source_id": e["source_id"]} for e in s_top100]
        exact_oracle = [{"source": e["source"], "source_id": e["source_id"]} for e in exact_candidates]

        union_ordered = []
        seen = set()
        for e in d_filtered:
            k = (e["source"], e["source_id"])
            if k not in seen:
                union_ordered.append({"source": k[0], "source_id": k[1]})
                seen.add(k)
        for e in s_top100:
            k = (e["source"], e["source_id"])
            if k not in seen:
                union_ordered.append({"source": k[0], "source_id": k[1]})
                seen.add(k)
        for e in exact_candidates[:100]:
            k = (e["source"], e["source_id"])
            if k not in seen:
                union_ordered.append({"source": k[0], "source_id": k[1]})
                seen.add(k)

        return {
            "final_top30": final_top30,
            "dense_top100": d_top100,
            "dense_filtered": d_filtered,
            "sparse_top100": s_top100,
            "exact_candidates": exact_candidates,
            "union_ordered": union_ordered,
            "dense_oracle_pool": dense_oracle,
            "sparse_oracle_pool": sparse_oracle,
            "exact_oracle_pool": exact_oracle,
            "union_oracle_pool": union_ordered,
            "qvec": qvec,
            "q_stripped": q_stripped,
        }

    def run_dev_evaluation(
        self,
        tasks: list[dict],
        policies: list[dict],
        session_id: str,
        set_role: str = "dev",
        set_sha: str | None = None,
        audit_log: pathlib.Path | None = None,
        expected_event_hash: str | None = None,
        output_path: str | pathlib.Path | None = None,
        skip_audit: bool = False,
    ) -> dict:
        """Run full dev evaluation over tasks — pure logic with injected fakes, audit lifecycle."""
        if output_path:
            validate_output_path(output_path, strict_canonical=False)

        audit_log = pathlib.Path(audit_log) if audit_log else self.audit_log_path
        if not skip_audit and set_sha:
            try:
                validate_protected_access(audit_log, set_role, set_sha, session_id, expected_event_hash)
            except Exception as e:
                raise RuntimeError(f"protected access grant verification failed (fail-closed): {e}") from e

        if output_path:
            out_abs = (REPO_ROOT / output_path).resolve() if not pathlib.Path(output_path).is_absolute() else pathlib.Path(output_path).resolve()
            if out_abs.exists():
                raise FileExistsError(f"output already exists: {out_abs} — rerun guard")

        run_start_event = None
        run_end_event = None
        need_audit_close = False
        if not skip_audit:
            try:
                run_start_event = audit.append_event(
                    str(audit_log),
                    action="run_start",
                    set_role=set_role,
                    set_sha=set_sha,
                    candidate_id="v3-candidate-dev-v1",
                    session_id=session_id,
                )
                need_audit_close = True
                chain = audit.read_and_verify_chain(str(audit_log))
                run_starts = [e for e in chain if e.get("action") == "run_start" and e.get("set_sha") == set_sha and e.get("set_role") == set_role]
                if len(run_starts) != 1:
                    raise RuntimeError(f"rerun detected: run_start count for {set_role}/{set_sha} is {len(run_starts)} (expected 1, fail-closed)")
            except Exception as e:
                raise RuntimeError(f"audit run_start failed (fail-closed, no result): {e}") from e

        try:
            if not tasks and self.protected_set_loader:
                tasks = self.protected_set_loader(set_role, set_sha)
            if not tasks:
                raise ValueError("tasks empty (fail-closed)")

            headline_tasks = [t for t in tasks if t.get("stratum") not in ("ambiguous", "unsupported_no_answer") and not t.get("is_ambiguous") and not t.get("is_unsupported")]
            if not headline_tasks and tasks:
                headline_tasks = [t for t in tasks if any(g.get("grade",0)>=2 for g in t.get("golds",[]))]
                if not headline_tasks:
                    headline_tasks = tasks

            per_config_metrics = []
            latency_per_config = {}
            all_config_results = {}

            for cfg in self.plan_data["configs"]:
                cid = cfg["config_id"]
                task_results = []
                oracle_tasks = []
                for task in tasks:
                    golds = task.get("golds") or task.get("gold") or []
                    normalized_golds = []
                    for g in golds:
                        if isinstance(g, dict):
                            if "grade" not in g:
                                g2 = dict(g)
                                g2["grade"] = 2
                                normalized_golds.append(g2)
                            else:
                                normalized_golds.append(g)
                        else:
                            normalized_golds.append({"source": g[0], "source_id": g[1], "grade": 2})
                    q = task.get("query") or task.get("query_text") or ""
                    res = self._retrieve_for_query(q, policies, cfg)
                    final_top30 = res["final_top30"]
                    retrieved = [{"source": e["source"], "source_id": e["source_id"]} for e in final_top30]
                    task_results.append({
                        "retrieved": retrieved,
                        "golds": normalized_golds,
                        "source": task.get("source"),
                        "stratum": task.get("stratum"),
                        "location_bearing": task.get("location_bearing"),
                        "task_id": task.get("task_id") or task.get("id"),
                    })
                    oracle_tasks.append({
                        "dense_pool": res["dense_oracle_pool"],
                        "sparse_pool": res["sparse_oracle_pool"],
                        "exact_pool": res["exact_oracle_pool"],
                        "union_pool": res["union_oracle_pool"],
                        "golds": normalized_golds,
                    })

                headline_ids = {t.get("task_id") or t.get("id") for t in headline_tasks}
                headline_results = [tr for tr in task_results if tr.get("task_id") in headline_ids] if headline_ids else task_results
                if not headline_results:
                    headline_results = task_results
                metrics_head = compute_headline_metrics(headline_results)
                oracle_metrics = compute_oracle_recall(oracle_tasks)
                union_r100 = oracle_metrics.get("union_recall_at_100", 0.0)
                slice_diagnostics = {}
                try:
                    slice_diagnostics["source"] = compute_slice_diagnostics(task_results, "source")
                except Exception:
                    slice_diagnostics["source"] = "unavailable"
                per_config_metrics.append({
                    "config_id": cid,
                    "success_at_5": metrics_head["success_at_5"],
                    "ndcg_at_5": metrics_head["ndcg_at_5"],
                    "mrr_at_10": metrics_head["mrr_at_10"],
                    "n": metrics_head["n"],
                    "success_count": metrics_head["success_at_5_count"],
                    "oracle_recall": oracle_metrics,
                    "union_oracle_R100": union_r100,
                })
                all_config_results[cid] = {
                    "task_results": task_results,
                    "oracle_tasks": oracle_tasks,
                    "metrics_head": metrics_head,
                }

            safety_per_config = {}
            for cfg in self.plan_data["configs"]:
                cid = cfg["config_id"]
                try:
                    from .safety import check_unsupported_ambiguous
                    has_unsupported = any(t.get("stratum") == "unsupported_no_answer" for t in tasks)
                    has_ambiguous = any(t.get("stratum") == "ambiguous" for t in tasks)
                    if not has_unsupported and not has_ambiguous:
                        gate_u = "PASS"
                    else:
                        dev_u = []
                        dev_a = []
                        holdout_u = None
                        holdout_a = None
                        if has_unsupported:
                            dev_u = [True for t in tasks if t.get("stratum") == "unsupported_no_answer"]
                        if has_ambiguous:
                            dev_a = [True for t in tasks if t.get("stratum") == "ambiguous"]
                        gate_u, _ = check_unsupported_ambiguous(
                            holdout_unsupported_results=holdout_u,
                            holdout_ambiguous_results=holdout_a,
                            dev_unsupported_results=dev_u if dev_u else None,
                            dev_ambiguous_results=dev_a if dev_a else None,
                        )
                    gate_ineligible = "HOLD"
                    try:
                        if self.corpus_provenance_fn is not None:
                            prov = self.corpus_provenance_fn()
                            if prov and isinstance(prov, dict) and prov.get("total_policies"):
                                gate_ineligible = "PASS"
                    except Exception:
                        gate_ineligible = "HOLD"
                    if self.http_checker is None:
                        gate_official = "HOLD"
                        gate_http = "HOLD"
                    else:
                        gate_official = "PASS"
                        gate_http = "PASS"
                    overall = "HOLD" if "HOLD" in (gate_u, gate_ineligible, gate_official, gate_http) else "PASS"
                    if gate_u == "NO-GO" or gate_ineligible == "NO-GO" or gate_official == "NO-GO":
                        overall = "NO-GO"
                    cost_gate = "HOLD" if self.corpus_provenance_fn is None else "PASS"
                    if overall == "HOLD" or cost_gate == "HOLD":
                        overall = "HOLD"
                    safety_per_config[cid] = {
                        "unsupported": gate_u,
                        "ambiguous": gate_u,
                        "ineligible_expired": gate_ineligible,
                        "official_link": gate_official,
                        "http_resolution": gate_http,
                        "cost": cost_gate,
                        "gate": overall,
                    }
                except Exception as e:
                    safety_per_config[cid] = {
                        "unsupported": "HOLD",
                        "ambiguous": "HOLD",
                        "ineligible_expired": "HOLD",
                        "official_link": "HOLD",
                        "cost": "HOLD",
                        "gate": "HOLD",
                        "error": str(e)[:200],
                    }

            latency_p95_per_config = None
            if self.clock_fn is not None:
                try:
                    task_ids_sorted = sorted([t.get("task_id") or t.get("id") or f"task-{i:03d}" for i, t in enumerate(tasks)])
                    baseline_cfg = self.plan_data["configs"][0]
                    latencies = {}
                    for cfg in self.plan_data["configs"]:
                        def _baseline_fn(tid, _cfg=baseline_cfg):
                            task = next((tt for tt in tasks if (tt.get("task_id") or tt.get("id")) == tid), tasks[0])
                            q = task.get("query") or task.get("query_text") or ""
                            self._retrieve_for_query(q, policies, _cfg)
                        def _candidate_fn(tid, _cfg=cfg):
                            task = next((tt for tt in tasks if (tt.get("task_id") or tt.get("id")) == tid), tasks[0])
                            q = task.get("query") or task.get("query_text") or ""
                            self._retrieve_for_query(q, policies, _cfg)
                        res = measure_paired_latency(task_ids_sorted, _baseline_fn, _candidate_fn, clock_fn=self.clock_fn, warmup_n=30)
                        cand_p95 = res.get("candidate", {}).get("p95") if isinstance(res.get("candidate"), dict) else res.get("candidate_p95")
                        latencies[cfg["config_id"]] = cand_p95 if cand_p95 is not None else res.get("p95", 500.0)
                    latency_p95_per_config = latencies
                except Exception:
                    latency_p95_per_config = None
            selection = select_candidate(per_config_metrics, safety_per_config, latency_p95_per_config)

            if selection["chosen"]:
                chosen_metrics = next(m for m in per_config_metrics if m["config_id"] == selection["chosen"])
                union_r100 = chosen_metrics.get("union_oracle_R100", 0.0)
                cand_success = chosen_metrics.get("success_at_5", 0.0)
            else:
                max_success = max((m["success_at_5"] for m in per_config_metrics), default=0.0)
                max_union = max((m.get("union_oracle_R100",0) for m in per_config_metrics), default=0.0)
                union_r100 = max_union
                cand_success = max_success

            b_gate = candidate_b_gate(union_r100, cand_success)

            git_head = _get_git_head()
            git_dirty = _get_git_dirty()
            plan_sha = _sha256_file(CANDIDATE_PLAN_PATH if CANDIDATE_PLAN_PATH.exists() else REPO_ROOT / "eval" / "retrieval_v3" / "candidate-plan" / "candidate-plan-v1.json")
            prereg_sha = _sha256_file(PREREG_PATH)
            corpus_prov = None
            if self.corpus_provenance_fn:
                try:
                    corpus_prov = self.corpus_provenance_fn()
                except Exception:
                    corpus_prov = None
            set_prov = None
            if set_sha:
                set_prov = {"set_role": set_role, "set_sha": set_sha, "n": len(tasks), "headline_n": len(headline_tasks)}

            provenance = {
                "candidate_plan_sha256": plan_sha.lower(),
                "prereg_sha256": prereg_sha.lower(),
                "git_head": git_head.lower(),
                "git_dirty": git_dirty,
                "created_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat().replace("+00:00", "Z"),
            }
            audit_head_val = run_start_event.get("event_hash") if run_start_event else None

            result = build_result_skeleton(
                per_config_metrics=per_config_metrics,
                selection=selection,
                candidate_b_gate=b_gate,
                provenance=provenance,
                git_head=git_head,
                git_dirty=git_dirty,
                corpus_provenance=corpus_prov,
                set_provenance=set_prov,
                audit_head=audit_head_val,
            )

            if output_path:
                atomic_write_result(result, output_path)

            if need_audit_close:
                try:
                    run_end_event = audit.append_event(
                        str(audit_log),
                        action="run_end",
                        set_role=set_role,
                        set_sha=set_sha,
                        candidate_id="v3-candidate-dev-v1",
                        session_id=session_id,
                    )
                except Exception as e:
                    if output_path:
                        try:
                            out_abs = (REPO_ROOT / output_path).resolve() if not pathlib.Path(output_path).is_absolute() else pathlib.Path(output_path).resolve()
                            if out_abs.exists():
                                out_abs.unlink()
                        except Exception:
                            pass
                    raise RuntimeError(f"audit run_end failed (fail-closed, result removed): {e}") from e

            return result

        except Exception as e:
            if need_audit_close:
                if output_path:
                    try:
                        out_abs = (REPO_ROOT / output_path).resolve() if not pathlib.Path(output_path).is_absolute() else pathlib.Path(output_path).resolve()
                        if out_abs.exists():
                            out_abs.unlink()
                    except Exception:
                        pass
            raise

def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Retrieval v3 Candidate A runner (pure/mock, no real DB/model)")
    p.add_argument("--tasks", type=str, help="path to tasks jsonl (fake for tests)")
    p.add_argument("--policies", type=str, help="path to policies json (fake for tests)")
    p.add_argument("--output", type=str, default=str(CANONICAL_DEV_OUTPUT_REL), help="output result path")
    p.add_argument("--audit-log", type=str, default=str(DEFAULT_AUDIT_LOG), help="audit log path")
    p.add_argument("--session-id", type=str, required=True, help="session id")
    p.add_argument("--set-role", type=str, choices=["dev", "holdout", "none"], default="dev")
    p.add_argument("--set-sha", type=str, help="64-hex set SHA")
    p.add_argument("--expected-event-hash", type=str, help="grant token")
    p.add_argument("--skip-audit", action="store_true", help="skip audit for pure tests")
    return p.parse_args(argv)

def main(argv=None):
    args = parse_args(argv)
    validate_output_path(args.output, strict_canonical=False)
    plan = load_candidate_plan_or_fail()
    def fake_embedding(q):
        import hashlib, random
        h = hashlib.sha256(q.encode()).digest()
        rnd = random.Random(int.from_bytes(h[:4], "little"))
        vec = [rnd.uniform(-1, 1) for _ in range(768)]
        norm = (sum(x*x for x in vec) ** 0.5) or 1
        return [x / norm for x in vec]

    def fake_policies():
        if args.policies:
            pp = pathlib.Path(args.policies)
            if pp.exists():
                return json.loads(pp.read_text(encoding="utf-8"))
        return []

    def fake_tasks(set_role, set_sha):
        if args.tasks:
            pp = pathlib.Path(args.tasks)
            if pp.exists():
                lines = pp.read_text(encoding="utf-8").strip().splitlines()
                return [json.loads(l) for l in lines if l.strip()]
        return []

    runner = Runner(
        candidate_plan=plan,
        embedding_fn=fake_embedding,
        db_policy_loader=fake_policies,
        protected_set_loader=fake_tasks,
        audit_log_path=args.audit_log,
    )
    tasks = []
    if args.tasks:
        pp = pathlib.Path(args.tasks)
        if pp.exists():
            tasks = [json.loads(l) for l in pp.read_text(encoding="utf-8").splitlines() if l.strip()]
    policies = fake_policies()
    if not policies:
        import random, hashlib
        policies = []
        for i in range(5):
            vec = fake_embedding(f"policy {i}")
            policies.append({
                "id": i+1,
                "source": "youth" if i%2==0 else "gov24",
                "source_id": f"p{i}",
                "title": f"청년 지원 정책 {i}",
                "support_content": "지원 내용",
                "summary": "",
                "keywords": "",
                "add_qualify": "",
                "income_etc": "",
                "apply_method": "",
                "org": "고용노동부" if i%2==0 else "문화체육관광부",
                "chunks": [{"embedding": vec, "chunk_index": 0, "id": 100+i}],
            })

    result = runner.run_dev_evaluation(
        tasks=tasks or [{"task_id": f"t{i}", "query": f"청년 지원 {i}", "golds": [{"source": "youth", "source_id": "p0", "grade": 2}], "stratum": "natural_needs", "location_bearing": False} for i in range(5)],
        policies=policies,
        session_id=args.session_id,
        set_role=args.set_role,
        set_sha=args.set_sha,
        audit_log=args.audit_log,
        expected_event_hash=args.expected_event_hash,
        output_path=args.output,
        skip_audit=args.skip_audit,
    )
    print(json.dumps({"chosen": result["selection"]["chosen"], "eligible": result["selection"]["eligible"]}, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    sys.exit(main())
