# Retrieval v3 D-166 — generation-v9r29 PRE-SMOKE WEB PASS

Date: 2026-09-10 (KST)
Stage: fresh-successor private-builder construction + same-stage transport/confinement repair + independent Web final-byte PRE-SMOKE review
Generation: `retrieval-v3-dev-generation-v9r29`
Private builder: `C:\Users\joji\Documents\programming\bc-v3-dev-v2-builder-20260910-v9r29`
D-165 closure base commit: `4fe7df60ef4c829d4024c35218d8f7c37a2b80ad` (`2026-09-09T18:20:12+00:00`)

## Verdict

**D-166 / v9r29 PRE-SMOKE: FINAL WEB PASS for static/PRE-SMOKE only. NOT D-167 Smoke-A authorization. STOP before Smoke A.**

V9r29 is a fresh D-166 successor to immutable terminal D-165/v9r28. D-165 remains `CONTRACT_INVALID_GENERATION / HARD HOLD / NON-RESUMABLE`: its single authorized target used an absolute `C:/.../run_smoke_a_once.py` script path, the executor transport produced `//C:/...`, and Python returned rc2 before opening the runner. Therefore v9r28 produced zero Phase-C Author/query rows and zero Smoke-A coordinator/model output. Exactly the existing FIFTEEN query-fingerprint exclusion sets carry forward; there is no sixteenth set.

The D-166 repair is narrow and mechanical. It separates the future Core executor workdir from the Smoke runtime cwd, uses only the relative script basename in the future executor command, repins current generation identity/provenance from v9r28 to v9r29, and fail-closes a live/nonterminal Core result without any same-executor follow-up. Retrieval/evaluation semantics, rubric, quotas/reserve/location, A/B-all-360, C-every-360, agreement/selector, failed-generation freshness semantics, protected-data boundaries, and one-shot terminality remain unchanged.

No D-167 Smoke A/B, model, Paseo/OMP execution, real freeze, source-truth snapshot, Phase C, semantic Author/Reviewer/C role, selector, protected dev-v2 evaluation, holdout evaluation, production change, or canonical audit append occurred in D-166.

## Reconciled repo base before durable record

- branch `codex/retrieval-v3-user-search-quality`
- HEAD = upstream = direct origin = `4fe7df60ef4c829d4024c35218d8f7c37a2b80ad`
- working tree clean; `git diff --check` PASS
- canonical `eval/retrieval-v3/audit/events.jsonl` remains 4 events, SHA256 `90cfb54df614bc59e01551943436fdafc3cd5cac121b071742acbb2fb604c506`; no D-166 audit append
- protected `eval/retrieval-v3/dev/`, `eval/retrieval-v3/dev-v2/`, `eval/retrieval-v3/holdout/` absent
- `ml-service/` worktree diff = 0
- immutable v9r28 predecessor key verification: 8/8 exact
- final v9r29 builder state before this durable record: no runtime/freeze/source artifacts; Smoke runtime root absent; after review-hygiene cleanup cache0/pyc0

## Fresh v9r29 identity and final hashes

- plan version `retrieval-v3-dev-generation-v9r29`
- hold base D-165 commit `4fe7df60ef4c829d4024c35218d8f7c37a2b80ad`, hold time `2026-09-09T18:20:12+00:00`
- `GENERATION_PLAN.json` SHA256 `d1ed3eda0f64a1570d71423604499d90f5af690dbde39590bbeb19883efd751a`
- `RUBRIC.json` SHA256 `08e598a449d2507d94b8e2dcf633789701c2ad5f9c0f741e55c38ca29bab02fe`
- `input/EXCLUSION_INPUTS.json` SHA256 `b3c4f23793ef7b8693ff72c8388fd93727e81db39e0959a7417a16b6ca97b7e2`
- `freeze_plan_v9r29.py` SHA256 `da1a64768bef79f30983d43587d22a093d186b8fbcdd806283638a02f72374db`
- `carry_exclusions_v9r29.py` SHA256 `9538759481f2467c2b01e96e259ef84a206feb089d7d399b3838a4f595056a47`
- `role_fs_helper.py` SHA256 `3a0f0fd67be66864c10975228fe3e9643656604adebe8e6e801dadc4aa827a16`
- `run_smoke_a_once.py` SHA256 `b5439f64243fd02e60c475d5726659eab05fceb200df47dfa46d746d0a71b6b9`
- `test_role_tools.py` SHA256 `b5fb3b9d4e561b1ec84c24bb07f15373ebafdf8dc9efb389c1181ef386fc71b2`
- `test_phasec_confinement.py` SHA256 `8029d7540a1fd259387f119a742bd10951ca0438ccc80909d435959584426a9e`
- `test_freeze_binding_regression.py` SHA256 `dd3ea6fccf79c11810c26fe8415599f90aab741f6b7b92e118b655fba3131fa8`
- `GENERATION_PLAN.author_isolation.mechanics_shas`: 69/69 exact disk bytes, missing 0, mismatch 0
- freshness exclusions: exactly FIFTEEN sets, 105 pairwise comparisons, overlap 0; no sixteenth set

