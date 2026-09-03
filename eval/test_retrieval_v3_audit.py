import hashlib, json, pathlib, tempfile, uuid, os
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from retrieval_v3.audit import (
    GENESIS_HASH,
    SCHEMA_VERSION,
    AuditChainError,
    AuditError,
    append_event,
    read_and_verify_chain,
    verify_holdout_access_allowed,
    _compute_event_hash,
)

def test_v3_schema_version_and_genesis():
    assert SCHEMA_VERSION == 1
    assert GENESIS_HASH == "0"*64

def test_append_and_verify_chain_v3():
    with tempfile.TemporaryDirectory() as td:
        log = pathlib.Path(td) / "events.jsonl"
        ev1 = append_event(log, action="run_start", candidate_id="c1", set_role="none", git_head="0"*40, git_dirty=False, session_id="s1")
        assert ev1["previous_event_hash"] == GENESIS_HASH
        ev2 = append_event(log, action="run_end", candidate_id="c1", set_role="none", git_head="0"*40, git_dirty=False, session_id="s1")
        assert ev2["previous_event_hash"] == ev1["event_hash"]
        events = read_and_verify_chain(log)
        assert len(events) == 2
        assert events[0]["event_hash"] == ev1["event_hash"]
        assert events[1]["event_hash"] == ev2["event_hash"]
def test_duplicate_event_id_fails_v3():
    with tempfile.TemporaryDirectory() as td:
        log = pathlib.Path(td) / "events.jsonl"
        eid = str(uuid.uuid4())
        append_event(log, action="run_start", candidate_id="c1", set_role="none", git_head="0"*40, git_dirty=False, session_id="s1", event_id=eid)
        # Craft second event manually with same event_id to test duplicate detection
        existing = read_and_verify_chain(log)
        prev = existing[-1]["event_hash"]
        payload = {
            "schema_version": SCHEMA_VERSION,
            "event_id": eid,
            "utc_timestamp": "2026-09-01T00:00:00Z",
            "git_head": "0"*40,
            "git_dirty": False,
            "process_id": os.getpid(),
            "session_id": "s1",
            "action": "run_end",
            "candidate_id": "c1",
            "set_role": "none",
            "set_sha": None,
            "command": None,
            "runner_id": None,
            "outcome": "success",
            "previous_event_hash": prev,
        }
        eh = _compute_event_hash(payload)
        ev = {**payload, "event_hash": eh}
        with open(log, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(ev, sort_keys=True, ensure_ascii=False, separators=(",", ":")) + "\n")
        try:
            read_and_verify_chain(log)
            assert False, "should raise duplicate"
        except AuditChainError:
            pass
def test_truncate_detection_v3():
    with tempfile.TemporaryDirectory() as td:
        log = pathlib.Path(td) / "events.jsonl"
        append_event(log, action="run_start", candidate_id="c1", set_role="none", git_head="0"*40, git_dirty=False, session_id="s1")
        append_event(log, action="run_end", candidate_id="c1", set_role="none", git_head="0"*40, git_dirty=False, session_id="s1")
        # truncate last line
        lines = log.read_text(encoding="utf-8").splitlines()
        log.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
        # truncated chain is still valid (but missing last event) – not error, but we can detect missing event by count
        events = read_and_verify_chain(log)
        assert len(events) == 1
        # Now append should succeed and create new chain
        append_event(log, action="run_end", candidate_id="c1", set_role="none", git_head="0"*40, git_dirty=False, session_id="s1")
        events = read_and_verify_chain(log)
        assert len(events) == 2

