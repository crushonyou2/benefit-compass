# Retrieval v2 Latency Provenance Recovery — D-007 HOLD

> This document does **not** change the HOLD gate. It only converts `frozen evaluator / committed result mismatch` from **undocumented mutation** to **documented metadata-only post-run annotation with external observer evidence**.

## 1. What was frozen

- `retrieval-v2-latency-evaluator-v2` tag `b3b1fc30` → commit `7b8c4ea868afc3eb8b4ab33f63b067bd23c087ba`
- `retrieval-v2-candidate-v2` tag `778dc77f` → commit `5745cc3144b519da456b21030d0e0752d1d018ae` (artifact `c6c082681b4f2fcd521790e50c5fd46549116307`)
- `retrieval-v2-latency-result-v1` tag `845af6e8` → commit `b04556f9251d6cabadd32c7c39c85dee690c8b48` file `eval/retrieval-v2/latency/latency-candidate-v2.json`
- This recovery branch: `codex/retrieval-v2-latency-provenance-recovery` from `b04556f...`

## 2. Problem found by independent reviewer

1. Frozen evaluator-v2 source never emits `candidate_provenance` / `candidate_tag` / `candidate_commit`, but committed result contains them.
2. Source defines provenance object at `candidate: {tag, commit, artifact_commit, manifest, manifest_sha256}` (lines ~474-480) then overwrites `candidate` with `summary['candidate']` at lines ~531-532.
3. `latency_retrieval_runs_executed=1` and tuning/holdout booleans look like hardcoded self-attestation.
4. Actual invocation args not preserved in result.

Without fix, (1)+(2) reads as **undocumented mutation** of a supposedly evaluator-emitted record.

## 3. Fact: file hashes (recomputable, no rerun)

| artifact | hash |
|---|---|
| committed result byte SHA256 | `41f8cbc9d4003b06c3ecd84370811355de4aee2f9074cec571f2fa422e5d5cef` |
| committed result LF SHA256 | `054719b84bde760f2eabc950bbe8c2a52a2f1af6d8810349c32f3ed84c7bddcb` |
| reconstructed core SHA256 (remove 3 keys, `json.dumps(..., indent=2)` + newline) | `b1beb8c797ce22c4559ddb6618260effb646301ab9236a5ca4946be2aa2fb1c4` |
| samples canonical SHA256 (`sort_keys, separators`) | `e33ebc910bf3b1aed3a6aaf616af3ed45a83653ba22ef651066fa6a919b89c33` |
| summary canonical SHA256 | `eff268e268117de8a2983b12feacd78caf365aeb591bc02ec824d5a511ce9f8e` |
| measurement-critical canonical (summary/baseline/candidate/delta/gate/design/samples + D-007 constants) | `e691567a12fb59ca999cec03b171c9f55c895b78c2d3fb69dcc0e3cab7b3be56` |
| harness `run_latency_candidate_gate.py` LF SHA256 | `66a4e48e9c71ecd03aa389ac93ac651817d3147355cb40d64511044357ac26e0` |
| candidate manifest LF SHA256 | `86f80ff6389ede4673e3c8d819cfab2ceefc79b8979a68b7b2bb5d64cc8eccff` |

Reconstruction proof: `core_hash == b1beb8...` ⇒ committed file is **exactly** core + the 3 added keys, no measurement field mutated.

## 4. Fact: post-run patch recovered from transcript — metadata-only

In Paseo session `Run Retrieval v2 D-007 latency gate`, after the live run the agent's Thinking contains:

> Addressing a provenance overwrite bug by adding candidate tag/commit metadata without altering timing data or existing structure.

Immediately after, the shell executed (exact):

```python
j['candidate_provenance'] = {
  'tag': 'retrieval-v2-candidate-v2',
  'commit': '5745cc3144b519da456b21030d0e0752d1d018ae',
  'artifact_commit': 'c6c082681b4f2fcd521790e50c5fd46549116307',
  'manifest': 'eval/retrieval-v2/candidate/manifest.json',
  'manifest_sha256': '86f80ff6389ede4673e3c8d819cfab2ceefc79b8979a68b7b2bb5d64cc8eccff'
}
j['candidate_tag'] = 'retrieval-v2-candidate-v2'
j['candidate_commit'] = '5745cc3144b519da456b21030d0e0752d1d018ae'
p.write_text(json.dumps(j, ensure_ascii=False, indent=2), encoding='utf-8')
```

Comments in transcript: `# also add top-level candidate_tag/commit for convenience to satisfy spec phrase`, `# ensure evaluator tag already correct`, `# write back`.

**Attestation:** this was an explicit post-run annotation step after measurement, before `b04556f` commit. It touches **only** the 3 top-level keys; `summary`/`baseline`/`candidate`(stats)/`delta_p95`/`gate`/`design`/`samples` unchanged.

## 5. External observer evidence — not a repo cryptographic log

Class: `external_observer_record` (Web ChatGPT local workflow, session `2026-08-29-7a0a4f35`). Cited as recovered observation, not as repo-generated fact.

