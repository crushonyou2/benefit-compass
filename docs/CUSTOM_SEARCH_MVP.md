# Custom Search MVP 검증 기록

기준일: 2026-08-27

## 데이터 소스 게이트

| 후보 | 공식 범위·이용 조건 | 필요한 검색 필드 | MVP 판정 |
|---|---|---|---|
| 행정안전부 대한민국 공공서비스(혜택) 정보 | 중앙부처·지자체·공공기관·교육청, 전국, REST JSON/XML, 무료, 개발계정 일 10,000회, 자동승인 | 서비스 ID, 정책명, 목적, 지원대상·선정기준·지원내용, 신청기한·방법·공식 상세 URL, 기관, 수정일, 구조화 연령·소득 조건 | **선택** |
| 한국사회보장정보원 복지서비스정보 | 중앙부처 복지서비스, 무료 OpenAPI | 서비스 ID·명·URL·요약·기관·기준연도·수정일은 제공하지만 공개 목록 설명상 상세 지원내용·대상·신청기한 필드가 부족 | 보류 |

선택 근거는 범위와 필드 완전성이다. 정부24 API는 기존 청년정책 밖의 일반 국민 정책과 지역 정책을 한 출처에서 다루고, 현재 `policy` 스키마에 필요한 주요 필드를 제공한다. 새 저장소, 크롤러, 검색 인프라 없이 기존 e5·pgvector·리랭커 경로에 합칠 수 있다.

공식 근거:

