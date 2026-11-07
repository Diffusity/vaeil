# T2 evidence — 7 November 2026

Spec: #9 and approved `docs/specs/t2-t3-seams.md`. Code base for T2-only review: `0ea6790`; no existing test file changed. T3 not implemented here. No configured static typechecker; no claim of static typing verification.

## Red/green cycles

| Cycle | Red | Green | Commit |
| --- | --- | --- | --- |
| First active-slot refusal | Missing module, then working wrong-placeholder directory fails `DID NOT RAISE MemberAlreadyActiveError` | 1 passed | 35d07e0 |
| Lifecycle and Reveal slot release | 5 failed / 1 passed: missing flags/restore | 6 passed | 17b5950 |
| Block/outsider/permanent exclusion | 5 failed / 6 passed: missing new errors/Block operation | 11 passed | a819582 |
| Constructor and duplicate ID guards | 13 failed / 17 passed: missing error types | 30 passed | d361bb4 |
| Monotonic restoration | 12 failed / 31 passed: missing transition error, wrong-type errors, slot/pair `DID NOT RAISE` | 43 passed | 26d4486 |
| Existing projection integration/regression checks | Already supported by preceding cycles and T1; no artificial red claimed | 46 passed | b2143a7 |

The added parametrized cases include public error/immutable snapshot requirements, not 46 distinct product features. No test loosened to get green. Shared placement validation was extracted during review and all cases retained. Normal suite and architecture checks are reported in TESTING/session log after mutation source restoration.

## Selected mutations

Run `scripts/check_t2_mutations.py` alone. Final **19/19 killed** by test failures (no collection-error kill accepted), exact source bytes restored: `249feb443e0edf99cf2015d0d34b13c188ba8a3e44a090d82168ff3564792624`.

| Mutation | Killing evidence in tests/test_conversation.py |
| --- | --- |
| Active ignores Reveal | lifecycle truth table; Reveal releases both slots |
| Active ignores Block | lifecycle truth table; Block frees slots |
| Reveal closes chat | lifecycle truth table; completed Reveal |
| Block allows chat | lifecycle truth table; Block closes chat |
| Escalation ignores pair Reveal | truth table; sequential projection |
| Projection context hides Reveal | truth table; sequential revealed/anonymous payloads |
| Duplicate ID overwrites history | duplicate ID refusal |
| Reversed Block pair escapes exclusion | Block exclusion and restore reversed pair |
| Restore conflicts with same record | restore idempotence |
| Outsider can Block | outsider refusal; invalid-operation canaries |
| Block not recorded | Block lifecycle and pair exclusion |
| Restore reverses Reveal | reverse-reveal case |
| Restore reverses Block | reverse-block case |
| Restore changes participants | replace/reorder participant cases |
| Open/restore ignore slots | active-slot and restore refusal cases |
| Open/restore ignore pair exclusion | permanent-pair refusal cases |
| Same participant twice accepted | invalid shape; invalid-open atomicity |
| Non-Boolean Reveal accepted | invalid flag case |
| Mutable Conversation | frozen snapshot truth table |

An initial runner classified two actual kills as errors because test names contained “errors”; fixed reporting to recognize numeric pytest error summaries. Assertions stayed unchanged. The final run covers the shared validator after the review refactor, not stale source.

## Review and limits

Independent Spec review: zero actionable mismatches. Standards review requested graded-document refresh and noted duplicated open/restore placement rules; both addressed. Trusted restore is not exposed to Members and cannot replace T8 consent/threshold enforcement. In-memory authority has no persistence/concurrency guarantee; T5 must provide atomic storage behavior. Continued safety/Reports are downstream requirements, not inferred from `open_for_chat`. Rule 5 partial, 3/6 domain and 0/6 E2E remain unchanged.
