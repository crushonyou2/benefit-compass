"""D-065 HOLD-repair adversarial tests — temp/synthetic only (no protected bytes).

Covers exactly the Web HOLD findings on 75069eb: launcher-owned grant append,
exact token handoff, pre/post-transfer close ownership, four-event chain,
run-once, env secrecy, token-free CLI, and the runner-CLI supersession claim.
No DB/model/embedding/HTTP/latency execution, no protected dev/holdout
plaintext (all set_sha values are synthetic hex; the loader never succeeds),
no canonical result write, no real audit log append outside temp dirs.
"""

import ast
import inspect
import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import retrieval_v3.launch as L
from retrieval_v3.launch import (
    launch_canonical_dev,
    main,
    parse_launch_args,
    preflight_canonical_launch,
    resolve_database_url,
)

GOOD_SHA = "a" * 64
OTHER_SHA = "c" * 64
SECRET = "postgres://u:S3CR3T-sentinel-xyz@h/db"


def _good_kwargs(**over):
    kw = dict(
        session_id="g1",
        set_role="dev",
        set_sha=GOOD_SHA,
        materialized_path="authorized/dev-evalset.jsonl",
        evalset_base="authorized",
        output_path="eval/retrieval-v3/results/v3-candidate-dev-result.json",
        audit_log="eval/retrieval-v3/audit/events.jsonl",
    )
    kw.update(over)
    return kw


def _reader(events):
    def _fn(_path):
        return list(events)

    return _fn


def _never_exists(_path):
    return False


class _FakeSession:
    def __init__(self, log):
        self._log = log
        self.is_closed = False

    def close(self):
        self._log.append("close")
        self.is_closed = True


class _FakeRunner:
    """Simulates Runner grant contract: may fire callback, may append its own end."""

    def __init__(self, log, append_fn=None, behavior="transfer_and_close", error=None):
        self._log = log
        self._append = append_fn
        self._behavior = behavior
        self._error = error
        self.seen = None
        self.calls = 0

    def run_dev_evaluation(self, **kw):
        self._log.append("run")
        self.calls += 1
        self.seen = kw
        if self._error is not None:
            raise self._error
        cb = kw.get("on_grant_verified")
        if self._behavior in ("transfer_and_close", "transfer_open"):
            assert callable(cb), "runner must receive the ownership-transfer callback"
            cb()
        if self._behavior == "transfer_and_close" and self._append is not None:
            self._append(
                kw.get("audit_log"),
                action="protected_access_end",
                set_role="dev",
                set_sha=kw.get("set_sha"),
                candidate_id="v3-candidate-dev-v1",
                session_id=kw.get("session_id"),
                outcome="success",
            )
        return {"ok": True}


def _launch(log, runner, append_fn, **over):
    kw = _good_kwargs(**over)
    kw.update(
        audit_reader=_reader([]),
        output_exists_fn=_never_exists,
        audit_append_fn=append_fn,
        session_factory=lambda: (log.append("session"), _FakeSession(log))[1],
        adapter_builder=lambda s, m, b: (log.append("adapters"), {"m": 1})[1],
        runner_factory=lambda a, s: (log.append("runner"), runner)[1],
    )
    return launch_canonical_dev(**kw)


def test_preflight_appends_no_grant(monkeypatch):
    def _boom(*a, **k):
        raise AssertionError("preflight must not append audit events")

    monkeypatch.setattr(L.audit, "append_event", _boom)
    out = preflight_canonical_launch(**_good_kwargs(), audit_reader=_reader([]), output_exists_fn=_never_exists)
    assert out["args"]["set_sha"] == GOOD_SHA


def test_grant_append_failure_means_no_run():
    log = []
    runner = _FakeRunner(log)

    def _fail(_path, **kw):
        raise RuntimeError("log unwritable (synthetic)")

    with pytest.raises(RuntimeError, match="grant append failed"):
        _launch(log, runner, _fail)
    assert "run" not in log, "append failure must mean no run"
    assert log.count("close") == 1


def test_exact_token_passed_to_runner():
    log = []
    seen = {}

    def _append(_path, **kw):
        seen[kw["action"]] = kw
        if kw["action"] == "protected_access_start":
            assert kw["outcome"] == "success"
            return {"event_hash": "ab" * 32}
        return {"event_hash": "12" * 32}

    runner = _FakeRunner(log, behavior="transfer_open")
    _launch(log, runner, _append)
    assert runner.calls == 1, "exactly one run"
    assert runner.seen["expected_event_hash"] == "ab" * 32, "exact returned token must reach the runner"
    assert runner.seen["skip_audit"] is False
    assert "on_grant_verified" in runner.seen


