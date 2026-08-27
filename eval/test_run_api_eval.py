import unittest

from run_api_eval import summarize


class ApiEvalTest(unittest.TestCase):
    def test_summarizes_retrieval_and_grounding_failures(self):
        records = [
            (
                {
                    "query": "일반 국민 정책",
                    "gold_source": "gov24",
                    "gold_source_id": "g-1",
                    "case_type": "general",
                },
                {
                    "generated": True,
                    "sources": [
                        {"source": "youth", "source_id": "y-1", "apply_url": None},
                        {
                            "source": "gov24",
                            "source_id": "g-1",
                            "apply_url": "https://www.gov.kr/example",
                        },
                    ],
                },
            ),
            (
                {"query": "정답 없는 질문", "expected_no_results": True},
                {"generated": False, "sources": []},
            ),
            (
                {"query": "무근거 생성 탐지", "expected_no_results": True},
                {"generated": True, "sources": []},
            ),
            (
                {
                    "query": "스무 살인데 기초연금을 받을 수 있나요?",
                    "age": 20,
                    "excluded_source": "gov24",
                    "excluded_source_id": "pension-65",
                },
                {
                    "generated": True,
                    "sources": [
                        {
                            "source": "gov24",
                            "source_id": "pension-65",
                            "apply_url": "https://www.gov.kr/pension",
                        }
                    ],
                },
            ),
        ]

        result = summarize(records)

        self.assertEqual(1.0, result["retrieval"]["recall@5"])
        self.assertEqual(0.5, result["retrieval"]["mrr"])
        self.assertEqual(1, result["missing_ground_links"])
        self.assertEqual(1, result["answer_generated_without_sources"])
        self.assertEqual(0, result["no_answer"]["unexpected_results"])
        self.assertEqual(1, result["ineligible"]["forbidden_policy_results"])


if __name__ == "__main__":
    unittest.main()
