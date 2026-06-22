"""
평가셋 생성 — 정책 N개를 뽑아, 각 정책을 찾을 법한 질문을 Gemini로 생성.
질문의 정답(gold) = 그 정책. → eval/evalset.jsonl

이어하기 지원: 이미 생성된 정책은 건너뛰고 append. 429는 백오프 후 재시도.

표준 합성 평가셋 방식. (한계: 문서 파생 질문이라 실제보다 쉬울 수 있음 → 추후 수동 난질문 보강.)
필요: GEMINI_API_KEY
사용법: python make_evalset.py   (중간에 끊겨도 다시 실행하면 이어서 진행)
"""
import os
import json
import random
import time
import pathlib

from dotenv import load_dotenv
from google import genai

ROOT = pathlib.Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY", "").strip())
MODEL = "gemini-3.1-flash-lite"  # 현행 stable lite (별도 쿼터 버킷, 질문 생성에 충분)

INFILE = ROOT / "ingest" / "data" / "youth_policies.jsonl"
OUTFILE = pathlib.Path(__file__).resolve().parent / "evalset.jsonl"
N = 60
SLEEP = 7            # 성공 호출 간격 (무료 10 RPM 아래로)
MAX_RETRY = 4        # 429 백오프 재시도

PROMPT = """다음은 정부 청년정책 설명이다.
이 정책을 모르는 일반 사용자가, 이런 지원이 필요해서 검색창에 칠 법한 자연스러운 한국어 질문 1개만 만들어라.
- 정책명/기관명을 그대로 쓰지 말 것 (사용자는 정책명을 모른다)
- 한 문장, 질문만 출력 (번호·설명·따옴표 없이)

정책명: {title}
요약: {summary}
지원내용: {support}
"""


def gen_query(p):
    for attempt in range(MAX_RETRY):
        try:
            r = client.models.generate_content(
                model=MODEL,
                contents=PROMPT.format(
                    title=p["title"], summary=p.get("summary") or "",
                    support=(p.get("support_content") or "")[:500]),
            )
            return r.text.strip().splitlines()[0].strip().lstrip("0123456789.-) ").strip('"')
        except Exception as e:  # noqa: BLE001
            wait = 20 * (attempt + 1)
            print(f"     API 오류(429 쿼터/503 과부하 등) → {wait}s 대기 후 재시도 ({str(e)[:60]})")
            time.sleep(wait)
    return None


def main():
    if not os.getenv("GEMINI_API_KEY", "").strip():
        raise SystemExit("GEMINI_API_KEY 없음")

    pols = [json.loads(l) for l in INFILE.open(encoding="utf-8")]
    pols = [p for p in pols if (p.get("support_content") or p.get("summary"))]
    random.seed(42)
    sample = random.sample(pols, min(N, len(pols)))

    done = set()
    if OUTFILE.exists():
        for l in OUTFILE.open(encoding="utf-8"):
            done.add(json.loads(l)["gold_source_id"])
    todo = [p for p in sample if p["source_id"] not in done]
    print(f"전체 {len(sample)} / 완료 {len(done)} / 남은 {len(todo)}")

    consecutive_fail = 0
    with OUTFILE.open("a", encoding="utf-8") as f:
        for i, p in enumerate(todo, 1):
            q = gen_query(p)
            if not q:
                consecutive_fail += 1
                print(f"  {i}/{len(todo)}: 실패, 건너뜀")
                if consecutive_fail >= 3:
                    print("\n연속 실패 — 일일 한도(RPD) 소진으로 보임. "
                          "PT 자정 후 다시 실행하면 이어서 진행됨(resume).")
                    break
                continue
            consecutive_fail = 0
            f.write(json.dumps({"query": q, "gold_source_id": p["source_id"],
                                "gold_title": p["title"]}, ensure_ascii=False) + "\n")
            f.flush()
            print(f"  {i}/{len(todo)}: {q}")
            time.sleep(SLEEP)
    print(f"\n완료 → {OUTFILE}")


if __name__ == "__main__":
    main()
