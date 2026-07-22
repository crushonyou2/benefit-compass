# 정본·공개 상태 재검증 — 2026-07-22

## 범위와 안전 경계

- 코딩 정본: `C:\Users\joji\Documents\취준자료\project-repos\benefit-compass`
- 공개 저장소: `crushonyou2/benefit-compass`
- Cloud Run project/region: `healthy-clock-465504-t5` / `asia-northeast3`
- GitHub·Pages·Cloud Run은 읽기 전용으로 확인했다.
- Cloud Run은 traffic, image, CPU, memory, concurrency, timeout, instance 한도,
  port, startup probe와 명시적으로 허용한 비민감 설정만 조회했다.
- secret 값, 전체 환경 변수, 질문 원문, 나이와 지역은 조회 결과에 기록하지 않았다.

## Git과 GitHub

| 항목 | 2026-07-22 확인값 |
|---|---|
| 재검증 대상 로컬 브랜치 | `codex/production-lab-2` |
| 재검증 시작 HEAD | `af8ed6647bcd2fec74116b40869767e6fe40d897` |
| 로컬 `main` / `origin/main` | `78170156307d17e92b3bd7269453347522aa00d0` |
| 재검증 시작 ahead/behind | `8/0` |
| 재검증 시작 작업 트리 | clean |
| 원격 `codex/production-lab-2` | 없음 |
| 공개 main CI | `7817015`의 API quality gate 성공 |
| 별도 CI draft PR | `#3`, `chore/git-workflow`, open·unmerged |

Production Lab 2는 아직 GitHub branch나 PR로 보존되지 않았고 CI도 실행되지 않았다.
PR #3의 web build·Python syntax 범위는 PL2의 API·ML test workflow와 중복 없이 통합한 뒤
PR #3 자체의 처리 여부를 결정한다.

## GitHub Pages

| 항목 | 확인값 |
|---|---|
| `gh-pages` HEAD | `93c1a5705794488295114c55b1a49fcfdce6f6e7` |
| commit 시각 | 2026-06-23 16:03:15 UTC |
| Pages 배포 | 성공 |
| 라이브 응답 | HTTP 200 |
| 배포 JS | `/benefit-compass/assets/index-C8-US8xf.js` |
| JS의 API URL | `https://benefit-api-866560009438.asia-northeast3.run.app` |

배포 JS에는 현재 `main`의 90초 timeout과 단계별 콜드스타트 안내가 없다. 지역 입력은 없고
지역명 대신 지원 내용을 입력하라는 안내는 존재한다. 따라서 Pages와 현재 web source는
완전히 같지 않다. 프론트 변경을 실제로 공개할 때만 새 Pages 배포를 검토한다.

## Cloud Run traffic과 artifact

| 역할 | 공개 revision | traffic | image digest |
|---|---|---:|---|
| API | `benefit-api-00002-ndd` | 100% | `sha256:ccc7129750517ef7669c4b35dab2ef7a00910780849c64f3720f96a6930dcde9` |
| ML | `benefit-ml-00001-wvn` | 100% | `sha256:db3d6c57a376f3ea0f95b52144f1bee450566e4fd939a52e2f8051317498e45d` |
| PL2 API after | `benefit-api-pl2a-0ba0aa4` | 0% tag | `sha256:f0e88ec2bb403867f156d762893e0f0804f378b4e75d49aba6e029c387474472` |
| PL2 ML after | `benefit-ml-pl2a-0ba0aa4` | 0% tag | `sha256:1070274d936397be06e925a1eea52687f7df2597d499a7d2dc0c7f79e6954b14` |

`latestReadyRevisionName`은 API·ML 모두 PL2 after였지만 공개 traffic은 이전 revision에
100% 유지됐다. latest ready와 공개 revision은 같은 의미가 아니다. PL2 before/after/final
tag와 0% revision은 보존돼 있었다.

### 안전 설정 비교

| 항목 | 공개 API | PL2 API after | 공개 ML | PL2 ML after |
|---|---:|---:|---:|---:|
| CPU | 1 | 1 | 2 | 2 |
| memory | 1GiB | 1GiB | 2GiB | 2GiB |
| concurrency | 80 | 80 | 160 | 160 |
| timeout | 300s | 300s | 300s | 300s |
| min instances | 0 기본값 | 0 | 0 기본값 | 0 |
| max instances | 20 | 20 | 명시값 없음 | 10 |
| port | 8080 | 8080 | 8080 | 8080 |
| startup CPU boost | true | true | true | true |
| startup probe | TCP | TCP | TCP | HTTP `/ready`, 2s × 120 |
| ML runtime flag | 해당 없음 | 해당 없음 | `RERANK=0` | `RERANK=0`, `MODEL_LOCAL_ONLY=1` |

