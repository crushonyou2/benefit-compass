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

## 2026-07-22 리뷰 후 상태

후속 코드 리뷰에서 위 최종 ML revision에 `/ready` startup probe가 없고 기본 TCP probe만
사용된 사실을 확인했다. 따라서 해당 revision의 검색·로그 측정은 유효하지만, 모델 준비 전
traffic을 차단하는 배포 후보로는 승인하지 않는다. 실패 응답 타이밍 보존, 안전한 API 오류
응답, `/ready` startup probe 조건을 로컬 코드와
`scripts/deploy-production-lab-2.ps1`에 보완했다.

이 보완 코드는 아직 Cloud Run에 재배포하지 않았다. 새 ML/API 0% revision, startup probe
성공, 실패/성공 타이밍 헤더, 동일 조건 콜드·웜 재측정이 확인될 때까지 Production Lab 2의
배포 검증은 **재검증 대기**다. 공개 traffic과 기존 revision은 변경하지 않았다.

2차 리뷰 뒤 첫 startup probe 예산은 120초에서 Cloud Run 상한인 240초로 넓혔고, 실측 뒤에만
낮추도록 파라미터화했다. 배포 스크립트는 `MODEL_LOCAL_ONLY=0/1`을 모두 만들 수 있으며
API/ML의 CPU·메모리·concurrency·timeout·max·port를 기존 실험값으로 명시한다. MVC 405/415가
500으로 바뀌던 로컬 회귀도 수정했으며 새 revision은 여전히 만들지 않았다. `--port=8080`은
기존 Cloud Run 기본값과 Dockerfile 기본값을 명시적으로 고정한 no-op 조건으로 추가했다.
