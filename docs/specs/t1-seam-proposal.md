# T1 seam and choice lists — approved with consolidated amendments

Approved by Parth on October 24 with the amendments below. Write and show the red tests now; implementation waits for his review of those tests. This document is not product code. Existing scanner/Pseudonym contracts remain except the explicit owner-identity input proposed below.

## Pure projection and ownership

```python
def project_member_for_viewer(
    member: Member,
    *,
    viewer_id: str,
    conversation: ConversationRevealState,
) -> PreRevealMemberView | RevealedMemberView: ...
```

`ConversationRevealState` is an immutable projection input with `conversation_id`, the two `participant_ids`, and `revealed: bool`. It contains no active-slot policy or consent operation. T2 supplies it from authoritative Conversation state; clients never provide the flag. Reject unless subject and viewer are distinct participants in this exact pair. No membership authorization is inferred from a bare boolean. Before T2, domain tests use explicit pair fixtures. HTTP auth/lookup remains future application work; this function performs no I/O.

## Types

All new records are frozen, slotted dataclasses; the following is the approved public shape, not an implementation.

```python
MemberIdentity(member_id: str, legal_name: PrivateText, email: PrivateText,
               phone: PrivateText | None, date_of_birth: PrivateDate)

Member(identity: MemberIdentity, pseudonym: Pseudonym,
       values_profile: ValuesProfile)

ValuesProfile(relationship_intent: RelationshipIntent,
              life_stage: LifeStage,
              interests: frozenset[Interest],
              values: frozenset[CoreValue],
              communication_style: CommunicationStyle,
              pace_and_lifestyle: PaceAndLifestyle,
              about: str = "")

PreRevealMemberView(pseudonym: Pseudonym, values_profile: ValuesProfile)
RevealedMemberView(pseudonym: Pseudonym, values_profile: ValuesProfile,
                   legal_name: PrivateText, email: PrivateText, phone: PrivateText | None)
OwnProfileView(pseudonym: Pseudonym, values_profile: ValuesProfile,
               legal_name: PrivateText, email: PrivateText, phone: PrivateText | None, date_of_birth: PrivateDate)
```

`Member` here is the completed-profile projection input, not the entire admission lifecycle. T6 owns incomplete-onboarding/account state. There is no Member-level Reveal field and no photo field in any type. The post-Reveal result preserves Pseudonym and Values Profile alongside the allowed identity payload. DOB never enters either Match view. The separate owner-only projection can include it. Public serializers explicitly encode the selected view; never recursively serialize Member.

For write validation use `build_values_profile(owner: MemberIdentity, ...approved structured fields..., about: str = "") -> ValuesProfile`. Member and generated text must pass the same factory before storage. No unchecked alternate application save path. Use `contains_self_name(text: str, *, identity: MemberIdentity, mode: SelfNameMode) -> bool` as the shared pure predicate. Preserve the directory seam but require identity: `PseudonymDirectory.claim(member_id: str, candidate: str, *, identity: MemberIdentity) -> Pseudonym`; reject mismatched owner ID with `IdentityOwnerMismatchError`. Invalid profile input raises `InvalidValuesProfileError`. Existing callers/tests migrate explicitly; no default that bypasses the self-name check. Fixed-once guard remains first, including repeated same-name claims.

## Approved fixed choices

Stable enum codes are fixed below; display labels live in the frontend. The approved vocabulary is retained.

| Field | Proposed choices |
| --- | --- |
| Relationship intent | Long-term relationship; Open to a relationship; Still exploring |
| Life stage | Undergraduate study; Postgraduate study; Working; Between study and work |
| Communication style | Direct; Reflective; Expressive; Balanced |
| Pace and lifestyle | Quiet and routine; Balanced routine and spontaneity; Active and spontaneous |
| Interests (1-5 distinct for complete profile) | Reading; Music; Films; Gaming; Cooking; Art; Technology; Sports; Fitness; Outdoors; Travel; Volunteering |
| Values (1-5 distinct for complete profile) | Honesty; Kindness; Curiosity; Family; Independence; Ambition; Stability; Creativity; Community; Wellbeing |

All four single-choice fields are required. Complete profiles require 1-5 interests and 1-5 values; duplicate or unknown selections are refused before storing frozensets. Drafts may be incomplete but are not Matching-eligible. T10 enforces complete-profile eligibility at candidate selection, with persistence/API wiring in T5/T6 preserving that distinction. No custom free-text selections. These lists do not establish scoring weights; T10's algorithm seam remains separately reviewed.

One optional `about` field only: trim and NFKC-normalize before counting 280 Unicode code points, store the normalized text, reject control characters rather than silently removing them, and never truncate. The shared scanner and whole-word self-name mode both run before storage. Control characters in raw input (including tabs/newlines) are rejected even if trimming would remove them.

