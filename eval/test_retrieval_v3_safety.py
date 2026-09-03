import math, pathlib, hashlib, json
import sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from retrieval_v3.safety import (
    dedupe_official_links,
    validate_snapshot_pin,
    SnapshotPinError,
    check_single_url_with_mock,
    MockHttpResponse,
    evaluate_http_resolution,
    evaluate_official_link_semantic_match,
    check_ineligible_expired,
    check_unsupported_ambiguous,
)

def test_snapshot_pin_fail_closed():
    snap = {"snapshot_id": "v1", "sha256": "a"*64, "eligible_map": {}}
    # missing pin => HOLD
    try:
        validate_snapshot_pin(snap, None)
        assert False, "should raise"
    except SnapshotPinError:
        pass
    # mismatched pin
    try:
        validate_snapshot_pin(snap, "b"*64)
        assert False
    except SnapshotPinError:
        pass
    # absent snapshot
    try:
        validate_snapshot_pin(None, "a"*64)
        assert False
    except SnapshotPinError:
        pass
    # correct
    validate_snapshot_pin(snap, "a"*64)

def test_dedupe_exact_string_after_trim():
    urls = [" https://example.com/a ", "https://example.com/a", "https://example.com/A", "https://example.com/b ", " https://example.com/b"]
    uniq = dedupe_official_links(urls)
    # exact-string after trim, case-sensitive, so "a" and "A" are different, duplicates removed
    assert uniq == ["https://example.com/a", "https://example.com/A", "https://example.com/b"]
    # empty
    assert dedupe_official_links([]) == []
    assert dedupe_official_links(["   ", " "]) == []

def test_http_head_200_success():
    ok = check_single_url_with_mock(
        "https://example.com/a",
        [MockHttpResponse(status=200)],
        []
    )
    assert ok is True

def test_http_head_301_redirect_success():
    ok = check_single_url_with_mock(
        "https://example.com/b",
        [MockHttpResponse(status=301, redirect_location="https://example.com/b2"), MockHttpResponse(status=200)],
        []
    )
    assert ok is True

def test_http_head_405_fallback_get_success():
    ok = check_single_url_with_mock(
        "https://example.com/c",
        [MockHttpResponse(status=405)],
        [MockHttpResponse(status=200)]
    )
    assert ok is True

def test_http_network_error_fallback_get_success():
    ok = check_single_url_with_mock(
        "https://example.com/d",
        [MockHttpResponse(is_network_error=True)],
        [MockHttpResponse(status=200)]
    )
    assert ok is True

def test_http_head_404_no_fallback_fail():
    ok = check_single_url_with_mock(
        "https://example.com/e",
        [MockHttpResponse(status=404)],
        []
    )
    assert ok is False

def test_http_retry_success():
    # first HEAD 500, second HEAD 200 (retry)
    ok = check_single_url_with_mock(
        "https://example.com/f",
        [MockHttpResponse(status=500), MockHttpResponse(status=200)],
        []
    )
    assert ok is True

def test_http_exceed_redirects_fail():
    ok = check_single_url_with_mock(
        "https://example.com/g",
        [
            MockHttpResponse(status=301, redirect_location="1"),
            MockHttpResponse(status=301, redirect_location="2"),
            MockHttpResponse(status=301, redirect_location="3"),
            MockHttpResponse(status=301, redirect_location="4"),
        ],
        []
    )
    assert ok is False  # exceeds 3

def test_http_resolution_threshold_ceil():
    # 100 unique, need ceil(0.99*100)=99
    urls = [f"https://example.com/{i}" for i in range(100)]
    mocks = {}
    for i, u in enumerate(urls):
        if i < 99:
            mocks[u] = ([MockHttpResponse(status=200)], [])
        else:
            mocks[u] = ([MockHttpResponse(status=404)], [])
    snap = {"snapshot_id": "v1", "sha256": "a"*64}
    gate, details = evaluate_http_resolution(urls, mocks, snap, "a"*64)
    assert gate == "PASS"
    assert details["required"] == 99
    assert details["successes"] == 99
    # 98 successes => NO-GO
    for i in range(98, 100):
        u = urls[i]
        mocks[u] = ([MockHttpResponse(status=404)], [])
    gate, details = evaluate_http_resolution(urls, mocks, snap, "a"*64)
    assert gate == "NO-GO"
    assert details["successes"] == 98

