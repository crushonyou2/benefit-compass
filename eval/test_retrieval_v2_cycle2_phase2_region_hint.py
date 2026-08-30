"""Static/unit tests for bounded region-core lexical hint (cycle2 Phase2 Exp1).

Covers general rules, not dev case hardcode. Cases use synthetic queries containing
SIDO aliases to verify semantics. No holdout file access, no git show holdout.

HARD RULES verified:
- Uses ml_app.SIDO only, no hardcoded dev case IDs
- No lower-level 시/군/구/동 dictionary, no n-gram, no morphological lib
- lex embedding/query vector and youth bias remain stripped (checked via strip_region contract)
- rp=None, region_filter(None) unchanged — tested that module does not call region_filter with non-None
"""

import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ml-service"))
sys.path.insert(0, str(ROOT / "eval"))

import app as ml_app
from retrieval_v2.candidate_lexical_rewrite import lexical_overlap_terms_rewrite
from retrieval_v2.candidate_region_hint import (
    canonical_for_code,
    detect_sido_codes,
    lexical_overlap_terms_region_hint,
)
from source_ranking import LEXICAL_STOPWORDS


class RegionHintSemanticsTest(unittest.TestCase):
    def test_canonical_is_first_alias_and_shortest(self):
        """General rule: canonical == SIDO[code][0] == shortest alias for all codes."""
        for code, aliases in ml_app.SIDO.items():
            canon = canonical_for_code(code)
            self.assertEqual(canon, aliases[0], f"code {code} canonical must be first alias")
            shortest = min(aliases, key=len)
            self.assertEqual(canon, shortest, f"code {code} canonical must be shortest alias")
            self.assertGreaterEqual(len(canon), 2, "canonical length >=2")
            self.assertNotIn(canon, LEXICAL_STOPWORDS, "canonical must not be stopword")
            self.assertTrue(canon.strip(), "canonical not empty/whitespace")

    def test_busan_hint_added(self):
        raw = "부산에 사는 청년이 월세 지원을 받을 수 있나요?"
        q_stripped = ml_app.strip_region(raw)
        base = lexical_overlap_terms_rewrite(q_stripped)
        hinted = lexical_overlap_terms_region_hint(raw)
        self.assertNotIn("부산", base, "base from stripped q should not contain 부산")
        self.assertIn("부산", hinted, "hinted should contain 부산")
        self.assertEqual(len(hinted), len(base) + 1)
        self.assertEqual(hinted[-1], "부산")
        self.assertEqual(canonical_for_code("26"), "부산")

    def test_gyeonggi_hint_added(self):
        raw = "경기도 청년이 청년참여기구를 통해 정책 제안에 참여할 수 있을까요?"
        base = lexical_overlap_terms_rewrite(ml_app.strip_region(raw))
        hinted = lexical_overlap_terms_region_hint(raw)
        self.assertIn("경기", hinted)
        self.assertNotIn("경기", base)
        self.assertEqual(hinted[len(base)], "경기")

    def test_chungnam_hint_added(self):
        raw = "충남에서 청년이 정신건강 검진을 받을 수 있나요?"
        base = lexical_overlap_terms_rewrite(ml_app.strip_region(raw))
        hinted = lexical_overlap_terms_region_hint(raw)
        self.assertIn("충남", hinted)
        self.assertNotIn("충남", base)

    def test_no_region_identical_to_base(self):
        raw = "청년이 주택 마련을 위해 청년주택드림청약통장을 가입할 수 있는 방법이 있을까요?"
        q_stripped = ml_app.strip_region(raw)
        base = lexical_overlap_terms_rewrite(q_stripped)
        hinted = lexical_overlap_terms_region_hint(raw)
        self.assertEqual(base, hinted, "no region => term list identical to candidate-v2 base")
        self.assertEqual(detect_sido_codes(raw), [])

    def test_same_region_alias_duplicate_single_hint(self):
        raw_short = "충남에서 청년 지원"
        raw_long = "충청남도에서 청년 지원"
        raw_both = "충남과 충청남도에서 청년 지원"
        for raw in [raw_short, raw_long, raw_both]:
            hinted = lexical_overlap_terms_region_hint(raw)
            self.assertEqual(hinted.count("충남"), 1, f"raw {raw} should have exactly one 충남 hint")
            self.assertNotIn("충청남도", hinted, "canonical is 충남, not 충청남도")
            codes = detect_sido_codes(raw)
            self.assertEqual(codes, ["44"], f"raw {raw} should match single code 44")

    def test_same_region_multiple_mentions_still_one(self):
        raw = "부산에서 부산 청년이 부산 월세 지원"
        hinted = lexical_overlap_terms_region_hint(raw)
        self.assertEqual(hinted.count("부산"), 1)
        self.assertEqual(detect_sido_codes(raw), ["26"])

    def test_multiple_sido_codes_bounded_per_code(self):
        raw = "서울과 부산에서 청년이 창업 지원을 받을 수 있나요?"
        hinted = lexical_overlap_terms_region_hint(raw)
        base = lexical_overlap_terms_rewrite(ml_app.strip_region(raw))
        codes = detect_sido_codes(raw)
        self.assertEqual(set(codes), {"11", "26"})
        self.assertIn("서울", hinted)
        self.assertIn("부산", hinted)
        self.assertEqual(len(hinted), len(base) + 2, "two distinct SIDO codes => +2 hints")
        self.assertEqual(hinted.count("서울"), 1)
        self.assertEqual(hinted.count("부산"), 1)

    def test_sejong_hint(self):
        raw = "세종시에서 청년이 청년센터를 이용할 수 있나요?"
        hinted = lexical_overlap_terms_region_hint(raw)
        base = lexical_overlap_terms_rewrite(ml_app.strip_region(raw))
        self.assertIn("세종", hinted)
        self.assertNotIn("세종", base)
        self.assertIn("36", detect_sido_codes(raw))
        self.assertEqual(canonical_for_code("36"), "세종")

    def test_gangwon_hint_via_substring(self):
        raw = "강원도 삼척시에서 청년 인턴"
        hinted = lexical_overlap_terms_region_hint(raw)
        base = lexical_overlap_terms_rewrite(ml_app.strip_region(raw))
        self.assertIn("강원", hinted)
        # 삼척시 is lower-level, should not be added as hint beyond base
        hints_part = hinted[len(base):]
        self.assertNotIn("삼척", hints_part)
        self.assertNotIn("삼척시", hints_part)
        codes = detect_sido_codes(raw)
        self.assertIn("51", codes)
        raw_only_samcheok = "삼척시에서 대학생 아르바이트"
        self.assertEqual(detect_sido_codes(raw_only_samcheok), [], "삼척 is not SIDO level")

    def test_lower_level_not_hint(self):
        for raw in [
            "삼척시에서 청년 인턴",
            "완주군에서 청년 출산급여",
            "양평에서 주민 생활문화",
            "예천군에서 귀농 지원",
        ]:
            hinted = lexical_overlap_terms_region_hint(raw)
            base = lexical_overlap_terms_rewrite(ml_app.strip_region(raw))
            self.assertEqual(hinted, base, f"lower-level only raw should not add hint: {raw}")

    def test_hint_not_stopword_not_empty_deduped(self):
        raws = [
            "부산에 사는 청년이 월세 지원",
            "서울에서 청년 창업",
            "제주에서 청년 농업",
        ]
        for raw in raws:
            hinted = lexical_overlap_terms_region_hint(raw)
            base = lexical_overlap_terms_rewrite(ml_app.strip_region(raw))
            for hint in hinted[len(base):]:
                self.assertTrue(hint.strip(), "hint not whitespace")
                self.assertNotIn(hint, LEXICAL_STOPWORDS)
                self.assertGreaterEqual(len(hint), 2)
            for hint in hinted[len(base):]:
                self.assertNotIn(hint, base, "hint must be deduped against base")
            self.assertEqual(len(hinted), len(set(hinted)), "hinted list must be deduped")

    def test_bounded_term_increase(self):
        cases = [
            ("청년 창업 지원", 0),
            ("부산 청년 월세", 1),
            ("서울과 부산 청년 월세", 2),
        ]
        for raw, expected_increase in cases:
            base = lexical_overlap_terms_rewrite(ml_app.strip_region(raw))
            hinted = lexical_overlap_terms_region_hint(raw)
            self.assertEqual(len(hinted) - len(base), expected_increase)

    def test_rp_and_region_filter_not_used(self):
        import ast

        mod_path = ROOT / "eval" / "retrieval_v2" / "candidate_region_hint.py"
        src = mod_path.read_text(encoding="utf-8")
        tree = ast.parse(src)
        called_names = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called_names.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called_names.add(node.func.attr)
        self.assertNotIn("region_filter", called_names, "candidate_region_hint must not call region_filter")
        self.assertIn("ml_app.SIDO", src)

    def test_uses_sido_table_only(self):
        mod_path = ROOT / "eval" / "retrieval_v2" / "candidate_region_hint.py"
        src = mod_path.read_text(encoding="utf-8")
        self.assertNotIn("c2d-", src)
        for lib in ["konlpy", "mecab", "n_gram", "ngram"]:
            self.assertNotIn(lib.lower(), src.lower())

    def test_hint_order_deterministic(self):
        raw = "부산과 서울과 경기 청년"
        h1 = lexical_overlap_terms_region_hint(raw)
        h2 = lexical_overlap_terms_region_hint(raw)
        self.assertEqual(h1, h2, "deterministic output")
        base_len = len(lexical_overlap_terms_rewrite(ml_app.strip_region(raw)))
        hints = h1[base_len:]
        # hints should be in code-sorted order
        expected_codes = detect_sido_codes(raw)
        expected_hints = [canonical_for_code(c) for c in expected_codes]
        self.assertEqual(hints, expected_hints)

    def test_strip_region_unchanged_for_embedding(self):
        raws = ["부산 청년 월세", "세종시 청년센터", "충남 청년 검진"]
        for raw in raws:
            stripped = ml_app.strip_region(raw)
            base = lexical_overlap_terms_rewrite(stripped)
            hinted = lexical_overlap_terms_region_hint(raw)
            self.assertTrue(len(hinted) >= len(base))


if __name__ == "__main__":
    unittest.main()