def test_pre_transfer_failure_closes_grant_once():
    log = []
    actions = []

    def _append(_path, **kw):
        actions.append((kw["action"], kw.get("outcome")))
        return {"event_hash": "ef" * 32}

    runner = _FakeRunner(log, behavior="silent", error=RuntimeError("boom before verify (synthetic)"))
    with pytest.raises(RuntimeError, match="boom"):
        _launch(log, runner, _append)
    assert actions == [("protected_access_start", "success"), ("protected_access_end", "failure")]
    assert log.count("close") == 1


def test_post_transfer_no_double_close():
    log = []
    actions = []

    def _append(_path, **kw):
        actions.append((kw["action"], kw.get("outcome")))
        return {"event_hash": "ef" * 32}

    runner = _FakeRunner(log, append_fn=_append, behavior="transfer_and_close")
    _launch(log, runner, _append)
    assert actions == [("protected_access_start", "success"), ("protected_access_end", "success")]
    assert sum(1 for a, _ in actions if a == "protected_access_end") == 1, "launcher must never double-close"


def test_success_four_event_chain_run_once_tmp_log(tmp_path, monkeypatch):
    # Confinement-boundary stub (this test proves lifecycle on a temp chain;
    # confinement itself is pinned unstubbed below).
    monkeypatch.setattr(L, "_is_canonical_audit_log_path", lambda p: True)
    from retrieval_v3 import audit as _audit

    log_path = tmp_path / "events.jsonl"
    calls = []

    class _ChainRunner:
        def run_dev_evaluation(self, **kw):
            calls.append(kw)
            kw["on_grant_verified"]()
            _audit.append_event(
                str(log_path), action="run_start", set_role="dev", set_sha=kw["set_sha"],
                candidate_id="v3-candidate-dev-v1", session_id=kw["session_id"],
            )
            _audit.append_event(
                str(log_path), action="run_end", set_role="dev", set_sha=kw["set_sha"],
                candidate_id="v3-candidate-dev-v1", session_id=kw["session_id"], outcome="success",
            )
            _audit.append_event(
                str(log_path), action="protected_access_end", set_role="dev", set_sha=kw["set_sha"],
                candidate_id="v3-candidate-dev-v1", session_id=kw["session_id"], outcome="success",
            )
            return {"ok": True}

    session_log = []
    out = launch_canonical_dev(
        **_good_kwargs(audit_log=str(log_path)),
        audit_reader=_reader([]),
        output_exists_fn=_never_exists,
        audit_append_fn=None,
        session_factory=lambda: (session_log.append("session"), _FakeSession(session_log))[1],
        adapter_builder=lambda s, m, b: {"m": 1},
        runner_factory=lambda a, s: _ChainRunner(),
    )
    assert out == {"ok": True}
    assert len(calls) == 1, "exactly one run"
    chain = _audit.read_and_verify_chain(str(log_path))
    assert [e["action"] for e in chain] == [
        "protected_access_start", "run_start", "run_end", "protected_access_end",
    ]
    assert chain[0]["outcome"] == "success" and chain[-1]["outcome"] == "success"


def test_real_runner_callback_fires_before_loader(tmp_path):
    from retrieval_v3 import audit as _audit
    from retrieval_v3.runner import Runner

    log_path = tmp_path / "events.jsonl"
    sha = OTHER_SHA
    start = _audit.append_event(
        str(log_path), action="protected_access_start", set_role="dev", set_sha=sha,
        candidate_id="v3-candidate-dev-v1", session_id="g2", outcome="success",
    )
    fired = []

    def _boom_loader(_role, _sha):
        raise RuntimeError("loader boom (synthetic)")

    runner = Runner(
        candidate_plan=__import__("retrieval_v3.runner", fromlist=["load_candidate_plan_or_fail"]).load_candidate_plan_or_fail(),
        db_policy_loader=None,
        protected_set_loader=_boom_loader,
        audit_log_path=log_path,
        adapter_kind="real",
        safety_evidence_fn=lambda payload: {"unsupported": {"gate": "HOLD"}, "ambiguous": {"gate": "HOLD"},
            "production_exclusion": {"gate": "HOLD"}, "official_link": {"gate": "HOLD"},
            "http_resolution": {"gate": "HOLD"}, "cost": {"gate": "HOLD"}},
        d003_baseline_fn=lambda *a: {},
        clock_fn=lambda: 1,
        corpus_provenance_fn=lambda: {"total_policies": 1, "snapshot": "synthetic"},
        evaluation_context_exec_fn=lambda sql: "UTC" if sql == "SHOW TimeZone" else "2026-09-04",
    )
    with pytest.raises(RuntimeError, match="loader boom"):
        runner.run_dev_evaluation(
            tasks=[], policies=[], session_id="g2", set_role="dev", set_sha=sha,
            audit_log=log_path, expected_event_hash=start["event_hash"],
            output_path=None, skip_audit=False, on_grant_verified=lambda: fired.append("fired"),
        )
    assert fired == ["fired"], "callback must fire after verify, before loader"
    chain = _audit.read_and_verify_chain(str(log_path))
    assert [e["action"] for e in chain] == ["protected_access_start", "protected_access_end"]
    assert chain[-1]["outcome"] == "failure", "runner owns closure once transferred"
    assert not [e for e in chain if e["action"] == "run_start"], "loader failure precedes run_start"