Pseudonym mode uses substring matching on normalized identity tokens; About mode uses whole-word matching on the same tokens. Normalize before splitting legal name/email local part on whitespace, dots, underscores, hyphens and plus signs; ignore tokens shorter than three. Mark may write “market”; Will cannot write “will”. The latter is a documented false positive with a generic, rephrase-friendly error that never echoes private text.

## Viewer, serialization and redaction contracts

- Self-view raises `SelfViewerError`; unrelated viewer raises `ViewerNotParticipantError`; subject outside the pair raises `SubjectNotParticipantError`. Validate subject membership before viewer rules. `project_own_profile(member: Member) -> OwnProfileView` is the separate trusted owner projection; the application later resolves the signed-in owner.
- `serialize_member_view(view)` is the pure public JSON-ready encoder for view records. Pre-Reveal JSON keys are exactly `pseudonym` and `values_profile`; structured choices serialize as stable codes and sets as deterministic lists. Own/Revealed identity output is intentional and authorized, never a pre-Reveal fallback.
- No private value appears in repr/str of identity-containing records, including Member, RevealedMemberView and OwnProfileView; errors/exceptions never echo private values or rejected input. This includes the existing Applicant DOB and its nested appearance in redeemed Invite representations. Use frozen/slotted new records. PreRevealMemberView has no Member/identity reference or hidden private slots.
- Canary tests cover pre-Reveal repr/str, exceptions, dictionary access, recursive slot inspection, pickle/roundtrip, dataclasses.asdict and JSON. Private fields use opaque immutable values. Scalars and records refuse pickle/copy/reduction/asdict/generic JSON. Explicit authorized view encoding is allowed; T5 adds explicit persistence mapping. Deliberate extraction by code with access is not prevented; the three-site AST boundary makes ordinary extraction greppable.

## Stable enum codes

| Enum | Exact codes |
| --- | --- |
| RelationshipIntent | `long_term`, `open_to_relationship`, `still_exploring` |
| LifeStage | `undergraduate`, `postgraduate`, `working`, `between_study_and_work` |
| CommunicationStyle | `direct`, `reflective`, `expressive`, `balanced` |
| PaceAndLifestyle | `quiet_and_routine`, `balanced_routine_and_spontaneity`, `active_and_spontaneous` |
| Interest | `reading`, `music`, `films`, `gaming`, `cooking`, `art`, `technology`, `sports`, `fitness`, `outdoors`, `travel`, `volunteering` |
| CoreValue | `honesty`, `kindness`, `curiosity`, `family`, `independence`, `ambition`, `stability`, `creativity`, `community`, `wellbeing` |

`SelfNameMode` has PSEUDONYM and ABOUT modes. The complete-profile factory refuses incomplete selections; future draft/account storage is not itself a complete ValuesProfile. No gender/orientation fields are introduced. Private future match preferences belong outside ValuesProfile and the public view types, so their addition need not expand those views.

## Approval covers test behavior

- Pin exactly the two pre-Reveal fields, including serialized keys; no nested private object.
- Unmistakable canaries in every private field, scanned across every pre-Reveal projection and serializer; distinct pair fixtures verify isolation. Post-Reveal intentionally includes the allowed identity canaries, never DOB.
- Refuse wrong pair/viewer, invalid/duplicate/over-limit choices, 281-character about, identifiers and self-name content; pin 280 and normalization boundaries, unchanged state and retry.
- Shared predicate tests cover casefold/NFKC/separators/email-local tokens/short tokens; directory tests retain taken/fixed-once/reserved/format behavior.
- Separate red-green commits for profile/projection and Pseudonym integration; show each red run first. Mutations remove allow-list protection, profile checks, pair validation, self-name normalization/threshold/check integration, accepting a Member Reveal flag, ignoring Conversation state, exposing a private pre-Reveal field, dropping whole-word matching or redaction; each must fail a meaningful public-seam test. Purity guard green. Rule 5 remains partial and TESTING rule counts do not change.
- Consent, engagement eligibility, storage, delivery and UI are outside T1. No photo representation.

## Approved opaque refinement

PrivateText/PrivateDate are not native str/date or dataclasses; equality is same-private-type only and values are unhashable. Rendering redacts and no native text/calendar/arithmetic API is exposed. Constructors accept plain inputs and wrap them. One method, UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE, is permitted only in member.serialize_member_view, self_name.contains_self_name and invite.redeem_invite. The exact AST guard and fake violations are in tests/test_private_unwrap_boundary.py. Explicit view field names and JSON payloads are unchanged.
