"""D-056 real-adapter wiring contracts — mock/static only, no real IO.

Proves the eight production-faithful surfaces share ONE governing session
with the exact lifecycle plan -> session -> SHOW TimeZone ->
SELECT CURRENT_DATE -> corpus load/provenance -> grant -> protected loader
-> run_start -> evaluation, with the pinned date immutable afterwards.

No protected dev/holdout plaintext, no real DB connect/query, no network,
no model/embedding load, no retrieval/latency benchmark, no Git recovery.
"""
import ast
import datetime
import hashlib
import json
import pathlib
import random
import sys
import tempfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from retrieval_v3.candidate_registry import load_and_validate
from retrieval_v3.evaluation_context import capture_pinned_context
from retrieval_v3.real_adapters import (
    CORPUS_SQL,
    D003_SQL,
    EMBED_DIM,
    EMBED_MODEL_ID,
    EMBED_QUERY_PREFIX,
    FROZEN_D003_BASELINE,
    OFFICIAL_LINK_MAPPING_BLOCKER,
    RealClock,
    RealD003Baseline,
    RealEmbeddingAdapter,
    RealEvaluationSession,
    RealProtectedLoader,
    RealSafetyAdapter,
    TransportOutcome,
    build_real_adapters,
    check_url_with_transport,
    parse_pgvector,
    read_database_url,
)
from retrieval_v3.runner import D003_BASELINE as RUNNER_D003, Runner
from retrieval_v3.safety import (
    MockHttpResponse,
    check_production_exclusion,
    check_single_url_with_mock,
    cross_check_owned_core,
    evaluate_owned_ambiguous,
    evaluate_owned_unsupported,
)
from retrieval_v3 import audit as _audit

REPO = pathlib.Path(__file__).resolve().parents[1]
RA_PATH = REPO / "eval" / "retrieval-v3" / "real_adapters.py"
SYN_TZ = "SYNTH-TZ"
SYN_DATE = "2026-02-10"


def _vec_text(seed, n=768):
    rnd = random.Random(seed)
    vals = [rnd.uniform(-1, 1) for _ in range(n)]
    return "[" + ",".join(f"{x:.6f}" for x in vals) + "]"


def _corpus_rows(specs):
    """specs: (pid, source, sid, nchunks, biz_end) -> CORPUS_SQL-ordered row tuples."""
    rows = []
    for pid, src, sid, nch, biz in specs:
        for ci in range(nch):
            rows.append((
                pid, src, sid, f"title {sid}", f"org {sid}", f"support {sid}",
                f"summary {sid}", f"kw {sid}", f"addq {sid}", f"inc {sid}",
                f"method {sid}", f"https://apply.example/{sid}", biz,
                None, None, None,
                1000 + pid * 10 + ci, ci, _vec_text(pid * 100 + ci),
            ))
    return rows


class FakeCursor:
    def __init__(self, conn):
        self._conn = conn
        self._rows = []

    def execute(self, sql, params=None):
        self._conn.statements.append(sql)
        self._conn.params.append(params)
        flat = " ".join(str(sql).split())
        if flat == "SHOW TimeZone":
            self._rows = [self._conn.tz_value]
        elif flat == "SELECT CURRENT_DATE":
            self._rows = [self._conn.date_value]
        elif "WITH nearest" in flat:
            self._rows = list(self._conn.d003_rows)
        elif "FROM policy p LEFT JOIN" in flat:
            self._rows = list(self._conn.corpus_rows)
        else:
            raise AssertionError(f"unexpected SQL in D-056 mock: {flat[:90]}")

    def fetchone(self):
        return self._rows[0] if self._rows else None

    def fetchall(self):
        return list(self._rows)

    def close(self):
        pass


class FakeConn:
    def __init__(self, corpus_rows=(), tz_value=(SYN_TZ,), date_value=None, d003_rows=()):
        self.corpus_rows = list(corpus_rows)
        self.tz_value = tz_value
        self.date_value = date_value if date_value is not None else (datetime.date(2026, 2, 10),)
        self.d003_rows = list(d003_rows)
        self.statements = []
        self.params = []
        self.closed = False
        self.set_session_calls = []

    def set_session(self, readonly=None, autocommit=None, isolation_level=None):
        self.set_session_calls.append({"readonly": readonly, "autocommit": autocommit, "isolation_level": isolation_level})

    def cursor(self):
        return FakeCursor(self)

    def close(self):
        self.closed = True

def _session(conn, dsn="postgres://mock"):
    seen = {}

    def connect(got):
        seen["dsn"] = got
        return conn

    session = RealEvaluationSession(env={"DATABASE_URL": dsn}, connect_fn=connect)
    return session, seen


class FakeModel:
    def __init__(self):
        self.calls = []

    def encode(self, texts, normalize_embeddings=False):
        assert normalize_embeddings is True, "production normalizes embeddings"
        out = []
        for t in texts:
            h = hashlib.sha256(t.encode()).digest()
            rnd = random.Random(int.from_bytes(h[:4], "little"))
            v = [rnd.uniform(-1, 1) for _ in range(768)]
            norm = (sum(x * x for x in v) ** 0.5) or 1
            out.append([x / norm for x in v])
        self.calls.append((list(texts), normalize_embeddings))
        return out


