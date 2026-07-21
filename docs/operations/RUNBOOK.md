# 운영 런북

## 검색이 30초 이상 지연될 때

1. `/actuator/health`로 API 프로세스 상태를 확인한다.
2. 같은 시간대 `benefitcompass.http.server.duration`의 endpoint·status를 확인한다.
3. Cloud Run API와 ML 서비스 인스턴스의 콜드스타트 여부를 분리한다.
4. Neon 연결 실패, ML 서비스 준비 지연, Gemini 호출 지연 순서로 로그를 확인한다.
5. 질문 원문은 장애 조사 목적으로도 로그에 남기지 않는다.

### 구간 판별 순서

1. API 응답의 `Server-Timing`에서 `api_to_ml`, `ml_total`, `gemini`를 확인한다.
2. `api_to_ml`이 크고 `ml_total`이 작으면 `api_ml_transport`와 API/ML revision을 확인한다.
3. `ml_model_wait`가 크면 ML `/health`와 `/ready`를 각각 확인한다. `/health` 200은
   모델 준비 완료를 뜻하지 않는다.
4. `ml_db_connect`가 크면 Neon 휴면 해제·TLS 연결, `ml_db_query`가 크면 SQL/벡터 검색을 본다.
5. `/api/ask`에서만 `gemini`가 기록된다. 검색 전용 `/api/policies/recommend`에는 없다.

허용된 구간명 외 `Server-Timing` 값은 API가 버린다. 로그에는 request ID, 고정 구간명,
결과 건수와 시간만 남기고 요청 본문은 남기지 않는다.

## 콜드·웜 재현

공개 트래픽을 바꾸지 않은 새 tagged revision의 URL을 사용하되, 새 revision이라는 이유만으로
첫 요청을 콜드라고 단정하지 않는다. 배포 검증 과정에서 만들어진 인스턴스가 남아 있을 수 있다.
스크립트 첫 행은 `cold_candidate`로 저장하고, 같은 ML revision의 `ml_model_load`와
`ml_search` 로그가 해당 요청 직전에 같은 인스턴스에서 이어졌는지 확인된 경우에만 콜드로
판정한다. 기존 URL을 오래 방치했다는 이유만으로도 콜드라고 추정하지 않는다.

```powershell
.\scripts\measure-cold-warm.ps1 `
  -ApiBaseUrl 'https://TAGGED-REVISION-URL' `
  -Mode recommend `
  -Scenario 'before' `
  -Revision 'benefit-api-REVISION' `
  -Runs 6 `
  -FirstRequestColdCandidate `
  -OutputCsv '.\docs\operations\cold-warm-before-YYYY-MM-DD.csv'
```

스크립트는 2026-07-14 기준선과 같은 고정 비식별 질문을 메모리에서만 사용한다.
CSV에는 질문·나이 열이 없으며 revision, 요청 순서, 응답시간, 상태, 결과 건수,
고정 구간 시간만 저장한다. `cold_verification=pending_revision_log`인 행은 다음 형식의
로그 확인이 끝날 때까지 콜드 성과로 쓰지 않는다.

```powershell
gcloud logging read `
  'resource.type="cloud_run_revision" AND resource.labels.revision_name="ML_REVISION" AND (textPayload:"ml_model_load" OR textPayload:"ml_search")' `
  --freshness=30m `
  --format='table(timestamp,labels.instanceId,textPayload)'
```

애플리케이션 로그는 모델 이벤트, request ID, 고정 구간명·시간과 결과 건수만 포함한다.

## 5xx가 증가할 때

1. 응답의 `X-Request-ID`로 해당 요청 로그를 찾는다.
2. `/api/ask`와 `/api/policies/recommend` 중 영향 범위를 확인한다.
3. 외부 의존성별 상태를 확인하고, 불필요한 재시도로 부하를 키우지 않는다.
4. 사용자 영향·시작/종료 시각·원인·재발 방지책을 포스트모템에 기록한다.

## 무결과 비율이 증가할 때

1. `benefitcompass.search.requests{outcome="no_results"}` 비율을 확인한다.
2. 공공데이터 적재 건수와 임베딩 청크 수가 최근 배포 전후로 변했는지 확인한다.
3. 익명화되지 않은 실제 질문을 수집하지 말고, 자발적 피드백으로 평가셋 후보를 확보한다.
