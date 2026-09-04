"""D-065 launch-orchestrator tests — pure/static/mock only (no protected bytes).

No DB/model/embedding/HTTP/latency execution, no protected dev/holdout
plaintext, no audit append, no result write. All DB/session/runner surfaces
are injected fakes; frozen-file checks use the real non-protected repo docs
or tmp copies of them (never the materialized protected evalset content).
"""

import ast
import hashlib
import inspect
import pathlib
import shutil
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from retrieval_v3.launch import (
    COST_V1_REL,
    FROZEN_COST_V1_SHA,
    FROZEN_LINK_V2_SHA,
    FROZEN_PLAN_SHA,
    FROZEN_PREREG_SHA,
    LINK_V2_REL,
    PLAN_ALT,
    PLAN_REL,
    PREREG_REL,
    launch_canonical_dev,
    launch_canonical_dev_real,
    preflight_canonical_launch,
    validate_launch_args,
    verify_frozen_files,
)

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
GOOD_SHA = "a" * 64
OTHER_SHA = "b" * 64


def _good_kwargs(**over):
    kw = dict(
        session_id="s1",
        set_role="dev",
        set_sha=GOOD_SHA,
        materialized_path="authorized/dev-evalset.jsonl",
        evalset_base="authorized",
        output_path="eval/retrieval-v3/results/v3-candidate-dev-result.json",
        audit_log="nonexistent-audit-events.jsonl",
    )
    kw.update(over)
    return kw


def _no_side_effect_reader(events):
    calls = []

    def _reader(_path):
        calls.append(_path)
        return list(events)

    _reader.calls = calls
    return _reader


def _false_exists():
    calls = []

    def _fn(_path):
        calls.append(_path)
        return False

    _fn.calls = calls
    return _fn


# ---- frozen pins ----

def test_frozen_files_real_repo_pass():
    out = verify_frozen_files()
    assert out["shas"]["candidate-plan-v4"] == FROZEN_PLAN_SHA.lower()
    assert out["plan"]["plan_id"] == "retrieval-v3-candidate-plan-v4"
    assert len(out["plan"]["configs"]) == 18


def test_frozen_file_drift_fails_closed(tmp_path):
    base = tmp_path / "repo"
    for rel in (PREREG_REL, LINK_V2_REL, COST_V1_REL, PLAN_REL):
        dest = base / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / rel, dest)
    cases = [
        (PREREG_REL, FROZEN_PREREG_SHA),
        (LINK_V2_REL, FROZEN_LINK_V2_SHA),
        (COST_V1_REL, FROZEN_COST_V1_SHA),
        (PLAN_REL, FROZEN_PLAN_SHA),
    ]
    for rel, _pin in cases:
        target = base / rel
        raw = target.read_bytes()
        target.write_bytes(raw + b"\n# drift")
        with pytest.raises(ValueError, match="SHA mismatch"):
            verify_frozen_files(base)
        target.write_bytes(raw)


def test_missing_frozen_file_fails_closed(tmp_path):
    base = tmp_path / "repo"
    for rel in (PREREG_REL, LINK_V2_REL, COST_V1_REL, PLAN_REL):
        dest = base / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / rel, dest)
    (base / COST_V1_REL).unlink()
    with pytest.raises(FileNotFoundError):
        verify_frozen_files(base)


# ---- arg shape ----

def test_arg_shape_rejects_non_dev_bad_ids_and_paths():
    with pytest.raises(ValueError, match="dev only"):
        validate_launch_args(**_good_kwargs(set_role="holdout"))
    with pytest.raises(ValueError, match="64-hex"):
        validate_launch_args(**_good_kwargs(set_sha="0" * 63))
    with pytest.raises(ValueError, match="session_id"):
        validate_launch_args(**_good_kwargs(session_id="  "))
    with pytest.raises(ValueError, match="materialized_path"):
        validate_launch_args(**_good_kwargs(materialized_path="  "))
    with pytest.raises(ValueError, match="evalset_base"):
        validate_launch_args(**_good_kwargs(evalset_base=""))
    with pytest.raises(ValueError, match="canonical"):
        validate_launch_args(**_good_kwargs(output_path="eval/other/result.json"))
    with pytest.raises(ValueError):
        validate_launch_args(**_good_kwargs(output_path="../outside/result.json"))