def _make_canonical_180():
    from retrieval_v3.runner import DEV_STRATA_EXACT
    order = ["exact_navigation", "natural_needs", "exploratory_multi_valid", "multi_constraint",
             "short_keywords", "colloquial_typo_spacing_abbrev", "ambiguous", "unsupported_no_answer"]
    tasks, idx, loc_made = [], 0, 0
    for s in order:
        for _ in range(DEV_STRATA_EXACT[s]):
            loc = loc_made < 54 and s in ("exact_navigation", "natural_needs", "multi_constraint")
            loc_made += 1 if loc else 0
            golds = [] if s == "unsupported_no_answer" else [{"source": "youth", "source_id": f"p{idx}", "grade": 1 if s == "ambiguous" else 2}]
            tasks.append({"task_id": f"c{idx:03d}", "query": f"query {idx} content",
                          "golds": golds, "stratum": s, "location_bearing": loc})
            idx += 1
    for t in tasks:
        if loc_made >= 54:
            break
        if t["stratum"] in ("exploratory_multi_valid", "short_keywords", "colloquial_typo_spacing_abbrev") and not t["location_bearing"]:
            t["location_bearing"] = True
            loc_made += 1
    return tasks


# ---- A) import-time IO detector ----

def test_d056_import_adds_no_drivers_or_network():
    import subprocess as _sp
    probe = (
        "import socket, sys; "
        "socket.socket.connect = lambda *a, **k: (_ for _ in ()).throw(AssertionError('net during import')) ; "
        "sys.path.insert(0, 'eval'); "
        "import retrieval_v3.real_adapters as ra; "
        "session = ra.RealEvaluationSession(env={}); "
        "ra.build_real_adapters(session, model_loader=lambda: (_ for _ in ()).throw(AssertionError('no load'))); "
        "mods = set(sys.modules); "
        "assert 'psycopg2' not in mods and 'sentence_transformers' not in mods, 'lazy drivers leaked at import'; "
        "print('IMPORT-CLEAN')"
    )
    proc = _sp.run([sys.executable, "-c", probe], capture_output=True, text=True, cwd=str(REPO))
    assert proc.returncode == 0, f"import-time IO detected: {proc.stderr[-2000:]}"
    assert "IMPORT-CLEAN" in proc.stdout


def test_d056_import_top_level_allowlist():
    tree = ast.parse(RA_PATH.read_text(encoding="utf-8"))
    allowed_std = {"__future__", "hashlib", "json", "math", "os", "pathlib", "time", "typing"}
    for node in tree.body:
        if isinstance(node, ast.Import):
            for a in node.names:
                assert a.name.split(".")[0] in allowed_std, f"top-level import {a.name} performs no IO proof violated"
        elif isinstance(node, ast.ImportFrom):
            if (node.level or 0) == 0:
                assert (node.module or "").split(".")[0] in allowed_std, f"top-level from-import {node.module} violates IO proof"


def test_d056_construction_performs_no_io():
    calls = []

    def connect(dsn):
        calls.append(dsn)
        raise AssertionError("connect at construction (forbidden)")

    session = RealEvaluationSession(env={"DATABASE_URL": "postgres://x"}, connect_fn=connect)
    assert calls == [], "session construction must not connect"
    adapters = build_real_adapters(session, model_loader=lambda: (_ for _ in ()).throw(AssertionError("no load")))
    assert calls == [], "adapter binding must not connect or load"
    assert session.is_closed is False
    session.close()


# ---- B) shared session ordering + canonical lifecycle ----

def test_d056_capture_exact_once_ordered():
    conn = FakeConn()
    session, _ = _session(conn)
    pinned = capture_pinned_context(session.capture_executor)
    assert pinned == {"db_session_timezone": SYN_TZ, "evaluation_as_of_date": SYN_DATE}
    assert session.pinned_context == pinned
    assert conn.statements == ["SHOW TimeZone", "SELECT CURRENT_DATE"]


def test_d056_capture_allowlist_rejects_third_and_set():
    conn = FakeConn()
    session, _ = _session(conn)
    for bad in ("SELECT 1", "SET TIME ZONE 'UTC'", "SHOW TimeZone; SELECT CURRENT_DATE", "show timezone", "select current_date"):
        try:
            session.capture_executor(bad)
            assert False, f"capture must reject {bad!r}"
        except (ValueError, RuntimeError):
            pass
    try:
        session.capture_executor("SHOW TimeZone")
        session.capture_executor("SHOW TimeZone")
        assert False, "duplicate SHOW must fail"
    except ValueError:
        pass
    session2, _ = _session(FakeConn())
    try:
        session2.capture_executor("SELECT CURRENT_DATE")
        assert False, "DATE before SHOW must fail"
    except ValueError:
        pass


def test_d056_corpus_load_before_capture_forbidden():
    conn = FakeConn(corpus_rows=_corpus_rows([(1, "youth", "p0", 1, None)]))
    session, _ = _session(conn)
    try:
        session.load_corpus_policies()
        assert False, "pre-capture corpus load must fail"
    except RuntimeError as e:
        assert "capture" in str(e).lower()
    assert conn.statements == [], "no DB touch before capture"


