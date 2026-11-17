# T7 retrospective

1. Fresh-state eligibility must include review locks, not only roles/Block/Reveal. The callback regression proves a matching review claim created during an external call cannot be bypassed by a late Approved result. Keep that test beside the Block-race test.
2. Body-bearing type names carry authorization meaning: review DTOs must not inherit recipient-only DTOs. Shared immutability/export behavior belongs in a neutral base; public shape/export tests pin the difference.
3. A successful action on an old receipt must not clear unrelated draft state. Delayed/error boundary tests plus truthful action flags are more useful than happy-path screenshots alone.
4. Mutation survival can indicate redundant defense rather than a weak test. Record it honestly, then mutate the whole category's policy and leave tests unchanged. Preflight normalized temporary edit text on Windows and always restore exact bytes/build; never count syntax/anchor/setup failures as kills.
5. The issue, approved seam and current code together make the review packet. Reconcile root glossary/current-state prose and exact citations along with new sections; passing tests do not validate stale claims.
6. Existing Ruff/assumption/purity/AST/real-browser/shared-database checks and the existing mutation runner suffice. T7adds product fault cases, not agent infrastructure, providers or deployment tooling. Keep human capacity, agent elapsed time and unverified gaps distinct.
