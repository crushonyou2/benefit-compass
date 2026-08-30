# Retrieval v2 Cycle3 — Pre-registration Provenance Addendum (INFRA REPAIR v2)

> **Type:** Provenance clarification addendum — does NOT modify `eval/retrieval-v2/cycle3/prereg-v1.json` or `docs/RETRIEVAL_V2_CYCLE3_PREREG.md` candidate semantics. Original files remain immutable at bootstrap freeze.

## 1. Nominal vs Canonical Time

- `prereg-v1.json:created_at = "2026-08-30T00:00:00Z"` is a **nominal placeholder** (midnight UTC of bootstrap day). It was set at bootstrap file creation and intentionally left unchanged to preserve file immutability.
- **Canonical freeze time** is the bootstrap Git commit timestamp:
  - commit `e4e56198ba3faef7ae687e356e41bf2d7543c198`
  - author `2026-08-30T18:34:01+09:00` / committer `2026-08-30T18:34:01+09:00` (`1788082441` epoch)
  - UTC `2026-08-30T09:34:01Z`
  - Verified: `git cat-file -p e4e56198ba3faef7ae687e356e41bf2d7543c198` + `git log -1 --format=%aI|%cI`

All candidate IDs, K values, SQL semantics, selection predicates, max=3, and D-003/D-004/D-007/D-011 were frozen at this commit. No post-bootstrap addition/change/rerun is allowed.

## 2. File SHA256 (re-verified via Git/filesystem)

- `eval/retrieval-v2/cycle3/prereg-v1.json`
  - `SHA256 (lower)` `18b6c997eb71a8cdff36d84ff46b5bbb6b699874ff6d0fccd18636f00268e156`
  - `SHA256 (upper)` `18B6C997EB71A8CDFF36D84FF46B5BBB6B699874FF6D0FCCD18636F00268E156`
  - Basis: file bytes as stored (LF, UTF-8, 10534 bytes)
  - Verification: `sha256sum eval/retrieval-v2/cycle3/prereg-v1.json` + `python -c "hashlib.sha256(read_bytes()).hexdigest()"`
  - **Immutable:** Not modified in infra-repair; provenance-only addendum.

## 3. Tag Object / Peeled Commit (re-verified via Git)

- Tag `retrieval-v2-cycle3-start-v1`
  - object `2a30e8d371b9892f29ebcc21a81ab48ed9614378` (type `tag`)
  - peeled commit `e4e56198ba3faef7ae687e356e41bf2d7543c198`
  - tagger `crushonyou2 <jigwan.joe@gmail.com> 1788082480 +0900` (`2026-08-30T18:34:40+09:00`, UTC `09:34:40Z`)
  - Verification: `git rev-parse retrieval-v2-cycle3-start-v1` → tag object, `git rev-parse retrieval-v2-cycle3-start-v1^{commit}` → peeled commit, `git cat-file -p <object>`
  - **Immutable:** Not moved or deleted in infra-repair; `retrieval-v2-cycle3-start-v1` remains the bootstrap anchor. Infra-repair adds separate tag `retrieval-v2-cycle3-infra-v2`.

## 4. Machine-readable attestation

- `eval/retrieval-v2/cycle3/prereg-v1.provenance.json` — structured JSON with all fields above.

## 5. Infra-repair tag

- New annotated tag `retrieval-v2-cycle3-infra-v2` will point to the single infra-repair commit on `codex/retrieval-v2-cycle3-start` after bootstrap. It does NOT replace bootstrap tag.

## 6. Candidate semantics immutability

Bootstrap prereg candidate semantics are **IMMUTABLE** per D-011 and bootstrap spec:
- Candidate IDs `c3e1-vector-pool-128` / `c3e2-vector-pool-256` / `c3e3-vector-pool-512`
- Pool K `128 / 256 / 512`, final N `30`
- SQL template (nearest → vector_pool K → lexical on K only → youth/lexical ordering → LIMIT 30)
- Selection predicates, tie-break, max=3
- D-003 / D-004 / D-007 / D-011 contracts

Infra-repair modifies only `cycle3_audit.py` / `cycle3_fingerprint.py` / tests / docs provenance — no candidate selection or SQL semantics change, no `prereg-v1.json` content edit.
