# Retrieval v3 D-075 dev-v2 generation-v6 strategy — filesystem-confinement pre-result freeze

Status: D-075 NEW LOGICAL STAGE (user-authorized continuation). Plaintext-free. No generated query/gold plaintext on main.
Stage identity: D-075 creates a generation-v6 PRE-RESULT freeze ONLY. No source-truth snapshot, no candidate generation, no A/B/C, no selector in D-075.

## 1. Reconciled base (this record phase, actual repo/Git/remote/SSOT wins — observed)

- Branch `codex/retrieval-v3-user-search-quality` HEAD `6d99fc93e4c3b208dff6d6e80c1f4cad4f5b6b80` clean, local = upstream = direct remote identical (`git ls-remote` identical).
- `git diff --check` PASS; `git diff HEAD -- ml-service/` 0.
- Frozen six byte-identical: prereg `7842018613d66aa4570f4db2f8ae5a698ceb46757995a6b7e26873177b36160e`, plan-v4 `a25d9c482094696ff7a438593979813ac568c91a977a2543a50618ca4f5177d6`, safe-action `c512fb5627179697a987b05a2431b8f7e30d1153af2ff6dca37995f6b232a35d`, policy-v2 `6fee9ec22d5d3ac153ff19a6b1b5d27ab6a6a43bda11e35821d689f938968fe5`, link-V2 `f028ce4697f1a19e8d37e9048f6d7cd07d87c35ad68478d0efa968b7c62a7e71`, cost-V1 `5891b0bab0621da71499c5c2c6a21a6ac6692bd3ee94d6cb5342adc480958323`.
- Audit `eval/retrieval-v3/audit/events.jsonl` 4 events SHA `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506` byte-identical (D-068 open grant/run untouched).
- Canonical v3 result absent; `eval/retrieval-v3/dev/` + `holdout/` absent on main; no dev-v2 branch/tag/worktree created or touched; protected v3 dev/holdout freeze branches + worktrees pre-existing, untouched.
- OMP `18.1.5`; root/plan `opencode-go/muse-spark-1.3-contributor:xhigh`; no project override (`opencode.json`/`.opencode.json` absent); no child-agent fallback through Phase B.
- No protected plaintext recovery, no `git show`/`cat-file`/`checkout`/`restore` of protected evalsets, no audit append/run/result/benchmark/retrieval/ranking/model/latency/HTTP, no candidate tuning/B, no ml-service change, no protected branch/tag/worktree/import, no history rewrite in this stage.

## 2. Standing (unchanged)

- D-074 canonical disposition is CONTRACT_INVALID_GENERATION per D-074-SC. Its 360/A/B/C/selector are failed diagnostic evidence only and NEVER reusable/relabelable/supplemented. D-074 selector counts MUST NOT tune quotas/reserve.
- D-073 paired-grounded ambiguous authoring contract was frozen pre-D074 and remains the intended authoring contract; kept unchanged.
- Final evaluation contract and 18 candidate configs/gates unchanged.

## 3. V6 identity and unchanged final contract