def test_d056_corpus_load_shape_and_provenance():
    rows = _corpus_rows([(2, "gov24", "g1", 1, "2026-01-01"), (1, "youth", "p0", 2, None)])
    conn = FakeConn(corpus_rows=rows)
    session, _ = _session(conn)
    capture_pinned_context(session.capture_executor)
    policies = session.load_corpus_policies()
    assert [p["source_id"] for p in policies] == ["g1", "p0"], "deterministic identity order"
    assert [len(p["chunks"]) for p in policies] == [1, 2]
    assert all(len(c["embedding"]) == 768 for p in policies for c in p["chunks"])
    assert policies[0]["biz_end"] == "2026-01-01"
    prov = session.corpus_provenance()
    assert prov["total_policies"] == 2 and prov["total_chunks"] == 3
    assert prov["evaluation_as_of_date"] == SYN_DATE and prov["db_session_timezone"] == SYN_TZ
    assert prov["snapshot"]["kind"] == "recomputable-content-fingerprint"
    assert len(prov["snapshot"]["corpus_sha256"]) == 64
    fp = prov["snapshot"]["corpus_sha256"]
    session2, _ = _session(FakeConn(corpus_rows=rows))
    capture_pinned_context(session2.capture_executor)
    session2.load_corpus_policies()
    assert session2.corpus_provenance()["snapshot"]["corpus_sha256"] == fp, "fingerprint must be recomputable"
    assert session.load_corpus_policies() is policies, "corpus cached: no second query"
    assert [s for s in conn.statements if "FROM policy" in s].__len__() == 1


def test_d056_corpus_malformed_fail_closed():
    good = _corpus_rows([(1, "youth", "p0", 1, None)])[0]

    def attempt(rows):
        s, _ = _session(FakeConn(corpus_rows=rows))
        capture_pinned_context(s.capture_executor)
        try:
            s.load_corpus_policies()
        except (ValueError, RuntimeError) as e:
            return str(e)
        return None
    assert attempt([]) is not None, "empty corpus must fail"
    dup = [good, good]
    assert attempt(dup) is not None, "duplicate identity must fail"
    short = list(good); short[-1] = _vec_text(9, 767)
    assert attempt([tuple(short)]) is not None, "767-dim vector must fail"
    badvec = list(good); badvec[-1] = "[not-a-number" + ",0" * 767 + "]"
    assert attempt([tuple(badvec)]) is not None, "non-numeric vector must fail"
    nonlocal_vec = list(good); nonlocal_vec[-1] = None
    assert attempt([tuple(nonlocal_vec)]) is not None, "missing vector must fail"
    noid = list(good); noid[1] = ""
    assert attempt([tuple(noid)]) is not None, "missing source must fail"
    unordered = _corpus_rows([(2, "youth", "p1", 1, None), (1, "youth", "p0", 1, None)])
    assert attempt(unordered) is not None, "nondeterministic row order must fail"


def test_d056_canonical_full_ordering_pinned_everywhere():
    specs = [(i + 1, "youth", f"p{i}", 1, None) for i in range(6)]
    conn = FakeConn(corpus_rows=_corpus_rows(specs))

    class OrderSession(RealEvaluationSession):
        def __init__(self):
            super().__init__(env={"DATABASE_URL": "postgres://mock"}, connect_fn=lambda dsn: conn)
            self.order = []

        def capture_executor(self, sql):
            self.order.append(("capture", sql))
            return super().capture_executor(sql)

        def execute_readonly(self, sql, params=None):
            flat = " ".join(str(sql).split())
            tag = "corpus" if "FROM policy p LEFT JOIN" in flat else ("d003" if "WITH nearest" in flat else flat[:24])
            self.order.append(("query", tag))
            return super().execute_readonly(sql, params)

        def load_corpus_policies(self):
            self.order.append(("corpus-load",))
            return super().load_corpus_policies()

    session = OrderSession()
    model = FakeModel()
    adapters = build_real_adapters(session, model_loader=lambda: model)
    tasks180 = _make_canonical_180()
    with tempfile.TemporaryDirectory() as td:
        mat = pathlib.Path(td) / "dev.jsonl"
        mat.write_bytes("\n".join(json.dumps(t, ensure_ascii=False) for t in tasks180).encode("utf-8"))
        set_sha = hashlib.sha256(mat.read_bytes()).hexdigest()
        audit_log = pathlib.Path(td) / "audit.jsonl"
        _audit.append_event(str(audit_log), action="protected_access_start", set_role="dev",
                            set_sha=set_sha, session_id="d056-full", candidate_id="v3-candidate-dev-v1", outcome="success")
        plan = load_and_validate()
        protected = RealProtectedLoader(mat, allowed_base=td)
        runner = Runner(candidate_plan=plan, embedding_fn=adapters["embedding_fn"],
                        db_policy_loader=adapters["policy_loader"], protected_set_loader=protected,
                        audit_log_path=audit_log, adapter_kind="real",
                        safety_evidence_fn=adapters["safety_evidence_fn"],
                        d003_baseline_fn=adapters["d003_baseline_fn"], clock_fn=adapters["clock_fn"],
                        corpus_provenance_fn=adapters["corpus_provenance_fn"],
                        evaluation_context_exec_fn=adapters["evaluation_context_fn"],
                        evaluation_session=session)
        res = runner.run_dev_evaluation(tasks=[], policies=[], session_id="d056-full", set_role="dev",
                                        set_sha=set_sha, audit_log=audit_log, output_path=None, skip_audit=False)
        chain = _audit.read_and_verify_chain(str(audit_log))
        starts = [e for e in chain if e.get("action") == "run_start"]
        assert len(starts) == 1 and starts[0].get("evaluation_as_of_date") == SYN_DATE
        assert session.is_closed is True, "session closed exactly once on success"
        body = json.dumps(res, ensure_ascii=False)
        assert "DATABASE_URL" not in body
        assert "DATABASE_URL" not in audit_log.read_text(encoding="utf-8")
    kinds = [o[0] for o in session.order]
    assert kinds[0] == "capture" and session.order[0][1] == "SHOW TimeZone"
    assert kinds[1] == "capture" and session.order[1][1] == "SELECT CURRENT_DATE"
    assert ("corpus-load",) in session.order
    captures = [o for o in session.order if o[0] == "capture"]
    assert len(captures) == 2, f"exactly-once capture, got {captures}"
    post_capture = [s for s in conn.statements if s not in ("SHOW TimeZone", "SELECT CURRENT_DATE")]
    assert post_capture, "corpus + D-003 queries must run post-capture"
    assert all("CURRENT_DATE" not in s for s in post_capture), "no runtime CURRENT_DATE anywhere after pinning"
    pinned = {"db_session_timezone": SYN_TZ, "evaluation_as_of_date": SYN_DATE}
    assert res["evaluation_context"] == pinned
    assert res["corpus_provenance"]["db_session_timezone"] == SYN_TZ
    assert res["corpus_provenance"]["evaluation_as_of_date"] == SYN_DATE
    d003_as_of = {p["as_of"] for p in conn.params if isinstance(p, dict) and "as_of" in p}
    assert d003_as_of == {SYN_DATE}, f"D-003 must carry the pinned date only, got {d003_as_of}"


