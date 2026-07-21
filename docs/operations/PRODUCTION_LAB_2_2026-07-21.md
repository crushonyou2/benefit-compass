# Production Lab 2 — 콜드스타트 구간 관측과 무비용 개선

상태: **0% tagged revision 실환경 재검증 완료 — 공개 traffic 미변경**

## 결론

### 2026-07-22 최종 재검증

리뷰 보완 코드를 커밋 `0ba0aa425db71430549b1ff4ac15419812a9d015`에서 다시 빌드해,
같은 API/ML image digest와 같은 자원 조건으로 before/after 0% revision을 만들었다. ML은
`/ready` startup probe가 모델 준비 전 traffic을 차단했고, 모델 준비 뒤 첫 검색의
`ml_model_wait` 중앙값은 before 0.011ms, after 0.013ms였다. 모델 준비 시간은 ML handler 밖
Cloud Run startup·request queue로 이동해 `api_ml_transport`에 포함됐다.

15분 유휴 뒤 전/후를 동시에 호출하는 절차를 5쌍 반복했다. 10개 첫 요청 모두 API와 ML의
`AUTOSCALING` 새 instance, 같은 ML instance의 모델 로딩 완료, CSV request ID의 첫 검색
완료로 콜드가 확인됐다. 검색은 전부 HTTP 200, 정책 5건이었다.

비용 없는 변경 `MODEL_LOCAL_ONLY=1`의 모델 로딩 중앙값은 24,239.065ms에서
23,092.880ms로 **1,146.185ms(4.73%) 감소**했다. 다만 pair별 모델 로딩 차이는
-2,673.688~+4,887.150ms로 변동이 컸다. cold end-to-end 중앙값은
37,678.160ms에서 37,781.083ms로 102.923ms(0.27%) 늘었고, paired 평균 차이도
+1,480.316ms였다. 따라서 **모델 로딩 중앙값 감소는 관측됐지만 성능 개선은 미확정이고,
검증된 개선은 런타임 Hub 의존 제거와 정상 동작이다.** end-to-end 개선도 검증되지 않았다.
이 제한을 성과에서 숨기지 않는다.

실제 5개 ML instance의 Cloud Logging에서 before는 HF Hub unauthenticated warning 5건,
after는 0건이었다. Python 회귀 테스트는 local-only가 모델 import 전에 offline 환경과
`local_files_only`를 적용함을 확인한다. 이 두 증거와 after 5/5 검색 성공을 근거로 외부 Hub
의존 제거와 정상 동작을 검증했다.

5쌍의 지배 구간은 `api_ml_transport` 중앙값 26,962.727ms(before),
25,934.645ms(after)였다. 이는 단순 네트워크가 아니라 ML scale-from-zero, 모델 startup
probe 대기, Cloud Run queue를 포함한다. ML 내부에서 다음으로 큰 구간은 첫 embedding이었고,
DB 연결과 쿼리가 뒤를 이었다. 별도 warm `/api/ask` 2회의 Gemini 중앙값은
929.058ms/920.690ms로 정상 분리됐다.

### 2026-07-21 초기 실험

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

후속 리뷰에서 background loader를 도입한 초기 관측 revision에 `/ready` startup probe가
연결되지 않아 모델 준비 전 traffic을 받을 수 있음을 확인했다. 이 초기 revision은 배포 후보로
승인하지 않았다. 위 2026-07-22 재검증은 `/ready` probe, 실패 응답 구간 header와 안전한 API
오류 응답을 포함한 새 0% revision에서 수행했다.

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
| 2026-07-22 before | `benefit-api-pl2b-0ba0aa4` | `benefit-ml-pl2b-0ba0aa4` | 0% tag |
| 2026-07-22 after | `benefit-api-pl2a-0ba0aa4` | `benefit-ml-pl2a-0ba0aa4` | 0% tag |

before/after ML은 같은 이미지 digest `sha256:73aaf7be...020b8c`, API는 같은
`sha256:f9c84d5e...f26d8`를 사용한다. 차이는 `MODEL_LOCAL_ONLY=0/1`뿐이다.
API는 1 vCPU·1GiB·concurrency 80·timeout 300s·max 20, ML은 2 vCPU·2GiB·
concurrency 160·timeout 300s·max 10이다. 두 서비스 모두 `minScale` 주석이 없고
startup CPU boost만 기존대로 켜져 있다. 최소 인스턴스, CPU·메모리 증설, 공개 traffic
변경은 없었다.

2026-07-22 before/after API는 동일 digest
`sha256:f0e88ec2bb403867f156d762893e0f0804f378b4e75d49aba6e029c387474472`, ML은 동일 digest
`sha256:1070274d936397be06e925a1eea52687f7df2597d499a7d2dc0c7f79e6954b14`를 사용했다.
ML 조건 차이는 `MODEL_LOCAL_ONLY=0/1`, API 조건 차이는 각각의 ML tag URL뿐이다.
ML `/ready` startup probe는 2초 간격·최대 120회로 적용됐다. 실제 revision 설정과 공개
traffic 불변 확인은 [배포 기록](DEPLOYMENT_2026-07-21.md)에 있다.

기존 최종 revision은 검색과 `/api/ask` 모두 200/정책 5건을 반환했다. ML 로그에는
`ml_model_load` start/complete와 `ml_search`의 request ID·결과 건수·고정 구간 시간만
남았고 질문·나이는 없었다. 다만 `/ready` startup probe 누락 때문에 이 revision을 새 배포
후보로 승인하지 않는다. 상세 revision, 두 번의 API 시작 실패와 2026-07-22 재검증은
[배포 기록](DEPLOYMENT_2026-07-21.md)에 남겼다.

