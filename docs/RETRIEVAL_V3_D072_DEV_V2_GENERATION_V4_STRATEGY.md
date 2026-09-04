# Retrieval v3 D-072 dev-v2 generation-v4 strategy — D-071 postmortem + pre-result plan basis

Status: D-072 Phase A durable record. Plaintext-free. No generated query/gold plaintext on main.
Stage identity: D-072 is a NEW logical stage (user-authorized). D-071 rows are failed-generation evidence only.

## 1. D-071 outcome (first durable record; execution lived only in the private builder)

- Private builder `bc-v3-dev-v2-builder-20260904-v3` preserved byte-for-byte. Verdict `INFEASIBLE_STOP_HOLD`
  (`D071_HOLD_SUMMARY.json` SHA `c2f200e0766db666c264a981f20224a438e8e5a1930b8af41844cc21c7d0d76c`,
  determined `2026-09-04T13:21:03+00:00`). No selector seal; no protected branch/tag/worktree/run/audit/holdout contact.
- Frozen v3 bytes verified unchanged: plan `558f7df7...` (13477 B), lock `f17d8e40...`, rubric `9ceda4ee...`,
  adjudicated pool `64ece2a9...` (273 rows). Plan was never mutated after freeze (`mutated_after_freeze false`).
- Generation/annotation contract was valid: C coverage 273/273 with no A/B fallback. Infeasibility is genuine, not procedural.
- C-authoritative census vs final-180 need (stratum total / location-bearing):
  exact 49/22 (need 21/6 — surplus); natural 66/18 (need 25/7 — surplus); exploratory 33/9 (need 21/6 — surplus);
  multi 37/14 (need 25/8 — surplus); short 21/2 (need 18/5 — SHORTFALL loc);
  colloquial 16/5 (need 20/6 — SHORTFALL total+loc); ambiguous 8/1, valid 0/0 (need 23/7 — SHORTFALL total+loc, all 8 invalid);
  unsupported 43/14 (need 27/9 — surplus).
- Necessary shortfalls (exact): short loc 2<5; colloquial total 16<20 and loc 5<6; ambiguous total 8<23 and loc 1<7.
  Note ambiguous valid = 0/0 because all 8 C-ambiguous rows were marked `labelable=false` (see §3).

## 2. Corrected disagreement bookkeeping (append-only; old artifact bytes preserved)

- `disagreement_matrix.json` (`951fa3de...`): N=273, any=61, per-dimension stratum 60 / location 2 / labelable 7 /
  answerable 16 / ambiguous 7 / ambiguity_type 7, gold_set_disagreements 128. Its `61` is QUERY-DIMENSION-ONLY.
- Correct query-level six-dimension disagreement = 61/273 (unchanged meaning, relabeled explicitly).
- Correct gold semantic disagreement (identity/grade/equiv) = 224/273; ANY semantic disagreement union
  (query dims OR gold identity/grade/equiv) = 226/273; full semantic agreement = 47/273.
- Correct reading: nearly all rows needed C on substance, not just 61/273. No protected benchmark result exists;
  this is pre-result dataset-generation strategy, not candidate/result tuning.

## 3. Corrected per-gold grade kappa method (diagnostic-only, never a gate)

- Existing per-gold Cartesian x273 kappa .5049 is NOT the standing diagnostic: for a preselection pool where a gold
  identity can recur across candidate queries, Cartesian product overstates N and distorts agreement.
- Standing method (task-local gold unit): unit = `(candidate_id, source, source_id)`; union A/B within each candidate;
  ABSENT sentinel for a missing side; grade category only.
- Mechanical D-071 recomputation under this method: N=364, agree=114, raw=0.3131868131868132,
  expected=0.3722150102644608, kappa=-0.09402613640462133; A counters {3:230, ABSENT:97, 2:35, 1:2};
  B counters {ABSENT:125, 3:148, 2:90, 1:1}. Diagnostic-only. Old artifact bytes preserved; corrected only here.
- When final selected gold identities are globally unique, this method reduces to the standing D-034 identity metric.

## 4. Rubric-definition mismatch exposed by D-071 (corrected prospectively in v4, never by relabeling D-071)

- D-071 C marked all 8 C-ambiguous rows `labelable=false`. Ambiguity safety tasks CAN be evaluable/labelable even
  though not determinate enough for an immediate answer — the v3 rubric conflated ambiguity with unlabelability.
- v4 rule: `labelable=true` = coherent/interpretable enough that expected system handling can be judged.
  An intentionally ambiguous query omitting exactly one essential referent can and normally should be
  `labelable=true` (requires CLARIFY/ABSTAIN, safety-only). `labelable=false` is reserved for
  contradictory/incoherent/non-evaluable text. Ambiguity != unlabelability. No quotas/intended labels in rubric.
- Standing invariant restored explicitly: selected FINAL 180 MUST all be `labelable=true` (0-unlabelable).

## 5. Location-vector typo correction (append-only; old text untouched)

