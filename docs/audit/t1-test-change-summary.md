# Approved T1 test-change commit

Before: 98 T1 red cases + 33 slice-2 Pseudonym cases = 131. After: 201 T1 cases + 35 Pseudonym cases = 236. Whole suite: 325 collected; pre-skeleton red 221 failed / 104 passed. No implementation changed. Ruff passed. Full legacy diff: `t1-slice2-test-diff.patch`; no slice-1 test was edited.

## Categories

- Preserve the audit's original behavior expectations and add independent Unicode, normalized-length, punctuation, separator, required-choice and embedded-control boundaries.
- Strengthen private graph, all-field immutability, collection aliases and deterministic code serialization.
- Pin viewer precedence and two-distinct-participant construction, plus seven distinct profile-validation errors in the requested order.
- Refuse pickle (every supported protocol), reduction, copying, asdict and generic JSON mappings for all six private-record kinds; only explicit authorized view encoding is allowed. Explicit persistence mapping belongs to T5.
- Distinct DOB canary: 14 March 1987; positive controls include ISO, DMY, MDY, English display, Python date repr and binary pickle state/decoded values.
- Merges retain parametrized cases: owner 2->2; identifiers/generated text 6->6; fixed-once scenarios 2->2; taken/retry scenarios 2->2. Other cases are retained or strengthened; count does not decrease.

## Updated slice-2 functions (all assertions/policy cases retained)

1. test_a_valid_pseudonym_is_claimed
2. test_blank_pseudonym_is_rejected
3. test_identifier_like_pseudonym_is_rejected
4. test_pseudonyms_are_unique_case_insensitively
5. test_pseudonym_is_fixed_once_set
6. test_a_failed_claim_does_not_set_the_pseudonym
7. test_a_failed_taken_claim_does_not_set_the_member
8. test_normalized_names_share_one_claim
9. test_display_value_is_trimmed_and_nfkc_normalized
10. test_pseudonym_format_boundaries
11. test_reserved_names_are_refused
12. test_claiming_the_same_name_twice_is_still_a_change_attempt
13. test_format_valid_phone_identifier_is_refused

Each caller supplies an explicit synthetic MemberIdentity through a local test helper; production claims without identity must fail. Existing uniqueness, format/constants, reserved words, fixed-once, identifier and retry cases remain.
