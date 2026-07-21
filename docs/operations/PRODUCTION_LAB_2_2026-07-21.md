# Production Lab 2 — 콜드스타트 구간 관측과 무비용 개선

상태: **리뷰 보완 로컬 완료, 새 무트래픽 revision 재검증 대기 — 공개 traffic 미변경**

## 결론

2026-07-14의 검색 전용 첫 요청 58,909ms에는 구간 header가 없어 그 단일 요청을
사후에 정확히 재분해할 수 없다. 같은 고정 합성 입력을 관측 revision에서 재현한 첫 요청은
35,328.073ms였고, 가장 큰 구간은 모델 readiness 대기 26,097.431ms(73.87%)였다.
임베딩 5,168.575ms(14.63%), DB 연결 1,156.977ms(3.27%), DB 쿼리
984.802ms(2.79%), API↔ML 잔여 1,081.741ms(3.06%), client/API 잔여
837.850ms(2.37%) 순이었다. 이 관측 revision의 검색 경로에서는 **ML 모델 준비**가
가장 큰 구간이었다. 58.909초 역사 기준선은 동기 startup 구조였고 구간 header도 없어,
두 숫자가 완전히 같은 시스템의 전후 결과는 아니다.

비용 없는 변경은 이미지에 이미 포함된 모델을 `MODEL_LOCAL_ONLY=1`로만 여는 것이다.
같은 컨테이너 이미지·리소스, 최소 인스턴스 0, scale-to-zero 후 동시 첫 요청에서
모델 로드 관측값은 25,897.345ms와 25,381.032ms로 **516.313ms(1.99%) 차이**였다.
콜드 end-to-end도 39,324.449ms에서 37,385.248ms로 1,939.201ms(4.93%)
감소했지만, 이 중 3,090.269ms는 Cloud Run/API·클라이언트 잔여 차이이므로 전체 감소를
local-only 효과로 귀속하지 않는다. 조건별 콜드 표본이 1개뿐이므로 1.99%도 성능 개선으로
확정하지 않는다. 검증된 변화는 동일 이미지에서 런타임 HF Hub 확인 경로와 경고가 사라진 것이다.

후속 리뷰에서 background loader를 도입한 관측 revision에 `/ready` startup probe가 연결되지
않아 모델 준비 전 traffic을 받을 수 있음을 확인했다. 로컬 코드에는 `/ready` probe 배포 조건,
실패 응답 구간 header, 안전한 API 오류 응답을 보완했다. 이 보완은 새 0% revision에서
재검증하기 전까지 Production Lab 2의 검증된 배포 결과로 세지 않는다.

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

기존 최종 revision은 검색과 `/api/ask` 모두 200/정책 5건을 반환했다. ML 로그에는
`ml_model_load` start/complete와 `ml_search`의 request ID·결과 건수·고정 구간 시간만
남았고 질문·나이는 없었다. 다만 `/ready` startup probe 누락 때문에 이 revision을 새 배포
후보로 승인하지 않는다. 상세 revision, 두 번의 API 시작 실패, 리뷰 후 재검증 상태는
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
접근 경고가 남았다. local-only 쪽 모델 로드·대기 관측값은 더 작았지만 임베딩·DB와 플랫폼
변동 때문에 ML 전체는
증가했다. 따라서 local-only의 성능 효과는 미확정으로 두고, 외부 Hub 확인 경로 제거만
검증된 개선으로 판정한다.

별도 warm 5회의 end-to-end 중앙값은 before 751.040ms, after 776.566ms였다.
DB 연결 중앙값은 429.969ms/437.835ms, DB 쿼리는 231.693ms/231.267ms로 warm의
주요 비용은 매 요청 DB 연결이었다. `/api/ask` warm 3회의 Gemini 중앙값은
874.346ms/987.091ms였다. Gemini는 검색 콜드 비교에서 제외한다.

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
초기 before는 별도 warm CSV를 추가 수집했고 after 초기 CSV에는 콜드 후보 뒤 warm 행이
함께 있다. 원본은 모두 보존했지만 이 프로토콜 비대칭 때문에 warm 수치는 추세 참고용이다.

