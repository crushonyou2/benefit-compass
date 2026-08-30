# Cycle2 Phase2 Exp3 — Semantic-Core Embedding (dev 36)

**Status:** REJECTED (quality REJECTED, latency NOT_RUN_EARLY_STOP)
**Dev:** `C:\Users\joji\Documents\취준자료\project-repos\benefit-compass\eval\retrieval-v2\cycle2\dev\evalset.jsonl` SHA `c8b66fef69bdfd0db053ac7cac0fb027fc3271c6072ab992b622cacdc71ace5e` (36 Youth18/Gov24 18)
**Model:** `intfloat/multilingual-e5-base` strip_region, youth bias on stripped, CANDIDATES 30 COSINE_MIN 0.78 LEXICAL_BIAS 0.01 RERANK 0
**Candidate-v2 reference:** `retrieval-v2-candidate-v2` `5745cc3144b519da456b21030d0e0752d1d018ae`
**New candidate (Exp3 semantic-core):** `" ".join(lexical_overlap_terms_rewrite(strip_region(raw)))` or fallback `strip_region(raw)` if empty; lexical identical to candidate-v2

## Quality (paired, shared DB/corpus/SQL, 1 encode + 1 retrieval per variant)

- baseline R@1 0.5833 (21/36) R@5 0.7778 (28/36) R@10 0.8056 MRR@10 0.6577 macro 0.7778
- candidate-v2 R@1 0.5833 (21/36) R@5 0.8333 (30/36) R@10 0.8333 MRR@10 0.6884 macro 0.8333
- new R@1 0.6389 (23/36) R@5 0.8333 (30/36) R@10 0.8333 MRR@10 0.7116 macro 0.8333

Youth/Gov24 R@5: baseline Youth 10/18 Gov24 18/18
candidate-v2 Youth 12/18 Gov24 18/18
new Youth 12/18 Gov24 18/18

Baseline vs new: net 2 gains 2 losses 0
Candidate-v2 vs new: net 0 gains 0 losses 0
  gains vs baseline: ['c2d-025', 'c2d-031']

Quality verdict: **REJECTED** — new 30/36 vs candidate 30 vs baseline 28, gov24 new 18/18, losses_c 0, pass_requires new>=31 && gov24==18 && loss0
Requires new>=31 && Gov24==18 && loss0 vs candidate: new 30 >=31? False, Gov24 18==18? True, loss0? True

## Latency (symmetric, diagnostic_only/not_final_gate)

N/A vs N/A (diagnostic_only, not_final_gate, 180/variant, interleaved, warm model) — quality REJECTED so latency not run
Verdict: **NOT_RUN_EARLY_STOP**

## Provenance

- git 44ce287d615a6131be2a2e1fd2f44d48287e0645 dirty True
- corpus {'total_policies': 13589, 'total_chunks': 17609, 'by_source': {'gov24': 10958, 'youth': 2631}}
- qvec: baseline/candidate shared stripped; new semantic-core distinct (join rewrite terms or fallback stripped)
- lexical: baseline lexical_overlap_terms(stripped), candidate/new lexical_overlap_terms_rewrite(stripped) identical
- SQL same, youth_bias on stripped, lexical bias 0.01, region_filter None, rp None
- per-case: query_stripped, semantic_core_terms, embedding_query_new, rank/rank_top30/hit@1/5/10/score/lexical_terms for each variant
- production diff 0 (to verify via git diff)

Overall: **REJECTED**
Generated 2026-08-30T07:36:11.502404+00:00