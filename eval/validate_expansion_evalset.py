"""확장 평가 라벨이 실제 Gov24 코퍼스와 일치하는지 오프라인 검증한다."""
import collections
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
EVAL = ROOT / "eval" / "expansion_evalset.jsonl"
API_EVAL = ROOT / "eval" / "expansion_api_evalset.jsonl"
CORPUS = ROOT / "ingest" / "data" / "gov24_policies.jsonl"

REQUIRED_CASE_TYPES = {
    "general",
    "household_housing",
    "employment_income",
    "welfare_health",
    "nationwide",
    "regional",
    "ineligible",
    "no_answer",
    "cross_source_similar",
}


def read_jsonl(path):
    if not path.exists():
        raise SystemExit(f"파일 없음: {path}")
    return [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]


def expectation_count(item):
    return sum((
        bool(item.get("gold_source") and item.get("gold_source_id")),
        bool(item.get("excluded_source") and item.get("excluded_source_id")),
        item.get("expected_no_results") is True,
    ))


def validate_items(items, corpus, *, positives_only=False):
    queries = [item.get("query") for item in items]
    if any(not query for query in queries):
        raise SystemExit("query가 비어 있는 평가 문항이 있습니다")
    duplicates = [query for query, count in collections.Counter(queries).items() if count > 1]
    if duplicates:
        raise SystemExit(f"중복 query: {duplicates}")

    for line_number, item in enumerate(items, 1):
        if expectation_count(item) != 1:
            raise SystemExit(f"{line_number}행 기대값 형식 오류")
        if positives_only and not item.get("gold_source_id"):
            raise SystemExit(f"{line_number}행 검색 평가는 gold key가 필요합니다")
        for prefix in ("gold", "excluded"):
            source_id = item.get(f"{prefix}_source_id")
            if not source_id:
                continue
            key = (item[f"{prefix}_source"], source_id)
            policy = corpus.get(key)
            if not policy:
                raise SystemExit(f"{line_number}행 코퍼스에 없는 key: {key}")
            expected_title = item.get(f"{prefix}_title")
            if expected_title and policy["title"] != expected_title:
                raise SystemExit(f"{line_number}행 title 불일치: {key}")


def main():
    corpus_items = read_jsonl(CORPUS)
    corpus = {(item["source"], item["source_id"]): item for item in corpus_items}
    retrieval = read_jsonl(EVAL)
    api = read_jsonl(API_EVAL)

    validate_items(retrieval, corpus, positives_only=True)
    validate_items(api, corpus)
    case_counts = collections.Counter(item.get("case_type") for item in api)
    missing_types = REQUIRED_CASE_TYPES - set(case_counts)
    if missing_types:
        raise SystemExit(f"필수 case_type 누락: {sorted(missing_types)}")
    retrieval_queries = {item["query"] for item in retrieval}
    if not retrieval_queries.issubset({item["query"] for item in api}):
        raise SystemExit("검색 평가 문항이 API 평가셋에 모두 포함되지 않았습니다")

    print(f"corpus={len(corpus)}")
    print(f"retrieval_cases={len(retrieval)}")
    print(f"api_cases={len(api)}")
    for case_type, count in sorted(case_counts.items()):
        print(f"case_type[{case_type}]={count}")


if __name__ == "__main__":
    main()
