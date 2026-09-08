# Retrieval v3 D-141 — generation-v9r22 Phase-C CONTRACT_INVALID_GENERATION

Date: 2026-09-08
Stage: one-shot Phase-C execution closure
Generation: `retrieval-v3-dev-generation-v9r22`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260908-v9r22`
D-140 pre-execution commit: `91b8b13b23cdbe271657a0e9183e0d77e3ce98c9`

## Verdict

**v9r22 = HARD HOLD / CONTRACT_INVALID_GENERATION / NON-RESUMABLE / NON-REPAIRABLE.** The D-140-authorized frozen Phase-C execute was consumed exactly once. Source truth, both Authors, the mechanically valid 360-row candidate pool, Reviewer A/B, raw A/B freeze, keymaps, agreement and disagreement artifacts all completed. Adjudicator C then final-stopped after writing only 240/360 rows. The frozen completion gate waited its full 5400-second deadline and the frozen driver returned `rc=3` with canonical error `adjudicatorC: role completion gate: role completion deadline exceeded (5400s)`. No retry, resume, run-lock removal, frozen-byte patch, manual C continuation, second coordinator, or same-generation repair is permitted.

## Reconciled closure base

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin `91b8b13b23cdbe271657a0e9183e0d77e3ce98c9` before this docs-only closure
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing baseline `5327661445c37191a3fd61db195f3af4d2cf893a` = 0
- canonical `eval/retrieval-v3/audit/events.jsonl` remains exactly 4 rows, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/dev-v2/`, and `eval/retrieval-v3/holdout/` remain absent
- no selector/final evalset artifact was produced

## Frozen-byte preservation

Post-failure independent rehash proves all 75 `FROZEN_HASHES.json` entries exact, missing 0, mismatch 0.

- `GENERATION_PLAN.json` SHA256 `58c862958dc2167b3a2ca7dab9ddb94af8f0c8a57fff307cd6cd89d354a821f3`
- `PLAN_LOCK.json` SHA256 `0a1c5ac8e706829fd0de2189c3cc02f2d6ffc3c4159189e8bf1bd67ee1bed24c`
- `FROZEN_HASHES.json` SHA256 `e65156efbe71427f93887408e8a78ee164992cdd45d7a345dfbbea8863615ebb`
- frozen driver `coord_wrapper_tpl/phasec_driver.py` SHA256 `d6d96d08fe45171990133a3ac91dc0a1126459ed2d4096d414b026c9c8a770c7`
- frozen completion gate `role_completion_gate.py` SHA256 `a4e25a14b0710b3fcd6ee8d0c843ff37b8ff61f6172554dfe7bc15df7c9baf5b`
- frozen role filesystem helper `role_fs_helper.py` SHA256 `84bb969a7abcbc8f0ab5724abaea21cfc2e073b587e206fa52b93efd0da03f8b`
- frozen role extension `coord_wrapper_tpl/phasec_role_ext.ts` SHA256 `2b6cfc74d0126b4280824271297bfd4442437764dae700975b154f32178b06f9`

The run lock remains present and preserved: `{"started": "2026-09-08T08:01:02Z", "pid": 59028}`. PID 59028 is no longer alive after canonical driver termination. Runtime cache/pyc created by the consumed run is left untouched as failure evidence.

## Exactly-one execute evidence

Execute coordinator:

- agent `f01ab78c-4ff5-4f2b-94fe-e4ee153de825`
- title `D141 v9r22 Phase-C execute`
- cwd `C:\Users\joji\bc-v3-v9r22-coord-execute-20260908\cwd`
- model `opencode-go/muse-spark-1.3-contributor`, thinking `xhigh`, mode `full`, Parent null
- OMP session `2026-09-08T08-00-52-813Z_01a08008-c24d-73f2-8e28-3de1d8fec394.jsonl`
- session structural parse: exactly one assistant `phasec_execute` tool call and exactly one matching tool result
- exactly one matching v9r22 execute-agent directory/record
- coordinator wrapper log: exactly one row, mode `execute`, custom tool `phasec_execute`, built-in tools `todo`, frozen controls `--tools=todo -e --no-extensions --no-skills --no-rules`, coordinator extension SHA256 `3871b68603e510f6b06584f1fa20a6b5ef95d06f4697787c72d6cb1c3999f4e6`

Canonical terminal tool result at `2026-09-08T10:23:15.181Z`:

`phasec_execute: driver nonzero exit rc=3 tail={"verdict": "CONTRACT_INVALID_GENERATION", "error": "adjudicatorC: role completion gate: role completion deadline exceeded (5400s)"}`

