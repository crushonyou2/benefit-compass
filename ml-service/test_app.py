import os
import sys
import threading
import time
import types
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import app as ml_app


class HealthReadinessApiTest(unittest.TestCase):
    def test_local_only_mode_disables_all_hub_access_before_model_import(self):
        captured = {"reranker": {}}

        class FakeSentenceTransformer:
            def __init__(self, model_name, **kwargs):
                captured["model_name"] = model_name
                captured["kwargs"] = kwargs

        class FakeCrossEncoder:
            def __init__(self, model_name, **kwargs):
                captured["reranker"] = {"model_name": model_name, "kwargs": kwargs}

        fake_module = types.ModuleType("sentence_transformers")
        fake_module.SentenceTransformer = FakeSentenceTransformer
        fake_module.CrossEncoder = FakeCrossEncoder

        with patch.dict(os.environ, {}, clear=True), \
                patch.dict(sys.modules, {"sentence_transformers": fake_module}), \
                patch.object(ml_app, "MODEL_LOCAL_ONLY", True), \
                patch.object(ml_app, "RERANK", True):
            models = ml_app.load_models()
            self.assertEqual("1", os.environ["HF_HUB_OFFLINE"])
            self.assertEqual("1", os.environ["TRANSFORMERS_OFFLINE"])

        self.assertIn("model", models)
        self.assertEqual("intfloat/multilingual-e5-base", captured["model_name"])
        self.assertEqual({"local_files_only": True}, captured["kwargs"])
        self.assertEqual("BAAI/bge-reranker-v2-m3", captured["reranker"]["model_name"])
        self.assertEqual({"local_files_only": True}, captured["reranker"]["kwargs"])

    def test_liveness_responds_while_readiness_waits_for_model_loader(self):
        loader_started = threading.Event()
        release_loader = threading.Event()

        def controlled_loader():
            loader_started.set()
            if not release_loader.wait(1.0):
                raise TimeoutError("test loader was not released")
            return {"model": object()}

        with patch.object(ml_app, "load_models_with_log", controlled_loader):
            with TestClient(ml_app.app) as client:
                self.assertTrue(loader_started.wait(1.0))

                health = client.get("/health")
                readiness_while_loading = client.get("/ready")
                self.assertEqual(200, health.status_code)
                self.assertEqual({"status": "ok"}, health.json())
                self.assertEqual(503, readiness_while_loading.status_code)
                self.assertEqual("loading", readiness_while_loading.json()["status"])

                release_loader.set()
                deadline = time.monotonic() + 1.0
                readiness_after_load = client.get("/ready")
                while readiness_after_load.status_code != 200 and time.monotonic() < deadline:
                    time.sleep(0.01)
                    readiness_after_load = client.get("/ready")

                self.assertEqual(200, readiness_after_load.status_code)
                self.assertEqual("ready", readiness_after_load.json()["status"])
                self.assertGreaterEqual(readiness_after_load.json()["model_load_ms"], 0.0)
                self.assertEqual({"status", "model_load_ms"}, set(readiness_after_load.json()))

    def test_search_returns_only_fixed_segment_headers(self):
        class FakeModel:
            def encode(self, texts, normalize_embeddings):
                return [[0.1, 0.2]]

        class FakeCursor:
            def execute(self, sql, params):
                self.params = params

            def fetchall(self):
                return [[
                    "policy-1", "청년 주거 지원", "테스트 기관", "지원 내용",
                    "온라인", "https://example.test", 19, 34, None, 0.9,
                ]]

            def close(self):
                pass

        class FakeConnection:
            def cursor(self):
                return FakeCursor()

            def close(self):
                pass

        fake_runtime = ml_app.ModelRuntime()
        fake_runtime.start(lambda: {"model": FakeModel()})
        fake_runtime.wait(1.0)

        with patch.object(ml_app, "runtime", fake_runtime), \
                patch.object(ml_app, "RERANK", False), \
                patch.object(ml_app.psycopg2, "connect", return_value=FakeConnection()):
            with self.assertLogs(ml_app.log, level="INFO") as captured:
                with TestClient(ml_app.app) as client:
                    response = client.post(
                        "/search",
                        headers={"X-Request-ID": "request-123"},
                        json={"query": "fixed synthetic query", "age": 345678901, "k": 5},
                    )

        self.assertEqual(200, response.status_code)
        self.assertEqual(1, len(response.json()["results"]))
        server_timing = response.headers["Server-Timing"]
        self.assertIn("model_wait;dur=", server_timing)
        self.assertIn("embedding;dur=", server_timing)
        self.assertIn("db_connect;dur=", server_timing)
        self.assertIn("db_query;dur=", server_timing)
        self.assertIn("ml_total;dur=", server_timing)
        timing_names = [entry.strip().split(";", 1)[0]
                        for entry in server_timing.split(",")]
        self.assertEqual(
            ["model_wait", "embedding", "db_connect", "db_query", "rerank", "ml_total"],
            timing_names,
        )
        self.assertIn("X-ML-Model-Load-Ms", response.headers)
        joined_logs = "\n".join(captured.output)
        self.assertIn("request_id=request-123", joined_logs)
        self.assertNotIn("fixed synthetic query", joined_logs)
        self.assertNotIn("345678901", joined_logs)

    def test_not_ready_error_keeps_fixed_timings_without_query_or_age(self):
        secret_query = "query-value-that-must-never-be-logged"
        secret_age = 987654321
        failed_runtime = ml_app.ModelRuntime()
        failed_runtime.start(lambda: (_ for _ in ()).throw(
            ValueError(f"loader {secret_query} {secret_age}")))
        with self.assertRaises(RuntimeError):
            failed_runtime.wait(1.0)

        with patch.object(ml_app, "runtime", failed_runtime):
            with self.assertLogs(ml_app.log, level="ERROR") as captured:
                with TestClient(ml_app.app) as client:
                    readiness = client.get("/ready")
                    response = client.post(
                        "/search",
                        headers={"X-Request-ID": "request-error-1"},
                        json={"query": secret_query, "age": secret_age, "k": 5},
                    )

        self.assertEqual(503, readiness.status_code)
        self.assertEqual({"status", "model_load_ms"}, set(readiness.json()))
        self.assertEqual("error", readiness.json()["status"])
        self.assertEqual(503, response.status_code)
        self.assertEqual({"detail": "ML models are not ready"}, response.json())
        self.assertIn("model_wait;dur=", response.headers["Server-Timing"])
        self.assertIn("ml_total;dur=", response.headers["Server-Timing"])
        self.assertIn("X-ML-Model-Load-Ms", response.headers)
        joined_logs = "\n".join(captured.output)
        self.assertNotIn(secret_query, joined_logs)
        self.assertNotIn(str(secret_age), joined_logs)

    def test_search_failure_returns_fixed_error_and_timing_headers(self):
        secret_query = "db-query-value-that-must-never-be-logged"
        secret_age = 876543210

        class FakeModel:
            def encode(self, texts, normalize_embeddings):
                return [[0.1, 0.2]]

        fake_runtime = ml_app.ModelRuntime()
        fake_runtime.start(lambda: {"model": FakeModel()})
        fake_runtime.wait(1.0)

        with patch.object(ml_app, "runtime", fake_runtime), \
                patch.object(ml_app, "RERANK", False), \
                patch.object(ml_app.psycopg2, "connect",
                             side_effect=ValueError(f"db {secret_query} {secret_age}")):
            with self.assertLogs(ml_app.log, level="ERROR") as captured:
                with TestClient(ml_app.app) as client:
                    response = client.post(
                        "/search",
                        headers={"X-Request-ID": "request-error-2"},
                        json={"query": secret_query, "age": secret_age, "k": 5},
                    )

        self.assertEqual(500, response.status_code)
        self.assertEqual({"detail": "ML search failed"}, response.json())
        self.assertIn("embedding;dur=", response.headers["Server-Timing"])
        self.assertIn("ml_total;dur=", response.headers["Server-Timing"])
        joined_logs = "\n".join(captured.output)
        self.assertNotIn(secret_query, joined_logs)
        self.assertNotIn(str(secret_age), joined_logs)


if __name__ == "__main__":
    unittest.main()
