# Retrieval v3 — User Search Quality — Bootstrap (docs/memory only)

> **Bootstrap durable record — 2026-09-01 — docs/memory only. No retrieval/DB/model/embedding/benchmark execution, no protected holdout/dev plaintext access, no production change.**
> This page bootstraps Retrieval v3 (user-search-quality) from the durable closure of Retrieval v2 Cycle3. It does not define a new evaluation contract, does not freeze datasets, and does not select a candidate.

## 1. Reconciled base (read-only before edits in this bootstrap)

| item | value | verification |
|---|---|---|
| Worktree | `C:/Users/joji/Documents/취준자료/project-repos/benefit-compass` | `git rev-parse --show-toplevel` |
| Branch | `codex/retrieval-v3-user-search-quality` | `git branch --show-current` → `codex/retrieval-v3-user-search-quality` |
| HEAD | `5327661445c37191a3fd61db195f3af4d2cf893a` | `git rev-parse HEAD` == expected `5327661445c37191a3fd61db195f3af4d2cf893a` |
| Expected branch@SHA | `codex/retrieval-v3-user-search-quality` at `5327661445c37191a3fd61db195f3af4d2cf893a` | matches HEAD, branch, tree clean |
| Tree | `6e5dfa73cd860c4d619b0feffb6c2d6c95d2db7a` (`HEAD^{tree}`) | `git rev-parse HEAD^{tree}` clean, `git status --porcelain` empty, `git diff --check` PASS |
| Origin | `https://github.com/crushonyou2/benefit-compass.git` | `git config --get remote.origin.url`, `git remote -v` |
| Actual remote | `https://github.com/crushonyou2/benefit-compass.git` | origin == actual remote, `git ls-remote origin HEAD` `9048347caed1074619763c51bcbc4e35e7e60363` is `main` |
| Closure tag | `retrieval-v2-cycle3-closure-v1` | tag object `0c94d801da23050d0c9537717b2a3e83ee1b0bf6` → `5327661445c37191a3fd61db195f3af4d2cf893a` |
| Tag peel | `git rev-parse retrieval-v2-cycle3-closure-v1` → `0c94d801da23050d0c9537717b2a3e83ee1b0bf6` (tag), `git rev-parse retrieval-v2-cycle3-closure-v1^{}` / `^{commit}` → `5327661445c37191a3fd61db195f3af4d2cf893a` (commit) | `git cat-file -p retrieval-v2-cycle3-closure-v1` type `tag` object `5327661...`, peel verified |
| Branch→tag lineage | branch created from closure commit | `5327661 docs(memory): record D-012 Cycle3 closure without holdout` is tag target, `git log --oneline -3` `5327661 → a6a232c → a7a8b93` |
| `git diff --check` | PASS | `git diff --check HEAD` and `--cached` exit 0, `git diff --check` from dev-freeze base `cb47935..HEAD -- ml-service/` diff 0 carried forward |
| Working tree | clean | `git status --porcelain` empty, no untracked docs/memory beyond this bootstrap |

**Reconcile verdict:** branch/HEAD/tree, origin/actual remote, closure tag peel, and `git diff --check` all **materially match expectation — no STOP condition.** Tree is clean at the exact D-012 closure commit.

## 2. Lineage — Retrieval v2 Cycle3 closure (D-012) in force

