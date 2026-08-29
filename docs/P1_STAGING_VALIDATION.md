# P1 Data Refresh / Staging Validation — 2026-08-29

## 목적
검색 계약 변경 없이 최신 코드 기준 데이터 refresh와 staging 수준 안전한 검증.

## 확정 검색 계약 (불변)
`RERANK=0`, `CANDIDATES=30`, `COSINE_MIN=0.78`, `LEXICAL 0.01`, `strip_region`, 만료 제외, `(source, source_id)` gold, `intfloat/multilingual-e5-base`.

## 데이터 상태
- youth 2,631 / gov24 10,958 / total 13,589
- chunks youth 3,083 / gov24 14,526 / total 17,609
- youth missing_links 615 → 599 (16건 bug fix), gov24 0
- missing_embeddings 0, duplicate 0, orphan 0

## Refresh 전략 결정
**16-policy targeted URL correction + staging full-copy validation** 선택.
- 전체 재수집/재임베딩: 불필요 (URL은 chunk/embedding 미포함), youth 원천 변동 위험
- 기존 파일 기반 full reload: `ingest/data`에 youth 파일 없음 (gitignored), gov24만 있어 youth 유실 위험
- Staging DB full reload: local pgvector `benefit-staging:5433`에 production 13589/17609 복제 후 fix 검증 → 안전성 확보, 재현성 유지
- 최종: staging에서 전체 복제 후 16건 fix 검증, production에는 동일 targeted UPDATE만 적용

## 실행
1. `python ingest/fix_youth_urls.py --dry-run` — prod 615, 16 recoverable 확인 (P0 baseline)
2. `python scripts/staging_copy.py` — prod → staging 13589/17609 복제
3. `python ingest/fix_youth_urls.py --dry-run --staging-url postgresql://postgres:postgres@localhost:5433/benefit` — staging 615
4. `python ingest/fix_youth_urls.py --execute --staging-url ...` — staging 615→599, validation dup 0 등
5. `python ingest/fix_youth_urls.py --execute` — production 615→599 total; final batch 614→599 (15 rows, 1 row already corrected via manual check before batch — see `eval/fix_youth_urls_report.json` `initial_missing_before_any_fix`/`before_missing`)
6. `python eval/run_data_quality.py` — youth 599 확인
7. `python eval/run_eval.py --lexical-bias 0.01` smoke — youth 60 recall@1 0.2333 유지 (P0 canonical 불변)

## 검증
- source별 policy/chunk count 유지
- policy↔chunk coverage 정상
- duplicate `(source, source_id)` 0
- missing_embeddings 0
- youth URL 16건 복구, 599 source limitation 유지
- gov24 10958 유지
- region 추론 없음
- retrieval smoke youth 0.2333 / gov24 0.2857 유지
- P0 canonical `eval/canonical_*.json` 불변

## Provenance
- `eval/fix_youth_urls_report.json` — before/after, per-row details
- `eval/data_quality.json` — 599
- `scripts/staging_copy.py` / `ingest/fix_youth_urls.py` — staging 경로

## 남은 조건 (production rollout 전)
- staging Cloud Run no-traffic 검증은 P2에서 수행 (P1은 DB만)
- 최소 인스턴스 등 운영 비용 결정은 P2
- youth `refUrlAddr2` 1건 추가 회수는 보류
