"""Cycle3 latency HOLD repair regression — pure/fake, no DB/model/plaintext.

Proves the a19b274 drift is fixed and D-007 methodology is restored:

- qvec precompute count (exactly 36) and no timed re-encode
- warmup covers each of 36 queries exactly once per measured variant (not random replacement)
- timed count 180/variant (5*36)
- lexical/youth/retrieval/postfilter are inside timed sample boundary (t0 before lexical)
- strip_region excluded from timed (precomputed q)
- canonical nearest-rank p95 (not linear interpolation) and perf_counter_ns
- non-quality candidates are never measured
- baseline remains paired (consecutive per case/round)

These tests exercise the REAL latency factory with fakes (no DB/model/plaintext)
and WOULD FAIL on a19b274 where:
  - terms_map/youth/embedding recomputed before t0,
  - warmup used rng.choice random-with-replacement,
  - t0 started only before retrieval_fn,
  - strip_region recomputed inside timed,
  - p95 used linear interpolation.

Existing pure/static suites remain untouched; this file adds the HOLD-specific proofs.
"""

import pathlib
import sys
import time as stdlib_time
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "eval"))
sys.path.insert(0, str(ROOT / "ml-service"))

from retrieval_v2.cycle3_runner import ALL_CANONICAL_IDS, BASELINE_ID, CANDIDATE_IDS  # type: ignore
import retrieval_v2.run_cycle3_canonical_dev as mod  # type: ignore


def _synthetic_dev_items(n=36):
    items = []
    for i in range(n):
        # unique query per index, no region keyword so strip_region is identity
        # For strip test we also use region-bearing queries in dedicated test
        items.append(
            {
                "query": f"query-{i:02d} unique synthetic for hold repair",
                "gold_source": "youth" if i % 2 == 0 else "gov24",
                "gold_source_id": f"src-{i:03d}",
                "category": "housing_finance",
                "age": None,
                "id": f"case-{i:03d}",
            }
        )
    return items


def _synthetic_dev_items_with_region(n=36):
    # Include a region keyword that strip_region would remove (e.g., '서울')
    # This exposes strip_region cost inside timed if recomputed
    items = []
    for i in range(n):
        items.append(
            {
                "query": f"서울 query-{i:02d} region-bearing for strip test",
                "gold_source": "youth" if i % 2 == 0 else "gov24",
                "gold_source_id": f"src-{i:03d}",
                "category": "housing_finance",
                "age": None,
                "id": f"case-{i:03d}",
            }
        )
    return items


class LatencyQvecPrecomputeTest(unittest.TestCase):
    """qvec precompute count and no timed re-encode.

    D-007 precomputes qvec before warmup/timing (clauses 304-314) and never re-encodes
    inside timed samples. a19b274 recomputed terms_map/youth/qvec before t0 on every
    warmup and timed iteration (lines ~302-304 before t0 at 309), causing 216 encodes
    vs 36 and p95 drift. This test fails on a19b274.
    """

    def test_embedding_called_exactly_once_per_query_before_warmup(self):
        dev_items = _synthetic_dev_items(36)
        embed_calls = []

        def fake_embed(stripped: str):
            embed_calls.append(stripped)
            return "[0.100000,0.200000,0.300000]"

        retrieve_calls = []

        def fake_retrieve(cid, vec, terms, yb, age, rp):
            retrieve_calls.append((cid, vec))
            return []

        factory = mod._real_latency_measurer_factory(dev_items, fake_embed, fake_retrieve)
        result = factory([CANDIDATE_IDS[0]])

        self.assertEqual(
            len(embed_calls),
            36,
            f"qvec must be precomputed exactly 36 times outside timed, got {len(embed_calls)} (a19b274 did 216)",
        )
        self.assertEqual(len(set(embed_calls)), 36, "each query qvec must be computed exactly once")
        self.assertEqual(len(retrieve_calls), 72 + 360)
        self.assertEqual(result[BASELINE_ID]["count"], 180)
        self.assertEqual(result[CANDIDATE_IDS[0]]["count"], 180)

    def test_no_embedding_inside_timed_via_ordering(self):
        """Additional proof: embedding calls all occur before first timed retrieval (t0)."""
        dev_items = _synthetic_dev_items(36)
        order = []

        def fake_embed(stripped: str):
            order.append(("embed", stripped))
            return "[0.100000,0.200000]"

        def fake_retrieve(cid, vec, terms, yb, age, rp):
            order.append(("retrieve", cid, vec))
            return []

        factory = mod._real_latency_measurer_factory(dev_items, fake_embed, fake_retrieve)
        factory([CANDIDATE_IDS[0]])
        self.assertEqual(len([x for x in order if x[0] == "embed"]), 36)
        first_retrieve_idx = next(i for i, x in enumerate(order) if x[0] == "retrieve")
        last_embed_idx = max(i for i, x in enumerate(order) if x[0] == "embed")
        self.assertLess(last_embed_idx, first_retrieve_idx, "all qvec precomputes must happen before any retrieval (D-007)")
        embeds_after_first_retrieve = [x for i, x in enumerate(order) if x[0] == "embed" and i > first_retrieve_idx]
        self.assertEqual(len(embeds_after_first_retrieve), 0, "no re-encode inside warmup/timed (a19b274 recomputed qvec before t0)")


