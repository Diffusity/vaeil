# Initial T1 code review — 75d4ced...b1dd84a

Historical findings below were resolved by the approved opaque refinement. Final re-review of `06fd4b6` is appended; no unresolved serialization gate remains.

## Standards

No hard documented-standard violation found. Domain purity/injected time and bounded tests are preserved. Two judgment findings:

- Privacy wording overstates scalar protection: native str-compatible PrivateText still serializes after direct field extraction. Canonical private-record exports are guarded. Needs the user decision in t1-private-scalar-decision.md, not a silently narrowed claim.
- Repeated private-text wrapping in three post-init methods is a possible maintenance smell. Keep explicit field mappings for now: each private field set remains directly reviewable. No unrequested generic reflective copier is introduced.

## Spec

One requirement conflict: native str field compatibility and refusal of generic JSON serialization of those scalar values cannot both hold. User must choose opaque private types/extra tests or explicitly record-only scope. No additional correctness finding in validation order, exact view fields, participant precedence, normalized matching modes, profile boundaries or existing claim rules.

Summary: Standards 0 hard violations / 2 judgments; Spec 1 contract conflict. No reviewer changed source/tests or ran mutations. Not a final approval or claim that all mutations are killed.

## Final Standards re-review — ec78775...06fd4b6

No hard-standard violations or blocking maintainability findings. Native subtype leakage is resolved; wrappers are opaque, immutable/slotted/non-dataclass, unhashable, safely rendered and explicitly extracted. One nonblocking typing observation: generated dataclass constructors accept plain inputs in post-init while field annotations describe wrapped state. A typed factory/explicit input signature can be clarified when adapters need static checking; runtime ergonomics and wrapping are tested. No test change requested.

## Final Spec re-review — 06fd4b6

No additional actionable findings. Opaque values resolve native JSON/format leakage; exact view shapes/payload, profile precedence, participant rules, both self-name modes and original claim policy match the approved contract. Only the approved residual limit remains: deliberate extraction by code with access is not prevented. The AST test pins the three production functions.

Both reviewers completed source reads before mutations began. Final summary: Standards 0 hard violations / 1 nonblocking typing note; Spec 0 additional actionable findings. Complete mutation evidence is recorded separately (74/74 killed), not inferred from review.

## Requested pre-merge review — 75d4ced...b1937f6

Two independent read-only reviewers checked the complete PR against master and Issue #8/the approved seam. Standards found two stale documentation summaries: DESIGN retained superseded cost-cap failure wording, and UBIQUITOUS_LANGUAGE omitted the implemented T1 seams. Both were corrected without changing source or tests. Spec found zero missing, incorrect, or unrequested behaviors. Full local check: 401 passed, Ruff and assumption validation green. Windows CI must pass on the documentation-fix head before the authorized merge commit.
