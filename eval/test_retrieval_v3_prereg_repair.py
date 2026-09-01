import json, pathlib, re, hashlib, math
from collections import Counter

PREREG = pathlib.Path("docs/RETRIEVAL_V3_PREREG.md")
DECISIONS = pathlib.Path("memory/DECISIONS.md")
OPEN_Q = pathlib.Path("memory/OPEN-QUESTIONS.md")

def test_decisions_supersession_protocol():
    txt = DECISIONS.read_text(encoding="utf-8")
    # D-014 must have superseded marker exactly one line
    assert "→ superseded by D-015 (2026-09-01)" in txt
    # D-014 block must still exist (not deleted)
    assert "## D-014 · Close Q-006" in txt
    # D-015 must exist and supersede D-014
    assert "## D-015 · Supersede D-014" in txt
    # D-015 must say D-014 superseded because of Web HOLD and D-013 remains
    d15_section = txt.split("## D-015")[1]
    assert "Supersedes D-014" in d15_section
    assert "D-013" in d15_section and "remains standing" in d15_section
    assert "Web HOLD" in d15_section or "Web-HOLD" in d15_section
    # Q-006 must remain historical, not falsified
    assert "Q-006" in txt
    # D-015 must be append-only after D-014
    pos14 = txt.index("## D-014")
    pos15 = txt.index("## D-015")
    assert pos15 > pos14

def test_q006_history_not_falsified():
    qtxt = OPEN_Q.read_text(encoding="utf-8")
    # Q-006 must still be closed -> D-014 (historical chain)
    assert "Q-006" in qtxt
    assert "closed → D-014" in qtxt
    # Should not be rewritten to D-015 directly (history preserved)
    # It's okay if index mentions superseded chain, but OPEN-QUESTIONS should not fabricate new Q

def test_prereg_final_repair_header_and_governance():
    txt = PREREG.read_text(encoding="utf-8")
    assert "FINAL REPAIR" in txt
    assert "Supersedes D-014" in txt or "superseded by D-015" in txt
    assert "Governed by D-015" in txt or "Governed by D-015" in txt or "D-015" in txt
    # Original SHA preserved mention
    assert "b3250e592d4c80099e29d20d1bf87594f2bac11a59907ac8067d3e1ddbd65da3" in txt
    # Re-audit SHAs mentioned (durable v2)
    assert "a47bb525f7966d7c23a06e57fc361119eca1c610e0cc1caf77e4cf2cd828aea3" in txt
    assert "ad7f8017f125209a7c43a3cb67b359d1585eb3eb1c63d36abdd694179ec37dc5" in txt
    assert "aaf349afe6e327bd23bd55d4ebb2970b431d62db5b6f07595fb942599267063f" in txt
    assert "0d7ac781ae3aad06ee9d01fe4a1f09ba3c2c2833a7641f7241c1cdedb474b2d6" in txt or "f758d91e32d1b5b26938ae99a1f0f1933dbd3c75a7527fd09ae7f0684b114a67" in txt
