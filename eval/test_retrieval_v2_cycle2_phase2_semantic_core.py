"""Static/unit tests for semantic-core embedding (cycle2 Phase2 Exp3).

Fail-closed contract verification, no holdout/dev plaintext access, no DB/model/embedding run.

HARD INVARIANTS (4 required + production parity):
(1) lexical terms == candidate-v2 lexical_overlap_terms_rewrite(strip_region(raw))
(2) embedding input == " ".join(terms) when terms non-empty
(3) empty fallback == strip_region(raw) when terms == []
(4) no region hint / hardcode / new dictionary / extra encode / extra retrieval

Plus: youth_source_bias parity, production parity constants unchanged,
      no SIDO/region tables introduced.
"""

import pathlib
import sys
import inspect
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "ml-service"))
sys.path.insert(0, str(ROOT / "eval"))

import app as ml_app
from retrieval_v2.candidate_lexical_rewrite import lexical_overlap_terms_rewrite
from retrieval_v2.candidate_semantic_core import (
    lexical_terms_for_candidate,
    semantic_core_embedding_query,
)
from source_ranking import youth_source_bias


class SemanticCoreInvariantsTest(unittest.TestCase):
    # Synthetic raws covering region, youth intent, boilerplate, empty-case
    RAWS = [
        "부산에 사는 청년이 월세 지원을 받을 수 있나요?",
        "서울에서 청년이 창업 지원을 받을 수 있을까요?",
        "청년이 주택 마련을 위해 청년주택드림청약통장을 가입할 수 있는 방법이 있을까요?",
        "경기도 청년이 청년참여기구를 통해 정책 제안에 참여할 수 있을까요?",
        "충남에서 청년이 정신건강 검진을 받을 수 있나요?",
        "세종시에서 청년이 청년센터를 이용할 수 있나요?",
        "강원도 삼척시에서 청년 인턴",
        "알려주세요",
        "도움받을",
        "있는 수 있는",
        "청년 지원",
        "월세 지원 방법 알려주세요",
    ]

    def test_01_lexical_terms_identical_to_candidate_v2(self):
        """(1) lexical == candidate-v2 rewrite on stripped."""
        for raw in self.RAWS:
            stripped = ml_app.strip_region(raw)
            base = lexical_overlap_terms_rewrite(stripped)
            cand = lexical_terms_for_candidate(raw)
            self.assertEqual(
                cand,
                base,
                f"lexical must be identical to candidate-v2 for raw={raw!r} stripped={stripped!r}",
            )
            # also verify order/ dedup preserved via direct rewrite
            self.assertEqual(cand, lexical_overlap_terms_rewrite(stripped))

    def test_02_embedding_input_exactly_rewrite_terms_join(self):
        """(2) embedding == ' '.join(terms) when terms non-empty."""
        for raw in self.RAWS:
            stripped = ml_app.strip_region(raw)
            terms = lexical_overlap_terms_rewrite(stripped)
            emb = semantic_core_embedding_query(raw)
            if terms:
                expected = " ".join(terms)
                self.assertEqual(
                    emb,
                    expected,
                    f"embedding must be join(terms) for raw={raw!r} terms={terms}",
                )
                # must be exactly join, not stripped, when terms present
                # for raws with boilerplate stripped away, join != stripped
                # we don't assert inequality universally, but spot-check one:
            else:
                # covered by next test
                pass
        # spot-check: boilerplate-heavy query should dilute vs core
        raw = "부산에 사는 청년이 월세 지원을 받을 수 있나요?"
        stripped = ml_app.strip_region(raw)
        terms = lexical_overlap_terms_rewrite(stripped)
        emb = semantic_core_embedding_query(raw)
        self.assertEqual(emb, " ".join(terms))
        self.assertNotEqual(emb, stripped, "semantic core should differ from stripped when terms non-empty (shows dilution removal)")

    def test_03_empty_fallback_is_strip_region(self):
        """(3) when terms == [] fallback must be strip_region(raw) exactly."""
        # Find raws that produce empty terms
        empties = [r for r in self.RAWS if not lexical_overlap_terms_rewrite(ml_app.strip_region(r))]
        self.assertGreater(len(empties), 0, "need at least one empty-terms case in RAWS")
        for raw in empties:
            stripped = ml_app.strip_region(raw)
            terms = lexical_overlap_terms_rewrite(stripped)
            self.assertEqual(terms, [])
            emb = semantic_core_embedding_query(raw)
            self.assertEqual(
                emb,
                stripped,
                f"empty fallback must be stripped for raw={raw!r}",
            )
            self.assertEqual(emb, ml_app.strip_region(raw))
        # explicit fallback cases
        self.assertEqual(semantic_core_embedding_query("알려주세요"), ml_app.strip_region("알려주세요"))
        self.assertEqual(semantic_core_embedding_query(""), ml_app.strip_region(""))
        self.assertEqual(semantic_core_embedding_query("있나요"), ml_app.strip_region("있나요"))
        # verify fallback preserves original when stripped is used (not empty string join)
        raw = "서울에서 알려주세요"
        stripped = ml_app.strip_region(raw)
        self.assertEqual(lexical_overlap_terms_rewrite(stripped), [])
        self.assertEqual(semantic_core_embedding_query(raw), stripped)

    def test_04_no_region_hint_hardcode_new_dict(self):
        """(4) no region hint, hardcode, new dictionary, lower-level logic."""
        src_lex = inspect.getsource(lexical_terms_for_candidate)
        src_emb = inspect.getsource(semantic_core_embedding_query)
        # module logic body only (exclude top-level docstring that explains prohibitions)
        # Extract code bodies after the initial module docstring for file-level checks
        full_src = pathlib.Path(ROOT / "eval" / "retrieval_v2" / "candidate_semantic_core.py").read_text(encoding="utf-8")
        # Split off first docstring block to avoid keyword hits inside documentation
        # We check the executable part: everything after the closing """ of the first block
        parts = full_src.split('"""')
        logic_src = '"""'.join(parts[2:]) if len(parts) >= 3 else full_src

        # No SIDO / region table usage at all (Exp3 is region-agnostic) — check logic only
        for src, name in [(src_lex, "lexical"), (src_emb, "embedding"), (logic_src, "module_logic")]:
            self.assertNotIn("SIDO", src, f"{name} must not reference SIDO")
            self.assertNotIn("region_hint", src, f"{name} must not contain region_hint")
            self.assertNotIn("region_codes", src)
            self.assertNotIn("region_filter", src)
            # no new dict for regions
            # ensure no dict literal with known sido aliases as keys
            self.assertNotIn('"11"', src, f"{name} should not define region code dict")
            self.assertNotIn("'11'", src)

        # No per-case hardcode (c2d-*) in logic
        self.assertNotIn("c2d-", logic_src)
        # Also check function bodies
        self.assertNotIn("c2d-", src_lex + src_emb)

        # No extra model encode / DB retrieval in this pure module logic
        for forbidden in ["psycopg2", "SQL", "cur.execute", "DATABASE_URL", "dual", "blend", "vector_only"]:
            self.assertNotIn(forbidden, logic_src, f"module logic must not contain {forbidden}")
        # encode check: logic must not call encode (runner does single encode)
        self.assertNotIn("encode(", logic_src, "pure transform must not encode; runner does single encode")

        # No lower-level region dictionary — logic must not define ADMIN_UNITS etc
        self.assertNotIn("ADMIN_UNITS", logic_src)
        self.assertNotIn("candidate_region_hint", logic_src)
        self.assertNotIn("candidate_embedding_region_hint", logic_src)

        # Must only call strip_region and lexical_overlap_terms_rewrite
        self.assertIn("ml_app.strip_region", src_emb)
        self.assertIn("lexical_overlap_terms_rewrite", src_emb)
        self.assertIn("ml_app.strip_region", src_lex)
        self.assertIn("lexical_overlap_terms_rewrite", src_lex)

        # No hardcode list of region names in code logic
        for alias in ["서울", "부산", "경기", "충남"]:
            self.assertNotIn(f'"{alias}"', src_emb, f"embedding logic should not hardcode {alias}")
            self.assertNotIn(f"'{alias}'", src_emb)

        self.assertNotIn("candidate_embedding_region_hint", logic_src)
    def test_05_youth_source_bias_parity(self):
        """youth_source_bias must remain on stripped query, not on embedding core."""
        for raw in self.RAWS:
            stripped = ml_app.strip_region(raw)
            bias_stripped = youth_source_bias(stripped)
            # still, stripped bias should be deterministic
            self.assertIsInstance(bias_stripped, float)
        # Exp3 module must not compute bias itself — parity is caller's job; check logic only
        src_lex = inspect.getsource(lexical_terms_for_candidate)
        src_emb = inspect.getsource(semantic_core_embedding_query)
        self.assertNotIn("youth_source_bias", src_lex, "lexical logic must not compute youth bias")
        self.assertNotIn("youth_source_bias", src_emb, "embedding logic must not compute youth bias; caller uses stripped parity")

    def test_06_production_parity_constants_unchanged(self):
        """Production invariants remain frozen; module does not alter them."""
        self.assertEqual(ml_app.CANDIDATES, 30)
        self.assertEqual(ml_app.COSINE_MIN, 0.78)
        from source_ranking import LEXICAL_OVERLAP_BIAS
        self.assertEqual(LEXICAL_OVERLAP_BIAS, 0.01)
        # SQL must still contain expected placeholders (caller will use production SQL)
        self.assertIn("%(vec)s", ml_app.SQL)
        self.assertIn("%(lexical_terms)s", ml_app.SQL)
        self.assertIn("%(youth_bias)s", ml_app.SQL)
        self.assertIn("%(rp)s", ml_app.SQL)
        # region_filter(None) must be no-op
        dummy = [{"org": "서울시청"}, {"org": "부산시청"}]
        self.assertEqual(ml_app.region_filter(dummy, None), dummy)
        self.assertEqual(ml_app.region_filter(dummy, ""), dummy)

    def test_07_single_encode_single_retrieval_contract(self):
        """Each variant must be realizable with 1 encode + 1 retrieval; no dual-vector/blend in module."""
        src_emb = inspect.getsource(semantic_core_embedding_query)
        src_lex = inspect.getsource(lexical_terms_for_candidate)
        full_src = pathlib.Path(ROOT / "eval" / "retrieval_v2" / "candidate_semantic_core.py").read_text(encoding="utf-8")
        parts = full_src.split('"""')
        logic_src = '"""'.join(parts[2:]) if len(parts) >= 3 else full_src
        # Module is pure string transform, so encode count is 0 here; runner will do exactly 1
        self.assertEqual(logic_src.count("encode"), 0, "pure transform must not encode; runner does single encode")
        # No dual/blend markers in logic
        for kw in ["dual", "blend", "vector_only"]:
            self.assertNotIn(kw, src_emb.lower(), f"no {kw} in embedding logic")
            self.assertNotIn(kw, src_lex.lower(), f"no {kw} in lexical logic")
            self.assertNotIn(kw, logic_src.lower(), f"no {kw} in module logic")
    def test_08_lexical_and_embedding_consistency(self):
        """Terms and embedding must be consistent: join(terms) == embedding when non-empty."""
        for raw in self.RAWS:
            terms = lexical_terms_for_candidate(raw)
            emb = semantic_core_embedding_query(raw)
            stripped = ml_app.strip_region(raw)
            if terms:
                self.assertEqual(emb, " ".join(terms))
                # lexical terms must be deduplicated order-preserved (via rewrite)
                self.assertEqual(terms, list(dict.fromkeys(terms)))
            else:
                self.assertEqual(emb, stripped)
        # Extra: stripped empty edge (raw empty)
        self.assertEqual(semantic_core_embedding_query(""), "")
        self.assertEqual(lexical_terms_for_candidate(""), [])


if __name__ == "__main__":
    unittest.main()
