# Production Lab 2 — 콜드스타트 구간 관측과 무비용 개선

상태: **배포 전 로컬 검증 완료, 실제 revision 검증 대기**

## 목적

2026-07-14 검색 전용 첫 요청 58,909ms를 API→ML 통신, ML 모델 로딩·준비,
임베딩, DB 연결·검색으로 분리한다. `/api/ask`에서는 Gemini 생성 시간도 별도로
관측한다. 그 증거를 바탕으로 최소 인스턴스 없이 개선 하나를 같은 조건에서 비교한다.

## 개인정보 경계

- API와 ML 로그에는 질문 원문·나이·지역을 기록하지 않는다.
- 메트릭 태그는 고정 endpoint, status class, segment, outcome만 허용한다.
- API가 ML의 `Server-Timing`을 받을 때도 허용 목록 밖 이름은 버린다.
- 측정 스크립트는 고정 합성 질문을 요청 메모리에서만 사용하며 CSV에는 저장하지 않는다.
- CSV의 request ID는 요청 본문과 무관한 난수 식별자다.

## 관측 구조

검색 요청은 다음 값으로 분해된다.

```text
API 전체 요청
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

ML `/health`는 프로세스 생존, `/ready`는 모델 준비 상태를 나타낸다. 모델 import와
가중치 로딩은 백그라운드 loader의 시작부터 완료까지 측정되고 `/ready`와
`X-ML-Model-Load-Ms`에 노출된다. 첫 검색이 로딩 중 들어오면 실패시키지 않고 readiness를
기다린 시간을 `ml_model_wait`로 기록한다.

## 로컬 검증

2026-07-21 KST 실행 결과:

- `api\gradlew.bat test --no-daemon`: Java 단위·API 테스트 7개 통과
- `python -m unittest -v`: ML 단위·health/readiness/search API 테스트 6개 통과
- PowerShell parser로 `scripts/measure-cold-warm.ps1` 문법 확인
- 현재 공개 API에서 스크립트가 HTTP 200과 결과 5건을 읽는 스모크 테스트 확인

스모크 테스트는 tagged revision의 첫 요청이 아니어서 콜드·웜 성과에는 포함하지 않는다.

## 관측 오버헤드

`SEGMENT_OBSERVABILITY_ENABLED=false/true`와 같은 실행 경로를 7라운드,
라운드별 모드당 20,000회 비교했다. 중앙값은 비활성 165.455ns/op,
활성 6,908.550ns/op, 증분 **6,743.095ns/op(0.006743ms/op)** 이었다.

이는 로컬 JVM 마이크로벤치마크이며 Cloud Run 네트워크 지연을 뜻하지 않는다.
원본은 [observation-overhead-2026-07-21.csv](observation-overhead-2026-07-21.csv),
재현 명령은 다음과 같다.

```powershell
cd api
.\gradlew.bat observationOverhead --no-daemon `
  -PoverheadOutput=C:\absolute\path\observation-overhead.csv
```

## 실제 환경 비교 설계

기존 공개 traffic은 API `benefit-api-00002-ndd`, ML `benefit-ml-00001-wvn`에
각각 100% 유지한다. 최소 인스턴스는 설정하지 않는다.

1. 관측 코드 + `MODEL_LOCAL_ONLY=0`인 API/ML revision을 `--no-traffic` 태그로 배포한다.
2. 새 API 태그 URL의 첫 검색 1회와 연속 웜 검색 5회를 `before` CSV로 저장한다.
3. 모델이 이미지에 이미 포함된 조건에서 외부 모델 조회를 금지하는
   `MODEL_LOCAL_ONLY=1`만 바꾼 ML revision과 이를 가리키는 API revision을 새 태그로 만든다.
4. 같은 입력·리소스·지역·횟수로 `after` CSV를 저장한다.
5. 두 revision에서 웜 `/api/ask`도 실행해 Gemini 시간을 별도 CSV로 확인한다.

Sentence Transformers의
[`local_files_only`](https://www.sbert.net/docs/package_reference/sentence_transformer/model.html)는
로컬 파일만 사용하도록 제한한다. 이 프로젝트는 모델을 이미지 빌드 단계에 미리 내려받으므로
최소 인스턴스나 CPU·메모리 증설 없이 적용할 수 있다. 실제 개선 여부는 배포 후 CSV로만
판정하며, 감소를 미리 성과로 기록하지 않는다.

## 배포·측정 결과

사용자 승인 전이므로 아직 배포하지 않았다. revision, 전후 CSV와 병목 판정은 실제 측정 후
이 절을 갱신한다.

## 한계와 포스트모템

실제 측정 전에는 원인이나 개선 효과를 확정하지 않는다. 현재 알려진 측정 한계는 다음과 같다.

- tagged revision의 첫 요청은 API와 ML을 함께 콜드로 만들지만 Cloud Run 이미지 fetch 등
  플랫폼 구간은 애플리케이션 내부 타이머 밖에 있다.
- `api_ml_transport`는 순수 네트워크 RTT가 아니라 프록시·직렬화/역직렬화 잔여 시간이다.
- DB 연결과 쿼리는 분리하지만 Neon 내부 휴면 해제 세부 단계까지는 보이지 않는다.
- Gemini는 외부 서비스 변동성이 있으므로 검색 콜드스타트 비교와 분리한다.

최종 포스트모템은 두 revision의 원본 CSV와 Cloud Run revision 검증 후 작성한다.