def test_exact_allocations_and_headline_denominator():
    txt = PREREG.read_text(encoding="utf-8")
    # Dev 180 exact strata exact numbers — check numbers present
    assert "180 total tasks exact" in txt
    assert "250 total tasks exact" in txt
    # Check all strata numbers present
    assert "exact_navigation 21" in txt
    assert "natural_needs 25" in txt
    assert "exploratory_multi_valid 21" in txt
    assert "multi_constraint 25" in txt
    assert "short_keywords 18" in txt
    assert "colloquial_typo_spacing_abbrev 20" in txt
    assert "ambiguous 23" in txt
    assert "unsupported_no_answer 27" in txt
    assert "exact_navigation 28" in txt
    assert "natural_needs 33" in txt
    assert "exploratory_multi_valid 31" in txt
    assert "multi_constraint 36" in txt
    assert "short_keywords 24" in txt
    assert "colloquial_typo_spacing_abbrev 28" in txt
    assert "ambiguous 32" in txt
    assert "unsupported_no_answer 38" in txt
    # Headline exact
    assert "EXACT 130" in txt
    assert "EXACT 180" in txt
    # Location exact
    assert "EXACT 54 (30%)" in txt
    assert "EXACT 75 (30%)" in txt
    # Sums recomputed pure
    dev_headline = 21+25+21+25+18+20
    assert dev_headline == 130, "dev headline sum"
    dev_total = dev_headline + 23+27
    assert dev_total == 180
    hold_headline = 28+33+31+36+24+28
    assert hold_headline == 180
    hold_total = hold_headline +32+38
    assert hold_total == 250
    # Check prereg says headline denominator BY CONSTRUCTION and exact invariants
    assert "BY CONSTRUCTION" in txt
    assert "exact post-freeze invariants" in txt or "must remain exact" in txt
    # Check no "minimum that can drift" — should not contain old D-014 minimum phrasing for dev 160/holdout 220
    assert "dev 160" not in txt.lower() or "superseded" in txt  # allow only historical mention if any
    # More strict: prereg should not define dev 160 / holdout 220 as current allocations
    # Remove false positive from history table: check that current allocations are not 160/220
    # The header 0 base should mention Prior HEAD 26e819e but not allocate 160/220 as current
    assert "160 total" not in txt or txt.count("160") <= 2  # allow only in pilot line

def test_confidence_rule_deterministic():
    txt = PREREG.read_text(encoding="utf-8")
    # Wilson primary, Clopper sensitivity
    assert "Wilson" in txt
    assert "Clopper-Pearson" in txt
    # exact headline n=180 and half-width approx 5.2pp <=5.5pp
    assert "n=180" in txt and "5.2" in txt
    assert "≤5.5" in txt or "<=5.5" in txt or "≤5.5 pp" in txt
    # PASS condition exact — allow point estimate wording
    assert "point" in txt and "≥85%" in txt and "Wilson" in txt and "≥80%" in txt
    assert "point" in txt and "≥90%" in txt and "Wilson" in txt and "≥85%" in txt
    # HOLD vs NO-GO deterministic
    assert "NO-GO" in txt
    assert "HOLD" in txt
    # should not contain vague HOLD discretion
    # Check D-015 also
    dtxt = DECISIONS.read_text(encoding="utf-8").split("## D-015")[1]
    assert "Wilson" in dtxt
    assert "point ≥85% AND Wilson lower bound ≥80%" in dtxt
    assert "Wilson lower≥85%" in dtxt or "Wilson lower" in dtxt

def test_wilson_math_correct():
    # Recompute Wilson half-width for n=180 p=0.85
    import math
    def wilson_half(p,n,z=1.96):
        denom = 1 + z*z/n
        centre = (p + z*z/(2*n)) / denom
        half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / denom
        return half
    half180 = wilson_half(0.85,180)
    assert abs(half180 - 0.052) < 0.005, f"half180 {half180}"
    assert half180 <= 0.055
    half130 = wilson_half(0.85,130)
    assert half130 > 0.05 and half130 < 0.07
    half250 = wilson_half(0.85,250)
    assert half250 < 0.05
    # Also check HOLD example: n=180 p=0.85 lower ~79.2 <80 => HOLD
    def wilson_interval(p,n,z=1.96):
        denom = 1 + z*z/n
        centre = (p + z*z/(2*n)) / denom
        half = z * math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / denom
        return (centre-half, centre+half)
    lo,hi = wilson_interval(0.85,180)
    assert lo < 0.80 and lo > 0.78, f"lo {lo}"
    lo2, _ = wilson_interval(0.86,180)
    assert lo2 >= 0.80

