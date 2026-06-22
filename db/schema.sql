-- 혜택나침반 통합 스키마 (Postgres + pgvector)
-- 세 소스(youth/gov24/welfare)가 모두 이 구조로 들어온다.

CREATE EXTENSION IF NOT EXISTS vector;

-- 정책 본체 (구조화 자격필드 = 추천 필터용 / 본문 = RAG용)
CREATE TABLE IF NOT EXISTS policy (
    id              BIGSERIAL PRIMARY KEY,
    source          TEXT NOT NULL,              -- 'youth' | 'gov24' | 'welfare'
    source_id       TEXT NOT NULL,              -- 원천 PK (plcyNo / 서비스ID)
    title           TEXT NOT NULL,              -- 정책명
    summary         TEXT,                       -- 한줄 설명
    support_content TEXT,                       -- 지원내용 (RAG 핵심 본문)
    keywords        TEXT,                       -- 키워드
    category_large  TEXT,                       -- 대분류
    category_mid    TEXT,                       -- 중분류
    org             TEXT,                       -- 주관기관
    apply_method    TEXT,                       -- 신청방법
    screening_method TEXT,                      -- 심사방법
    apply_url       TEXT,                       -- 신청 링크
    submit_docs     TEXT,                       -- 제출서류
    etc_note        TEXT,                       -- 기타사항
    biz_start       DATE,                       -- 사업 시작
    biz_end         DATE,                       -- 사업 종료
    apply_period    TEXT,                       -- 신청기간(원문)
    -- 구조화 자격조건 (자격필터)
    age_min         INT,
    age_max         INT,
    age_limit_yn    BOOLEAN,
    income_min      BIGINT,
    income_max      BIGINT,
    income_cond     TEXT,                       -- 소득조건 구분코드
    income_etc      TEXT,                       -- 소득조건 설명문
    marriage_status TEXT,                       -- 결혼상태 코드
    region_codes    TEXT[],                     -- 법정동코드 배열 (지역)
    add_qualify     TEXT,                       -- 추가 자격조건
    raw             JSONB,                      -- 원본 레코드 전체
    created_at      TIMESTAMPTZ DEFAULT now(),
    updated_at      TIMESTAMPTZ DEFAULT now(),
    UNIQUE (source, source_id)
);

CREATE INDEX IF NOT EXISTS idx_policy_age     ON policy (age_min, age_max);
CREATE INDEX IF NOT EXISTS idx_policy_income  ON policy (income_min, income_max);
CREATE INDEX IF NOT EXISTS idx_policy_region  ON policy USING GIN (region_codes);

-- RAG 청크 + 임베딩 (Gemini text-embedding-004 = 768차원)
CREATE TABLE IF NOT EXISTS policy_chunk (
    id          BIGSERIAL PRIMARY KEY,
    policy_id   BIGINT NOT NULL REFERENCES policy(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    content     TEXT NOT NULL,
    embedding   VECTOR(768),
    UNIQUE (policy_id, chunk_index)
);

CREATE INDEX IF NOT EXISTS idx_chunk_embedding
    ON policy_chunk USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
