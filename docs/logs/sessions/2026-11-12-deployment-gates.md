# Deployment gate follow-up — 12 November 2026

Working block started 19:48 Asia/Calcutta (recovered from the first tool activity; minute precision). Parth confirms the Neon password was changed and requests the previously recommended work in order, explicitly excluding T6 implementation. The preceding recommendation retained final merge-approval gates for PRs #21 and #22. No merge approval or acceptance waiver is inferred.

Recovered `codex/t5-persistence` at dcc1dec with its pending final-CI log entry. Preserved that tracked entry in a named Git stash before switching to `codex/t4-deployment`; unrelated historical untracked files remain untouched. Both PRs have green final Windows/security checks; T4 also has green container CI, T5 green shared PostgreSQL/SQLite contracts and mutations.

Public `/api/ready` returned 200 with exactly `{"status":"ready"}` in 8.034 seconds after rotation confirmation. The complete T4 public smoke subsequently passed HTML/assets, exact anonymous payload, health and readiness, finishing at 19:53:46. No secret fields were opened or copied. This supports working deployed database credentials without inspecting them.

Browser control initially timed out, then recovered through the existing Chrome session. The safe Render Events page still identifies the deployed runtime as 7fd4ad0. A new idle observation starts after the final public smoke, with no agent app requests during the quiet interval. Actual sleep/loader evidence is not claimed from elapsed time alone. Live RAM graphs remain unavailable on the Free dashboard; no upgrade is authorized or attempted.

End timestamp and final outcome will be appended at handoff. Elapsed time includes external waiting, not verified human active effort; effort before time tracking remains unverified. T6 remains untouched.