The coordinator then reported the failure and stopped with no relaunch. A later structural count that searched both call and result records together could misleadingly produce `2`; direct role/type parsing proves one actual call + one result, not two executes.

## Completed structural runtime before C failure

Fresh source truth and generation inputs are preserved:

- `source_truth.jsonl`: 75,207,689 bytes, 13,589 rows, SHA256 `9fe194653a4b5c9c688364aa9ae686996cb7cabfebd446a6b9a7e8895374c1a5`
- `source_truth_meta.json`: 789 bytes, SHA256 `27cae92dfd5aab742d8e5bebcc21275128054ca8a1c1889e9a1b055696c3d707`
- `anchors.json` SHA256 `079012d55d40f424d4e06f7a5b8752a782153ab42d9bd18225f772ab60dbf692`
- `slots_1.json` SHA256 `d5dd110d9350f835781b148390f66a82008c9f72ef454e8a888d2e5363a3fbcb`
- `slots_2.json` SHA256 `d8473fb2cccfe05d45374b550116507a526c34be2e9a7c81661cbd5ade193723`

Driver-owned roles are unique and completed as follows:

- Author-1 `3277189c-fac3-4eb6-8e01-122a01361010`: 6 chunks / 180 rows; collected SHA256 `91bbcb3faf3729658f7f3e4e7d89e880ac64d32a001df46c2a9211c9776b326d`
- Author-2 `ba81e384-0755-4788-a664-d1e52da62f13`: 6 chunks / 180 rows; collected SHA256 `b22f5863be7edffa683f75877abc5dc9216e447590377e7118dc526a6d58a1be`
- `candidates_merged.json`: 156,129 bytes, SHA256 `96c497d31c54846399a4723484c849e41182fe8fc09bdd25dfad22544c6d1c27`
- Reviewer A `9a057942-3e45-429e-9c13-40b2d88bd64b`: 6 chunks / 360 rows
- Reviewer B `bf4a26cd-8e94-4b5b-b64b-888daf7e8a35`: 6 chunks / 360 rows

The v9r18/D-123 pool-validation mechanics defect did not recur: v9r22 passed the 180+180 -> 360 candidate merge/validation boundary and proceeded through both complete reviewers.

A/B lifecycle artifacts remain exact:

- `raw_freeze_manifest.json` SHA256 `f487de07cfae8a8a91c64aae3447f185f36a5bc807aeeeeeb4b1b18a2f1907d2`
- `transcript_audit_attestation.json` SHA256 `d7170ef16f20e134ba2f994b66bc00d9839d2e81588ce6e9ae8d822541dbf385`
- `packet_keymap_A.json` SHA256 `5cec1e9c77887a3d56e494a3bc87a3626cd3ee8e16c8bc35ecdd0dbc37414802`
- `packet_keymap_B.json` SHA256 `8ce6a8e35a17e0816275744a343e4264cd675afd3400380ae6cf9931f99e1b34`
- `raw_A.jsonl` 360 rows / SHA256 `0661e239de4759c69f16f003f440dc0b74b196cdc584029152a368d3b91d03ab`
- `raw_B.jsonl` 360 rows / SHA256 `5010b050644f4424f05df3452cbf1d953faa5eb3b8a2d72503ff501c08378638`
- `ab_by_candidate.jsonl` 360 rows / SHA256 `af01ae19ef1fd0d30c1fe78df1d7f0b26a44edf4e83ed7bed6cfcfcf3c40d964`
- `agreement_audit.json` SHA256 `7923022f5d3642fbe326b907c4cbc0d924504ede90314b949014040400d63e47`
- `disagreement_matrix.json` SHA256 `b88b909b1c650a4d150c8eded93cc9f192c8f4235d66999a158284de3829c3ae`
- `c_keymap.json` SHA256 `04c9842eb86454f2e6e01840bf962d3c0d053a8e6514f7b2fb0611342515b68c`

## Adjudicator C exact failure boundary

C agent `a440ac79-5063-460a-b9b6-86ff53d9be31` was launched once at the exact C staging root with the frozen role surface. Its live session remains locked by the preserved idle wrapper, so shared-compatible read was used rather than stopping the process.

Session structural evidence:

