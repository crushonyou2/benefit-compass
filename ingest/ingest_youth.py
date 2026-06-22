"""
온통청년 청년정책 API → 통합 스키마로 정규화 → data/youth_policies.jsonl 저장.

DB 없이도 돌아간다 (전체 코퍼스를 로컬에 먼저 확보). 이후 별도 단계에서 Postgres 적재.

사용법:
    python ingest_youth.py
"""
import os
import json
import pathlib
import time
from urllib.parse import unquote

import requests
from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).resolve().parent.parent / ".env")

YOUTH_KEY = unquote(os.getenv("YOUTH_API_KEY", "").strip())
OUT = pathlib.Path(__file__).resolve().parent / "data"
OUT.mkdir(exist_ok=True)
OUTFILE = OUT / "youth_policies.jsonl"

URL = "https://www.youthcenter.go.kr/go/ythip/getPlcy"
PAGE_SIZE = 100


def _int(v):
    try:
        return int(str(v).strip())
    except (TypeError, ValueError):
        return None


def _date(v):
    """YYYYMMDD(공백 포함 가능) → 'YYYY-MM-DD' 또는 None."""
    s = (v or "").strip()
    return f"{s[:4]}-{s[4:6]}-{s[6:8]}" if len(s) == 8 and s.isdigit() else None


def _regions(v):
    s = (v or "").strip()
    return [c for c in (x.strip() for x in s.split(",")) if c] if s else []


def normalize(p: dict) -> dict:
    """youth 레코드 → 통합 스키마 dict."""
    return {
        "source": "youth",
        "source_id": p.get("plcyNo"),
        "title": p.get("plcyNm"),
        "summary": p.get("plcyExplnCn"),
        "support_content": p.get("plcySprtCn"),
        "keywords": p.get("plcyKywdNm"),
        "category_large": p.get("lclsfNm"),
        "category_mid": p.get("mclsfNm"),
        "org": p.get("sprvsnInstCdNm"),
        "apply_method": p.get("plcyAplyMthdCn"),
        "screening_method": p.get("srngMthdCn"),
        "apply_url": (p.get("aplyUrlAddr") or p.get("refUrlAddr1") or "").strip() or None,
        "submit_docs": p.get("sbmsnDcmntCn"),
        "etc_note": p.get("etcMttrCn"),
        "biz_start": _date(p.get("bizPrdBgngYmd")),
        "biz_end": _date(p.get("bizPrdEndYmd")),
        "apply_period": (p.get("aplyYmd") or "").strip() or None,
        "age_min": _int(p.get("sprtTrgtMinAge")),
        "age_max": _int(p.get("sprtTrgtMaxAge")),
        "age_limit_yn": (p.get("sprtTrgtAgeLmtYn") == "Y"),
        "income_min": _int(p.get("earnMinAmt")),
        "income_max": _int(p.get("earnMaxAmt")),
        "income_cond": p.get("earnCndSeCd"),
        "income_etc": (p.get("earnEtcCn") or "").strip() or None,
        "marriage_status": p.get("mrgSttsCd"),
        "region_codes": _regions(p.get("zipCd")),
        "add_qualify": (p.get("addAplyQlfcCndCn") or "").strip() or None,
        "raw": p,
    }


def fetch_all() -> list:
    records, page = [], 1
    total = None
    while True:
        r = requests.get(
            URL,
            params={"apiKeyNm": YOUTH_KEY, "pageNum": page,
                    "pageSize": PAGE_SIZE, "rtnType": "json"},
            timeout=30,
        )
        r.raise_for_status()
        body = r.json()
        result = body.get("result", {})
        if total is None:
            total = result.get("pagging", {}).get("totCount", 0)
            print(f"총 {total}건 수집 시작")
        batch = result.get("youthPolicyList", []) or []
        if not batch:
            break
        records.extend(batch)
        print(f"  page {page}: +{len(batch)} (누적 {len(records)}/{total})")
        if len(records) >= total:
            break
        page += 1
        time.sleep(0.3)  # 예의상 간격
    return records


if __name__ == "__main__":
    if not YOUTH_KEY:
        raise SystemExit("YOUTH_API_KEY 없음 — .env 확인")
    raw_records = fetch_all()
    with OUTFILE.open("w", encoding="utf-8") as f:
        for p in raw_records:
            f.write(json.dumps(normalize(p), ensure_ascii=False) + "\n")
    print(f"\n완료: {len(raw_records)}건 → {OUTFILE}")
