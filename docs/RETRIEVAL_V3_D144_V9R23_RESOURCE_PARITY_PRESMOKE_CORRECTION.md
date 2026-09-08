# Retrieval v3 D-144 — generation-v9r23 resource-parity PRE-SMOKE correction PASS

Date: 2026-09-08
Stage: Smoke-A prelaunch reconciliation / same-generation PRE-SMOKE correction
Generation: `retrieval-v3-dev-generation-v9r23`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r23`
D-143 durable base commit: `41c484edf96d059c4e83d853d7b92e3225731307`

## Verdict

**D-144 / v9r23 PRE-SMOKE CORRECTION: WEB PASS.**

D-143 remains immutable historical evidence for the earlier reviewed bytes, but its final-byte Smoke-A authorization is superseded for execution by D-144. After D-143 durable closure, independent current-byte review found an additional operative PRE-SMOKE mismatch that D-143 had missed: the current plan states reviewer/author prompts and briefs use kind-bound resource names and expose no literal staging paths, yet model-facing text still carried pseudo-path and direct-input instructions — reviewer/C briefs used `$R/...` path forms, the author brief presented `source_truth.jsonl`/`source_truth_meta.json` as local inputs, and the C prompt instructed a generic `role_read_resource` resource `"c_packet_k"` that the helper would DENY (only exact `c_packet_00..c_packet_11` are accepted).

No v9r23 Smoke A/B, real freeze, Phase C, source-truth snapshot, Author/Reviewer/C generation role, selector, protected evaluation, holdout, production change, or canonical audit append had occurred, so the defect was repaired in place as the same v9r23 PRE-SMOKE stage before any one-shot boundary was consumed.

The corrected final v9r23 bytes are independently PASSed and eligible for the separately authorized exactly-one Smoke A gate. Smoke B, real freeze, Phase C, protected dev-v2, holdout, and production remain prohibited.

## Fresh prelaunch base

Before the repair and again before D-144 durable closure:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `41c484edf96d059c4e83d853d7b92e3225731307`
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- canonical audit exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/dev-v2/`, `eval/retrieval-v3/holdout/` absent
- OMP `18.1.13`; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`
- bundled Paseo `0.7.2`
- immutable v9r22 frozen evidence remains 75/75 exact and its run lock remains present

## Discovered D-143 blocker

The D-143 final plan stated (reviewer_filesystem_confinement + generation_authors):

- reviewer initial prompt/brief uses kind-bound resource names, never paths;
- author prompts expose no literal staging paths; the session cwd is the staging root with kind-bound tools.

But current model-facing text was not fully aligned:

1. `reviewer_brief.md` said `$R` is given in the task prompt and used `$R/packet.jsonl`, `$R/RUBRIC.json`, `$R/out/...` path forms.
2. `c_brief.md` similarly used `$R/c_packet_00...`, `$R/RUBRIC.json`, `$R/out/...` path forms.
3. `author_brief.md` presented `source_truth.jsonl` and `source_truth_meta.json` as local input filenames even though direct snapshot file read is not a kind-bound resource and `source_truth_meta.json` is not staged to authors.
4. `prompt_adjudicatorC.txt` gave the invalid generic tool example `role_read_resource {resource: "c_packet_k"}` even though only exact `c_packet_00..c_packet_11` names are accepted — a real C role following it would take a helper DENY.
5. reviewer prompt `$R` wording needed the same session-cwd + kind-bound-resource reconciliation.

## Sole repair executor

The same D-142/D-143 implementation executor remained the sole builder executor:

- agent `3526a9e5-dabd-498d-9c67-3df795c5650a`
- title `D142 v9r23 successor pre-smoke executor`
- ParentAgentId null
- cwd main repo
- provider/model `omp` / `opencode-go/muse-spark-1.3-contributor`
- thinking `xhigh`, mode `full`

Repair and cache-cleanup prompts were sent with `paseo --prompt-file`. No replacement executor or generation identity was created.

## Narrow repair

The repair changed only pre-smoke prompt/brief wording and associated test pins:

1. Reviewer/C briefs now bind the staging root to the session cwd and reference readable files only by exact kind-bound resource names — no `$R/` or `$OWN_ROOT/` pseudo-path dependence.
2. The author brief no longer treats snapshot/meta as directly readable local inputs; snapshot evidence is only via `role_search_snapshot`/`role_get_policy`, and `source_truth_meta.json` is explicitly not staged/readable to authors.
3. C instructions use only exact `c_packet_00` through `c_packet_11` resource names; no generic `c_packet_k`.
4. Writes remain `role_write_chunk` chunk "0".."5" with the destination derived internally; prose describes chunk numbers/coverage but requires no model-supplied path (all `Create out/ if missing` lines removed).
5. The plan was NOT relaxed: prompt/brief/runtime now conform to the existing no-path/kind-bound-resource contract.
6. Permanent confinement regression coverage (confinement 216 -> 251 checks) now proves RESOURCE_MAP exact sets per role, absence of pseudo-path/direct-input/generic-resource recurrence, all five role prompts, prior literal-path-append absence, and smoke launcher/prompt parity.
7. Mechanics pins were regenerated; plan generation is byte-stable.

## Final hashes and preserved contracts

Final current plan:

- `GENERATION_PLAN.json`: 69,469 bytes
- SHA256 `6bddf1fe4661819b9cb7029f2694194298a91c99ba6d5d491e8634eae4b67eae`
- `author_isolation.mechanics_shas`: **60/60 exact**, missing 0, mismatch 0

Relevant final file hashes:

- `author_brief.md`: 11,985 bytes, SHA256 `17400657873b57992c08b422c8d01e558e6b8f6b3332530b3dfb6f7166e57a8d`
- `reviewer_brief.md`: 5,072 bytes, SHA256 `99c8243cf576c2d6b4b9e3b0d1775ed102ae7abda05d2f3b5e6c21c3afe7a384`
- `c_brief.md`: 4,259 bytes, SHA256 `4573eb23ad6cdb4944ddf4a7cd37870e12c491740d5dbe346f667e61eb29ca9b`
- `prompt_author1.txt`: 3,565 bytes, SHA256 `2457ec0bfe56cc2c4dd3b883548f819ca4aadac26e9ec78a1195016770d1e84f`
- `prompt_author2.txt`: 3,583 bytes, SHA256 `cd1e77df07145595f2a05125387f261096bfaa3fde23f1bb9a3070b908965b1a`
- `prompt_reviewerA.txt`: 3,280 bytes, SHA256 `304754598f2eee287581232f2ed8ebd7f3eecc15dea5fca78cd7ada23076defb`
- `prompt_reviewerB.txt`: 3,280 bytes, SHA256 `02f7de1a9a0909dadd7ab3553e8cdbe0678ad421a1665c6e81765950c39ac1f8`
- `prompt_adjudicatorC.txt`: 4,084 bytes, SHA256 `3da2b2e0280a81ace3b3f988412b42c929fbf4943459e412cc6cac49c004d9d6`
- `test_phasec_confinement.py`: 42,480 bytes, SHA256 `22ef85ef31694fe1b47a0fbe2ec896b0e8fb894d186545602e0bcd37d254105d`
- `freeze_plan_v9r23.py`: unchanged, 97,441 bytes, SHA256 `a467ff8bbe8b680b60f2f5b4cc29887e33d3536e1967fceca80cde9c256d6457`

Preserved unchanged in substance:

- v9r23 identity / D-141 lineage / immutable v9r22 boundary
- failed-D141 hash-only carry
- exactly 13 query sets / 78 pairwise checks / overlap 0
- canonical-only gold exclusions
- C fixed `c_packet_00..11`, 12 x 30 rows / all 360
- immediate fail-close on proven final-stop + incomplete/invalid output
- D-123 slot/location contract
- D-135 truthful timestamp + exactly-once O_EXCL mechanics
- A/B/C semantic roles, quotas, rubric, selector algorithm, and protected-data boundaries

## Final static validation

Executor full final battery on these bytes: confinement 251 PASS; freeze binding 87 PASS; role completion gate PASS incl five invalid final-stop shapes sleep0.0; staging 41 PASS; role tools 220 PASS; writer preflight 36 PASS; launcher reachability 87 PASS; lifecycle 53 PASS; registry 37 PASS; exact Paseo CLI 64 PASS; thirteen-set 13 sets/78 pairs/overlap0; freeze rerun/timestamp 66 PASS; carry exclusions 13 PASS; D-123 slot/location 6 positive/5 negative; mechanics 60/60 exact; deterministic plan reproduction stable; freeze path stops at missing Smoke-A pin and did not publish real freeze.

Prime independently re-ran the full battery on final bytes. One first-pass test-only `strict_future_plus1s_rejected` case in `test_freeze_rerun_rejection` transiently failed; immediate rerun passed 66/66. Source inspection showed production freeze logic rejects `frozen_at_dt > observed_now_utc` with no tolerance; the test constructs now+1s then truncates/serializes to whole seconds, so elapsed wall time can erase the future relation. Fresh worker-7 independently assessed this exact event as test-harness second-truncation timing nondeterminism, not an operative freeze-contract weakness. Recorded transparently; not a production HOLD.

## Fresh independent review

Worker-7 READ-ONLY final review on exact plan SHA `6bddf1fe4661819b9cb7029f2694194298a91c99ba6d5d491e8634eae4b67eae` / 69,469 returned FINAL corrected-byte operative PRE-SMOKE PASS, no blockers. It verified prompt/brief-to-RESOURCE_MAP parity repaired; exact C `c_packet_00..11` only; author snapshot/meta truthful; writes tool-derived; no literal staging-root append; mechanics 60/60; 13/78 overlap0; C12x30; D-141 fail-fast unchanged; one-shot/runtime roots/artifacts/registry roles absent. Its cache-hygiene note saw caches produced during its review, but the SAME executor later removed only resolved builder-local cache artifacts. Prime then directly verified cache dirs = 0, `.pyc` = 0, plan SHA unchanged, mechanics 60/60 exact.

## Final duplicate/runtime zero-state

Immediately before D-144 closure:

- real v9r23 `PLAN_LOCK.json` absent
- `FROZEN_HASHES.json` absent
- `phasec_driver.run.lock` absent
- source truth / source-truth meta absent
- anchors / slots / candidates / final evalset absent
- expected Smoke-A/lifecycle/PhaseC/execute roots absent
- Smoke-A registry/process matches 0
- builder cache dirs 0 / `.pyc` 0

No one-shot runtime boundary was consumed by D-144.

## Gate boundary

**D-144 supersedes D-143 only for the current final-byte PRE-SMOKE authorization.** D-143 remains immutable historical evidence of the earlier review and its missed blocker.

This closure itself does NOT authorize Smoke A execution. The next separate user `진행해` must trigger a fresh read-only duplicate/runtime/provenance prelaunch gate and, if still PASS, exactly one Smoke A on `6bddf1fe` bytes. Smoke B, real freeze, Phase C, protected dev-v2, holdout, and production remain prohibited.
