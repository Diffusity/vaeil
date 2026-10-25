# T1 skeleton red run

Test-only commit: `607062b`. All 325 tests collect. Skeleton intentionally supplies mutable records, wrong enum-code placeholders and NotImplementedError operation bodies; it does not supply domain behavior. It preserves every public declaration for later implementation rather than deleting scaffolding.

Observed whole suite: **219 failed, 106 passed in 7.86s**. Direct exception categories: **178 NotImplementedError, 20 AssertionError, 21 pytest Failed (missing expected exception)**. No missing attribute/import/setup errors. One AssertionError is the long-predicate subprocess surfacing a child NotImplementedError, so semantically **179 unimplemented paths and 40 behavior-assertion failures**. The raw categories are retained rather than hiding this distinction.

## Passing T1 cases reviewed (17)

- Required-identity signature (1): Python's required keyword binding already enforces the skeleton ABI; it does not prove owner/self-name policy. Keep; not a business false positive.
- Canary field controls (4), clean control (1), forbidden identity-reference graph control (1), date-display controls (6): **12 test-harness controls**. Expected to pass because the test helpers are real, independent of domain implementation. They establish that deliberately leaky fakes fail; do not count them as implemented product behavior.
- Existing age-gate error redaction (4): pre-existing specific exceptions already have safe messages. Keep as regression protection; Applicant/Invite repr and serialization still fail.

The other **89 passing cases** are unchanged baseline tests outside the migrated Pseudonym suite. All 35 migrated Pseudonym cases still fail at its deliberately unimplemented claim body. No passing T1 business-rule test is being accepted on a placeholder return. No test was loosened or changed in response to this run.
