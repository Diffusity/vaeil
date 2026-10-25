# Initial T1 code review — 75d4ced...b1dd84a

## Standards

No hard documented-standard violation found. Domain purity/injected time and bounded tests are preserved. Two judgment findings:

- Privacy wording overstates scalar protection: native str-compatible PrivateText still serializes after direct field extraction. Canonical private-record exports are guarded. Needs the user decision in t1-private-scalar-decision.md, not a silently narrowed claim.
- Repeated private-text wrapping in three post-init methods is a possible maintenance smell. Keep explicit field mappings for now: each private field set remains directly reviewable. No unrequested generic reflective copier is introduced.

## Spec

One requirement conflict: native str field compatibility and refusal of generic JSON serialization of those scalar values cannot both hold. User must choose opaque private types/extra tests or explicitly record-only scope. No additional correctness finding in validation order, exact view fields, participant precedence, normalized matching modes, profile boundaries or existing claim rules.

Summary: Standards 0 hard violations / 2 judgments; Spec 1 contract conflict. No reviewer changed source/tests or ran mutations. Not a final approval or claim that all mutations are killed.