def test_d056_canonical_cli_no_precapture_load_and_cleanup():
    conn = FakeConn(corpus_rows=_corpus_rows([(1, "youth", "p0", 1, None)]))
    events = []

    class RecordingSession(RealEvaluationSession):
        def __init__(self):
            super().__init__(env={"DATABASE_URL": "postgres://mock"}, connect_fn=lambda dsn: conn)

        def capture_executor(self, sql):
            events.append(("capture", sql))
            return super().capture_executor(sql)

        def load_corpus_policies(self):
            events.append(("corpus-load",))
            return super().load_corpus_policies()

    import retrieval_v3.runner as R
    real_cls = R.RealEvaluationSession
    R.RealEvaluationSession = RecordingSession
    try:
        with tempfile.TemporaryDirectory() as td:
            audit_log = pathlib.Path(td) / "audit.jsonl"
            _audit.append_event(str(audit_log), action="protected_access_start", set_role="dev",
                                set_sha="c" * 64, session_id="cli-order", candidate_id="v3-candidate-dev-v1", outcome="success")
            args = R.parse_args(["--session-id", "cli-order", "--set-role", "dev", "--set-sha", "c" * 64,
                                 "--audit-log", str(audit_log), "--output", "eval/retrieval-v3/results/v3-candidate-dev-result.json"])
            try:
                R.main_canonical_dev(args)
                assert False, "loader without materialized path must fail"
            except RuntimeError as e:
                assert "materialized" in str(e).lower() or "loader" in str(e).lower()
            kinds = [e[0] for e in events]
            assert kinds[0] == "capture", f"capture first, got {events}"
            assert "corpus-load" in kinds and kinds.index("corpus-load") > 1, f"corpus after capture: {events}"
    finally:
        R.RealEvaluationSession = real_cls
    assert conn.closed is True, "CLI session cleaned up on failure"


# ---- C) pinned-date propagation ----

def test_d056_pinned_context_immutable_copy():
    conn = FakeConn()
    session, _ = _session(conn)
    capture_pinned_context(session.capture_executor)
    first = session.pinned_context
    first["evaluation_as_of_date"] = "1999-01-01"
    assert session.pinned_context["evaluation_as_of_date"] == SYN_DATE, "pin must be immutable"


def test_d056_session_close_exact_once():
    session, _ = _session(FakeConn())
    assert session.is_closed is False
    session.close()
    assert session.is_closed is True
    try:
        session.close()
        assert False, "second close must raise"
    except RuntimeError as e:
        assert "exact-one" in str(e) or "already closed" in str(e)
    try:
        session.capture_executor("SHOW TimeZone")
        assert False, "use after close must fail"
    except RuntimeError:
        pass


def test_d056_corpus_sql_readonly_source_load():
    import re as _re
    flat = " ".join(CORPUS_SQL.split())
    upper = flat.upper()
    assert "ORDER BY" in upper, "deterministic ordering required"
    for forbidden in ("INSERT", "UPDATE", "DELETE", "DROP", "CREATE", "ALTER", "TRUNCATE", "GRANT", "COPY", "VACUUM",
                      "SET TIME ZONE", "SET SESSION", "SET LOCAL", "CURRENT_DATE", "<=>"):
        assert forbidden not in upper, f"corpus load must not contain {forbidden} (source load only, no ranking/date)"
    assert _re.search(r"\bLIMIT\b", upper) is None, "corpus load is a full source load (no ranking LIMIT)"
    assert upper.lstrip().startswith("SELECT"), "corpus load is a SELECT"


