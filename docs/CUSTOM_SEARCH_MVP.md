# Custom Search MVP 검증 기록

기준일: 2026-08-28

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

초기 접근 검증에서는 무인증 요청이 `401`을 반환했고, 첫 인증키도 활용등록 전이라 `401`, 코드 `-4`를 반환했다. 활용등록을 수정한 뒤 공식 Swagger의 헤더 인증으로 세 엔드포인트의 실제 응답을 받았고, 2026-08-27 전체 10,958건 수집을 완료했다. 필수 ID·정책명과 세 원본 결합은 10,958건 모두 정상이고 `(source, source_id)`도 전부 유일하다. 연령 필터가 활성화된 정책은 9,914건이며 비정상 연령 범위와 임의 지역코드는 0건이다.

첫 전체 수집에서는 스킴 없는 `온라인신청사이트URL`이 유효한 정부24 상세 URL보다 먼저 선택돼 공식 링크가 349건 누락됐다. 첫 번째 유효한 HTTP(S) 후보를 선택하도록 수정하고 전체 재수집한 결과 공식 링크 누락은 0건이 됐다.

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

## 평가 결과

2026-08-28 적재 직전 Neon은 기존 `youth` 정책 2,631건과 청크 3,083건만 보유했고 임베딩 누락은 0건이었다. 이 상태에서 기존 청년정책 60문항을 다시 실행해 `eval/results_before_expansion.json`에 기준선을 먼저 보존했다.

Gov24 정책 10,958건과 768차원 청크 14,526건을 적재한 뒤 정책은 총 13,589건, 청크는 총 17,609건이 됐다.

| 출처 | 정책 | 청크 | 공식 링크 누락 | 지역코드 보유 |
|---|---:|---:|---:|---:|
| `youth` | 2,631 | 3,083 | 615 | 2,631 |
| `gov24` | 10,958 | 14,526 | 0 | 0 |

`(source, source_id)` 중복 정책, `(policy_id, chunk_index)` 중복 청크, 고아 청크, 청크 없는 정책, 누락 임베딩, 768차원이 아닌 임베딩은 모두 0건이다. 같은 파일을 반복 적재한 뒤에도 출처별 수와 무결성 결과가 같았다. 출처 간 제목이 같은 정책은 93개다. 지역 필터는 계속 노출하지 않는다.

기존 60문항의 bi-encoder 결과는 다음과 같다.

| 지표 | 적재 전 | 적재 후 | 변화 |
|---|---:|---:|---:|
| Recall@1 | 0.4000 | 0.3167 | -0.0833 |
| Recall@5 | 0.7333 | 0.6667 | -0.0666 |
| Recall@10 | 0.8000 | 0.7333 | -0.0667 |
| MRR@10 | 0.5346 | 0.4560 | -0.0786 |

Gov24 추가 뒤 기존 청년정책 검색은 네 지표 모두 회귀했다. 복수 출처 통합이 검색 품질을 개선했다는 주장은 하지 않는다. 결과 원본은 `eval/results_before_expansion.json`과 `eval/results_after_expansion.json`에 보존했다.

실제 Gov24 코퍼스의 서비스 ID·정책명을 대조해 고정한 신규 검색 정답 21문항 결과는 다음과 같다.

| 지표 | 결과 |
|---|---:|
| Recall@1 | 0.2857 |
| Recall@5 | 0.4762 |
| Recall@10 | 0.7143 |
| MRR@10 | 0.3901 |

결과 원본은 `eval/results_expansion.json`에 보존했다. `expansion_api_evalset.jsonl`은 같은 검색 문항에 비대상 3문항과 정답 없음 3문항을 더한 27문항이며, 9개 유형을 각각 3문항씩 포함한다. 오프라인 코퍼스·라벨 검증과 API 평가기 단위 테스트는 통과했다.

실제 27문항 API 통합 평가는 실행하지 않았다. 검색 결과가 있는 문항은 Gemini 외부 호출을 발생시키지만 이번 승인 범위는 Gov24 전체 수집과 현재 Neon 적재까지였기 때문이다. 따라서 Gemini 생성 품질, 무근거 생성, 비대상 정책 노출의 실제 API 수치는 아직 없다.

평가 도구는 출처를 포함한 gold key와 출처별 Recall/MRR를 기록한다. `run_data_quality.py`는 출처별 정책 수, 공식 링크 누락, 지역코드 보유, 임베딩 누락, 출처 간 동일 제목 수를 `eval/data_quality.json`에 저장한다.

## 재현 절차와 남은 게이트

이번 적재에서는 이미 완성된 `gov24_policies.jsonl`과 `chunks.jsonl`을 사용했다. 수집과 임베딩은 다시 실행하지 않았다.

```powershell
# 적재 전 — 이 순서를 바꾸지 않는다.
python scripts/check_db.py
python eval/run_eval.py --output eval/results_before_expansion.json

# Gov24 적재와 무결성·품질 확인
python ingest/load_db.py
python scripts/check_db.py
python eval/run_data_quality.py

# 적재 후 회귀와 확장 검색 평가
python eval/run_eval.py --output eval/results_after_expansion.json
python eval/run_eval.py --eval-file eval/expansion_evalset.jsonl --output eval/results_expansion.json

# 확장 라벨과 API 평가기 오프라인 검증
python eval/validate_expansion_evalset.py
python eval/test_run_api_eval.py
```

27문항 API 통합 평가는 ML 서비스와 Spring API를 실행하고 Gemini 외부 호출 승인을 받은 환경에서만 다음 명령으로 수행한다.

```powershell
python eval/run_api_eval.py `
  --eval-file eval/expansion_api_evalset.jsonl `
  --output eval/results_expansion_api.json
```

남은 품질 게이트:

- Gov24 추가 뒤 발생한 기존 60문항 회귀의 원인 분석과 검색 품질 회복
- 승인된 환경에서 27문항 API 통합 평가 실행
- API 평가로 공식 링크 누락, 무근거 생성, 비대상 정책 노출의 실제 건수 측정

Gov24 전체 수집·임베딩·Neon 적재와 검색 평가는 완료했다. 다만 위 회귀가 남아 있으므로 복수 출처 검색 품질 향상을 주장하지 않는다.
