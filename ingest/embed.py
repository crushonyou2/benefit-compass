"""
*_policies.jsonl → RAG 텍스트 구성 → 청킹 → 로컬 임베딩 → data/chunks.jsonl

임베딩: intfloat/multilingual-e5-base (768차원, schema.sql 의 VECTOR(768) 와 일치).
  - 온디바이스(무료, API 한도 없음). 한국어 포함 다국어 검색에 강함.
  - e5 계열은 문서에 "passage: ", 질의에 "query: " 접두사를 붙이고 정규화해야 한다.
    → 검색 단계(질의 임베딩)에서도 반드시 "query: " 접두사를 쓸 것.

첫 실행 시 모델(~440MB)을 1회 내려받는다.
사용법: python embed.py
"""
import json
import os
import pathlib

from sentence_transformers import SentenceTransformer

MODEL_NAME = "intfloat/multilingual-e5-base"
DIMS = 768

DATA = pathlib.Path(__file__).resolve().parent / "data"
OUTFILE = DATA / "chunks.jsonl"
TEMPFILE = OUTFILE.with_suffix(OUTFILE.suffix + ".tmp")

CHUNK_SIZE = 800   # 글자 수 기준 (정책 본문 대부분 1~2 청크)
OVERLAP = 100
INFERENCE_BATCH_SIZE = 32
CHECKPOINT_SIZE = 320


def build_doc(p: dict) -> str:
    """정책 한 건 → 검색용 문서 텍스트 (라벨 + 값)."""
    age = (f"{p['age_min']}~{p['age_max']}세"
           if p.get("age_min") is not None else None)
    category = " > ".join(x for x in (p.get("category_large"),
                                      p.get("category_mid")) if x)
    parts = [
        ("정책명", p.get("title")),
        ("요약", p.get("summary")),
        ("지원내용", p.get("support_content")),
        ("지원대상 연령", age),
        ("소득조건", p.get("income_etc")),
        ("추가자격", p.get("add_qualify")),
        ("신청기간", p.get("apply_period")),
        ("신청방법", p.get("apply_method")),
        ("제출서류", p.get("submit_docs")),
        ("심사방법", p.get("screening_method")),
        ("기타", p.get("etc_note")),
        ("분류", category or None),
        ("주관기관", p.get("org")),
    ]
    return "\n".join(f"[{k}] {v}" for k, v in parts if v)


def split(text: str) -> list:
    if len(text) <= CHUNK_SIZE:
        return [text]
    out, i = [], 0
    while i < len(text):
        out.append(text[i:i + CHUNK_SIZE])
        i += CHUNK_SIZE - OVERLAP
    return out


def completed_chunks(chunks: list) -> int:
    """체크포인트가 현재 코퍼스의 앞부분과 일치하는지 검증하고 재개 위치를 반환한다."""
    if not TEMPFILE.exists():
        return 0
    completed = 0
    with TEMPFILE.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            try:
                saved = json.loads(line)
            except json.JSONDecodeError as exc:
                raise SystemExit(
                    f"임베딩 체크포인트 {line_number}행 손상 — {TEMPFILE}을 삭제 후 재실행"
                ) from exc
            if completed >= len(chunks):
                raise SystemExit(f"임베딩 체크포인트가 현재 코퍼스보다 큽니다 — {TEMPFILE} 삭제 필요")
            expected = chunks[completed]
            key = (saved.get("source"), saved.get("source_id"), saved.get("chunk_index"))
            expected_key = (expected["source"], expected["source_id"], expected["chunk_index"])
            if (key != expected_key or saved.get("content") != expected["content"]
                    or len(saved.get("embedding", [])) != DIMS):
                raise SystemExit(f"임베딩 체크포인트가 현재 코퍼스와 다릅니다 — {TEMPFILE} 삭제 필요")
            completed += 1
    return completed


def main() -> None:
    infiles = sorted(DATA.glob("*_policies.jsonl"))
    if not infiles:
        raise SystemExit(f"{DATA}에 정책 파일 없음 — 수집 스크립트를 먼저 실행")

    policies = [
        json.loads(line)
        for infile in infiles
        for line in infile.open(encoding="utf-8")
    ]
    chunks = []
    for p in policies:
        for idx, c in enumerate(split(build_doc(p))):
            chunks.append({"source": p["source"], "source_id": p["source_id"],
                           "chunk_index": idx, "content": c})
    print(f"{len(policies)}개 정책 → {len(chunks)}개 청크")

    print(f"모델 로드: {MODEL_NAME} (첫 실행 시 다운로드)")
    model = SentenceTransformer(MODEL_NAME)

    start = completed_chunks(chunks)
    if start:
        print(f"체크포인트 재개: {start}/{len(chunks)}개 청크 완료")

    mode = "a" if start else "w"
    with TEMPFILE.open(mode, encoding="utf-8") as stream:
        for offset in range(start, len(chunks), CHECKPOINT_SIZE):
            batch = chunks[offset:offset + CHECKPOINT_SIZE]
            inputs = [f"passage: {chunk['content']}" for chunk in batch]
            vectors = model.encode(
                inputs,
                normalize_embeddings=True,
                batch_size=INFERENCE_BATCH_SIZE,
                show_progress_bar=False,
            )
            records = []
            for chunk, vector in zip(batch, vectors):
                record = {**chunk, "embedding": [round(float(x), 6) for x in vector]}
                records.append(json.dumps(record, ensure_ascii=False))
            stream.write("\n".join(records) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
            done = min(offset + len(batch), len(chunks))
            print(f"임베딩 진행: {done}/{len(chunks)}", flush=True)

    TEMPFILE.replace(OUTFILE)
    print(f"\n완료: {len(chunks)}개 청크 → {OUTFILE} (차원 {DIMS})")


if __name__ == "__main__":
    main()
