# T6 retrospective

The existing Windows checks, browser tests, disposable PostgreSQL contract job and exact-source-restoration mutation runner remain the guardrails. No new agent tooling was added.

1. Review caught stale current-state claims in a long DESIGN narrative. Reconcile historical prose alongside new sections before handoff; the two-axis review remains useful because passing tests cannot validate those claims.
2. Self-review exposed password work inside a repository transaction and missing remote operation bounds. Regressions now cover availability as well as result correctness, without flaky timing of cryptographic internals.
3. GitHub issue reconciliation caught required projection canaries and frontend contract documentation missing from an otherwise implemented seam. Review both issue and seam; neither replaces the other.
4. Use explicit UTF-8 for Windows document operations and inspect exit codes before commits. One default-codepage edit failed; the UTF-8 retry completed. No additional hooks/framework are warranted for this task.

These are observations for the handoff, not new product decisions or permission to expand scope.

## Fresh PR24 review and whole-process lessons

Ordered by severity:

1. **Input boundaries:** escaped malformed Unicode reached storage or response encoding. New HTTP regressions must use escaped JSON content, because the client JSON helper rejects it before the server. Pin safe refusal and unchanged state, not merely an error status. Reuse these tests in existing CI; no new agent tooling.
2. **Review completeness:** use both approved seam and originating issue. Earlier review caught missing persisted-note canaries/API contracts; a fresh pass caught Unicode handling despite the large green suite. The issue, seam, mutation targets and implementation form the review packet.
3. **Graded documentation:** current-state prose contradicted new implementation sections. Reconcile the whole document and exact citations, separating implementation, CI and deployed evidence. This needs reviewer judgment; do not add broad agent instructions or a speculative framework.
4. **Execution hygiene:** UTF-8 explicitly for Windows files, inspect failed commands before committing, and run mutation writers alone with exact restoration. Existing Ruff/assumption/purity/boundary/browser/database jobs remain the guardrails.
5. **Effort accounting:** agent wall time and human sessions differ; gaps and pretracking effort remain unverified. Review/operational work needs schedule room. Teammate willingness is not measured delivery.

These recommendations do not reopen the definition, add tooling, authorize deployment or assign teammates.