- New private builder only: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260905-v6`. Never D-070/D-071/D-072/v5 directories.
- New identity: plan_version `retrieval-v3-dev-generation-v6`; seed `benefit-compass-retrieval-v3-dev-v2-generation-v6-2026-09-05` (new builder only); candidate IDs `v3g6-001..v3g6-360`.
- Final contract EXACTLY unchanged: total 180; strata 21/25/21/25/18/20/23/27; headline first-six 130; safety ambiguous 23 + unsupported 27 = 50; location exact 54 at 6/7/6/8/5/6/7/9. 18 candidate configs/gates unchanged.
- Reserve remains uniform 2.0x, exactly 360 slots 42/50/42/50/36/40/46/54 and location 108 at 12/14/12/16/10/12/14/18. Do NOT inflate or target reserve from D-074 diagnostics. Symmetric construction capacity only; no gate change.
- NO target/reserve change from D074 diagnostics.

## 4. V6 authoring, annotation, rubric, selector (semantics unchanged)

- All eight authoring contracts same as frozen v5, including paired-grounded ambiguous (two distinct snapshot anchors, one omitted dimension, shared frame, two completions plus distinguishing evidence; location-bearing ambiguous shares explicit location with non-location omitted dimension). No semantic challenger/prefilter.
- Neutral rubric semantic definitions byte-semantically identical to v5 (dimensions/judgment_rules/role equal); only truthful version metadata changed to v6 (`plan_version` + `retrieval-v3-dev-generation-v6-rubric-v1`). No quotas/intended labels in rubric.
- A/B genuine independent ALL 360, C EVERY 360, agreement method (query_dim_any/gold_any/full_agreement plus task-local per-gold union+ABSENT diagnostic) and exact lexicographically-smallest selector semantics unchanged.
- Query overlap 0 vs dev-v1/holdout/history + failed D070/D071/D072/D074; gold overlap 0 vs canonical dev-v1/holdout/history only. Selected-only global gold uniqueness. Source snapshot taken only in later Phase C after Web/user continuation. Plan/rubric/lock immutable after freeze; infeasible/contract-invalid => STOP, no supplement/relabel/retune.

## 5. V6 reviewer filesystem-confinement contract (new isolation mechanics only; annotation semantics unchanged)

Durable claim is `filesystem-disjoint staging + no pre-review keymap materialization + transcript path-confinement fail-closed gate`, not stronger. No OS-sandbox claim.

1) Coordinator private builder contains candidates/intended metadata/ledgers/exclusion inputs. Reviewer tasks are NEVER given the builder path.
2) BEFORE A/B review, create TWO independent random-UUID staging roots under a neutral private temp parent outside the builder. Each reviewer receives ONLY its own staging-root absolute path. Each staging root contains exactly: its own `packet.jsonl` (fields only item_id/query_text), `RUBRIC.json`, `source_truth.jsonl` copy, `search_snapshot.py`, `reviewer_brief.md`, and its own `out/`. No counterpart packet, no keymap, no candidates, plan, ledgers, author outputs, exclusions/history, counterpart output, or coordinator files.
3) Packet A and B are generated directly into their separate staging roots. DO NOT materialize packet_keymap_A/B anywhere before BOTH reviewer raw outputs are frozen and transcript-confinement audit passes. Mapping is deterministically reconstructable afterward from frozen seed + candidate IDs + packet-order algorithm; exact reconstruction specified in plan (`a_b_packets.keymap_reconstruction`: opaque_id = first-8-hex(SHA256(seed NUL reviewer-role NUL candidate_id)) with NUL-counter collision resolution; packet order ascending opaque_id; keymap opaque_id->candidate_id).
4) Reviewer prompts contain only role + own staging-root path; no builder/repo/coordinator path. Reviewers MUST NOT list/read parent/system/OMP session dirs, traverse outside own staging root, contact each other, or use absolute paths outside own root. Source-truth/search helper are local copies inside own root.
5) After BOTH raw reviewer outputs freeze, BEFORE agreement or C, coordinator mechanically audits each reviewer OMP transcript/tool-call arguments. Fail closed `CONTRACT_INVALID_GENERATION` if any file/path-bearing read/list/grep/bash/eval/write/edit refers outside that reviewer's own staging root (except runtime-internal metadata with no user filesystem content), or mentions counterpart packet/keymap/candidate/intended/plan/ledger/author-output/other-review-root/OMP session path. This path-confinement audit is a HARD pre-agreement gate, not a semantic gate.
6) Only after both reviewer transcript audits PASS may coordinator reconstruct/materialize keymaps privately in the builder, copy/hash frozen packet/raw bytes into builder evidence, compute agreement, and proceed to C.
7) C gets its own separate random staging root containing only c_packet, same neutral rubric/source-truth/search helper/c_brief/out. C may use same-role chunk workers inside that C root. No raw A/B files/keymaps/candidates/ledgers/plan are present. Run analogous path-confinement audit before merging C; disagreement bundles are the only A/B values allowed by standing protocol.
8) Staging roots are private evidence; preserve until Web review. No OS-sandbox claim is required.

## 6. Plan lock truthful flags

- `source_truth_content_read_for_this_plan=false`; `d070/d071/d072/d074_semantic_rows_read_for_plan=false` except already-durable aggregate/contract-invalid facts; `protected_old_plaintext_read=false`.
- No D074 semantic rows/labels/golds/mappings/ledgers read for plan design. Query_text-only fingerprint extraction from v5 `candidates_merged.json` is allowed and recorded in lock (`d074_query_text_fingerprint_extraction_only=true`, source SHA `86bdf17082ec0e33b0ac846d1cf795bcae0847af608c1fbb23e4766eb53fb536`).

## 7. Phase B freeze record (frozen BEFORE source-truth content; immutable afterward)

- Builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260905-v6` (new directory; never D-070/D-071/D-072/v5).
- Exclusion (`build_exclusions.py`): v5 `candidates_merged.json` (SHA `86bdf17082ec0e33b0ac846d1cf795bcae0847af608c1fbb23e4766eb53fb536`) query_text ONLY -> SHA256(NFC->strip->collapse whitespace->casefold), sorted unique 360/360 -> `input/failed_d074_query_fingerprints.json` SHA `fde763315b362774875b9142ebad85897363bd2180cce3ee4047281d79ad8d05`. No old plaintext printed/stored outside the v5 builder; no D-074 labels/golds/ledgers/mappings/keymaps read. Byte-carried fingerprint-only inputs verified identical to v5 manifest: D-070 `0acc6f279fb3c89db3d5df9a8268cfc668571401945830d99763384216f06b53` (273), D-071 `3a037d988bba8993cca642cd3e2e2c40dbb003301efe77b1d652328570e320f9` (273), D-072 `ff3f65d60b1af9bb0d5dc9dac67a1ce4ad55704904e18c72c96ca3f38380ddde` (360), dev-v1 `57716c6a6b3aaa08e9e8072f7148aac691d80ed81fdc7e10bd07957386035f88` (180q/228g), holdout `3463a8a1737c19b9a4a7536d7c8f3d92051c8526506096ecaea2d54d3d7f8bc1` (250q/212g), history `42e8534d578bc45808d6546bee9f59a49564ad455cd3b693d23853676d169454` (248q/248g). Manifest `input/EXCLUSION_INPUTS.json` SHA `5d90c1357ab575cd0e7bc6790bdbd213cd6af52211c378eeb9ad94bd20707a11`.
- Frozen (`freeze_plan.py`, canonical single-line bytes + LF): `GENERATION_PLAN.json` 21302 bytes SHA `4e5c869ba1694b48bc84580dd1a6e03fc7c928221e57b1360af3871b373de286` (version `retrieval-v3-dev-generation-v6`, seed `benefit-compass-retrieval-v3-dev-v2-generation-v6-2026-09-05`, candidate IDs `v3g6-001..v3g6-360`, reserve 42/50/42/50/36/40/46/54=360 + location 12/14/12/16/10/12/14/18=108, paired-grounded ambiguous contract unchanged, seven other contracts unchanged, A/B-all-360 + C-every-360, agreement scope + task-local per-gold method unchanged, exact lexicographically-smallest selector with selected-only gold uniqueness + D074 query-gate added, filesystem-confinement contract added, keymap reconstruction specified); `RUBRIC.json` 3330 bytes SHA `3604105e737e1d87dc39a0a253b8f498750a2103f8e11a47695c43382f48b533` (v6 rubric, dimensions/rules/role byte-semantically identical to v5 `249892030c0bb2f78e6045050a71348adfc22cc201b6e79e581e55405bf77aff`, only version metadata changed); `PLAN_LOCK.json` 1312 bytes SHA `f5b09980feba349f7e38b9ca0ba6161664f82c6a4dc8aac57e95fb1749b087cc` (truthful not-read flags + query_text-only extraction recorded). V5 base verified identical before use (`70cc98ff`/`24989203`/`dff69b07`).
- Provenance (actual, observed): OMP `18.1.5`; root session model `opencode-go/muse-spark-1.3-contributor:xhigh` (runtime context; model config never changed); no project model override (no `opencode.json`/`.opencode.json`); no child agents spawned through Phase B; no fallback model used. Phase C child agents/sessions will be recorded with their model/session evidence at spawn time.
- Gate: this record is committed+pushed and remote-verified BEFORE any Phase C source-truth content read. Post-freeze rule in force: NEVER mutate plan/rubric/lock; infeasible/contract-invalid -> STOP/HOLD, no supplement/relabel/retune/recycle.

## 8. End state and STOP

- Main contains only plaintext-free D-075 strategy/freeze records. Private builder contains exclusions + scripts + plan/rubric/lock only; `source_truth.jsonl` ABSENT; candidates ABSENT; reviewer staging roots NOT created yet.
- Verify clean local=upstream=direct remote, diff-check PASS, ml-service 0, frozen six/audit exact, result/dev/holdout absent, no dev-v2 protected refs.
- STOP for Web independent review. Phase C generation requires Web review/user continuation and is NOT authorized in D-075.

## 9. Forbidden counts (this stage)

Forbidden counts all 0: source-truth snapshot, candidate generation, A/B/C, selector, benchmark/retrieval/ranking/latency/HTTP/model-encode, D068 retry/audit append/result, protected plaintext/recovery/git-show/cat-file/checkout/restore/sparse/worktree for protected evalsets, protected branch/tag/worktree/import, ml-service change, history rewrite, D074 row reuse (fingerprint-only exclusion excepted).