- **D-012 (2026-09-01, user-confirmed, Web independent result/provenance review PASS):** Cycle3 canonical dev one-shot executed **exactly once** at `a6a232c93115647c0716a6ccd97a7d8e2a2ef4be` (base `a7a8b93`, session `cycle3-canonical-dev-9ee016db7048-20260901`, Web PASS). Frozen dev `3791368f4722b612058b7a005e17bf5f1caae4ac0437daa9d44ff28f28ca260c` (36 Youth18/Gov2418, catalog union 248, `retrieval-v2-cycle3-dev-v1`), canonical result `de5d46ae600668f610b5453d52396bafdbf0b8fa1946cfdff0710ab3c3921433` (schema 1, batch `cycle3-canonical-dev-v1`, prereg `18b6c997eb71a8cdff36d84ff46b5bbb6b699874ff6d0fccd18636f00268e156`, `git a7a8b93 dirty True`, corpus `13589/17609`), audit `16 → 20` with exactly one `run_start 1d9cdbe9`/`run_end 9339790a` and one `protected_access_start 74c35e23`/`protected_access_end ea7fd2dc` for that session, no holdout access.
- **Quality/DEV_SELECTABLE:** baseline `hit@5 36/36 recall@5 1.0 macro 1.0 Youth18/18 Gov2418/18 mrr@10 1.0`, `c3e1 K128 36 macro 1.0 net 0`, `c3e2 K256 36 macro 1.0 net 0`, `c3e3 K512 36 macro 1.0 net 0`, each `macro_gt false` / `net_ge_2 false` / `youth_no_regression true` / `gov24_no_regression true` → `quality_selectable []` → latency `{baseline:null,c3e1:null,c3e2:null,c3e3:null}` `quality_only true` not measured (boundary) → **`DEV_SELECTABLE []` / `selected_candidate None`.** By frozen prereg §8 / D-011 rule, **zero `DEV_SELECTABLE` closes Cycle3 WITHOUT holdout** — no candidate freeze, no holdout evaluation/access, no further Cycle3 experiment/rerun. Final holdout `retrieval-v2-cycle3-holdout-v1` (`4c631ce7...` 40 Youth20/Gov2420) remains sealed/unused.
- **Production/contracts unchanged:** `D-003`/`D-004`/`D-007`/`D-008`/`D-010`/`D-011` remain in force as applicable; `D-012` does **not** authorize deletion of provenance refs; Git hygiene cleanup is a **separate future stage** requiring fresh CAS checks. Tag `retrieval-v2-cycle3-closure-v1` is immutable and points to the D-012 closure commit (`5327661`), not directly to `a6a232c`.

Cycle3 state is fully durable in `docs/RETRIEVAL_V2.md` § Cycle 3 — CLOSURE DURABILITY RECORD — D-012, `memory/DECISIONS.md` D-012, and `memory/SESSION-LOG.md` 2026-09-01 D-012 entry. This V3 bootstrap does **not** rewrite or reinterpret that history.

## 3. Scope of this V3 bootstrap (docs/memory only)

**Allowed in this bootstrap:** durable docs/memory record only — this file (`docs/RETRIEVAL_V3.md`), `memory/00-INDEX.md` (add V3 reference), and `memory/SESSION-LOG.md` (append-only V3 bootstrap entry). No code, no eval artifact, no prereg change.

**Explicitly not performed in this bootstrap:**

- No `eval/` creation/modification (no dev/holdout builder, no candidate, no runner, no audit `events.jsonl` append, no `canonical-dev-result.json` access via `git show`/`cat-file`/`checkout`/`restore`/`sparse`/`parent worktree`).
- No retrieval/DB/model/embedding/benchmark/latency execution, no `CYCLE3_CANONICAL_EXECUTION` / `DATABASE_URL` / `SENTENCE_TRANSFORMER` usage.
- No protected dev/holdout/evalset/canonical result plaintext per-case access (use only existing aggregate/provenance facts durable in docs/memory).
- No production `ml-service` behavior change (`git diff HEAD -- ml-service/` 0 preserved from D-012 base, `prereg-v1.json` `18b6c997...` unchanged, `D-003/D-004/D-007` preserved).
- No new branch/tag creation, no remote push/tag, no history rewrite (amend/rebase/squash/reset), no Git hygiene cleanup (branch/worktree deletion/prune).
- No new decision in `memory/DECISIONS.md` (V3 evaluation contract not yet user-confirmed; bootstrap is a durable record, not a decision — to become `D-013` only upon explicit user approval).

## 4. Retrieval v3 — user-search-quality — intent and standing frame

