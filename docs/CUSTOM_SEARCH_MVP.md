# Custom Search MVP 검증 기록

기준일: 2026-08-29 — P0 Canonical Evaluation Freeze
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
- Gemini 프롬프트에는 검색된 정책의 이름·출처·지원내용·공식 링크만 들어간다. 모델은 `api/src/main/resources/application.yml`의 `gemini.model=${GEMINI_MODEL:gemini-3.5-flash-lite}` (Free Tier, env로 교체 가능)이며, 요청 형식·재시도·프롬프트 구조는 이전 `gemini-3.1-flash-lite`와 동일하다.
- 검색 결과가 0건이면 Gemini를 호출하지 않는다.
- `(source, source_id)`로 평가해 출처 간 ID 충돌을 피한다.
- `region`이 들어온 공개 API 요청은 기존과 같이 400으로 거절한다.

## 지역 데이터 판정

gov24 v3 공식 Swagger에는 서비스의 행정 지역코드가 없다. `소관기관코드`·`소관기관유형`·기관명은 서비스 적용 지역과 같은 의미라고 검증되지 않았으므로 지역코드로 변환하지 않았다. 전국, 특정 지역, 지역 확인 불가를 안정적으로 구분할 표본도 아직 없다.

따라서 이번 변경은 gov24 정책의 `region_codes`를 빈 배열로 저장하고 지역 필터를 노출하지 않는다. `run_data_quality.py`는 출처별 지역코드 보유 건수를 기록하지만, 이것은 지역 정확도 증거가 아니다.

## 평가 결과

2026-08-28 적재 직전 Neon은 기존 `youth` 정책 2,631건과 청크 3,083건만 보유했고 임베딩 누락은 0건이었다. 이 상태에서 기존 청년정책 60문항을 다시 실행해 `eval/results_before_expansion.json`에 기준선을 먼저 보존했다.

Gov24 정책 10,958건과 768차원 청크 14,526건을 적재한 뒤 정책은 총 13,589건, 청크는 총 17,609건이 됐다.

| `youth` | 2,631 | 3,083 | 615 (DB) / 599 (projected after fix) | 2,631 |
| `gov24` | 10,958 | 14,526 | 0 | 0 |

현재 DB `youth missing_links 615(NULL 564+non-http 51)`는 `eval/run_data_quality.py:17` `apply_url IS NULL OR !~ '^https?://'` 기준 실측치다. 그 중 `16`건은 `raw.aplyUrlAddr`가 `www.`·`-`·`추후 공지` 등 non-http이면서 `raw.refUrlAddr1`에 `https://`가 있으나 `ingest_youth:61`이 앞의 truthy non-http를 선택한 ingestion bug이며, `12dbaca fix: prefer valid youth policy URLs` 패치(`_official_url`)로 동일 raw 2631건에 대해 `projected 599`로 복구된다. `refUrlAddr2`는 youth 2631건 중 `https` 328건이나 missing 615 중 추가 복구는 1건에 불과해 이번 production URL source로 미채택. 남은 `599`는 양 필드 모두에 유효 `http(s)`가 없는 source limitation이다.

`(source, source_id)` 중복 정책, `(policy_id, chunk_index)` 중복 청크, 고아 청크, 청크 없는 정책, 누락 임베딩, 768차원이 아닌 임베딩은 모두 0건이다. 같은 파일을 반복 적재한 뒤에도 출처별 수와 무결성 결과가 같았다. 출처 간 제목이 같은 정책은 93개다. 지역 필터는 계속 노출하지 않는다.

기존 60문항의 bi-encoder 결과는 다음과 같다.

| 지표 | 적재 전 | 적재 후(무보정) | 변화 |
|---|---:|---:|---:|
| Recall@1 | 0.4000 | 0.3167 | -0.0833 |
| Recall@5 | 0.7333 | 0.6667 | -0.0666 |
| Recall@10 | 0.8000 | 0.7333 | -0.0667 |
| MRR@10 | 0.5346 | 0.4560 | -0.0786 |