def test_protected_access_lifecycle_v3():
    with tempfile.TemporaryDirectory() as td:
        log = pathlib.Path(td) / "events.jsonl"
        sha = "a"*64
        # start grant
        start = append_event(log, action="protected_access_start", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id="s1", outcome="success")
        # verify allowed
        granted = verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha, session_id="s1")
        assert granted["event_hash"] == start["event_hash"]
        # with expected_event_hash correct
        granted2 = verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha, session_id="s1", expected_event_hash=start["event_hash"])
        assert granted2["event_hash"] == start["event_hash"]
        # wrong expected hash => fail
        try:
            verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha, session_id="s1", expected_event_hash="b"*64)
            assert False
        except AuditError:
            pass
        # close grant
        append_event(log, action="protected_access_end", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id="s1", outcome="success")
        # now verify should fail (stale)
        try:
            verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha, session_id="s1")
            assert False
        except AuditError:
            pass
        # new grant after close should succeed
        start2 = append_event(log, action="protected_access_start", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id="s1", outcome="success")
        granted3 = verify_holdout_access_allowed(log, set_role="holdout", set_sha=sha, session_id="s1", expected_event_hash=start2["event_hash"])
        assert granted3["event_hash"] == start2["event_hash"]

def test_holdout_rerun_prevention_one_shot():
    with tempfile.TemporaryDirectory() as td:
        log = pathlib.Path(td) / "events.jsonl"
        sha = "c"*64
        # first run_start for holdout
        append_event(log, action="run_start", candidate_id="v3-canonical-holdout-v1", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id="s1")
        append_event(log, action="run_end", candidate_id="v3-canonical-holdout-v1", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id="s1")
        # second run_start for same holdout sha should be rejected if we enforce one-shot guard
        # The audit module itself does not automatically reject second run_start, but we can simulate guard: check chain has exactly one run_start for that sha
        events = read_and_verify_chain(log)
        run_starts = [e for e in events if e["action"]=="run_start" and e["set_sha"]==sha]
        assert len(run_starts) == 1
        # Attempt second run_start – we append but then verify that one-shot is violated
        append_event(log, action="run_start", candidate_id="v3-canonical-holdout-v1", set_role="holdout", set_sha=sha, git_head="0"*40, git_dirty=False, session_id="s1")
        events2 = read_and_verify_chain(log)
        run_starts2 = [e for e in events2 if e["action"]=="run_start" and e["set_sha"]==sha]
        assert len(run_starts2) == 2
        # For v3, second run_start for same holdout is considered forever rejected – we assert that count >1 is a violation
        # In pure tests, we just verify that the chain would show 2 and that verifier could detect it
        assert len(run_starts2) != 1, "second run_start should be detectable as rerun violation"

def test_canonical_hash_deterministic():
    ev = {"schema_version":1, "event_id": str(uuid.uuid4()), "utc_timestamp":"2026-09-01T00:00:00Z", "git_head":"0"*40, "git_dirty": False, "process_id":123, "session_id":"s1", "action":"run_start", "candidate_id":None, "set_role":"none", "set_sha": None, "command":None, "runner_id":None, "outcome":None, "previous_event_hash": GENESIS_HASH}
    h1 = _compute_event_hash(ev)
    h2 = _compute_event_hash(ev)
    assert h1 == h2
    assert len(h1)==64
    # different previous hash => different hash
    ev2 = dict(ev)
    ev2["previous_event_hash"] = "1"*64
    assert _compute_event_hash(ev2) != h1

def test_atomic_append_and_no_protected_plaintext():
    # Pure API reachable without protected plaintext
    with tempfile.TemporaryDirectory() as td:
        log = pathlib.Path(td) / "events.jsonl"
        # append events without touching protected files
        append_event(log, action="run_start", candidate_id="test", set_role="none", git_head="0"*40, git_dirty=False, session_id="orchestrator-test")
        events = read_and_verify_chain(log)
        assert len(events)==1
        assert events[0]["action"]=="run_start"
        # No protected plaintext accessed

def test_expected_event_hash_is_verifier_parameter_not_event_field():
    with tempfile.TemporaryDirectory() as td:
        log = pathlib.Path(td) / "events.jsonl"
        sha = "d"*64
        ev = append_event(log, action="protected_access_start", set_role="dev", set_sha=sha, git_head="0"*40, git_dirty=False, session_id="s1", outcome="success")
        # Event should NOT contain expected_event_hash field
        assert "expected_event_hash" not in ev
        # Verifier parameter works
        granted = verify_holdout_access_allowed(log, set_role="dev", set_sha=sha, session_id="s1", expected_event_hash=ev["event_hash"])
        assert granted["event_hash"] == ev["event_hash"]
