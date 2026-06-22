"""
혜택나침반 — 공공데이터 API 연결 검증 프로브.

목적: 발급한 키로 각 API가 실제로 응답하는지 확인하고, 원시 응답을 samples/ 에 저장한다.
      이 출력을 보고 DB 스키마와 파서를 확정한다. (지금은 "스키마 추측 금지" 단계)

사용법:
    pip install -r requirements.txt
    # 프로젝트 루트의 .env 에 키 입력 후
    python probe.py
"""
import os
import pathlib
from urllib.parse import unquote

import requests
from dotenv import load_dotenv

load_dotenv(pathlib.Path(__file__).resolve().parent.parent / ".env")

SAMPLES = pathlib.Path(__file__).resolve().parent / "samples"
SAMPLES.mkdir(exist_ok=True)

_RAW_KEY = os.getenv("DATA_GO_KR_KEY", "").strip()
# 키가 이미 URL 인코딩돼 있어도(%2B 등) unquote로 한 번 풀어두면,
# requests가 params로 넘길 때 정확히 한 번만 인코딩한다 (이중 인코딩 방지).
DATA_KEY = unquote(_RAW_KEY)
YOUTH_KEY = unquote(os.getenv("YOUTH_API_KEY", "").strip())

if _RAW_KEY:
    print(f"[키] 입력 키 길이={len(_RAW_KEY)}, "
          f"{'인코딩된 키로 보임 → 디코딩 적용' if '%' in _RAW_KEY else '디코딩 키로 보임 → 그대로 사용'}")


def save(name: str, text: str) -> None:
    (SAMPLES / name).write_text(text, encoding="utf-8")
    print(f"   saved -> samples/{name}")


def show_keys(label: str, items: list) -> None:
    if items and isinstance(items[0], dict):
        print(f"   {label} 첫 항목 필드: {list(items[0].keys())}")


def probe_gov24() -> None:
    """행안부 공공서비스(혜택) gov24 — JSON, 일 10,000. 주력 코퍼스."""
    print("\n[1] 행안부 gov24 (JSON, 일 10,000)")
    if not DATA_KEY:
        print("   SKIP: DATA_GO_KR_KEY 없음")
        return
    base = "https://api.odcloud.kr/api/gov24/v3"
    # odcloud(api.odcloud.kr)는 apis.data.go.kr과 게이트웨이가 다르다.
    # serviceKey 쿼리파라미터가 아니라 Authorization: Infuser {디코딩 키} 헤더로 인증한다.
    headers = {"Authorization": f"Infuser {DATA_KEY}"}
    # 3개 테이블 각각 1페이지만 받아 구조 확인 (목록 / 상세 / 자격조건)
    for ep in ("serviceList", "serviceDetail", "supportConditions"):
        try:
            r = requests.get(
                f"{base}/{ep}",
                params={"page": 1, "perPage": 5},
                headers=headers,
                timeout=20,
            )
            print(f"   {ep}: status={r.status_code}")
            save(f"gov24_{ep}.json", r.text)
            if r.status_code == 200:
                data = r.json()
                items = data.get("data") or []
                print(f"      totalCount={data.get('totalCount')} / 받은 {len(items)}건")
                show_keys(ep, items)
            else:
                print(f"      본문: {r.text[:200]}")
        except Exception as e:  # noqa: BLE001
            print(f"   {ep}: 오류 {e}")


def probe_welfare() -> None:
    """사회보장정보원 중앙부처복지서비스 — XML, 개발계정 일 100. 본문 보강용."""
    print("\n[2] 사회보장정보원 복지서비스 (XML, 일 100)")
    if not DATA_KEY:
        print("   SKIP: DATA_GO_KR_KEY 없음")
        return
    url = ("https://apis.data.go.kr/B554287/NationalWelfareInformationsV001/"
           "NationalWelfarelistV001")
    # 파라미터명이 명세 확인 전이라 best-effort. 실패 시 응답 XML이 필수 파라미터를 알려준다.
    try:
        r = requests.get(
            url,
            params={"serviceKey": DATA_KEY, "pageNo": 1, "numOfRows": 5, "callTp": "L"},
            timeout=20,
        )
        print(f"   목록조회: status={r.status_code}")
        save("welfare_list.xml", r.text)
        print(f"      앞부분: {r.text[:300]}")
    except Exception as e:  # noqa: BLE001
        print(f"   오류 {e}")


def probe_youth() -> None:
    """온통청년 청년정책 — JSON, 일 2,219. 선택(청년 세그먼트)."""
    print("\n[3] 온통청년 청년정책 (JSON, 일 2,219)")
    if not YOUTH_KEY:
        print("   SKIP: YOUTH_API_KEY 없음")
        return
    # 최신 엔드포인트 best-effort. 실패 시 응답으로 정확한 파라미터 확인.
    url = "https://www.youthcenter.go.kr/go/ythip/getPlcy"
    try:
        r = requests.get(
            url,
            params={"apiKeyNm": YOUTH_KEY, "pageNum": 1, "pageSize": 5, "rtnType": "json"},
            timeout=20,
        )
        print(f"   정책조회: status={r.status_code}")
        save("youth_list.json", r.text)
        print(f"      앞부분: {r.text[:300]}")
    except Exception as e:  # noqa: BLE001
        print(f"   오류 {e}")


if __name__ == "__main__":
    print("=== 혜택나침반 API 프로브 ===")
    probe_gov24()
    probe_welfare()
    probe_youth()
    print("\n완료. samples/ 의 파일과 위 출력을 공유해줘 → 스키마/파서 확정.")
