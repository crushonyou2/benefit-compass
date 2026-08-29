import pathlib
import unittest


class RunEvalProductionParityTest(unittest.TestCase):
    def test_uses_production_contract(self):
        src = pathlib.Path(__file__).with_name("run_eval.py").read_text(encoding="utf-8")
        # Must reuse production definitions instead of legacy copy
        self.assertIn("ml_app.SQL", src)
        self.assertIn("ml_app.CANDIDATES", src)
        self.assertIn("ml_app.COSINE_MIN", src)
        self.assertIn("ml_app.LEXICAL_OVERLAP_BIAS", src)
        self.assertIn("lexical_overlap_terms", src)
        self.assertIn("strip_region", src)
        self.assertIn("region_filter", src)
        self.assertIn("SEARCH_RESULT_COLUMNS", src)
        # Legacy drift markers must not be present
        self.assertNotIn("SELECT t.source, t.source_id FROM (", src)
        self.assertNotIn('"k": TOPK', src)
        self.assertNotIn("LIMIT %(k)s", src)

    def test_evaluate_uses_production_ranking(self):
        import json
        import pathlib
        from unittest.mock import MagicMock, patch

        import run_eval
        import app as ml_app
        from source_ranking import lexical_overlap_terms, youth_source_bias

        captured = {}

        class FakeEmbedder:
            def encode(self, texts, normalize_embeddings):
                captured["texts"] = texts
                captured["normalize_embeddings"] = normalize_embeddings
                return [[0.1, 0.2]]

        class FakeCursor:
            def __init__(self, rows):
                self._rows = rows

            def execute(self, sql, params=None):
                if "FROM policy" in sql and "count(*)" in sql:
                    captured["corpus_sql"] = sql
                    return
                captured["sql"] = sql
                captured["params"] = params

            def fetchall(self):
                if "corpus_sql" in captured and captured.get("sql") is None:
                    return []
                return self._rows

            def fetchone(self):
                if "corpus_sql" in captured:
                    return [0]
                return self._rows[0] if self._rows else [0]

            def close(self):
                pass

        class FakeConn:
            def __init__(self, rows):
                self._rows = rows

            def cursor(self):
                return FakeCursor(self._rows)

            def close(self):
                pass

        # Single item that should pass COSINE_MIN and be rank 1
        rows_pass = [
            ("youth", "gold", "청년 지원", "기관", "지원 내용", "온라인",
             "https://example.test/youth", 19, 34, None, 0.9),
            ("gov24", "other", "일반 지원", "기관", "다른 내용", "방문",
             "https://example.test/gov24", None, None, None, 0.85),
        ]
        fake_output = MagicMock()
        fake_output.parent.mkdir = MagicMock()
        fake_output.write_text = MagicMock()

        with patch.object(run_eval, "parse_args", return_value=MagicMock(
            eval_file=pathlib.Path("dummy.jsonl"), output=fake_output, lexical_bias=None)):
            with patch.object(run_eval, "load_items", return_value=[{
                "query": "서울 청년 지원",
                "age": 25,
                "gold_source": "youth",
                "gold_source_id": "gold",
            }]):
                with patch.object(run_eval, "load_embedder", return_value=FakeEmbedder()):
                    with patch.object(run_eval.psycopg2, "connect", return_value=FakeConn(rows_pass)):
                        with patch.object(run_eval, "DB", "dummy"):
                            run_eval.main()

        self.assertEqual(["query: 청년 지원"], captured["texts"])
        self.assertTrue(captured["normalize_embeddings"])
        self.assertIs(captured["sql"], ml_app.SQL)
        self.assertEqual(25, captured["params"]["age"])
        self.assertIsNone(captured["params"]["rp"])
        self.assertEqual(0.015, captured["params"]["youth_bias"])
        self.assertEqual(["청년"], captured["params"]["lexical_terms"])
        self.assertEqual(ml_app.LEXICAL_OVERLAP_BIAS, captured["params"]["lexical_bias"])
        self.assertEqual(ml_app.CANDIDATES, captured["params"]["n"])
        # SEARCH_RESULT_COLUMNS mapping and TOPK semantics: gold should be rank 1
        written = json.loads(fake_output.write_text.call_args[0][0])
        self.assertEqual(1, written["n"])
        self.assertEqual(1.0, written["recall@1"])
        self.assertEqual(1.0, written["recall@5"])

        # Verify COSINE_MIN filtering: gold below threshold must be excluded
        captured.clear()
        rows_below = [
            ("youth", "gold", "청년 지원", "기관", "지원 내용", "온라인",
             "https://example.test/youth", 19, 34, None, 0.5),
            ("gov24", "other", "일반 지원", "기관", "다른 내용", "방문",
             "https://example.test/gov24", None, None, None, 0.4),
        ]
        fake_output2 = MagicMock()
        fake_output2.parent.mkdir = MagicMock()
        fake_output2.write_text = MagicMock()
        with patch.object(run_eval, "parse_args", return_value=MagicMock(
            eval_file=pathlib.Path("dummy.jsonl"), output=fake_output2, lexical_bias=None)):
            with patch.object(run_eval, "load_items", return_value=[{
                "query": "서울 청년 지원",
                "age": 25,
                "gold_source": "youth",
                "gold_source_id": "gold",
            }]):
                with patch.object(run_eval, "load_embedder", return_value=FakeEmbedder()):
                    with patch.object(run_eval.psycopg2, "connect", return_value=FakeConn(rows_below)):
                        with patch.object(run_eval, "DB", "dummy"):
                            run_eval.main()

        written2 = json.loads(fake_output2.write_text.call_args[0][0])
        self.assertEqual(0.0, written2["recall@1"])
        self.assertEqual(0.0, written2["recall@5"])


if __name__ == "__main__":
    unittest.main()