def test_env_secrecy_and_dotenv_fallback(tmp_path, capsys):
    assert resolve_database_url(env={"DATABASE_URL": SECRET}) == SECRET
    assert capsys.readouterr().out == "" and capsys.readouterr().err == ""
    (tmp_path / "bare").mkdir()
    try:
        resolve_database_url(repo_root=tmp_path / "bare", env={})
        assert False, "missing URL must fail-closed"
    except RuntimeError as e:
        assert SECRET not in str(e) and "S3CR3T" not in str(e)
        assert "unavailable" in str(e).lower()
    dotenv = tmp_path / ".env"
    dotenv.write_text(
        "# comment\nOTHER=1\nexport IGNORED=2\nDATABASE_URL='  " + SECRET + "  '\n",
        encoding="utf-8",
    )
    assert resolve_database_url(repo_root=tmp_path, env={}) == SECRET
    try:
        resolve_database_url(repo_root=tmp_path / "no-such-dir", env={})
        assert False
    except RuntimeError as e:
        assert "S3CR3T" not in str(e)
    (tmp_path / "empty").mkdir()
    try:
        resolve_database_url(repo_root=tmp_path / "empty", env={})
        assert False
    except RuntimeError as e:
        assert "unavailable" in str(e).lower()


def test_cli_needs_no_external_token(monkeypatch, capsys):
    args = parse_launch_args([
        "--session-id", "g3", "--set-sha", GOOD_SHA,
        "--materialized-evalset", "m.jsonl", "--materialized-evalset-base", "b",
    ])
    assert not hasattr(args, "expected_event_hash")
    assert "token" not in vars(args)
    seen = {}

    def _fake_real(**kw):
        seen.update(kw)
        return {"selection": {"chosen": "candidate-a-01", "eligible": ["candidate-a-01"]}}

    monkeypatch.setattr(L, "launch_canonical_dev_real", _fake_real)
    assert main([
        "--session-id", "g3", "--set-sha", GOOD_SHA,
        "--materialized-evalset", "m.jsonl", "--materialized-evalset-base", "b",
    ]) == 0
    assert "expected_event_hash" not in seen, "CLI must not traffic any external token"
    assert seen["session_id"] == "g3" and seen["set_sha"] == GOOD_SHA
    assert json.loads(capsys.readouterr().out)["chosen"] == "candidate-a-01"


def test_hold_findings_closed_statically():
    import retrieval_v3.runner as _R

    src = pathlib.Path(L.__file__).read_text(encoding="utf-8")
    assert src.count("protected_access_start") >= 1, "launcher must append the grant itself"
    assert "def parse_launch_args" in src and "def main(" in src and '__main__' in src
    assert "DATABASE_URL" in src and ".env" in src
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in (
            "validate_launch_args", "preflight_canonical_launch",
            "launch_canonical_dev", "launch_canonical_dev_real",
        ):
            names = [a.arg for a in list(node.args.args) + node.args.kwonlyargs]
            assert "expected_event_hash" not in names, f"{node.name} must take no external token"
    doc = _R.main_canonical_dev.__doc__ or ""
    assert "launch" in doc, "runner CLI supersession claim must be documented"
    assert "do not use for FIRST-dev" in doc


def test_launch_mirrors_identical():
    import hashlib

    hyphen = pathlib.Path(L.__file__)
    under = hyphen.parent.parent / "retrieval_v3" / "launch.py"
    assert hyphen.read_bytes() == under.read_bytes()
    assert hashlib.sha256(hyphen.read_bytes()).hexdigest() == hashlib.sha256(under.read_bytes()).hexdigest()


