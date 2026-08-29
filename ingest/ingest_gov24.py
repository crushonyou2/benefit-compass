"""행정안전부 공공서비스(혜택) API v3를 통합 정책 스키마로 정규화한다.

사용법:
    python ingest_gov24.py            # 전체 수집
    python ingest_gov24.py --limit 5  # 연결/필드 검증용 소량 수집
"""
import argparse
import datetime
import json
import os
import pathlib
import re
import time
from urllib.parse import unquote

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:  # 정규화 단위 테스트는 외부 패키지 없이 실행 가능
    load_dotenv = lambda *_args, **_kwargs: None

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

API_KEY = unquote(os.getenv("DATA_GO_KR_KEY", "").strip())
BASE_URL = "https://api.odcloud.kr/api/gov24/v3"
PAGE_SIZE = 100
TIMEOUT = (5, 30)
OUTFILE = pathlib.Path(__file__).resolve().parent / "data" / "gov24_policies.jsonl"

INCOME_CODES = {
    "JA0201": "중위소득 0~50%",
    "JA0202": "중위소득 51~75%",
    "JA0203": "중위소득 76~100%",
    "JA0204": "중위소득 101~200%",
    "JA0205": "중위소득 200% 초과",
}


def _text(value):
    value = str(value or "").strip()
    return value or None


def _int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _active(value):
    return str(value or "").strip().upper() in {"Y", "1", "TRUE"}


def _dates(value):
    found = []
    for year, month, day in re.findall(
        r"(\d{4})\s*(?:[./-]|년)\s*(\d{1,2})\s*(?:[./-]|월)\s*(\d{1,2})",
        str(value or ""),
    ):
        try:
            found.append(datetime.date(int(year), int(month), int(day)).isoformat())
        except ValueError:
            pass
    return found


def _official_url(*candidates):
    for candidate in candidates:
        url = _text(candidate)
        if url and url.startswith(("https://", "http://")):
            return url
    return None


def normalize(list_item, detail=None, condition=None):
    """gov24 목록·상세·지원조건 한 건을 기존 policy 필드로 변환한다."""
    detail = detail or {}
    condition = condition or {}
    source_id = _text(list_item.get("서비스ID") or detail.get("서비스ID"))
    title = _text(list_item.get("서비스명") or detail.get("서비스명"))
    if not source_id or not title:
        raise ValueError("gov24 레코드에 서비스ID 또는 서비스명이 없습니다")

    age_min = _int(condition.get("JA0110"))
    age_max = _int(condition.get("JA0111"))
    valid_age = (
        age_min is not None and age_max is not None
        and 0 <= age_min <= age_max <= 150
        and (age_min, age_max) != (0, 0)
    )
    income = [label for code, label in INCOME_CODES.items() if _active(condition.get(code))]
    target = _text(detail.get("지원대상") or list_item.get("지원대상"))
    criteria = _text(detail.get("선정기준") or list_item.get("선정기준"))
    qualifications = "\n".join(x for x in (target, criteria) if x) or None
    online_url = detail.get("온라인신청사이트URL")
    apply_period = _text(detail.get("신청기한") or list_item.get("신청기한"))
    period_dates = _dates(apply_period)

    return {
        "source": "gov24",
        "source_id": source_id,
        "title": title,
        "summary": _text(list_item.get("서비스목적요약") or detail.get("서비스목적")),
        "support_content": _text(detail.get("지원내용") or list_item.get("지원내용")),
        "keywords": None,
        "category_large": _text(list_item.get("서비스분야")),
        "category_mid": _text(list_item.get("지원유형")),
        "org": _text(detail.get("소관기관명") or list_item.get("소관기관명")),
        "apply_method": _text(detail.get("신청방법") or list_item.get("신청방법")),
        "screening_method": criteria,
        "apply_url": _official_url(online_url, list_item.get("상세조회URL")),
        "submit_docs": _text(detail.get("구비서류")),
        "etc_note": _text(detail.get("문의처") or list_item.get("전화문의")),
        "biz_start": period_dates[0] if len(period_dates) > 1 else None,
        "biz_end": period_dates[-1] if period_dates else None,
        "apply_period": apply_period,
        "age_min": age_min if valid_age else None,
        "age_max": age_max if valid_age else None,
        "age_limit_yn": valid_age,
        "income_min": None,
        "income_max": None,
        "income_cond": ",".join(code for code in INCOME_CODES if _active(condition.get(code))) or None,
        "income_etc": ", ".join(income) or None,
        "marriage_status": None,
        # gov24 v3에는 검증 가능한 지역코드가 없어 지역 필터에 사용하지 않는다.
        "region_codes": [],
        "add_qualify": qualifications,
        "raw": {"serviceList": list_item, "serviceDetail": detail, "supportConditions": condition},
    }