def test_signature_structurally_forbids_fakes():
    import retrieval_v3.launch as _L
    for fn in (launch_canonical_dev, preflight_canonical_launch, _L.launch_canonical_dev_real, validate_launch_args):
        params = set(inspect.signature(fn).parameters)
        assert "tasks" not in params and "policies" not in params and "skip_audit" not in params
        assert "expected_event_hash" not in params, "HOLD repair: launcher accepts no external token"
    params = set(inspect.signature(launch_canonical_dev).parameters)
    assert {"session_factory", "adapter_builder", "runner_factory"} <= params
    assert callable(launch_canonical_dev_real)


# ---- preflight: audit one-shot + output + no protected IO ----

def test_one_shot_prior_run_start_rejected_and_other_sha_passes():
    same = {"action": "run_start", "set_role": "dev", "set_sha": GOOD_SHA}
    with pytest.raises(RuntimeError, match="rerun detected"):
        preflight_canonical_launch(
            **_good_kwargs(), audit_reader=_no_side_effect_reader([same]), output_exists_fn=_false_exists()
        )
    ok = preflight_canonical_launch(
        **_good_kwargs(), audit_reader=_no_side_effect_reader(
            [{"action": "run_start", "set_role": "dev", "set_sha": OTHER_SHA}]
        ), output_exists_fn=_false_exists()
    )
    assert ok["audit_events"] == 1


def test_tampered_chain_fails_closed():
    def _bad(_path):
        raise ValueError("tamper")

    with pytest.raises(RuntimeError, match="audit chain unreadable"):
        preflight_canonical_launch(**_good_kwargs(), audit_reader=_bad, output_exists_fn=_false_exists())


def test_output_exists_preflight_blocks_before_session():
    calls = []

    def _factory():
        calls.append("session")
        raise AssertionError("must not reach session creation")

    with pytest.raises(FileExistsError, match="already exists"):
        launch_canonical_dev(
            **_good_kwargs(),
            audit_reader=_no_side_effect_reader([]),
            output_exists_fn=lambda _p: True,
            session_factory=_factory,
            adapter_builder=lambda *_a: (_ for _ in ()).throw(AssertionError("no build")),
            runner_factory=lambda *_a: (_ for _ in ()).throw(AssertionError("no runner")),
        )
    assert calls == []


def test_preflight_touches_no_protected_bytes(tmp_path):
    sentinel = tmp_path / "no-such-dir" / "dev-evalset.jsonl"
    out = preflight_canonical_launch(
        **_good_kwargs(materialized_path=str(sentinel), evalset_base=str(tmp_path)),
        audit_reader=_no_side_effect_reader([]),
        output_exists_fn=_false_exists(),
    )
    assert out["args"]["set_sha"] == GOOD_SHA
    assert not sentinel.exists()


# ---- ordered launch with fakes ----

class _FakeSession:
    def __init__(self, log):
        self._log = log
        self.is_closed = False
        self.closes = 0

    def close(self):
        self._log.append("close")
        self.closes += 1
        self.is_closed = True


class _FakeRunner:
    def __init__(self, log, result=None, error=None):
        self._log = log
        self._result = {"ok": True} if result is None else result
        self._error = error
        self.seen = None

    def run_dev_evaluation(self, **kw):
        self._log.append("run")
        self.seen = kw
        if self._error is not None:
            raise self._error
        cb = kw.get("on_grant_verified")
        if callable(cb):
            cb()
        return self._result


def _launch_with(log, runner_error=None, adapter_error=None):
    def _factory():
        log.append("session")
        return _FakeSession(log)

    def _builder(session, mat, base):
        log.append("adapters")
        assert session is not None and mat and base
        if adapter_error is not None:
            raise adapter_error
        return {"marker": "adapters"}

    holder = {}
    appended = []

    def _append(_path, **kw):
        appended.append(kw)
        return {"event_hash": "aa" * 32}

    def _runner_factory(adapters, session):
        log.append("runner")
        holder["runner"] = _FakeRunner(log, error=runner_error)
        return holder["runner"]

    result = launch_canonical_dev(
        **_good_kwargs(),
        audit_reader=_no_side_effect_reader([]),
        output_exists_fn=_false_exists(),
        audit_append_fn=_append,
        session_factory=_factory,
        adapter_builder=_builder,
        runner_factory=_runner_factory,
    )
    return result, holder["runner"], appended


