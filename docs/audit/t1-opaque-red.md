# Opaque private values: test-only red evidence

Against unchanged production head `ec78775`: **39 failed, 35 passed in 0.61s** for the 74 new scalar/boundary cases; no import/setup errors in this valid run. Three JSON refusal cases independently fail `DID NOT RAISE TypeError`. Actual synthetic values serialized as `"SyntheticNameZXQ"`, `"synthetic@example.invalid"`, `"+919876543210"`. Formatting tests independently detect `CanaryNameZXQ` in padded format/.format output. Initial test-authoring collection typo was corrected before this run and is not red evidence.

Passing cases protect behavior already present (repr/str, copy refusal, native JSON's inability to encode date), existing payload compatibility and architecture-checker positive controls; they do not prove opacity. New opacity/native-operation/format/boundary checks expose the missing policy. Implementation follows only after this test commit.

## Existing test functions changed by name

- test_reveal_adds_identity_without_removing_the_public_profile: compare fields against PrivateText instances; retain exact authorized payload and field pins.
- test_owner_projection_is_a_separate_redacted_view: compare text/date fields against wrappers; retain all redaction and owner-payload checks.
- test_shared_predicate_has_distinct_pseudonym_and_about_modes: add two raw-candidate NFKC cases, retaining every prior case.
- test_turning_eighteen_today_is_allowed
- test_turned_eighteen_yesterday_is_allowed
- test_leap_day_birthday_turns_eighteen_on_feb_28_in_non_leap_years
- test_leap_day_birthday_is_allowed_on_mar_1_in_non_leap_years

The last four compare against PrivateDate(date(...)), retaining exact birthdays and Invite assertions. Full slice-1 diff is t1-opaque-slice1-test-diff.patch. No slice-2 test changes in this refinement. Constructors continue accepting plain inputs. Exact view field names and explicit authorized JSON remain pinned; plain-string/date equality is now explicitly forbidden.

Unwrap method selected: `UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE`. The AST test scans all production modules and pins exactly member.serialize_member_view, self_name.contains_self_name and invite.redeem_invite. Its fake-module tests detect direct calls, aliases and literal getattr. Wrapper values will be unhashable: they are not needed as keys, so no private-value hashing API is exposed.