## 실측 결과

### 2026-07-22 startup probe 적용 5-pair pilot

아래 값은 조건별 cold 5개의 중앙값이다. 각 열의 중앙값은 서로 다른 pair에서 나올 수 있어
행을 합산해 end-to-end를 재구성하지 않는다.

| 지표 | before ms | after ms | 변화 |
|---|---:|---:|---:|
| client/API 잔여 | 5,798.561 | 5,201.000 | -597.561 |
| API→ML | 31,103.971 | 32,591.339 | +1,487.368 |
| API↔ML transport/startup queue | 26,962.727 | 25,934.645 | -1,028.082 |
| ML model wait | 0.011 | 0.013 | +0.002 |
| 첫 embedding | 1,908.034 | 3,895.305 | +1,987.271 |
| DB 연결 | 1,085.569 | 529.897 | -555.672 |
| DB 쿼리 | 977.615 | 233.552 | -744.063 |
| ML 전체 | 4,158.352 | 4,685.215 | +526.863 |
| 모델 로딩 | 24,239.065 | 23,092.880 | **-1,146.185 (-4.73%)** |
| end-to-end | 37,678.160 | 37,781.083 | **+102.923 (+0.27%)** |

| pair | before 전체 ms | after 전체 ms | after-before ms | before 모델 로딩 ms | after 모델 로딩 ms |
|---:|---:|---:|---:|---:|---:|
| 1 | 36,902.532 | 37,781.083 | +878.551 | 23,970.425 | 21,541.786 |
| 2 | 36,229.780 | 35,820.860 | -408.920 | 23,804.688 | 22,099.894 |
| 3 | 39,172.488 | 44,274.400 | +5,101.912 | 25,772.472 | 30,659.622 |
| 4 | 37,678.160 | 42,130.594 | +4,452.434 | 24,239.065 | 28,763.193 |
| 5 | 38,514.074 | 35,891.678 | -2,622.396 | 25,766.568 | 23,092.880 |

모델 로딩은 after가 3쌍에서 빠르고 2쌍에서 느렸다. 중앙값은 개선됐지만 Cloud Run CPU
스케줄링과 모델 파일 역직렬화 변동이 남았다. end-to-end는 after가 2쌍에서만 빨랐으며,
플랫폼 queue·첫 embedding·DB 변동이 모델 로딩 차이를 상쇄했다. 그러므로 local-only를
공개 traffic으로 전환할 근거는 아직 아니다. 5-pair pilot에서 모델 로딩 중앙값 감소는
관측됐지만 성능 개선은 미확정이며, 외부 Hub 의존 제거와 정상 동작만 검증된 것으로 판정한다.

warm 검색 중앙값은 before 774.530ms, after 767.892ms였다. warm `/api/ask` 2회의 Gemini
중앙값은 929.058ms/920.690ms였고 두 조건 모두 HTTP 200, 정책 source 5건이었다.

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

2026-07-22 최종 재검증 원본:

- [before 통합 CSV](cold-paired-before-2026-07-22.csv)와 pair별 원본
  `cold-paired-before-2026-07-22-p1.csv`~`p5.csv`
- [after 통합 CSV](cold-paired-after-2026-07-22.csv)와 pair별 원본
  `cold-paired-after-2026-07-22-p1.csv`~`p5.csv`
- [pair 비교 CSV](cold-paired-summary-2026-07-22.csv)
- [API·ML cold instance 증거 CSV](cold-instance-evidence-2026-07-22.csv)
- [배포 revision 안전 설정 검증 CSV](deployment-validation-2026-07-22.csv)
- [before Gemini warm CSV](gemini-warm-before-2026-07-22.csv)
- [after Gemini warm CSV](gemini-warm-after-2026-07-22.csv)

각 pair는 앞선 요청 종료 뒤 15분 유휴, 전/후 병렬 시작, 조건별 첫 cold candidate와 즉시
warm 1회로 수집했다. pair별 원본은 수정하지 않았고 통합·요약 CSV는 원본을 기계적으로
결합했다. CSV schema에는 질문·나이·지역 열이 없다.

2026-07-21 초기 실험 원본:

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
- 2026-07-22 최종: Java 12개, Python 9개, PowerShell parser와 배포 dry-run safety assertion
  통과. 정본의 한글 상위 경로에서 Gradle test classpath가 깨지는 Windows 환경 문제는
  `C:\tmp\benefit-compass-pl2` ASCII junction에서 `clean test`를 다시 실행해 12/12 통과로
  확인했다. 임시 Python venv에는 `requirements-test.txt`만 설치했다.
- 새 0% revision: recommend 10개 cold+10개 warm, ask 4개 warm 모두 HTTP 200·정책 5건,
  고정 timing header와 request ID 확인. 10/10 cold 후보는 revision·instance 로그로 확정했다.

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
- 최종 scale-to-zero pilot은 조건별 5개뿐이다. 모델 로딩 중앙값은 4.73% 감소했지만
  pair별 차이가 -2.674~+4.887초이고 end-to-end 중앙값은 개선되지 않았다. 신뢰구간이나
  공개 traffic 전환 판단에는 표본이 부족하다.
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
- 측정은 0% tag에서만 수행했다. 공개 traffic 사용자 분포, 동시 부하, 장시간 안정성은
  검증하지 않았으며 사용자 승인 전에는 공개 revision으로 전환하지 않는다.

원인, 실패 탐지 누락과 후속 조치는 [포스트모템](POSTMORTEM_2026-07-21.md)에 정리했다.
