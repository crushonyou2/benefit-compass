<!-- ballast session-start block — append to the project's CLAUDE.md -->

## Session start (ballast)

1. Before substantive work, read `memory/00-INDEX.md` and `memory/DECISIONS.md`. Standing decisions are followed without relitigating — to change one, use the supersede protocol (ballast decision-ledger skill).
2. Record decisions and important facts in `memory/` **in the same session they appear**. Unresolved items go to `memory/OPEN-QUESTIONS.md` — and so does any reading of a non-answer you are proceeding on, as `assumed`, never as a decision.
3. Claims carry labels: confirmed / observed / assumed / hearsay / unknown (ballast verify-gate skill).
4. External-facing product claims require evidence in `memory/PRODUCT-TRUTH.md` (ballast proof-standard skill).

## Chat On Steroids path/privacy

1. Chat On Steroids Core/Desktop tool arguments, worker context, and worker messages must not include user-specific native absolute paths such as `C:\Users\<user>\...` or `C:/Users/<user>/...` when an equivalent supported virtual or repo-relative reference works.
2. Prefer the current project working directory and repo-relative paths. Use a verified Chat On Steroids virtual alias only when the specific tool/action explicitly supports that alias; do not assume shell `workdir` accepts app virtual paths.
3. Inside commands and worker instructions, prefer repo-relative paths such as `eval/...`, `docs/...`, and `memory/...`; refer to the repository as `current benefit-compass repository` rather than embedding a native home-directory path.
4. Native absolute paths are allowed only when technically unavoidable and no supported virtual alias or relative reference can perform the operation. Do not weaken or bypass genuine sensitive-information safety confirmations.
