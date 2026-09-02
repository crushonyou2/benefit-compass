"""Path confinement — traversal, symlink, worktree escape."""
from __future__ import annotations
import pathlib
import os
import tempfile

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
ALLOWED_PREFIXES = [
    REPO_ROOT / "eval" / "retrieval-v3" / "results",
    REPO_ROOT / "eval" / "retrieval_v3" / "results",
    REPO_ROOT / "eval" / "retrieval-v3" / "candidate-plan",
    REPO_ROOT / "eval" / "retrieval_v3" / "candidate-plan",
]

CANONICAL_DEV_OUTPUT_REL = pathlib.Path("eval/retrieval-v3/results/v3-candidate-dev-result.json")
CANONICAL_DEV_OUTPUT_ALT = pathlib.Path("eval/retrieval_v3/results/v3-candidate-dev-result.json")

def _is_subpath(child: pathlib.Path, parent: pathlib.Path) -> bool:
    try:
        child.relative_to(parent)
        return True
    except ValueError:
        return False

def _is_temp_path(p: pathlib.Path) -> bool:
    try:
        temp_root = pathlib.Path(tempfile.gettempdir()).resolve()
        real_p = pathlib.Path(os.path.realpath(str(p)))
        if not real_p.exists():
            cur = real_p
            while not cur.exists() and cur != cur.parent:
                cur = cur.parent
            if cur.exists():
                try:
                    rel = real_p.relative_to(cur)
                    real_p = pathlib.Path(os.path.realpath(str(cur))) / rel
                except ValueError:
                    real_p = pathlib.Path(os.path.realpath(str(cur)))
        return str(real_p).startswith(str(temp_root))
    except Exception:
        return False

def validate_output_path(path: str | pathlib.Path, strict_canonical: bool = False) -> pathlib.Path:
    p = pathlib.Path(path)
    if str(p).strip() == "":
        raise ValueError("output path empty (fail-closed)")
    # Web-HOLD hardening: explicit ".." traversal fail-closed before resolve — OS-agnostic (both "/" and "\" as separators)
    # Normalize separators to "/" for host-agnostic check: Windows "\" and POSIX "/" both split; preserves pure/static/mock hardening, no DB/model/HTTP
    normalized_posix = str(p).replace("\\", "/")
    if ".." in normalized_posix.split("/"):
        raise ValueError(f"path contains .. traversal: {path!r}")
    # Web-HOLD: .git guard OS-agnostic before resolve — fail-closed for any .git segment unless under results
    if ".git" in normalized_posix.split("/"):
        if "results" not in pathlib.PurePath(p).as_posix():
            raise ValueError(f"path must not point into .git: {path!r}")
    # Allow temp directory for pure tests (outside repo but inside system temp) — still check traversal/symlink within temp
    if p.is_absolute() and _is_temp_path(p):
        temp_root = pathlib.Path(tempfile.gettempdir()).resolve()
        # Resolve abs_path for temp
        abs_path = p.resolve() if p.is_absolute() else (REPO_ROOT / p).resolve()
        try:
            real = pathlib.Path(os.path.realpath(str(abs_path)))
            if not real.exists():
                parent_real = pathlib.Path(os.path.realpath(str(abs_path.parent)))
                if not str(parent_real).startswith(str(temp_root)):
                    raise ValueError(f"temp path outside temp root: {path!r}")
            else:
                if not str(real).startswith(str(temp_root)):
                    raise ValueError(f"temp path escape: {path!r}")
        except ValueError:
            raise
        except Exception as e:
            raise ValueError(f"temp path validation failed: {e}") from e
        if ".git" in str(p).replace("\\", "/").split("/"):
            raise ValueError(f"path must not point into .git: {path!r}")
        return abs_path
    # Relative or non-temp absolute
    if not p.is_absolute():
        abs_path = (REPO_ROOT / p).resolve()
    else:
        abs_path = p.resolve()
    # Check traversal: ensure resolved is inside repo root
    try:
        real = pathlib.Path(os.path.realpath(str(abs_path if p.is_absolute() else (REPO_ROOT / p))))
        target_for_check = real if real.exists() else real.parent
        if not real.exists():
            parent_real = pathlib.Path(os.path.realpath(str((REPO_ROOT / p).parent if not p.is_absolute() else p.parent)))
            cur = parent_real
            while not cur.exists() and cur != cur.parent:
                cur = cur.parent
            repo_real = pathlib.Path(os.path.realpath(str(REPO_ROOT)))
            intended_str = str(abs_path)
            repo_str = str(repo_real)
            if not intended_str.startswith(repo_str):
                raise ValueError(f"path traversal escape: {path!r} resolves to {intended_str!r} outside repo {repo_str!r}")
            if strict_canonical:
                expected = (REPO_ROOT / CANONICAL_DEV_OUTPUT_REL).resolve()
                expected_alt = (REPO_ROOT / CANONICAL_DEV_OUTPUT_ALT).resolve()
                if abs_path != expected and abs_path != expected_alt:
                    raise ValueError(f"strict canonical path required: got {path!r} expected {CANONICAL_DEV_OUTPUT_REL!r}")
            else:
                # For non-strict, allow any under allowed prefixes or under eval/retrieval
                allowed = False
                for pref in ALLOWED_PREFIXES:
                    pref_str = str(pref.resolve()) if pref.exists() else str((REPO_ROOT / pref.relative_to(REPO_ROOT)).resolve())
                    if str(abs_path).startswith(pref_str):
                        allowed = True
                        break
                    if str(abs_path).startswith(str(pref)):
                        allowed = True
                        break
                if not allowed:
                    repo_real = pathlib.Path(os.path.realpath(str(REPO_ROOT)))
                    if not str(abs_path).startswith(str(repo_real)):
                        raise ValueError(f"path outside repo: {path!r}")
                    if "eval/retrieval" not in pathlib.PurePath(p).as_posix():
                        raise ValueError(f"path not under allowed prefix: {path!r}")
            return abs_path
        else:
            repo_real = pathlib.Path(os.path.realpath(str(REPO_ROOT)))
            if not str(real).startswith(str(repo_real)):
                raise ValueError(f"symlink escape: {path!r} resolves to {real!r} outside repo {repo_real!r}")
            if strict_canonical:
                expected = (REPO_ROOT / CANONICAL_DEV_OUTPUT_REL).resolve()
                expected_alt = (REPO_ROOT / CANONICAL_DEV_OUTPUT_ALT).resolve()
                if real != expected and real != expected_alt:
                    raise ValueError(f"strict canonical path required: got {path!r}")
            return real
    except ValueError:
        raise
    except Exception as e:
        raise ValueError(f"path validation failed for {path!r}: {e}") from e
    if ".git" in str(p).replace("\\", "/").split("/"):
        if "results" not in pathlib.PurePath(p).as_posix():
            raise ValueError(f"path must not point into .git: {path!r}")
    return abs_path
