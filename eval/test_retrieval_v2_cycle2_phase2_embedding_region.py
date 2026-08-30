"""Static tests for embedding-input SIDO 1-preservation (cycle2 Phase2 Exp2).

Verifies: lexical unchanged, embedding adds at most one SIDO canonical from raw via SIDO table only,
no si/gun/gu dict, no hardcode, deterministic, bounded, earliest occurrence rule.
"""

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ml-service"))
sys.path.insert(0, str(ROOT / "eval"))

import app as ml_app
from retrieval_v2.candidate_lexical_rewrite import lexical_overlap_terms_rewrite
from retrieval_v2.candidate_embedding_region_hint import (
    _detect_sido_codes,
    canonical_for_code,
    embedding_query_with_region_hint,
    lexical_terms_for_candidate,
)


class EmbeddingRegionHintSemanticsTest(unittest.TestCase):
    def test_lexical_terms_identical_to_candidate_v2(self):
        raws = [
            "부산에 사는 청년이 월세 부담을 덜기 위해 월세 지원을 받을 수 있나요?",
            "세종시에서 청년이 청년센터를 이용해 정책 네트워크나 프로그램에 참여할 수 있나요?",
            "충남에서 청년이 우울이나 자살 관련 정신건강 검진과 심리지원을 받을 수 있나요?",
            "경기도 청년이 청년참여기구를 통해 정책 제안이나 모니터링에 참여할 수 있을까요?",
            "청년이 주택 마련을 위해 청년주택드림청약통장을 가입할 수 있는 방법이 있을까요?",
        ]
        for raw in raws:
            stripped = ml_app.strip_region(raw)
            base = lexical_overlap_terms_rewrite(stripped)
            cand = lexical_terms_for_candidate(raw)
            self.assertEqual(base, cand, f"lexical must be identical for {raw}")

    def test_canonical_is_first_alias(self):
        for code, aliases in ml_app.SIDO.items():
            self.assertEqual(canonical_for_code(code), aliases[0])

    def test_busan_embedding_adds_one_busan(self):
        raw = "부산에 사는 청년이 월세 지원을 받을 수 있나요?"
        stripped = ml_app.strip_region(raw)
        q = embedding_query_with_region_hint(raw)
        self.assertEqual(q, f"{stripped} 부산")
        self.assertEqual(_detect_sido_codes(raw), ["26"])
        self.assertNotIn("부산", stripped)

    def test_sejong_embedding_adds_sejong(self):
        raw = "세종시에서 청년이 청년센터를 이용할 수 있나요?"
        stripped = ml_app.strip_region(raw)
        q = embedding_query_with_region_hint(raw)
        self.assertEqual(q, f"{stripped} 세종")
        self.assertIn("36", _detect_sido_codes(raw))

    def test_chungnam_embedding_adds_chungnam_not_full_name(self):
        raw = "충남에서 청년이 정신건강 검진을 받을 수 있나요?"
        q = embedding_query_with_region_hint(raw)
        stripped = ml_app.strip_region(raw)
        self.assertEqual(q, f"{stripped} 충남")
        self.assertNotIn("충청남도", q)
        raw_long = "충청남도에서 청년이 정신건강 검진을 받을 수 있나요?"
        q_long = embedding_query_with_region_hint(raw_long)
        self.assertEqual(q_long, f"{ml_app.strip_region(raw_long)} 충남")
        self.assertEqual(_detect_sido_codes(raw_long), ["44"])
        self.assertEqual(_detect_sido_codes("충남과 충청남도에서 청년 지원"), ["44"])

    def test_no_region_embedding_unchanged(self):
        raw = "청년이 주택 마련을 위해 청년주택드림청약통장을 가입할 수 있는 방법이 있을까요?"
        stripped = ml_app.strip_region(raw)
        q = embedding_query_with_region_hint(raw)
        self.assertEqual(q, stripped)
        self.assertEqual(_detect_sido_codes(raw), [])

    def test_multiple_sido_bounded_to_one(self):
        raw = "서울과 부산에서 청년이 창업 지원을 받을 수 있나요?"
        stripped = ml_app.strip_region(raw)
        q = embedding_query_with_region_hint(raw)
        codes = _detect_sido_codes(raw)
        self.assertEqual(set(codes), {"11", "26"})
        # earliest in raw is 서울 at pos 0 -> 서울
        self.assertEqual(q, f"{stripped} 서울")
        self.assertEqual(q.split().count("서울"), 1)
        self.assertNotIn("부산", q)

    def test_earliest_not_sorted(self):
        # reversed order: 부산 appears before 서울, earliest wins over sorted-code order
        raw = "부산과 서울에서 청년이 창업 지원을 받을 수 있나요?"
        stripped = ml_app.strip_region(raw)
        q = embedding_query_with_region_hint(raw)
        self.assertEqual(q, f"{stripped} 부산")
        self.assertEqual(q.split().count("부산"), 1)
        self.assertNotIn("서울", q)
        from retrieval_v2.candidate_embedding_region_hint import _earliest_sido_code

        self.assertEqual(_earliest_sido_code(raw), "26")
        self.assertEqual(_earliest_sido_code("서울과 부산에서"), "11")

    def test_same_region_duplicate_still_one(self):
        raw = "부산에서 부산 청년이 부산 월세 지원"
        q = embedding_query_with_region_hint(raw)
        stripped = ml_app.strip_region(raw)
        self.assertEqual(q, f"{stripped} 부산")
        self.assertEqual(q.split().count("부산"), 1)
        self.assertEqual(_detect_sido_codes(raw), ["26"])

    def test_gyeonggi_embedding(self):
        raw = "경기도 청년이 청년참여기구를 통해 정책 제안에 참여할 수 있을까요?"
        stripped = ml_app.strip_region(raw)
        q = embedding_query_with_region_hint(raw)
        self.assertEqual(q, f"{stripped} 경기")
        self.assertEqual(canonical_for_code("41"), "경기")

    def test_embedding_lexical_independent(self):
        raw = "강원도 삼척시에서 청년 인턴"
        lex = lexical_terms_for_candidate(raw)
        q = embedding_query_with_region_hint(raw)
        self.assertNotEqual(q, " ".join(lex))

    def test_no_hardcoded_dev_ids_or_new_dict(self):
        import inspect

        src = inspect.getsource(embedding_query_with_region_hint)
        self.assertNotIn("c2d-", src)
        self.assertNotIn("2026", src)
        self.assertIn("_earliest_sido_code", src)
        self.assertIn("canonical_for_code", src)
        src2 = inspect.getsource(_detect_sido_codes)
        self.assertIn("ml_app.SIDO", src2)
        from retrieval_v2.candidate_embedding_region_hint import _earliest_sido_code

        src3 = inspect.getsource(_earliest_sido_code)
        self.assertIn("ml_app.SIDO", src3)
        src4 = inspect.getsource(canonical_for_code)
        self.assertIn("ml_app.SIDO", src4)


if __name__ == "__main__":
    unittest.main()
