# Repository development rules

이 저장소를 수정할 때는 먼저 Git 상태와 저장소 문서를 확인한다.

## Git 작업 방식

- 안정 브랜치(`main`, 아직 이전하지 않은 저장소의 `master`)에서 직접 기능을 구현하지 않는다.
- 작업은 `feature/*`, `fix/*`, `chore/*`, `docs/*`, `refactor/*`, `test/*`, `ci/*` 브랜치에서 수행한다.
- 작업 브랜치가 없다면 `..\_project-tooling\scripts\Start-Task.ps1`을 사용한다.
- 비 trivial한 기능 개발, 병렬 작업, 긴급 수정은 `-UseWorktree`로 기존 작업과 분리한다.
- 이미 적절한 작업 브랜치 또는 worktree에 있다면 중복 생성하지 않는다.
- 여러 기능의 장기 통합 시험이 필요한 경우에만 `dev`를 도입한다.
- 기존 사용자 변경 사항을 임의로 덮어쓰거나 폐기하지 않는다.

## 검증과 완료

- README, 패키지 스크립트, CI 설정에서 프로젝트의 lint, typecheck, test, build 명령을 찾는다.
- 변경 범위에 맞는 검증을 실행하고 실패 또는 미실행 항목을 보고한다.
- 사용자의 명시적 승인 없이 안정 브랜치 병합, 원격 push, PR 병합, 버전 태그 push, 실제 배포를 하지 않는다.

공통 상세 원칙: `..\_project-tooling\standards\git-workflow.md`