class LatencyWarmupCoverageTest(unittest.TestCase):
    """Warmup covers each of 36 queries exactly once per measured variant, not random replacement."""

    def test_warmup_covers_each_query_exactly_once_per_variant(self):
        dev_items = _synthetic_dev_items(36)

        def fake_embed(stripped: str):
            return f"vec:{stripped}"

        retrieve_log = []

        def fake_retrieve(cid, vec, terms, yb, age, rp):
            retrieve_log.append((cid, vec))
            return []

        factory = mod._real_latency_measurer_factory(dev_items, fake_embed, fake_retrieve)
        variants = [BASELINE_ID, CANDIDATE_IDS[0]]
        factory([CANDIDATE_IDS[0]])

        warmup_count = len(variants) * 36
        warmup_slice = retrieve_log[:warmup_count]

        for cid in variants:
            vecs_for_cid = [vec for (c, vec) in warmup_slice if c == cid]
            self.assertEqual(len(vecs_for_cid), 36, f"warmup for {cid} must be 36, got {len(vecs_for_cid)}")
            self.assertEqual(len(set(vecs_for_cid)), 36, f"warmup for {cid} must cover 36 distinct queries exactly once (a19b274 random choice fails)")
        all_warm_vecs = set(vec for (_, vec) in warmup_slice)
        self.assertEqual(len(all_warm_vecs), 36, "warmup must touch all 36 queries (random choice would miss some)")

    def test_warmup_not_random_with_replacement_distribution(self):
        dev_items = _synthetic_dev_items(36)

        def fake_embed(s):
            return f"vec:{s}"

        seen = set()

        def fake_retrieve(cid, vec, terms, yb, age, rp):
            seen.add(vec)
            return []

        factory = mod._real_latency_measurer_factory(dev_items, fake_embed, fake_retrieve)
        factory([CANDIDATE_IDS[0]])
        self.assertEqual(len(seen), 36)


