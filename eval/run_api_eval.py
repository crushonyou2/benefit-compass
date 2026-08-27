"""실행 중인 /api/ask를 평가해 검색·근거 안전성 지표를 JSON으로 저장한다."""
import argparse
import json
import pathlib
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent


def load_items(path):
    if not path.exists():
        raise SystemExit(f"평가셋 없음: {path}")
    items = [json.loads(line) for line in path.open(encoding="utf-8") if line.strip()]
    if not items:
        raise SystemExit(f"평가셋이 비어 있습니다: {path}")
    for line_number, item in enumerate(items, 1):
        if not item.get("query"):
            raise SystemExit(f"평가셋 {line_number}행 query 누락")
        positive = bool(item.get("gold_source") and item.get("gold_source_id"))
        negative = item.get("expected_no_results") is True
        if positive == negative:
            raise SystemExit(
                f"평가셋 {line_number}행은 gold key 또는 expected_no_results=true 중 하나만 필요합니다"
            )
    return items


def ask(url, item, top_k, timeout):
    payload = {"query": item["query"], "age": item.get("age"), "k": top_k}
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"평가 API 요청 실패: {item['query'][:30]}") from exc
    if not isinstance(body.get("sources"), list) or not isinstance(body.get("generated"), bool):
        raise RuntimeError("API 응답에 sources 배열 또는 generated 불리언이 없습니다")
    return body


def _metrics(ranks):
    if not ranks:
        return {"n": 0, "recall@1": None, "recall@5": None, "mrr": None}
    n = len(ranks)
    return {
        "n": n,
        "recall@1": round(sum(rank == 1 for rank in ranks) / n, 4),
        "recall@5": round(sum(1 <= rank <= 5 for rank in ranks) / n, 4),
        "mrr": round(sum(1 / rank if rank else 0 for rank in ranks) / n, 4),
    }


def summarize(records):
    positive = []
    by_source = {}
    by_case_type = {}
    no_answer_total = 0
    no_answer_with_results = 0
    answer_without_sources = 0
    missing_ground_links = 0

    for item, response in records:
        sources = response["sources"]
        missing_ground_links += sum(
            not str(source.get("apply_url") or "").startswith(("http://", "https://"))
            for source in sources
        )
        if not sources and response["generated"]:
            answer_without_sources += 1

        if item.get("expected_no_results") is True:
            no_answer_total += 1
            no_answer_with_results += bool(sources)
            continue

        gold = (item["gold_source"], item["gold_source_id"])
        keys = [(source.get("source"), source.get("source_id")) for source in sources]
        rank = keys.index(gold) + 1 if gold in keys else 0
        positive.append(rank)
        by_source.setdefault(gold[0], []).append(rank)
        by_case_type.setdefault(item.get("case_type", "uncategorized"), []).append(rank)

    return {
        "total_cases": len(records),
        "retrieval": _metrics(positive),
        "by_source": {source: _metrics(ranks) for source, ranks in sorted(by_source.items())},
        "by_case_type": {
            case_type: _metrics(ranks) for case_type, ranks in sorted(by_case_type.items())
        },
        "no_answer": {
            "n": no_answer_total,
            "unexpected_results": no_answer_with_results,
        },
        "missing_ground_links": missing_ground_links,
        "answer_generated_without_sources": answer_without_sources,
    }


def parse_args():
    parser = argparse.ArgumentParser(description="실행 중인 혜택나침반 API 통합 평가")
    parser.add_argument("--eval-file", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, default=HERE / "results_api.json")
    parser.add_argument("--url", default="http://localhost:8080/api/ask")
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--timeout", type=float, default=30)
    return parser.parse_args()


def main():
    args = parse_args()
    if args.k < 5:
        raise SystemExit("Recall@5 측정을 위해 --k는 5 이상이어야 합니다")
    items = load_items(args.eval_file)
    records = [(item, ask(args.url, item, args.k, args.timeout)) for item in items]
    result = {
        "eval_file": str(args.eval_file),
        "url": args.url,
        "top_k": args.k,
        **summarize(records),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    print(f"저장 → {args.output}")


if __name__ == "__main__":
    main()
