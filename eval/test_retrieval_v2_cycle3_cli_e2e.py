"""Cycle3 CLI E2E fake/mock tests — actual main/orchestration/audit/complete validation/write path.

Covers blockers 1-8 via injected factories and temp canonical root/log/output:
- no DB/model/plaintext touched (fake embedding/retrieval/corpus/load)
- exercises real parse_args, path confinement, grant token pinning, one-shot, audit lifecycle,
  corpus provenance, embedding parity, pgvector formatting, MRR@10, result schema, atomic race guard.

All tests use temp audit log + temp canonical root via ROOT patching and injected deps.
"""

import hashlib
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
    EXPECTED_DEV_SHA256,
    EXPECTED_DEV_CASES,
    EXPECTED_CORPUS_TOTAL_POLICIES,
    EXPECTED_CORPUS_TOTAL_CHUNKS,
    EXPECTED_CORPUS_BY_SOURCE,
    BATCH_ID,
    CANDIDATE_IDS,
    BASELINE_ID,
    ALL_CANONICAL_IDS,
    CANONICAL_DEV_OUTPUT_REL,
    CANONICAL_DEV_AUDIT_REL,
    format_pgvector,
    compute_metrics_from_ranks,
    validate_complete_result,
    validate_corpus_provenance,
    assert_no_prior_canonical_attempt,
)
from retrieval_v2.cycle3_audit import append_event, read_and_verify_chain
from retrieval_v2.run_cycle3_canonical_dev import main as cli_main, parse_args
import retrieval_v2.cycle3_runner as runner_mod
import retrieval_v2.run_cycle3_canonical_dev as cli_mod


def _synthetic_items(n=36):
    items = []
    for i in range(n):
        src = "youth" if i % 2 == 0 else "gov24"
        items.append({
            "id": f"c3d-{i+1:03d}",
            "case_id": f"c3d-{i+1:03d}",
            "query": f"synthetic query {i} for {src} 청년 지원" if src == "youth" else f"synthetic query {i} for {src} 정부24 지원",
            "raw": f"synthetic query {i}",
            "gold_source": src,
            "gold_source_id": f"gold-{i}",
            "source": src,
            "source_id": f"gold-{i}",
            "age": 25,
            "category": "housing_finance" if i % 6 == 0 else "family_care",
        })
    return items


class EmbeddingParityTest(unittest.TestCase):
    def test_real_embedding_factory_uses_query_prefix_and_normalize_and_6decimal(self):
        from retrieval_v2.run_cycle3_canonical_dev import _real_embedding_fn_factory
        from retrieval_v2.cycle3_runner import format_pgvector
        calls = []
        class FakeModel:
            def encode(self, texts, normalize_embeddings=False):
                calls.append((texts, normalize_embeddings))
                import numpy as np
                return np.array([[0.123456789, 0.2, 0.987654321]])
        model = FakeModel()
        fn = _real_embedding_fn_factory(model)
        vec_str = fn("hello stripped")
        self.assertEqual(len(calls), 1)
        texts, norm = calls[0]
        self.assertEqual(texts, ["query: hello stripped"])
        self.assertTrue(norm)
        self.assertEqual(vec_str, "[0.123457,0.200000,0.987654]")
        self.assertEqual(format_pgvector([0.123456789, 0.2]), "[0.123457,0.200000]")

    def test_format_pgvector_production_compatible(self):
        import numpy as np
        vec = np.array([1.0, 0.0, -0.5])
        s = format_pgvector(vec)
        self.assertEqual(s, "[1.000000,0.000000,-0.500000]")
        self.assertEqual(format_pgvector([0.1, 0.2]), "[0.100000,0.200000]")


