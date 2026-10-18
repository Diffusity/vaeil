# Project logs

Durable records of how this project's conventions were formed, so that later sessions stay consistent. Raw conversation transcripts are not kept here — these are curated summaries; the hosting app retains the raw sessions.

- **`assumptions.md`** — running log of assumptions agents made when the answer wasn't fully specified.
- **`sessions/`** — one summary per working session, named `YYYY-MM-DD-<slug>.md` (dated by the session's start day).

## Rules

- Before deciding anything ambiguous for this project, read `assumptions.md` and follow the recorded assumption. If it no longer holds, update the entry (mark it `superseded` or `invalidated`, add the replacement) — never silently choose differently.
- Log assumptions, not facts: calls a reasonable agent could make differently, and what would invalidate them.
- Append a session summary at the end of each session; don't rewrite old logs — add corrections instead.
- Keep entries short, dated, and reference artifacts (files, issues, PRs) by path or URL rather than duplicating their content.
- If an assumption is later confirmed as a real decision, graduate it to an ADR in `docs/adr/` and link the two.

## Local environment quirks

- **`gh` not found in agent shells after install/upgrade**: the hosting app (OpenCode) can cache the pre-install `PATH`, so shells report `gh` not found even though a fresh terminal finds it. Fix: restart the app, or refresh per command and retry:

  ```powershell
  $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
  ```
