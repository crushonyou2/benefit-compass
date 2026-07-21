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
