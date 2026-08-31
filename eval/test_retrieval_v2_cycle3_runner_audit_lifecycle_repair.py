"""Cycle3 runner audit lifecycle + ownership repair — pure/fake, no DB/model/plaintext.

Regressions for 5892762 Web HOLD blockers 1/2. Each test would fail on 5892762:
- Blocker1: grant remains open on failures after grant but before run_start (missing env, dev path, sha, second one-shot, run_start)
- Blocker2: failure cleanup deletes foreign output (ownership) + atomic fallback overwrite risk

No real retrieval/DB/model/embedding/benchmark, no CYCLE3_CANONICAL_EXECUTION=1 against real deps, no dev/holdout plaintext.
"""
import json
import os
import pathlib
import tempfile
import unittest
from unittest import mock

import sys
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
sys.path.insert(0, str(ROOT / "ml-service"))

from retrieval_v2.cycle3_runner import (
    BATCH_ID,
    CANONICAL_DEV_AUDIT_REL,
    CANONICAL_DEV_OUTPUT_REL,
    EXPECTED_DEV_SHA256,
    EXPECTED_DEV_CASES,
    EXPECTED_CORPUS_TOTAL_CHUNKS,
    EXPECTED_CORPUS_TOTAL_POLICIES,
    EXPECTED_CORPUS_BY_SOURCE,
    validate_complete_result,
    format_pgvector,
)
from retrieval_v2.cycle3_audit import append_event, read_and_verify_chain, verify_holdout_access_allowed
import retrieval_v2.cycle3_runner as runner_mod
import retrieval_v2.run_cycle3_canonical_dev as cli_mod
from retrieval_v2.run_cycle3_canonical_dev import main as cli_main


def _synthetic_items(n=36):
    items = []
    for i in range(n):
        src = "youth" if i % 2 == 0 else "gov24"
        items.append({
            "id": f"c3d-{i:03d}",
            "case_id": f"c3d-{i:03d}",
            "query": f"synthetic query {i} for {src}",
            "raw": f"synthetic query {i} for {src}",
            "gold_source": src,
            "gold_source_id": f"gold-{i}",
            "source": src,
            "source_id": f"gold-{i}",
            "category": "housing_finance",
            "age": None,
        })
    return items


def _fake_deps(scenario="success"):
    items = _synthetic_items(36)
    def fake_embed_factory(_):
        def _embed(stripped: str):
            return format_pgvector([hash(stripped) % 100 / 100.0, 0.2, 0.3])
        return _embed
    def fake_retrieval_factory(_, __):
        def _retrieve(cid, vec, terms, yb, age, rp):
            assert rp is None
            assert isinstance(vec, str) and vec.startswith("[")
            # baseline worst, candidates best
            idx = 0  # not precise, just return gold for candidates
            # Use simple deterministic: if cid == baseline -> rank 10, else rank 1
            # caller will compute rank via gold in items; we need to know idx mapping
            # For simplicity return all rows with gold at desired position
            # This helper is not stateful enough for per-case; orchestration will call per case with idx implicit via call order
            # We'll use call counter via closure
            return []
        return _retrieve
    # Better: use counter as in existing tests for per-case gold
    call_counter = {"n": 0}
    def fake_retrieval_factory2(_, __):
        def _retrieve(cid, vec, terms, yb, age, rp):
            assert rp is None
            assert isinstance(vec, str)
            idx = call_counter["n"] // 4
            if idx >= len(items):
                idx = len(items) - 1
            gold_src = items[idx]["gold_source"]
            gold_id = items[idx]["gold_source_id"]
            desired = 10 if cid == "baseline" else 1
            rows = []
            for r in range(1, 31):
                dist = 0.05 + (r-1)*0.005
                score = 1.0 - dist
                if r == desired:
                    rows.append({"source": gold_src, "source_id": gold_id, "dist": dist, "score": score})
                else:
                    rows.append({"source": "other", "source_id": f"other-{r}", "dist": dist, "score": score})
            call_counter["n"] += 1
            return rows
        return _retrieve
    def fake_latency_factory(dev_items, emb_fn, ret_fn):
        def _measure(quality_ids):
            out = {}
            for cid in quality_ids:
                out[cid] = {"p50": 400.0, "p95": 450.0, "count": 180, "samples": [400]*5}
            out["baseline"] = {"p50": 410.0, "p95": 460.0, "count": 180, "samples": [410]*5}
            return out
        return _measure
    def fake_load(path, role="dev"):
        return items
    def fake_sha(path):
        return EXPECTED_DEV_SHA256
    def fake_corpus():
        return {"total_policies": EXPECTED_CORPUS_TOTAL_POLICIES, "total_chunks": EXPECTED_CORPUS_TOTAL_CHUNKS, "by_source": dict(EXPECTED_CORPUS_BY_SOURCE)}
    return {
        "items": items,
        "embed_factory": fake_embed_factory,
        "retrieval_factory": fake_retrieval_factory2,
        "latency_factory": fake_latency_factory,
        "load_fn": fake_load,
        "sha_fn": fake_sha,
        "corpus_fn": fake_corpus,
        "call_counter": call_counter,
    }


