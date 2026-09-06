# Retrieval v3 D-099 generation-v9r12 PRE-SMOKE Web PASS (2026-09-06)

Fresh successor-generation pre-smoke closure after D-097/D-098 closed v9r11 as
CONTRACT_INVALID_GENERATION. This record is plaintext-free: identities, paths,
hashes, counts, test verdicts, and structural mechanics only. No protected
query/gold plaintext is recorded.

## 0. Reconciled base and stage boundary

- Repo `C:\Users\joji\Documents\취준자료\project-repos\benefit-compass`, branch
  `codex/retrieval-v3-user-search-quality`, base HEAD
  `70216da60db246a4143291da136479740a59682b` (D-098); local = upstream =
  direct remote; working tree clean; `git diff --check` PASS; production
  `ml-service/` diff from `5327661445c37191a3fd61db195f3af4d2cf893a` = 0.
- OMP `18.1.5`; effective modelRoles default/plan
  `opencode-go/muse-spark-1.3-contributor:xhigh`.
- Audit `eval/retrieval-v3/audit/events.jsonl`: exactly 4 events, SHA256
  `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`.
- Canonical `eval/retrieval-v3/result`, `dev`, `holdout`, and `dev-v2` absent.
- Latest durable SSOT before this stage was D-098. No D-099 artifact existed.
- This logical stage authorizes only fresh successor PRE-SMOKE builder work and
  Web independent review. It does not authorize Smoke A/B, real freeze, Phase C,
  source-truth snapshot, semantic roles, selector, protected evaluation,
  holdout, or production retrieval changes.

## 1. Executor and fresh successor identity

- Single Paseo/OMP executor root:
  `076e517b-7b3d-41c0-aaf3-19bd169de2c6`, title
  `D099-v9r12-presmoke-builder`, repo cwd, model
  `opencode-go/muse-spark-1.3-contributor`, thinking `xhigh`, ParentAgentId
  `null`, final status `idle`. No task/hub/subagents were spawned.
- Fresh builder was absent before write and then created at
  `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260906-v9r12`.
- Identity is fresh and coherent:
  - generation `retrieval-v3-dev-generation-v9r12`
  - seed `benefit-compass-retrieval-v3-dev-v2-generation-v9r12-2026-09-06`
  - candidate IDs `v3g9r12-001..360`
  - C IDs `v9r12c-001..360`
  - renamed mechanics `carry_exclusions_v9r12.py` and
    `freeze_plan_v9r12.py`.
- Final builder inventory: 64 files; no `__pycache__`/`.pyc` after cleanup.
- Same TEN fingerprint exclusion sets remain operative; no 11th set was added.
  Final independent TEN re-run checked all 45 pairs with overlap 0 and counts
  dev-v1 180 / holdout 250 / history 248 / D070 273 / D071 273 / D072 360 /
  D074 360 / D076 365 / D082 360 / D086 360.

## 2. Narrow generic-role launcher repair

D-097 established that v9r11 computed a wrapper PATH but did not propagate it,
and also did not pass `OMP_WRAPPER_LOG` although the role wrapper requires it
and `sanitized_env()` removes ambient `OMP_*` keys.

Final v9r12 `launch_top_level_paseo.py` now explicitly passes the same repaired
environment for every role kind (`author1`, `author2`, `reviewerA`, `reviewerB`,
`c`, `lifecycle_smoke`):

- `--env PATH=<staging>\wrapper_bin;<original PATH>`
- `--env OMP_WRAPPER_LOG=<staging>\wrapper_invocation.log`
- `--env BC_ROLE_STAGING=<staging>`
- `--env BC_ROLE_MODE=role`
- `--env BC_ROLE_KIND=<exact role kind>`

The launcher still sanitizes inherited `PASEO_*`/`OMP_*`, uses the same genuine
top-level Paseo provider/model/thinking/cwd flow, and preserves the existing
exact-session fallback provenance verification. The role wrapper remains
`--tools=todo -e <frozen v9r12 role extension> --no-extensions --no-skills
--no-rules`, with built-in read/eval/bash/etc. unavailable to semantic roles.

The role extension/helper paths and SHA pins were migrated to the fresh v9r12
builder. Coordinator wrapper/extension pins were likewise re-bound to final
v9r12 bytes.

## 3. Permanent regression and Web independent verification

New permanent `test_launcher_reachability.py` performs command capture with a
mocked subprocess and synthetic staging only; it does not launch Paseo/OMP.
It verifies:

1. the computed wrapper PATH is actually present in the Paseo command;
2. exact per-staging `OMP_WRAPPER_LOG` is passed;
3. all three `BC_ROLE_*` bindings are passed;
4. ambient `PASEO_*`/`OMP_*` are not relied upon;
5. all six role kinds share the repaired environment sequence; and
6. read-only v9r11 source has the old dead PATH computation and lacks both the
   PATH propagation and wrapper-log propagation, so v9r11 would fail this gate.

Web independently re-ran the final-byte non-model battery:

- launcher reachability: `REACHABILITY_PASS`, 87 checks, 0 failures;
- role completion gate: `GATE_TESTS_PASS`;
- TEN-set gate: 45 pairs / overlap 0 / exact counts above;
- role tools: `ROLE_TESTS_PASS`, 157 checks;
- Phase-C confinement: `CONFINEMENT_TESTS_PASS`, 182 checks. Its intermediate
  CONTRACT_INVALID outputs are intentional negative cases proving fail-closed
  behavior.
- `GENERATION_PLAN.json.author_isolation.mechanics_shas`: 48 entries, final disk
  comparison 48/48 match, zero missing/mismatch.
- normalized v9r12->v9r11 comparison across 63 paired files left only eight
  non-identity-equivalent files, all explained by the authorized repair or
  successor lineage: carry script, freeze script, plan, generic launcher, role
  wrapper SHA repin, confinement old-token deny list, coordinator wrapper SHA
  repin, and exclusion manifest description. No unintended evaluation-semantic
  delta was found.
- 18 carried rubric/fingerprint/support files were compared to v9r11: 17 are
  byte-identical; only `input/EXCLUSION_INPUTS.json` differs intentionally in
  successor lineage/manifest description while the TEN input fingerprints and
  their pinned hashes/counts remain unchanged.

During executor construction two fingerprint files were briefly line-ending
normalized; their SHA drift was detected before finalization and both were
restored byte-identical to v9r11. A freeze-script identity-migration omission
was also detected and repaired before final binding. Neither incident survives
in final bytes; final mechanics and carried-input checks above are authoritative.

Web test re-runs created only disposable `__pycache__` and a synthetic
`C:\Users\joji\v9r12_live_tmp_<pid>` confinement fixture. The fixture was tied
directly to `test_phasec_confinement.py` (`Path.home()/v9r12_live_tmp_<pid>`),
contained only synthetic `live_a/out` plus a two-byte `slots.json`, and was
removed after exact-path verification. Final v9r12 home-temp scan is empty and
builder pycache count is 0. No smoke/session evidence was deleted.

## 4. Final key bytes

Final v9r12 SHA256 values, independently re-hashed after Web tests/cleanup:

- `GENERATION_PLAN.json`
  `ce4eef9542f89e24235ee1e7dc19a1f16796301599f7f4df614ad8b086a6aa56`
- `launch_top_level_paseo.py`
  `bb9aaef95d60a74d5c215b8f2351ae2c18c32f5b55fc92ebcc8b2edbf3908af6`
- `role_omp_wrapper.py`
  `3d2ce2362a388ea96452933654b651550ffe878364b79d0cbb00190e6498a1dc`
- `coord_wrapper_tpl/phasec_role_ext.ts`
  `ac8c976f4ba21eacd702b6642f0a6fada25180325112528c98f25cba28da5280`
- `run_lifecycle_smoke.py`
  `dd84ca9bd6af1ac071740d6a7c2bf987fec297d69405cabc2d38fffe608fc67c`
- `audit_lifecycle_smoke.py`
  `48174d27f9e06cb8cb5cd1eb577a78ac926c100404398c7628229d2bb480bf1a`
- `role_completion_gate.py`
  `6c445620dcbc5b99402580292fd3f69c5755ede881a738f76493c40615853ea2`
- `test_launcher_reachability.py`
  `1464a992ee90c8b345810c01952ef17d2475fca0846ad7a2f58dbbbe292d00f3`
- `freeze_plan_v9r12.py`
  `f8ea65e722683cf6b0f784b32b317850b184ce214d4352b0f8f70be348b03b50`
- `carry_exclusions_v9r12.py`
  `cc9c0824c3ba03b883411ef82ab9638be98d3714f702bee98ea00cff443f9045`

The nine v9r11 immutable key files were re-hashed after the entire D-099 build
and Web review and all still match their D-097 expected SHAs. v9r11 remains
unchanged failure evidence.

## 5. No-real-freeze / no-execution proof and verdict

Final real v9r12 builder has none of:

- `PLAN_LOCK.json`
- `FROZEN_HASHES.json`
- `phasec_driver.run.lock`
- real `source_truth.jsonl` / `source_truth_meta.json`
- candidate/reviewer/C/selector runtime outputs
- `evalset.jsonl`.

D-099 executor transcript was structurally inspected for command-like launch
patterns. Its OMP uses were version/config queries, source inspection, compile,
and non-model tests. No `paseo run`, lifecycle smoke runner execution, Phase-C
execute, or semantic-role launch occurred. Therefore Smoke A/B remain unconsumed
for v9r12.

**WEB PRE-SMOKE VERDICT: PASS.**

Generation-v9r12 is approved only to the next smoke gate on the exact final
bytes above. This is not a real freeze and not Phase C approval. No successor
byte repair is permitted after consuming a smoke result under the one-shot rule;
a smoke contract failure must close v9r12 rather than be repaired in-place.

Next logical stage may run exactly one coordinator Smoke A on these bytes and,
only if A passes, exactly one neutral lifecycle Smoke B. No retry, no second
launch per smoke, no Phase C, source truth, protected evaluation, or production
change in that smoke stage.