Gov24 추가 뒤 기존 청년정책 검색은 네 지표 모두 회귀했다. 복수 출처 통합만으로 검색 품질이 개선됐다는 주장은 하지 않는다. 무보정 결과 원본은 `eval/results_after_expansion.json`에 보존했다.

이 회귀를 완화하기 위해 검색 후보 정렬에만 최소 보정을 적용했다. 질의에 `청년`·`대학생`·`사회초년생`이 명시되고 알려진 Gov24 기관명이 없을 때만 `youth` 출처의 거리에서 `0.015`를 뺀다. 기관명이 명시되면 보정을 적용하지 않는다. 스키마·FTS·재임베딩·데이터 재수집은 변경하지 않았고, 평가 결과에는 규칙 metadata를 함께 기록한다.

| 지표 | 적재 후(무보정) | 최소 보정 후 | 변화 |
|---|---:|---:|---:|
| Recall@1 | 0.3167 | 0.3333 | +0.0167 |
| Recall@5 | 0.6667 | 0.6667 | +0.0000 |
| Recall@10 | 0.7333 | 0.7833 | +0.0500 |
| MRR@10 | 0.4560 | 0.4693 | +0.0133 |

현재 평가에서 `0.005`, `0.010`, `0.015`, `0.020`, `0.025`를 비교했다. `0.015`는 Recall@1과 MRR@10을 함께 개선한 가장 작은 후보였고, `0.020`·`0.025`는 추가 개선이 없었다. 따라서 이 값은 현재 평가셋에 대한 최소 선택값이지 일반화된 production 최적값으로 간주하지 않는다. 최종 결과 원본은 `eval/results_after_source_bias.json`에 보존했다.

실제 Gov24 코퍼스의 서비스 ID·정책명을 대조해 고정한 신규 검색 정답 21문항 결과는 다음과 같다.

| 지표 | 무보정 | 최소 보정 후 | 변화 |
|---|---:|---:|---:|
| Recall@1 | 0.2857 | 0.2857 | +0.0000 |
| Recall@5 | 0.4762 | 0.4762 | +0.0000 |
| Recall@10 | 0.7143 | 0.7143 | +0.0000 |
| MRR@10 | 0.3901 | 0.3901 | +0.0000 |

신규 21문항의 Gov24 검색 범위는 이 보정으로 감소하지 않았다. 최종 결과 원본은 `eval/results_expansion_source_bias.json`에 보존했다. `expansion_api_evalset.jsonl`은 기존 27문항(21+3+3)에서 hard-negative 9건을 추가해 36문항(21+3+12)으로 확장했으며, 신규 no_answer의 목적은 abstention 일반화 검증으로 retrieval-level에서 달성됐다. 36-case Gemini E2E는 MVP 필수 gate가 아니므로 실행하지 않았다. 27문항 API E2E는 `eval/results_expansion_api_27.json`(기존 `results_expansion_api.json`)에 기록된 바와 같이 실행 완료됐다. 오프라인 코퍼스·라벨 검증과 API 평가기 단위 테스트는 통과했다.
### Production-parity 리랭커 판정

2026-08-29 한 차례 실측에서 후보 랭킹 진단과 실제 `/search` 사이의 차이를 없애기 위해 `run_eval_rerank.py`가 production 코드를 직접 공유하도록 바꿨다. 같은 `strip_region`, 후보 SQL과 만료 정책 제외, `CANDIDATES=30`, source bias, 결과 column mapping을 사용한다. `RERANK=0`은 cosine `0.78` cut, `RERANK=1`은 `title + support_content` 400자와 raw logit `0.12` cut을 적용한다.

평가 명령 한 번이 같은 후보에 대해 `bi_encoder`(`RERANK=0`)와 `rerank`(`RERANK=1`) 결과 block을 함께 기록한다.

