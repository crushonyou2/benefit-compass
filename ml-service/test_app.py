import threading
import time
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

import app as ml_app


class HealthReadinessApiTest(unittest.TestCase):
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
            with TestClient(ml_app.app) as client:
                response = client.post(
                    "/search",
                    headers={"X-Request-ID": "request-123"},
                    json={"query": "fixed synthetic query", "age": None, "k": 5},
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


if __name__ == "__main__":
    unittest.main()