API 후보는 각각 같은 조건의 ML tag를 `ML_BASE_URL`로 사용한다. 전체 환경 변수는 조회하지
않았다. 공개 ML과 PL2 ML 모두 리랭커가 비활성화돼 있으므로 README의 평가 파이프라인과
공개 실행 경로를 분리해 해석해야 한다.

PL2 image는 `0ba0aa425db71430549b1ff4ac15419812a9d015`에서 빌드됐다. 이 commit과 최종
`af8ed66`의 `api/` tree ID는 `dbbed6d6f7a163cf7508bd1cc6ed4e3abc55879d`,
`ml-service/` tree ID는 `605cb3a1dc5004482bb35aed07172138335a91f9`로 각각 동일하다.
후속 차이는 배포 스크립트 플래그, 문서와 측정 원본이다. 기존 digest를 공개 후보로 쓸지,
merge된 commit에서 다시 빌드할지는 traffic 전환 전에 별도로 결정한다.

## 공개 smoke test

개인정보가 없는 고정 합성 입력을 메모리에서만 사용해 확인했다.

| endpoint | 결과 |
|---|---|
| Pages `/benefit-compass/` | HTTP 200 |
| `/actuator/health` | HTTP 200, `UP` |
| `/api/policies/recommend` | HTTP 200, 정책 5건, request ID 있음 |
| `/api/ask` | HTTP 200, 정책 source 5건, 답변 있음, request ID 있음 |

공개 API 응답에는 PL2의 `Server-Timing`이 없었다. 단발 smoke의 지연시간은 API·ML instance
온도를 통제하지 않았으므로 성능 기준선이나 개선 성과로 사용하지 않는다.

## 공식 데이터 소스 사전 확인

- [행정안전부 gov24 공공서비스 API](https://www.data.go.kr/data/15113968/openapi.do)는
  공식 포털에서 v3 JSON·XML 목록/상세/지원조건, 무료, 개발·운영 자동승인,
  개발계정 10,000회, 실시간 갱신으로 안내된다.
- [한국사회보장정보원 중앙부처복지서비스 API](https://www.data.go.kr/data/15090532/openapi.do)는
  XML 목록·상세, 무료, 개발·운영 자동승인, 개발계정 100회, 실시간 갱신으로 안내된다.
- 온통청년 API는 공식 포털에서 고정 숫자 대신 기관 정책에 따라 traffic이 다를 수 있다고
  안내한다.
- 로컬 `.env`와 `ingest/samples/`가 없어 인증된 실제 응답과 필드 스키마는 확인하지 않았다.

키를 채팅이나 문서에 기록하지 않는다. 사용자가 로컬 `.env`에 키를 둔 뒤 승인한 소량 probe로
목록·상세·자격조건 연결 키, 지역·연령·소득 필드, 종료 상태와 원문 URL을 확인하기 전에는
전국민 파서를 구현하지 않는다.

## 로컬 병합 후보 검증

- API: 동일 소스를 `C:\tmp`의 ASCII 경로에 복사해 `gradlew clean test --no-daemon` 실행,
  12 tests / 0 failures / 0 errors / 0 skipped
- ML: lightweight test dependency 경로에서 `python -m unittest -v` 실행, 9 tests / OK
- web: Vite production build 성공, 31 modules transformed
- Python: `python -m compileall -q ingest ml-service eval` 성공
- 배포 스크립트: PowerShell parser 성공, API·ML dry-run의 `--no-traffic`, `--min=0`,
  max instances, ML `/ready` startup probe와 local-only flag 확인
- 변경 파일: `git diff --check`와 비밀값 패턴 검사 통과

현재 Windows 정본 경로에서 API `clean test`를 직접 실행하면 `compileJava`가 main class를
생성한 뒤에도 `compileTestJava` classpath의 `취준자료`가 `�����ڷ�`로 깨져 main class를 찾지
못한다. 동일 소스의 ASCII 경로 clean build는 통과하므로 코드 실패와 구분한다. GitHub의
Linux runner에서 PR CI를 통과해야 최종 검증으로 인정한다.

## Phase 1 전환 조건

1. PL2 branch push와 PR CI 성공
2. 별도 독립 리뷰에서 P0~P2 없음
3. merge 대상 commit과 image digest 관계 명시
4. 기존 공개 revision과 후보 설정 비교
5. 0% tag에서 health·ready·recommend·ask·request ID·timing 재확인
6. 사용자 승인 뒤에만 traffic 변경
7. 실패 시 API `benefit-api-00002-ndd`, ML `benefit-ml-00001-wvn`으로 rollback

Pages는 UI 변경을 공개하기로 결정한 경우에만 별도 배포한다.
