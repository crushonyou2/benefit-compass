"""Canonical write guard — Retrieval v2 must never default-write into eval/canonical_*.json.

- output path containing "canonical" or "canonical_" is rejected
- default output is eval/retrieval-v2/...
- existing canonical files' hash/content must remain unchanged (checked by tests, not here)
"""
from __future__ import annotations

import os
import pathlib


def is_canonical_path(path: str | pathlib.Path) -> bool:
    p = pathlib.Path(path).as_posix()
    name = pathlib.Path(path).name
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
    raw = str(output)
    posix = pathlib.PurePosixPath(raw.replace("\\", "/")).as_posix()
    if pathlib.PurePosixPath(posix).is_absolute():
        raise ValueError(f"Retrieval v2 output must be relative under eval/retrieval-v2/, got absolute {output!r}")
    import posixpath
    norm = posixpath.normpath(posix)
    if not norm.startswith("eval/retrieval-v2/"):
        raise ValueError(f"Retrieval v2 output must be under eval/retrieval-v2/ (no traversal), got {output!r} -> {norm!r}")
    if ".." in pathlib.PurePosixPath(norm).parts:
        raise ValueError(f"Retrieval v2 output must not contain .. traversal, got {output!r}")
    if not posix.startswith("eval/retrieval-v2/"):
        raise ValueError(f"Retrieval v2 output must be under eval/retrieval-v2/, got {output!r}")
    return pathlib.Path(output)
