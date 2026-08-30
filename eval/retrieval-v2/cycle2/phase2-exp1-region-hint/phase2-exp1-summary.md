# Cycle2 Phase2 Exp1 — Bounded Region-Core Lexical Hint (dev 36)

**Status:** REJECTED (quality REJECTED, latency NOT_RUN_EARLY_STOP)
**Dev:** `C:\Users\joji\Documents\취준자료\project-repos\benefit-compass\eval\retrieval-v2\cycle2\dev\evalset.jsonl` SHA `c8b66fef69bdfd0db053ac7cac0fb027fc3271c6072ab992b622cacdc71ace5e` (36 Youth18/Gov2418)
**Model:** `intfloat/multilingual-e5-base` strip_region, youth bias suppressed for Gov24, CANDIDATES 30 COSINE_MIN 0.78 LEXICAL_BIAS 0.01 RERANK 0
**Candidate-v2 reference:** `retrieval-v2-candidate-v2` `5745cc3144b519da456b21030d0e0752d1d018ae`
**New candidate:** `lexical_overlap_terms_region_hint` (base + SIDO[code][0] per matched code from raw, bounded)

## Quality (paired, shared qvec/DB/corpus/SQL)

- baseline R@1 0.5833 (21/36) R@5 0.7778 (28/36) R@10 0.8056 MRR 0.6577 macro 0.7778
- candidate-v2 R@1 0.5833 (21/36) R@5 0.8333 (30/36) R@10 0.8333 MRR 0.6884 macro 0.8333
- new R@1 0.6111 (22/36) R@5 0.8333 (30/36) R@10 0.8333 MRR 0.7069 macro 0.8333

Youth/Gov24 R@5:
- baseline Youth 10/18 Gov24 18/18
- candidate-v2 Youth 12/18 Gov24 18/18
- new Youth 12/18 Gov24 18/18

Per-category R@5 (new vs baseline vs cand_v2):
| business_agriculture | 6/6 | 1.0000 |
| culture_community | 5/6 | 0.8333 |
| employment_education | 4/6 | 0.6667 |
| family_care | 6/6 | 1.0000 |
| housing_finance | 5/6 | 0.8333 |
| welfare_health | 4/6 | 0.6667 |

Baseline vs new: net 2 gains 2 losses 0
Candidate-v2 vs new: net 0 gains 0 losses 0

Region hint stats: hinted 23/36, total_added 23, avg_per_hinted 1.000, max 1

- baseline->new gains: 2
  - c2d-025 culture_community baseline rank 0 -> new 1 (cand_v2 3) added 1 hint ['36']
  - c2d-031 business_agriculture baseline rank 7 -> new 2 (cand_v2 2) added 1 hint ['29']
- baseline->new losses: 0

- cand_v2->new gains: 0

- cand_v2->new losses: 0


Quality verdict: **REJECTED** — new R@5 30/36 not >30

## Latency

N/A vs N/A (diagnostic_only, not_final_gate, 180/variant, interleaved)
Verdict: **NOT_RUN_EARLY_STOP**

## Provenance

- git c2dfd87bf6602e78bef5ecbc09d297bfbf2a6f74 dirty True
- corpus {'total_policies': 13589, 'total_chunks': 17609, 'by_source': {'gov24': {'policies': 10958}, 'youth': {'policies': 2631}}}
- qvec shared, SQL same, rp None, region_filter None
- production diff 0 (to verify via git diff)

Overall: **REJECTED**
Generated 2026-08-30T05:21:01.104836+00:00