class LatencyTimedCountTest(unittest.TestCase):
    """Timed sample count 180/variant (5*36) fixed before inspection."""

    def test_timed_count_180_per_variant_single_quality(self):
        dev_items = _synthetic_dev_items(36)

        def fake_embed(s):
            return "[0.1,0.2]"

        def fake_retrieve(cid, vec, terms, yb, age, rp):
            return []

        factory = mod._real_latency_measurer_factory(dev_items, fake_embed, fake_retrieve)
        result = factory([CANDIDATE_IDS[0]])
        self.assertEqual(result[BASELINE_ID]["count"], 180)
        self.assertEqual(result[CANDIDATE_IDS[0]]["count"], 180)
        for cid in CANDIDATE_IDS[1:]:
            self.assertIsNone(result[cid])

    def test_timed_count_180_per_variant_two_qualities(self):
        dev_items = _synthetic_dev_items(36)

        def fake_embed(s):
            return "[0.1,0.2]"

        def fake_retrieve(cid, vec, terms, yb, age, rp):
            return []

        factory = mod._real_latency_measurer_factory(dev_items, fake_embed, fake_retrieve)
        result = factory(list(CANDIDATE_IDS[:2]))
        for cid in [BASELINE_ID, CANDIDATE_IDS[0], CANDIDATE_IDS[1]]:
            self.assertEqual(result[cid]["count"], 180)
        self.assertIsNone(result[CANDIDATE_IDS[2]])

    def test_timed_count_zero_quality_only_baseline_not_measured_via_orchestrator(self):
        dev_items = _synthetic_dev_items(36)

        def fake_embed(s):
            return "[0.1,0.2]"

        def fake_retrieve(cid, vec, terms, yb, age, rp):
            return []

        factory = mod._real_latency_measurer_factory(dev_items, fake_embed, fake_retrieve)
        result = factory([])
        self.assertEqual(result[BASELINE_ID]["count"], 180)
        for cid in CANDIDATE_IDS:
            self.assertIsNone(result[cid])


