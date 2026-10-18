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
