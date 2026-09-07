# Retrieval v3 D-123 — generation-v9r18 Phase-C CONTRACT_INVALID_GENERATION

Date: 2026-09-08
Stage: one-shot Phase-C execution closure
Generation: `retrieval-v3-dev-generation-v9r18`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260907-v9r18`

## Verdict

**v9r18 = HARD HOLD / CONTRACT_INVALID_GENERATION / NON-RESUMABLE / NON-REPAIRABLE.** The single D-122-authorized frozen Phase-C execute procedure was consumed exactly once. Fresh source truth and both 180-row Author outputs completed, but the frozen 360-pool mechanical validation returned `STRUCTURAL_FAIL` before `candidates_merged.json` was written and before Reviewer A/B staging or launch. No same-generation retry, run-lock removal, frozen-byte patch, manual reviewer launch, or second coordinator is permitted.

## Reconciled closure base

- Repo branch `codex/retrieval-v3-user-search-quality` at `b5a0241d9f032e46a7f9a4ce2c9e8167f4ce00d6`; local/upstream/direct origin equal and clean.
- `git diff --check` PASS; production `ml-service/` diff from the standing baseline is zero.
- Canonical audit remains exactly 4 events, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`; no protected-evaluation result event was appended.
- Main-tree `eval/retrieval-v3/dev/` and `eval/retrieval-v3/holdout/` plaintext paths remain absent.
- OMP effective default/plan remains `opencode-go/muse-spark-1.3-contributor:xhigh`; no new OMP/model execution was performed during this closure.

## Frozen-byte preservation

Independent current rehash after the failure proves all 71 `FROZEN_HASHES.json` entries exact, missing 0, mismatch 0:

- `GENERATION_PLAN.json` SHA256 `848b586235653737210d78424baa00935c86665aff2a7542d71ffa2b6807c532`
- `PLAN_LOCK.json` SHA256 `20d8a14518d57d28ad66ec65da627db300ad0180de402180675af4d4132a868c`
- `FROZEN_HASHES.json` SHA256 `7f3f4903c387d05a20e71ae5a6bc493e1264f234512a3509708e0f1b7fb01955`

The failed generation is preserved in place. The run lock remains present and is not removed.

## Exactly one execute

Execute session:

`C:\Users\joji\.omp\agent\sessions\-bc-v3-v9r18-coord-execute-20260907-cwd\2026-09-06T20-56-29-333Z_01a07882-2194-71ec-bf3f-0d1ac7195a1f.jsonl`

- 10 lines / 13,755 bytes
- SHA256 `cbf4750d74a95e7fd6c01130d46cc94b5281aa4e442a734a2bd42a25da17052b`
- user instruction required `phasec_execute` exactly once with an empty object, no bypass/retry
- `phasec_execute` tool call count exactly 1
- frozen driver terminal return: `rc=3`, verdict `CONTRACT_INVALID_GENERATION`
- no second execute coordinator or driver run

Current process reconciliation finds zero v9r18 matching processes; the terminal failure is final, not a still-running generation.

## Runtime artifacts and exact stop boundary

Present and preserved:

- `phasec_driver.run.lock`: SHA256 `45caf89911e9ab465dffb7a15b49d77086246f4fb8f058b3f8325512d6194c30`
- source truth: 13,589 rows, SHA256 `9fe194653a4b5c9c688364aa9ae686996cb7cabfebd446a6b9a7e8895374c1a5`
- `source_truth_meta.json`: SHA256 `940fef6ce917e3a5d87b253cc73a10aabedc799c875dc81fe706449d44a2aa3d`
- `anchors.json`: SHA256 `1060ed7d5221c9a7023b3dd578f41cb61c0d3cd6aa5c5ebe8017103c2cb4b06d`
- `slots_1.json`: SHA256 `7020fec1157ab8d78e2a3755957a4df5792ea1870b2b3e75b55d09a9b72d777c`
- `slots_2.json`: SHA256 `293d93c0354add532317219ddc6e033e184ae2735abc9106594a5fcf952a1c31`
- Author-1 candidate collection: 180 rows, SHA256 `158e47639db7ee86b8a71874a1b6b582c68dea1efcbff7b5af7c59f6fad6e6c5`
- Author-2 candidate collection: 180 rows, SHA256 `01028483c324331c2c8d23c6cb48c3eb662c9d35a72581cbb46b9e4f421a008d`
- Author-1 session: 777 lines, SHA256 `ae9192f6e716569267c7f99c2741d277d653656269ed448f9d8e60904bc61e95`
- Author-2 session: 674 lines, SHA256 `526428e8b1a40a91639ac0f674700c7d60a0a603a24b5b79c5a42646258ea289`
- Author-1 role access log: 253 rows, SHA256 `9f5c5c1fc0064b8fb3d583e98a5369029266f9eb950dc8115b2765b5e22c4c9e`
- Author-2 role access log: 274 rows, SHA256 `0c92cc41cd8200f6385051277d45919bf9c4dba0d8387c87188af95effcea0f8`

