"""D-058 narrow repair — set_session failure exact-once cleanup (would FAIL on 13301ab).

Covers the Web HOLD root cause only: connection creation succeeds but
conn.set_session(readonly/autocommit/REPEATABLE READ) raises. Old code
assigned self._conn only AFTER set_session, so the opened connection
leaked (close count 0 even after session.close). Fixed code owns the
connection immediately, closes it exactly once on config failure, leaves
self._conn=None + fail-closed, and surfaces a secret-free error.

Pure fake/injected only. No DB/model/network IO.
"""
import datetime
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import pytest

from retrieval_v3.real_adapters import RealEvaluationSession

SYN_TZ = "SYNTH-TZ"


class _Cursor:
    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, params=None):
        self._conn.statements.append(sql)
        flat = " ".join(str(sql).split())
        if flat == "SHOW TimeZone":
            self._rows = [(SYN_TZ,)]
        else:
            raise AssertionError(f"unexpected SQL in D-058 mock: {flat[:60]}")

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)

    def close(self):
        pass


class _FailConfigConn:
    """set_session raises with a secret-bearing message; close counts."""

    def __init__(self):
        self.set_session_calls = []
        self.events = []
        self.statements = []
        self.close_calls = 0
        self.closed = False

    def set_session(self, readonly=None, autocommit=None, isolation_level=None):
        self.set_session_calls.append(
            {"readonly": readonly, "autocommit": autocommit, "isolation_level": isolation_level}
        )
        raise ValueError("SECRET-cfg-postgres://user:pass@host/should-not-leak")

    def cursor(self):
        self.events.append("cursor")
        return _Cursor(self)

    def close(self):
        self.close_calls += 1
        self.closed = True


class _FailBothConn(_FailConfigConn):
    """set_session raises AND cleanup close raises; close attempt counted."""

    def close(self):
        self.close_calls += 1
        raise OSError("SECRET-cleanup-postgres://user:pass@host/should-not-leak")


class _OkConn:
    def __init__(self):
        self.set_session_calls = []
        self.events = []
        self.statements = []
        self.close_calls = 0
        self.closed = False

    def set_session(self, readonly=None, autocommit=None, isolation_level=None):
        self.set_session_calls.append(
            {"readonly": readonly, "autocommit": autocommit, "isolation_level": isolation_level}
        )
        self.events.append("set_session")

    def cursor(self):
        self.events.append("cursor")
        return _Cursor(self)

    def close(self):
        self.close_calls += 1
        self.closed = True


def _injected_session(conn, dsn="postgres://mock"):
    calls = {}

    def connect(got):
        calls["n"] = calls.get("n", 0) + 1
        calls["dsn"] = got
        return conn

    session = RealEvaluationSession(env={"DATABASE_URL": dsn}, connect_fn=connect)
    return session, calls


def _assert_secret_free(text):
    assert "SECRET" not in text, f"secret leaked: {text!r}"
    assert "postgres://user" not in text, f"credential leaked: {text!r}"
    assert "should-not-leak" not in text, f"secret leaked: {text!r}"


def test_d058_injected_config_failure_closes_exactly_once():
    conn = _FailConfigConn()
    session, calls = _injected_session(conn)
    with pytest.raises(RuntimeError, match="session config failed"):
        session.capture_executor("SHOW TimeZone")
    assert conn.close_calls == 1, f"cleanup must close exactly once, got {conn.close_calls}"
    assert session._conn is None, "half-configured resource must not be retained"
    assert session.is_closed is True, "session must stay fail-closed (no silent retry)"
    assert calls["n"] == 1
    # Second use must not reconnect.
    with pytest.raises(RuntimeError):
        session.capture_executor("SHOW TimeZone")
    assert calls["n"] == 1, "no silent reconnect after config failure"
    # Later session.close() must not close a second time (deterministic either way).
    try:
        session.close()
    except RuntimeError:
        pass
    assert conn.close_calls == 1, f"second close must not re-close, got {conn.close_calls}"


def test_d058_injected_config_error_is_secret_free():
    conn = _FailConfigConn()
    session, _ = _injected_session(conn)
    with pytest.raises(RuntimeError) as ei:
        session.capture_executor("SHOW TimeZone")
    text = str(ei.value)
    assert "session config failed" in text
    assert "ValueError" in text, "type name only is acceptable and expected"
    _assert_secret_free(text)


def test_d058_real_psycopg2_path_same_cleanup_as_injected():
    conn = _FailConfigConn()
    fake_mod = type(sys)("psycopg2")
    fake_mod.connect = lambda dsn: conn
    sys.modules["psycopg2"] = fake_mod
    try:
        session = RealEvaluationSession(env={"DATABASE_URL": "postgres://mock"})
        with pytest.raises(RuntimeError, match="session config failed"):
            session.capture_executor("SHOW TimeZone")
    finally:
        del sys.modules["psycopg2"]
    assert conn.close_calls == 1, f"real path must match injected: exactly one cleanup, got {conn.close_calls}"
    assert session._conn is None
    assert session.is_closed is True
    with pytest.raises(RuntimeError):
        session.capture_executor("SHOW TimeZone")
    try:
        session.close()
    except RuntimeError:
        pass
    assert conn.close_calls == 1


def test_d058_config_and_cleanup_both_fail_single_attempt_secret_free():
    conn = _FailBothConn()
    session, _ = _injected_session(conn)
    with pytest.raises(RuntimeError) as ei:
        session.capture_executor("SHOW TimeZone")
    text = str(ei.value)
    assert conn.close_calls == 1, f"cleanup attempted exactly once, got {conn.close_calls}"
    assert "session config failed" in text
    assert "cleanup" in text, f"dual failure must state config+cleanup: {text!r}"
    assert "ValueError" in text and "OSError" in text, f"type names expected: {text!r}"
    _assert_secret_free(text)
    assert session._conn is None, "failed resource must not be reusable"
    assert session.is_closed is True
    with pytest.raises(RuntimeError):
        session.capture_executor("SHOW TimeZone")
    try:
        session.close()
    except RuntimeError:
        pass
    assert conn.close_calls == 1


def test_d058_success_path_preserves_d057_contract():
    conn = _OkConn()
    session, _ = _injected_session(conn)
    assert session.capture_executor("SHOW TimeZone") == SYN_TZ
    assert conn.set_session_calls == [
        {"readonly": True, "autocommit": False, "isolation_level": "REPEATABLE READ"}
    ], f"D-057 exact tuple changed: {conn.set_session_calls}"
    assert conn.events[0] == "set_session", "config must precede first cursor"
    assert "cursor" in conn.events
    session.close()
    assert conn.close_calls == 1 and session.is_closed is True
    with pytest.raises(RuntimeError):
        session.close()


def test_d058_connect_failure_before_connection_no_close_target():
    def connect(dsn):
        raise RuntimeError("SECRET-connect-postgres://user:pass@host/should-not-leak")

    session = RealEvaluationSession(env={"DATABASE_URL": "postgres://mock"}, connect_fn=connect)
    with pytest.raises(RuntimeError) as ei:
        session.capture_executor("SHOW TimeZone")
    text = str(ei.value)
    assert "connect failed" in text
    _assert_secret_free(text)
    assert session._conn is None
