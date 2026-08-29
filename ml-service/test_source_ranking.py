import unittest

from source_ranking import (
    GOV24_INTENT_TERMS,
    LEXICAL_OVERLAP_BIAS,
    YOUTH_INTENT_BIAS,
    lexical_overlap_terms,
    ranking_metadata,
    youth_source_bias,
)


class SourceRankingTest(unittest.TestCase):
    def test_boosts_explicit_youth_intent(self):
        self.assertEqual(YOUTH_INTENT_BIAS, youth_source_bias("청년 월세 지원을 찾고 있어요"))
        self.assertEqual(YOUTH_INTENT_BIAS, youth_source_bias("대학생 취업 지원이 궁금해요"))
        self.assertEqual(YOUTH_INTENT_BIAS, youth_source_bias("사회초년생 주거 지원"))

    def test_explicit_gov24_agency_takes_precedence(self):
        self.assertEqual(
            0.0,
            youth_source_bias("국토교통부 청년월세 지원을 찾고 있어요"),
        )
        self.assertEqual(
            0.0,
            youth_source_bias("중소벤처기업부의 청년 창업 융자사업"),
        )

        corpus_agencies = (
            "해양수산부",
            "산림청",
            "국가보훈부",
            "통일부",
            "법무부",
            "국방부",
        )
        for agency in corpus_agencies:
            with self.subTest(agency=agency):
                self.assertIn(agency, GOV24_INTENT_TERMS)
                self.assertEqual(0.0, youth_source_bias(f"{agency} 청년 지원"))

    def test_leaves_generic_queries_unbiased(self):
        self.assertEqual(0.0, youth_source_bias("출산 후 받을 수 있는 지원"))

    def test_extracts_distinct_content_terms(self):
        self.assertEqual(
            ["청년", "월세", "지원금"],
            lexical_overlap_terms("청년 월세 지원금 받을 수 있나요"),
        )

    def test_metadata_records_lexical_rule(self):
        self.assertEqual(
            LEXICAL_OVERLAP_BIAS,
            ranking_metadata()["lexical_overlap_bias"],
        )

    def test_metadata_records_the_frozen_rule(self):
        metadata = ranking_metadata()
        self.assertEqual(YOUTH_INTENT_BIAS, metadata["youth_intent_bias"])
        self.assertIn("청년", metadata["youth_intent_terms"])
        self.assertIn("국토교통부", metadata["gov24_intent_terms"])


if __name__ == "__main__":
    unittest.main()