def test_d056_runner_closes_session_on_success_and_failures():
    plan = load_and_validate()

    def _policies(n=3):
        out = []
        for i in range(n):
            out.append({"id": i, "source": "youth", "source_id": f"p{i}", "title": f"policy {i}",
                        "support_content": "", "summary": "", "keywords": "", "add_qualify": "",
                        "income_etc": "", "apply_method": "", "org": "org",
                        "chunks": [{"embedding": [0.1] * 768, "chunk_index": 0, "id": i}]})
        return out

    def _ctx():
        def fn(sql):
            return {"SHOW TimeZone": SYN_TZ, "SELECT CURRENT_DATE": SYN_DATE}[sql]
        return fn

    tasks = [{"task_id": "t0", "query": "policy zero", "golds": [{"source": "youth", "source_id": "p0", "grade": 2}],
              "stratum": "natural_needs", "location_bearing": False}]

    def _run(session, embedding):
        runner = Runner(candidate_plan=plan, embedding_fn=embedding, audit_log_path=pathlib.Path("/none"),
                        evaluation_context_exec_fn=_ctx(), evaluation_session=session)
        with tempfile.TemporaryDirectory() as td:
            return runner.run_dev_evaluation(tasks=tasks, policies=_policies(), session_id="s", set_role="none",
                                             set_sha=None, audit_log=pathlib.Path(td) / "a.jsonl",
                                             output_path=None, skip_audit=True)

    ok_session = RealEvaluationSession(env={})
    _run(ok_session, lambda q: [0.1] * 768)
    assert ok_session.is_closed is True, "success must close the bound session"

    def _boom(q):
        raise RuntimeError("synthetic retrieval failure")

    fail_session = RealEvaluationSession(env={})
    try:
        _run(fail_session, _boom)
        assert False, "retrieval failure must propagate"
    except RuntimeError:
        pass
    assert fail_session.is_closed is True, "retrieval failure must still close the bound session"

    cap_session = RealEvaluationSession(env={})
    runner = Runner(candidate_plan=plan, embedding_fn=lambda q: [0.1] * 768,
                    evaluation_context_exec_fn=lambda sql: (_ for _ in ()).throw(RuntimeError("synthetic capture failure")),
                    evaluation_session=cap_session)
    with tempfile.TemporaryDirectory() as td:
        try:
            runner.run_dev_evaluation(tasks=tasks, policies=_policies(), session_id="s", set_role="none",
                                      set_sha=None, audit_log=pathlib.Path(td) / "a.jsonl",
                                      output_path=None, skip_audit=True)
            assert False
        except RuntimeError:
            pass
    assert cap_session.is_closed is True, "capture failure must still close the bound session"


# ---- D) protected loader ----

def _write_tasks(path, tasks):
    path.write_bytes("\n".join(json.dumps(t, ensure_ascii=False) for t in tasks).encode("utf-8"))
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_d056_protected_loader_explicit_path_and_sha():
    tasks = [{"task_id": "t0", "query": "alpha query", "golds": [], "stratum": "natural_needs", "location_bearing": False}]
    with tempfile.TemporaryDirectory() as td:
        mat = pathlib.Path(td) / "dev.jsonl"
        digest = _write_tasks(mat, tasks)
        loader = RealProtectedLoader(mat, allowed_base=td)
        assert loader("dev", digest) == tasks
        try:
            loader("dev", "0" * 64)
            assert False, "wrong SHA must fail"
        except ValueError as e:
            assert "mismatch" in str(e).lower()
        try:
            loader("holdout", digest)
            assert False, "holdout role must fail"
        except ValueError as e:
            assert "holdout" in str(e).lower()
        try:
            RealProtectedLoader(None)("dev", digest)
            assert False, "absent path must fail closed"
        except RuntimeError as e:
            assert "pre-gate" in str(e).lower() or "no authorized" in str(e).lower()


def test_d056_protected_loader_confinement():
    tasks = [{"task_id": "t0", "query": "alpha query"}]
    with tempfile.TemporaryDirectory() as td1, tempfile.TemporaryDirectory() as td2:
        mat = pathlib.Path(td2) / "dev.jsonl"
        digest = _write_tasks(mat, tasks)
        try:
            RealProtectedLoader(mat, allowed_base=td1)("dev", digest)
            assert False, "outside-base path must fail"
        except ValueError as e:
            assert "escapes" in str(e).lower()
        nested = pathlib.Path(td1) / "sub" / ".." / "dev.jsonl"
        _write_tasks(pathlib.Path(td1) / "dev.jsonl", tasks)
        assert RealProtectedLoader(nested, allowed_base=td1)("dev", digest) == tasks, "lexical .. resolving inside base is fine"
        link = pathlib.Path(td1) / "link.jsonl"
        try:
            link.symlink_to(mat)
        except (OSError, NotImplementedError):
            return
        try:
            RealProtectedLoader(link, allowed_base=td1)("dev", digest)
            assert False, "symlink escape must fail"
        except ValueError as e:
            assert "escapes" in str(e).lower()


def test_d056_protected_loader_malformed_fail_closed():
    with tempfile.TemporaryDirectory() as td:
        mat = pathlib.Path(td) / "dev.jsonl"
        mat.write_bytes(b"{not json}\n")
        loader = RealProtectedLoader(mat, allowed_base=td)
        try:
            loader("dev", hashlib.sha256(mat.read_bytes()).hexdigest())
            assert False
        except ValueError as e:
            assert "jsonl" in str(e).lower()
        mat.write_bytes(b'{"query": "no id"}\n')
        try:
            loader("dev", hashlib.sha256(mat.read_bytes()).hexdigest())
            assert False
        except ValueError as e:
            assert "task id" in str(e).lower()
        mat.write_bytes(b"")
        try:
            loader("dev", hashlib.sha256(mat.read_bytes()).hexdigest())
            assert False
        except ValueError as e:
            assert "empty" in str(e).lower()
        try:
            loader("dev", "not-hex")
            assert False
        except ValueError:
            pass


