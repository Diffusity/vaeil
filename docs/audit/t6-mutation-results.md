# T6 mutation results

Final review-fix local run: **45/45 killed**, exact source-byte restoration verified. PostgreSQL variants run in disposable-database CI; local skips are not passes. Existing persistence local14/14; earlier CI27/27.

| Mutation | Backend | Result | Killing test |
| --- | --- | --- | --- |
| drop login NFKC | sqlite | KILLED | `tests/test_t6_application.py::test_login_identity_uses_nfkc_and_casefold_not_lower` |
| replace login casefold with lower | sqlite | KILLED | `tests/test_t6_application.py::test_login_identity_uses_nfkc_and_casefold_not_lower` |
| skip age gate | sqlite | KILLED | `tests/test_t6_application.py::test_underage_never_calls_model_or_consumes_invite` |
| consume Invite before age validation | sqlite | KILLED | `tests/test_t6_application.py::test_underage_never_calls_model_or_consumes_invite` |
| skip pre-vetting Invite availability | sqlite | KILLED | `tests/test_t6_application.py::test_unknown_invite_never_reaches_vetting_or_stores_an_applicant` |
| skip atomic Invite consumption | sqlite | KILLED | `tests/test_t6_application.py::test_same_invite_concurrent_applications_have_one_atomic_winner` |
| auto-admit clean or injected note | sqlite | KILLED | `tests/test_t6_application.py::test_runtime_human_review_never_auto_admits_clean_or_injection_note` |
| send Applicant including DOB to model | domain | KILLED | `tests/test_t6_note.py::test_vetting_port_receives_only_the_application_note` |
| make model rejection representable | domain | KILLED | `tests/test_vetting.py::test_verdict_cannot_represent_rejection` |
| drop note NFKC normalization | domain | KILLED | `tests/test_t6_note.py::test_note_normalization_and_accepted_boundaries` |
| note minimum 19 | domain | KILLED | `tests/test_t6_note.py` |
| note minimum 21 | domain | KILLED | `tests/test_t6_note.py` |
| note maximum 499 | domain | KILLED | `tests/test_t6_note.py` |
| note maximum 501 | domain | KILLED | `tests/test_t6_note.py` |
| drop note controls | domain | KILLED | `tests/test_t6_note.py::test_invalid_note_refused_without_echoing_input` |
| drop note identifier check | domain | KILLED | `tests/test_t6_note.py::test_invalid_note_refused_without_echoing_input` |
| drop note self-name check | domain | KILLED | `tests/test_t6_note.py::test_whole_word_note_false_positive_can_be_rephrased` |
| use substring mode for free text | domain | KILLED | `tests/test_t6_note.py::test_note_normalization_and_accepted_boundaries` |
| bypass server role check | sqlite | KILLED | `tests/test_t6_application.py::test_approved_member_cannot_act_as_admin_even_with_forged_role` |
| omit session expiry | sqlite | KILLED | `tests/test_t6_application.py::test_session_boundary_logout_and_unknown_token` |
| omit logout revocation | sqlite | KILLED | `tests/test_t6_application.py::test_session_boundary_logout_and_unknown_token` |
| drop admission audit | sqlite | KILLED | `tests/test_t6_application.py::test_admin_rejection_is_human_terminal_and_audited` |
| commit Invite before application and audit | sqlite | KILLED | `tests/test_t6_application.py::test_failed_audit_rolls_back_application_and_invite_consumption` |
| ignore fixed-once Pseudonym | sqlite | KILLED | `tests/test_t6_profiles.py::test_private_draft_then_complete_then_profile_update_preserves_identity` |
| drop profile identifier check | sqlite | KILLED | `tests/test_t6_profiles.py::test_draft_writes_use_the_same_profile_safety_policies` |
| remove normalized Pseudonym uniqueness | sqlite | KILLED | `tests/test_repository_contract.py::test_concurrent_normalized_claims_commit_exactly_one_owner` |
| drop cookie HttpOnly | sqlite | KILLED | `tests/test_t6_http.py::test_registration_login_cookie_restricted_profile_and_logout` |
| drop cookie Secure | sqlite | KILLED | `tests/test_t6_http.py::test_registration_login_cookie_restricted_profile_and_logout` |
| drop same-origin CSRF check | sqlite | KILLED | `tests/test_t6_http.py::test_csrf_cross_origin_and_absent_origin_are_refused` |
| copy raw session token into JSON | sqlite | KILLED | `tests/test_t6_http.py::test_registration_login_cookie_restricted_profile_and_logout` |
| drop password length policy | domain | KILLED | `tests/test_t6_passwords.py::test_password_policy_refuses_without_echoing` |
| replace scrypt with fast hash | domain | KILLED | `tests/test_t6_passwords.py::test_verifier_accepts_a_frozen_independent_scrypt_vector_and_versioned_format` |
| use ordinary secret comparison | domain | KILLED | `tests/test_t6_passwords.py::test_verification_respects_the_vetted_constant_time_comparison` |
| increase password memory concurrency cap | domain | KILLED | `tests/test_t6_passwords.py::test_password_workers_refuse_overlap_instead_of_allocating_unbounded_memory` |
| unwrap from unauthorized login helper | architecture | KILLED | `tests/test_private_unwrap_boundary.py::test_production_unwrap_sites_are_exactly_the_approved_functions` |
| wrapper repr leaks private values | domain | KILLED | `tests/test_opaque_private_values.py::test_all_scalar_rendering_is_redacted` |
| hold repository lock during password verification | sqlite | KILLED | `tests/test_t6_application.py::test_password_verification_does_not_hold_the_repository_write_lock` |
| map duplicate email to infrastructure failure | sqlite | KILLED | `tests/test_t6_http.py::test_duplicate_email_conflict_rolls_back_invite_and_allows_retry` |
| disable remote TLS verification | domain | KILLED | `tests/test_t6_repository.py::test_remote_postgres_uses_verified_tls_even_if_url_requests_disable` |
| remove remote connect bound | domain | KILLED | `tests/test_t6_repository.py::test_remote_postgres_uses_verified_tls_even_if_url_requests_disable` |
| remove remote statement bound | domain | KILLED | `tests/test_t6_repository.py::test_remote_postgres_uses_verified_tls_even_if_url_requests_disable` |
| remove remote lock bound | domain | KILLED | `tests/test_t6_repository.py::test_remote_postgres_uses_verified_tls_even_if_url_requests_disable` |
| copy application note into recipient JSON | sqlite | KILLED | `tests/test_t6_profiles.py::test_persisted_application_note_never_enters_recipient_views` |
| skip registration UTF-8 validation | sqlite | KILLED | `tests/test_t6_http.py::test_registration_refuses_non_utf8_text_without_echo_or_invite_consumption` |
| skip profile UTF-8 validation | sqlite | KILLED | `tests/test_t6_http.py::test_profile_refuses_non_utf8_about_before_commit` |