- **Intent:** user-facing search quality (retrieval relevance as experienced by the end user). Exact metric, slice, latency, and adoption gates are **not yet defined** in this bootstrap.
- **Standing decisions carried forward:** `D-003` production retrieval contract (`RERANK=0 CANDIDATES 30 COSINE_MIN 0.78 LEXICAL_OVERLAP_BIAS 0.01 strip_region expired-policy exclusion intfloat/multilingual-e5-base youth bias Gov24-suppressed`), `D-004` rejected alternatives (cross-encoder reranking / global threshold / public region search remain out of scope unless materially new evidence), `D-008` cycle-1 HOLD immutable, `D-010` holdout disqualification / bounded Exp4, `D-011` clean-cycle hygiene (fresh dev+holdout, pre-registration, isolation, audit log), `D-012` closure without holdout — all remain history/contracts as applicable until superseded by an explicit new user-confirmed decision.
- **V2 artifacts are immutable evidence only:** frozen dev `3791368f...`, holdout `4c631ce7...`, canonical result `de5d46ae...`, audit chain 16→20, catalog union 248, and all cycle1/2 tags/commits remain immutable and are **not** reused as tuning data or selection evidence for V3.
- **V3 evaluation contract status:** **open — not yet proposed or user-confirmed.** A future V3 contract (primary metric, floors, holdout split, paired gates, hard-negative/latency methodology) will be recorded as a new append-only decision that supersedes or constrains `D-007` only when explicitly user-confirmed. No contract is assumed from silence.

## 5. Validations for this bootstrap (docs/memory only)

- `git branch --show-current` `codex/retrieval-v3-user-search-quality`, `git rev-parse HEAD` `5327661445c37191a3fd61db195f3af4d2cf893a`, `git rev-parse HEAD^{tree}` `6e5dfa73cd860c4d619b0feffb6c2d6c95d2db7a`, `git status --porcelain` clean before edits, `git diff --check` PASS (before and after), `git diff HEAD -- ml-service/` 0, `prereg-v1.json` SHA `18b6c997eb71a8cdff36d84ff46b5bbb6b699874ff6d0fccd18636f00268e156` unchanged, `eval/retrieval-v2/cycle3/audit/events.jsonl` 20 events unchanged (no append), `eval/retrieval-v2/cycle3/canonical-dev/canonical-dev-result.json` SHA `de5d46ae...` unchanged (not opened per-case), no `git show`/`cat-file` of protected plaintext in this bootstrap worktree.
- After this bootstrap commit: working tree clean, local HEAD remains `5327661`-derived plus docs/memory delta, `git diff --check` PASS, and changed paths limited to `docs/RETRIEVAL_V3.md` + `memory/00-INDEX.md` + `memory/SESSION-LOG.md` only.

## 6. Next gates (explicit, no auto-advance)

1. **User-confirmed V3 evaluation contract** — define V3 primary metric, floors, dev/holdout split, paired quality/P0/hard-negative/latency gates, and adoption rule; record as new decision (e.g., `D-013`) with evidence in this SSOT.
2. **Pre-registration + independent freeze plan** — candidate design space, max experiments, SQL/embedding/latency methodology, audit/chain plan (D-011 hygiene) before any dataset build.
3. **Isolated dataset freeze(s)** — fresh V3 dev/holdout (if contract requires) via sanitized builder sessions with fingerprint-only overlap checks, **candidate tuning before freeze 금지**.
4. **Runner implementation + Web static review + one-shot execution** — only after contract + freeze + independent review PASS; isolated until then.

This bootstrap **STOPs** after the durable docs/memory commit. No dataset freeze, no runner implementation, no retrieval execution, and no holdout access follow from this record.

## 7. History note

V2 SSOT remains `docs/RETRIEVAL_V2.md` (cycle-1 HOLD, cycle-2 disqualified holdout, cycle3 closure without holdout, D-012). This V3 file is the V3-specific durable record bootstrapped from that closure. No V2 history is rewritten by this bootstrap.