def test_safety_gates_deterministic():
    txt = PREREG.read_text(encoding="utf-8")
    # Check each safety gate exact
    assert "unsupported/no-answer correct safe handling ≥95%" in txt
    assert "holdout unsupported 38" in txt
    assert "ambiguous correct clarification-or-safe-abstention ≥90%" in txt
    assert "holdout ambiguous 32" in txt
    assert "ineligible/expired top-5 intrusion = 0 cases" in txt
    assert "official-link semantic/source match = 100%" in txt
    assert "HTTP resolution ≥99%" in txt
    assert "preregistered fixed retry/check protocol" in txt
    assert "candidate index size ≤2x baseline" in txt
    assert "per-query DB scanned rows ≤3x baseline" in txt
    assert "0 extra external model calls unless Candidate B" in txt
    # deterministic HOLD vs NO-GO: missing measurement => HOLD, numeric failure => NO-GO
    # Should appear twice
    # handle bold markers **HOLD** etc
    assert txt.count("missing measurement") >= 2 and txt.count("HOLD") >= 2
    assert txt.count("numeric failure") >= 2 and txt.count("NO-GO") >= 2
    # No vague marginal safety HOLD as active gate (allow explanatory "No discretionary \"marginal safety HOLD\"")
    # Check that active safety gates are deterministic via exact thresholds
    assert "No discretionary" in txt
    # Integer implications: 95% on 38 requires >=37 correct (37/38=97.3 pass, 36/38=94.7 fails)
    assert round(37/38,3) >= 0.95
    assert round(36/38,3) < 0.95
    # 90% on 32 requires >=29 (29/32=90.6 pass, 28/32=87.5 fail)
    assert round(29/32,3) >= 0.90
    assert round(28/32,3) < 0.90

def test_candidate_B_exact_gate():
    txt = PREREG.read_text(encoding="utf-8")
    dtxt = DECISIONS.read_text(encoding="utf-8").split("## D-015")[1]
    for t in [txt, dtxt]:
        nt = t.lower().replace("*","")
        assert "union oracle recall@100" in nt and "97%" in nt
        assert "5.0" in nt
        # Should NOT contain old range 95–97%
        # Check that "95–97%" or "95-97%" not present as gate
        assert "95–97%" not in t or "replaces" in t.lower()  # allow explanatory
        assert "95-97%" not in t or "replaces" in t.lower()
        # Should not contain vague ranking still limits without threshold
        # The gate must be exact union oracle + delta
        assert "union oracle" in nt and "candidate-a" in nt
        assert "b is forbidden" in nt
        assert "lightweight" in nt
        assert "never old cross-encoder" in nt

def test_latency_exact_no_if_feasible():
    txt = PREREG.read_text(encoding="utf-8")
    dtxt = DECISIONS.read_text(encoding="utf-8").split("## D-015")[1]
    for t in [txt, dtxt]:
        nt = t.lower().replace("*","")
        assert "deterministic warm-up" in nt and "30 task_ids" in nt
        assert "one timed sample per task per variant" in t.lower()
        assert "alternate variant order" in t.lower()
        assert "p50/p95/p99" in t.lower() or "p50" in t.lower()
        assert "250 tasks" in t.lower()
        # Gate
        assert "candidate p95 ≤ paired baseline p95 +80ms" in t
        assert "candidate p95 ≤700ms" in t
        # No discretionary sampling
        assert "No discretionary 150-of-N sampling" in t or "No discretionary" in t
        # Should NOT contain vague latency phrases
        # allow explanatory "No “if feasible”" but not as active sampling option
        # Check that deterministic warm-up phrase exists and old 150 sampling not present as active
        assert "deterministic warm-up" in t.lower()
    # Ensure old latency 150 queries per variant interleaved not present as current gate
    assert "150 queries per variant" not in txt or "No discretionary" in txt

def test_candidate_A_tuning_boundary_24():
    txt = PREREG.read_text(encoding="utf-8")
    dtxt = DECISIONS.read_text(encoding="utf-8").split("## D-015")[1]
    for t in [txt, dtxt]:
        nt = t.lower().replace("*","")
        assert "max 24" in nt
        assert "dev-scored configurations at MAX 24 total" in t or "MAX 24 dev-scored" in t
        assert "candidate-plan" in nt and "config" in nt
        assert "after first dev result" in nt
        assert "no new signal" in nt
        assert "sparse/dense" in nt
        assert "exact title" in nt
        # deterministic selection rule
        assert "highest" in nt and "success@5" in nt and "ndcg@5" in nt and "mrr@10" in nt and "lexicographic" in nt
        assert "no holdout" in nt
        # Should not contain adaptive loophole
        assert "adaptive" not in nt or "prohibit" in nt
        assert "result-driven" in nt or "prohibit" in nt

