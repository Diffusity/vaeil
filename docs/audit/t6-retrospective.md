# T6 retrospective

The existing Windows checks, browser tests, disposable PostgreSQL contract job and exact-source-restoration mutation runner remain the guardrails. No new agent tooling was added.

1. Review caught stale current-state claims in a long DESIGN narrative. Reconcile historical prose alongside new sections before handoff; the two-axis review remains useful because passing tests cannot validate those claims.
2. Self-review exposed password work inside a repository transaction and missing remote operation bounds. Regressions now cover availability as well as result correctness, without flaky timing of cryptographic internals.
3. GitHub issue reconciliation caught required projection canaries and frontend contract documentation missing from an otherwise implemented seam. Review both issue and seam; neither replaces the other.
4. Use explicit UTF-8 for Windows document operations and inspect exit codes before commits. One default-codepage edit failed; the UTF-8 retry completed. No additional hooks/framework are warranted for this task.

These are observations for the handoff, not new product decisions or permission to expand scope.
