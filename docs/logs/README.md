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

## Checkable assumption history

Each table row has a stable ID (`A001`, `A002`, ...), date, rationale, invalidation condition, status, and `Supersedes` links. Keep IDs when editing or moving rows; assign new rows the next unused ID.

- A replacement lists the earlier IDs in `Supersedes` and marks those earlier rows `superseded` in the same change.
- A disproven assumption with no replacement is `invalidated`; explain why below the table. Other current rows are `active`.
- Use `-` for no predecessors. The validator rejects duplicate/malformed IDs, missing links, cycles, invalid statuses/dates, replaced rows still active, and superseded rows with no replacement.
- Run `python scripts/check_assumptions.py`, or the complete `python scripts/check.py`. CI runs the same validation. Whether the meaning actually changed remains a review judgement; links alone cannot prove semantic consistency.

For earlier-session imports and issue/PR closure, follow `docs/agents/workflow.md`. Session transcripts remain in the originating harness; the bounded reader avoids persisting another raw copy.

## Local environment quirks

- **`gh` not found in agent shells after install/upgrade**: the hosting app (OpenCode) can cache the pre-install `PATH`, so shells report `gh` not found even though a fresh terminal finds it. Fix: restart the app, or refresh per command and retry:

  ```powershell
  $env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
  ```
