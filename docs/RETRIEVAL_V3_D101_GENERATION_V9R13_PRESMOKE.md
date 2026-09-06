# Retrieval v3 D-101 generation-v9r13 PRE-SMOKE Web PASS (2026-09-06)

Fresh successor PRE-SMOKE closure after D-100 closed v9r12 as
CONTRACT_INVALID_GENERATION. This record is plaintext-free: identities, hashes,
counts, structural contracts, and test verdicts only. No protected query/gold
plaintext is included.

## 0. Reconciled base and stage boundary

- Repo branch `codex/retrieval-v3-user-search-quality`, base HEAD/local/upstream/
  direct remote `69f8ee3c2c503835a2ff9396bd0d7b23e6c9874a` (D-100), clean;
  `git diff --check` PASS; production `ml-service/` diff from
  `5327661445c37191a3fd61db195f3af4d2cf893a` = 0.
- OMP `18.1.5`; effective default/plan
  `opencode-go/muse-spark-1.3-contributor:xhigh`.
- Audit `eval/retrieval-v3/audit/events.jsonl`: exactly 4 events, SHA256
  `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`.
- Canonical `eval/retrieval-v3/result`, `dev`, `holdout`, and `dev-v2` absent.
- D-100 commit time used by the future freeze provenance gate:
  `2026-09-06T22:27:25+09:00` (`2026-09-06T13:27:25+00:00`).
- This stage authorizes only fresh v9r13 PRE-SMOKE builder work and Web
  independent review. No v9r13 model smoke, real freeze, Phase C, source-truth
  snapshot, semantic role, selector, protected evaluation, holdout, or
  production retrieval change was run.

## 1. Fresh successor identity and executor

- Single Paseo/OMP executor root:
  `2f61d8e4-c6ac-4688-8153-b6f69858d0d1`, title
  `D101-v9r13-presmoke-builder`, repo cwd, model
  `opencode-go/muse-spark-1.3-contributor`, thinking `xhigh`, ParentAgentId
  `null`, final status `idle`; no subagents.
- Fresh builder:
  `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260906-v9r13`.
  Final inventory: 65 non-pycache files; final `__pycache__` count 0 after
  executor/Web synthetic-test cleanup.
- Identity:
  - generation `retrieval-v3-dev-generation-v9r13`
  - seed `benefit-compass-retrieval-v3-dev-v2-generation-v9r13-2026-09-06`
  - candidate IDs `v3g9r13-001..360`
  - C IDs `v9r13c-001..360`
  - mechanics renamed to `carry_exclusions_v9r13.py` and
    `freeze_plan_v9r13.py`.
- Same TEN fingerprint exclusion sets remain operative; no 11th set exists.
  Web independently re-ran 45 pairwise comparisons with overlap 0 and exact
  counts: dev-v1 180 / holdout 250 / history 248 / D070 273 / D071 273 /
  D072 360 / D074 360 / D076 365 / D082 360 / D086 360.
- RUBRIC semantics and candidate-plan/numeric contracts are unchanged from
  v9r12. v9r12 produced no candidate/query rows, so no new exclusion set was
  introduced.

## 2. Deterministic lifecycle-smoke proof repair

D-100 established that v9r12 PATH/`OMP_WRAPPER_LOG` reachability worked, but
Smoke B failed because the frozen proof depended on model emission of an
unavailable built-in attempt and optional negative probes. v9r13 repairs only
that proof contract.

### Lifecycle-smoke-only custom probe

`coord_wrapper_tpl/phasec_role_ext.ts` now registers `role_smoke_probe` only
when `ROLE_KIND == lifecycle_smoke`:

- empty-object schema; no model-supplied path/resource/command;
- exactly three fixed helper operations:
  1. `read-resource ... lifecycle_smoke packet` -> expect `DENY:cross-role`;
  2. `read-resource ... lifecycle_smoke ../outside.json` -> expect
     `DENY:unknown-resource`;
  3. `write ... lifecycle_smoke out/evil.jsonl <fixed neutral row>` -> expect
     `DENY:bad-target`;
- unexpected helper success, spawn error, or missing expected marker throws
  fail-closed;
- success returns only structural `EXPECTED_DENIES_PROVEN` + marker names.