| 평가셋·지표 | `RERANK=0` | `RERANK=1` | 변화 |
|---|---:|---:|---:|
| 기존 60 Recall@1 | 0.2000 | 0.2500 | +0.0500 |
| 기존 60 Recall@5 | 0.4000 | 0.3333 | -0.0667 |
| 기존 60 Recall@10 | 0.4667 | 0.3333 | -0.1334 |
| 기존 60 MRR@10 | 0.2881 | 0.2817 | -0.0064 |
| Gov24 21 Recall@1 | 0.2857 | 0.2857 | +0.0000 |
| Gov24 21 Recall@5 | 0.4762 | 0.6190 | +0.1428 |
| Gov24 21 Recall@10 | 0.6190 | 0.6190 | +0.0000 |
| Gov24 21 MRR@10 | 0.3798 | 0.4222 | +0.0424 |

리랭커는 Gov24 평가의 Recall@5와 MRR을 높였지만 기존 youth 평가의 Recall@5·@10과 MRR을 악화시켰다. 두 검색 범위를 함께 유지한다는 채택 기준을 만족하지 못하므로 **No-Go**로 판정하고 배포의 `RERANK=0`을 유지한다. 결과 원본은 `eval/results_after_source_bias_rerank.json`과 `eval/results_expansion_source_bias_rerank.json`이다. **P0 이전 historical 결과 파일(`results_before_expansion.json`, `results_after_expansion.json`, `results_after_source_bias.json`, `results_expansion_source_bias.json`, `results_after_source_bias_rerank.json`, `results_expansion_source_bias_rerank.json`)은 모두 보존했다. 이후 수치는 현재 production 계약으로 재현한 canonical artifact(`eval/canonical_*.json`, `eval/canonical_manifest.json`)를 기준으로 한다.**

27문항 API 통합 평가는 실행 완료됐으며 결과는 `eval/results_expansion_api_27.json`(기존 `results_expansion_api.json`)에 `positive n=21 Recall@1 0.2857 Recall@5 0.7143 MRR 0.4143, ineligible forbidden 0/3, answer_without_sources 0, missing_ground_links 3`으로 기록됐다. 36-case Gemini E2E는 MVP 필수 gate가 아니므로 실행하지 않았다.

평가 도구는 출처를 포함한 gold key와 출처별 Recall/MRR를 기록한다. `run_data_quality.py`는 출처별 정책 수, 공식 링크 누락, 지역코드 보유, 임베딩 누락, 출처 간 동일 제목 수를 `eval/data_quality.json`에 저장한다. **P0의 `run_eval.py`는 `generated_at`·`git_commit`·`corpus`·`production_contract`·`lexical_bias_used`를 함께 기록하며, `--lexical-bias` override로 lexical 0 vs production 0.01을 동일 SQL·전처리에서 비교한다.**
Canonical artifact는 clean evaluator commit `58dff80`에서 저장소 밖 임시 디렉터리로 생성해 `git_dirty=false`를 확인한 뒤 `eval/`에 복사했다. 따라서 tracked canonical 파일을 직접 덮어쓰며 순차 재실행하는 절차는 지표 재현에는 사용할 수 있지만 clean provenance 생성 절차와는 구분한다.
이번 적재에서는 이미 완성된 `gov24_policies.jsonl`과 `chunks.jsonl`을 사용했다. 수집과 임베딩은 다시 실행하지 않았다.