def test_ordered_launch_success_closes_exactly_once():
    log = []
    result, runner, appended = _launch_with(log)
    assert result == {"ok": True}
    assert log == ["session", "adapters", "runner", "run", "close"]
    assert runner.seen["expected_event_hash"] == "aa" * 32
    assert [(a["action"], a.get("outcome")) for a in appended] == [("protected_access_start", "success")]
    assert runner.seen["tasks"] == [] and runner.seen["policies"] == []
    assert runner.seen["skip_audit"] is False
    assert runner.seen["set_role"] == "dev" and runner.seen["set_sha"] == GOOD_SHA


def test_adapter_build_failure_closes_once_without_run():
    log = []

    def _factory():
        log.append("session")
        return _FakeSession(log)

    def _builder(_s, _m, _b):
        log.append("adapters")
        raise RuntimeError("build boom")

    def _runner_factory(_a, _s):
        log.append("runner")
        raise AssertionError("must not construct runner")

    with pytest.raises(RuntimeError, match="adapter build failed"):
        launch_canonical_dev(
            **_good_kwargs(),
            audit_reader=_no_side_effect_reader([]),
            output_exists_fn=_false_exists(),
            session_factory=_factory,
            adapter_builder=_builder,
            runner_factory=_runner_factory,
        )
    assert log == ["session", "adapters", "close"]


def test_runner_run_failure_closes_once():
    log = []
    with pytest.raises(RuntimeError, match="boom"):
        _launch_with(log, runner_error=RuntimeError("boom"))
    assert log == ["session", "adapters", "runner", "run", "close"]


def test_session_factory_failure_needs_no_close():
    def _factory():
        raise RuntimeError("connect boom")

    with pytest.raises(RuntimeError, match="session creation failed"):
        launch_canonical_dev(
            **_good_kwargs(),
            audit_reader=_no_side_effect_reader([]),
            output_exists_fn=_false_exists(),
            session_factory=_factory,
            adapter_builder=lambda *_a: (_ for _ in ()).throw(AssertionError("no build")),
            runner_factory=lambda *_a: (_ for _ in ()).throw(AssertionError("no runner")),
        )


def test_session_close_failure_surfaces():
    log = []

    class _BadClose(_FakeSession):
        def close(self):
            log.append("close")
            self.is_closed = True
            raise RuntimeError("close boom")

    def _factory():
        log.append("session")
        return _BadClose(log)

    with pytest.raises(RuntimeError, match="session close failed"):
        launch_canonical_dev(
            **_good_kwargs(),
            audit_reader=_no_side_effect_reader([]),
            output_exists_fn=_false_exists(),
            audit_append_fn=lambda _p, **kw: {"event_hash": "bb" * 32},
            session_factory=_factory,
            adapter_builder=lambda s, m, b: {"marker": "a"},
            runner_factory=lambda a, s: _FakeRunner(log),
        )
    assert log == ["session", "run", "close"]


# ---- static: mirrors + import purity ----

def test_mirrors_identical_and_import_pure():
    hyphen = REPO_ROOT / "eval" / "retrieval-v3" / "launch.py"
    under = REPO_ROOT / "eval" / "retrieval_v3" / "launch.py"
    assert hyphen.exists() and under.exists()
    ha = hashlib.sha256(hyphen.read_bytes()).hexdigest()
    hb = hashlib.sha256(under.read_bytes()).hexdigest()
    assert ha == hb
    tree = ast.parse(hyphen.read_text(encoding="utf-8"))
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                mods.add(node.module.split(".")[0])
    assert mods.isdisjoint({"psycopg2", "sentence_transformers", "requests", "urllib", "socket", "datetime", "time"}), mods