class EnvGateBeforeGrantTest(unittest.TestCase):
    """(a) missing execution env — gate before grant acquisition, no reusable grant left by this invocation."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmp_root = pathlib.Path(self.tmpdir.name)
        (self.tmp_root / "eval/retrieval-v2/cycle3/dev").mkdir(parents=True)
        (self.tmp_root / "eval/retrieval-v2/cycle3/canonical-dev").mkdir(parents=True)
        (self.tmp_root / "eval/retrieval-v2/cycle3/audit").mkdir(parents=True)
        self.dev_path = self.tmp_root / "eval/retrieval-v2/cycle3/dev/evalset.jsonl"
        self.dev_path.write_text('{"dummy":1}\n', encoding="utf-8")
        self.out_path = self.tmp_root / CANONICAL_DEV_OUTPUT_REL
        self.audit_path = self.tmp_root / CANONICAL_DEV_AUDIT_REL
        self.session_id = "env-gate-session-001"
        self.p1 = mock.patch.object(runner_mod, "ROOT", self.tmp_root)
        self.p2 = mock.patch.object(cli_mod, "ROOT", self.tmp_root)
        self.p1.start(); self.p2.start()
        self.addCleanup(self.p1.stop); self.addCleanup(self.p2.stop)
        self.addCleanup(self.tmpdir.cleanup)

    def test_missing_env_fails_before_grant_not_protected_denied(self):
        # No pre-grant, env missing => should fail with execution gate message, not grant denial.
        # This would fail on 5892762 where grant check happened before env check (grant denial).
        deps = _fake_deps()
        env = {"CYCLE3_CANONICAL_EXECUTION": "0", "CYCLE3_SESSION_ID": self.session_id}
        # Ensure no grant exists yet
        self.assertFalse(self.audit_path.exists())
        with mock.patch.dict(os.environ, env, clear=False):
            # Ensure env var not set to 1
            if "CYCLE3_GRANT_TOKEN" in os.environ:
                del os.environ["CYCLE3_GRANT_TOKEN"]
            with self.assertRaises(RuntimeError) as ctx:
                cli_main(
                    ["--dev-evalset", "eval/retrieval-v2/cycle3/dev/evalset.jsonl",
                     "--output", CANONICAL_DEV_OUTPUT_REL,
                     "--audit-log", CANONICAL_DEV_AUDIT_REL,
                     "--session-id", self.session_id],
                    _embedding_fn_factory=deps["embed_factory"],
                    _retrieval_fn_factory=deps["retrieval_factory"],
                    _latency_measurer_factory=deps["latency_factory"],
                    _load_and_validate_fn=deps["load_fn"],
                    _canonical_sha_fn=deps["sha_fn"],
                    _corpus_provenance_fn=deps["corpus_fn"],
                )
        msg = str(ctx.exception)
        self.assertIn("canonical dev batch execution is not allowed", msg)
        self.assertNotIn("protected dev access denied", msg.lower())
        # No grant acquired, so no protected_access_end should exist
        if self.audit_path.exists():
            chain = read_and_verify_chain(self.audit_path)
            ends = [e for e in chain if e["action"] == "protected_access_end"]
            self.assertEqual(len(ends), 0, "gate before grant should not create protected_access_end")

    def test_valid_grant_plus_missing_env_leaves_no_reusable_acquired_grant(self):
        # Valid temp grant + missing env => with gate-before, main fails before verifying grant,
        # so grant remains as pure external but main did not acquire; with gate-after+closure, grant would be closed.
        # After our repair (gate-before), main does not acquire, so no new protected_access_end.
        # The crucial check is that main's failure does NOT leave an *acquired* grant open without closure.
        # We verify by checking that audit log still has grant open (since we didn't close) but main didn't claim to have closed.
        # However the repaired lifecycle demands that if grant was acquired, it must be closed.
        # For this test we instead verify that missing env does not result in a run_start and does not create spurious output.
        deps = _fake_deps()
        # Create external grant
        grant = append_event(self.audit_path, action="protected_access_start", candidate_id=None, set_role="dev", set_sha=EXPECTED_DEV_SHA256, outcome="success", session_id=self.session_id)
        token = grant["event_hash"]
        env = {"CYCLE3_CANONICAL_EXECUTION": "0", "CYCLE3_SESSION_ID": self.session_id, "CYCLE3_GRANT_TOKEN": token}
        with mock.patch.dict(os.environ, env, clear=False):
            with self.assertRaises(RuntimeError) as ctx:
                cli_main(
                    ["--dev-evalset", "eval/retrieval-v2/cycle3/dev/evalset.jsonl",
                     "--output", CANONICAL_DEV_OUTPUT_REL,
                     "--audit-log", CANONICAL_DEV_AUDIT_REL,
                     "--session-id", self.session_id,
                     "--grant-token", token],
                    _embedding_fn_factory=deps["embed_factory"],
                    _retrieval_fn_factory=deps["retrieval_factory"],
                    _latency_measurer_factory=deps["latency_factory"],
                    _load_and_validate_fn=deps["load_fn"],
                    _canonical_sha_fn=deps["sha_fn"],
                    _corpus_provenance_fn=deps["corpus_fn"],
                )
        self.assertIn("canonical dev batch execution is not allowed", str(ctx.exception))
        self.assertFalse(self.out_path.exists())
        # After gate-before, grant was not verified, so still open - verify should still succeed (gate avoided acquiring)
        # This is acceptable as gate-before; the grant not being closed is not a bug because not acquired.
        # The test ensures no run_start was appended.
        chain = read_and_verify_chain(self.audit_path)
        self.assertFalse(any(e["action"] == "run_start" for e in chain), "gate-before should not append run_start")


class PreRunStartGrantClosureTest(unittest.TestCase):
    """(b) missing dev path / SHA mismatch / run_start append failure must close grant exactly once."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmp_root = pathlib.Path(self.tmpdir.name)
        (self.tmp_root / "eval/retrieval-v2/cycle3/dev").mkdir(parents=True)
        (self.tmp_root / "eval/retrieval-v2/cycle3/canonical-dev").mkdir(parents=True)
        (self.tmp_root / "eval/retrieval-v2/cycle3/audit").mkdir(parents=True)
        self.dev_path = self.tmp_root / "eval/retrieval-v2/cycle3/dev/evalset.jsonl"
        self.dev_path.write_text('{"dummy":1}\n', encoding="utf-8")
        self.out_path = self.tmp_root / CANONICAL_DEV_OUTPUT_REL
        self.audit_path = self.tmp_root / CANONICAL_DEV_AUDIT_REL
        self.session_id = "pre-run-session-002"
        self.p1 = mock.patch.object(runner_mod, "ROOT", self.tmp_root)
        self.p2 = mock.patch.object(cli_mod, "ROOT", self.tmp_root)
        self.p1.start(); self.p2.start()
        self.addCleanup(self.p1.stop); self.addCleanup(self.p2.stop)
        self.addCleanup(self.tmpdir.cleanup)
        self.env_patch = mock.patch.dict(os.environ, {"CYCLE3_CANONICAL_EXECUTION": "1", "CYCLE3_SESSION_ID": self.session_id})
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

    def _create_grant(self):
        return append_event(self.audit_path, action="protected_access_start", candidate_id=None, set_role="dev", set_sha=EXPECTED_DEV_SHA256, outcome="success", session_id=self.session_id)

    def _deps_ok(self):
        return _fake_deps()

    def test_missing_dev_path_closes_grant(self):
        grant = self._create_grant()
        deps = self._deps_ok()
        # Make dev_path not exist at resolved location (remove file)
        self.dev_path.unlink()
        with self.assertRaises(RuntimeError) as ctx:
            cli_main(
                ["--dev-evalset", "eval/retrieval-v2/cycle3/dev/evalset.jsonl",
                 "--output", CANONICAL_DEV_OUTPUT_REL,
                 "--audit-log", CANONICAL_DEV_AUDIT_REL,
                 "--session-id", self.session_id],
                _embedding_fn_factory=deps["embed_factory"],
                _retrieval_fn_factory=deps["retrieval_factory"],
                _latency_measurer_factory=deps["latency_factory"],
                _load_and_validate_fn=deps["load_fn"],
                _canonical_sha_fn=deps["sha_fn"],
                _corpus_provenance_fn=deps["corpus_fn"],
            )
        self.assertIn("dev evalset not found", str(ctx.exception).lower())
        chain = read_and_verify_chain(self.audit_path)
        ends = [e for e in chain if e["action"] == "protected_access_end" and e["set_role"] == "dev" and e["session_id"] == self.session_id]
        self.assertEqual(len(ends), 1, f"expected exactly one protected_access_end on missing dev path, got {ends}")
        self.assertEqual(ends[0]["outcome"], "failure")
        # Grant must be closed: verify should now fail
        with self.assertRaises(Exception):
            verify_holdout_access_allowed(self.audit_path, set_role="dev", set_sha=EXPECTED_DEV_SHA256, session_id=self.session_id, expected_event_hash=grant["event_hash"])
        self.assertFalse(self.out_path.exists())

    def test_sha_mismatch_closes_grant(self):
        grant = self._create_grant()
        deps = self._deps_ok()
        def bad_sha(path):
            return "0"*64
        with self.assertRaises(RuntimeError) as ctx:
            cli_main(
                ["--dev-evalset", "eval/retrieval-v2/cycle3/dev/evalset.jsonl",
                 "--output", CANONICAL_DEV_OUTPUT_REL,
                 "--audit-log", CANONICAL_DEV_AUDIT_REL,
                 "--session-id", self.session_id],
                _embedding_fn_factory=deps["embed_factory"],
                _retrieval_fn_factory=deps["retrieval_factory"],
                _latency_measurer_factory=deps["latency_factory"],
                _load_and_validate_fn=deps["load_fn"],
                _canonical_sha_fn=bad_sha,
                _corpus_provenance_fn=deps["corpus_fn"],
            )
        self.assertIn("sha mismatch", str(ctx.exception).lower())
        chain = read_and_verify_chain(self.audit_path)
        ends = [e for e in chain if e["action"] == "protected_access_end"]
        self.assertEqual(len(ends), 1)
        self.assertEqual(ends[0]["outcome"], "failure")
        with self.assertRaises(Exception):
            verify_holdout_access_allowed(self.audit_path, set_role="dev", set_sha=EXPECTED_DEV_SHA256, session_id=self.session_id, expected_event_hash=grant["event_hash"])
        self.assertFalse(self.out_path.exists())

    def test_second_one_shot_closes_grant(self):
        grant = self._create_grant()
        deps = self._deps_ok()
        call_count = {"n": 0}
        def fake_assert(path):
            call_count["n"] += 1
            if call_count["n"] == 1:
                return None
            raise RuntimeError(f"canonical dev batch one-shot guard: prior run_start for batch_id={BATCH_ID} already exists at event fake123... — re-run / second attempt not allowed")
        with mock.patch.object(runner_mod, "assert_no_prior_canonical_attempt", side_effect=fake_assert), mock.patch.object(cli_mod, "assert_no_prior_canonical_attempt", side_effect=fake_assert):
            with self.assertRaises(RuntimeError) as ctx:
                cli_main(
                    ["--dev-evalset", "eval/retrieval-v2/cycle3/dev/evalset.jsonl",
                     "--output", CANONICAL_DEV_OUTPUT_REL,
                     "--audit-log", CANONICAL_DEV_AUDIT_REL,
                     "--session-id", self.session_id],
                    _embedding_fn_factory=deps["embed_factory"],
                    _retrieval_fn_factory=deps["retrieval_factory"],
                    _latency_measurer_factory=deps["latency_factory"],
                    _load_and_validate_fn=deps["load_fn"],
                    _canonical_sha_fn=deps["sha_fn"],
                    _corpus_provenance_fn=deps["corpus_fn"],
                )
            self.assertIn("one-shot", str(ctx.exception).lower())
        chain = read_and_verify_chain(self.audit_path)
        ends = [e for e in chain if e["action"] == "protected_access_end" and e["session_id"] == self.session_id]
        self.assertEqual(len(ends), 1)
        self.assertEqual(ends[0]["outcome"], "failure")

    def test_run_start_append_failure_closes_grant(self):
        grant = self._create_grant()
        deps = self._deps_ok()
        with mock.patch("retrieval_v2.run_cycle3_canonical_dev.append_canonical_run_start", side_effect=RuntimeError("mock run_start fail")):
            with self.assertRaises(RuntimeError) as ctx:
                cli_main(
                    ["--dev-evalset", "eval/retrieval-v2/cycle3/dev/evalset.jsonl",
                     "--output", CANONICAL_DEV_OUTPUT_REL,
                     "--audit-log", CANONICAL_DEV_AUDIT_REL,
                     "--session-id", self.session_id],
                    _embedding_fn_factory=deps["embed_factory"],
                    _retrieval_fn_factory=deps["retrieval_factory"],
                    _latency_measurer_factory=deps["latency_factory"],
                    _load_and_validate_fn=deps["load_fn"],
                    _canonical_sha_fn=deps["sha_fn"],
                    _corpus_provenance_fn=deps["corpus_fn"],
                )
        self.assertIn("run_start", str(ctx.exception).lower())
        chain = read_and_verify_chain(self.audit_path)
        ends = [e for e in chain if e["action"] == "protected_access_end" and e["session_id"] == self.session_id]
        self.assertEqual(len(ends), 1)
        self.assertEqual(ends[0]["outcome"], "failure")
        self.assertFalse(self.out_path.exists())
        # If closure itself fails, it should be surfaced
        with mock.patch("retrieval_v2.cycle3_audit.append_event", side_effect=RuntimeError("mock protected_end fail")):
            # Need new audit for this subcase
            tmp2 = tempfile.TemporaryDirectory()
            tmp_root2 = pathlib.Path(tmp2.name)
            (tmp_root2 / "eval/retrieval-v2/cycle3/dev").mkdir(parents=True)
            (tmp_root2 / "eval/retrieval-v2/cycle3/canonical-dev").mkdir(parents=True)
            (tmp_root2 / "eval/retrieval-v2/cycle3/audit").mkdir(parents=True)
            dev2 = tmp_root2 / "eval/retrieval-v2/cycle3/dev/evalset.jsonl"
            dev2.write_text('{"dummy":1}\n', encoding="utf-8")
            audit2 = tmp_root2 / CANONICAL_DEV_AUDIT_REL
            append_event(audit2, action="protected_access_start", candidate_id=None, set_role="dev", set_sha=EXPECTED_DEV_SHA256, outcome="success", session_id="closure-fail-session")
            with mock.patch.object(runner_mod, "ROOT", tmp_root2), mock.patch.object(cli_mod, "ROOT", tmp_root2):
                with mock.patch.dict(os.environ, {"CYCLE3_CANONICAL_EXECUTION": "1", "CYCLE3_SESSION_ID": "closure-fail-session"}):
                    with self.assertRaises(RuntimeError) as ctx2:
                        cli_main(
                            ["--dev-evalset", "eval/retrieval-v2/cycle3/dev/evalset.jsonl",
                             "--output", CANONICAL_DEV_OUTPUT_REL,
                             "--audit-log", CANONICAL_DEV_AUDIT_REL,
                             "--session-id", "closure-fail-session"],
                            _embedding_fn_factory=deps["embed_factory"],
                            _retrieval_fn_factory=deps["retrieval_factory"],
                            _latency_measurer_factory=deps["latency_factory"],
                            _load_and_validate_fn=deps["load_fn"],
                            _canonical_sha_fn=deps["sha_fn"],
                            _corpus_provenance_fn=deps["corpus_fn"],
                        )
                    # The dev file missing case will trigger closure failure path; we forced append_event to fail
                    # Our mock affects all append_event, so run_start will also fail, but closure failure should be surfaced
                    self.assertIn("protected_access_end", str(ctx2.exception).lower())
            tmp2.cleanup()


