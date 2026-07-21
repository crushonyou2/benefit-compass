# 콜드스타트·관측 배포 포스트모템 — 2026-07-21

## 영향

검증은 0% tagged revision에만 수행해 공개 사용자 영향은 없었다. 기준 API revision 두 개가
시작에 실패했지만 공개 traffic은 기존 revision 100%를 유지했다.

2026-07-22 재검증도 새 API/ML revision 네 개를 0% tag로만 만들었다. 공개 traffic과
min instances는 바꾸지 않았다. 첫 재배포 명령은 잘못된 `--max=10` 플래그 때문에 revision
생성 전에 종료됐고 서비스 상태 변화나 사용자 영향은 없었다.

## 2026-07-22 재검증 결론

1. 같은 API/ML digest·자원에서 `MODEL_LOCAL_ONLY=0/1`만 달리해 scale-to-zero cold 5쌍을
   수집했다. 10개 첫 요청 모두 API·ML 새 instance와 request ID로 cold가 검증됐다.
2. `/ready` startup probe 적용 뒤 정상 첫 검색의 `ml_model_wait`는 약 0.01ms였다. 모델 준비
   대기는 사라진 것이 아니라 ML handler 전 Cloud Run startup·queue로 이동했고,
   `api_ml_transport` 중앙값이 약 26~27초로 가장 컸다.
3. local-only에서 모델 로딩 중앙값은 24.239초에서 23.093초로 1.146초(4.73%) 작은 값이
   관측됐다. 하지만 paired 평균 모델 로딩은 악화됐고 cold end-to-end 중앙값도 37.678초에서
   37.781초로 0.103초 늘었다. 성능 개선은 미확정이며, 외부 Hub 의존 제거와 정상 동작만
   확인됐다.
4. pair별 모델 로딩 차이는 -2.674~+4.887초, end-to-end 차이는 -2.622~+5.102초였다.
   Cloud Run instance 시작·CPU 스케줄링, 첫 embedding, DB 연결·쿼리 변동이 남아 있어
   5쌍으로 공개 traffic 전환이나 통계적 효과를 주장할 수 없다.

배포 실패의 직접 원인은 gcloud가 `--max`를 지원하지 않는다는 점이었다. dry-run은 명령을
출력만 하고 CLI 유효성을 검사하지 않아 이를 잡지 못했다. API/ML 모두
`--max-instances=20/10`으로 수정했고, 이후 실제 0% 배포와 dry-run assertion이 통과했다.

## 관찰된 원인

1. 동일 입력의 재현 첫 요청 35.328초 중 모델 readiness 대기가 26.097초(73.87%)로
   가장 컸다. 역사 58.909초의 지배 원인도 같은 모델 준비 경로로 판단하지만, 옛 요청에는
   구간 header가 없어 숫자를 소급 분해할 수는 없다.
2. background loader는 process health와 분리됐지만 Cloud Run의 요청 기반 CPU 할당 때문에
   유휴 중 거의 진행되지 않았다. 첫 검색이 CPU를 유지하는 동안 모델이 준비됐다.
3. 온라인 모드는 이미지에 모델이 있어도 HF Hub metadata 경로를 확인했고 warning을 남겼다.
   local-only는 이 외부 의존을 제거했다. 통제된 콜드 쌍의 모델 로드 차이는 1.99%였지만
   조건별 표본 1개라 성능 개선으로 확정하지 않는다.
4. warm 경로는 DB 연결 중앙값 약 430ms가 가장 컸다. 이 Lab에서는 연결 수명 변경의
   안정성·Neon 비용 영향을 함께 검증하지 않아 개선 범위에서 제외했다.

## 탐지에서 놓친 것

- component 단위 테스트가 생성자를 직접 호출해 실제 Spring constructor resolution을
  검증하지 못했다. 두 0% API revision이 순서대로 시작 실패했다.
- ML의 별도 logger는 Python 기본 WARNING 수준에 막혀 INFO 관측 이벤트가 Cloud Logging에
  나오지 않았다. HTTP access log와 timing header는 있었지만 계획한 cold log 상관관계가
  완전하지 않았다.
- 후속 리뷰에서 ML background loader와 배포 기본 TCP startup probe의 계약 불일치를
  발견했다. process가 포트를 열면 모델 준비 전에도 revision이 준비된 것으로 판정될 수 있었고,
  `/ready`는 존재하지만 실제 probe에 연결되지 않았다.
- ML 5xx는 타이밍 header를 만들지 않았고 API도 하위 5xx header를 수집하지 않아, 실패 요청은
  가장 필요한 구간 증거가 빠졌다.

## 수정과 검증

- 주 생성자에 `@Autowired`를 명시하고 전체 Spring Boot context 시작 테스트를 추가했다.
- ML 관측을 Uvicorn logger에 연결하고 질문·나이가 로그에 없음을 테스트했다.
- 콜드 판정은 측정 CSV의 후보 표기와 별도로 Cloud Run `AUTOSCALING` instance 시작 및
  같은 instance의 첫 검색 200을 확인했다.
- 최종 `pl2-final` ML/API 0% revision에서 health/readiness, 검색, Gemini, timing header,
  INFO 로그를 재검증했다.
- 2026-07-22 로컬 보완에서 `/ready` startup probe 배포 조건, 성공·실패 공통 timing header,
  고정 API 오류 응답, reranker local-only 전달을 추가했다. 2차 리뷰에서 MVC 405/415 상태 보존,
  최대 240초 첫 probe 예산, before/after 배포 인자를 추가했다. 새 0% API/ML revision 네 개에서
  probe, recommend/ask, timing header와 cold instance 증거를 검증했고 Java 테스트 12개와
  Python 테스트 9개가 통과했다.

## 후속 작업

- 5쌍 pilot에서 모델 로딩 중앙값 감소가 관측됐지만 인과적 성능 개선과 end-to-end 개선은
  확인되지 않았다. 공개 traffic
  전환 전에 표본 수를 늘리거나, 더 큰 병목인 startup queue와 이미지/model load 자체를 줄이는
  별도 비용 없는 변경을 검증한다.
- `/ready` startup probe 240초 예산은 모든 표본에서 통과했다. 예산 축소는 더 다양한 cold
  표본과 최악값을 확보한 뒤 별도 변경으로 검증한다. 최소 인스턴스와 always-on CPU는 사용하지 않는다.
- DB connection 재사용은 warm 약 430ms 병목 후보지만, stale connection 복구와 Neon 유휴
  정책·비용을 함께 검증하기 전에는 적용하지 않는다.