- [공공데이터포털 API 정보](https://www.data.go.kr/data/15113968/openapi.do): 무료, 이용허락 제한 없음, 개발·운영 자동승인, 개발계정 일 10,000회
- [2025년 v3 상세 필드 변경 공지](https://www.data.go.kr/bbs/ntc/selectNotice.do?originId=NOTICE_0000000004156): `/gov24/v3/serviceDetail` 유지 및 구비서류 필드 추가
- [정부24 실제 서비스 상세 예시](https://www.gov.kr/portal/rcvfvrSvc/dtlEx/B55190400005): 지원대상·지원내용·신청방법·기관·최종수정일과 공식 신청 경로 확인

현재 접근 검증에서는 무인증 `serviceList?page=1&perPage=1` 요청이 `401`과 `인증키는 필수 항목`을 반환했다. 즉 엔드포인트는 응답하지만 실제 데이터 200 응답은 활용신청된 `DATA_GO_KR_KEY`가 있어야 검증할 수 있다. 저장소와 프로세스 환경에는 키가 없었다.

## 정규화 계약

`ingest/ingest_gov24.py`는 `serviceList`, `serviceDetail`, `supportConditions`를 `서비스ID`로 결합한다.

| 통합 필드 | gov24 원본 |
|---|---|
| `source`, `source_id` | 고정값 `gov24`, `서비스ID` |
| `title`, `summary` | `서비스명`, `서비스목적요약` 또는 `서비스목적` |
| `support_content` | 상세 또는 목록의 `지원내용` |
| `org` | `소관기관명` |
| `apply_method`, `apply_period` | `신청방법`, `신청기한` |
| `apply_url` | `온라인신청사이트URL`, 없으면 `상세조회URL`; 둘 다 없으면 추측하지 않고 `null` |
| `age_min`, `age_max` | 지원조건 `JA0110`, `JA0111`; 정상 범위일 때만 연령 필터 활성화 |
| `income_etc` | `JA0201`~`JA0205`의 활성 중위소득 구간 |
| `add_qualify` | `지원대상` + `선정기준` |
| `region_codes` | 빈 배열 |
| `raw` | 세 원본 레코드를 분리해 그대로 보존 |

만료 처리는 `신청기한`에 명시적인 날짜가 있을 때만 날짜를 추출해 `biz_end`로 저장하고 기존 검색 SQL에서 지난 정책을 제외한다. `상시신청`, 기관별 상이처럼 날짜가 없는 문구는 임의 만료일을 만들지 않고 원문만 보존한다.

필수 ID나 정책명이 없으면 제외하고, HTTP 타임아웃·비정상 상태·JSON/응답 구조 오류는 안전한 오류 메시지로 중단한다. 출력은 임시 파일을 완성한 뒤 교체하므로 실패한 수집이 기존 코퍼스를 덮어쓰지 않는다.

`embed.py`와 `load_db.py`는 `*_policies.jsonl`을 함께 처리한다. DB 적재는 `(source, source_id)` UPSERT로 모든 정규화 필드를 갱신하고, 해당 정책의 청크를 한 트랜잭션에서 교체한다.

## 검색·답변 계약

- ML 검색 결과는 `source`, `source_id`, 공식 링크를 함께 반환한다.
- Java API와 React 화면은 기존 필드를 유지하면서 출처 배지만 추가한다.
- `/api/ask`는 기존 `answer`·`sources`에 하위 호환되는 `generated` 불리언을 추가해 실제 LLM 호출 여부를 노출한다.
- Gemini 프롬프트에는 검색된 정책의 이름·출처·지원내용·공식 링크만 들어간다.
- 검색 결과가 0건이면 Gemini를 호출하지 않는다.
- `(source, source_id)`로 평가해 출처 간 ID 충돌을 피한다.
- `region`이 들어온 공개 API 요청은 기존과 같이 400으로 거절한다.

## 지역 데이터 판정

gov24 v3 공식 Swagger에는 서비스의 행정 지역코드가 없다. `소관기관코드`·`소관기관유형`·기관명은 서비스 적용 지역과 같은 의미라고 검증되지 않았으므로 지역코드로 변환하지 않았다. 전국, 특정 지역, 지역 확인 불가를 안정적으로 구분할 표본도 아직 없다.

따라서 이번 변경은 gov24 정책의 `region_codes`를 빈 배열로 저장하고 지역 필터를 노출하지 않는다. `run_data_quality.py`는 출처별 지역코드 보유 건수를 기록하지만, 이것은 지역 정확도 증거가 아니다.

## 평가 상태

측정된 기존 기준값은 청년정책 60문항의 저장된 결과다.

| 지표 | bi-encoder | 리랭킹 |
|---|---:|---:|
| Recall@1 | 0.4000 | 0.5167 |
| Recall@5 | 0.7333 | 0.7167 |
| MRR@10 | 0.5346 | 0.6135 |

이번 환경에는 `DATABASE_URL`, 모델 실행 환경, gov24 인증키가 없어 같은 조건의 기준값 재측정과 확장 후 측정을 실행하지 못했다. 따라서 위 숫자는 **기존 청년정책 기준값**일 뿐, 복수 출처 개선 수치가 아니다.

확장 평가 라벨은 실제 gov24 전체 코퍼스를 받은 뒤 다음 유형을 포함해 먼저 고정해야 한다: 일반 국민, 가구·주거, 취업·소득, 복지·건강, 전국, 지역, 비대상 조건, 정답 없음, 출처 간 유사 정책. 실제 코퍼스에 존재하는 서비스 ID를 확인하기 전에 정답을 추측해 넣지 않는다.

평가 도구는 출처를 포함한 gold key와 출처별 Recall/MRR를 기록하도록 바뀌었다. `run_data_quality.py`는 출처별 정책 수, 공식 링크 누락, 지역코드 보유, 임베딩 누락, 출처 간 동일 제목 수를 저장한다.

## 재현 절차와 남은 게이트

```powershell
cd ingest
python ingest_gov24.py --limit 5
python ingest_gov24.py
python embed.py
python load_db.py

cd ..
python eval/run_data_quality.py
python eval/run_eval.py
python eval/run_eval_rerank.py
```

기존 60문항과 확장 평가셋의 결과를 덮어쓰지 않으려면 파일을 명시한다.

```powershell
python eval/run_eval.py --eval-file eval/expansion_evalset.jsonl --output eval/results_expansion.json
python eval/run_eval_rerank.py --eval-file eval/expansion_evalset.jsonl --baseline eval/results_expansion.json --output eval/results_expansion_rerank.json
python eval/run_api_eval.py --eval-file eval/expansion_evalset.jsonl --output eval/results_expansion_api.json
```

두 평가기는 빈 파일과 `query`·`gold_source_id` 누락을 실행 전에 거절하고, 결과 JSON에 사용한 평가 파일 경로를 기록한다. 기존 청년정책 라벨은 `gold_source`가 없으면 `youth`로 해석해 이전 평가셋과 호환한다. 확장 평가셋에는 `gold_source`를 반드시 명시한다.

API 통합 평가셋의 검색 정답 문항은 `gold_source`·`gold_source_id`를, 정답 없음 문항은 `expected_no_results: true`를 사용한다. 선택 필드 `case_type`으로 일반 국민·가구/주거·취업/소득·복지/건강·전국·지역·비대상·출처 간 유사 정책을 구분한다. 평가기는 Recall@1/5·MRR·출처별/유형별 성공률과 함께 정답 없음 오탐, 공식 링크 누락, `sources` 없이 LLM이 호출된 건수를 저장한다.

아직 완료되지 않은 항목:

- 활용신청된 키로 v3 세 엔드포인트의 200 응답과 원본 필드 표본 검증
- 전체 gov24 수집·임베딩·DB 적재 및 반복 적재 수치
- 실제 코퍼스 기준 확장 평가셋 라벨 확정
- 기존 60문항 회귀와 신규 Recall@1/5·MRR 실측
- 공식 링크 누락, 무근거 답변, 지역 오탐의 실제 건수

이 항목이 끝나기 전에는 Custom Search MVP 완료나 검색 품질 향상을 주장하지 않는다.
