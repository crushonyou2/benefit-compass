# 혜택나침반 운영 목표 초안

아래 값은 아직 달성 성과가 아니라 실사용 데이터를 수집하기 위한 초기 목표다. 2주간 기준선을 측정한 뒤 현실적인 SLO로 다시 정한다.

## 사용자 관점 지표

- 검색 성공: HTTP 2xx이면서 근거 정책이 1건 이상 반환됨
- 검색 무결과: 정상 응답이지만 근거 정책이 0건
- 검색 실패: HTTP 4xx·5xx 또는 프론트엔드 90초 타임아웃
- 핵심 지연시간: `/api/ask` 요청 완료 시간의 p50·p95

## 초기 목표

- API 성공률 99% 이상
- 웜 상태 `/api/ask` p95 10초 이하
- 콜드스타트 요청과 웜 요청을 분리해 기록
- 5xx가 5분 동안 3건 이상이면 확인

## 개인정보 원칙

- 질문 원문과 나이는 로그·메트릭에 저장하지 않는다.
- endpoint는 사전에 정의된 값만 태그로 사용한다.
- 검색 결과는 건수와 `results/no_results` 결과만 집계한다.

Prometheus 지표는 `/actuator/prometheus`, 상태 확인은 `/actuator/health`에서 제공한다.

## 구간 관측

`benefitcompass.segment.duration`은 아래 고정 `segment` 태그만 사용한다.

| segment | 의미 |
|---|---|
| `api_to_ml` | API가 ML `/search`를 호출해 응답 역직렬화를 마칠 때까지의 왕복 시간 |
| `api_ml_transport` | `api_to_ml - ml_total`; 네트워크·프록시·직렬화와 ML Cloud Run 인스턴스 시작·요청 큐가 합쳐진 잔여 시간 |
| `ml_model_wait` | 검색 요청이 모델 readiness를 기다린 시간 |
| `ml_embedding` | e5 질의 임베딩 시간 |
| `ml_db_connect` | DB 연결 수립 시간 |
| `ml_db_query` | pgvector SQL 실행·결과 수신 시간 |
| `ml_rerank` | cross-encoder 리랭킹 시간; 비활성 시 0 |
| `ml_total` | ML `/search` 내부 전체 시간 |
| `gemini` | 재시도를 포함한 Gemini 답변 생성 시간 |

측정 CSV의 `client_api_residual_ms`는 클라이언트가 본 전체 시간에서 `api_to_ml`과
`gemini`를 뺀 값이다. Cloud Run이 애플리케이션에 요청을 넘기기 전의 API 콜드스타트,
클라이언트↔API 네트워크와 API 직렬화 등이 함께 들어가므로 단일 원인으로 해석하지 않는다.

`outcome`은 `success`, `degraded`, `error`만 사용한다. 질문, 나이, 지역,
검색어 해시, 정책 ID는 태그나 로그에 넣지 않는다. 응답의 `Server-Timing`도 같은
고정 이름만 허용한다.

ML 서비스의 `/health`는 프로세스 생존만, `/ready`는 모델 준비 완료 여부와
모델 로딩 경과/완료 시간만 반환한다. 모델 이름이나 환경 변수 값, 사용자 입력은
상태 응답에 포함하지 않는다. Cloud Run ML revision은 HTTP startup probe를 `/ready`에
연결해 모델 준비 전에는 traffic을 받지 않아야 하며, `/health`를 startup probe로 쓰지 않는다.
현재 `/health`는 수동·로컬 liveness 진단용이고 Cloud Run liveness probe는 별도로 설정하지 않는다.
startup probe 뒤의 ML 인스턴스 시작·요청 큐 대기는 ML 내부 `ml_total` 밖이지만 API의
`api_ml_transport`에는 포함된다. 별도 segment로 분리되지는 않으므로 클라이언트 end-to-end,
`X-ML-Model-Load-Ms`, Cloud Run revision·instance 로그를 함께 본다. 모델 로드 header는 같은
인스턴스의 warm 응답에도 반복되므로 그 값 하나만으로 현재 요청을 콜드라고 판정하지 않는다.

고정 9 segment × 3 outcome Timer는 대시보드 계열을 안정시키기 위해 시작 시 등록되므로,
아직 발생하지 않은 조합도 `/actuator/prometheus`에 count 0으로 보일 수 있다.

2026-07-21의 0% tagged revision 실측값은 목표치가 아니라 운영 기준선이다. 콜드·웜·Gemini
원본과 해석 한계는 [Production Lab 2 결과](PRODUCTION_LAB_2_2026-07-21.md)에 기록한다.
