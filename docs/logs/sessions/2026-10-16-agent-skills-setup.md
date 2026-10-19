# 2026-10-16 — Agent skills setup

_Session ran 2026-10-16 into 2026-10-17._

## Goal

Initialize the per-repo configuration the Matt Pocock engineering skills assume: issue tracker, triage labels, and domain docs (via `.agents/skills/setup-matt-pocock-skills`).

## What happened

- Explored the repo: greenfield — only `.agents/`, `LICENSE`, `skills-lock.json`. GitHub remote `Diffusity/vaeli`. `triage` skill installed. No monorepo signals → single-context.
- User decisions (asked explicitly):
  - Issue tracker → **GitHub** Issues via `gh` CLI.
  - Triage labels → **keep the five defaults**.
  - Instruction file → create **`AGENTS.md`** (no `CLAUDE.md`).
- Wrote from the skill's seed templates: `AGENTS.md`, `docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`, `docs/agents/domain.md`.
- User installed and authenticated `gh`: version 2.102.0, account `Diffusity`, HTTPS, token scopes `gist, read:org, repo, workflow`.
- Created issue labels: `needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`. `wontfix` already existed and was left as-is.
- User asked to keep an assumptions log and session logs → created `docs/logs/` (this file, `assumptions.md`, `README.md`) and added a `## Project logs` section to `AGENTS.md`.

## Open / follow-ups

- None blocking. Revisit the single-context assumption if monorepo signals (`packages/`, workspaces) appear.

## Environment notes

- The hosting app (OpenCode) cached the pre-install `PATH`, so `gh` wasn't visible to its shells. Fix (restart app, or PATH-refresh one-liner) recorded in `docs/logs/README.md`.

## Related artifacts

- `AGENTS.md`, `docs/agents/issue-tracker.md`, `docs/agents/triage-labels.md`, `docs/agents/domain.md`
- Issue tracker: https://github.com/Diffusity/vaeli

## 2026-10-18 addendum

- Committed the setup as `48f75f2` on `master` ("Add agent skills setup and project logs"): `AGENTS.md`, `docs/`, and `.gitignore` (which keeps the vendored `.agents/` skills directory and `skills-lock.json` out of the repo).

## 2026-10-19 addendum

- Surfaced a local `main` branch (GitHub's default branch) carrying three local-only commits imported from `vaeil.zip` — skeleton, backend slices (domain rules, `Clock` port/adapter), and a pytest suite. `origin/main` is still at "Initial commit" (`d4199cb`); nothing has been pushed.
- **User decision:** development continues on `master`; `main` is out of scope — left untouched, not to be merged, checked out, or cherry-picked from (see `../assumptions.md`).
- Push to GitHub deferred (user: "Not yet"). Everything stays local.

## 2026-10-19 — Course deliverables wired in

- Read the IT643 project page (https://it643.ankushchander.com/project/): evaluation requires four root files — `README.md`, `UBIQUITOUS_LANGUAGE.md`, `DESIGN.md`, `TESTING.md` — and docs are graded against the code (`file:line`); stale docs count as absent.
- Created `UBIQUITOUS_LANGUAGE.md` (course format: term table + flagged ambiguities) and `GLOSSARY.md` (skills format). Both are intentionally empty of terms: the course warns an unreviewed agent-authored glossary is worse than none — the team populates them.
- `docs/agents/domain.md`: vocabulary section added (read both files; keep in sync; code wins on disagreement).
- `AGENTS.md`: `## Project constraints` section added.
- Not yet created on `master`: `README.md`, `DESIGN.md`, `TESTING.md` — they land with the work.
