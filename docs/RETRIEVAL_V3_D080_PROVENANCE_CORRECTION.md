# D-080 provenance correction — author staging roots 2 (2026-09-05)

Append-only SAME-STAGE correction. D-080 entry, D-080 SESSION-LOG entry, and `docs/RETRIEVAL_V3_D080_CONTRACT_INVALID_GENERATION.md` preserved verbatim; this doc corrects only the `author_staging_roots_created 0` count and its gate wording.

- Original private `D080_CONTRACT_INVALID_SUMMARY.json` SHA256 `e4c60e14b236d2fb7851f70737534a2fb44ecd1669d485dfa5e16d66d7b7569e` (3769 bytes) preserved byte-for-byte verbatim; its verdict and hard-gate facts are correct, but its staging-roots count is superseded.
- Actual filesystem evidence (observed this stage, names only): exactly TWO disjoint author staging roots under `C:/Users/joji/Documents/programming/bc-v8-phasec-staging-20260905/b41971bfe472498889c9d07e651965ec` — `author1-3bc4401fb2524de586859ec08900efe0` + `author2-fd1bcb43db8a4267ab0ddffaa49fa23d`. Materialized before launch (user-authoritative); each holds role-local snapshot/slots/helpers only (`RUBRIC.json`, `author_brief.md`, `check_anchor.py`, `search_snapshot.py`, `slots.json`, `source_truth.jsonl`, `source_truth_meta.json`, `input/` 9 fingerprint-only files); both `out/` empty — no author candidate outputs.
- Correction record: private `D080_CONTRACT_INVALID_SUMMARY_CORRECTION.json` SHA256 `9813f858854e3ec3d128e4b550cc7178267c35ea9d517a83e21cb61597a88618` (1587 bytes), plaintext-free, supersedes ONLY the staging-roots count/wording.
- Unchanged: valid author agents 0 (2 intended, both invalid); candidate/query rows 0; A/B/C/selector/protected actions 0; audit appends 0; result none. D-080 verdict CONTRACT_INVALID_GENERATION unchanged.
- No D-081/v9. No builder plan/mechanics/source/candidate mutation; no author resume; no git object recovery; no Desktop/browser/computer in this correction.