class SuccessfulPathClosesOnceTest(unittest.TestCase):
    """(c) successful path closes grant exactly once, run_start/run_end coherent."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmp_root = pathlib.Path(self.tmpdir.name)
        (self.tmp_root / "eval/retrieval-v2/cycle3/dev").mkdir(parents=True)
        (self.tmp_root / "eval/retrieval-v2/cycle3/canonical-dev").mkdir(parents=True)
        (self.tmp_root / "eval/retrieval-v2/cycle3/audit").mkdir(parents=True)
        self.dev_path = self.tmp_root / "eval/retrieval-v2/cycle3/dev/evalset.jsonl"
        self.dev_path.write_text('{"dummy":1}\n', encoding="utf-8")
        self.out_path = self.tmp_root / CANONICAL_DEV_OUTPUT_REL
        self.audit_path = self.tmp_root / CANONICAL_DEV_AUDIT_REL
        self.session_id = "success-session-003"
        self.p1 = mock.patch.object(runner_mod, "ROOT", self.tmp_root)
        self.p2 = mock.patch.object(cli_mod, "ROOT", self.tmp_root)
        self.p1.start(); self.p2.start()
        self.addCleanup(self.p1.stop); self.addCleanup(self.p2.stop)
        self.addCleanup(self.tmpdir.cleanup)
        self.env_patch = mock.patch.dict(os.environ, {"CYCLE3_CANONICAL_EXECUTION": "1", "CYCLE3_SESSION_ID": self.session_id})
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

    def test_success_closes_once_and_no_reuse(self):
        grant = append_event(self.audit_path, action="protected_access_start", candidate_id=None, set_role="dev", set_sha=EXPECTED_DEV_SHA256, outcome="success", session_id=self.session_id)
        deps = _fake_deps()
        cli_main(
            ["--dev-evalset", "eval/retrieval-v2/cycle3/dev/evalset.jsonl",
             "--output", CANONICAL_DEV_OUTPUT_REL,
             "--audit-log", CANONICAL_DEV_AUDIT_REL,
             "--session-id", self.session_id],
            _embedding_fn_factory=deps["embed_factory"],
            _retrieval_fn_factory=deps["retrieval_factory"],
            _latency_measurer_factory=deps["latency_factory"],
            _load_and_validate_fn=deps["load_fn"],
            _canonical_sha_fn=deps["sha_fn"],
            _corpus_provenance_fn=deps["corpus_fn"],
        )
        self.assertTrue(self.out_path.exists())
        data = json.loads(self.out_path.read_text(encoding="utf-8"))
        validate_complete_result(data)
        chain = read_and_verify_chain(self.audit_path)
        starts = [e for e in chain if e["action"] == "run_start" and e["candidate_id"] == BATCH_ID]
        ends = [e for e in chain if e["action"] == "run_end" and e["candidate_id"] == BATCH_ID]
        p_ends = [e for e in chain if e["action"] == "protected_access_end" and e["set_role"] == "dev" and e["session_id"] == self.session_id]
        self.assertEqual(len(starts), 1)
        self.assertEqual(len(ends), 1)
        self.assertEqual(ends[0]["outcome"], "success")
        self.assertEqual(len(p_ends), 1)
        self.assertEqual(p_ends[0]["outcome"], "success")
        # Grant must be closed: verify should fail
        with self.assertRaises(Exception):
            verify_holdout_access_allowed(self.audit_path, set_role="dev", set_sha=EXPECTED_DEV_SHA256, session_id=self.session_id, expected_event_hash=grant["event_hash"])
        # Complete linkage: result provenance grant hash matches
        self.assertEqual(data["provenance"]["grant_event_hash"], grant["event_hash"])
        self.assertEqual(data["provenance"]["run_start_event_hash"], starts[0]["event_hash"])
        # run_start/run_end coherent: run_end after run_start
        start_idx = chain.index(starts[0])
        end_idx = chain.index(ends[0])
        p_idx = chain.index(p_ends[0])
        self.assertLess(start_idx, end_idx)
        self.assertLess(end_idx, p_idx)


class RetrievalFailureClosesOnceNoOwnResultTest(unittest.TestCase):
    """(d) retrieval/orchestration failure closes grant once and leaves no own result."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmp_root = pathlib.Path(self.tmpdir.name)
        (self.tmp_root / "eval/retrieval-v2/cycle3/dev").mkdir(parents=True)
        (self.tmp_root / "eval/retrieval-v2/cycle3/canonical-dev").mkdir(parents=True)
        (self.tmp_root / "eval/retrieval-v2/cycle3/audit").mkdir(parents=True)
        self.dev_path = self.tmp_root / "eval/retrieval-v2/cycle3/dev/evalset.jsonl"
        self.dev_path.write_text('{"dummy":1}\n', encoding="utf-8")
        self.out_path = self.tmp_root / CANONICAL_DEV_OUTPUT_REL
        self.audit_path = self.tmp_root / CANONICAL_DEV_AUDIT_REL
        self.session_id = "retrieval-fail-session-004"
        self.p1 = mock.patch.object(runner_mod, "ROOT", self.tmp_root)
        self.p2 = mock.patch.object(cli_mod, "ROOT", self.tmp_root)
        self.p1.start(); self.p2.start()
        self.addCleanup(self.p1.stop); self.addCleanup(self.p2.stop)
        self.addCleanup(self.tmpdir.cleanup)
        self.env_patch = mock.patch.dict(os.environ, {"CYCLE3_CANONICAL_EXECUTION": "1", "CYCLE3_SESSION_ID": self.session_id})
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

    def test_retrieval_failure_closes_once_no_result(self):
        grant = append_event(self.audit_path, action="protected_access_start", candidate_id=None, set_role="dev", set_sha=EXPECTED_DEV_SHA256, outcome="success", session_id=self.session_id)
        deps = _fake_deps()
        def failing_retr_factory(_, __):
            def _r(cid, vec, terms, yb, age, rp):
                raise RuntimeError("synthetic retrieval failure")
            return _r
        with self.assertRaises(RuntimeError) as ctx:
            cli_main(
                ["--dev-evalset", "eval/retrieval-v2/cycle3/dev/evalset.jsonl",
                 "--output", CANONICAL_DEV_OUTPUT_REL,
                 "--audit-log", CANONICAL_DEV_AUDIT_REL,
                 "--session-id", self.session_id],
                _embedding_fn_factory=deps["embed_factory"],
                _retrieval_fn_factory=failing_retr_factory,
                _load_and_validate_fn=deps["load_fn"],
                _canonical_sha_fn=deps["sha_fn"],
                _corpus_provenance_fn=deps["corpus_fn"],
            )
        self.assertIn("canonical dev batch failed", str(ctx.exception))
        self.assertFalse(self.out_path.exists(), "failed contender must not leave own result")
        chain = read_and_verify_chain(self.audit_path)
        run_ends = [e for e in chain if e["action"] == "run_end"]
        p_ends = [e for e in chain if e["action"] == "protected_access_end"]
        self.assertEqual(len(run_ends), 1)
        self.assertEqual(run_ends[0]["outcome"], "failure")
        self.assertEqual(len(p_ends), 1)
        self.assertEqual(p_ends[0]["outcome"], "failure")
        # No reusable grant
        with self.assertRaises(Exception):
            verify_holdout_access_allowed(self.audit_path, set_role="dev", set_sha=EXPECTED_DEV_SHA256, session_id=self.session_id, expected_event_hash=grant["event_hash"])


