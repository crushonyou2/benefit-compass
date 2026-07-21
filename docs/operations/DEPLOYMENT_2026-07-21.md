# Production Lab 2 배포 기록 — 2026-07-21

## 안전 경계

- 프로젝트: `healthy-clock-465504-t5`, region: `asia-northeast3`
- 공개 traffic: API `benefit-api-00002-ndd`, ML `benefit-ml-00001-wvn` 각 100% 유지
- 새 revision은 모두 `--no-traffic` tag로만 검증
- 최소 인스턴스 미설정, CPU·메모리·concurrency·timeout 유지
- secret 값과 전체 환경 설정은 조회·출력하지 않음

## revision 순서

| 시도 | revision | 결과 |
|---|---|---|
| ML before | `benefit-ml-pl2b-3f11ebc` | 성공, 0%, `MODEL_LOCAL_ONLY=0` |
| API before 1 | `benefit-api-pl2b-3f11ebc` | 실패, Spring 생성자 선택 오류 |
| API before 2 | `benefit-api-pl2b-000a86b` | 실패, 다음 component의 같은 오류 |
| API before 3 | `benefit-api-pl2b-8577c94` | 성공, 0% |
| ML after | `benefit-ml-pl2a-8577c94` | 성공, 0%, 동일 이미지·local-only |
| API after | `benefit-api-pl2a-8577c94` | 성공, 0%, 동일 이미지 |
| ML final | `benefit-ml-pl2f-e0b0ada` | 성공, 0%, INFO 로그 수정 포함 |
| API final | `benefit-api-pl2f-e0b0ada` | 성공, 0%, final ML 연결 |

첫 API 실패는 `SegmentObservation`, 두 번째는 `MlClient`에 테스트 보조 생성자가 함께 있어
Spring이 주 생성자를 선택하지 못한 것이 원인이었다. `@Autowired`를 명시하고
`BenefitCompassApplicationContextTest`를 추가한 뒤 세 번째 배포가 성공했다.

최종 ML에서 모델 load start/complete와 안전한 `ml_search` INFO 로그를 Cloud Logging에서
확인했다. 최종 API의 recommend/ask는 각각 HTTP 200, 정책 5건, request ID,
`Server-Timing`, `X-ML-Model-Load-Ms`를 반환했다. `/api/ask`에는 `gemini` 구간도 있었다.

main 병합, push, 공개 traffic 변경, 외부 공개는 수행하지 않았다.

## 2026-07-22 리뷰 후 재검증

후속 코드 리뷰에서 위 최종 ML revision에 `/ready` startup probe가 없고 기본 TCP probe만
사용된 사실을 확인했다. 따라서 해당 revision의 검색·로그 측정은 유효하지만, 모델 준비 전
traffic을 차단하는 배포 후보로는 승인하지 않는다. 실패 응답 타이밍 보존, 안전한 API 오류
응답, `/ready` startup probe 조건을 로컬 코드와
`scripts/deploy-production-lab-2.ps1`에 보완했다.

2차 리뷰 뒤 첫 startup probe 예산은 120초에서 Cloud Run 상한인 240초로 넓혔고, 실측 뒤에만
낮추도록 파라미터화했다. 배포 스크립트는 `MODEL_LOCAL_ONLY=0/1`을 모두 만들 수 있으며
API/ML의 CPU·메모리·concurrency·timeout·max instances·port를 기존 실험값으로 명시한다.
MVC 405/415가 500으로 바뀌던 로컬 회귀도 수정했다. `--port=8080`은 기존 Cloud Run 기본값과
Dockerfile 기본값을 명시적으로 고정한 no-op 조건이다.

사용자 승인 뒤 커밋 `0ba0aa425db71430549b1ff4ac15419812a9d015`에서 API와 ML 이미지를
각각 한 번만 빌드했다.

| 역할 | Cloud Build ID | image digest |
|---|---|---|
| API | `ece820db-175a-4652-8eed-bcfd8b5d035e` | `sha256:f0e88ec2bb403867f156d762893e0f0804f378b4e75d49aba6e029c387474472` |
| ML | `38276cd9-65f6-45ac-83ca-8b009bdfad7d` | `sha256:1070274d936397be06e925a1eea52687f7df2597d499a7d2dc0c7f79e6954b14` |

before/after는 이 동일 digest를 사용한다. ML은 2 vCPU·2GiB·concurrency 160·timeout
300초·max instances 10·startup CPU boost·`/ready` HTTP startup probe 240초 예산,
API는 1 vCPU·1GiB·concurrency 80·timeout 300초·max instances 20·startup CPU boost다.
두 서비스 모두 min instances 기본값 0이고 `--no-traffic`으로 만들었다.

| 역할 | revision | 안전 조건 | 결과 |
|---|---|---|---|
| ML before | `benefit-ml-pl2b-0ba0aa4` | `MODEL_LOCAL_ONLY=0`, 0% | ready |
| ML after | `benefit-ml-pl2a-0ba0aa4` | `MODEL_LOCAL_ONLY=1`, 0% | ready |
| API before | `benefit-api-pl2b-0ba0aa4` | before ML tag 연결, 0% | ready |
| API after | `benefit-api-pl2a-0ba0aa4` | after ML tag 연결, 0% | ready |

첫 실제 ML 배포 시 `gcloud run deploy`가 `--max=10`을 인식하지 않아 revision 생성 전에
종료했다. Cloud Run 상태 변경은 없었다. 스크립트의 API/ML 플래그를 각각
`--max-instances=20/10`으로 고치고 dry-run assertion을 통과한 뒤 재실행했다. 이 오류와
수정은 커밋 `0ba0aa4` 뒤 작업 트리 변경으로 남긴다.

각 조건 5회의 scale-to-zero 측정에서 `/ready`는 모델 로딩 동안 503, 완료 뒤 200을 반환했고,
모든 첫 요청은 API와 ML 양쪽의 `AUTOSCALING` 새 instance로 확인됐다. 10개 모두 같은 ML
instance에서 모델 로딩 완료와 첫 검색 request ID가 이어졌다. 원본은
`cold-instance-evidence-2026-07-22.csv`에 있다.

배포 뒤 Cloud Run에서 다시 읽은 digest·CPU·memory·concurrency·timeout·max/min instances·
port·startup probe·tag·traffic의 안전한 필드 원본은
[`deployment-validation-2026-07-22.csv`](deployment-validation-2026-07-22.csv)에 보존했다.
전체 환경변수와 secret 값은 조회하거나 기록하지 않았다.

측정 시간대의 HF Hub warning은 before ML revision 5건, after ML revision 0건이었다.
after의 5개 cold 검색과 후속 warm 검색은 모두 200이어서 local-only의 정상 동작을 확인했다.

재검증 뒤에도 공개 traffic은 API `benefit-api-00002-ndd`, ML `benefit-ml-00001-wvn`에
각각 100%로 유지됐다. main 병합, push, 공개 traffic 전환과 외부 공개는 수행하지 않았다.
