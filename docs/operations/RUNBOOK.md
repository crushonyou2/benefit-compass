# 운영 런북

## 검색이 30초 이상 지연될 때

1. `/actuator/health`로 API 프로세스 상태를 확인한다.
2. 같은 시간대 `benefitcompass.http.server.duration`의 endpoint·status를 확인한다.
3. Cloud Run API와 ML 서비스 인스턴스의 콜드스타트 여부를 분리한다.
4. Neon 연결 실패, ML 서비스 준비 지연, Gemini 호출 지연 순서로 로그를 확인한다.
5. 질문 원문은 장애 조사 목적으로도 로그에 남기지 않는다.

### 구간 판별 순서

1. API 응답의 `Server-Timing`에서 `api_to_ml`, `ml_total`, `gemini`를 확인한다.
2. `api_to_ml`이 크고 `ml_total`이 작으면 `api_ml_transport`를 본다. 이 값에는 실제
   네트워크·프록시뿐 아니라 ML Cloud Run 인스턴스 시작·요청 큐가 포함된다. 같은 revision의
   `AUTOSCALING` 새 instance와 첫 요청 로그가 이어지면 콜드로 판정하고, 새 instance 증거 없이
   계속 크면 네트워크·프록시 경로를 조사한다. `X-ML-Model-Load-Ms`는 규모 비교에 쓰되 같은
   instance의 warm 응답에도 반복되므로 단독 판정자로 쓰지 않는다.
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

Cloud Run의 요청 기반 CPU에서는 process가 살아 있어도 background 모델 loader가 유휴 중
거의 진행되지 않을 수 있다. `/health` 200과 경과 wall time만으로 모델이 CPU를 계속 사용했다고
가정하지 않는다. 확정 측정은 scale-to-zero 후 `AUTOSCALING` 새 instance 시작, 같은 instance의
첫 검색, 응답의 `ml_model_wait`·`X-ML-Model-Load-Ms`를 함께 확인한다.

ML 배포 후보는 `/ready` HTTP startup probe가 200이 되기 전 traffic을 받지 않아야 한다.
저장소의 배포 스크립트는 기본이 dry-run이며, 사용자 승인 뒤에만 `-Execute`를 붙인다.
dry-run은 gcloud 플래그 유효성까지 검사하지 않는다. 2026-07-22에는 `--max`가 실제 CLI에서
거부된 뒤 `--max-instances`로 수정됐다. gcloud 버전 변경 뒤에는 parser/dry-run뿐 아니라
0% canary 한 건의 실제 종료 코드도 확인한다.

```powershell
.\scripts\deploy-production-lab-2.ps1 `
  -Stage Ml `
  -Image 'asia-northeast3-docker.pkg.dev/PROJECT/REPOSITORY/IMAGE@sha256:DIGEST' `
  -RevisionSuffix 'pl2r-COMMIT' `
  -Tag 'pl2-before' `
  -ModelLocalOnly 0 `
  -StartupFailureThreshold 120 # dry-run; 실행 승인 전에는 -Execute 금지
```

이 명령은 최소 인스턴스 0, startup CPU boost, `--no-traffic`, `/ready` startup probe
(2초 간격 120회, Cloud Run 상한인 최대 240초), 기존과 같은 ML 2 vCPU·2GiB·concurrency
160·timeout 300초·max 10을 명시한다. 첫 검증에서 실제 `model_load_ms`를 확보한 뒤에만
threshold를 낮춘다. after 조건은 같은 이미지와 인자를 유지하고 `-ModelLocalOnly 1`만 바꾼다.
ML tag URL을 확인한 뒤 API 단계에는
`-Stage Api -MlBaseUrl 'https://ML-TAG-URL'`을 사용한다. 이미지 digest와 실제 명령,
생성 revision은 배포 기록에 남긴다.

