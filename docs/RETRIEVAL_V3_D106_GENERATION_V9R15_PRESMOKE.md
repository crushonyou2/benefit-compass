# Retrieval v3 D-106 — generation-v9r15 PRE-SMOKE Web PASS

Date: 2026-09-07
Stage: fresh successor PRE-SMOKE construction + independent Web review
Generation: `retrieval-v3-dev-generation-v9r15`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260907-v9r15`

## Verdict

**D-106 / v9r15 PRE-SMOKE: WEB PASS.**

v9r15 is a fresh successor to D-105. It repairs the v9r14 frozen real-freeze CLI binding defect without changing Retrieval v3 evaluation/retrieval semantics. No model smoke, real freeze, source-truth snapshot, Phase C, Author/Reviewer/C, selector, protected evaluation, holdout evaluation, or production change occurred in D-106.

The next gate is exactly one Smoke A on these final bytes and, only if A passes, exactly one Smoke B. No same-generation repair is allowed after a smoke is consumed.

## Reconciled base

Before successor construction, actual state was reverified:

- branch `codex/retrieval-v3-user-search-quality`
- HEAD/local/upstream/direct remote `821d72727e502fa17a4fa7d33df5267e8a61d4de` (D-105)
- working tree clean; `git diff --check` PASS
- production `ml-service/` diff from standing base: 0 files
- audit exactly 4 events, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`
- canonical `eval/retrieval-v3/result`, `dev`, `holdout`, `dev-v2` absent
- OMP `18.1.5`; effective default/plan `opencode-go/muse-spark-1.3-contributor:xhigh`
- v9r15 destination absent before creation
- v9r14 real-freeze artifacts absent; v9r14 builder and both consumed smoke sessions preserved

The local Paseo CLI exposed command help but its daemon/list path did not return a usable agent state in this shell. To avoid duplicate/ambiguous agent creation, the same approved executor model was run as one direct OMP root and later resumed once for the same-stage Web blocker repair. OMP session:

`C:\Users\joji\.omp\agent\sessions\-Documents-취준자료-project-repos-benefit-compass\2026-09-06T15-50-13-784Z_01a07769-be18-7114-b91b-bad5ce41cbaf.jsonl`

- final session lines: 352
- session SHA256: `22e68788c3a674e8b7cd1d6362d74012df437df5116da8a8955e37ef4e81b164`
- initial executor prompt SHA256: `194cf5bb8697d8cb21c1453ab4612da688e4b985af2aeca16e1d77f6f79dc721`

No model smoke/Paseo role launch was performed by this root.

## Fresh v9r15 identity

Final builder contains 66 files and zero `__pycache__`/`.pyc`.

- plan version: `retrieval-v3-dev-generation-v9r15`
- seed: `benefit-compass-retrieval-v3-dev-v2-generation-v9r15-2026-09-07`
- candidate IDs: `v3g9r15-001..360`
- C IDs: `v9r15c-001..360`
- hold/provenance base: D-105 `821d72727e502fa17a4fa7d33df5267e8a61d4de`
- same TEN exclusion sets exactly; no 11th exclusion
- rubric/counts/role semantics/retrieval/evaluation semantics unchanged

## D-105 repair

The final `freeze_plan_v9r15.py` production path now defines and uses:

- `build_parser()`
- `require_smoke_binding(args)`
- `smoke_auditor_argv(args)`
- `lifesmoke_auditor_argv(args)`

The production parser explicitly registers all first-class smoke proof inputs, including the missing D-105 field:

`--lifesmoke-cwd`

Smoke A binds agent/cwd/session/wrapper inputs; Smoke B binds agent/cwd/session/wrapper inputs. `main()` uses the same parser/binding functions and passes the exact Smoke-B cwd to `audit_lifecycle_smoke.py` and later lock proof fields.

No test-only branch or production bypass was added.

## Permanent pre-smoke regression

New permanent mechanic:

`test_freeze_binding_regression.py`

Final Web rerun: **`FREEZE_BINDING_PASS`, 66 checks.**

It proves, without model/Paseo launch:

1. production parser registers the complete real-freeze invocation shape, including `--lifesmoke-cwd`;
2. complete A/B sentinel values parse exactly;
3. missing A or B cwd fails closed rc3;
4. production `main()` uses the same parser/binding/auditor-argv functions;
5. immutable v9r14 freeze bytes are SHA-pinned and fail the new contract (`--help` omits the field; complete shape is argparse rc2);
6. a disposable ordinary dry-freeze accepts the full CLI shape and reaches audit stage without creating real-builder locks;
7. stronger Web-requested runtime proof calls the actual production `main()` against a disposable builder while only `subprocess.run` is monkeypatched externally with synthetic contract-valid auditor PASS responses;
8. that runtime traversal captures exactly two auditor calls in A→B order, with byte-exact A/B argv including Smoke-B cwd;
9. disposable `PLAN_LOCK.json` binds the exact eight sentinel A/B agent/cwd/session/wrapper values and expected session hashes/line counts;
10. disposable artifacts are removed and the real builder remains lock-free.

The stronger runtime traversal was added in the same D-106 logical stage before any model smoke was consumed.

## Independent Web final-byte validation

Web independently reran the final battery:

- freeze binding: `FREEZE_BINDING_PASS` — 66 checks
- lifecycle smoke contract: `LIFECYCLE_CONTRACT_PASS` — 53 checks
- launcher reachability: `REACHABILITY_PASS` — 87 checks
- role tools: `ROLE_TESTS_PASS` — 166 checks
- completion gate: `GATE_TESTS_PASS`
- TEN gates: 45 pairwise comparisons, overlap 0; counts `180/250/248/273/273/360/360/365/360/360`
- Phase-C confinement: `CONFINEMENT_TESTS_PASS` — 192 checks
- `compileall` / targeted `py_compile`: PASS
- Bun role-tools probe: `PROBE_PASS`
- Bun Phase-C probe: `PROBE_PASS`
- TypeScript `tsc --noEmit`: PASS
- plan mechanics SHA map: **53/53 exact**

The freeze-binding runtime test's disposable successful freeze produced plan SHA `83307b659b53b4340aecc68b259de63c311288b0f6fa7064dfe3799c1b02f6e3`, matching the real final plan bytes, while all freeze artifacts remained confined to the disposable copy.

## Final key SHA256

- `GENERATION_PLAN.json` `83307b659b53b4340aecc68b259de63c311288b0f6fa7064dfe3799c1b02f6e3`
- `freeze_plan_v9r15.py` `81197047e943801edd744c0baebbf8103f0ed6dbb911df1b1354d0135630cbdf`
- `test_freeze_binding_regression.py` `a7641001fd7462c8615fa2ee47649e59908e568018afc72733092828904d8e28`
- `launch_top_level_paseo.py` `7719ecc7c3875055cafb8b288df18f7654f07011127852a53cc53006a90176fb`
- `role_omp_wrapper.py` `2051279a84a20b329e573e9e50d2efc3c2d5962ed114b135bd6398ecc5b71c53`
- `role_fs_helper.py` `ec6a838a27dfc44f348cf6f7b7ce65ae4ae23c23c95c945e056eea7d68a969d6`
- `coord_wrapper_tpl/phasec_role_ext.ts` `6b5a1f426752e403a7ba96585b263cedd0bb9aea3646779a37c6a4bad3e62534`
- `run_lifecycle_smoke.py` `32149e859823a9f71841dffc2183932a94d2cd0a8c627a34d32b8f3355f1adad`
- `audit_lifecycle_smoke.py` `6a43e2cb8bdf9323eb3a5b4135883ecaa6a1816497b867268fb6a7589775e2ef`
- `smoke_lifecycle_prompt.txt` `9f29ecbb6dbae10705e98a4da6753de2acc6d4a811585ae5bc0b854aad5c7350`
- `role_completion_gate.py` `90f7a95a0f3a2d6d67e0620496945e4415f58300fc80e4f2e657f2a7a1fb1698`
- `input/EXCLUSION_INPUTS.json` `62913a9a94337f23860e0bde18c717c349ecb9869f9a46ba52f4323853775fb2`
- `coord_wrapper_tpl/phasec_coordinator_ext.ts` `cdae659da7616b2225837e8a6778f12006d490a32ceb79dbb4113272c800e1f7`

## Predecessor comparison / semantic scope

v9r14 has 65 files; v9r15 has 66. All 65 predecessor files pair after the expected freeze/carry script rename; only `test_freeze_binding_regression.py` is new.

After v9r15→v9r14 identity/date normalization, only eight paired files remain non-identical:

- `GENERATION_PLAN.json`
- `carry_exclusions_v9r15.py`
- `coord_wrapper_tpl/coord_omp_wrapper.py`
- `freeze_plan_v9r15.py`
- `input/EXCLUSION_INPUTS.json`
- `role_fs_helper.py`
- `role_omp_wrapper.py`
- `test_phasec_confinement.py`

Those deltas are limited to D-105 lineage/provenance, complete freeze CLI binding, manifest description, old-token deny lists, wrapper extension SHA repins, and regression guards. Core semantic files including `RUBRIC.json`, `search_snapshot.py`, `check_anchor.py`, `validate_pool.py`, `merge_chunks.py`, `merge_raw_ab.py`, `freeze_raw_ab.py`, `build_agreement.py`, `merge_c.py`, `run_selector.py`, and `role_completion_gate.py` are byte-equivalent after identity normalization.

## Immutability and forbidden-state checks

v9r14 predecessor evidence remains unchanged, including:

- `freeze_plan_v9r14.py` SHA `543020bd584604cba27fbe4acf0b7825060b2229b106bfaa18eb9e7691868144`
- Smoke A session SHA `f6b0859ae06b2bfc6b11e75def452b0c7808064a9d33dbfa1862d68190019de0`
- Smoke B session SHA `4307a8d737cf84636db72c946d5d61607c86786fa883734cb361e6b2b52057c3`

Final v9r15 real builder has none of:

- `PLAN_LOCK.json`
- `FROZEN_HASHES.json`
- `phasec_driver.run.lock`
- `source_truth.jsonl`
- `source_truth_meta.json`
- `evalset.jsonl`
- `out/`
- candidate/reviewer/C/selector runtime outputs

No v9r15 smoke roots/session directories existed at final PRE-SMOKE review. No v9r15 branch/tag/worktree exists. Repo remained at D-105, clean, production diff 0, audit/canonical boundaries unchanged throughout construction and review.

## Next gate

**NEXT: exactly one v9r15 Smoke A on these final bytes. Only if A returns frozen-auditor PASS may exactly one Smoke B run.**

If either smoke fails, v9r15 closes CONTRACT_INVALID_GENERATION with no retry/repair. Real freeze and Phase C remain forbidden until both one-shot smokes pass and a later freeze gate is independently approved.
