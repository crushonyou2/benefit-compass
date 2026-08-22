import time
import unittest

from runtime_state import ModelRuntime, safe_request_id, server_timing_header


class ModelRuntimeTest(unittest.TestCase):
    def test_health_state_is_loading_before_models_are_ready(self):
        runtime = ModelRuntime()

        def loader():
            time.sleep(0.02)
            return {"model": object()}

        runtime.start(loader)
        self.assertIn(runtime.snapshot().status, {"loading", "ready"})
        self.assertIn("model", runtime.wait(1.0))
        snapshot = runtime.snapshot()
        self.assertEqual("ready", snapshot.status)
        self.assertGreaterEqual(snapshot.model_load_ms, 0.0)

    def test_loader_failure_becomes_not_ready_without_error_details(self):
        runtime = ModelRuntime()

        def loader():
            raise ValueError("sensitive loader detail")

        runtime.start(loader)
        with self.assertRaisesRegex(RuntimeError, "model loading failed"):
            runtime.wait(1.0)
        self.assertEqual("error", runtime.snapshot().status)


class TimingPrivacyTest(unittest.TestCase):
    def test_server_timing_uses_only_fixed_names(self):
        header = server_timing_header({
            "embedding": 12.3456,
            "db_query": 4.5,
            "user_question": 999,
        })
        self.assertEqual("embedding;dur=12.346, db_query;dur=4.500", header)
        self.assertNotIn("user_question", header)

    def test_request_id_rejects_arbitrary_content(self):
        request_id = "123e4567-e89b-42d3-a456-426614174000"
        self.assertEqual(request_id, safe_request_id(request_id))
        self.assertEqual("none", safe_request_id("abc-123"))
        self.assertEqual("none", safe_request_id("01012345678"))
        self.assertEqual("none", safe_request_id("서울-25"))
        self.assertEqual("none", safe_request_id("raw question with spaces"))


if __name__ == "__main__":
    unittest.main()