Authors retain five custom tools, reviewers/C retain four, and only lifecycle
smoke gets the sixth `role_smoke_probe`; real role zero-deny auditing remains
unchanged.

### Prompt and auditor

- `smoke_lifecycle_prompt.txt` no longer asks the model to invoke unavailable
  built-in read/eval/bash or manually formulate individual deny probes. It
  requires exactly one `role_smoke_probe {}`, then the six 1-row chunks,
  final `LIFECYCLE_SMOKE_DONE`, no descendants, and no post-stop tools.
- `audit_lifecycle_smoke.py` no longer requires a read/eval/bash attempt.
  Instead it:
  - permits only `todo` + the lifecycle custom tools;
  - requires `role_smoke_probe == 1`;
  - requires `role_write_chunk >= 6`;
  - requires access-log markers `cross-role`, `unknown-resource`, and
    `bad-target`;
  - fail-closes any arbitrary transcript tool such as read/eval/bash/task/hub;
  - retains exact-one wrapper, frozen controls/ext SHA/staging, final 6x1
    outputs, final stop, and zero-descendant proof.

### Permanent regression

New `test_lifecycle_smoke_contract.py` proves, without a live model/Paseo
launch, that v9r12 has the old impossible/model-dependent proof and v9r13 has
the deterministic replacement. It checks lifecycle-only registration, empty
schema, fixed deny triple, exactly-one probe requirement, forbidden arbitrary
tools, no probe exposure to authors/reviewers/C, actual helper deny logging on
synthetic staging, and mocked Bun registration behavior.

## 3. Preserved v9r12 reachability repair and bounded additional corrections

The generic launcher still passes all six role kinds:

- `PATH=<wrapper_bin>;<original PATH>`
- `OMP_WRAPPER_LOG=<staging>\wrapper_invocation.log`
- `BC_ROLE_STAGING`, `BC_ROLE_MODE=role`, `BC_ROLE_KIND=<kind>`.

Web separately re-ran the reachability regression: 87 checks PASS.

Two other final-byte changes were independently reviewed for scope:

- `role_fs_helper.py` only extends the old-generation token deny list through
  v9r12; it does not broaden resource/read/write permissions.
- `freeze_plan_v9r13.py` corrects pre-existing v9r12 freeze-binding
  inconsistencies needed to bind the repaired proof if a later real freeze is
  authorized: role wrapper allowlist token is `todo`; lifecycle runner/auditor/
  prompt/regression are included in the mechanics set; lifecycle wrapper-log
  and exact 6x1 outputs/probe/deny proof are checked from auditor output.
  These changes do not alter evaluation data, candidate semantics, thresholds,
  counts, A/B/C policy, selector policy, or protected-data boundaries.

The future freeze base is D-100
`69f8ee3c2c503835a2ff9396bd0d7b23e6c9874a`, and any real `frozen_at` must be
strictly later than `2026-09-06T13:27:25+00:00`.

## 4. Web independent final-byte verification

Web independently re-ran the final v9r13 non-model battery:

- lifecycle contract regression: `LIFECYCLE_CONTRACT_PASS`, 42 checks;
- generic launcher reachability: `REACHABILITY_PASS`, 87 checks;
- role tools: `ROLE_TESTS_PASS`, 160 checks;
- role completion gate: `GATE_TESTS_PASS`;
- TEN gate: 45 pairs, overlap 0, exact 10-set counts above;
- Phase-C confinement: `CONFINEMENT_TESTS_PASS`, 182 checks; intermediate
  CONTRACT_INVALID messages are intentional negative cases;
- Python compileall: rc 0;
- Bun `role_tools_probe.mjs`: `PROBE_PASS` with lifecycle-only probe exposure;
- Bun `phasec_probe.mjs`: `PROBE_PASS`;
- TypeScript `tsc --noEmit`: rc 0;
- `GENERATION_PLAN.json.author_isolation.mechanics_shas`: 52 entries, final
  disk 52/52 match, zero missing/mismatch.

Normalized v9r13->v9r12 comparison across 64 paired source files leaves 14
non-identity-equivalent files, all accounted for by the authorized lifecycle
proof repair, predecessor lineage/SHA repins, old-generation deny-list update,
and freeze-proof binding. No unintended retrieval/evaluation semantic delta was
found.