## 테스트와 관측 오버헤드

- `api\gradlew.bat test --no-daemon`: Java 단위·API·전체 Spring context 테스트 12개 통과
- `python -m unittest -v test_app test_runtime_state`: ML 단위·health/readiness/search API 9개 통과
- PowerShell parser: 측정 스크립트 문법 통과
- 2026-07-21 0% revision: recommend/ask 200, 각 정책 5건, 성공 구간 header와 request ID 확인
- 2026-07-22 보완: 배포 스크립트 dry-run과 `gradlew tasks` 통과; 새 revision 검증은 미실행

2차 리뷰 보완 후 50,000회 warmup, 9라운드, 모드당 50,000회로 현재 코드를 다시 측정한
중앙값은 비활성 144.558ns/op, 활성 6,582.766ns/op, 증분
**6,438.208ns/op(0.006438ms/op)** 이었다. 활성 라운드 범위는 6,321.526~8,457.882ns/op로
변동이 남아 있다. JMH가 아닌 로컬 JVM 마이크로벤치마크이며 disabled 경로의 객체가 escape하지
않으므로 대략적인 상한 수준의 코드 경로 비용으로만 해석한다. 현재 원본은
[observation-overhead-2026-07-22-post-review.csv](observation-overhead-2026-07-22-post-review.csv)다.
[1차 리뷰 보완 원본](observation-overhead-2026-07-22.csv)과
[2026-07-21 원본](observation-overhead-2026-07-21.csv)도 덮어쓰지 않고 보존했다.

## 한계

- 58,909ms 역사 요청에는 새 header가 없어 정확한 숫자 분해가 아니라 동일 입력 재현으로
  병목 후보를 확인했다. 역사 측정은 동기 startup, 관측 revision은 background loader라
  정확한 동일 시스템 재현은 아니다.
- 검증된 scale-to-zero 콜드 쌍은 각 조건 1개뿐이다. 1.99%는 반복 표본이 없어 성능
  개선으로 확정할 수 없다. 다음 측정은 조건별 최소 5쌍 pilot 뒤 분산으로 표본 수를 정한다.
- 두 요청을 동시에 보냈어도 Cloud Run의 instance 시작, 이미지 fetch, API queue는 달라진다.
- `/ready` startup probe가 적용되면 모델 준비는 ML handler 전 Cloud Run startup·queue 구간으로
  이동하고 `ml_model_wait`는 거의 0이 될 수 있다. API-side `api_to_ml`에는 이 대기가 포함되어
  `api_ml_transport`가 크게 보이지만 별도 startup segment로 분리되지는 않는다. instance 시작/probe
  로그와 client end-to-end를 함께 봐야 하며, probe 전후 CSV의 같은 열을 직접 비교하지 않는다.
- `client_api_residual`과 `api_ml_transport`는 여러 플랫폼·직렬화 요소가 섞인 잔여값이다.
- client 측 타이머는 응답 본문 파싱과 첫 실행 JIT 비용도 포함한다. 또한 `api_to_ml` 안에
  `ml_total`이 포함되는 식의 계층형 구간이므로 표의 모든 timer를 서로 더하면 이중 계산된다.
- DB 연결·쿼리는 분리했지만 Neon 휴면 해제 내부 단계는 보이지 않는다.
- Gemini는 외부 서비스 변동성이 있어 별도 warm 표본으로만 기록했다.
- 리뷰 보완 코드는 아직 Cloud Run 0% revision에서 실행하지 않았으므로 validated revision,
  새 콜드·웜 CSV, startup probe 로그가 남기 전에는 완료 상태가 아니다.

원인, 실패 탐지 누락과 후속 조치는 [포스트모템](POSTMORTEM_2026-07-21.md)에 정리했다.