- 1,478,140 bytes / 200 lines
- SHA256 `ed0ed63463a5be9adad8b869f470c9fe2749f1c6107d08bf2980e7b42c7dc233`
- 44 assistant messages, one initial user message, no later user/developer trigger
- final assistant stop at `2026-09-08T09:03:23Z`, stopReason `stop`
- calls/results exactly: `todo` 5, `role_read_resource` 4, `role_search_snapshot` 25, `role_get_policy` 37, `role_write_chunk` 4
- wrapper invocation SHA256 `e7f86b38aa63fb6e4511c3b5ed64ddb403c915878eaba347ac770a3ac31c56d9`
- role access log: 70 rows, SHA256 `65177ce659e77ac0f378890a385e697d8897bc8e0c2eacc6f6257f6135538785`

C wrote exactly four valid 60-row chunks:

- `chunk_0.jsonl` SHA256 `697350be0192da09031f042f678414c79e21bce2ed0113464cc7abfe55cf794f`
- `chunk_2.jsonl` SHA256 `14aaa7a54d144c4ebdae855ff69386ab32a1932632e5f9fa6cf51fb4a1cdcd76`
- `chunk_3.jsonl` SHA256 `38ea4053769eac5fe8b117355d49ecfa3cc6349256ed4cfbab695db94bd1c8ec`
- `chunk_5.jsonl` SHA256 `2cdc6211a7828f2b25302a2617fc3242f95ec63b009325360d9f1a7f7ce09547`

Missing fixed output chunks are `chunk_1.jsonl` and `chunk_4.jsonl`; structural completion is 240/360 with 120 residual rows. `adjudicated_pool.json`, C merge output, selector output, and final evalset are absent.

## Root cause and frozen lifecycle nuance

The immediate defect is model-facing C packet delivery completeness, not arbitrary filesystem denial. The frozen C role exposes fixed resources `c_brief`, `c_packet_1`, `c_packet_2`, and `rubric`. `role_read_resource` returns each packet as a whole resource and has no pagination/window/range API. The helper byte cap accepts the ~48-49 KB packet files, but the model-facing tool presentation elided/truncated middle content. C explicitly reported partial authority, 240/360 completed, and inability to access omitted exact packet rows.

No lawful same-generation recovery existed: C had no arbitrary read/bash/eval surface, Web/prime could not supply missing rows without breaking role confinement, and the standing one-shot contract forbids resume/message/manual continuation/new C/frozen patch after consumption.

A second mechanical defect is proven in the frozen completion gate. `wait_role_completion()` treats idle/final-stop with structurally incomplete output as WAIT and only fails when `ROLE_DEADLINE_S=5400` expires. Therefore the already non-recoverable C final-stop remained live for the full deadline. The canonical frozen semantics were obeyed rather than overridden; the driver finally failed closed at the deadline with rc3. A fresh successor may repair this by failing closed immediately once final-stop is proven while required output remains incomplete, while still preserving transient-idle protection before final stop.

## Process deviations disclosed

These deviations do not create a second generation execute, but are preserved for provenance:

1. The D-141 stage executor's first precheck turn was interrupted by a follow-up instruction. Fresh zero-state evidence at that boundary proved run lock, source truth, Phase-C root, execute cwd/session and execute identity were still absent, so the one-shot had not yet been consumed.
2. A pre-launch `take_snapshot.py --help` probe invoked `main()` and created temporary builder-local source-truth/cache output; the stage executor restored the pre-launch zero-state before the actual execute and reverified frozen 75/75. This did not consume the run lock or launch a model role.
3. The launcher kernel returned exit 130 after spawning the single execute coordinator but before returning its ID. The existing ID was recovered read-only from the Paseo registry; no replacement coordinator was launched.

## Closure / successor boundary

v9r22 is permanently closed as `CONTRACT_INVALID_GENERATION`. Preserve the builder, run lock, source-truth snapshot, all Phase-C roots, role sessions, wrapper/access logs, Author/Reviewer/C outputs, A/B lifecycle artifacts, and frozen bytes in place. Do not retry, resume, delete/recreate, patch, relabel, manually complete C, run C merge/selector, or launch another coordinator for v9r22.

A successor is a **new logical stage and fresh generation identity only**. Its narrow proven mechanical repair targets are:

1. fixed/paginated or fixed-window C packet access that preserves C-only confinement and does not introduce arbitrary path access;
2. immediate fail-close on proven final-stop + incomplete required output, while preserving transient-idle semantics before final stop.

Before successor construction, standing SSOT/prereg must be checked for whether v9r22's complete 360 authored queries become a failed-generation hash-only freshness exclusion set. This closure does not decide that disposition. No rubric/quota/selector/retrieval semantic relaxation, protected dev-v2/holdout execution, production change, or release-threshold change is authorized here.