def test_d056_secrets_never_surface():
    try:
        read_database_url({})
        assert False
    except RuntimeError as e:
        assert "postgres" not in str(e) and "://" not in str(e)

    def nasty(dsn):
        assert dsn == "postgres://SECRET-u:SECRET-p@SECRET-h/db"
        raise RuntimeError("driver says SECRET-h down SECRET-p")

    session = RealEvaluationSession(env={"DATABASE_URL": "postgres://SECRET-u:SECRET-p@SECRET-h/db"}, connect_fn=nasty)
    try:
        session.capture_executor("SHOW TimeZone")
        assert False
    except RuntimeError as e:
        assert "SECRET" not in str(e), f"secret leaked into message: {e}"


def test_d056_no_git_recovery_implementation():
    src = RA_PATH.read_text(encoding="utf-8")
    assert "subprocess" not in src, "no process/Git recovery machinery"
    for token in ("cat-file", "git show", "sparse", "worktree", "clone", "checkout", "ls-remote", "rev-parse"):
        assert token not in src, f"no protected-data recovery vector {token!r}"


# ---- E) DB adapter read-only + validation + secrets ----

def test_d056_readonly_session_setup():
    calls = {}

    class FakeDriverConn:
        def set_session(self, readonly=None, autocommit=None, isolation_level=None):
            calls["session"] = (readonly, autocommit, isolation_level)

        def cursor(self):
            raise AssertionError("no query in this test")

        def close(self):
            calls["closed"] = True

    import sys as _sys
    fake_mod = type(sys)("psycopg2")
    fake_mod.connect = lambda dsn: (calls.setdefault("dsn", dsn), FakeDriverConn())[1]
    _sys.modules["psycopg2"] = fake_mod
    try:
        session = RealEvaluationSession(env={"DATABASE_URL": "postgres://db"})
        session._ensure_conn()
    finally:
        del _sys.modules["psycopg2"]
    assert calls["session"] == (True, False, "REPEATABLE READ"), f"read-only consistent-snapshot session required, got {calls.get('session')}"
    session.close()
    assert calls.get("closed") is True


def test_d056_execute_readonly_rejects_writes():
    session, _ = _session(FakeConn())
    for bad in ("DELETE FROM policy", "UPDATE policy SET title='x'", "SET TIME ZONE 'UTC'", "SELECT 1; DROP TABLE policy"):
        try:
            session.execute_readonly(bad)
            assert False, f"must reject {bad[:20]}"
        except (ValueError, RuntimeError):
            pass


# ---- F) embedding adapter ----

def test_d056_embedding_contract_and_prefix():
    assert EMBED_MODEL_ID == "intfloat/multilingual-e5-base" and EMBED_DIM == 768
    assert EMBED_QUERY_PREFIX == "query: "
    adapter = RealEmbeddingAdapter(model_loader=FakeModel)
    try:
        adapter("no prefix here")
        assert False
    except ValueError as e:
        assert "prefix" in str(e).lower()
    try:
        adapter("query:   ")
        assert False
    except ValueError:
        pass


def test_d056_embedding_dim_normalize_single_load():
    model = FakeModel()
    loads = []

    def loader():
        loads.append(1)
        return model

    adapter = RealEmbeddingAdapter(model_loader=loader)
    assert adapter.model_id == EMBED_MODEL_ID
    vec = adapter("query: 청년 지원 정책")
    assert len(vec) == EMBED_DIM and all(isinstance(x, float) for x in vec)
    import math
    assert abs(sum(x * x for x in vec) ** 0.5 - 1.0) < 1e-6, "production normalizes embeddings"
    texts, norm = model.calls[0]
    assert texts == ["query: 청년 지원 정책"] and norm is True
    adapter("query: second")
    assert len(loads) == 1, "model loads once and is shared"


def test_d056_embedding_loader_failure_fail_closed():
    def loader():
        raise RuntimeError("weights absent (synthetic)")

    adapter = RealEmbeddingAdapter(model_loader=loader)
    try:
        adapter("query: x")
        assert False
    except RuntimeError as e:
        assert "fail-closed" in str(e)


def test_d056_embedding_local_only_no_fallback_static():
    src = RA_PATH.read_text(encoding="utf-8")
    assert "local_files_only=True" in src, "offline-first model load required"
    assert src.count("SentenceTransformer(") == 1, "single exact-model construction, no fallback"
    assert "from_pretrained" not in src or "local_files_only" in src


# ---- G) D-003 paired baseline ----

def test_d056_d003_descriptor_frozen():
    assert FROZEN_D003_BASELINE == RUNNER_D003, "adapter descriptor must equal the runner frozen descriptor"
    assert FROZEN_D003_BASELINE == {"RERANK": 0, "CANDIDATES": 30, "COSINE_MIN": 0.78, "LEXICAL_BIAS": 0.01,
                                    "strip_region": True, "youth_bias_suppressed_for_gov24_orgs": True,
                                    "embedding": "intfloat/multilingual-e5-base"}
    conn = FakeConn()
    session, _ = _session(conn)
    capture_pinned_context(session.capture_executor)
    baseline = RealD003Baseline(session, lambda q: [0.1] * 768)
    try:
        baseline("t0", "query text", {"RERANK": 1})
        assert False
    except ValueError as e:
        assert "drift" in str(e).lower()
    try:
        baseline("t0", "   ", dict(FROZEN_D003_BASELINE))
        assert False
    except ValueError:
        pass


