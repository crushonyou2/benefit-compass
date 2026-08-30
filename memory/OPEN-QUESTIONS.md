# OPEN QUESTIONS — registered, not remembered

Rule: anything unresolved gets a row here the moment it surfaces. A question is closed only by linking the decision (or finding) that resolved it — never by silently disappearing.

| ID | Question | Opened | Status |
|---|---|---|---|
| Q-001 | Retrieval v2 evaluation contract — What primary metric, regression floors, development/final-holdout split, latency budget, and adoption gate should govern Retrieval v2? | 2026-08-30 | closed → D-007 |
| Q-002 | Public cold-start impact — Does real public traffic show that cold starts materially cause user-visible latency, timeout, or abandonment problems? | 2026-08-30 | open |
| Q-003 | Generic ML normalization — When should generic ML routing be normalized after Retrieval v2 and the final ML revision are settled? | 2026-08-30 | open |
| Q-004 | Retrieval v2 evaluation cycle 2 — Whether to start a new evaluation cycle after cycle 1 closed as HOLD (D-008). A cycle 2 would require a separately designed evaluation cycle with a new independent holdout frozen **before** candidate tuning, not reuse of the cycle-1 holdout or its latency benchmark to claim a new PASS; cycle-1 HOLD verdict is immutable. | 2026-08-30 | closed → D-009 |
| Q-005 | Retrieval v2 after Cycle2 closure — Cycle2가 Exp4 REJECTED(30/36 vs 30, D-010 bounded, PROCESS AUDIT 2026-08-30)로 후보 없이 종료된 뒤, 별도 Cycle3 evaluation/candidate-search cycle을 새로 시작할지? (dev 36 SHA `c8b66fef…`는 tuning set으로 유지 가능하나 selection bias 방지를 위해 최종 선정은 fresh holdout에서만 가능 — audit는 `single execution`을 `canonical accepted execution 1회`로 정정, 28/30/30 수치는 유효하나 “충분히 탐색했다”는 완전성 결론은 durable 증거 없이 성립 불가로 판정) | 2026-08-30 | open |

## Readings in force — assumed, not decided

Rule: when work proceeds on a reading the user never confirmed (silence, a subject change, an "ok" that could mean anything), it is registered here with the user's words quoted — never in DECISIONS.md. One-way-door actions wait while a row is open. A row closes into a `D-` entry on confirmation, or is dropped — and what was built on it swept — on contradiction. (Protocol: ballast decision-ledger skill, *Provisional readings*.)

| ID | User's words (verbatim) | Our reading (`assumed`) | Breaks if wrong | Ends when | Relied on in |
|---|---|---|---|---|---|
