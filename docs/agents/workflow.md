# Recover context, verify work, and hand off

## Before implementation from an earlier session

1. Read `docs/logs/assumptions.md` and the relevant session summaries. Inspect the current branch and working-tree changes; preserve unfinished work.
2. If the user supplies an OpenCode session, read its visible dialogue before editing code:

   ```powershell
   .venv\Scripts\python.exe scripts/read_session.py <session-id> --start 0 --max-chars 8000
   ```

   Follow the reported next offset until the relevant decisions are read. Offsets count visible-text characters, so a large individual message can span pages without being lost. For an existing export, use `--input <json-path>` instead of a session ID. The script reads exports in memory and emits user/assistant text and question answers; it filters reasoning, ordinary tool output, and metadata. Visible dialogue may still contain sensitive content: keep exports local and retain curated summaries in the repo.
3. Read the current issue and its comments through `docs/agents/issue-tracker.md`. Reconcile the source dialogue with the checked-out code and issue: scope, approved test seam, required tests/mutations, required commits, and pending human review. Later explicit user decisions win; record replacements in the assumptions table.
4. Append a short recovery summary to the session log, naming the source session, current issue/branch, last completed step, and any pending approval. Start implementation only when the recovered approvals cover that work. If the source cannot be read, report the missing context and continue independent inspection; do not treat an absent approval as granted.

## Checks during a slice

Install `.[dev]` through the README setup. Run the same checks as Windows CI:

```powershell
.venv\Scripts\python.exe scripts/check.py
```

This runs Ruff, assumption validation, and pytest, stopping at the first failure. Ruff's selected rule families and tool versions live in `pyproject.toml`. CI runs on pull requests and pushes to master.

Keep the existing tests-first and slice-review approvals. Put large parametrized fixtures behind short explicit IDs; pytest automatically hashes long string/byte values and rejects collected node IDs longer than 200 characters. New performance-sensitive parsers need representative bounded regression cases, including punctuation-heavy input when relevant.

Mutation scripts rewrite source files. Run them alone, restore every mutation, then run the normal checks. They are deliberately excluded from the CI runner. The existing slice-2 script remains the reproduction command in TESTING.md.

## Before PR review and merge

1. Record the originating issue, red/green evidence, required mutation results, limitations, and any separate outstanding operation in the PR and session log. Use the PR skill's body format.
2. Verify the issue closure intent with `gh pr view <number> --json body,closingIssuesReferences`. Use `Closes #<issue>` when merging finishes the issue; `Refs #<issue>` only links it. If an issue intentionally stays open, state why and which acceptance remains. Separate a local tooling operation from a finished feature ticket when appropriate.
3. Run code-review against the PR base, resolve findings, and preserve the user's merge gate. Merge only when authorized. Then verify both the PR state and linked issue state; close an issue manually only when authorized.
4. Append the merge commit, validation result, issue outcome, and remaining work to the session log. Include that final record in the next authorized commit or docs PR; report it if it remains uncommitted. Run retro before discarding the build context.