def test_alternate_audit_rejected_before_session_grant():
    import retrieval_v3.launch as _L

    calls = []

    def _boom_factory():
        calls.append("session")
        raise AssertionError("must not reach session creation")

    def _boom_append(*a, **k):
        calls.append("append")
        raise AssertionError("must not append any grant event")

    bad_logs = [
        "eval/retrieval-v3/audit/alternate-empty.jsonl",
        "eval/retrieval_v3/audit/events.jsonl",
        "eval/other/events.jsonl",
        "../outside/events.jsonl",
        "eval/retrieval-v3/audit/../audit/events.jsonl",
    ]
    for bad in bad_logs:
        with pytest.raises(ValueError, match="ONE audit log"):
            _L.launch_canonical_dev(
                **_good_kwargs(audit_log=bad),
                audit_reader=_reader([]),
                output_exists_fn=_never_exists,
                audit_append_fn=_boom_append,
                session_factory=_boom_factory,
                adapter_builder=lambda *_a: (_ for _ in ()).throw(AssertionError("no build")),
                runner_factory=lambda *_a: (_ for _ in ()).throw(AssertionError("no runner")),
            )
    assert calls == [], "noncanonical audit values must fail before session/grant/append"


def test_canonical_audit_forms_accepted():
    import retrieval_v3.launch as _L

    canonical = [
        "eval/retrieval-v3/audit/events.jsonl",
        "eval\\retrieval-v3\\audit\\events.jsonl",
        str((_L.REPO_ROOT / "eval" / "retrieval-v3" / "audit" / "events.jsonl").resolve()),
        str(_L.DEFAULT_AUDIT_LOG),
    ]
    for good in canonical:
        out = preflight_canonical_launch(
            **_good_kwargs(audit_log=good), audit_reader=_reader([]), output_exists_fn=_never_exists
        )
        assert out["audit_events"] == 0


def test_prior_run_start_not_bypassable_by_switching_logs():
    import retrieval_v3.launch as _L

    prior = {"action": "run_start", "set_role": "dev", "set_sha": GOOD_SHA}
    with pytest.raises(ValueError, match="ONE audit log"):
        _L.launch_canonical_dev(
            **_good_kwargs(audit_log="eval/retrieval-v3/audit/alternate-empty.jsonl"),
            audit_reader=_reader([]),
            output_exists_fn=_never_exists,
            audit_append_fn=lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("no append")),
            session_factory=lambda: (_ for _ in ()).throw(AssertionError("no session")),
            adapter_builder=lambda *_a: (_ for _ in ()).throw(AssertionError("no build")),
            runner_factory=lambda *_a: (_ for _ in ()).throw(AssertionError("no runner")),
        )
    with pytest.raises(RuntimeError, match="rerun detected"):
        preflight_canonical_launch(
            **_good_kwargs(), audit_reader=_reader([prior]), output_exists_fn=_never_exists
        )


def test_cli_audit_option_forwards_and_launch_rejects(monkeypatch, capsys):
    import retrieval_v3.launch as _L

    seen = {}

    def _fake_real(**kw):
        seen.update(kw)
        return {"selection": {"chosen": None, "eligible": []}}

    monkeypatch.setattr(_L, "launch_canonical_dev_real", _fake_real)
    assert main([
        "--session-id", "g4", "--set-sha", GOOD_SHA,
        "--materialized-evalset", "m.jsonl", "--materialized-evalset-base", "b",
        "--audit-log", "eval/retrieval-v3/audit/alternate-empty.jsonl",
    ]) == 0
    assert seen["audit_log"] == "eval/retrieval-v3/audit/alternate-empty.jsonl", "CLI must not silently rewrite"
    calls = []
    with pytest.raises(ValueError, match="ONE audit log"):
        _L.launch_canonical_dev(
            **_good_kwargs(audit_log=seen["audit_log"]),
            audit_reader=_reader([]),
            output_exists_fn=_never_exists,
            audit_append_fn=lambda *_a, **_k: calls.append("append"),
            session_factory=lambda: (calls.append("session"), _FakeSession(calls))[1],
            adapter_builder=lambda *_a: (_ for _ in ()).throw(AssertionError("no build")),
            runner_factory=lambda *_a: (_ for _ in ()).throw(AssertionError("no runner")),
        )
    assert calls == [], "forwarded noncanonical value still fails before session/grant"
    capsys.readouterr()


def test_repo_root_module_command_supported():
    import subprocess

    import retrieval_v3.launch as _L

    proc = subprocess.run(
        [sys.executable, "-m", "eval.retrieval_v3.launch", "--help"],
        cwd=str(_L.REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr[-500:]
    assert "--session-id" in proc.stdout and "--set-sha" in proc.stdout


def test_confinement_pins_statically():
    src = pathlib.Path(L.__file__).read_text(encoding="utf-8")
    assert "CANONICAL_AUDIT_REL" in src and "_is_canonical_audit_log_path" in src
    assert "alternate logs bypass one-shot" in src
    assert "--audit-log" in src, "CLI keeps the option; noncanonical values fail before session/grant"