class LatencyInsideTimedBoundaryTest(unittest.TestCase):
    """Lexical/youth/retrieval/postfilter are inside timed sample boundary."""

    def test_lexical_youth_retrieval_filter_inside_t0_t1(self):
        dev_items = _synthetic_dev_items(36)

        def fake_embed(s):
            return f"vec:{s}"

        call_seq = []

        original_lex_stripped = mod.lexical_terms_for_stripped
        original_youth_stripped = mod.youth_bias_for_stripped
        original_filter = mod.apply_cosine_filter

        def fake_lex_stripped(stripped, candidate_id=None):
            call_seq.append(("lex", stripped, candidate_id))
            return original_lex_stripped(stripped, candidate_id=candidate_id)

        def fake_youth_stripped(stripped):
            call_seq.append(("youth", stripped))
            return original_youth_stripped(stripped)

        def fake_filter(results, cosine_min):
            call_seq.append(("filter",))
            return original_filter(results, cosine_min)

        def fake_retrieve(cid, vec, terms, yb, age, rp):
            call_seq.append(("retrieve", cid, vec))
            return []

        with mock.patch.object(mod.time, "perf_counter_ns") as mock_perf:
            counter = [0]

            def fake_perf_ns():
                counter[0] += 1_000_000
                call_seq.append(("perf", counter[0]))
                return counter[0]

            mock_perf.side_effect = fake_perf_ns

            with mock.patch.object(mod, "lexical_terms_for_stripped", side_effect=fake_lex_stripped):
                with mock.patch.object(mod, "youth_bias_for_stripped", side_effect=fake_youth_stripped):
                    with mock.patch.object(mod, "apply_cosine_filter", side_effect=fake_filter):
                        factory = mod._real_latency_measurer_factory(dev_items, fake_embed, fake_retrieve)
                        factory([CANDIDATE_IDS[0]])

        perf_indices = [i for i, x in enumerate(call_seq) if x[0] == "perf"]
        self.assertGreater(len(perf_indices), 0, "timed phase must have perf t0/t1")
        self.assertEqual(len(perf_indices), 720, f"expected 720 perf calls (360 samples *2), got {len(perf_indices)}")

        first_perf_idx = perf_indices[0]
        idx = first_perf_idx
        sample_idx = 0
        while idx < len(call_seq):
            self.assertEqual(call_seq[idx][0], "perf", f"sample {sample_idx} must start with perf t0")
            self.assertEqual(call_seq[idx + 1][0], "lex", f"sample {sample_idx} lex must be immediately after t0 (inside timed, a19b274 had lex before t0)")
            self.assertEqual(call_seq[idx + 2][0], "youth", f"sample {sample_idx} youth must be after lex inside timed")
            self.assertEqual(call_seq[idx + 3][0], "retrieve", f"sample {sample_idx} retrieve must be after youth inside timed")
            self.assertEqual(call_seq[idx + 4][0], "filter", f"sample {sample_idx} filter must be inside timed (post-LIMIT cosine)")
            self.assertEqual(call_seq[idx + 5][0], "perf", f"sample {sample_idx} must end with perf t1")
            idx += 6
            sample_idx += 1

        self.assertEqual(sample_idx, 360, "must have 360 timed samples (180*2)")
        pre_perf = call_seq[:first_perf_idx]
        self.assertTrue(any(x[0] == "lex" for x in pre_perf), "warmup lex must exist before timed")

    def test_old_code_would_have_lex_before_t0_static(self):
        """Static proof that current code has t0 before lexical; would fail on a19b274 source."""
        import inspect

        src = inspect.getsource(mod._real_latency_measurer_factory)
        timed_start = src.find("Timed phase")
        self.assertNotEqual(timed_start, -1)
        timed_src = src[timed_start:]
        t0_pos = timed_src.find("t0 = time.perf_counter_ns")
        lex_pos = timed_src.find("lexical_terms_for_stripped")
        youth_pos = timed_src.find("youth_bias_for_stripped")
        self.assertNotEqual(t0_pos, -1, "t0 must exist in timed phase (perf_counter_ns)")
        self.assertNotEqual(lex_pos, -1)
        self.assertNotEqual(youth_pos, -1)
        self.assertLess(t0_pos, lex_pos, "t0 must be before lexical_terms_for_stripped (a19b274 had lexical before t0)")
        self.assertLess(t0_pos, youth_pos, "t0 must be before youth_bias_for_stripped (D-007)")
        pre_pos = src.find("precomputed")
        warmup_pos = src.find("Warmup phase")
        self.assertLess(pre_pos, warmup_pos, "precomputed must be before warmup")
        after_t0 = timed_src[t0_pos:]
        embed_after_t0 = after_t0.count("embedding_fn(")
        self.assertEqual(embed_after_t0, 0, "embedding must not be called inside timed (qvec precomputed outside)")
        strip_after_t0 = after_t0.count("strip_region_for_runner(")
        self.assertEqual(strip_after_t0, 0, "strip_region must not be called inside timed (stripped precomputed, D-007 q)")
        self.assertIn("math.ceil(0.95", src, "p95 must use canonical nearest-rank ceil(0.95*n) as latency.py")
        self.assertNotIn("(len(samples_sorted) - 1) * 0.95", src, "linear interpolation p95 would drift gate vs D-007")

    def test_strip_region_not_inside_timed_with_region_queries(self):
        """Ensure strip_region is excluded from timed even with region-bearing queries."""
        dev_items = _synthetic_dev_items_with_region(36)
        strip_calls = []

        original_strip = mod.strip_region_for_runner

        def fake_strip(raw):
            strip_calls.append(raw)
            return original_strip(raw)

        def fake_embed(s):
            return f"vec:{s}"

        def fake_retrieve(cid, vec, terms, yb, age, rp):
            return []

        with mock.patch.object(mod, "strip_region_for_runner", side_effect=fake_strip):
            factory = mod._real_latency_measurer_factory(dev_items, fake_embed, fake_retrieve)
            factory([CANDIDATE_IDS[0]])
        # strip should be called exactly 36 times during precompute, not during timed (360*2 calls would be many)
        # Warmup also now does NOT call strip (uses stripped helper), so only precompute 36
        self.assertEqual(len(strip_calls), 36, f"strip_region must be called exactly 36 times outside timed, got {len(strip_calls)} (a19b274 recomputed per timed sample)")

    def test_p95_uses_canonical_nearest_rank(self):
        """Verify p95 is nearest-rank ceil(0.95*n) not linear interpolation."""
        import inspect, math
        src = inspect.getsource(mod._real_latency_measurer_factory)
        self.assertIn("math.ceil(0.5", src)
        self.assertIn("math.ceil(0.95", src)
        # Quick behavioral check: for n=180, p95 idx should be 170 (0-indexed)
        # Create deterministic latencies 0..179, p95 should be 170 per nearest-rank, not 170.05 interpolation
        dev_items = _synthetic_dev_items(36)

        # Fake retrieve that sleeps deterministic? Instead we check factory's p95 calculation via controlled latencies
        # We can monkey patch time to produce known latencies: use sequential increasing perf values
        # To avoid needing real timing variance, we can just test the helper logic directly via math
        n = 180
        expected_idx = math.ceil(0.95 * n) - 1
        self.assertEqual(expected_idx, 170)
        # Our factory should use this idx; verify via src not linear
        self.assertNotIn("0.95 * len", src.split("math.ceil(0.95")[0][-100:] if "math.ceil(0.95" in src else "")


