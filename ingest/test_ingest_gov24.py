import json
import pathlib
import unittest

from ingest_gov24 import Gov24Client, collect, normalize


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

    def test_falls_back_to_official_detail_when_online_url_has_no_scheme(self):
        policy = normalize(
            {
                "서비스ID": "TEST-4",
                "서비스명": "공식 링크 정책",
                "상세조회URL": "https://www.gov.kr/portal/rcvfvrSvc/dtlEx/TEST-4",
            },
            {"온라인신청사이트URL": "www.example.go.kr/apply"},
        )

        self.assertEqual(
            "https://www.gov.kr/portal/rcvfvrSvc/dtlEx/TEST-4", policy["apply_url"]
        )

    def test_collect_joins_endpoints_and_deduplicates(self):
        service_id = self.sample["serviceList"]["서비스ID"]

        class FakeClient:
            def fetch_all(inner_self, endpoint, limit=None):
                records = {
                    "serviceList": [
                        self.sample["serviceList"],
                        self.sample["serviceList"],
                        {"서비스명": "식별자 없는 정책"},
                    ],
                    "serviceDetail": [self.sample["serviceDetail"]],
                    "supportConditions": [self.sample["supportConditions"]],
                }
                return records[endpoint]

        policies, skipped = collect(FakeClient())

        self.assertEqual(1, len(policies))
        self.assertEqual(2, skipped)
        self.assertEqual(service_id, policies[0]["source_id"])
        self.assertEqual(
            self.sample["serviceDetail"], policies[0]["raw"]["serviceDetail"]
        )
        self.assertEqual(
            self.sample["supportConditions"], policies[0]["raw"]["supportConditions"]
        )

    def test_collect_deduplicates_ids_after_normalization(self):
        class FakeClient:
            def fetch_all(inner_self, endpoint, limit=None):
                records = {
                    "serviceList": [
                        {"서비스ID": " X ", "서비스명": "공백 포함 정책"},
                        {"서비스ID": "X", "서비스명": "정규화 후 중복 정책"},
                    ],
                    "serviceDetail": [],
                    "supportConditions": [],
                }
                return records[endpoint]

        policies, skipped = collect(FakeClient())

        self.assertEqual(["X"], [policy["source_id"] for policy in policies])
        self.assertEqual(1, skipped)

    def test_network_failure_has_safe_error_without_response_object(self):
        class FakeRequests:
            class RequestException(Exception):
                pass

        class FailingSession:
            def get(inner_self, *_args, **_kwargs):
                raise FakeRequests.RequestException("private transport detail")

        client = object.__new__(Gov24Client)
        client.requests = FakeRequests
        client.session = FailingSession()
        client.headers = {"Authorization": "hidden"}

        with self.assertRaisesRegex(RuntimeError, r"serviceList 요청 실패\(status=network\)"):
            client._page("serviceList", {"page": 1})


if __name__ == "__main__":
    unittest.main()