```powershell
# 적재 전 기준선
# 당시 source ranking 보정이 없는 코드로 실행한 결과를 `eval/results_before_expansion.json`에 보존했다.

# Gov24 적재와 무결성·품질 확인
python ingest/load_db.py
python scripts/check_db.py
python eval/run_data_quality.py

# 적재 후 source-aware 회귀와 확장 검색 평가 (historical)
python eval/run_eval.py --output eval/results_after_source_bias.json
python eval/run_eval.py --eval-file eval/expansion_evalset.jsonl --output eval/results_expansion_source_bias.json

# production `/search` 계약의 bi-encoder ↔ reranker 비교 (historical, lexical 0)
python eval/run_eval_rerank.py --output eval/results_after_source_bias_rerank.json
python eval/run_eval_rerank.py --eval-file eval/expansion_evalset.jsonl --output eval/results_expansion_source_bias_rerank.json

# P0 canonical — 현재 production 계약(RERANK=0, CANDIDATES=30, COSINE_MIN=0.78, lexical 0.01) 재현
python eval/run_eval.py --eval-file eval/evalset.jsonl --output eval/canonical_youth_production_parity.json --lexical-bias 0.01
python eval/run_eval.py --eval-file eval/evalset.jsonl --output eval/canonical_youth_production_lexical_0.json --lexical-bias 0
python eval/run_eval.py --eval-file eval/expansion_evalset.jsonl --output eval/canonical_gov24_production_parity.json --lexical-bias 0.01
python eval/run_eval.py --eval-file eval/expansion_evalset.jsonl --output eval/canonical_gov24_production_lexical_0.json --lexical-bias 0
python eval/run_hard_negative_eval.py --eval-file eval/expansion_api_evalset.jsonl --output eval/canonical_hard_negative_36_production_parity.json --lexical-bias 0.01

# 확장 라벨과 API 평가기 오프라인 검증
python eval/validate_expansion_evalset.py
python eval/test_run_api_eval.py
```
`ml-service` context에서 Docker 이미지를 빌드했고, 최종 이미지를 `MODEL_LOCAL_ONLY=1`로 두 번 실행했다. e5 모델 로딩은 각각 `11,458.596ms`, `13,780.656ms`였고 두 번째 실행에서 `/ready`가 로딩 중 `503`을 반환한 뒤 `200 {"status":"ready"}`로 전환되는 것을 확인했다. 런타임 Hub 접근 없이 baked model이 준비되는 경로까지 검증했다.

27문항 API 통합 평가는 ML 서비스와 Spring API를 실행하고 Gemini 외부 호출 승인을 받은 환경에서만 다음 명령으로 수행했으며, 결과는 `eval/results_expansion_api_27.json`(기존 `results_expansion_api.json` 27-case)으로 보존됐다.

```powershell
python eval/run_api_eval.py `
  --eval-file eval/expansion_api_evalset.jsonl `
  --output eval/results_expansion_api_27.json
```

### 경량 어휘 보정 실험

production-parity 후보 진단에서 기존 youth 60문항의 gold가 `CANDIDATES=30` 밖으로 밀린 사례가 대부분이었지만, gold 정책의 직접 코사인 점수는 모두 `0.78` 이상이었다. 따라서 재임베딩·리랭커 대신 후보 정렬에만 질의 핵심어가 정책 본문(`title`, `summary`, `support_content`, `add_qualify`, `keywords`)에 나타난 서로 다른 개수를 반영하는 보정을 실험했다. 질문 상투어는 제외하고, 어휘 보정값은 `0.01`로 고정했다. `RERANK=0`, `CANDIDATES=30`, `COSINE_MIN=0.78`, `strip_region`, 만료 제외, 결과 컬럼과 지역 요청 400 계약은 유지했다.

| 평가셋·지표 | 기존 bi-encoder (`--lexical-bias 0`) | 어휘 보정 bi-encoder (`--lexical-bias 0.01`, production) | 변화 |
|---|---:|---:|---:|
| 기존 youth 60 Recall@1 | 0.2000 | 0.2333 | +0.0333 |
| 기존 youth 60 Recall@10 | 0.4667 | 0.5167 | +0.0500 |
| 기존 youth 60 MRR@10 | 0.2881 | 0.3281 | +0.0400 |
| Gov24 21 Recall@1 | 0.2857 | 0.2857 | +0.0000 |
| Gov24 21 Recall@10 | 0.6190 | 0.7619 | +0.1429 |
| Gov24 21 MRR@10 | 0.3798 | 0.4222 | +0.0424 |