def test_http_resolution_small_denom_ceil():
    # 50 unique, ceil(0.99*50)=ceil(49.5)=50 => need 50/50
    urls = [f"https://example.com/{i}" for i in range(50)]
    mocks = {u: ([MockHttpResponse(status=200)], []) for u in urls}
    snap = {"snapshot_id": "v1", "sha256": "a"*64}
    gate, _ = evaluate_http_resolution(urls, mocks, snap, "a"*64)
    assert gate == "PASS"
    # one failure => 49/50 <50 => NO-GO
    mocks[urls[0]] = ([MockHttpResponse(status=404)], [])
    gate, _ = evaluate_http_resolution(urls, mocks, snap, "a"*64)
    assert gate == "NO-GO"

def test_http_missing_measurement_hold():
    snap = {"snapshot_id": "v1", "sha256": "a"*64}
    # empty unique => HOLD
    gate, details = evaluate_http_resolution([], {}, snap, "a"*64)
    assert gate == "HOLD"
    # missing mock for one URL => HOLD
    urls = ["https://example.com/a", "https://example.com/b"]
    mocks = {"https://example.com/a": ([MockHttpResponse(status=200)], [])}
    gate, _ = evaluate_http_resolution(urls, mocks, snap, "a"*64)
    assert gate == "HOLD"
    # missing snapshot pin => HOLD
    gate, _ = evaluate_http_resolution(urls, mocks, None, None)
    assert gate == "HOLD"

def test_official_link_semantic_100_percent():
    snap = {"snapshot_id": "v1", "sha256": "a"*64}
    urls = ["https://gov.kr/a", "https://gov.kr/b"]
    expected = {"https://gov.kr/a": "gov.kr", "https://gov.kr/b": "gov.kr"}
    gate, _ = evaluate_official_link_semantic_match(urls, expected, snap, "a"*64)
    assert gate == "PASS"
    # one mismatch => NO-GO
    expected2 = {"https://gov.kr/a": "gov.kr", "https://gov.kr/b": "other.kr"}
    gate, _ = evaluate_official_link_semantic_match(urls, expected2, snap, "a"*64)
    assert gate == "NO-GO"
    # missing => HOLD
    gate, _ = evaluate_official_link_semantic_match([], {}, snap, "a"*64)
    assert gate == "HOLD"

def test_ineligible_expired_exact_denominators():
    snap = {
        "snapshot_id": "v1",
        "sha256": "a"*64,
        "eligible_map": {
            ("src1", "id1"): {"eligible": True, "expired": False},
            ("src2", "id2"): {"eligible": False, "expired": False},
            ("src3", "id3"): {"eligible": True, "expired": True},
        }
    }
    # holdout 250 tasks, each 5 => but we test small for logic, use expected 2 tasks for pure test
    # Use expected 2 tasks, 10 slots for test (not 250, but we pass expected)
    top5 = {
        "t1": [("src1","id1")]*5,
        "t2": [("src1","id1")]*5,
    }
    gate, _ = check_ineligible_expired(top5, snap, "a"*64, expected_tasks=2, expected_slots=10)
    assert gate == "PASS"
    # one intrusion => NO-GO
    top5_intrusion = {
        "t1": [("src1","id1")]*4 + [("src2","id2")],
        "t2": [("src1","id1")]*5,
    }
    gate, _ = check_ineligible_expired(top5_intrusion, snap, "a"*64, expected_tasks=2, expected_slots=10)
    assert gate == "NO-GO"
    # missing eligibility => HOLD
    top5_missing = {
        "t1": [("src1","id1")]*4 + [("src_unknown","idx")],
        "t2": [("src1","id1")]*5,
    }
    gate, _ = check_ineligible_expired(top5_missing, snap, "a"*64, expected_tasks=2, expected_slots=10)
    assert gate == "HOLD"
    # wrong task count => HOLD
    gate, _ = check_ineligible_expired({"t1": [("src1","id1")]*5}, snap, "a"*64, expected_tasks=2, expected_slots=10)
    assert gate == "HOLD"
    # missing snapshot pin => HOLD
    gate, _ = check_ineligible_expired(top5, snap, None, expected_tasks=2, expected_slots=10)
    assert gate == "HOLD"

