"""D-067 loader-schema repair tests — pure/static/synthetic only (no protected bytes).

D-066 FIRST protected-dev execution failed fail-closed in
RealProtectedLoader.__call__ with "missing task id": the loader accepted
only task_id/id, but sealed dev v1 keys the task id as case_id with
query_text (durable non-protected record: D-033 section 2 —
case_id v3d-001..v3d-180, query_text, stratum/location_bearing/golds).

Narrow repair under test: the loader accepts case_id as a third task-id
source and aliases it to task_id in-memory (raw bytes/SHA untouched), so
the runner-facing contract holds with no runner/contract/gate change.

No launcher invocation, no protected worktree/evalset access, no DB/model/
embedding/benchmark/latency/HTTP, no holdout, no production change.
"""
import hashlib
import json
import pathlib
import sys

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from retrieval_v3.real_adapters import RealProtectedLoader
from retrieval_v3.runner import validate_canonical_dev_tasks

REPO = pathlib.Path(__file__).resolve().parents[1]


def _write(lines, path):
    path.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_d067_case_id_only_loads_with_task_id_alias(tmp_path):
    mat = tmp_path / "dev.jsonl"
    sha = _write([json.dumps({"case_id": "v3d-001", "query_text": "synthetic query one"},
                             ensure_ascii=False)], mat)
    tasks = RealProtectedLoader(str(mat), allowed_base=str(tmp_path))("dev", sha)
    assert len(tasks) == 1
    assert tasks[0]["task_id"] == "v3d-001"
    assert tasks[0]["case_id"] == "v3d-001"
    assert tasks[0].get("query_text") == "synthetic query one"


def test_d067_task_id_precedence_preserved(tmp_path):
    mat = tmp_path / "dev.jsonl"
    sha = _write([json.dumps({"task_id": "t-keep", "case_id": "v3d-002",
                              "query": "synthetic query two"}, ensure_ascii=False)], mat)
    tasks = RealProtectedLoader(str(mat), allowed_base=str(tmp_path))("dev", sha)
    assert tasks[0]["task_id"] == "t-keep"


def test_d067_id_only_untouched_no_alias_injected(tmp_path):
    mat = tmp_path / "dev.jsonl"
    sha = _write([json.dumps({"id": "legacy-3", "query": "synthetic query three"},
                             ensure_ascii=False)], mat)
    tasks = RealProtectedLoader(str(mat), allowed_base=str(tmp_path))("dev", sha)
    assert tasks[0].get("id") == "legacy-3"
    assert "task_id" not in tasks[0]


def test_d067_missing_all_id_keys_still_fail_closed(tmp_path):
    mat = tmp_path / "dev.jsonl"
    sha = _write([json.dumps({"query_text": "no id anywhere"}, ensure_ascii=False)], mat)
    with pytest.raises(ValueError, match="task id"):
        RealProtectedLoader(str(mat), allowed_base=str(tmp_path))("dev", sha)


def test_d067_empty_case_id_still_fail_closed(tmp_path):
    mat = tmp_path / "dev.jsonl"
    sha = _write([json.dumps({"case_id": "", "query_text": "empty id"}, ensure_ascii=False)],
                 mat)
    with pytest.raises(ValueError, match="task id"):
        RealProtectedLoader(str(mat), allowed_base=str(tmp_path))("dev", sha)


def test_d067_query_gates_unchanged(tmp_path):
    mat = tmp_path / "dev.jsonl"
    sha = _write([json.dumps({"case_id": "v3d-004"}, ensure_ascii=False)], mat)
    with pytest.raises(ValueError, match="query text"):
        RealProtectedLoader(str(mat), allowed_base=str(tmp_path))("dev", sha)
    # query (non-text alias) still accepted alongside query_text
    sha2 = _write([json.dumps({"case_id": "v3d-005", "query": "plain query"},
                              ensure_ascii=False)], mat)
    tasks = RealProtectedLoader(str(mat), allowed_base=str(tmp_path))("dev", sha2)
    assert tasks[0]["task_id"] == "v3d-005"


def test_d067_other_gates_unchanged(tmp_path):
    mat = tmp_path / "dev.jsonl"
    # invalid JSONL
    mat.write_bytes(b"{not json}\n")
    with pytest.raises(ValueError, match="JSONL"):
        RealProtectedLoader(str(mat), allowed_base=str(tmp_path))(
            "dev", hashlib.sha256(mat.read_bytes()).hexdigest())
    # non-object line
    sha = _write(["[1,2]"], mat)
    with pytest.raises(ValueError, match="must be an object"):
        RealProtectedLoader(str(mat), allowed_base=str(tmp_path))("dev", sha)
    # empty file
    mat.write_bytes(b"")
    with pytest.raises(ValueError, match="empty"):
        RealProtectedLoader(str(mat), allowed_base=str(tmp_path))(
            "dev", hashlib.sha256(mat.read_bytes()).hexdigest())
    # SHA mismatch
    mat2 = tmp_path / "dev2.jsonl"
    sha2 = _write([json.dumps({"case_id": "v3d-006", "query_text": "q"},
                              ensure_ascii=False)], mat2)
    with pytest.raises(ValueError, match="mismatch"):
        RealProtectedLoader(str(mat2), allowed_base=str(tmp_path))("dev", "0" * 64)
    assert sha2  # silence unused warning
    # holdout role still forbidden
    with pytest.raises(ValueError, match="dev only"):
        RealProtectedLoader(str(mat2), allowed_base=str(tmp_path))("holdout", sha2)