- D-071 durable shorthand in `memory/DECISIONS.md` D-071 §3 wrote the exact-dev location vector as `6/7/6/7/9`.
- Standing exact dev vector is `6/7/6/8/5/6/7/9` (sum 54). The D-071 plan doc itself (`...D071...PLAN.md:28`) has the
  correct 8-cell vector. Corrected here only; old text never edited in place.

## 6. v4 prospective corrections (frozen BEFORE source-truth content; immutable afterward)

1. Fresh builder `bc-v3-dev-v2-builder-20260904-v4` (never D-070/D-071 directories).
2. New identity: plan_version `retrieval-v3-dev-generation-v4`; seed
   `benefit-compass-retrieval-v3-dev-v2-generation-v4-2026-09-04` (truthful distinct suffix if collision, recorded).
3. Final contract EXACTLY unchanged: total 180; strata 21/25/21/25/18/20/23/27; headline first-six 130;
   safety ambiguous 23 + unsupported 27 = 50; location exact 54 at 6/7/6/8/5/6/7/9. 18 candidate configs/gates unchanged.
4. Reserve UNIFORM 2.0x per final stratum/location cell (symmetric construction capacity, NOT targeted to D-071
   shortfalls, fixed pre-truth): total slots exact 42/50/42/50/36/40/46/54 = 360;
   location slots exact 12/14/12/16/10/12/14/18 = 108. No evaluation threshold/gate change.
5. Full D-023 mutually-exclusive authoring contracts restored, with mechanical validators:
   short = exactly 2–3 meaningful tokens AND normalized exact-title equality/substring/fragment exclusion;
   colloquial = salient perturbation + private base→perturbed ledger + unperturbed-title exclusion;
   ambiguous = exactly one essential referent omitted, no exact title/broad request, location alone cannot remove
   ambiguity, PRIVATE omission ledger (omitted referent + ≥2 coherent completions), ledger never shown to A/B/C;
   unsupported = plausible coherent benefit intent + exhaustive full-snapshot negative validation, no blacklist.
6. Neutral rubric with §4 labelability fix; validity rules: headline = labelable + answerable + unambiguous +
   ≥1 grade≥2 source-truth gold; unsupported = labelable + not-answerable + zero grade≥2 gold;
   ambiguous = labelable + ambiguous=true, safety-only. No new numeric performance gate.
7. A/B each judge ALL 360 independently (opaque independently ordered `{item_id, query_text}` + rubric + source truth;
   no intended slots/ledgers/quotas/mappings/counterparts). C judges EVERY 360 exactly once; disagreement rows carry
   only frozen disagreement dimensions/values; full-agreement rows carry query only, no A/B labels. C final
   authoritative all-dimensions all-360; no A/B fallback.
8. Agreement artifact: query-level raw/kappa per standing dimensions; `any_semantic_disagreement` includes gold
   differences, with query_dim_any / gold_any / full_agreement reported separately. Per-gold grade diagnostic per §3.
9. Exact deterministic selector on C-rows only: lexicographically-smallest feasible 180 under exact strata/location,
   validity, selected-query uniqueness, selected GLOBAL gold-fingerprint uniqueness, canonical query+gold overlap 0
   vs history/dev-v1/holdout, failed D-070/D-071 query overlap 0. Global gold uniqueness required ONLY of selected
   180, not the 360 pool. Infeasible → STOP/HOLD, no supplement/relabel/plan edit.
10. Freeze `GENERATION_PLAN.json` + `RUBRIC.json` + `PLAN_LOCK.json` BEFORE source-truth content; lock carries
    `source_truth_content_read_for_this_plan=false`, `d070/d071_semantic_rows_read_for_plan=false`,
    `protected_old_plaintext_read=false`. Hash all. Never mutate after freeze.
11. Exclusions before truth: failed-query fingerprints from D-071 `candidates_merged.json` query_text ONLY
    (NFC→strip→collapse-whitespace→casefold→SHA256, sorted unique 273; no old plaintext printed/stored outside D-071
    builder; no D-071 labels/golds read for plan design) + carried D-070 failed fingerprints + canonical
    dev-v1/holdout/history fingerprint-only inputs. Required new-query overlap 0 vs D-070/D-071/dev-v1/holdout/history;
    required new-gold overlap 0 vs canonical dev-v1/holdout/history. Failed D-070/D-071 noncanonical golds are not
    exclusion gates.
12. Durable pre-result record (DECISIONS + SESSION-LOG + this doc) committed+pushed and remote-verified BEFORE
    opening source-truth. Only then Phase C: fresh read-only snapshot (no vectors/chunks, DSN never printed) →
    exactly 360 fresh queries → frozen mechanical validators → genuine A/B (360/360) → agreement → C (360/360) →
    exact selector → PRIVATE sanitized sealed outputs or HOLD evidence, then STOP. No protected import/ref/audit/run
    in any outcome.

## 7. Boundaries restated (this stage)

D-068 consumed/open untouched; holdout sealed; no launcher/grant/run_start/run_end/result/benchmark/tuning/Candidate-B;
no protected branch/tag/worktree/import; no ml-service change; no history rewrite; frozen six + audit bytes preserved;
main stays plaintext-free; normal commits/pushes only.
