# 배포 기록 — 2026-07-14

## 변경 목적

- Spring Boot Actuator health endpoint 공개
- Prometheus 형식의 API 지연시간·상태 지표 추가
- 질문 원문 없이 요청을 추적하는 `X-Request-ID` 추가

## 첫 배포 실패

Cloud Build의 Linux 컨테이너에서 Windows CRLF 형식의 `gradlew`를 실행하지 못해 `./gradlew: not found`로 실패했다. 빌드가 실패했기 때문에 기존 정상 리비전과 사용자 트래픽에는 영향이 없었다.

## 수정

- Dockerfile 빌드 단계에서 `gradlew`의 CRLF를 LF로 정규화
- 저장소 루트 `.gitattributes`에 `gradlew text eol=lf` 추가

## 결과

- Cloud Run revision: `benefit-api-00002-ndd`
- traffic: 100%
- `/actuator/health`: `UP`
- `/actuator/prometheus`: HTTP 200
- `/api/policies/recommend`: HTTP 200, 정책 5건
- 응답에 `X-Request-ID` 포함

배포 직후 health endpoint로 API를 먼저 기동한 뒤 첫 검색은 33,396ms, 두 번째 검색은 1,072ms였다. API 프로세스를 먼저 깨운 상태에서도 검색 지연이 발생했으므로 다음 측정에서는 ML 서비스와 DB 연결 시간을 별도로 관측한다.

## 후속 조치

1. ML 서비스에 readiness와 모델 로딩 시간을 추가한다.
2. API에서 ML 호출 구간과 Gemini 호출 구간을 별도 타이머로 기록한다.
3. GitHub 인증 복구 후 현재 배포 소스를 저장소에 커밋·푸시한다.
