# T7 mutation results

Final local backend30/30 and browser5/5 killed; exact source restoration verified. PostgreSQL is exercised separately in disposable CI; local skips are not passes. Initial redundant application-only Block guard removal survived because pure policy still enforced Block; the category fault now disables canonical Conversation policy, tests unchanged. An initial UI harness CRLF anchor failure restored source/build and is not counted as a complete run.

| Mutation | Local target | Result | Killing test |
| --- | --- | --- | --- |
| auto-approve scanner-clean baseline | sqlite | KILLED | `tests/test_t7_application.py::test_baseline_manual_review_then_one_audited_delivery_at_release_time` |
| clear identifier reasons | domain | KILLED | `tests/test_t7_assessment.py::test_approved_assessment_preserves_reason_and_pair_reveal_policy` |
| deliver technical or review Withheld | domain | KILLED | `tests/test_t7_assessment.py::test_review_and_technical_outcomes_never_deliver_even_when_flagged` |
| ignore Conversation Reveal | domain | KILLED | `tests/test_t7_assessment.py::test_approved_assessment_preserves_reason_and_pair_reveal_policy` |
| Message limit 1999 | domain | KILLED | `tests/test_t7_assessment.py::test_normalized_code_point_boundary_and_chat_whitespace_are_accepted` |
| Message limit 2001 | domain | KILLED | `tests/test_t7_assessment.py::test_invalid_text_is_refused_without_echo` |
| drop control refusal | domain | KILLED | `tests/test_t7_assessment.py::test_invalid_text_is_refused_without_echo` |
| bypass stored role | sqlite | KILLED | `tests/test_t7_application.py::test_roles_pair_and_request_collision_cannot_bypass_policy` |
| bypass participant pair | sqlite | KILLED | `tests/test_t7_application.py::test_roles_pair_and_request_collision_cannot_bypass_policy` |
| bypass Conversation Block policy | sqlite | KILLED | `tests/test_t7_application.py::test_block_during_external_call_prevents_delivery` |
| omit fresh state recheck after moderation | sqlite | KILLED | `tests/test_t7_application.py::test_block_during_external_call_prevents_delivery` |
| omit request replay lookup | sqlite | KILLED | `tests/test_t7_application.py::test_roles_pair_and_request_collision_cannot_bypass_policy` |
| remove durable request unique constraint | sqlite | KILLED | `tests/test_t7_repository.py::test_database_request_and_review_uniqueness_cannot_be_bypassed_by_another_writer` |
| remove durable review digest unique constraint | sqlite | KILLED | `tests/test_t7_repository.py::test_database_request_and_review_uniqueness_cannot_be_bypassed_by_another_writer` |
| ignore existing review text before moderation | sqlite | KILLED | `tests/test_t7_application.py::test_model_review_prevents_normalized_resend_even_after_discard` |
| permit repeated Admin release | sqlite | KILLED | `tests/test_t7_application.py::test_baseline_manual_review_then_one_audited_delivery_at_release_time` |
| drop terminal storage guard | sqlite | KILLED | `tests/test_t7_repository.py::test_review_reserves_digest_and_terminal_delivery_is_immutable` |
| omit human decision audit | sqlite | KILLED | `tests/test_t7_application.py::test_baseline_manual_review_then_one_audited_delivery_at_release_time` |
| commit human delivery before audit | sqlite | KILLED | `tests/test_t7_application.py::test_failed_release_audit_rolls_back_delivery_and_preserves_review` |
| timestamp release at submission | sqlite | KILLED | `tests/test_t7_application.py::test_baseline_manual_review_then_one_audited_delivery_at_release_time` |
| show pending sender receipts to the other participant | sqlite | KILLED | `tests/test_t7_application.py::test_baseline_manual_review_then_one_audited_delivery_at_release_time` |
| count Withheld as delivered storage | sqlite | KILLED | `tests/test_t7_repository.py::test_canonical_message_roundtrip_redacted_and_not_delivered` |
| copy Message body into audit identifier | sqlite | KILLED | `tests/test_t7_application.py::test_baseline_manual_review_then_one_audited_delivery_at_release_time` |
| copy Message body into review queue | sqlite | KILLED | `tests/test_t7_application.py::test_baseline_manual_review_then_one_audited_delivery_at_release_time` |
| allow demo failure config in production | sqlite | KILLED | `tests/test_t7_runtime.py::test_runtime_failure_switch_never_enables_approval` |
| accept client Reveal flag | sqlite | KILLED | `tests/test_t7_http.py::test_send_cannot_supply_authority_or_production_approval_switch` |
| extract identity from unapproved Message helper | architecture | KILLED | `tests/test_private_unwrap_boundary.py::test_production_unwrap_sites_are_exactly_the_approved_functions` |
| omit model-review decision provenance | sqlite | KILLED | `tests/test_t7_application.py::test_model_review_prevents_normalized_resend_even_after_discard` |
| omit review lock recheck after moderation | sqlite | KILLED | `tests/test_t7_application.py::test_review_lock_created_during_moderation_prevents_matching_late_delivery` |
| advertise retry of already reviewed matching text | sqlite | KILLED | `tests/test_t7_application.py::test_manual_review_digest_prevents_two_pending_copies` |
| discard unrelated composer draft | browser | KILLED | `frontend/tests/conversation.spec.js: older withheld` |
| accept contradictory review retry flags | browser | KILLED | `frontend/tests/conversation.spec.js: inconsistent` |
| enable duplicate send while checking | browser | KILLED | `frontend/tests/conversation.spec.js: checking disables` |
| reuse completed request key for deliberate technical retry | browser | KILLED | `frontend/tests/conversation.spec.js: checking disables` |
| promise forbidden retry actions | browser | KILLED | `frontend/tests/conversation.spec.js: never promises` |
