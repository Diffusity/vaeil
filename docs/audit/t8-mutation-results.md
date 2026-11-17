# T8 mutation results

Run writers alone, then normal checks. Local backend faults:24/24; browser faults:2/2. Exact source restoration is pinned by SHA256 in the raw artifacts. The shared-database CI matrix repeats database faults against disposable PostgreSQL.

| Fault | Local backend | Result | Killing test |
| --- | --- | --- | --- |
| threshold MIN_DELIVERED_MESSAGES = 19 | domain | KILLED | `tests/test_t8_reveal.py::test_all_threshold_boundaries` |
| threshold MIN_DELIVERED_MESSAGES = 21 | domain | KILLED | `tests/test_t8_reveal.py::test_all_threshold_boundaries` |
| threshold MIN_MESSAGES_PER_MEMBER = 4 | domain | KILLED | `tests/test_t8_reveal.py::test_all_threshold_boundaries` |
| threshold MIN_MESSAGES_PER_MEMBER = 6 | domain | KILLED | `tests/test_t8_reveal.py::test_all_threshold_boundaries` |
| threshold timedelta(hours=71) | domain | KILLED | `tests/test_t8_reveal.py::test_all_threshold_boundaries` |
| threshold timedelta(hours=73) | domain | KILLED | `tests/test_t8_reveal.py::test_all_threshold_boundaries` |
| measure DST wall time | domain | KILLED | `tests/test_t8_reveal.py::test_72_hours_means_elapsed_utc_time_across_a_dst_change` |
| unilateral completion | domain | KILLED | `tests/test_t8_reveal.py::test_bilateral_consent_withdrawal_idempotence_and_irreversibility` |
| ignore withdrawal | domain | KILLED | `tests/test_t8_reveal.py::test_bilateral_consent_withdrawal_idempotence_and_irreversibility` |
| permit completed withdrawal | domain | KILLED | `tests/test_t8_reveal.py::test_bilateral_consent_withdrawal_idempotence_and_irreversibility` |
| ignore participant authority | sqlite | KILLED | `tests/test_t8_application.py::test_role_pair_block_guards_and_active_slot_before_completion` |
| trust forged Member role | sqlite | KILLED | `tests/test_t8_application.py::test_role_pair_block_guards_and_active_slot_before_completion` |
| count Withheld evidence | sqlite | KILLED | `tests/test_t8_application.py::test_withheld_and_creation_time_cannot_satisfy_threshold_late_release_counts_once` |
| use creation not actual delivery | sqlite | KILLED | `tests/test_t8_application.py::test_twenty_recent_deliveries_cannot_use_old_creation_time` |
| omit completion audit | sqlite | KILLED | `tests/test_t8_application.py::test_durable_bilateral_reveal_exact_payload_audit_slot_release_and_isolation` |
| audit again on repeated consent | sqlite | KILLED | `tests/test_t8_application.py::test_durable_bilateral_reveal_exact_payload_audit_slot_release_and_isolation` |
| commit Reveal before audit | sqlite | KILLED | `tests/test_t8_application.py::test_reveal_and_consent_rollback_if_audit_fails` |
| share consent across Conversations | sqlite | KILLED | `tests/test_t8_application.py::test_durable_bilateral_reveal_exact_payload_audit_slot_release_and_isolation` |
| retain withdrawn consent in storage | sqlite | KILLED | `tests/test_t8_repository.py::test_pair_consents_roundtrip_and_rollback` |
| expose pre-Reveal identity | sqlite | KILLED | `tests/test_t8_application.py::test_durable_bilateral_reveal_exact_payload_audit_slot_release_and_isolation` |
| add DOB to revealed JSON | sqlite | KILLED | `tests/test_t8_http.py::test_exact_status_and_partner_payload_only_after_both_consents` |
| accept client Reveal flag | sqlite | KILLED | `tests/test_t8_http.py::test_session_role_pair_origin_and_safe_unknown_input_guards` |
| bypass all Block checks | sqlite | KILLED | `tests/test_t8_application.py::test_role_pair_block_guards_and_active_slot_before_completion` |
| unwrap outside approved Reveal sites | architecture | KILLED | `tests/test_private_unwrap_boundary.py::test_production_unwrap_sites_are_exactly_the_approved_functions` |
| ignore withdrawal action | browser | KILLED | `frontend/tests/reveal.spec.js` |
| offer consent while ineligible | browser | KILLED | `frontend/tests/reveal.spec.js` |

Initial partial run: single-endpoint UTC removal survived because the other conversion still gave elapsed-time semantics; final category fault removes both. The original rollback-only consent test did not detect committed deletion omission; a stricter committed-empty-consent assertion was added, preserving all prior cases. An initial script string-literal error occurred before mutation, and a duplicate PUT/DELETE validation anchor was refined to both routes. Partial runs are not counted as successful matrices. No test was weakened.
