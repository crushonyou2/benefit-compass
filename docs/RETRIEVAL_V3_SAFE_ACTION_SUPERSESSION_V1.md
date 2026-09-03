# Retrieval v3 safe-action supersession V1 — pre-result partial supersession (D-049 stage)

Status: DESIGN/FREEZE ONLY. No runner, safety, sparse/fusion/dedup, or production code is changed
by this document. Implementation is a later separately reviewed stage.

## 1. What is superseded (narrow)

D-044/D-048 preserved finding: V1-as-is has no executable user-visible ANSWER/ABSTAIN/CLARIFY
channel — `task_results[].retrieved` presence is the only action signal, the corpus is nonempty
(13589 policies), and every Candidate-A pipeline provably returns nonempty retrieval for every
non-blank query. Under the sole legitimate presence predicate (`abstention_credit`) dev safety is
deterministically 0/27 vs 26 and 0/23 vs 21: a pre-result structural NO-GO. D-048 history is
preserved, not rewritten; this document adds the one thing D-048 deliberately did not create.

## 2. Web HOLD corrections applied (D-049, D-048 bytes untouched)

1. The V1-as-is structural NO-GO above is KEPT as fact. FIRST dev must not run under V1 semantics.
2. D-048's over-gate is CORRECTED: the standing prereg does not require pre-dev proof that a newly
   frozen action policy will already reach dev 26/27 + 21/23 with headline >= 85%. The legitimate
   lifecycle is: define exactly ONE deterministic policy before protected access, freeze it without
   protected labels/results/result-driven tuning, review it independently, implement it, then let
   the protected dev measure PASS/FAIL. Lack of pre-dev performance proof is not a basis to discard
   Candidate A.
3. D-048's eligibility overclaim is CORRECTED: the normalized `policy` table has no
   eligible/expired columns, but Youth `raw` carries structured `plcyAprvSttsCd` (all 2631 rows
   `0044002` = 승인 per the official code table), `bizPrdSeCd`, `aplyPrdSeCd`. These were LEADS,
   not semantics. Full-corpus authoritative evidence stays HOLD until official semantics and source
   coverage are established — see `docs/RETRIEVAL_V3_ELIGIBILITY_EVIDENCE_V1.md`.

## 3. Frozen artifacts (parents immutable)

- Prereg `docs/RETRIEVAL_V3_PREREG.md` SHA256
  `7842018613d66aa4570f4db2f8ae5a698ceb46757995a6b7e26873177b36160e` — unchanged.
- `eval/retrieval-v3/candidate-plan/candidate-plan-v1.json` SHA256
  `2815361a469fee9bf69f6ffdf2124d19928220535cdb08b2005ae6674ae7d17c` — unchanged.
- NEW `eval/retrieval-v3/candidate-plan/safe-action-policy-v1.json` SHA256
  `c512fb5627179697a987b05a2431b8f7e30d1153af2ff6dca37995f6b232a35d` — the single frozen policy.
- NEW `eval/retrieval-v3/candidate-plan/candidate-plan-v2.json` SHA256
  `fa370e65d39b415800c7462ae44b4d65460e47b7e7cac36506d96e5f062f3928` — v1 values preserved
  (all 18 tuples, ranking/final-pool/selection/MAX24/D-003/embedding/B-gate/integer/latency/audit
  contracts identical; only plan_id/version/frozen_at changed and parents/safe_action_policy/
  supersession blocks added) plus the single common action-policy reference.
- NEW `eval/test_retrieval_v3_safe_action.py` — pure/static proof: v1→v2 18-tuple identity,
  single common policy, determinism, forbidden-input absence, representative fixtures.

## 4. Policy summary (normative detail lives in safe-action-policy-v1.json)

Query-only deterministic classifier, evaluated BEFORE retrieval, identical for all 18 configs:

- `N(q)` = NFC → strip → collapse whitespace → casefold (same as plan-v1 exact normalization).
- `P_U`: any of 18 narrow out-of-domain markers (외국인 관광객, 해외 유학, 비행기표, 주식 투자,
  손실 보전, 명품, 사치, 골프, 회원권, 암호화폐, 가상자산, 외제차, 게임기, 유튜브, 콘서트,
  레스토랑, 반려동물 미용, 헬스장) → ABSTAIN. Narrow compounds only — bare 유학/반려동물/
  바우처/코인 are excluded to protect legitimate policies.
- `P_C`: a generic benefit noun (13 entries: 지원금/혜택/지원/복지/대출/교육/보육/문화/의료비/
  창업/주거/이사/포인트) AND a vague request frame (11 entries) → CLARIFY.
- Precedence ABSTAIN > CLARIFY > ANSWER; blank → ABSTAIN fail-closed (unreachable on frozen dev).
- Enum: ANSWER = visible top-5; ABSTAIN/CLARIFY = no policy answer. Headline needs ANSWER +
  grade≥2; unsupported correct = ABSTAIN only; ambiguous correct = ABSTAIN or CLARIFY.
- Forbidden inputs: stratum, golds, ids, annotations, protected metadata, labels/results, any
  score/embedding/retrieval state, filename/ordering leaks. No COSINE_MIN or other score-cutoff
  reuse (D-004 stands). Design evidence is retrieval-blind pilot-100 qualitative only — frozen as
  ONE variant, never tuned, and fixtures prove mechanics only, never protected performance.

## 5. Explicit non-goals of this stage

No `runner.py`/`safety.py`/sparse/fusion/dedup/production edit; no protected dev/holdout access;
no retrieval/embedding/DB-rank/HTTP/latency execution; no Candidate B; no eligibility map freeze
(HOLD per the evidence report); no threshold/gate/MAX24 change.