위 표는 P0에서 동일 production 계약으로 `eval/canonical_youth_production_lexical_0.json` ↔ `eval/canonical_youth_production_parity.json`, `eval/canonical_gov24_production_lexical_0.json` ↔ `eval/canonical_gov24_production_parity.json`을 비교해 재현한 결과다. historical 파일은 각각 lexical 0 이전 수치에 해당한다. 어휘 보정은 두 평가 범위 모두 개선되어 유지한다. production parity evaluator와 ML 서비스가 같은 SQL·어휘 추출기를 공유하며, cross-encoder 결과는 기존과 같이 youth top-10을 악화시키므로 배포 결정은 `RERANK=0`으로 유지한다. provenance는 각 JSON의 `generated_at`·`git_commit`·`corpus`·`lexical_bias_used`에 기록된다.
### Abstention 판정: No-Go (P0 재현)

36문항 evalset(positive 21+ineligible 3+no_answer 12)으로 production retrieval(`CANDIDATES=30`·`COSINE_MIN=0.78`·`lexical 0.01`) 조건에서 hard-negative 확장 검증을 P0 canonical으로 재현했다. 결과는 `eval/canonical_hard_negative_36_production_parity.json`에 보존했다. per-case `top1 score`·`gap`·`lexical_overlap`과 aggregate가 함께 기록된다.

no-answer 12건(기존 3 + 신규 9) 중 `top1 0.8303~0.8658`이 positive 21건의 `0.8481~0.9242`와 겹쳐 `0.84`대 score separation은 붕괴됐다. canonical aggregate: `top1_score<0.8481`→`no_answer 5/12, positive false 1/21`, `score<0.842 & lex<2`→`3/12 vs 0/21` — 첫 기준은 positive false 1/21이 발생했고, 두 번째는 positive false 0/21이지만 no-answer 3/12만 탐지해 충분한 분리가 되지 않았다. gap/lex/tlex 등 저비용 신호도 동일하게 분리 불가. cross-encoder top1 gate는 기존과 같이 `ce<0.05 10/12 vs 8/21`, `ce<0.10 12/12 vs 8/21`, `ce<0.12 12/12 vs 10/21`로 positive false가 크고 `+1GB`·`+0.3s` 비용이 추가돼 재검증 없이 No-Go를 유지. 문서 `0.8356`은 이전 실측치이며 P0 canonical에서는 `0.8303`으로 재현됐다. global threshold·`ABSTAIN_MIN_SCORE`·score/gap 조합 재튜닝·cross-encoder gate 재실험을 하지 않으며, learned classifier/LLM relevance judge는 future work로 둔다.

### Youth URL 품질

현재 DB `missing_links 615` 중 `16`건은 ingestion bug, `599`건은 source limitation으로 확정됐다. 코드는 `12dbaca`에서 `_official_url`로 수정됐으나 DB는 아직 reload하지 않아 현재 실측치는 `615`, 다음 정상 refresh 시 `projected 599`가 된다. `599`는 youth 원천 자체에 유효 URL이 없는 accepted limitation이며, `refUrlAddr2`는 추가 복구 1건에 불과해 이번 scope에서 제외했다. `policy.apply_url`만 수정하면 `policy_chunk`·embedding에 영향이 없어 targeted UPDATE 16건 또는 다음 `load_db` refresh로 반영 가능하다.

### MVP exit state: Complete — P0 동결

**Custom Search MVP: Complete — P0 Canonical Freeze** — 현재 production-parity retrieval과 36-case abstention No-Go 수치는 `eval/canonical_*.json`과 `eval/canonical_manifest.json`에서 재현된다. cross-encoder No-Go는 P0 이전 historical reranker artifact에, 27-case API E2E(`Recall@1 0.2857` 등)는 `eval/results_expansion_api_27.json`에 보존돼 있다. Gov24 10,958건 확장과 youth `615→599` URL 분석은 본 문서의 데이터 품질·URL 근거에 기록돼 있다. production 계약은 `RERANK=0`·`CANDIDATES=30`·`COSINE_MIN=0.78`·`LEXICAL_OVERLAP_BIAS=0.01`·`strip_region`이다. historical 파일은 보존했고 이후 retrieval 변경은 canonical을 기준으로 한다. 남은 것은 `no-answer` 별도 gate 없음, `household_housing/welfare_health` 등 일부 recall 취약, youth `599` source limitation, learned relevance는 future work로, production load/performance test는 별도 backend-depth 작업이다.
