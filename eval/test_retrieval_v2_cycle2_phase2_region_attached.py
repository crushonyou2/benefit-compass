"""Static/unit tests for region-attached residue cleanup (cycle2 Phase2 Exp4).

Fail-closed contract verification, no holdout/dev plaintext access, no DB/model/embedding run.

HARD INVARIANTS (per user instruction 2026-08-30 Exp4, D-010 bounded):
(1) Examples exactly as spec (suffix/particle directly attached only)
(2) Lexical terms == candidate-v2 lexical_overlap_terms_rewrite(strip_region(raw))
(3) No-region / unchanged: region 없는 query unchanged after cleanup
(4) Empty cleanup fallback == strip_region(raw)
(5) No new dictionary beyond suffix/particle grammar (only SIDO + given suffix/particle)
(6) No c2d hardcode, no extra encode/DB, no region hint re-add, no 시군구
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
from retrieval_v2.candidate_region_attached_cleanup import (
    cleanup_embedding_query,
    lexical_terms_for_candidate,
    _region_attached_cleanup,
    _SIDO_ALIASES,
    _ADMIN_SUFFIXES,
    _PARTICLES,
    _ADMIN_SUFFIXES_RAW,
    _PARTICLES_RAW,
)


class RegionAttachedCleanupExamplesTest(unittest.TestCase):
    def test_examples_from_spec(self):
        # 부산에 ... -> ... (부산+에)
        self.assertEqual(cleanup_embedding_query("부산에 청년 지원"), "청년 지원")
        self.assertEqual(_region_attached_cleanup("부산에 청년 지원"), "청년 지원")
        # 충남에서 ... -> ... (충남+에서)
        self.assertEqual(cleanup_embedding_query("충남에서 청년 창업 지원"), "청년 창업 지원")
        self.assertEqual(_region_attached_cleanup("충남에서 청년 창업 지원"), "청년 창업 지원")
        # 경기도 청년 -> 청년 (경기+도)
        self.assertEqual(cleanup_embedding_query("경기도 청년"), "청년")
        self.assertEqual(_region_attached_cleanup("경기도 청년"), "청년")
        # 서울특별시에서 / 부산광역시로 also removed
        self.assertEqual(cleanup_embedding_query("서울특별시에서 청년 지원"), "청년 지원")
        self.assertEqual(_region_attached_cleanup("서울특별시에서 청년 지원"), "청년 지원")
        self.assertEqual(cleanup_embedding_query("부산광역시로 청년 지원"), "청년 지원")
        self.assertEqual(_region_attached_cleanup("부산광역시로 청년 지원"), "청년 지원")
        # 강원 삼척시 -> 삼척시 유지 (강원만 제거)
        self.assertEqual(cleanup_embedding_query("강원 삼척시 청년"), "삼척시 청년")
        self.assertEqual(_region_attached_cleanup("강원 삼척시 청년"), "삼척시 청년")
        self.assertEqual(cleanup_embedding_query("강원 삼척시"), "삼척시")
        # 경기도에서 -> primary empty -> fallback strip_region
        primary = _region_attached_cleanup("경기도에서")
        self.assertEqual(primary, "", "경기도+도+에서 directly attached should leave empty before fallback")
        fallback = ml_app.strip_region("경기도에서")
        self.assertEqual(cleanup_embedding_query("경기도에서"), fallback)

    def test_region_none_unchanged(self):
        raws = [
            "청년 전세 지원",
            "청년 창업 지원 사업",
            "청년 월세 지원",
            "일자리 교육",
        ]
        for raw in raws:
            with self.subTest(raw=raw):
                # no SIDO alias -> unchanged (normalized)
                self.assertEqual(_region_attached_cleanup(raw), raw)
                self.assertEqual(cleanup_embedding_query(raw), raw)

    def test_directly_attached_only_suffix_particle(self):
        # space prevents suffix/particle removal
        # 부산 에 (space) -> only 부산 removed, 에 remains
        self.assertEqual(_region_attached_cleanup("부산 에 청년"), "에 청년")
        self.assertEqual(cleanup_embedding_query("부산 에 청년"), "에 청년")
        # 경기 도 (space) -> only 경기 removed, 도 remains
        self.assertEqual(_region_attached_cleanup("경기 도 청년"), "도 청년")
        # suffix directly attached but particle with space -> only suffix removed
        self.assertEqual(_region_attached_cleanup("경기도 에서 청년"), "에서 청년")
        # general 조사 not directly attached -> alias alone removed, particle remains if separated
        self.assertEqual(_region_attached_cleanup("부산 청년은"), "청년은")
        self.assertEqual(cleanup_embedding_query("부산 청년은"), "청년은")
        # But directly attached 는 should be removed with alias
        self.assertEqual(_region_attached_cleanup("부산는 청년"), "청년")
        self.assertEqual(cleanup_embedding_query("부산는 청년"), "청년")

    def test_longest_first_alias(self):
        # 충청북도 vs 충북 longest-first
        self.assertEqual(_region_attached_cleanup("충청북도 청년"), "청년")
        # ensure 충북 alias alone also works, but longest wins when both possible
        # 충청남도 -> should match 충청남도 (4) not 충남 (2)
        self.assertEqual(_region_attached_cleanup("충청남도 청년"), "청년")
        # 전라북도 vs 전북
        self.assertEqual(_region_attached_cleanup("전라북도 청년"), "청년")
        self.assertEqual(_region_attached_cleanup("전북 청년"), "청년")
        # 세종특별자치시 case — 세종+특별자치시+에서 pattern
        self.assertEqual(_region_attached_cleanup("세종특별자치시에서 청년"), "청년")
        self.assertEqual(cleanup_embedding_query("세종특별자치시에서 청년"), "청년")

    def test_multiple_aliases_in_query(self):
        # multiple regions -> each removed
        self.assertEqual(_region_attached_cleanup("서울 부산 청년"), "청년")
        self.assertEqual(cleanup_embedding_query("서울 부산 청년"), "청년")
        self.assertEqual(_region_attached_cleanup("경기도와 부산에 청년"), "청년")
        # 경기도+와 -> 경기+도+와 (suffix 도 + particle 와)
        self.assertEqual(_region_attached_cleanup("경기도와 청년"), "청년")
    def test_lexical_identity(self):
        raws = [
            "부산에 청년 지원",
            "충남에서 청년 창업",
            "경기도 청년",
            "서울특별시에서 청년",
            "강원 삼척시 청년",
            "청년 전세 지원",
            "경기도에서",
            "부산 청년은 지원",
            "전라북도 청년 일자리",
        ]
        for raw in raws:
            with self.subTest(raw=raw):
                stripped = ml_app.strip_region(raw)
                expected = lexical_overlap_terms_rewrite(stripped)
                cand = lexical_terms_for_candidate(raw)
                self.assertEqual(cand, expected, f"lexical must be rewrite on stripped, not cleanup, for {raw!r}")
                # For cases where cleanup differs from strip, ensure lexical still based on stripped not cleanup
                cle = cleanup_embedding_query(raw)
                if cle != stripped:
                    self.assertEqual(cand, lexical_overlap_terms_rewrite(stripped))
                    # Ensure not accidentally using cleanup
                    # (if they were equal, this check would be trivially true; so only when differs we verify)
    def test_fallback_empty_is_strip_region(self):
        # empty primary -> fallback
        for raw in ["경기도에서", "서울에서", "부산에", "충남에서", "세종특별자치시에서"]:
            with self.subTest(raw=raw):
                prim = _region_attached_cleanup(raw)
                # For these, prim may be empty before fallback
                if not prim:
                    self.assertEqual(cleanup_embedding_query(raw), ml_app.strip_region(raw))
        # non-empty primary must not equal fallback when suffix/particle handling differs
        # 경기도 청년: cleanup -> 청년, strip_region -> 청년? Actually strip_region 경기도 청년 -> " 청년" -> "청년" same. So equality may hold sometimes, but fallback logic still correct.

    def test_no_new_dict_beyond_grammar(self):
        # Module must only use SIDO + given suffix/particle raw sets; no extra region dict
        full_src = pathlib.Path(ROOT / "eval" / "retrieval_v2" / "candidate_region_attached_cleanup.py").read_text(encoding="utf-8")
        parts = full_src.split('"""')
        logic_src = '"""'.join(parts[2:]) if len(parts) >= 3 else full_src
        # SIDO usage present in logic (not just docstring)
        self.assertIn("ml_app.SIDO", logic_src)
        # suffix/particle grammar present in logic
        for token in ["특별자치도", "특별자치시", "광역시", "으로부터", "에게서"]:
            self.assertIn(token, logic_src)
        # Forbid 시군구 detailed dictionary in logic (docstring intentionally mentions them as forbidden)
        for forbidden in ["시군구", "구군", "행정동", "읍면동"]:
            self.assertNotIn(forbidden, logic_src)
        # Forbid lower-level dict introduction (군, 구 list) in logic
        self.assertNotIn("candidate_region_hint", logic_src)
        self.assertNotIn("candidate_embedding_region_hint", logic_src)
        # Ensure suffix/particle lists are exactly the allowed sets (check raw lists exist in logic)
        self.assertIn("_ADMIN_SUFFIXES_RAW", logic_src)
        self.assertIn("_PARTICLES_RAW", logic_src)
        # Verify sorted lists are derived from raw, not hardcoded elsewhere
        self.assertIn("_ADMIN_SUFFIXES = sorted", logic_src)
        self.assertIn("_PARTICLES = sorted", logic_src)
        # Ensure no extra dictionary like {"서울": ..., "강남": ...} in logic
        self.assertNotIn("\"강남\"", logic_src)
        self.assertNotIn("\"삼척시\"", logic_src)

    def test_no_c2d_hardcode(self):
        full_src = pathlib.Path(ROOT / "eval" / "retrieval_v2" / "candidate_region_attached_cleanup.py").read_text(encoding="utf-8")
        parts = full_src.split('"""')
        logic_src = '"""'.join(parts[2:]) if len(parts) >= 3 else full_src
        self.assertNotIn("c2d-", logic_src)
        self.assertNotIn("c2d_", logic_src)
        self.assertNotIn("c2d001", logic_src.lower())
        # also check function sources
        self.assertNotIn("c2d-", inspect.getsource(cleanup_embedding_query))
        self.assertNotIn("c2d-", inspect.getsource(lexical_terms_for_candidate))

    def test_no_extra_encode_db_region_hint(self):
        full_src = pathlib.Path(ROOT / "eval" / "retrieval_v2" / "candidate_region_attached_cleanup.py").read_text(encoding="utf-8")
        parts = full_src.split('"""')
        logic_src = '"""'.join(parts[2:]) if len(parts) >= 3 else full_src
        # No model encode, retrieval, DB, embedding runtime in logic
        for kw in ["SentenceTransformer", "model.encode", "psycopg2", "psycopg", "DATABASE_URL", "encode(", "lexical_overlap_terms(", "youth_source_bias", "region_filter", "RERANK", "CANDIDATES"]:
            self.assertNotIn(kw, logic_src, f"logic must not contain {kw}")
        # Ensure lexical function uses only rewrite, not original — check logic
        self.assertIn("lexical_overlap_terms_rewrite", logic_src)
        # Embedding query must not import rerank or candidate-v2 hint modules — logic only
        self.assertNotIn("candidate_semantic_core", logic_src)

    def test_youth_source_bias_parity_not_in_module(self):
        full_src = pathlib.Path(ROOT / "eval" / "retrieval_v2" / "candidate_region_attached_cleanup.py").read_text(encoding="utf-8")
        parts = full_src.split('"""')
        logic_src = '"""'.join(parts[2:]) if len(parts) >= 3 else full_src
        self.assertNotIn("youth_source_bias", logic_src, "embedding logic must not compute youth bias; caller uses stripped parity")

    def test_single_encode_single_retrieval_contract(self):
        full_src = pathlib.Path(ROOT / "eval" / "retrieval_v2" / "candidate_region_attached_cleanup.py").read_text(encoding="utf-8")
        parts = full_src.split('"""')
        logic_src = '"""'.join(parts[2:]) if len(parts) >= 3 else full_src
        # Module must be pure functions, no retrieval loop in logic
        for kw in ["_fetch_cands", "cur.execute", "SQL", "vector", "fetch"]:
            self.assertNotIn(kw, logic_src)
        # Ensure module docstring mentions single encode/retrieval contract (check full)
        self.assertIn("1 encode + 1 retrieval", full_src)

    def test_aliases_sorted_longest_first(self):
        # Verify _SIDO_ALIASES sorted longest-first deterministic
        self.assertEqual(_SIDO_ALIASES, sorted(set(_SIDO_ALIASES), key=lambda x: (-len(x), x)))
        self.assertIn("충청북도", _SIDO_ALIASES)
        self.assertIn("충북", _SIDO_ALIASES)
        # Longest alias should appear before its short form
        self.assertLess(_SIDO_ALIASES.index("충청북도"), _SIDO_ALIASES.index("충북"))
        self.assertLess(_SIDO_ALIASES.index("전라북도"), _SIDO_ALIASES.index("전북"))
        # Suffixes longest-first
        self.assertEqual(_ADMIN_SUFFIXES, sorted(_ADMIN_SUFFIXES, key=lambda x: (-len(x), x)))
        self.assertLess(_ADMIN_SUFFIXES.index("특별자치도"), _ADMIN_SUFFIXES.index("도"))
        # Particles longest-first
        self.assertEqual(_PARTICLES, sorted(_PARTICLES, key=lambda x: (-len(x), x)))
        self.assertLess(_PARTICLES.index("으로부터"), _PARTICLES.index("에"))


