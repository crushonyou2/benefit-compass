import unittest

from run_eval_rerank import evaluate_items, ml_app


class ProductionParityEvaluationTest(unittest.TestCase):
    def test_uses_production_preprocessing_sql_and_score_contracts(self):
        captured = {"texts": [], "pairs": [], "sql": None, "params": None}

        class FakeEmbedder:
            def encode(self, texts, normalize_embeddings):
                captured["texts"].extend(texts)
                captured["normalize_embeddings"] = normalize_embeddings
                return [[0.1, 0.2]]

        class FakeReranker:
            def predict(self, pairs):
                captured["pairs"].extend(pairs)
                return [0.1, 0.9]

        class FakeCursor:
            def execute(self, sql, params):
                captured["sql"] = sql
                captured["params"] = params

            def fetchall(self):
                return [
                    (
                        "youth", "gold", "청년 지원", "기관", "지원 내용", "온라인",
                        "https://example.test/youth", 19, 34, None, 0.9,
                    ),
                    (
                        "gov24", "other", "일반 지원", "기관", "다른 내용", "방문",
                        "https://example.test/gov24", None, None, None, 0.85,
                    ),
                ]

        ranked = evaluate_items(
            [{
                "query": "서울 청년 지원",
                "age": 25,
                "gold_source": "youth",
                "gold_source_id": "gold",
            }],
            FakeEmbedder(),
            FakeReranker(),
            FakeCursor(),
        )

        self.assertEqual(
            [{"source": "youth", "bi_encoder": 1, "rerank": 0}], ranked)
        self.assertEqual(["query: 청년 지원"], captured["texts"])
        self.assertTrue(captured["normalize_embeddings"])
        self.assertEqual(ml_app.SQL, captured["sql"])
        self.assertEqual(25, captured["params"]["age"])
        self.assertIsNone(captured["params"]["rp"])
        self.assertEqual(0.015, captured["params"]["youth_bias"])
        self.assertEqual(ml_app.CANDIDATES, captured["params"]["n"])
        self.assertEqual("청년 지원", captured["pairs"][0][0])
        self.assertEqual("청년 지원 지원 내용", captured["pairs"][0][1])


if __name__ == "__main__":
    unittest.main()
