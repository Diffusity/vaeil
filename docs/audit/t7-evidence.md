# T7 red/green and review evidence

Issue25; approved seam docs/specs/t7-message-moderation-seam.md; basea4036b6; isolated branchcodex/t7-messages. H1PR28 remains separate. No merge/deployment/model/tunnel authorization. Frozen earlier assertions retained.

| Cycle | Observed red | Observed green / commit |
| --- | --- | --- |
| Pure assessment |33missingmodule |35includingpurity;5eeb9c0|
| Canonical storage |5localfail,4PGskips |48selected4skips;2c85884|
| Application/review |11localfail,11PGskips |59selected15skips;e437064|
| Authenticated HTTP |9localfail,9PGskips |40selected40skips inclT6HTTP;3f6eeef|
| Demo failure guard |3failed2pass5skips |8selected5skips;cd28368|
| Local vertical UI |Missing Conversation composer |1browser16.8s,TS/build;5a699de|
| Contradictory receipt |Expected safeerror, noalert |3browser19.6s;dcad024|
| Private view contract review |Review view incorrectlyisDelivered |1local1skip;f8cf2c0|
| Draft/status review |Unrelated draft cleared; forbidden action wording |5browser17.9s;4a64041|
| Model provenance |NeedsReview incorrectlyNONE |33selected22skips;a86c9c1|
| Late same-text review lock |2localfail2skips: offered forbiddenactions and lateapprovaldelivered |28application/HTTP28skips;42f3127|

Additional race/rollback/independent SQL unique-index tests pass. New fixture/helper setup corrections awaited actual POST/current row before selecting a review action; no expected behavior weakened. Real-API HTML-like input is released by an authorized synthetic Admin and rendered inertly as React text.

## Independent review

Standards:0hard violations,1judgment concern (review DTO inherited recipient-only DTO) resolved by independent types sharing only body-view privacy behavior. Spec:1P2 unrelated draft deletion and1minor status-guidance issue resolved with focused red/green tests; both reviewers confirmed closure. Subsequent provenance and late-review-lock refinements were independently rechecked, no outstanding Spec finding. All remaining new API/shape choices follow the approved seam; no definition interview reopened.

## Mutation honesty

Initial backend26/27: dropping only the application Block guard survives because pure-domain enforcement remains. This is redundant defense, not a claimed kill. Refined category mutation disables Conversation.open_for_chat; tests unchanged. Final backend matrix includes provenance and late-review-lock faults. The first temporary UI mutation run stopped on a CRLF anchor after one kill; finally restored exact source/build. No invalid run is counted as a complete matrix. Final artifacts/tables carry completed results and restoration hashes.

## Scope limits

No real model/provider/accuracy, safety certification, production database tests, deployment or full six-ruleE2E claim. Rule5partial, Rule3partial, existing3/6domain0/6complete-ruleE2E counts retained. Human review is not model-approved automation. Unfinished in-flight reservation stays undelivered/Busy; explicit new-key retry is allowed unless matching text is review-locked. Same-text check is exact normalized text, not semantic similarity. Full Admin console, Match opening, Reveal eligibility/consent and public Block/Report remain later tickets. H1merge not included.

Final restored full-suite/browser/CI counts are recorded after execution in the PR and session log; earlier per-cycle counts above are chronological evidence, not inferred current totals.

Final restored local checks: **687passed124explicitPGskips37.13s**, Ruff/assumptions/purity/AST green. TypeScript/build green; all13browsercases passed27.7s. Final local backend30/30 and browser5/5 faults killed, exact source restoration verified. Shared Postgres/Windows/container CI remains the published-head gate.