class MRRRank11Test(unittest.TestCase):
    def test_mrr_at_10_zero_beyond_10(self):
        per_case_ranks = [11] + [5] * 35
        per_case_sources = ["youth"] * 18 + ["gov24"] * 18
        metrics = compute_metrics_from_ranks(per_case_ranks, per_case_sources)
        expected_mrr = (35 * 0.2) / 36
        self.assertAlmostEqual(metrics["mrr@10"], expected_mrr, places=9)
        buggy_mrr = (1/11 + 35*0.2) / 36
        self.assertNotAlmostEqual(metrics["mrr@10"], buggy_mrr, places=4)
        self.assertEqual(metrics["hit@10"], 35)

    def test_mrr_rank_10_vs_11(self):
        ranks_10 = [10]
        ranks_11 = [11]
        m10 = compute_metrics_from_ranks(ranks_10, ["youth"])
        m11 = compute_metrics_from_ranks(ranks_11, ["youth"])
        self.assertAlmostEqual(m10["mrr@10"], 0.1)
        self.assertEqual(m11["mrr@10"], 0.0)


class CorpusProvenanceTest(unittest.TestCase):
    def test_valid_corpus_passes(self):
        valid = {
            "total_policies": 13589,
            "total_chunks": 17609,
            "by_source": {
                "youth": {"policies": 2631, "chunks": 3083},
                "gov24": {"policies": 10958, "chunks": 14526},
            },
        }
        validate_corpus_provenance(valid)

    def test_invalid_corpus_fails(self):
        bad = {
            "total_policies": 13588,
            "total_chunks": 17609,
            "by_source": {
                "youth": {"policies": 2631, "chunks": 3083},
                "gov24": {"policies": 10958, "chunks": 14526},
            },
        }
        with self.assertRaises(ValueError):
            validate_corpus_provenance(bad)


class ResultSchemaStrictTest(unittest.TestCase):
    def _make_valid_complete(self, tmp_root):
        items = _synthetic_items(36)
        call_counter = {"n": 0}
        def fake_embed(stripped):
            return format_pgvector([0.1, 0.2, 0.3])
        def fake_retrieve(cid, vec, terms, yb, age, rp):
            assert isinstance(vec, str)
            idx = call_counter["n"] // 4
            gold_src = items[idx]["gold_source"]
            gold_id = items[idx]["gold_source_id"]
            desired = 1 if cid != BASELINE_ID else 5
            rows = []
            for r in range(1, 31):
                dist = 0.05 + (r - 1) * 0.005
                score = 1.0 - dist
                if r == desired:
                    rows.append({"source": gold_src, "source_id": gold_id, "dist": dist, "score": score})
                else:
                    rows.append({"source": "other", "source_id": f"other-{r}", "dist": dist, "score": score})
            call_counter["n"] += 1
            return rows
        def fake_latency(quality_ids):
            out = {}
            for cid in quality_ids:
                out[cid] = {"p50": 400.0, "p95": 450.0, "count": 180}
            out[BASELINE_ID] = {"p50": 400.0, "p95": 460.0, "count": 180}
            return out
        call_counter["n"] = 0
        def fake_retrieve_quality(cid, vec, terms, yb, age, rp):
            idx = call_counter["n"] // 4
            gold_src = items[idx]["gold_source"]
            gold_id = items[idx]["gold_source_id"]
            desired = 10 if cid == BASELINE_ID else 1
            rows = []
            for r in range(1, 31):
                dist = 0.05 + (r - 1) * 0.005
                score = 1.0 - dist
                if r == desired:
                    rows.append({"source": gold_src, "source_id": gold_id, "dist": dist, "score": score})
                else:
                    rows.append({"source": "other", "source_id": f"other-{r}", "dist": dist, "score": score})
            call_counter["n"] += 1
            return rows
        from retrieval_v2.cycle3_runner import orchestrate_4way_batch
        result = orchestrate_4way_batch(items, embedding_fn=fake_embed, retrieval_fn=fake_retrieve_quality, latency_measurer=fake_latency)
        return result

    def test_selected_candidate_strict(self):
        result = self._make_valid_complete(None)
        self.assertIn(result["selection"]["selected_candidate"], list(CANDIDATE_IDS) + [None])
        self.assertNotEqual(result["selection"]["selected_candidate"], BASELINE_ID)
        result["selection"]["selected_candidate"] = BASELINE_ID
        with self.assertRaises(ValueError):
            validate_complete_result(result)

    def test_latency_quality_only(self):
        result = self._make_valid_complete(None)
        result["selection"]["quality_selectable"] = []
        result["selection"]["per_candidate"] = {cid: {"quality_selectable": False, "quality_diag": {}, "dev_selectable": False, "dev_diag": {}} for cid in CANDIDATE_IDS}
        result["latency"][CANDIDATE_IDS[0]] = {"p95": 400}
        with self.assertRaises(ValueError):
            validate_complete_result(result)

    def test_git_strict(self):
        result = self._make_valid_complete(None)
        result["git"]["head"] = "unknown"
        with self.assertRaises(ValueError):
            validate_complete_result(result)
        result = self._make_valid_complete(None)
        result["git"]["head"] = "zzzz" + "0"*36
        with self.assertRaises(ValueError):
            validate_complete_result(result)
        result = self._make_valid_complete(None)
        result["git"]["head"] = "a"*40
        result["git"]["dirty"] = "notbool"
        with self.assertRaises(ValueError):
            validate_complete_result(result)

    def test_corpus_required(self):
        result = self._make_valid_complete(None)
        del result["corpus_provenance"]
        with self.assertRaises(ValueError):
            validate_complete_result(result)
        result = self._make_valid_complete(None)
        result["corpus_provenance"]["total_policies"] = 999
        with self.assertRaises(ValueError):
            validate_complete_result(result)

    def test_metrics_per_case_consistency(self):
        result = self._make_valid_complete(None)
        result["per_case"][0]["ranks"][BASELINE_ID] = 1
        with self.assertRaises(ValueError):
            validate_complete_result(result)


