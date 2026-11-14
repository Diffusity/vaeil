# T6 two-axis review

Base: `ca2f4754058e3f9631f21b2d85215d61b9253f47`. Reviewed implementation through `60cc62d`, plus pending documentation/validation changes. Independent Standards and Spec agents used the code-review skill; a later pass reconciled GitHub Issue13 as well as the approved seam.

## Standards

One documented-standard finding: DESIGN still claimed note-only admission and auth were unimplemented. Corrected to distinguish implemented T6 APIs from the earlier live deployment, and scoped the absent adapter claim to the LLM. No actionable source-level standards violations or Fowler smells reported.

## Spec

Initial seam pass: no actionable mismatch. Issue13 reconciliation found two evidence/documentation gaps: persisted application-note canaries through both recipient views, and concrete HTTP profile contracts for H1. Added two parametrized projection cases per database and `docs/specs/t6-profile-http-contract.md`. No product behavior change was necessary. The newly authored test initially used the wrong record attribute (`application_note` instead of `note`); corrected that setup typo without weakening the persistence equality assertion. This is not claimed as behavioral red evidence.

The implementation self-review also caught the duplicate-email503 mismatch; the regression was red on503, then green on409 with atomic Invite retry. Remote operation limits and password verification lock scope each have regression evidence.

Final CI remains a handoff gate. No T6 merge or deployment is authorized here. Rule5 remains partial. Existing T1 assertions are unchanged; legacy Vetting changes are fixture/type-only.
