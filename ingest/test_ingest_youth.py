import unittest

from ingest_youth import _official_url, normalize


class YouthUrlSelectionTest(unittest.TestCase):
    def test_first_candidate_valid_https_is_selected(self):
        self.assertEqual(
            "https://youth.seoul.go.kr",
            _official_url("https://youth.seoul.go.kr", "https://www.busan.go.kr"),
        )

    def test_first_empty_second_valid_is_selected(self):
        self.assertEqual(
            "https://www.busan.go.kr/depart/reguarantee01",
            _official_url("", "https://www.busan.go.kr/depart/reguarantee01"),
        )
        self.assertEqual(
            "https://example.test/second",
            _official_url("   ", "https://example.test/second"),
        )
        self.assertEqual(
            "https://example.test/second",
            _official_url(None, "https://example.test/second"),
        )

    def test_first_non_http_second_valid_is_selected(self):
        # 핵심 regression: 16건 bug
        self.assertEqual(
            "https://www.busan.go.kr/depart/reguarantee01",
            _official_url("www.khug.or.kr/jeonse/index.js", "https://www.busan.go.kr/depart/reguarantee01"),
        )
        self.assertEqual(
            "https://jejuyouthdream.com/policy/detail/103",
            _official_url("-", "https://jejuyouthdream.com/policy/detail/103"),
        )
        self.assertEqual(
            "https://jejuyouthdream.com/policy/detail/69",
            _official_url("추후 공지", "https://jejuyouthdream.com/policy/detail/69"),
        )

    def test_both_invalid_returns_none(self):
        self.assertIsNone(_official_url("www.khug.or.kr/jeonse/index.js", "www.bokjiro.go.kr"))
        self.assertIsNone(_official_url("www.example.com", "www.example.com"))
        self.assertIsNone(_official_url("-", "추후 공지"))
        self.assertIsNone(_official_url("   ", "   "))

    def test_both_empty_returns_none(self):
        self.assertIsNone(_official_url("", ""))
        self.assertIsNone(_official_url(None, None))
        self.assertIsNone(_official_url("", None))
        self.assertIsNone(_official_url(None, ""))

    def test_normalize_preserves_other_fields(self):
        base = {
            "plcyNo": "TEST-001",
            "plcyNm": "청년 테스트 정책",
            "plcyExplnCn": "설명",
            "plcySprtCn": "지원내용",
            "sprvsnInstCdNm": "테스트기관",
            "sprtTrgtMinAge": "19",
            "sprtTrgtMaxAge": "34",
            "sprtTrgtAgeLmtYn": "Y",
            "zipCd": "11, 26",
        }
        # valid first
        p1 = {**base, "aplyUrlAddr": "https://youth.seoul.go.kr", "refUrlAddr1": "https://www.busan.go.kr"}
        self.assertEqual("https://youth.seoul.go.kr", normalize(p1)["apply_url"])
        self.assertEqual("청년 테스트 정책", normalize(p1)["title"])
        self.assertEqual([19, 34], [normalize(p1)["age_min"], normalize(p1)["age_max"]])
        self.assertEqual(["11", "26"], normalize(p1)["region_codes"])

        # non-http first, valid second
        p2 = {**base, "aplyUrlAddr": "www.khug.or.kr/jeonse/index.js", "refUrlAddr1": "https://www.busan.go.kr/depart/reguarantee01"}
        self.assertEqual("https://www.busan.go.kr/depart/reguarantee01", normalize(p2)["apply_url"])

        # both invalid
        p3 = {**base, "aplyUrlAddr": "www.example.com", "refUrlAddr1": "www.example.com"}
        self.assertIsNone(normalize(p3)["apply_url"])

    def test_normalize_with_real_16case_shape(self):
        # 실제 16건 중 대표 raw shape (개인정보 없는 최소 필드)
        raw = {
            "plcyNo": "20260513005400213187",
            "plcyNm": "부산 전세보증금 반환보증 보증료 지원",
            "aplyUrlAddr": "www.khug.or.kr/jeonse/index.js",
            "refUrlAddr1": "https://www.busan.go.kr/depart/reguarantee01",
            "refUrlAddr2": "",
            "sprtTrgtMinAge": "19",
            "sprtTrgtMaxAge": "39",
            "sprtTrgtAgeLmtYn": "Y",
            "zipCd": "26",
        }
        policy = normalize(raw)
        self.assertEqual("https://www.busan.go.kr/depart/reguarantee01", policy["apply_url"])
        self.assertEqual("20260513005400213187", policy["source_id"])


if __name__ == "__main__":
    unittest.main()