def test_d056_d003_pinned_date_both_predicates():
    conn = FakeConn()
    session, _ = _session(conn)
    capture_pinned_context(session.capture_executor)
    seen = {}

    def emb(q):
        seen["q"] = q
        return [0.2] * 768

    baseline = RealD003Baseline(session, emb)
    out = baseline("t0", "서울 청년 지원", dict(FROZEN_D003_BASELINE),
                   {"db_session_timezone": SYN_TZ, "evaluation_as_of_date": SYN_DATE})
    assert out["evaluation_as_of_date"] == SYN_DATE and out["descriptor"] == FROZEN_D003_BASELINE
    assert seen["q"].startswith("query: ") and "서울" not in seen["q"], "strip_region production semantics"
    dparams = [p for p in conn.params if isinstance(p, dict)]
    assert len(dparams) == 1
    params = dparams[0]
    assert params["as_of"] == SYN_DATE and params["age"] is None and params["rp"] is None
    assert params["n"] == 30 and params["lexical_bias"] == 0.01
    sql = conn.statements[-1]
    assert sql.count("%(as_of)s") == 2, "pinned date in BOTH expiry predicates"
    assert "CURRENT_DATE" not in sql
    assert session.d003_queries == 1


def test_d056_d003_sql_parity_with_production():
    import re
    src = (REPO / "ml-service" / "app.py").read_text(encoding="utf-8")
    prod = re.search(r"SQL = \"\"\"(.*?)\"\"\"", src, re.S).group(1)

    def norm(s):
        s = "\n".join(line.split("--")[0] for line in s.splitlines())
        return re.sub(r"\s+", " ", s).strip()

    assert norm(D003_SQL.replace("%(as_of)s", "CURRENT_DATE")) == norm(prod), "D-003 SQL must equal production modulo the pinned date"


def test_d056_d003_no_candidate_baseline_static():
    src = RA_PATH.read_text(encoding="utf-8")
    assert "candidate-a-01" not in src, "candidate configs must never be the baseline"
    assert "strip_region" in src and "youth_source_bias" in src and "lexical_overlap_terms" in src and "format_qvec" in src


# ---- H) safety evidence ----

def _safety_session():
    rows = _corpus_rows([(2, "gov24", "g1", 1, None), (1, "youth", "p0", 1, None)])
    conn = FakeConn(corpus_rows=rows)
    session, _ = _session(conn)
    capture_pinned_context(session.capture_executor)
    session.load_corpus_policies()
    return session


def _safety_payload():
    def tr(tid, action, visible, internal):
        return {"task_id": tid, "stratum": "natural_needs", "safe_action": action,
                "retrieved": visible, "retrieved_internal": internal}

    return {"config_id": "candidate-a-01", "results": {"task_results": [
        tr("t0", "ANSWER", [{"source": "youth", "source_id": "p0"}], [{"source": "youth", "source_id": "p0"}]),
        tr("t1", "ABSTAIN", [], [{"source": "gov24", "source_id": "g1"}]),
    ]}}


def test_d056_safety_hold_without_authoritative_evidence():
    session = _safety_session()
    calls = []

    def transport(url, method, timeout):
        calls.append((url, method))
        return TransportOutcome(status=200)

    adapter = RealSafetyAdapter(session, http_transport=transport)
    ev = adapter(_safety_payload())
    assert set(ev) == {"unsupported", "ambiguous", "production_exclusion", "official_link", "http_resolution", "cost"}
    for gate in ("unsupported", "ambiguous", "production_exclusion", "official_link", "http_resolution", "cost"):
        assert ev[gate]["gate"] in ("PASS", "NO-GO", "HOLD")
    assert ev["official_link"]["gate"] == "HOLD" and "mapping" in ev["official_link"]["detail"].lower()
    assert OFFICIAL_LINK_MAPPING_BLOCKER.split(":")[0] in ev["official_link"]["detail"]
    assert ev["http_resolution"]["gate"] == "HOLD"
    assert ev["cost"]["gate"] == "HOLD" and ev["cost"]["extra_model_calls"] == 0
    assert calls == [], "no benchmark HTTP in D-056"


def test_d056_safety_owned_core_matches_runner():
    session = _safety_session()
    adapter = RealSafetyAdapter(session)
    payload = _safety_payload()
    ev = adapter(payload)
    tres = payload["results"]["task_results"]
    top5 = {tr["task_id"]: [(d["source"], d["source_id"]) for d in tr["retrieved_internal"][:5]] for tr in tres}
    gate, det = check_production_exclusion(top5, session.biz_end_lookup, SYN_DATE, len(tres), len(tres) * 5)
    owned = {"unsupported": evaluate_owned_unsupported(None), "ambiguous": evaluate_owned_ambiguous(None),
             "production_exclusion": {"gate": gate, **det}}
    cross_check_owned_core(owned, ev)
    assert ev["unsupported"]["gate"] == "HOLD" and ev["ambiguous"]["gate"] == "HOLD", "no safety-stratum tasks in payload"
    assert ev["production_exclusion"]["gate"] == gate