def test_d067_sealed_shape_180_passes_canonical_validation(tmp_path):
    # Synthetic tasks in the documented sealed shape (D-033 section 2):
    # case_id + query_text + stratum/location_bearing/golds. Proves the
    # D-066 failure mode is repaired end-to-end through the canonical
    # 180/130/54 validator with no protected data.
    strata = ([("exact_navigation", 21)] + [("natural_needs", 25)] +
              [("exploratory_multi_valid", 21)] + [("multi_constraint", 25)] +
              [("short_keywords", 18)] + [("colloquial_typo_spacing_abbrev", 20)] +
              [("ambiguous", 23)] + [("unsupported_no_answer", 27)])
    loc_quota = {"exact_navigation": 6, "natural_needs": 7,
                 "exploratory_multi_valid": 6, "multi_constraint": 8,
                 "short_keywords": 5, "colloquial_typo_spacing_abbrev": 6,
                 "ambiguous": 7, "unsupported_no_answer": 9}
    seen = {}
    rows = []
    n = 0
    for stratum, count in strata:
        for _ in range(count):
            n += 1
            k = seen.get(stratum, 0)
            seen[stratum] = k + 1
            if stratum == "unsupported_no_answer":
                golds = [{"source": "youth", "source_id": "syn-1", "grade": 1}]
            else:
                golds = [{"source": "youth", "source_id": f"syn-{n}", "grade": 3}]
            rows.append({"case_id": f"v3d-{n:03d}",
                         "query_text": f"synthetic {stratum} query {k}",
                         "stratum": stratum,
                         "location_bearing": k < loc_quota[stratum],
                         "golds": golds})
    assert len(rows) == 180
    mat = tmp_path / "dev.jsonl"
    sha = _write([json.dumps(r, ensure_ascii=False) for r in rows], mat)
    loaded = RealProtectedLoader(str(mat), allowed_base=str(tmp_path))("dev", sha)
    assert len(loaded) == 180
    # every loaded task now resolves a runner-facing task id
    assert all(t.get("task_id") or t.get("id") for t in loaded)
    assert [t["task_id"] for t in loaded] == [f"v3d-{i:03d}" for i in range(1, 181)]
    summary = validate_canonical_dev_tasks(loaded)
    assert summary == {"n": 180, "headline_n": 130, "location_n": 54,
                       "strata": dict(strata)}


def test_d067_mirrors_byte_identical_and_static_contract():
    a = (REPO / "eval" / "retrieval-v3" / "real_adapters.py").read_bytes()
    b = (REPO / "eval" / "retrieval_v3" / "real_adapters.py").read_bytes()
    assert a == b, "real_adapters mirrors must stay byte-identical"
    text = a.decode("utf-8")
    assert 'obj.get("case_id")' in text
    assert "_valid_case_id" in text, "case_id non-empty-string gate must be present"
    assert 'isinstance(_case_id, str) and _case_id.strip() != ""' in text
    assert "D-067" in text
    # fail-closed gates intact in both mirrors
    assert "missing task id (fail-closed)" in text
    assert "missing query text (fail-closed)" in text
    assert "SHA mismatch" in text


@pytest.mark.parametrize("bad", [123, 0, True, False, "   ", "\t\n ", ["x"],
                                 {"k": "v"}, None, ""])
def test_d067_hold_invalid_case_id_never_satisfies_id_gate(tmp_path, bad):
    # Web HOLD repro lockdown (SAME-STAGE, synthetic only): when task_id/id
    # are absent, a non-string or blank case_id MUST fail-closed — it must
    # neither satisfy the id gate nor alias into task_id.
    mat = tmp_path / "dev.jsonl"
    sha = _write([json.dumps({"case_id": bad, "query_text": "q"},
                             ensure_ascii=False)], mat)
    with pytest.raises(ValueError, match="task id"):
        RealProtectedLoader(str(mat), allowed_base=str(tmp_path))("dev", sha)


def test_d067_hold_padded_string_case_id_loads_raw_preserved(tmp_path):
    # Non-blank strings pass the gate; the alias preserves raw bytes value
    # (no loader-side normalization of task content).
    mat = tmp_path / "dev.jsonl"
    sha = _write([json.dumps({"case_id": "  v3d-007  ", "query_text": "q"},
                             ensure_ascii=False)], mat)
    tasks = RealProtectedLoader(str(mat), allowed_base=str(tmp_path))("dev", sha)
    assert tasks[0]["task_id"] == "  v3d-007  "


def test_d067_hold_invalid_case_id_ignored_when_task_id_present(tmp_path):
    # Precedence path: a present task_id keeps working; the invalid case_id
    # is ignored, never aliased over it.
    mat = tmp_path / "dev.jsonl"
    sha = _write([json.dumps({"task_id": "t-keep", "case_id": 123,
                              "query": "q"}, ensure_ascii=False)], mat)
    tasks = RealProtectedLoader(str(mat), allowed_base=str(tmp_path))("dev", sha)
    assert tasks[0]["task_id"] == "t-keep"