Executor intermediate self-checks caught two incomplete finalization issues
(`search_snapshot.py` identity-equivalence assertion and the not-yet-created
lifecycle regression) and repaired them before final binding. No such defect
remains in final bytes.

Web re-runs created only disposable builder `__pycache__`; exact-path-checked
cleanup removed them. No home v9r13 synthetic temp remained. Source hashes were
reverified unchanged after cleanup.

## 5. Final key SHA256s and no-real-freeze proof

- `GENERATION_PLAN.json`
  `e0637090d4800bb0d5e0ba4859dfaaf4d199845c7feeb0873e43d12da3bb7940`
- `launch_top_level_paseo.py`
  `a501f5cfe855c105f862cfe40869220dda569d3125ce8fb3c144e399d13cc234`
- `role_omp_wrapper.py`
  `daf4ee5764f27b3aae8eb7542f820cef738129a177d765aeec0391c9cedc4257`
- `coord_wrapper_tpl/phasec_role_ext.ts`
  `ee7c9b5bd40ac6662c5f188412392a8765b529f17edc0054b32b8f674ff898ae`
- `role_fs_helper.py`
  `ff1d34f3bd4631f976ed829d0d3179c0d9e2253c2177bde86d3ee268fd4b3463`
- `run_lifecycle_smoke.py`
  `d9d4216ce4a7aaf31e79a14a5d4a365461a73d700ecf4493cec1cd7337f9e2c8`
- `audit_lifecycle_smoke.py`
  `54f0c34d4b60437305b38fc0d5fa2b2a7cf19e826a077ed5196f5742cf553c59`
- `smoke_lifecycle_prompt.txt`
  `915ff84ebb72952c2f0960cb25e8b2bde2d5afc06edc8bbf583d34b344ac0ded`
- `role_completion_gate.py`
  `786947aa0256714501e4b367a8a66d47892149a5e28773a2c528f62331298c1c`
- `test_launcher_reachability.py`
  `ef12bd06c311139702e7ee629c77f1841f67bae83f7886db66c360fa2fc1cf92`
- `test_lifecycle_smoke_contract.py`
  `b166c3b0b447919d18c3aee36d8f218a99c21eb7e99086e1a45c4b1a3f2ae71a`
- `freeze_plan_v9r13.py`
  `73c699338951b816b013966c0d167e4e24755ebe2b5902a5aefc9d6e6c9fa15a`
- `carry_exclusions_v9r13.py`
  `985305db2810df5c79963718f0e3f7fc5627547a4cd2e4342a2c447a16694ea7`
- `input/EXCLUSION_INPUTS.json`
  `624c20b46cc2c20f733b7c29732d4e3d5a853fd33d34d8a457b4e4d5f22ddf64`
- `coord_wrapper_tpl/phasec_coordinator_ext.ts`
  `61a05624968498cce4a3da8dd9716d97422f71e0509c5d63cec491f2dc229132`

Final real v9r13 builder has no `PLAN_LOCK.json`, `FROZEN_HASHES.json`,
`phasec_driver.run.lock`, source truth/meta, candidates/raw/reviewer/C/selector
outputs, or `evalset.jsonl`.

All eight v9r12 predecessor key hashes still match D-100. Hash-only checks of
v9r12 Smoke A/B sessions also still match:

- A `d8fd4f5752c705369ed75fa09aff709e3419fbc1bc966f755f30ea2d6e4b0260`
- B `0d0396a3c2a870276df4c16938a074a180fe04ab321cd165889d9e70c1c29f25`.

D-101 executor transcript was reviewed structurally: it contains source reads,
identity migration, synthetic tests, hashes, and compile/probe commands, but no
v9r13 Smoke A/B, live `paseo run`, lifecycle runner execution, Phase-C execute,
or semantic-role model launch. Repo remained clean throughout.

## 6. Verdict and next gate

**WEB PRE-SMOKE VERDICT: PASS.**

Generation-v9r13 is approved only to the one-shot smoke gate on the exact final
bytes above. This is not real-freeze or Phase-C approval.

Next logical stage may run exactly one coordinator Smoke A; only if A passes,
run exactly one lifecycle Smoke B. Any smoke contract failure closes v9r13 as
CONTRACT_INVALID_GENERATION with no retry or same-generation repair.