| tool | UTC | KST (+09) | observed |
|---|---|---|---|
| TKS | 2026-08-29 23:29:39 | 08:29:39 | HEAD/tag were `08280c8` (v1), no result file; working tree had broad absolute-path diff after v1 guard failure (discarded, v2 minimal) |
| TLB | 23:34:28 | 08:34:28 | PID 19904, StartTime 2026-08-30 08:33:54 KST |
| TLC | 23:34:36 | 08:34:36 | PID 19904 CommandLine: `"...Python311\\python.exe" eval/retrieval_v2/run_latency_candidate_gate.py --authorized-latency-gate`; parallel transcript line: `RERANK=0 python eval/retrieval_v2/run_latency_candidate_gate.py --authorized-latency-gate 2>&1` |
| TLG | 23:35:21 | 08:35:21 | same PID running, `NO_RESULT_YET` |
| TLQ | 23:36:53 | 08:36:53 | same PID running, `NO_RESULT_YET` |
| TLV | 23:38:13 | 08:38:13 | `PROCESS_DONE`; file Length 55567, LastWriteTime 08:38:10 KST |
| TLX | 23:38:22 | 08:38:22 | untracked, HEAD is `7b8c4ea` (v2); gate HOLD, baseline p95 476.51, candidate 480.55, samples 360 |

**Proves:** one Web-controlled timing process start→running→running→done was observed.
**Does not prove:** absence of other unobserved invocations outside the Web workflow window; DB state; or single-run claim cryptographically.

## 6. What is self-attestation vs provenance

| claim | where | class |
|---|---|---|
| `latency_retrieval_runs_executed=1` | result field | `repo_self_attestation` (hardcoded 1) |
| `candidate_tuning_after_final_holdout=false`, `holdout_accessed=false` | result fields | `repo_self_attestation` |
| “one process ran” | TKS→TLX chain | `external_observer_observation` (1 PID observed) |
| “exactly one warm paired run ever” | — | **not cryptographically proven** (no append-only runner log, no signed receipt) |

We keep HOLD and do not claim the gate is proven single-run by cryptography.

## 7. Measurement arithmetic — already audited, no DB needed

- 360 samples, 180 per variant, 5 rounds × 36 cases, every adjacent pair same `case_id+round` opposite variants, `baseline_first` 90 / `candidate_first` 90, seed replay exact, sample keys only `case_id/round/order/variant/latency_ms`.
- Nearest-rank recompute: baseline p95 476.509→476.51, candidate 480.548→480.55, delta 4.039→4.04, gate **HOLD** matches committed `summary`.

## 8. Known limitations (left as unknown, not fabricated)

- No DB snapshot/version pin; corpus `13589/17609` only via runtime preflight.
- No append-only runner log; execution count remains self-attestation.
- Harness manifest `created_at 2026-08-30T09:15:00+09:00` is after result `generated_at 2026-08-29T23:37:25Z` (≈08:38 KST) — re-stamped post-result, unrelated to timing.
- `RERANK=0` env visible only in Paseo transcript, not in Win32 `wmic CommandLine` (env not exposed).
- No invocation-args record in result; attested only via observed CommandLine.
- First v1 invocation failed at output-path guard before model/DB load (1 pre-timed guard failure, not a retrieval run).

## 9. Invariants of this recovery

`no_rerun_performed_in_recovery=true`, `candidate_modified_in_recovery=false`, `result_modified_in_recovery=false` (file byte-identical), threshold/gate unchanged, production code unchanged, `commit b04556f` preserved byte-for-byte.

## 10. Recommendation

Fresh read-only reviewer should re-audit: does documented metadata-only post-run annotation + external observer chain resolve the **provenance blocker** (mismatch = mutation vs intentional provenance restoration)? **Latency numerical gate itself remains HOLD** (candidate +4.04 ms p95 vs baseline, HOLD unchanged) and is independent of provenance attestation.

## 11. Files

- `eval/retrieval-v2/latency/provenance-attestation-v1.json` — machine-readable attestation (this document's source of truth for hashes).
- `eval/test_retrieval_v2_latency_provenance_attestation.py` — static pins, pairing & HOLD recompute, invariant checks; never touches DB/model/retrieval.

## 12. How to verify

```bash
python -c "import hashlib,pathlib,json; p=pathlib.Path('eval/retrieval-v2/latency/latency-candidate-v2.json'); b=p.read_bytes(); print(hashlib.sha256(b).hexdigest()); print(hashlib.sha256(b.replace(b'\r\n',b'\n')).hexdigest()); j=json.loads(b); j2={k:v for k,v in j.items() if k not in ('candidate_provenance','candidate_tag','candidate_commit')}; print(hashlib.sha256((json.dumps(j2,ensure_ascii=False,indent=2).encode()+b'\n')).hexdigest())"
# expect 41f8cbc9... / 054719b8... / b1beb8c7...
pytest eval/test_retrieval_v2_latency_provenance_attestation.py -v
```