사용자 승인 후 `-Execute`를 붙일 때는 먼저 같은 인자의 dry-run 출력을 배포 기록에 복사하고,
실행 출력도 다음처럼 별도 원본 로그로 보존한다. 이 명령에는 secret 값이나 전체 환경 조회를
추가하지 않는다.

```powershell
$deploymentAttemptLog = '.\docs\operations\deployment-attempt-YYYY-MM-DD.log'
$approvedDeployParameters = @{
  Stage = 'Ml'
  Image = 'asia-northeast3-docker.pkg.dev/PROJECT/REPOSITORY/IMAGE@sha256:DIGEST'
  RevisionSuffix = 'pl2r-COMMIT'
  Tag = 'pl2-before'
  ModelLocalOnly = '0'
  StartupFailureThreshold = 120
}
Start-Transcript -LiteralPath $deploymentAttemptLog
try {
  .\scripts\deploy-production-lab-2.ps1 @approvedDeployParameters -Execute
} finally {
  Stop-Transcript
}
```

probe의 성공 조건과 제한은 [Cloud Run health check 문서](https://docs.cloud.google.com/run/docs/configuring/healthchecks),
startup CPU 동작은 [Cloud Run CPU 문서](https://docs.cloud.google.com/run/docs/configuring/services/cpu)를 기준으로 한다.

startup probe가 적용되면 정상 첫 요청의 `ml_model_wait`는 거의 0이 되고, 모델 준비 대기는
ML 애플리케이션에 도달하기 전 Cloud Run 요청 큐에 포함될 수 있다. API의 `api_to_ml`은 이 대기를
포함하므로 `api_ml_transport`가 크게 보이지만 별도 startup segment로 분리된 것은 아니다.
instance 시작 로그, startup probe 통과 시각, 클라이언트 end-to-end를 함께 기록한다.
probe 전후 CSV에서 같은 `api_ml_transport` 열은 구성 요소가 달라질 수 있으므로 직접 성능 비교하지
않는다. `/health`는 현재 Cloud Run probe 소비자가 아니라 수동·로컬 liveness 진단면이다.

로딩 중 `/ready` 503 반복은 정상이다. probe가 240초 안에 통과하지 못하면 배포 명령이 non-zero로
끝나며 스크립트가 실패한다. 이때 재실행부터 하지 말고 다음 명령으로 revision ready 상태와 tag
부여 여부를 확인한 뒤 `ml_model_load event=error` 또는 timeout 증거를 배포 기록에 남긴다.

```powershell
gcloud run revisions list --service benefit-ml --region asia-northeast3 `
  --project healthy-clock-465504-t5
```

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

검증된 명령·원본 CSV·로그 증거 예시는
[Production Lab 2 결과](PRODUCTION_LAB_2_2026-07-21.md)를 따른다.

2026-07-22 검증값은 15분 유휴 5쌍이며 10/10 첫 요청이 API·ML 새 instance로 확인됐다.
`MODEL_LOCAL_ONLY=1`에서 모델 로딩 중앙값 24.239초→23.093초가 관측됐지만 paired 평균과
cold 전체 중앙값은 개선하지 못했다. 성능 효과는 미확정이므로 이 토글만으로 공개 traffic을
전환하지 않는다.

## 5xx가 증가할 때

1. 응답의 `X-Request-ID`로 해당 요청 로그를 찾는다.
2. `/api/ask`와 `/api/policies/recommend` 중 영향 범위를 확인한다.
3. 외부 의존성별 상태를 확인하고, 불필요한 재시도로 부하를 키우지 않는다.
4. 사용자 영향·시작/종료 시각·원인·재발 방지책을 포스트모템에 기록한다.

## 무결과 비율이 증가할 때

1. `benefitcompass.search.requests{outcome="no_results"}` 비율을 확인한다.
2. 공공데이터 적재 건수와 임베딩 청크 수가 최근 배포 전후로 변했는지 확인한다.
3. 익명화되지 않은 실제 질문을 수집하지 말고, 자발적 피드백으로 평가셋 후보를 확보한다.
