# Cycle2 Phase2 Exp2 — Embedding Region Hint (max 1 SIDO earliest, dev 36)

**Status:** REJECTED (quality REJECTED, latency NOT_RUN_EARLY_STOP)
**Dev:** `C:\Users\joji\Documents\취준자료\project-repos\benefit-compass\eval\retrieval-v2\cycle2\dev\evalset.jsonl` SHA `c8b66fef69bdfd0db053ac7cac0fb027fc3271c6072ab992b622cacdc71ace5e` (36 Youth18/Gov24 18)
**Model:** `intfloat/multilingual-e5-base` strip_region, youth bias on stripped, CANDIDATES 30 COSINE_MIN 0.78 LEXICAL_BIAS 0.01 RERANK 0
**Candidate-v2 reference:** `retrieval-v2-candidate-v2` `5745cc3144b519da456b21030d0e0752d1d018ae`
**New candidate:** `embedding_query_with_region_hint` (strip_region(raw) + at most one SIDO[code][0] from raw via earliest alias occurrence, bounded)

## Quality (paired, shared DB/corpus/SQL, new has different qvec only for embedding hint)

- baseline R@1 0.5833 (21/36) R@5 0.7778 (28/36) R@10 0.8056 MRR@10 0.6577 macro 0.7778
- candidate-v2 R@1 0.5833 (21/36) R@5 0.8333 (30/36) R@10 0.8333 MRR@10 0.6884 macro 0.8333
- new R@1 0.6944 (25/36) R@5 0.8333 (30/36) R@10 0.8333 MRR@10 0.7509 macro 0.8333

Youth/Gov24 R@5: baseline Youth 10/18 Gov24 18/18
candidate-v2 Youth 12/18 Gov24 18/18
new Youth 12/18 Gov24 18/18

Baseline vs new: net 2 gains 2 losses 0
Candidate-v2 vs new: net 0 gains 0 losses 0
  gains vs baseline: ['c2d-025', 'c2d-031']

Quality verdict: **REJECTED** — new 30 vs candidate 30 vs baseline 28, gov24 new 18/18, losses_c 0

## Latency (symmetric encode included)

N/A vs N/A (diagnostic_only, not_final_gate, 180/variant, interleaved, warm model)
Verdict: **NOT_RUN_EARLY_STOP**

## Provenance

- git 53bd190cd716cce8a81a1ff3979483098f78471d dirty True
- corpus {'total_policies': 13589, 'total_chunks': 17609, 'by_source': {'gov24': {'policies': 10958}, 'youth': {'policies': 2631}}}
- qvec: baseline/candidate-v2 shared stripped, new stripped+hint distinct when SIDO present (earliest)
- SQL same, youth_bias on stripped, lexical bias 0.01, region_filter None
- production diff 0 (to verify via git diff)

Overall: **REJECTED**
Generated 2026-08-30T07:05:53.683585+00:00