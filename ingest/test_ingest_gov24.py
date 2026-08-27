import json
import pathlib
import unittest

from ingest_gov24 import normalize


class Gov24NormalizeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fixture = pathlib.Path(__file__).resolve().parent / "fixtures" / "gov24_sample.json"
        cls.sample = json.loads(fixture.read_text(encoding="utf-8"))

    def test_maps_official_fields_to_shared_schema(self):
        policy = normalize(
            self.sample["serviceList"],
            self.sample["serviceDetail"],
            self.sample["supportConditions"],
        )

        self.assertEqual("gov24", policy["source"])
        self.assertEqual("TEST-GOV24-001", policy["source_id"])
        self.assertEqual("전 국민 생활안정 지원", policy["title"])
        self.assertEqual((19, 64, True),
                         (policy["age_min"], policy["age_max"], policy["age_limit_yn"]))
        self.assertEqual("중위소득 0~50%", policy["income_etc"])
        self.assertEqual([], policy["region_codes"])
        self.assertTrue(policy["apply_url"].startswith("https://www.gov.kr/"))
        self.assertEqual(self.sample["serviceList"], policy["raw"]["serviceList"])

    def test_rejects_missing_stable_identifier(self):
        with self.assertRaisesRegex(ValueError, "서비스ID"):
            normalize({"서비스명": "식별자 없는 정책"})

    def test_does_not_invent_invalid_age_or_region(self):
        policy = normalize(
            {"서비스ID": "TEST-2", "서비스명": "전국 정책"},
            condition={"JA0110": 70, "JA0111": 20},
        )
        self.assertIsNone(policy["age_min"])
        self.assertFalse(policy["age_limit_yn"])
        self.assertEqual([], policy["region_codes"])

    def test_extracts_only_explicit_application_dates(self):
        policy = normalize(
            {"서비스ID": "TEST-3", "서비스명": "기간 정책",
             "신청기한": "2026. 1. 2. ~ 2026. 12. 31."}
        )
        self.assertEqual("2026-01-02", policy["biz_start"])
        self.assertEqual("2026-12-31", policy["biz_end"])


if __name__ == "__main__":
    unittest.main()
