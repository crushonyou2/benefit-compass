# 콜드스타트·관측 배포 포스트모템 — 2026-07-21

## 영향

검증은 0% tagged revision에만 수행해 공개 사용자 영향은 없었다. 기준 API revision 두 개가
시작에 실패했지만 공개 traffic은 기존 revision 100%를 유지했다.

## 관찰된 원인

1. 동일 입력의 재현 첫 요청 35.328초 중 모델 readiness 대기가 26.097초(73.87%)로
   가장 컸다. 역사 58.909초의 지배 원인도 같은 모델 준비 경로로 판단하지만, 옛 요청에는
   구간 header가 없어 숫자를 소급 분해할 수는 없다.
2. background loader는 process health와 분리됐지만 Cloud Run의 요청 기반 CPU 할당 때문에
   유휴 중 거의 진행되지 않았다. 첫 검색이 CPU를 유지하는 동안 모델이 준비됐다.
3. 온라인 모드는 이미지에 모델이 있어도 HF Hub metadata 경로를 확인했고 warning을 남겼다.
   local-only는 이 외부 의존을 제거하고 통제된 콜드 쌍에서 모델 로드를 1.99% 줄였다.
4. warm 경로는 DB 연결 중앙값 약 430ms가 가장 컸다. 이 Lab에서는 연결 수명 변경의
   안정성·Neon 비용 영향을 함께 검증하지 않아 개선 범위에서 제외했다.

## 탐지에서 놓친 것

- component 단위 테스트가 생성자를 직접 호출해 실제 Spring constructor resolution을
  검증하지 못했다. 두 0% API revision이 순서대로 시작 실패했다.
- ML의 별도 logger는 Python 기본 WARNING 수준에 막혀 INFO 관측 이벤트가 Cloud Logging에
  나오지 않았다. HTTP access log와 timing header는 있었지만 계획한 cold log 상관관계가
  완전하지 않았다.

## 수정과 검증

- 주 생성자에 `@Autowired`를 명시하고 전체 Spring Boot context 시작 테스트를 추가했다.
- ML 관측을 Uvicorn logger에 연결하고 질문·나이가 로그에 없음을 테스트했다.
- 콜드 판정은 측정 CSV의 후보 표기와 별도로 Cloud Run `AUTOSCALING` instance 시작 및
  같은 instance의 첫 검색 200을 확인했다.
- 최종 `pl2-final` ML/API 0% revision에서 health/readiness, 검색, Gemini, timing header,
  INFO 로그를 재검증했다.

## 후속 작업

- local-only 1.99%는 콜드 쌍 n=1이므로 반복 측정 전 큰 성과로 확대 해석하지 않는다.
- 다음 Lab에서는 HTTP readiness startup probe나 모델 로드 방식 변경을 별도 실험하되,
  최소 인스턴스와 always-on CPU 없이 사용자 요청 지연이 실제로 줄어드는지 검증한다.
- DB connection 재사용은 warm 약 430ms 병목 후보지만, stale connection 복구와 Neon 유휴
  정책·비용을 함께 검증하기 전에는 적용하지 않는다.