def test_d056_safety_official_link_denominator_exact():
    session = _safety_session()

    def tr(tid, visible):
        return {"task_id": tid, "stratum": "natural_needs", "safe_action": "ANSWER",
                "retrieved": visible, "retrieved_internal": visible}

    payload = {"config_id": "c", "results": {"task_results": [
        tr("t0", [{"source": "youth", "source_id": "p0"}, {"source": "gov24", "source_id": "g1"}]),
        tr("t1", [{"source": "youth", "source_id": "p0"}, {"source": "youth", "source_id": "p0 "}]),
        tr("t2", []),
    ]}}
    ev = RealSafetyAdapter(session)(payload)
    det = ev["official_link"]
    assert det["visible_slots"] == 4, "visible top-5 only (suppressed tasks contribute nothing)"
    assert det["unique_urls"] == 2, "exact-string trim-only dedupe"
    assert det["url_field"] == "apply_url"


def test_d056_http_state_machine_parity_with_frozen():
    def scripted(head_seq, get_seq):
        h, g = list(head_seq), list(get_seq)

        def t(url, method, timeout):
            assert timeout == (5, 10), "frozen timeout pair"
            seq = h if method == "HEAD" else g
            assert seq, "mock exhaustion must fail closed, never authorize fallback"
            kind = seq.pop(0)
            if kind[0] == "status":
                return TransportOutcome(status=kind[1], location=kind[2] if len(kind) > 2 else None)
            return TransportOutcome(error=kind[1])

        return t

    def mock_resp(kind):
        if kind[0] == "status":
            return MockHttpResponse(status=kind[1], redirect_location=kind[2] if len(kind) > 2 else None)
        flag = kind[1]
        return MockHttpResponse(status=None, is_network_error=flag == "network",
                                is_tls_error=flag == "tls", is_timeout=flag == "timeout")

    R1 = "https://apply.example/a"
    scenarios = [
        ([("status", 200)], [], True),
        ([("status", 405)], [("status", 200)], True),
        ([("status", 404)], [], False),
        ([("status", 500), ("status", 200)], [], True),
        ([("error", "timeout"), ("error", "timeout")], [("status", 200)], False),
        ([("error", "network"), ("error", "network")], [("status", 200)], True),
        ([("status", 301, R1), ("status", 200)], [], True),
        ([("status", 301, R1)] * 4, [], False),
        ([("status", 405)], [("status", 405)], False),
    ]
    for head, get, expected in scenarios:
        got = check_url_with_transport(R1, scripted(list(head), list(get)))
        want = check_single_url_with_mock(R1, [mock_resp(k) for k in head], [mock_resp(k) for k in get])
        assert got == want == expected, f"transport parity failed for {head}/{get}: {got} vs {want}"
    assert check_url_with_transport("  ", scripted([], [])) is False


def test_d056_safety_malformed_payload_fail_closed():
    session = _safety_session()
    adapter = RealSafetyAdapter(session)
    for bad in (None, {}, {"results": {}}, {"results": {"task_results": []}}, {"results": {"task_results": [None]}}):
        try:
            adapter(bad)
            assert False, f"malformed payload {bad!r} must fail"
        except (ValueError, AttributeError):
            pass


def test_d056_cost_hook_measured_not_assumed():
    session = _safety_session()
    ev = RealSafetyAdapter(session)(_safety_payload())
    cost = ev["cost"]
    assert cost["policies"] == 2 and cost["corpus_rows_scanned"] == 2
    assert cost["d003_queries"] == 0 and cost["extra_model_calls"] == 0
    for key in ("index_ratio", "rows_ratio"):
        assert key not in cost, f"cost must not assume {key}"


# ---- I) clock ----

def test_d056_clock_monotonic_ns():
    import time as _time
    src = RA_PATH.read_text(encoding="utf-8")
    assert "perf_counter_ns" in src, "monotonic high-resolution clock required"
    clock = RealClock()
    assert getattr(clock, "__real_adapter__", False) is True
    a, b = clock(), clock()
    assert isinstance(a, int) and isinstance(b, int) and b >= a
    assert abs(_time.perf_counter_ns() - b) < 60_000_000_000, "clock tracks the standing source"


# ---- J) mirrors, descriptors, leakage ----

def test_d056_mirrors_byte_identical():
    for name in ("real_adapters.py", "runner.py"):
        h1 = hashlib.sha256((REPO / "eval" / "retrieval-v3" / name).read_bytes()).hexdigest()
        h2 = hashlib.sha256((REPO / "eval" / "retrieval_v3" / name).read_bytes()).hexdigest()
        assert h1 == h2, f"mirror mismatch {name}"


def test_d056_no_secret_or_dsn_leakage_static():
    src = RA_PATH.read_text(encoding="utf-8")
    assert "print(" not in src and "logging" not in src, "adapters never print/log (DSN cannot leak)"
    assert src.count("DATABASE_URL") <= 5, "DATABASE_URL referenced only at the env read and fail-closed messages"

def test_d056_vector_parser_rejects_garbage():
    assert parse_pgvector(_vec_text(3)) and len(parse_pgvector(_vec_text(3))) == 768
    for bad in ("", "1,2,3", "[1,2]", "[nan" + ",0" * 767 + "]", "[inf" + ",0" * 767 + "]", None, 42):
        try:
            parse_pgvector(bad)
            assert False, f"vector {str(bad)[:20]!r} must fail"
        except (ValueError, TypeError):
            pass


def test_d056_materialized_evalset_arg_defaults_unset():
    from retrieval_v3.runner import parse_args
    args = parse_args(["--session-id", "s"])
    assert getattr(args, "materialized_evalset", "missing") is None, "no standing materialization in D-056"