def test_unsupported_ambiguous_integer_cutoffs():
    # holdout 38 unsupported, 32 ambiguous exact
    # PASS requires 37/38 and 29/32
    holdout_u_pass = [True]*37 + [False]*1  # 37/38
    holdout_a_pass = [True]*29 + [False]*3  # 29/32
    gate, _ = check_unsupported_ambiguous(holdout_u_pass, holdout_a_pass)
    assert gate == "PASS"
    # 36/38 => NO-GO
    holdout_u_fail = [True]*36 + [False]*2
    gate, _ = check_unsupported_ambiguous(holdout_u_fail, holdout_a_pass)
    assert gate == "NO-GO"
    # 28/32 => NO-GO
    holdout_a_fail = [True]*28 + [False]*4
    gate, _ = check_unsupported_ambiguous(holdout_u_pass, holdout_a_fail)
    assert gate == "NO-GO"
    # wrong denominator => HOLD
    gate, _ = check_unsupported_ambiguous([True]*10, holdout_a_pass)
    assert gate == "HOLD"
    # dev diagnostic
    dev_u = [True]*26 + [False]*1  # 26/27 pass
    dev_a = [True]*21 + [False]*2  # 21/23 pass
    gate, _ = check_unsupported_ambiguous(holdout_u_pass, holdout_a_pass, dev_u, dev_a)
    assert gate == "PASS"
    dev_u_fail = [True]*25 + [False]*2
    gate, _ = check_unsupported_ambiguous(holdout_u_pass, holdout_a_pass, dev_u_fail, dev_a)
    assert gate == "NO-GO"

def test_safety_orchestrator_reachability_without_protected_plaintext():
    # Pure API surface reachable without protected data
    # Just verify imports and that functions are callable with mock data
    snap = {"snapshot_id": "test", "sha256": "c"*64, "eligible_map": {("a","1"): {"eligible": True, "expired": False}}}
    validate_snapshot_pin(snap, "c"*64)
    uniq = dedupe_official_links([" https://gov.kr/a ", "https://gov.kr/a"])
    assert uniq == ["https://gov.kr/a"]
    # HTTP check without network
    gate, _ = evaluate_http_resolution(
        ["https://gov.kr/a"],
        {"https://gov.kr/a": ([MockHttpResponse(status=200)], [])},
        snap,
        "c"*64
    )
    assert gate == "PASS"

def test_http_head_network_error_retries_same_method_first():
    # Web repro: HEAD network-error -> HEAD 200 must succeed via same-method retry (not instant fallback).
    ok = check_single_url_with_mock(
        "https://example.com/r1",
        [MockHttpResponse(is_network_error=True), MockHttpResponse(status=200)],
        []
    )
    assert ok is True

def test_http_head_timeout_retries_same_method_first():
    # Web repro: HEAD timeout -> HEAD 200 must succeed via same-method retry.
    ok = check_single_url_with_mock(
        "https://example.com/r2",
        [MockHttpResponse(is_timeout=True), MockHttpResponse(status=200)],
        []
    )
    assert ok is True

def test_http_redirect_hop_has_own_retry_budget():
    # Web repro: HEAD 301 -> 500 -> 200 must succeed (hop 2 retries within its own budget).
    ok = check_single_url_with_mock(
        "https://example.com/r3",
        [MockHttpResponse(status=301, redirect_location="https://example.com/r3b"), MockHttpResponse(status=500), MockHttpResponse(status=200)],
        []
    )
    assert ok is True

def test_http_head_500_then_500_no_fallback_fail():
    # Other 5xx exhausts same-method budget with no GET fallback.
    ok = check_single_url_with_mock(
        "https://example.com/r4",
        [MockHttpResponse(status=500), MockHttpResponse(status=500)],
        [MockHttpResponse(status=200)]
    )
    assert ok is False

def test_http_head_timeout_only_never_falls_back():
    # Prereg wording exact: fallback triggers are 405/501/network/TLS, not timeout; timeout-only exhaustion fails.
    ok = check_single_url_with_mock(
        "https://example.com/r5",
        [MockHttpResponse(is_timeout=True), MockHttpResponse(is_timeout=True)],
        [MockHttpResponse(status=200)]
    )
    assert ok is False

