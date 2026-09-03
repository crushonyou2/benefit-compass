"""Result schema/publication — deterministic strict, atomic, provenance pin, fail-closed."""
from __future__ import annotations
import hashlib
import json
import os
import pathlib
import re
import uuid

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CANONICAL_DEV_OUTPUT_REL = pathlib.Path("eval/retrieval-v3/results/v3-candidate-dev-result.json")
CANONICAL_DEV_OUTPUT_ALT = pathlib.Path("eval/retrieval_v3/results/v3-candidate-dev-result.json")
SCHEMA_VERSION = 1

HEX40_RE = re.compile(r"^[0-9a-f]{40}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")

def _validate_hex40(s: str, name: str):
    if not isinstance(s, str) or not HEX40_RE.match(s.lower()):
        raise ValueError(f"{name} must be 40-hex, got {s!r}")

def _validate_hex64(s: str, name: str):
    if not isinstance(s, str) or not HEX64_RE.match(s.lower()):
        raise ValueError(f"{name} must be 64-hex, got {s!r}")

def build_result_skeleton(
    per_config_metrics: list[dict],
    selection: dict,
    candidate_b_gate: dict,
    provenance: dict,
    git_head: str,
    git_dirty: bool,
    corpus_provenance: dict | None = None,
    set_provenance: dict | None = None,
    audit_head: str | None = None,
    safety_per_config: dict | None = None,
    latency_per_config: dict | None = None,
) -> dict:
    """Build complete result dict."""
    # provenance must contain candidate_plan_sha, prereg_sha
    candidate_plan_sha = provenance.get("candidate_plan_sha256") or provenance.get("candidate_plan_sha")
    prereg_sha = provenance.get("prereg_sha256") or provenance.get("prereg_sha")
    if not candidate_plan_sha:
        raise ValueError("provenance missing candidate_plan_sha256")
    if not prereg_sha:
        raise ValueError("provenance missing prereg_sha256")
    _validate_hex64(candidate_plan_sha, "candidate_plan_sha256")
    _validate_hex64(prereg_sha, "prereg_sha256")
    _validate_hex40(git_head, "git_head")
    if not isinstance(git_dirty, bool):
        raise ValueError("git_dirty must be bool")
    if len(per_config_metrics) != 18:
        raise ValueError(f"per_config_metrics must be exactly 18, got {len(per_config_metrics)}")
    # Check config IDs
    ids = [m.get("config_id") for m in per_config_metrics]
    expected = [f"candidate-a-{i:02d}" for i in range(1, 19)]
    if ids != expected:
        # Allow sorted? But strict expects lexicographic order as in registry
        if sorted(ids) != expected:
            raise ValueError(f"config_ids mismatch: {ids}")
        # Enforce sorted order for deterministic publication
        per_config_metrics = sorted(per_config_metrics, key=lambda x: x["config_id"])
    # Check each metrics internally consistent
    for m in per_config_metrics:
        if not isinstance(m.get("success_at_5"), (int, float)):
            raise ValueError(f"{m.get('config_id')} success_at_5 invalid")
        if not 0 <= m["success_at_5"] <= 1:
            raise ValueError(f"{m.get('config_id')} success_at_5 out of range")
        if "ndcg_at_5" in m and not 0 <= m["ndcg_at_5"] <= 1:
            raise ValueError(f"{m.get('config_id')} ndcg out of range")
        if "mrr_at_10" in m and not 0 <= m["mrr_at_10"] <= 1:
            raise ValueError("mrr out of range")
        # Ensure ndcg/mrr present
        if "ndcg_at_5" not in m or "mrr_at_10" not in m:
            raise ValueError(f"{m.get('config_id')} missing ndcg/mrr")
        # latency p95 if present must be numeric
        if "p95" in m and m["p95"] is not None and not isinstance(m["p95"], (int, float)):
            raise ValueError("p95 invalid")

    # Candidate B must be absent unless separate future gate
    # Check no config_id contains candidate-b
    for m in per_config_metrics:
        if "candidate-b" in m.get("config_id", "").lower():
            raise ValueError("Candidate B must not be present in per_config_metrics")
    # Also selection must not contain B
    if selection.get("chosen") and "candidate-b" in str(selection.get("chosen")).lower():
        raise ValueError("Candidate B must not be chosen")

    # Ensure candidate_b_gate reflects diagnostic only, not instantiated
    if candidate_b_gate.get("instantiated") not in (False, None):
        # spec says instantiated false
        if candidate_b_gate.get("instantiated") is True:
            raise ValueError("candidate_b_gate.instantiated must be false (B not instantiated)")

    result = {
        "schema_version": SCHEMA_VERSION,
        "batch_id": "v3-candidate-dev-v1",
        "git_head": git_head.lower(),
        "git_dirty": git_dirty,
        "candidate_plan_sha256": candidate_plan_sha.lower(),
        "prereg_sha256": prereg_sha.lower(),
        "provenance": provenance,
        "corpus_provenance": corpus_provenance,
        "set_provenance": set_provenance,
        "audit_head": audit_head,
        "per_config_metrics": per_config_metrics,
        "selection": selection,
        "candidate_b_gate": candidate_b_gate,
        "safety_per_config": safety_per_config,
        "latency_per_config": latency_per_config,
        "per_config_count": len(per_config_metrics),
        "created_at": provenance.get("created_at") or __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    return result

def validate_complete_result(result: dict):
    """Strict validation — fail-closed."""
    if not isinstance(result, dict):
        raise ValueError("result must be dict")
    if result.get("schema_version") != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    # git provenance
    _validate_hex40(result.get("git_head", ""), "git_head")
    if not isinstance(result.get("git_dirty"), bool):
        raise ValueError("git_dirty must be bool")
    _validate_hex64(result.get("candidate_plan_sha256", ""), "candidate_plan_sha256")
    _validate_hex64(result.get("prereg_sha256", ""), "prereg_sha256")
    # per_config_metrics
    pcs = result.get("per_config_metrics")
    if not isinstance(pcs, list) or len(pcs) != 18:
        raise ValueError(f"per_config_metrics must be list len 18, got {type(pcs)} len {len(pcs) if isinstance(pcs,list) else 'n/a'}")
    ids = [p.get("config_id") for p in pcs]
    expected = [f"candidate-a-{i:02d}" for i in range(1, 19)]
    if ids != expected:
        # also allow sorted check but strict requires order
        if sorted(ids) != expected:
            raise ValueError(f"config_ids mismatch: {ids}")
        else:
            raise ValueError(f"config_ids not in lexicographic order: {ids}")
    for p in pcs:
        # internally consistent
        if not 0 <= p.get("success_at_5", -1) <= 1:
            raise ValueError(f"{p.get('config_id')} success_at_5 inconsistent")
        if not 0 <= p.get("ndcg_at_5", -1) <= 1:
            raise ValueError(f"{p.get('config_id')} ndcg inconsistent")
        if not 0 <= p.get("mrr_at_10", -1) <= 1:
            raise ValueError(f"{p.get('config_id')} mrr inconsistent")
        if "candidate-b" in p.get("config_id","").lower():
            raise ValueError("Candidate B absent check failed")
    sel = result.get("selection")
    if not isinstance(sel, dict) or "chosen" not in sel:
        raise ValueError("selection missing")
    if sel.get("chosen") and "candidate-b" in str(sel.get("chosen")).lower():
        raise ValueError("Candidate B must not be chosen")
    b_gate = result.get("candidate_b_gate")
    if b_gate and b_gate.get("instantiated") is True:
        raise ValueError("candidate_b_gate.instantiated must be false")
    # set provenance pin
    set_prov = result.get("set_provenance")
    if set_prov:
        if set_prov.get("set_role") not in ("dev", "holdout", None):
            raise ValueError("set_role invalid")
        if set_prov.get("set_sha"):
            _validate_hex64(set_prov["set_sha"], "set_sha")
            # D-039: canonical result n=180/headline_n=130 when set_sha present (fail-closed).
            # D-040 correction-3: missing field also fails (exact canonical output requires both pins).
            # D-041 correction-4: canonical requires complete 18-key safety+latency evidence and selection consistency.
            # Noncanonical mock (no set_sha) stays lightweight: no evidence requirement.
            expected_ids = [f"candidate-a-{i:02d}" for i in range(1, 19)]
            safety_map = result.get("safety_per_config")
            if not isinstance(safety_map, dict) or sorted(safety_map.keys()) != expected_ids:
                raise ValueError("canonical safety_per_config must carry complete 18 config keys (fail-closed)")
            for cid in expected_ids:
                rep = safety_map.get(cid)
                if not isinstance(rep, dict):
                    raise ValueError(f"canonical safety {cid} must be dict")
                for gate in ("unsupported", "ambiguous", "ineligible_expired", "official_link", "http_resolution", "cost"):
                    if rep.get(gate) not in ("PASS", "NO-GO", "HOLD"):
                        raise ValueError(f"canonical safety {cid}.{gate} must be PASS/NO-GO/HOLD")
            latency_map = result.get("latency_per_config")
            if not isinstance(latency_map, dict) or sorted(latency_map.keys()) != expected_ids:
                raise ValueError("canonical latency_per_config must carry complete 18 config keys (fail-closed)")
            for cid in expected_ids:
                ev = latency_map.get(cid)
                if not isinstance(ev, dict):
                    raise ValueError(f"canonical latency {cid} must be dict")
                if ev.get("gate") not in ("PASS", "NO-GO", "HOLD"):
                    raise ValueError(f"canonical latency {cid}.gate must be PASS/NO-GO/HOLD")
                for side in ("baseline", "candidate"):
                    blk = ev.get(side)
                    if not isinstance(blk, dict):
                        raise ValueError(f"canonical latency {cid}.{side} must be dict")
                    for stat in ("p50", "p95", "p99"):
                        val = blk.get(stat)
                        if not isinstance(val, (int, float)):
                            raise ValueError(f"canonical latency {cid}.{side}.{stat} must be numeric")
                if not isinstance(ev.get("n"), int) or not isinstance(ev.get("warmup_n"), int):
                    raise ValueError(f"canonical latency {cid} must carry int n/warmup_n")
            sel = result.get("selection") or {}
            eligible = sel.get("eligible")
            chosen = sel.get("chosen")
            if not isinstance(eligible, list) or any(e not in expected_ids for e in eligible):
                raise ValueError("canonical selection.eligible must list known config ids only")
            if chosen is not None and chosen not in eligible:
                raise ValueError("canonical selection.chosen must be in eligible (fail-closed consistency)")
            for cid in (eligible + ([chosen] if chosen else [])):
                m = next((p for p in result.get("per_config_metrics", []) if p.get("config_id") == cid), None)
                if m is None or not isinstance(m.get("success_at_5"), (int, float)) or not m.get("success_at_5") >= 0.85:
                    raise ValueError(f"canonical eligible {cid} must carry success_at_5>=0.85")
                for gate in ("unsupported", "ambiguous", "ineligible_expired", "official_link", "http_resolution", "cost"):
                    if safety_map.get(cid, {}).get(gate) != "PASS":
                        raise ValueError(f"canonical eligible {cid} must carry six-gate safety PASS")
                if latency_map.get(cid, {}).get("gate") != "PASS":
                    raise ValueError(f"canonical eligible {cid} must carry latency gate PASS")
            if set_prov.get("n") != 180:
                raise ValueError(f"canonical set_provenance.n must be 180, got {set_prov.get('n')!r}")
            if set_prov.get("headline_n") != 130:
                raise ValueError(f"canonical set_provenance.headline_n must be 130, got {set_prov.get('headline_n')!r}")
    # corpus provenance pin
    corpus = result.get("corpus_provenance")
    if corpus:
        if "total_policies" in corpus and not isinstance(corpus["total_policies"], int):
            raise ValueError("corpus_provenance.total_policies invalid")
    # provenance pins
    prov = result.get("provenance", {})
    if not prov.get("candidate_plan_sha256") or not prov.get("prereg_sha256"):
        raise ValueError("provenance missing pins")

def atomic_write_result(result: dict, output_path: str | pathlib.Path) -> pathlib.Path:
    """Validate and atomically write — fail-closed on existing, concurrent, rerun."""
    from .paths import validate_output_path, CANONICAL_DEV_OUTPUT_REL, CANONICAL_DEV_OUTPUT_ALT, REPO_ROOT
    # Validate complete before any FS
    validate_complete_result(result)
    out = pathlib.Path(output_path)
    # D-040 correction-3: canonical dev result with set_sha must write exact canonical output (fail-closed).
    set_prov = (result.get("set_provenance") or {}) if isinstance(result, dict) else {}
    needs_canonical = bool(set_prov.get("set_sha"))
    if needs_canonical:
        # Strict canonical required; temp/non-canonical rejected even if confined.
        validate_output_path(out, strict_canonical=True)
        out_posix = pathlib.PurePath(out).as_posix()
        canon_posix = pathlib.PurePath(CANONICAL_DEV_OUTPUT_REL).as_posix()
        canon_alt_posix = pathlib.PurePath(CANONICAL_DEV_OUTPUT_ALT).as_posix()
        if out_posix not in (canon_posix, canon_alt_posix):
            # Also accept absolute that resolves to canonical (OS-agnostic).
            canonical_abs = (REPO_ROOT / CANONICAL_DEV_OUTPUT_REL).resolve()
            canonical_alt_abs = (REPO_ROOT / CANONICAL_DEV_OUTPUT_ALT).resolve()
            abs_probe = (REPO_ROOT / out).resolve() if not out.is_absolute() else out.resolve()
            if abs_probe not in (canonical_abs, canonical_alt_abs):
                raise ValueError(f"canonical dev result must write exact canonical output (fail-closed): got {output_path!r}")
        is_canonical = True
    else:
        # Path confinement — strict canonical if output is dev canonical
        # Determine if this is canonical dev path
        is_canonical = False
        try:
            # try strict
            validate_output_path(out, strict_canonical=True)
            is_canonical = True
        except ValueError:
            # not canonical strict, try non-strict confinement (must still be inside allowed)
            validate_output_path(out, strict_canonical=False)
            pass

    # Determine intended canonical absolute for existence guard comparison
    canonical_abs = (REPO_ROOT / CANONICAL_DEV_OUTPUT_REL).resolve()
    canonical_alt_abs = (REPO_ROOT / CANONICAL_DEV_OUTPUT_ALT).resolve()
    abs_out = (REPO_ROOT / out).resolve() if not out.is_absolute() else out.resolve()

    # If output is canonical, enforce exact match — OS-agnostic via as_posix (covers Windows backslash vs POSIX slash)
    out_posix = pathlib.PurePath(out).as_posix()
    canon_posix = pathlib.PurePath(CANONICAL_DEV_OUTPUT_REL).as_posix()
    canon_alt_posix = pathlib.PurePath(CANONICAL_DEV_OUTPUT_ALT).as_posix()
    if out_posix in (canon_posix, canon_alt_posix) or abs_out in (canonical_abs, canonical_alt_abs):
        pass
    else:
        pass

    # Single-batch guard: existing file must fail
    if abs_out.exists():
        raise FileExistsError(f"result already exists at {abs_out} — single batch guard (rerun prevention)")
    # Ensure parent exists
    abs_out.parent.mkdir(parents=True, exist_ok=True)
    # Validate again after mkdir that parent is inside allowed (re-check symlink)
    # Use realpath check — allow temp directory for pure tests
    import os as _os, tempfile
    from .paths import _is_subpath as _rs_is_subpath
    repo_real = pathlib.Path(_os.path.realpath(str(REPO_ROOT)))
    out_real_parent = pathlib.Path(_os.path.realpath(str(abs_out.parent)))
    temp_root = pathlib.Path(tempfile.gettempdir()).resolve()
    temp_real = pathlib.Path(_os.path.realpath(str(temp_root)))
    # D-039: component-aware containment (string startswith allows benefit-compass-escape sibling).
    is_temp_out = _rs_is_subpath(out_real_parent, temp_real) or _rs_is_subpath(abs_out, temp_root)
    if not is_temp_out and not _rs_is_subpath(out_real_parent, repo_real):
        raise ValueError(f"output parent outside repo: {out_real_parent}")
    # Also ensure target file's realpath would be inside repo (if symlink)
    # Since file doesn't exist yet, check logical path string — OS-agnostic via PurePath.as_posix()
    if not is_temp_out and not _rs_is_subpath(abs_out, repo_real) and not _rs_is_subpath(abs_out, canonical_abs.parent):
        # allow any under repo — Windows hardening: use as_posix() for prefix check (covers "\" vs "/" )
        if "eval/retrieval" not in pathlib.PurePath(out).as_posix():
            raise ValueError(f"output path not under allowed eval: {out}")

    tmp = abs_out.with_name(abs_out.name + f".tmp.{uuid.uuid4().hex}")
    payload = json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(payload)
        f.flush()
        try:
            os.fsync(f.fileno())
        except Exception as e:
            raise RuntimeError(f"fsync failed: {e}") from e
    # Validate temp
    try:
        loaded = json.loads(tmp.read_text(encoding="utf-8"))
        validate_complete_result(loaded)
    except Exception:
        try:
            tmp.unlink()
        except Exception:
            pass
        raise
    # Pre-publish concurrent check
    if abs_out.exists():
        try:
            tmp.unlink()
        except Exception:
            pass
        raise FileExistsError(f"result already exists at {abs_out} — concurrent race pre-publish")
    # Atomic publish via hardlink
    try:
        os.link(str(tmp), str(abs_out))
        try:
            tmp.unlink()
        except Exception:
            pass
    except FileExistsError:
        try:
            tmp.unlink()
        except Exception:
            pass
        raise FileExistsError(f"result already exists at {abs_out} — concurrent link race")
    except OSError as e:
        if abs_out.exists():
            try:
                tmp.unlink()
            except Exception:
                pass
            raise FileExistsError(f"result already exists at {abs_out} — concurrent race fallback") from e
        # Fallback exclusive create
        created = False
        try:
            fd = os.open(str(abs_out), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            created = True
            try:
                data = payload.encode("utf-8")
                written = 0
                while written < len(data):
                    n = os.write(fd, data[written:])
                    if n == 0:
                        raise RuntimeError("short write")
                    written += n
                try:
                    os.fsync(fd)
                except Exception as fe:
                    raise RuntimeError(f"fsync fallback failed: {fe}") from fe
            finally:
                try:
                    os.close(fd)
                except Exception:
                    pass
            actual = abs_out.read_text(encoding="utf-8")
            if actual != payload:
                raise RuntimeError("fallback content mismatch")
            loaded_fb = json.loads(actual)
            validate_complete_result(loaded_fb)
            try:
                tmp.unlink()
            except Exception:
                pass
        except FileExistsError:
            try:
                tmp.unlink()
            except Exception:
                pass
            raise
        except Exception as ee:
            if created:
                try:
                    if abs_out.exists():
                        abs_out.unlink()
                except Exception:
                    pass
            try:
                tmp.unlink()
            except Exception:
                pass
            raise RuntimeError(f"atomic publish failed: {ee}") from ee
    return abs_out
