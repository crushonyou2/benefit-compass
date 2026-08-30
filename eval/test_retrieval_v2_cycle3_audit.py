import hashlib
import json
import os
import pathlib
import tempfile
import unittest
import uuid

import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from retrieval_v2.cycle3_audit import (
    GENESIS_HASH,
    SCHEMA_VERSION,
    AuditChainError,
    AuditError,
    append_event,
    read_and_verify_chain,
    verify_holdout_access_allowed,
    _compute_event_hash,
)

class Cycle3AuditTest(unittest.TestCase):
    def test_schema_version_constant(self):
        self.assertEqual(1, SCHEMA_VERSION)

    def test_append_and_verify_chain(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            e1 = append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="dev", set_sha="abc", command="pytest", runner_id="r1", outcome="started", git_head="0"*40, git_dirty=False, session_id="s1")
            e2 = append_event(log, action="run_end", candidate_id="c3e1-vector-pool-128", set_role="dev", set_sha="abc", runner_id="r1", outcome="success", git_head="0"*40, git_dirty=False, session_id="s1")
            events = read_and_verify_chain(log)
            self.assertEqual(2, len(events))
            self.assertEqual(e1["event_hash"], events[0]["event_hash"])
            self.assertEqual(e2["event_hash"], events[1]["event_hash"])
            self.assertEqual(GENESIS_HASH, events[0]["previous_event_hash"])
            self.assertEqual(events[0]["event_hash"], events[1]["previous_event_hash"])
            # hash recomputation matches stored
            without = {k: v for k, v in events[0].items() if k != "event_hash"}
            self.assertEqual(_compute_event_hash(without), events[0]["event_hash"])
            # outcome preserved
            self.assertEqual("started", events[0]["outcome"])
            self.assertEqual("success", events[1]["outcome"])

    def test_chain_violation_on_tamper(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="dev", git_head="0"*40, git_dirty=False, session_id="s1")
            append_event(log, action="run_end", candidate_id="c3e1-vector-pool-128", set_role="dev", git_head="0"*40, git_dirty=False, session_id="s1")
            # Tamper: edit outcome field without updating hash
            text = log.read_text(encoding="utf-8").splitlines()
            obj = json.loads(text[1])
            obj["outcome"] = "tampered"
            # keep old hash (so mismatch)
            text[1] = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
            log.write_text("\n".join(text) + "\n", encoding="utf-8")
            with self.assertRaises(AuditChainError):
                read_and_verify_chain(log)
            # also append after tamper must fail
            with self.assertRaises(AuditChainError):
                append_event(log, action="run_start", candidate_id="c3e2-vector-pool-256", set_role="dev", git_head="0"*40, git_dirty=False, session_id="s1")

    def test_truncate_detection(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            e1 = append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="dev", git_head="0"*40, git_dirty=False, session_id="s1")
            e2 = append_event(log, action="run_end", candidate_id="c3e1-vector-pool-128", set_role="dev", git_head="0"*40, git_dirty=False, session_id="s1")
            e3 = append_event(log, action="run_start", candidate_id="c3e2-vector-pool-256", set_role="dev", git_head="0"*40, git_dirty=False, session_id="s1")
            self.assertEqual(3, len(read_and_verify_chain(log)))
            # Truncate: remove last line, then try to append a new event that should reference e2 but writer will see truncated chain
            # First, simulate truncate by overwriting file with first 2 lines only
            lines = log.read_text(encoding="utf-8").splitlines()
            log.write_text("\n".join(lines[:2]) + "\n", encoding="utf-8")
            # Now file is valid chain of length 2, but original e3 is lost — this is a truncated valid chain.
            # Next append will succeed locally but history is lost; we at least verify that truncated chain is still internally valid
            events_truncated = read_and_verify_chain(log)
            self.assertEqual(2, len(events_truncated))
            # To detect truncation as failure, caller must compare against expected external anchor;
            # here we test that tampered previous hash fails: manually craft a bad truncate+append
            # Overwrite last event's previous hash to wrong value and expect failure
            tampered = json.loads(lines[1])
            tampered["previous_event_hash"] = "f" * 64
            # recompute hash incorrectly still stored old
            lines2 = [lines[0], json.dumps(tampered, sort_keys=True, ensure_ascii=False, separators=(",", ":"))]
            log.write_text("\n".join(lines2) + "\n", encoding="utf-8")
            with self.assertRaises(AuditChainError):
                read_and_verify_chain(log)

    def test_overwrite_non_json_fails(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="dev", git_head="0"*40, git_dirty=False, session_id="s1")
            log.write_text("not json\n", encoding="utf-8")
            with self.assertRaises(AuditChainError):
                read_and_verify_chain(log)

    def test_duplicate_event_id_fails(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            eid = str(uuid.uuid4())
            append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="dev", git_head="0"*40, git_dirty=False, session_id="s1", event_id=eid)
            # Second event with same id but different hash chain — should be detected as duplicate after verify
            # Craft second event manually with same event_id
            existing = read_and_verify_chain(log)
            prev = existing[-1]["event_hash"]
            payload = {
                "schema_version": SCHEMA_VERSION,
                "event_id": eid,  # duplicate
                "utc_timestamp": "2026-08-30T00:00:00Z",
                "git_head": "0"*40,
                "git_dirty": False,
                "process_id": os.getpid(),
                "session_id": "s1",
                "action": "run_end",
                "candidate_id": "c3e1-vector-pool-128",
                "set_role": "dev",
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
            with self.assertRaises(AuditChainError):
                read_and_verify_chain(log)

    def test_holdout_access_gate_requires_event(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            # No event yet → gate must deny
            with self.assertRaises(AuditError):
                verify_holdout_access_allowed(log, set_role="holdout")
            # Dev event alone does not unlock holdout
            append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="dev", git_head="0"*40, git_dirty=False, session_id="s1")
            append_event(log, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="dev", set_sha="devsha", git_head="0"*40, git_dirty=False, session_id="s1", outcome="success")
            with self.assertRaises(AuditError):
                verify_holdout_access_allowed(log, set_role="holdout")
            # Holdout protected_access_start unlocks
            append_event(log, action="protected_access_start", candidate_id="c3e2-vector-pool-256", set_role="holdout", set_sha="holdoutsha", git_head="0"*40, git_dirty=False, session_id="s1", outcome="success")
            # Should not raise
            verify_holdout_access_allowed(log, set_role="holdout")
            # Also works with outcome None (treated as success)
            with tempfile.TemporaryDirectory() as td2:
                log2 = pathlib.Path(td2) / "events.jsonl"
                append_event(log2, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="holdout", git_head="0"*40, git_dirty=False, session_id="s1", outcome=None)
                verify_holdout_access_allowed(log2, set_role="holdout")

    def test_holdout_gate_fails_on_tampered_chain(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            append_event(log, action="protected_access_start", candidate_id="c3e1-vector-pool-128", set_role="holdout", git_head="0"*40, git_dirty=False, session_id="s1", outcome="success")
            # Tamper the event
            text = log.read_text(encoding="utf-8").splitlines()
            obj = json.loads(text[0])
            obj["set_role"] = "dev"
            text[0] = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
            log.write_text("\n".join(text) + "\n", encoding="utf-8")
            with self.assertRaises(AuditChainError):
                verify_holdout_access_allowed(log, set_role="holdout")

    def test_action_and_role_validation(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            with self.assertRaises(Exception):
                append_event(log, action="invalid_action", candidate_id="x", set_role="dev", git_head="0"*40, git_dirty=False, session_id="s1")
            with self.assertRaises(Exception):
                append_event(log, action="run_start", candidate_id="x", set_role="invalid_role", git_head="0"*40, git_dirty=False, session_id="s1")

    def test_git_fields_captured(self):
        with tempfile.TemporaryDirectory() as td:
            log = pathlib.Path(td) / "events.jsonl"
            ev = append_event(log, action="run_start", candidate_id="c3e1-vector-pool-128", set_role="none", session_id="test-session")
            self.assertIn("git_head", ev)
            self.assertIn("git_dirty", ev)
            self.assertIn("utc_timestamp", ev)
            self.assertIn("process_id", ev)
            self.assertIn("session_id", ev)
            self.assertEqual(64, len(ev["event_hash"]))
            self.assertEqual(64, len(ev["previous_event_hash"]))
