## Agent skills

### Issue tracker

Issues live as GitHub Issues in `Diffusity/vaeil`, operated via the `gh` CLI. See `docs/agents/issue-tracker.md`.

### Triage labels

The five canonical triage roles use the default label strings (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`). See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.

## Project logs

When recovering an earlier session, implementing a slice, or preparing a PR handoff, follow `docs/agents/workflow.md`.

Assumptions and session history live in `docs/logs/`. Before deciding anything ambiguous for this project, read `docs/logs/assumptions.md` and stay consistent with recorded assumptions; record any new assumption there (dated, with what would invalidate it). Append a session summary to `docs/logs/sessions/` when a session's work is done. See `docs/logs/README.md`.

## Project constraints

IT643 course project — evaluation requires four files at the repo root: `README.md`, `UBIQUITOUS_LANGUAGE.md`, `DESIGN.md`, `TESTING.md`. Docs are graded against the code (`file:line`); stale docs count as absent. The shared vocabulary lives in `UBIQUITOUS_LANGUAGE.md` + `GLOSSARY.md`, kept in sync — rules in `docs/agents/domain.md`, rationale in `docs/logs/assumptions.md`.