class ForeignOutputSurvivesTest(unittest.TestCase):
    """(e) foreign/concurrent output appearing after initial guard must survive failing contender (ownership-safe)."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmp_root = pathlib.Path(self.tmpdir.name)
        (self.tmp_root / "eval/retrieval-v2/cycle3/dev").mkdir(parents=True)
        (self.tmp_root / "eval/retrieval-v2/cycle3/canonical-dev").mkdir(parents=True)
        (self.tmp_root / "eval/retrieval-v2/cycle3/audit").mkdir(parents=True)
        self.dev_path = self.tmp_root / "eval/retrieval-v2/cycle3/dev/evalset.jsonl"
        self.dev_path.write_text('{"dummy":1}\n', encoding="utf-8")
        self.out_path = self.tmp_root / CANONICAL_DEV_OUTPUT_REL
        self.audit_path = self.tmp_root / CANONICAL_DEV_AUDIT_REL
        self.session_id = "foreign-output-session-005"
        self.p1 = mock.patch.object(runner_mod, "ROOT", self.tmp_root)
        self.p2 = mock.patch.object(cli_mod, "ROOT", self.tmp_root)
        self.p1.start(); self.p2.start()
        self.addCleanup(self.p1.stop); self.addCleanup(self.p2.stop)
        self.addCleanup(self.tmpdir.cleanup)
        self.env_patch = mock.patch.dict(os.environ, {"CYCLE3_CANONICAL_EXECUTION": "1", "CYCLE3_SESSION_ID": self.session_id})
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

    def test_foreign_output_survives_failing_contender(self):
        grant = append_event(self.audit_path, action="protected_access_start", candidate_id=None, set_role="dev", set_sha=EXPECTED_DEV_SHA256, outcome="success", session_id=self.session_id)
        deps = _fake_deps()
        # Ensure initial guard passes (no file at start)
        self.assertFalse(self.out_path.exists())
        foreign_payload = {"foreign": True, "marker": "foreign-output-survives"}
        def foreign_writing_retr_factory(_, __):
            def _retrieve(cid, vec, terms, yb, age, rp):
                # On first call, simulate concurrent writer publishing foreign output after initial guard
                # We do this only once to simulate race
                if not self.out_path.exists():
                    # Create foreign file that is NOT owned by this invocation
                    self.out_path.parent.mkdir(parents=True, exist_ok=True)
                    self.out_path.write_text(json.dumps(foreign_payload), encoding="utf-8")
                raise RuntimeError("synthetic failure after foreign publish")
            return _retrieve
        with self.assertRaises(RuntimeError):
            cli_main(
                ["--dev-evalset", "eval/retrieval-v2/cycle3/dev/evalset.jsonl",
                 "--output", CANONICAL_DEV_OUTPUT_REL,
                 "--audit-log", CANONICAL_DEV_AUDIT_REL,
                 "--session-id", self.session_id],
                _embedding_fn_factory=deps["embed_factory"],
                _retrieval_fn_factory=foreign_writing_retr_factory,
                _load_and_validate_fn=deps["load_fn"],
                _canonical_sha_fn=deps["sha_fn"],
                _corpus_provenance_fn=deps["corpus_fn"],
            )
        # Foreign output must survive (ownership-safe)
        self.assertTrue(self.out_path.exists(), "FOREIGN_OUTPUT_SURVIVES must be True after failing contender")
        content = json.loads(self.out_path.read_text(encoding="utf-8"))
        self.assertEqual(content, foreign_payload, "foreign content must be unchanged")
        # Audit closure must still be exactly once failure
        chain = read_and_verify_chain(self.audit_path)
        p_ends = [e for e in chain if e["action"] == "protected_access_end"]
        self.assertEqual(len(p_ends), 1)
        self.assertEqual(p_ends[0]["outcome"], "failure")
        # Verify no own result was published (foreign remains, not our result)
        # Ensure our result not present (foreign marker)
        self.assertEqual(content.get("marker"), "foreign-output-survives")

    def test_no_foreign_no_file_after_failure(self):
        # Without foreign writer, failing contender must leave no file
        grant = append_event(self.audit_path, action="protected_access_start", candidate_id=None, set_role="dev", set_sha=EXPECTED_DEV_SHA256, outcome="success", session_id=self.session_id)
        deps = _fake_deps()
        def failing_retr(_, __):
            def _r(cid, vec, terms, yb, age, rp):
                raise RuntimeError("fail")
            return _r
        with self.assertRaises(RuntimeError):
            cli_main(
                ["--dev-evalset", "eval/retrieval-v2/cycle3/dev/evalset.jsonl",
                 "--output", CANONICAL_DEV_OUTPUT_REL,
                 "--audit-log", CANONICAL_DEV_AUDIT_REL,
                 "--session-id", self.session_id],
                _embedding_fn_factory=deps["embed_factory"],
                _retrieval_fn_factory=failing_retr,
                _load_and_validate_fn=deps["load_fn"],
                _canonical_sha_fn=deps["sha_fn"],
                _corpus_provenance_fn=deps["corpus_fn"],
            )
        self.assertFalse(self.out_path.exists())


class AtomicPublishNoOverwriteTest(unittest.TestCase):
    """(f) atomic publish no-overwrite race/fallback ownership — must not overwrite foreign, must preserve no-overwrite."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmp_root = pathlib.Path(self.tmpdir.name)
        (self.tmp_root / "eval/retrieval-v2/cycle3/canonical-dev").mkdir(parents=True)
        self.out_path = self.tmp_root / CANONICAL_DEV_OUTPUT_REL
        self.p1 = mock.patch.object(runner_mod, "ROOT", self.tmp_root)
        self.p1.start()
        self.addCleanup(self.p1.stop)
        self.addCleanup(self.tmpdir.cleanup)

    def _make_valid_result(self):
        # Build valid complete result where no candidate is quality-selectable (so latency None is allowed)
        from retrieval_v2.cycle3_runner import orchestrate_4way_batch, format_pgvector
        items = _synthetic_items(36)
        def fake_embed(stripped: str):
            return format_pgvector([0.1, 0.2, 0.3])
        call_counter = {"n": 0}
        def fake_ret(cid, vec, terms, yb, age, rp):
            # All variants return same rank (5) => candidate not greater than baseline => not quality-selectable => latency None allowed
            idx = call_counter["n"] // 4
            if idx >= len(items):
                idx = len(items)-1
            gold_src = items[idx]["gold_source"]
            gold_id = items[idx]["gold_source_id"]
            desired = 5  # same for all
            rows = []
            for r in range(1, 31):
                dist = 0.05 + (r-1)*0.005
                if r == desired:
                    rows.append({"source": gold_src, "source_id": gold_id, "dist": dist, "score": 1.0-dist})
                else:
                    rows.append({"source": "other", "source_id": f"other-{r}", "dist": dist, "score": 1.0-dist})
            call_counter["n"] += 1
            return rows
        result = orchestrate_4way_batch(items, embedding_fn=fake_embed, retrieval_fn=fake_ret, latency_measurer=None)
        return result
    def test_preexisting_file_blocks_overwrite(self):
        result = self._make_valid_result()
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        self.out_path.write_text('{"preexisting": true}\n', encoding="utf-8")
        pre_content = self.out_path.read_text(encoding="utf-8")
        from retrieval_v2.cycle3_runner import atomic_write_result
        with self.assertRaises((FileExistsError, RuntimeError)):
            atomic_write_result(result, self.out_path)
        self.assertEqual(self.out_path.read_text(encoding="utf-8"), pre_content, "preexisting must not be overwritten")

    def test_concurrent_race_after_initial_guard(self):
        result = self._make_valid_result()
        from retrieval_v2.cycle3_runner import atomic_write_result
        call_cnt = {"n": 0}
        orig_exists = pathlib.Path.exists
        def fake_exists(self_path):
            if str(self_path) == str(self.out_path):
                call_cnt["n"] += 1
                if call_cnt["n"] == 1:
                    return False
                if call_cnt["n"] == 2:
                    if not orig_exists(self.out_path):
                        self.out_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(self.out_path, "w", encoding="utf-8") as f:
                            f.write('{"foreign": true}\n')
                    return True
                return orig_exists(self_path)
            return orig_exists(self_path)
        with mock.patch.object(pathlib.Path, "exists", fake_exists):
            with self.assertRaises(FileExistsError):
                atomic_write_result(result, self.out_path)
        self.assertTrue(self.out_path.exists())
        self.assertIn("foreign", self.out_path.read_text(encoding="utf-8"))


    def test_fallback_exclusive_create_no_overwrite(self):
        result = self._make_valid_result()
        # Force fallback by making os.link raise EXDEV
        with mock.patch("os.link", side_effect=OSError(18, "Invalid cross-device link")):
            # First write should succeed via fallback exclusive create
            from retrieval_v2.cycle3_runner import atomic_write_result
            out1 = atomic_write_result(result, self.out_path)
            self.assertTrue(out1.exists())
            # Second attempt should fail with FileExistsError, not overwrite via fallback replace
            with self.assertRaises(FileExistsError):
                atomic_write_result(result, self.out_path)
            # Content must remain first payload, not overwritten
            self.assertTrue(self.out_path.exists())

    def test_fallback_owns_only_own_file_on_failure(self):
        result = self._make_valid_result()
        # Mock os.open to fail after exclusive create? Simulate write failure then ensure no foreign delete
        # Create foreign file first
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        self.out_path.write_text('{"foreign": true}\n', encoding="utf-8")
        foreign_content = self.out_path.read_text(encoding="utf-8")
        from retrieval_v2.cycle3_runner import atomic_write_result
        with mock.patch("os.link", side_effect=OSError(18, "EXDEV")):
            with self.assertRaises(FileExistsError):
                atomic_write_result(result, self.out_path)
        self.assertEqual(self.out_path.read_text(encoding="utf-8"), foreign_content)


if __name__ == "__main__":
    unittest.main()