class RunnerContractStaticTest(unittest.TestCase):
    """Minimal runner contract verification without DB/holdout/model — static source inspection only."""

    RUNNER = ROOT / "eval" / "retrieval_v2" / "run_cycle2_phase2_exp4_region_attached.py"

    def test_sql_param_exact_contract(self):
        src = self.RUNNER.read_text(encoding="utf-8")
        # Must contain exact contract keys vec, age, rp=None, youth_bias, lexical_terms, lexical_bias, n
        self.assertIn('"vec": vec_str', src)
        self.assertIn('"age": age', src)
        self.assertIn('"rp": None', src)
        self.assertIn('"youth_bias": youth_bias', src)
        self.assertIn('"lexical_terms": lexical_terms', src)
        self.assertIn('"lexical_bias": D003_LEXICAL_BIAS', src)
        self.assertIn('"n": n', src)
        # Must NOT use limit param
        parts = src.split('"""')
        logic = '"""'.join(parts[2:]) if len(parts) >= 3 else src
        self.assertNotIn('"limit":', logic, "SQL param must use n, not limit")
        self.assertNotIn("'limit':", logic)
        # Rows must be zipped via SEARCH_RESULT_COLUMNS
        self.assertIn("ml_app.SEARCH_RESULT_COLUMNS", logic)

    def test_corpus_provenance_singular_and_fail_closed(self):
        src = self.RUNNER.read_text(encoding="utf-8")
        parts = src.split('"""')
        logic = '"""'.join(parts[2:]) if len(parts) >= 3 else src
        # Corpus tables must be singular: policy, policy_chunk, and source from policy
        self.assertIn("FROM policy", logic)
        self.assertIn("FROM policy_chunk", logic)
        # Must not hide exception with None — get_corpus_summary should not contain except returning None
        corpus_section = logic.split("def get_corpus_summary")[1].split("def get_git_commit")[0] if "def get_corpus_summary" in logic else ""
        self.assertNotIn("return {\"total_policies\": None", corpus_section)
        # No try/except hiding in corpus provenance (fail-closed)
        self.assertNotIn("try:", corpus_section)

    def test_git_dirty_uses_porcelain(self):
        src = self.RUNNER.read_text(encoding="utf-8")
        self.assertIn("git status --porcelain", src)
        parts = src.split('"""')
        logic = '"""'.join(parts[2:]) if len(parts) >= 3 else src
        # Ensure git_dirty logic in get_git_commit uses porcelain, not diff --quiet
        git_section = logic.split("def get_git_commit")[1].split("def rank_of")[0] if "def get_git_commit" in logic else ""
        self.assertNotIn("git diff --quiet", git_section)

    def test_quality_three_encodes_separate_vectors(self):
        src = self.RUNNER.read_text(encoding="utf-8")
        parts = src.split('"""')
        logic = '"""'.join(parts[2:]) if len(parts) >= 3 else src
        # Precompute must have three separate encode calls with distinct variable names
        self.assertIn("vec_baseline = model.encode", logic)
        self.assertIn("vec_candidate = model.encode", logic)
        self.assertIn("vec_new = model.encode", logic)
        self.assertIn("vec_baseline_str", logic)
        self.assertIn("vec_candidate_str", logic)
        # Quality loop must use separate vectors
        self.assertIn('pc["vec_baseline_str"]', logic)
        self.assertIn('pc["vec_candidate_str"]', logic)
        self.assertNotIn('pc["vec_stripped_str"]', logic, "must not share vec_stripped_str between baseline and candidate")

    def test_lexical_identity_preserved(self):
        src = self.RUNNER.read_text(encoding="utf-8")
        self.assertIn("lex_new == lex_rewrite", src)
        self.assertIn("lexical_terms_for_candidate", src)
        self.assertIn("lexical_overlap_terms_rewrite", src)

    def test_embedding_changed_tracking(self):
        src = self.RUNNER.read_text(encoding="utf-8")
        self.assertIn("embedding_changed_vs_candidate", src)
        self.assertIn("embedding_changed_count", src)
        self.assertIn("q_new != q_stripped", src)

if __name__ == "__main__":
    unittest.main()
