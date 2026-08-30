# Cycle2 Phase2 Exp4 — Region-Attached Residue Cleanup Embedding (dev 36)

**Status:** REJECTED (quality REJECTED, latency NOT_RUN_EARLY_STOP)
**Dev:** `C:\Users\joji\Documents\취준자료\project-repos\benefit-compass\eval\retrieval-v2\cycle2\dev\evalset.jsonl` SHA `c8b66fef69bdfd0db053ac7cac0fb027fc3271c6072ab992b622cacdc71ace5e` (36 Youth18/Gov24 18)
**Model:** `intfloat/multilingual-e5-base` strip_region, youth bias on stripped, CANDIDATES 30 COSINE_MIN 0.78 LEXICAL_BIAS 0.01 RERANK 0
**Candidate-v2 reference:** `retrieval-v2-candidate-v2` `5745cc3144b519da456b21030d0e0752d1d018ae`
**New candidate (Exp4 region-attached cleanup):** `cleanup_embedding_query(raw)` = alias+optional suffix(max1 longest)+optional particle(max1 longest) directly attached cleanup with fallback `strip_region(raw)`; lexical identical to candidate-v2

## Quality (paired, shared DB/corpus/SQL, 1 encode + 1 retrieval per variant)

- baseline R@1 0.5833 (21/36) R@5 0.7778 (28/36) R@10 0.8056 MRR@10 0.6577 macro 0.7778
- candidate-v2 R@1 0.5833 (21/36) R@5 0.8333 (30/36) R@10 0.8333 MRR@10 0.6884 macro 0.8333
- new R@1 0.5833 (21/36) R@5 0.8333 (30/36) R@10 0.8333 MRR@10 0.6884 macro 0.8333

Youth/Gov24 R@5: baseline Youth 10/18 Gov24 18/18
candidate-v2 Youth 12/18 Gov24 18/18
new Youth 12/18 Gov24 18/18

Baseline vs new: net 2 gains 2 losses 0
Candidate-v2 vs new: net 0 gains 0 losses 0
  gains vs baseline: ['c2d-025', 'c2d-031']

Quality verdict: **REJECTED** — new 30/36 vs candidate 30 vs baseline 28, gov24 new 18/18, losses_c 0, embedding_changed 8/36, cleanup_applied 23/36, pass_requires new>=31 && gov24==18 && loss0
Requires new>=31 && Gov24==18 && loss0 vs candidate: new 30 >=31? False, Gov24 18==18? True, loss0? True
Embedding changed vs candidate (q_new != q_stripped): 8/36 — actual qvec change
Cleanup applied (alias cleanup occurred, primary != raw): 23/36

## Latency (symmetric, diagnostic_only/not_final_gate)

N/A vs N/A (diagnostic_only, not_final_gate, 180/variant, interleaved, warm model) — quality REJECTED so latency not run
Verdict: **NOT_RUN_EARLY_STOP**

## Provenance

- git beb9828a69432477c0cb22b8d776fc800a90dbfe dirty True
- corpus {'total_policies': 13589, 'total_chunks': 17609, 'by_source': {'gov24': 10958, 'youth': 2631}}
- qvec: baseline and candidate separate encodes with same stripped text (no vector object sharing) — each variant 1 encode +1 retrieval, total 3 encodes +3 retrievals per query; new cleanup distinct (alias+suffix+particle directly attached cleanup or fallback stripped)
- lexical: baseline lexical_overlap_terms(stripped), candidate/new lexical_overlap_terms_rewrite(stripped) identical
- SQL same, youth_bias on stripped, lexical bias 0.01, region_filter None, rp None, n=30, exact param contract vec/age/rp/youth_bias/lexical_terms/lexical_bias/n
- per-case: query_stripped, cleanup_primary, cleanup_applied (alias cleanup), embedding_changed_vs_candidate (q_new != q_stripped), embedding_query_new, rank/rank_top30/hit@1/5/10/score/lexical_terms for each variant
- production diff 0 (to verify via git diff)
- grammar: suffix 특별자치도,특별자치시,특별시,광역시,자치도,도,시 (longest-first, max 1); particle 으로부터,에게서,에서,으로,에게,한테,부터,까지,은,는,이,가,을,를,의,에,와,과,로,도,만,께 (longest-first, max 1)

Overall: **REJECTED**
Generated 2026-08-30T08:13:35.645803+00:00