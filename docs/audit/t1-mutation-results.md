# T1 complete mutation results

74/74 killed; zero survivors and zero collection/setup-error kills. Each mutation ran independently, pytest exit 1 plus actual failing test cases was required, then exact source bytes were restored in finally. The first runner attempt stopped at a Windows CRLF target mismatch after 16 kills; its results were not substituted for the corrected complete 74-run result below. All protected source/test paths and SHA-256 contents match the pre-run snapshot.

Reproduce on Windows: `.venv/Scripts/python.exe scripts/check_t1_mutations.py`. Run alone, never alongside other source-mutating checks. Raw results are in t1-mutation-results.json. This is selected-fault evidence, not an assertion that every possible mutation is killed. Redaction faults deliberately bypass the full layered guard; removing only one redundant guard can be behaviorally equivalent.

| # | Mutation | Result | Failing cases | First killing test |
| --- | --- | --- | ---: | --- |
| 1 | remove phone detection | KILLED | 18 | `test_every_identifier_category_refuses_the_entire_profile_save[phone]` |
| 2 | remove email detection | KILLED | 6 | `test_every_identifier_category_refuses_the_entire_profile_save[email]` |
| 3 | remove handle detection | KILLED | 7 | `test_every_identifier_category_refuses_the_entire_profile_save[handle]` |
| 4 | remove obfuscated_email detection | KILLED | 9 | `test_every_identifier_category_refuses_the_entire_profile_save[obfuscated]` |
| 5 | remove url detection | KILLED | 6 | `test_every_identifier_category_refuses_the_entire_profile_save[url]` |
| 6 | phone threshold 9 | KILLED | 2 | `test_phone_digit_threshold_boundary[123456789-False]` |
| 7 | phone threshold 11 | KILLED | 14 | `test_every_identifier_category_refuses_the_entire_profile_save[phone]` |
| 8 | drop Pseudonym NFKC | KILLED | 3 | `test_a_failed_taken_claim_does_not_set_the_member[merged-t1-fullwidth-taken]` |
| 9 | drop Pseudonym casefold | KILLED | 7 | `test_pseudonyms_are_unique_case_insensitively` |
| 10 | drop claim identifier check | KILLED | 1 | `test_format_valid_phone_identifier_is_refused` |
| 11 | drop fixed-once guard | KILLED | 4 | `test_fixed_once_precedes_other_claim_validation` |
| 12 | drop reserved-name check | KILLED | 5 | `test_reserved_names_are_refused[admin]` |
| 13 | make identity optional | KILLED | 1 | `test_pseudonym_claim_requires_private_identity_without_a_bypass_default` |
| 14 | drop owner check | KILLED | 1 | `test_claim_rejects_a_mismatched_identity_without_leaking_private_values` |
| 15 | drop claim self-name check | KILLED | 1 | `test_pseudonym_self_name_failure_does_not_consume_the_slot` |
| 16 | use whole-word in claim | KILLED | 1 | `test_pseudonym_self_name_failure_does_not_consume_the_slot` |
| 17 | move fixed-once after owner | KILLED | 1 | `test_fixed_once_precedes_other_claim_validation` |
| 18 | drop self-name NFKC | KILLED | 2 | `test_shared_predicate_has_distinct_pseudonym_and_about_modes[about-nfkc]` |
| 19 | drop email-local NFKC | KILLED | 1 | `test_self_name_normalization_tokens_and_length_boundary[nfkc-local]` |
| 20 | replace casefold with lower | KILLED | 3 | `test_shared_predicate_has_distinct_pseudonym_and_about_modes[about-sharp-s]` |
| 21 | drop text NFKC | KILLED | 2 | `test_shared_predicate_has_distinct_pseudonym_and_about_modes[about-input-nfkc]` |
| 22 | name token threshold 2 | KILLED | 2 | `test_self_name_normalization_tokens_and_length_boundary[short]` |
| 23 | name token threshold 4 | KILLED | 2 | `test_self_name_normalization_tokens_and_length_boundary[three]` |
| 24 | do not split plus | KILLED | 2 | `test_self_name_normalization_tokens_and_length_boundary[name-separators]` |
| 25 | do not split dot | KILLED | 1 | `test_self_name_normalization_tokens_and_length_boundary[dot]` |
| 26 | include email domain | KILLED | 1 | `test_self_name_normalization_tokens_and_length_boundary[not-domain]` |
| 27 | drop whole-word boundaries | KILLED | 5 | `test_about_whole_word_mode_accepts_market_for_mark` |
| 28 | drop About self-name | KILLED | 3 | `test_profile_errors_never_print_private_rejected_text[legal-name]` |
| 29 | substring mode in About | KILLED | 1 | `test_about_whole_word_mode_accepts_market_for_mark` |
| 30 | drop profile identifier check | KILLED | 8 | `test_every_identifier_category_refuses_the_entire_profile_save[email]` |
| 31 | drop controls | KILLED | 11 | `test_about_control_characters_are_refused_even_at_trim_boundaries[nul]` |
| 32 | About limit 279 | KILLED | 5 | `test_about_is_optional_and_normalized_before_storage_and_counting` |
| 33 | About limit 281 | KILLED | 5 | `test_about_is_optional_and_normalized_before_storage_and_counting` |
| 34 | selection maximum 4 | KILLED | 2 | `test_complete_profile_selection_boundaries[5-True-interests]` |
| 35 | selection maximum 6 | KILLED | 2 | `test_complete_profile_selection_boundaries[6-False-interests]` |
| 36 | selection minimum 0 | KILLED | 2 | `test_complete_profile_selection_boundaries[0-False-interests]` |
| 37 | selection minimum 2 | KILLED | 82 | `test_pre_reveal_type_and_serialized_keys_are_exactly_the_allow_list` |
| 38 | silently deduplicate | KILLED | 3 | `test_duplicate_selections_are_refused_before_frozenset_conversion[interests]` |
| 39 | mutable interests | KILLED | 3 | `test_complete_profile_selection_boundaries[1-True-interests]` |
| 40 | mutable values | KILLED | 3 | `test_complete_profile_selection_boundaries[1-True-values]` |
| 41 | drop About normalization | KILLED | 3 | `test_about_is_optional_and_normalized_before_storage_and_counting` |
| 42 | drop About trim | KILLED | 2 | `test_about_is_optional_and_normalized_before_storage_and_counting` |
| 43 | scanner before length | KILLED | 1 | `test_profile_validation_precedence_is_pinned` |
| 44 | self-name before scanner | KILLED | 1 | `test_profile_validation_precedence_is_pinned` |
| 45 | controls before selection | KILLED | 1 | `test_profile_validation_precedence_is_pinned` |
| 46 | length before controls | KILLED | 1 | `test_profile_validation_precedence_is_pinned` |
| 47 | duplicate check before unknown codes | KILLED | 1 | `test_profile_validation_precedence_is_pinned` |
| 48 | skip shape checks | KILLED | 1 | `test_profile_validation_precedence_is_pinned` |
| 49 | accept Member Reveal flag | KILLED | 1 | `test_member_cannot_supply_a_global_reveal_flag` |
| 50 | always reveal | KILLED | 9 | `test_pre_reveal_type_and_serialized_keys_are_exactly_the_allow_list` |
| 51 | never reveal | KILLED | 12 | `test_reveal_adds_identity_without_removing_the_public_profile` |
| 52 | drop subject membership | KILLED | 3 | `test_viewer_errors_are_distinct_and_do_not_echo_identity[wrong-subject-SubjectNotParticipantError-anonymous]` |
| 53 | drop self-view check | KILLED | 3 | `test_viewer_errors_are_distinct_and_do_not_echo_identity[self-SelfViewerError-anonymous]` |
| 54 | drop viewer membership | KILLED | 3 | `test_viewer_errors_are_distinct_and_do_not_echo_identity[outsider-ViewerNotParticipantError-anonymous]` |
| 55 | accept duplicate participants | KILLED | 1 | `test_conversation_state_requires_exactly_two_distinct_participants[duplicate]` |
| 56 | expose private pre-Reveal field | KILLED | 5 | `test_pre_reveal_type_and_serialized_keys_are_exactly_the_allow_list` |
| 57 | leak identity repr | KILLED | 4 | `test_private_records_never_print_identity_values[identity]` |
| 58 | leak Applicant repr | KILLED | 5 | `test_existing_date_of_birth_holders_also_redact_private_representations[repr-applicant]` |
| 59 | echo rejected private About | KILLED | 3 | `test_profile_errors_never_print_private_rejected_text[legal-name]` |
| 60 | allow shallow private copy | KILLED | 8 | `test_private_records_refuse_generic_serialization[copy-applicant]` |
| 61 | allow deep private copy/asdict | KILLED | 20 | `test_private_records_refuse_generic_serialization[deepcopy-applicant]` |
| 62 | allow private pickle | KILLED | 14 | `test_private_records_refuse_generic_serialization[pickle-applicant]` |
| 63 | allow direct private reduction | KILLED | 8 | `test_private_records_refuse_generic_serialization[reduce-applicant]` |
| 64 | SDK import in domain | KILLED | 1 | `test_domain_imports_only_the_standard_library_and_its_own_package` |
| 65 | real clock in domain | KILLED | 1 | `test_domain_does_not_read_the_system_clock` |
| 66 | unwrap outside allowed function | KILLED | 1 | `test_production_unwrap_sites_are_exactly_the_approved_functions` |
| 67 | wrapper repr leaks | KILLED | 4 | `test_all_scalar_rendering_is_redacted[repr-legal_name]` |
| 68 | drop scalar str redaction | KILLED | 9 | `test_all_scalar_rendering_is_redacted[str-legal_name]` |
| 69 | drop scalar format redaction | KILLED | 13 | `test_all_scalar_rendering_is_redacted[format-legal_name]` |
| 70 | private equality against plain value | KILLED | 4 | `test_equality_never_compares_equal_to_a_plain_value[name]` |
| 71 | allow wrapper hashing | KILLED | 4 | `test_scalars_are_opaque_immutable_slotted_and_unhashable[legal_name]` |
| 72 | expose PrivateDate year | KILLED | 1 | `test_private_date_exposes_no_calendar_accessors[year]` |
| 73 | view holds plain private text | KILLED | 8 | `test_reveal_adds_identity_without_removing_the_public_profile` |
| 74 | global Reveal cache by Member | KILLED | 3 | `test_reveal_in_one_pair_does_not_reveal_the_subject_in_another` |
