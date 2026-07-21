# Production Lab 2 — 콜드스타트 구간 관측과 무비용 개선

상태: **완료 — 무트래픽 revision 실측·콜드 로그 검증, 공개 traffic 미변경**

## 결론

2026-07-14의 검색 전용 첫 요청 58,909ms에는 구간 header가 없어 그 단일 요청을
사후에 정확히 재분해할 수 없다. 같은 고정 합성 입력을 관측 revision에서 재현한 첫 요청은
35,328.073ms였고, 가장 큰 구간은 모델 readiness 대기 26,097.431ms(73.87%)였다.
임베딩 5,168.575ms(14.63%), DB 연결 1,156.977ms(3.27%), DB 쿼리
984.802ms(2.79%), API↔ML 잔여 1,081.741ms(3.06%), client/API 잔여
837.850ms(2.37%) 순이었다. 병목은 API나 Gemini가 아니라 **ML 모델 준비**였다.

비용 없는 변경은 이미지에 이미 포함된 모델을 `MODEL_LOCAL_ONLY=1`로만 여는 것이다.
같은 컨테이너 이미지·리소스, 최소 인스턴스 0, scale-to-zero 후 동시 첫 요청에서
모델 로드가 25,897.345ms에서 25,381.032ms로 **516.313ms(1.99%) 감소**했다.
콜드 end-to-end도 39,324.449ms에서 37,385.248ms로 1,939.201ms(4.93%)
감소했지만, 이 중 3,090.269ms는 Cloud Run/API·클라이언트 잔여 차이이므로 전체 감소를
local-only 효과로 귀속하지 않는다. 검증된 개선 성과는 모델 로드 1.99%뿐이다.

## 개인정보 경계와 관측 구조

- API·ML 로그, metric tag, 측정 CSV에 질문 원문·나이·지역을 기록하지 않는다.
- request ID는 본문과 무관한 난수이고, segment/outcome은 고정 allowlist만 허용한다.
- 측정 스크립트의 합성 질문과 `age=null`은 요청 메모리에만 존재한다.
- ML `/health`는 프로세스 생존, `/ready`는 모델 준비 상태와 로드 시간만 반환한다.

```text
클라이언트 end-to-end
├─ client_api_residual
├─ api_to_ml
│  ├─ api_ml_transport = api_to_ml - ml_total
│  └─ ml_total
│     ├─ ml_model_wait
│     ├─ ml_embedding
│     ├─ ml_db_connect
│     ├─ ml_db_query
│     └─ ml_rerank
└─ gemini (/api/ask만)
```

API는 ML `Server-Timing`에서 허용된 이름만 수집하고 Micrometer
`benefitcompass.segment.duration`에 고정 `segment`·`outcome` tag로 기록한다.
응답에는 같은 구간과 `X-ML-Model-Load-Ms`를 내보낸다.

## 배포 revision과 비용 조건

| 역할 | API revision | ML revision | traffic |
|---|---|---|---:|
| 기존 공개 | `benefit-api-00002-ndd` | `benefit-ml-00001-wvn` | 100% |
| before | `benefit-api-pl2b-8577c94` | `benefit-ml-pl2b-3f11ebc` | 0% tag |
| after | `benefit-api-pl2a-8577c94` | `benefit-ml-pl2a-8577c94` | 0% tag |
| 최종 로그 검증 | `benefit-api-pl2f-e0b0ada` | `benefit-ml-pl2f-e0b0ada` | 0% tag |

before/after ML은 같은 이미지 digest `sha256:73aaf7be...020b8c`, API는 같은
`sha256:f9c84d5e...f26d8`를 사용한다. 차이는 `MODEL_LOCAL_ONLY=0/1`뿐이다.
API는 1 vCPU·1GiB·concurrency 80·timeout 300s·max 20, ML은 2 vCPU·2GiB·
concurrency 160·timeout 300s·max 10이다. 두 서비스 모두 `minScale` 주석이 없고
startup CPU boost만 기존대로 켜져 있다. 최소 인스턴스, CPU·메모리 증설, 공개 traffic
변경은 없었다.

최종 revision은 검색과 `/api/ask` 모두 200/정책 5건을 반환했다. ML 로그에는
`ml_model_load` start/complete와 `ml_search`의 request ID·결과 건수·고정 구간 시간만
남았고 질문·나이는 없었다. 상세 revision과 두 번의 API 시작 실패 복구는
[배포 기록](DEPLOYMENT_2026-07-21.md)에 남겼다.

## 실측 결과

### 병목 재현

| 구간 | 첫 요청 ms | 전체 대비 |
|---|---:|---:|
| client/API 잔여 | 837.850 | 2.37% |
| API↔ML 잔여 | 1,081.741 | 3.06% |
| 모델 readiness 대기 | 26,097.431 | 73.87% |
| 임베딩 | 5,168.575 | 14.63% |
| DB 연결 | 1,156.977 | 3.27% |
| DB 쿼리 | 984.802 | 2.79% |
| 리랭크 | 0 | 0% |
| end-to-end | 35,328.073 | 100% |