Absent / never reached:

- `candidates_merged.json`
- Reviewer A/B staging, agents, sessions, or raw outputs
- Reviewer C/adjudication artifacts
- selector final 180 / `evalset.jsonl`
- protected dev-v2 evaluation
- holdout evaluation
- production change

## Frozen pool-validation failure

The frozen validator returned exactly eight fatal entries:

1. `POOL` — `loc_short_keywords_11_!=_10`
2. `v3g9r18-196` — `location_token_absent`
3. `v3g9r18-199` — `location_token_absent`
4. `v3g9r18-220` — `location_token_absent`
5. `v3g9r18-244` — `location_token_absent`
6. `v3g9r18-287` — `location_token_absent`
7. `v3g9r18-291` — `location_token_absent`
8. `v3g9r18-294` — `location_token_absent`

The same frozen validator was independently re-run with the frozen UTF-8 execution mode and reproduced the exact eight failures. `dup_anchor_stat` (`dup_keys=34`, `dup_rows=171`) is diagnostic output only and is not one of the eight fatal fail codes.

## Root cause

Two distinct mechanical defects are proven.

### 1. Missing exact slot metadata binding

Per-ID comparison of the immutable slots against the collected Author rows finds exactly one metadata mismatch: `v3g9r18-220`. The frozen slot has `intended_stratum=short_keywords` and `intended_location=false`; the returned row preserved the stratum but changed `intended_location` to `true`. Because frozen `validate_pool.py` checks only candidate-ID set plus aggregate stratum/location counts, not exact per-candidate slot metadata, the mutation survived until aggregate/location validation. It produced the short-keyword 11-vs-10 location-count failure and the row's own `location_token_absent` failure.

### 2. Producer/validator mismatch for real location tokens

The frozen Author contract says a location-bearing slot must contain a **real location token**, but frozen `validate_pool.py` recognizes only a small undocumented closed set of location bases. Mechanical comparison using the immutable slot booleans finds six otherwise location-bearing rows whose real place names are missed by that parser: five use `천안`, one uses `아산` (`196`, `199`, `244`, `287`, `291`, `294`). No unexpected-location false positive was found across the 360 immutable slots.

Therefore the failure is not grounds to weaken location quotas or disable the location gate. A fresh successor must instead bind returned slot metadata exactly and make the author-facing allowed-location contract identical to the validator's frozen vocabulary/parser, including particle-attached forms.

## Failed-query freshness disposition

The two collected candidate files form a complete 180+180 = 360-query failed-generation pool. Under the standing D-087 precedent, a complete failed generation may be carried forward **only** as one-way normalized SHA256 query fingerprints, never as semantic/template material. Mechanical hash-only inspection proves 360 rows / 360 unique fingerprints and zero overlap with each of the existing ELEVEN sets. A fresh successor may therefore add v9r18 as the twelfth query-fingerprint freshness set, yielding 66 pairwise set comparisons. Gold exclusions remain unchanged. No v9r18 query text may be persisted to the repo or reused as successor authoring material.

## Closure / successor boundary

v9r18 is closed permanently as `CONTRACT_INVALID_GENERATION`. Preserve the builder, run lock, Phase-C roots, Author roots, candidate rows, sessions, access logs, and frozen bytes as one-shot failure evidence. Do not retry, resume, patch, relabel, manually merge, or launch downstream roles for v9r18.

The next allowed implementation is a **fresh generation identity only**, limited to the proven mechanical repairs: exact slot metadata binding, one shared/frozen location-token contract with regression coverage, twelfth hash-only freshness exclusion under D-087 precedent, and ordinary identity/freeze-mechanics repins. No rubric/quota/selector/retrieval semantics, protected datasets, production `ml-service/`, or release thresholds are changed. Build and static/pre-smoke validation may proceed; any successor model smoke remains a separate gate.