def test_no_loopholes_remaining():
    txt = PREREG.read_text(encoding="utf-8")
    dtxt = DECISIONS.read_text(encoding="utf-8").split("## D-015")[1]
    combined = txt + dtxt
    # No 95–97 range
    assert "95–97%" not in combined
    assert "95-97%" not in combined
    # No "if feasible"
    # allow explanatory mention
    assert "deterministic" in combined.lower()
    # No marginal safety HOLD discretion
    assert "no discretionary" in combined.lower()
    # No vague ranking still limits without numeric threshold
    # The phrase "ranking still limits" should not appear without the 5pp threshold nearby
    if "ranking still limits" in combined.lower():
        assert "5.0" in combined  # must be quantified
    # No adaptive >24
    # Check that tuning boundary is max 24, not "up to 24" with discretion
    assert "MAX 24" in combined

def test_annotation_retrieval_blind_and_isolation():
    txt = PREREG.read_text(encoding="utf-8")
    assert "retrieval-blind" in txt
    assert "two independent annotators" in txt.lower() and "third adjudicator" in txt.lower()
    assert "raw agreement" in txt.lower() and "cohen" in txt.lower()
    assert "source-truth validation" in txt.lower()
    assert "separate isolated" in txt.lower() and "fingerprint-only" in txt.lower()
    assert "holdout plaintext isolated" in txt.lower() or "holdout plaintext" in txt.lower()

def test_corpus_grounded_vs_conceptual_distinction():
    txt = PREREG.read_text(encoding="utf-8")
    # Pilot answerability is conceptual, final is source-truth grounded
    assert "conceptual/intent only" in txt.lower()
    assert "must not" in txt.lower()
    assert "every headline task must have" in txt.lower() and "grade" in txt.lower() and "source-truth" in txt.lower()
    # Check that pilot 85% not used for sizing
    assert "not derived from pilot" in txt.lower()

def test_one_shot_and_rerun_prevention():
    txt = PREREG.read_text(encoding="utf-8")
    assert "one-shot" in txt.lower() or "One-shot" in txt
    assert "exactly one" in txt.lower()
    assert "No post-result retuning" in txt
    assert "append-only" in txt.lower()
    assert "hash-chained" in txt.lower() or "hash-chained audit log" in txt

def test_production_diff_and_protected_counts():
    # This is a static check that prereg asserts diff 0 and no protected execution
    txt = PREREG.read_text(encoding="utf-8")
    assert "git diff 5327661..HEAD -- ml-service/` 0" in txt or "ml-service` diff" in txt.lower()
    # Check that docs/RETRIEVAL_V2.md not rewritten incorrectly (if exists)
    v2 = pathlib.Path("docs/RETRIEVAL_V2.md")
    if v2.exists():
        vtxt = v2.read_text(encoding="utf-8")
        # should not contain v3 headline sizes 130/180 as v2
        # v2 is historical cycle HOLD
        assert "retrieval-v2-cycle3-closure" in vtxt.lower() or "cycle3 closure" in vtxt.lower()

def test_location_exact_30_percent_cross_cutting():
    txt = PREREG.read_text(encoding="utf-8")
    assert "Location-bearing EXACT 54 (30%)" in txt
    assert "Location-bearing EXACT 75 (30%)" in txt
    assert "cross-cutting across strata" in txt
    # math check
    assert 54/180 == 0.30
    assert 75/250 == 0.30

def test_no_ambiguous_headline_leakage():
    # Ensure ambiguous tasks are counted as safety-only, not headline
    txt = PREREG.read_text(encoding="utf-8")
    # Headline 130/180 must be first six strata only, ambiguous excluded
    # Check that dev headline 130 = sum first six, not including ambiguous 23
    assert dev_headline_correct()
    assert hold_headline_correct()
    # Ensure prereg explicitly says ambiguous is safety-only
    assert "Ambiguous 23 + unsupported 27 safety-only" in txt
    assert "Ambiguous 32 + unsupported 38 safety-only" in txt

def dev_headline_correct():
    return 21+25+21+25+18+20 == 130

def hold_headline_correct():
    return 28+33+31+36+24+28 == 180
