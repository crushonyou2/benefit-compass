"""Canonical write guard — Retrieval v2 must never default-write into eval/canonical_*.json.

- output path containing "canonical" or "canonical_" is rejected
- default output is eval/retrieval-v2/...
- existing canonical files' hash/content must remain unchanged (checked by tests, not here)
"""
from __future__ import annotations

import pathlib


def is_canonical_path(path: str | pathlib.Path) -> bool:
    p = pathlib.Path(path).as_posix()
    name = pathlib.Path(path).name
    # any segment or filename containing canonical_ or canonical.
    if "canonical" in p:
        return True
    if name.startswith("canonical_"):
        return True
    return False


def assert_not_canonical(output: str | pathlib.Path) -> None:
    if is_canonical_path(output):
        raise ValueError(f"refusing to write Retrieval v2 output to canonical path: {output} — use eval/retrieval-v2/...")

def default_output(role: str, suffix: str = ".json") -> pathlib.Path:
    if role not in {"dev", "holdout", "paired", "latency"}:
        raise ValueError(f"unknown role {role!r}")
    return pathlib.Path(f"eval/retrieval-v2/{role}{suffix}")

def ensure_retrieval_v2_path(output: str | pathlib.Path) -> pathlib.Path:
    assert_not_canonical(output)
    p = pathlib.Path(output)
    if not p.as_posix().startswith("eval/retrieval-v2/"):
        raise ValueError(f"Retrieval v2 output must be under eval/retrieval-v2/, got {output}")
    return p
