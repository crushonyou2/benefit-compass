# 운영 런북

## 검색이 30초 이상 지연될 때

1. `/actuator/health`로 API 프로세스 상태를 확인한다.
2. 같은 시간대 `benefitcompass.http.server.duration`의 endpoint·status를 확인한다.
3. Cloud Run API와 ML 서비스 인스턴스의 콜드스타트 여부를 분리한다.
4. Neon 연결 실패, ML 서비스 준비 지연, Gemini 호출 지연 순서로 로그를 확인한다.
5. 질문 원문은 장애 조사 목적으로도 로그에 남기지 않는다.

## 5xx가 증가할 때

1. 응답의 `X-Request-ID`로 해당 요청 로그를 찾는다.
2. `/api/ask`와 `/api/policies/recommend` 중 영향 범위를 확인한다.
3. 외부 의존성별 상태를 확인하고, 불필요한 재시도로 부하를 키우지 않는다.
4. 사용자 영향·시작/종료 시각·원인·재발 방지책을 포스트모템에 기록한다.

## 무결과 비율이 증가할 때

1. `benefitcompass.search.requests{outcome="no_results"}` 비율을 확인한다.
2. 공공데이터 적재 건수와 임베딩 청크 수가 최근 배포 전후로 변했는지 확인한다.
3. 익명화되지 않은 실제 질문을 수집하지 말고, 자발적 피드백으로 평가셋 후보를 확보한다.