모델 loader의 최초 wall time은 1,179,855.962ms였다. Cloud Run이 요청 밖에서
background thread CPU를 제한하므로, 짧은 readiness polling 동안 로딩이 거의 진행되지
않다가 첫 `/search`가 열린 동안 완료됐다. 이 wall time은 사용자 요청 시간과 동일하지 않아
개선 비교에는 사용하지 않았다.

### 동일 조건 before/after

15분 이상 유휴 후 두 tag를 동시에 호출했다. Cloud Logging에서 각 ML revision에
`AUTOSCALING` 새 instance와 같은 instance의 첫 `/search` 200이 이어져 두 첫 행을
콜드로 확정했다.

| 지표 | before ms | after ms | 변화 |
|---|---:|---:|---:|
| 모델 로드 | 25,897.345 | 25,381.032 | **-516.313 (-1.99%)** |
| 모델 대기 | 25,801.542 | 25,345.674 | -455.868 (-1.77%) |
| ML 전체 | 28,638.856 | 29,981.241 | +1,342.385 (+4.69%) |
| API→ML | 30,997.486 | 32,148.554 | +1,151.068 (+3.71%) |
| client/API 잔여 | 8,326.963 | 5,236.694 | -3,090.269 (-37.11%) |
| end-to-end | 39,324.449 | 37,385.248 | -1,939.201 (-4.93%) |

after는 외부 Hub 경고 없이 로컬 가중치를 열었고, before에는 unauthenticated HF Hub
접근 경고가 남았다. 모델 로드·대기는 감소했지만 임베딩·DB와 플랫폼 변동 때문에 ML 전체는
증가했다. 따라서 local-only를 큰 콜드스타트 해결책으로 과장하지 않고, 외부 의존 제거와
확인된 1.99% 모델 로드 단축만 개선으로 판정한다.

별도 warm 5회의 end-to-end 중앙값은 before 751.040ms, after 776.566ms였다.
DB 연결 중앙값은 429.972ms/437.835ms, DB 쿼리는 231.693ms/231.267ms로 warm의
주요 비용은 매 요청 DB 연결이었다. `/api/ask` warm 3회의 Gemini 중앙값은
874.349ms/987.090ms였다. Gemini는 검색 콜드 비교에서 제외한다.

## 원본과 재현

- [초기 before 콜드·웜 CSV](cold-warm-before-2026-07-21.csv)
- [초기 after 콜드·웜 CSV](cold-warm-after-2026-07-21.csv)
- [scale-to-zero 동시 before CSV](cold-paired-before-2026-07-21.csv)
- [scale-to-zero 동시 after CSV](cold-paired-after-2026-07-21.csv)
- [콜드 instance 로그 증거 CSV](cold-instance-evidence-2026-07-21.csv)
- [before warm 5회 CSV](warm-before-2026-07-21.csv)
- [before Gemini CSV](gemini-before-2026-07-21.csv)
- [after Gemini CSV](gemini-after-2026-07-21.csv)

```powershell
.\scripts\measure-cold-warm.ps1 `
  -ApiBaseUrl 'https://TAGGED-API-URL' `
  -Mode recommend `
  -Scenario 'paired-before-scale-zero' `
  -Revision 'benefit-api-REVISION' `
  -Runs 2 `
  -FirstRequestColdCandidate `
  -OutputCsv '.\docs\operations\cold-paired-before.csv'
```

첫 행은 항상 `cold_candidate/pending_revision_log`로만 생성한다. Cloud Logging에서 같은
revision·instance의 `AUTOSCALING` 시작과 첫 검색을 확인한 뒤 문서에서 콜드로 확정한다.

## 테스트와 관측 오버헤드

- `api\gradlew.bat test --no-daemon`: Java 단위·API·전체 Spring context 테스트 9개 통과
- `python -m unittest -v test_app test_runtime_state`: ML 단위·health/readiness/search API 7개 통과
- PowerShell parser: 측정 스크립트 문법 통과
- 최종 0% revision: recommend/ask 200, 각 정책 5건, 구간 header와 request ID 확인

관측 활성/비활성 경로를 7라운드, 모드당 20,000회 비교한 중앙값은 비활성
165.455ns/op, 활성 6,908.550ns/op, 증분 **6,743.095ns/op(0.006743ms/op)** 이었다.
이는 로컬 JVM 마이크로벤치마크다. 원본은
[observation-overhead-2026-07-21.csv](observation-overhead-2026-07-21.csv)다.

## 한계

- 58,909ms 역사 요청에는 새 header가 없어 정확한 숫자 분해가 아니라 동일 입력 재현으로
  원인을 확인했다.
- 검증된 scale-to-zero 콜드 쌍은 각 조건 1개뿐이다. 1.99%는 반복 표본이 없는 작은 효과다.
- 두 요청을 동시에 보냈어도 Cloud Run의 instance 시작, 이미지 fetch, API queue는 달라진다.
- `client_api_residual`과 `api_ml_transport`는 여러 플랫폼·직렬화 요소가 섞인 잔여값이다.
- DB 연결·쿼리는 분리했지만 Neon 휴면 해제 내부 단계는 보이지 않는다.
- Gemini는 외부 서비스 변동성이 있어 별도 warm 표본으로만 기록했다.

원인, 실패 탐지 누락과 후속 조치는 [포스트모템](POSTMORTEM_2026-07-21.md)에 정리했다.