class CliE2ETest(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.tmp_root = pathlib.Path(self.tmpdir.name)
        (self.tmp_root / "eval/retrieval-v2/cycle3/dev").mkdir(parents=True)
        (self.tmp_root / "eval/retrieval-v2/cycle3/canonical-dev").mkdir(parents=True)
        (self.tmp_root / "eval/retrieval-v2/cycle3/audit").mkdir(parents=True)
        self.dev_path = self.tmp_root / "eval/retrieval-v2/cycle3/dev/evalset.jsonl"
        self.dev_path.write_text('{"dummy": 1}\n', encoding="utf-8")
        self.out_path = self.tmp_root / CANONICAL_DEV_OUTPUT_REL
        self.audit_path = self.tmp_root / CANONICAL_DEV_AUDIT_REL
        self.session_id = "e2e-test-session-20260831"
        self.patcher_runner_root = mock.patch.object(runner_mod, "ROOT", self.tmp_root)
        self.patcher_cli_root = mock.patch.object(cli_mod, "ROOT", self.tmp_root)
        self.patcher_runner_root.start()
        self.patcher_cli_root.start()
        self.addCleanup(self.patcher_runner_root.stop)
        self.addCleanup(self.patcher_cli_root.stop)
        self.addCleanup(self.tmpdir.cleanup)
        self.env_patch = mock.patch.dict(os.environ, {
            "CYCLE3_CANONICAL_EXECUTION": "1",
            "CYCLE3_SESSION_ID": self.session_id,
            "DATABASE_URL": "postgres://fake",
        })
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)

    def _create_grant(self, session_id=None, set_sha=EXPECTED_DEV_SHA256):
        sid = session_id or self.session_id
        ev = append_event(
            self.audit_path,
            action="protected_access_start",
            candidate_id=None,
            set_role="dev",
            set_sha=set_sha,
            outcome="success",
            session_id=sid,
        )
        return ev

    def _synthetic_injected_deps(self, scenario="selectable"):
        items = _synthetic_items(36)
        call_counter = {"n": 0}
        def fake_embed_factory(_):
            def _embed(stripped: str):
                return format_pgvector([hash(stripped) % 100 / 100.0, 0.2, 0.3])
            return _embed
        def fake_retrieval_factory(_, __):
            def _retrieve(cid, vec, terms, yb, age, rp):
                assert isinstance(vec, str) and vec.startswith("[")
                assert rp is None
                idx = call_counter["n"] // 4
                if idx >= len(items):
                    idx = len(items) - 1
                gold_src = items[idx]["gold_source"]
                gold_id = items[idx]["gold_source_id"]
                desired = 10 if cid == BASELINE_ID else 1
                rows = []
                for r in range(1, 31):
                    dist = 0.05 + (r - 1) * 0.005
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
                out[BASELINE_ID] = {"p50": 410.0, "p95": 460.0, "count": 180, "samples": [410]*5}
                return out
            return _measure
        def fake_load(path, role="dev"):
            return items
        def fake_sha(path):
            return EXPECTED_DEV_SHA256
        def fake_corpus():
            return {
                "total_policies": EXPECTED_CORPUS_TOTAL_POLICIES,
                "total_chunks": EXPECTED_CORPUS_TOTAL_CHUNKS,
                "by_source": dict(EXPECTED_CORPUS_BY_SOURCE),
            }
        return {
            "items": items,
            "embed_factory": fake_embed_factory,
            "retrieval_factory": fake_retrieval_factory,
            "latency_factory": fake_latency_factory,
            "load_fn": fake_load,
            "sha_fn": fake_sha,
            "corpus_fn": fake_corpus,
            "call_counter": call_counter,
        }

    def test_cli_success_e2e_through_actual_main(self):
        grant = self._create_grant()
        deps = self._synthetic_injected_deps()
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
        self.assertEqual(data["corpus_provenance"]["total_policies"], EXPECTED_CORPUS_TOTAL_POLICIES)
        self.assertIn(data["selection"]["selected_candidate"], list(CANDIDATE_IDS) + [None])
        self.assertNotEqual(data["selection"]["selected_candidate"], BASELINE_ID)
        for cid in CANDIDATE_IDS:
            is_q = data["selection"]["per_candidate"][cid]["quality_selectable"]
            if not is_q:
                self.assertIsNone(data["latency"][cid])
            else:
                self.assertIsNotNone(data["latency"][cid])
                self.assertIn("p95", data["latency"][cid])
        self.assertIsNotNone(data["latency"][BASELINE_ID])
        self.assertRegex(data["git"]["head"], r"^[0-9a-f]{40}$")
        self.assertIsInstance(data["git"]["dirty"], bool)
        chain = read_and_verify_chain(self.audit_path)
        actions = [e["action"] for e in chain]
        self.assertIn("run_start", actions)
        self.assertIn("run_end", actions)
        self.assertIn("protected_access_end", actions)
        run_ends = [e for e in chain if e["action"] == "run_end" and e["candidate_id"] == BATCH_ID]
        self.assertEqual(run_ends[-1]["outcome"], "success")

    def test_cli_failure_no_result_and_audit_failure_closure(self):
        grant = self._create_grant()
        deps = self._synthetic_injected_deps()
        def failing_retrieval_factory(_, __):
            def _retrieve(cid, vec, terms, yb, age, rp):
                raise RuntimeError("synthetic retrieval failure")
            return _retrieve
        with self.assertRaises(RuntimeError) as ctx:
            cli_main(
                ["--dev-evalset", "eval/retrieval-v2/cycle3/dev/evalset.jsonl",
                 "--output", CANONICAL_DEV_OUTPUT_REL,
                 "--audit-log", CANONICAL_DEV_AUDIT_REL,
                 "--session-id", self.session_id],
                _embedding_fn_factory=deps["embed_factory"],
                _retrieval_fn_factory=failing_retrieval_factory,
                _load_and_validate_fn=deps["load_fn"],
                _canonical_sha_fn=deps["sha_fn"],
                _corpus_provenance_fn=deps["corpus_fn"],
            )
        self.assertIn("canonical dev batch failed", str(ctx.exception))
        self.assertFalse(self.out_path.exists())
        chain = read_and_verify_chain(self.audit_path)
        run_ends = [e for e in chain if e["action"] == "run_end" and e["candidate_id"] == BATCH_ID]
        self.assertEqual(run_ends[-1]["outcome"], "failure")
        protected_ends = [e for e in chain if e["action"] == "protected_access_end" and e["set_role"] == "dev"]
        self.assertEqual(protected_ends[-1]["outcome"], "failure")

    def test_cli_audit_closure_failure_removes_result(self):
        grant = self._create_grant()
        deps = self._synthetic_injected_deps()
        with mock.patch("retrieval_v2.run_cycle3_canonical_dev.append_canonical_run_end", side_effect=RuntimeError("mock run_end fail")):
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
            self.assertIn("audit run_end append failed", str(ctx.exception))
            self.assertIn("result removed", str(ctx.exception))
        self.assertFalse(self.out_path.exists())

    def test_cli_one_shot_blocks_second_attempt_even_if_first_failed_before_output(self):
        grant = self._create_grant()
        deps = self._synthetic_injected_deps()
        def failing_factory(_, __):
            def _r(cid, vec, terms, yb, age, rp):
                raise RuntimeError("fail before output")
            return _r
        with self.assertRaises(RuntimeError):
            cli_main(
                ["--dev-evalset", "eval/retrieval-v2/cycle3/dev/evalset.jsonl",
                 "--output", CANONICAL_DEV_OUTPUT_REL,
                 "--audit-log", CANONICAL_DEV_AUDIT_REL,
                 "--session-id", self.session_id],
                _embedding_fn_factory=deps["embed_factory"],
                _retrieval_fn_factory=failing_factory,
                _load_and_validate_fn=deps["load_fn"],
                _canonical_sha_fn=deps["sha_fn"],
                _corpus_provenance_fn=deps["corpus_fn"],
            )
        self.assertFalse(self.out_path.exists())
        deps2 = self._synthetic_injected_deps()
        with self.assertRaises(RuntimeError) as ctx2:
            cli_main(
                ["--dev-evalset", "eval/retrieval-v2/cycle3/dev/evalset.jsonl",
                 "--output", CANONICAL_DEV_OUTPUT_REL,
                 "--audit-log", CANONICAL_DEV_AUDIT_REL,
                 "--session-id", self.session_id],
                _embedding_fn_factory=deps2["embed_factory"],
                _retrieval_fn_factory=deps2["retrieval_factory"],
                _latency_measurer_factory=deps2["latency_factory"],
                _load_and_validate_fn=deps2["load_fn"],
                _canonical_sha_fn=deps2["sha_fn"],
                _corpus_provenance_fn=deps2["corpus_fn"],
            )
        self.assertIn("one-shot", str(ctx2.exception).lower())
        self.assertIn(BATCH_ID, str(ctx2.exception))
        self.assertFalse(self.out_path.exists())

    def test_cli_one_shot_blocks_second_success_attempt(self):
        grant = self._create_grant()
        deps = self._synthetic_injected_deps()
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
        deps2 = self._synthetic_injected_deps()
        with self.assertRaises((RuntimeError, FileExistsError)) as ctx:
            cli_main(
                ["--dev-evalset", "eval/retrieval-v2/cycle3/dev/evalset.jsonl",
                 "--output", CANONICAL_DEV_OUTPUT_REL,
                 "--audit-log", CANONICAL_DEV_AUDIT_REL,
                 "--session-id", self.session_id],
                _embedding_fn_factory=deps2["embed_factory"],
                _retrieval_fn_factory=deps2["retrieval_factory"],
                _latency_measurer_factory=deps2["latency_factory"],
                _load_and_validate_fn=deps2["load_fn"],
                _canonical_sha_fn=deps2["sha_fn"],
                _corpus_provenance_fn=deps2["corpus_fn"],
            )
        msg = str(ctx.exception).lower()
        self.assertTrue("one-shot" in msg or "single batch guard" in msg or "already exists" in msg, f"unexpected error: {ctx.exception}")
        self.out_path.unlink()
        deps3 = self._synthetic_injected_deps()
        with self.assertRaises(RuntimeError) as ctx3:
            cli_main(
                ["--dev-evalset", "eval/retrieval-v2/cycle3/dev/evalset.jsonl",
                 "--output", CANONICAL_DEV_OUTPUT_REL,
                 "--audit-log", CANONICAL_DEV_AUDIT_REL,
                 "--session-id", self.session_id],
                _embedding_fn_factory=deps3["embed_factory"],
                _retrieval_fn_factory=deps3["retrieval_factory"],
                _latency_measurer_factory=deps3["latency_factory"],
                _load_and_validate_fn=deps3["load_fn"],
                _canonical_sha_fn=deps3["sha_fn"],
                _corpus_provenance_fn=deps3["corpus_fn"],
            )
        self.assertIn("one-shot", str(ctx3.exception).lower())

    def test_cli_atomic_overwrite_race_guard(self):
        grant = self._create_grant()
        deps = self._synthetic_injected_deps()
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        self.out_path.write_text('{"preexisting": true}\n', encoding="utf-8")
        with self.assertRaises((FileExistsError, RuntimeError)) as ctx:
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
        content = self.out_path.read_text(encoding="utf-8")
        self.assertIn("preexisting", content)

    def test_cli_grant_token_pinning(self):
        grant = self._create_grant()
        token = grant["event_hash"]
        deps = self._synthetic_injected_deps()
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
        self.assertTrue(self.out_path.exists())
        tmp2 = tempfile.TemporaryDirectory()
        tmp_root2 = pathlib.Path(tmp2.name)
        (tmp_root2 / "eval/retrieval-v2/cycle3/dev").mkdir(parents=True)
        (tmp_root2 / "eval/retrieval-v2/cycle3/canonical-dev").mkdir(parents=True)
        (tmp_root2 / "eval/retrieval-v2/cycle3/audit").mkdir(parents=True)
        dev2 = tmp_root2 / "eval/retrieval-v2/cycle3/dev/evalset.jsonl"
        dev2.write_text('{"dummy":1}\n', encoding="utf-8")
        audit2 = tmp_root2 / CANONICAL_DEV_AUDIT_REL
        out2 = tmp_root2 / CANONICAL_DEV_OUTPUT_REL
        ev2 = append_event(audit2, action="protected_access_start", candidate_id=None, set_role="dev", set_sha=EXPECTED_DEV_SHA256, outcome="success", session_id="session-token-test")
        valid_token2 = ev2["event_hash"]
        invalid_token = "0"*64
        with mock.patch.object(runner_mod, "ROOT", tmp_root2), mock.patch.object(cli_mod, "ROOT", tmp_root2):
            deps2 = self._synthetic_injected_deps()
            with self.assertRaises(RuntimeError) as ctx:
                cli_main(
                    ["--dev-evalset", "eval/retrieval-v2/cycle3/dev/evalset.jsonl",
                     "--output", CANONICAL_DEV_OUTPUT_REL,
                     "--audit-log", CANONICAL_DEV_AUDIT_REL,
                     "--session-id", "session-token-test",
                     "--grant-token", invalid_token],
                    _embedding_fn_factory=deps2["embed_factory"],
                    _retrieval_fn_factory=deps2["retrieval_factory"],
                    _latency_measurer_factory=deps2["latency_factory"],
                    _load_and_validate_fn=deps2["load_fn"],
                    _canonical_sha_fn=deps2["sha_fn"],
                    _corpus_provenance_fn=deps2["corpus_fn"],
                )
            self.assertIn("protected dev access denied", str(ctx.exception).lower())
            self.assertFalse(out2.exists())
            deps3 = self._synthetic_injected_deps()
            with mock.patch.dict(os.environ, {"CYCLE3_GRANT_TOKEN": valid_token2, "CYCLE3_CANONICAL_EXECUTION": "1", "CYCLE3_SESSION_ID": "session-token-test"}):
                cli_main(
                    ["--dev-evalset", "eval/retrieval-v2/cycle3/dev/evalset.jsonl",
                     "--output", CANONICAL_DEV_OUTPUT_REL,
                     "--audit-log", CANONICAL_DEV_AUDIT_REL,
                     "--session-id", "session-token-test"],
                    _embedding_fn_factory=deps3["embed_factory"],
                    _retrieval_fn_factory=deps3["retrieval_factory"],
                    _latency_measurer_factory=deps3["latency_factory"],
                    _load_and_validate_fn=deps3["load_fn"],
                    _canonical_sha_fn=deps3["sha_fn"],
                    _corpus_provenance_fn=deps3["corpus_fn"],
                )
                self.assertTrue(out2.exists())
        tmp2.cleanup()

    def test_cli_path_confinement_blocks_traversal(self):
        grant = self._create_grant()
        deps = self._synthetic_injected_deps()
        traversal = "../../../eval/retrieval-v2/cycle3/dev/evalset.jsonl"
        with self.assertRaises((ValueError, RuntimeError)):
            cli_main(
                ["--dev-evalset", traversal,
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

if __name__ == "__main__":
    unittest.main()