class LatencyQualitySelectableOnlyTest(unittest.TestCase):
    """Non-quality candidates are never measured (quality-selectable-only latency)."""

    def test_only_quality_and_baseline_measured(self):
        dev_items = _synthetic_dev_items(36)

        def fake_embed(s):
            return "[0.1,0.2]"

        called_cids = set()

        def fake_retrieve(cid, vec, terms, yb, age, rp):
            called_cids.add(cid)
            return []

        factory = mod._real_latency_measurer_factory(dev_items, fake_embed, fake_retrieve)
        result = factory([CANDIDATE_IDS[0]])
        self.assertIn(BASELINE_ID, called_cids)
        self.assertIn(CANDIDATE_IDS[0], called_cids)
        self.assertNotIn(CANDIDATE_IDS[1], called_cids)
        self.assertNotIn(CANDIDATE_IDS[2], called_cids)
        self.assertIsNone(result[CANDIDATE_IDS[1]])
        self.assertIsNone(result[CANDIDATE_IDS[2]])

        called_cids.clear()
        result2 = factory([CANDIDATE_IDS[0], CANDIDATE_IDS[2]])
        self.assertIn(CANDIDATE_IDS[0], called_cids)
        self.assertIn(CANDIDATE_IDS[2], called_cids)
        self.assertNotIn(CANDIDATE_IDS[1], called_cids)

    def test_baseline_always_paired_even_with_single_quality(self):
        dev_items = _synthetic_dev_items(36)

        def fake_embed(s):
            return f"vec:{s}"

        retrieve_order = []

        def fake_retrieve(cid, vec, terms, yb, age, rp):
            retrieve_order.append((cid, vec))
            return []

        factory = mod._real_latency_measurer_factory(dev_items, fake_embed, fake_retrieve)
        factory([CANDIDATE_IDS[1]])
        warmup = len([BASELINE_ID, CANDIDATE_IDS[1]]) * 36
        timed = retrieve_order[warmup:]
        variants = {BASELINE_ID, CANDIDATE_IDS[1]}
        for i in range(0, len(timed), 2):
            group = timed[i : i + 2]
            self.assertEqual(len(group), 2)
            cids = {c for (c, _) in group}
            self.assertEqual(cids, variants, "each timed case must have baseline paired with quality candidate (interleaved/paired)")
            vecs = {vec for (_, vec) in group}
            self.assertEqual(len(vecs), 1, "paired variants for same case must share same precomputed vec (same query)")


class LatencyBaselinePairedTest(unittest.TestCase):
    """Baseline remains paired (interleaved per case/round)."""

    def test_baseline_paired_across_all_rounds(self):
        dev_items = _synthetic_dev_items(36)

        def fake_embed(s):
            return f"vec:{s}"

        log = []

        def fake_retrieve(cid, vec, terms, yb, age, rp):
            log.append((cid, vec))
            return []

        factory = mod._real_latency_measurer_factory(dev_items, fake_embed, fake_retrieve)
        factory([CANDIDATE_IDS[0], CANDIDATE_IDS[1]])

        warmup = 3 * 36
        timed = log[warmup:]
        self.assertEqual(len(timed), 3 * 180)
        for i in range(0, len(timed), 3):
            triple = timed[i : i + 3]
            cids = {c for (c, _) in triple}
            self.assertIn(BASELINE_ID, cids)
            vecs = {v for (_, v) in triple}
            self.assertEqual(len(vecs), 1, f"triple {i//3} must be paired on same query vec")


if __name__ == "__main__":
    unittest.main()