def test_http_head_network_exhausted_falls_back_get():
    # Network failure honors its same-method budget first, then GET fallback under same protocol.
    ok = check_single_url_with_mock(
        "https://example.com/r6",
        [MockHttpResponse(is_network_error=True), MockHttpResponse(is_network_error=True)],
        [MockHttpResponse(status=200)]
    )
    assert ok is True

def test_http_get_own_retry_budget_after_fallback():
    # GET fallback has its own 2-attempt budget: 405 then GET 500 -> GET 200.
    ok = check_single_url_with_mock(
        "https://example.com/r7",
        [MockHttpResponse(status=405)],
        [MockHttpResponse(status=500), MockHttpResponse(status=200)]
    )
    assert ok is True

def test_http_redirect_then_head_405_falls_back_get():
    # Redirect hop preserving method, then hop failure with fallback cause, then GET success.
    ok = check_single_url_with_mock(
        "https://example.com/r8",
        [MockHttpResponse(status=301, redirect_location="https://example.com/r8b"), MockHttpResponse(status=405), MockHttpResponse(status=405)],
        [MockHttpResponse(status=200)]
    )
    assert ok is True

def test_abstention_credit_empty_only():
    # Interface-forced semantics: only actually-empty retrieval counts as safe abstention; no thresholds.
    from retrieval_v3.safety import abstention_credit
    assert abstention_credit([]) is True
    assert abstention_credit([{"source": "youth", "source_id": "p0"}]) is False
    try:
        abstention_credit(None)
        assert False, "non-list retrieved must fail closed"
    except ValueError:
        pass
    try:
        abstention_credit("youth/p0")
        assert False, "non-list retrieved must fail closed"
    except ValueError:
        pass

def test_ineligible_missing_flags_hold_never_default_pass():
    # No authoritative per-policy eligible+expired evidence => HOLD; never synthesize eligible=True.
    pin = "d" * 64
    snap = {"snapshot_id": "test", "sha256": pin}
    top5 = {"t001": [("youth", "p0")] * 5}
    gate, det = check_ineligible_expired(top5, snap, pin, 1, 5)
    assert gate == "HOLD", "empty eligible_map must HOLD (missing evidence, no eligible=True default)"
    # Entry missing expired flag => HOLD, not PASS.
    snap2 = {"snapshot_id": "test", "sha256": pin, "eligible_map": {("youth", "p0"): {"eligible": True}}}
    gate2, _ = check_ineligible_expired(top5, snap2, pin, 1, 5)
    assert gate2 == "HOLD", "entry missing expired flag must HOLD"
    # Control: complete evidence measures (all eligible, none expired) => PASS.
    snap3 = {"snapshot_id": "test", "sha256": pin, "eligible_map": {("youth", "p0"): {"eligible": True, "expired": False}}}
    gate3, det3 = check_ineligible_expired(top5, snap3, pin, 1, 5)
    assert gate3 == "PASS"
    assert det3["intrusions_task"] == 0 and det3["intrusions_slot"] == 0

def test_http_405_second_head_must_not_rescue():
    # Web repro A: HEAD 405 chooses GET fallback at once; second HEAD 200 must not rescue; GET fails => False.
    ok = check_single_url_with_mock(
        "https://example.com/a405",
        [MockHttpResponse(status=405), MockHttpResponse(status=200)],
        [MockHttpResponse(status=500), MockHttpResponse(status=500)]
    )
    assert ok is False

def test_http_501_second_head_must_not_rescue():
    # Web repro B: HEAD 501 fallback governs; second HEAD 200 must not rescue; GET fails => False.
    ok = check_single_url_with_mock(
        "https://example.com/b501",
        [MockHttpResponse(status=501), MockHttpResponse(status=200)],
        [MockHttpResponse(status=500), MockHttpResponse(status=500)]
    )
    assert ok is False

def test_http_ordinary_404_no_retry_no_fallback():
    # Web repro C: ordinary 4xx is not in the prereg retry list and has no fallback; immediate fail.
    ok = check_single_url_with_mock(
        "https://example.com/c404",
        [MockHttpResponse(status=404), MockHttpResponse(status=200)],
        []
    )
    assert ok is False
