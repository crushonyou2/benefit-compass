# Retrieval v3 D-143 — generation-v9r23 literal-path PRE-SMOKE correction PASS

Date: 2026-09-08
Stage: Smoke-A prelaunch reconciliation / same-generation PRE-SMOKE correction
Generation: `retrieval-v3-dev-generation-v9r23`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r23`
D-142 durable base commit: `ac97086be76ef5f8f231c591561541874d7458ff`

## Verdict

**D-143 / v9r23 PRE-SMOKE CORRECTION: WEB PASS.**

D-142 remains historical evidence for the earlier reviewed bytes, but its final-byte Smoke-A authorization is superseded by D-143. During the fresh D-142 -> Smoke-A prelaunch gate, independent read-only review found a current operative plan/runtime contradiction that D-142 had missed: the SHA-pinned common semantic-role launch path appended the absolute staging directory directly to every Author/Reviewer/C prompt even though the current plan says semantic-role prompts expose no literal staging paths and role filesystem access is kind-bound.

No v9r23 Smoke A/B, real freeze, Phase C, source-truth snapshot, Author/Reviewer/C generation role, selector, protected evaluation, holdout, production change, or canonical audit append had occurred, so the defect was repaired in place as the same v9r23 PRE-SMOKE stage before any one-shot boundary was consumed.

The corrected final v9r23 bytes are independently PASSed and eligible for the separately authorized exactly-one Smoke A gate. Smoke B, real freeze, Phase C, protected dev-v2, holdout, and production remain prohibited.

## Fresh prelaunch base

Before the repair and again before D-143 durable closure:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `ac97086be76ef5f8f231c591561541874d7458ff`
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- canonical audit exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/dev-v2/`, `eval/retrieval-v3/holdout/` absent
- OMP `18.1.13`; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`
- bundled Paseo `0.7.2`
- immutable v9r22 frozen evidence remains 75/75 exact and its run lock remains present

## Discovered D-142 blocker

The D-142 final plan stated:

- Author prompts expose no literal staging paths; the session cwd is the staging root and file access uses the five kind-bound role tools.
- Reviewer/C confinement uses kind-bound resources and never exposes literal staging paths.

But current pinned `coord_wrapper_tpl/phasec_driver.py::run_agent_stage()` contained:

`prompt_text += f"\n\nYour staging root is: {staging}\n"`

immediately before launching every Author-1/2, Reviewer-A/B, and C agent. This was a direct final plan/runtime mismatch and therefore a PRE-SMOKE hard blocker.

A same-class path append also existed in the lifecycle-smoke launch surface. It was not yet consumed and was repaired in the same static stage.

## Sole repair executor

The same D-142 implementation executor remained the sole builder executor:

- agent `3526a9e5-dabd-498d-9c67-3df795c5650a`
- title `D142 v9r23 successor pre-smoke executor`
- ParentAgentId null
- cwd main repo
- provider/model `omp` / `opencode-go/muse-spark-1.3-contributor`
- thinking `xhigh`, mode `full`

The authoritative D-143 repair prompt was sent via `paseo send --prompt-file` to avoid the earlier Windows multiline transport truncation. No replacement executor or generation identity was created.

## Narrow repair

The repair changed only pre-smoke path-surface mechanics and associated prompt/test pins:

1. `phasec_driver.run_agent_stage()` no longer appends the concrete `staging` value, or any other literal path, to semantic-role prompts.
2. Author-1/2, Reviewer-A/B, and C prompts bind the staging root to the **session cwd** without claiming a concrete path is supplied.
3. The lifecycle-smoke launcher likewise no longer appends a literal staging path; its prompt binds root to session cwd.
4. `--cwd` launch behavior, exact-cwd/model/fallback provenance verification, prepared-set confinement, kind-bound tools, wrapper controls, and all semantic contracts remain unchanged.
5. Permanent confinement regression coverage now checks the production launch paths and the role prompt set so the literal-path append cannot silently recur.
6. Mechanics pins were regenerated; plan generation is byte-stable.

The symbolic `$R/...` notation retained in reviewer/C briefs is not a literal Windows staging path and does not create a path-capable tool surface. Independent review explicitly accepted it under the standing **no literal staging path + kind-bound tool** contract.

## Final hashes and preserved contracts

Final current plan:

- `GENERATION_PLAN.json`: 69,469 bytes
- SHA256 `27b5906fae19d016fc3beb845d3c547788fa1815f4d0b41c97d13f5572669065`
- `author_isolation.mechanics_shas`: **60/60 exact**, missing 0, mismatch 0

Preserved unchanged in substance:

- D-141 lineage / immutable v9r22 boundary
- failed-D141 hash-only carry
- exactly 13 query sets / 78 pairwise checks / overlap 0
- canonical-only gold exclusions
- C fixed `c_packet_00..11`, 12 x 30 rows / all 360
- immediate fail-close on proven final-stop + incomplete/invalid output
- D-123 slot/location contract
- D-135 truthful timestamp + exactly-once O_EXCL mechanics
- A/B/C semantic roles, quotas, rubric, selector algorithm, and protected-data boundaries

## Final static validation

Current final bytes re-PASSed the non-model gate:

- `CONFINEMENT_TESTS_PASS` — 227 checks
- `FREEZE_BINDING_PASS` — 87 checks
- `GATE_TESTS_PASS` — five final-stop invalid cases each sleep `0.0`
- `PASEO_CLI_GATE_PASS` — 64 checks
- `PREFLIGHT_PASS` — 36 checks
- `REACHABILITY_PASS` — 87 checks
- `LIFECYCLE_CONTRACT_PASS` — 53 checks
- `ROLE_TESTS_PASS` — 220 checks
- `STAGING_EXACT_SET_PASS` — 41 checks
- thirteen sets — 78 pairwise / overlap 0
- `REGISTRY_SCAN_PASS` — 37 checks
- `FREEZE_RERUN_REJECTION_PASS` — 66 checks
- `CARRY_EXCLUSIONS_PASS` — 13 sets; D-141 360 fingerprints; failed-gold additions 0
- D-123 location/slot regression — 6 positive / 5 negative
- literal Windows path hits across role prompts/briefs = 0
- production semantic-role and lifecycle launchers contain no staging-path append

The static battery created only builder-local Python cache artifacts. The exact two resolved `__pycache__` directories inside the v9r23 builder were removed after verification. Final cache dirs = 0; `.pyc` = 0; mechanics remained 60/60 exact.

## Final duplicate/runtime zero-state

Immediately before D-143 closure:

- real v9r23 `PLAN_LOCK.json` absent
- `FROZEN_HASHES.json` absent
- `phasec_driver.run.lock` absent
- source truth / source-truth meta absent
- final evalset absent
- expected Smoke-A root `C:\Users\joji\bc-v3-v9r23-coord-smoke-20260908` absent
- expected exact Smoke-A OMP session directory absent
- complete local Paseo registry: 336 parseable records, parse errors 0, exact Smoke-A cwd matches 0
- matching Smoke-A processes 0

No one-shot runtime boundary was consumed by D-143.

## Independent final review

Independent current-byte review on exact plan SHA `27b5906f...69065` confirmed:

- the prior literal staging-path blocker is cleared;
- all five semantic-role prompts bind root to session cwd and expose no literal Windows/builder/repo path;
- symbolic `$R` brief notation is not a standing-contract violation;
- mechanics 60/60 exact;
- cache0 / runtime0 / Smoke-A root-session-process0;
- repo local/upstream/direct-origin aligned at `ac97086...58ff` and clean;
- **no remaining blocker**.

## Gate boundary

**D-143 supersedes D-142 only for the current final-byte PRE-SMOKE authorization.** D-142 remains immutable historical evidence of the earlier review and its missed blocker.

The corrected v9r23 final bytes may now proceed to the already user-authorized **exactly one Smoke A** after a final read-only duplicate/provenance reconciliation. Any Smoke-A failure consumes the one-shot stage and closes/fails v9r23 per standing rules; no repair/retry/second Smoke A is permitted. Smoke B, real freeze, Phase C, protected dev-v2, holdout, and production remain separately gated.
