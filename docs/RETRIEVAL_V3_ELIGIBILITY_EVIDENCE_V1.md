# Retrieval v3 eligibility/expired authoritative-field evidence V1 (D-049 stage)

Verdict: PARTIAL schema evidence only. NO full-corpus `(source,source_id)->{eligible,expired}`
map is frozen. Ineligible/expired measurement stays HOLD. This report must not be represented as
gate-ready. Read-only methods only; no synthesis, no free-text parsing, no defaults.

## 1. Method (read-only, aggregate only)

- `information_schema.columns` + `SELECT source, COUNT(*), COUNT(biz_end)` on `public.policy`.
- Top-level `raw` JSONB key inventory per source; value distributions (counts only) for Youth
  `plcyAprvSttsCd`/`bizPrdSeCd`/`aplyPrdSeCd`; format-class buckets (regex/length, never content
  parsing) for Youth `aplyYmd`/`bizPrdBgngYmd`/`bizPrdEndYmd` and Gov24 `신청기한`.
- One external lookup, provenance only: the official Youth open-API code table (not the checker,
  not a benchmark). No DB writes; secret never printed; no per-policy plaintext quoted.

## 2. Normalized table: no eligible/expired columns (reconfirmed)

`public.policy` = id, source, source_id, title, summary, support_content, keywords,
category_large, category_mid, org, apply_method, screening_method, apply_url, submit_docs,
etc_note, biz_start, biz_end, apply_period, age_min, age_max, age_limit_yn, income_min,
income_max, income_cond, income_etc, marriage_status, region_codes, add_qualify, raw,
created_at, updated_at. `has_eligible=False`, `has_expired=False`; matches `db/schema.sql`.
Counts: total 13589 = gov24 10958 + youth 2631; `biz_end` NOT NULL 2285 (gov24 611, youth 1674),
NULL 11304. `biz_end` is a runtime date filter, not a frozen per-policy flag.

## 3. Youth raw: structured leads with official semantics (covers 2631/13589 only)

All 2631 Youth rows carry all 60 raw keys. Distributions:

- `plcyAprvSttsCd`: `0044002` × 2631 (constant).
- `bizPrdSeCd`: `0056001` × 1597, `0056002` × 1034.
- `aplyPrdSeCd`: `0057001` × 1311, `0057003` × 888, `0057002` × 432.
- `aplyYmd`: RANGE8 (`YYYYMMDD~YYYYMMDD`) × 1308, other-text × 3, NULL × 1320 —
  NULL exactly on 마감/상시 rows, values exactly on 특정기간 rows (1:1 with `0057001`).
- `bizPrdBgngYmd`/`bizPrdEndYmd`: YMD8 × 1674, empty × 868, NULL × 89.

Official semantics (first-party authority, NOT the unofficial MCP mirror):

- Source: 온통청년 open-API 코드정의서 `API코드정보.xlsx`,
  URL `https://www.youthcenter.go.kr/downloadform/API코드정보.xlsx`
  (via `https://www.youthcenter.go.kr/cmnFooter/openapiIntro/oaiDoc`),
  retrieved 2026-09-03, SHA256 `81cd89ddc7bd49dfa9e53dec4f093bc8372d241505b5e8374cbfaf018245a5ef`
  (21213 bytes). Raw values carry a `00` prefix over the table codes.
- `plcyAprvSttsCd` 정책승인상태코드: 44001 신청 / 44002 승인 / 44003 반려 / 44004 임시저장.
  All current rows are 승인 (approved for publication). This is policy-global publication state,
  NOT user-specific eligibility: it cannot serve prereg `eligible` semantics, and being constant
  it discriminates nothing.
- `aplyPrdSeCd` 신청기간구분코드: 57001 특정기간 / 57002 상시 / 57003 마감.
  마감 (closed) is an authoritative structured closed-application marker; 상시 (always open) marks
  no application window. But 57001 rows need their window parsed (3 of 1311 are non-RANGE text),
  so even Youth-only expiry derivation is not total without content parsing.
- `bizPrdSeCd` 사업기간구분코드: 56001 특정기간 / 56002 기타 — a period TYPE, not an
  active/expired verdict; 868 rows carry empty business dates, so date-based expiry is not total
  either. No official document defines an `expired` mapping for these codes.

## 4. Gov24 raw: no structured equivalent (covers 10958/13589)

Every Gov24 row has exactly three raw keys: `serviceList`, `serviceDetail`, `supportConditions`
(JA-code eligibility-attribute matrix + service IDs/names — attribute codes, not policy-global
active flags). The only deadline-ish fields are free-text `신청기한` (detail + list, 2563 distinct
values each): strict date format × 337, short fixed words (수시/연중/예산 소진 시까지) × 29,
other free text × 10592. No status/period code, no structured end date. Free-text parsing is
forbidden synthesis, so no Gov24 `expired` derivation is legitimate.

## 5. Conclusion (HOLD, exact limitation)

A COMPLETE authoritative full-corpus map cannot be built: Gov24 (81% of corpus) has no native
structured active/eligible/expired field, and Youth structured codes either lack `eligible`
semantics (승인 ≠ eligible), lack totality (dates), or lack an official `expired` mapping.
No snapshot artifact is frozen in this stage. A future map requires either an official Gov24
status source or an explicit authoritative rule making every branch total — neither exists now.