class Gov24Client:
    def __init__(self, api_key, session=None):
        if not api_key:
            raise ValueError("DATA_GO_KR_KEY가 없습니다")
        import requests

        self.requests = requests
        self.session = session or requests.Session()
        self.headers = {"Authorization": f"Infuser {api_key}"}

    def _page(self, endpoint, params):
        try:
            response = self.session.get(
                f"{BASE_URL}/{endpoint}", params=params, headers=self.headers, timeout=TIMEOUT
            )
            response.raise_for_status()
        except self.requests.RequestException as exc:
            failed_response = getattr(exc, "response", None)
            status = getattr(failed_response, "status_code", "network")
            raise RuntimeError(f"gov24 {endpoint} 요청 실패(status={status})") from exc
        try:
            body = response.json()
        except ValueError as exc:
            raise RuntimeError(
                f"gov24 {endpoint} 응답 JSON이 올바르지 않습니다(status={response.status_code})"
            ) from exc
        if not isinstance(body, dict) or not isinstance(body.get("data"), list):
            raise RuntimeError(f"gov24 {endpoint} 응답 형식이 올바르지 않습니다")
        time.sleep(0.1)
        return body

    def fetch_all(self, endpoint, limit=None):
        records = []
        page = 1
        while limit is None or len(records) < limit:
            body = self._page(endpoint, {"page": page, "perPage": PAGE_SIZE})
            batch = body["data"]
            records.extend(batch)
            total = _int(body.get("totalCount"))
            if not batch or (total is not None and len(records) >= total):
                break
            page += 1
        return records[:limit] if limit is not None else records

    def fetch_one(self, endpoint, source_id):
        body = self._page(
            endpoint,
            {"page": 1, "perPage": 1, "cond[서비스ID::EQ]": source_id},
        )
        if not body["data"]:
            return {}
        item = body["data"][0]
        if item.get("서비스ID") != source_id:
            raise RuntimeError(f"gov24 {endpoint} 서비스ID가 요청과 다릅니다")
        return item


def collect(client, limit=None):
    listed = client.fetch_all("serviceList", limit=limit)
    if limit is not None:
        details = {
            item["서비스ID"]: client.fetch_one("serviceDetail", item["서비스ID"])
            for item in listed if item.get("서비스ID")
        }
        conditions = {
            item["서비스ID"]: client.fetch_one("supportConditions", item["서비스ID"])
            for item in listed if item.get("서비스ID")
        }
    else:
        details = {x.get("서비스ID"): x for x in client.fetch_all("serviceDetail")}
        conditions = {x.get("서비스ID"): x for x in client.fetch_all("supportConditions")}

    policies, skipped, seen = [], 0, set()
    for item in listed:
        source_id = item.get("서비스ID")
        try:
            policy = normalize(item, details.get(source_id), conditions.get(source_id))
        except ValueError:
            skipped += 1
            continue
        if policy["source_id"] in seen:
            skipped += 1
            continue
        policies.append(policy)
        seen.add(policy["source_id"])
    return policies, skipped


def write_jsonl(policies, path=OUTFILE):
    path.parent.mkdir(exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        for policy in policies:
            stream.write(json.dumps(policy, ensure_ascii=False) + "\n")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="소량 연결 검증 시 수집할 최대 정책 수")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        raise SystemExit("--limit은 1 이상이어야 합니다")
    if not API_KEY:
        raise SystemExit("DATA_GO_KR_KEY 없음 — .env 확인")

    policies, skipped = collect(Gov24Client(API_KEY), args.limit)
    if not policies:
        raise SystemExit("gov24에서 유효한 정책을 받지 못했습니다")
    write_jsonl(policies)
    print(f"완료: {len(policies)}건 저장, 필수값 누락 {skipped}건 제외 → {OUTFILE}")


if __name__ == "__main__":
    main()