## Frozen future D-167 executor transport

The future D-167 Smoke-A process shape is frozen to exactly:

- tool: `Chat_On_Steroids_Core.exec_command`
- executor workdir: `/programming/bc-v3-dev-v2-builder-20260910-v9r29`
- scalar `cmd`: `python -B run_smoke_a_once.py`
- `yield_time_ms=30000`
- title: `D167 v9r29 Smoke A`
- runtime cwd remains a separate concept: `C:\Users\joji\bc-v3-v9r29-coord-smoke-20260910\cwd`

`cmds`, shell `cd`/composition, absolute or mapped script paths, `./run_smoke_a_once.py`, wrappers, and extra runner arguments are forbidden. If the sole future Core call returns a live session or any other nonterminal result, D-167 is consumed/fail-closed for that executor: no `write_stdin` and no second executor tool call; later Web may inspect resulting state read-only.

A harmless same-name stub proof used the exact future executor workdir + relative-basename command shape and returned `D166_RELATIVE_TRANSPORT_OK`; the real runner was restored byte-for-byte before final hashing and testing. This proof did not execute Smoke/model/Paseo/OMP/runtime work and is not D-167 authorization.

## Same-stage Web-found old-token blocker and repair

The first independent D-166 transport review found a real final-byte blocker: operative plan/freeze text claimed old-builder filesystem/provenance denial through v9r28, but production `role_fs_helper.py` `OLD_TOKENS` still ended at v9r27. That mismatch was a HARD HOLD until repaired.

The same D-166 implementation executor extended the production helper to all seven required v9r28 predecessor families: `v9r28`, `v3g9r28`, `v9r28c`, `20260910-v9r28`, `bc-v9r28`, `bc-v3-v9r28`, and `bc-v3-dev-v2-builder-20260910-v9r28`. Permanent role/confinement/binding regressions prove those tokens are denied on filesystem/provenance paths while semantic search/get-policy/anchor strings remain unaffected merely because they contain predecessor text. Operative plan wording now truthfully states `old-builder tokens v9r6..v9r28 denied on filesystem/provenance paths`.

## Final executor validation on corrected bytes

All checks below were non-model/static/disposable where applicable:

- syntax compile: 51/51
- D149 carry: 358 unique / 360 source rows / 2 duplicate groups
- D150 retryable: 7
- D156 reviewer-resource retryable: 9
- FIFTEEN: 15 sets / 105 pairs / overlap 0
- freeze binding: 120
- freeze rerun rejection: 66
- reachability: 87
- lifecycle: 53
- one-shot terminality: 24/24
- Smoke-once runner regression: 68
- Paseo CLI static gate: 64
- confinement: 253
- registry scan: 37
- completion/gate suite: PASS
- role tools: 267
- preflight: 36
- slot/location: 6 positive / 5 negative
- staging exact set: 41
- mechanics: 69/69 exact
- deterministic disposable plan/manifest reproduction: identical to the canonical final plan/manifest

## Independent final-byte review and cache hygiene

The independent final reviewer read the corrected final bytes and returned first line exactly **`FINAL PRE-SMOKE PASS`**, with no blocker and no edits. It independently verified the exact D-167 transport pins, runner mechanics, D-166/D-165 provenance, v9r28 seven-family path denial plus semantic-string allowance, all reported primary hashes, mechanics 69/69, runtime/freeze artifact absence, and Smoke-root absence. The review performed no Smoke, model, Paseo, protected-data, or runtime execution.

Review/static work left exactly two builder-local `__pycache__` directories containing 51 `.pyc` files. After the formal review closed, only those two known cache directories were removed. Post-cleanup verification used PowerShell/.NET only — no Python was run after cleanup — and proved cache0/pyc0, all ten final v9r29 primary hashes above unchanged, mechanics 69/69 exact, builder runtime artifacts0, v9r29 Smoke root absent, and immutable v9r28 key hashes 8/8 unchanged.

## Durable record scope and final boundary

This closure records only this D-166 document plus append-only D-166 entries in `memory/DECISIONS.md` and `memory/SESSION-LOG.md`. It does not alter the private builder except the already-described cache hygiene and does not mutate runtime, canonical audit, `ml-service`, protected data, or production state.

**D-166 PRE-SMOKE WEB PASS ONLY; NOT D-167 Smoke-A authorization. STOP before Smoke A.**

A next, separately and explicitly authorized user continuation may authorize only a fresh D-167 Smoke-A prelaunch gate and, if that gate still passes on these exact final bytes, exactly one execution of the frozen Core workdir + scalar relative-basename command above. Before any new OMP root/plan execution, actual global and project effective OMP config must be reconciled. Smoke B, real freeze, source truth, Phase C, semantic generation roles, protected dev-v2, holdout, production, and canonical audit append remain prohibited until their own later gates.
