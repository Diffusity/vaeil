"""T7 faults through the existing exact-restore runner. Run alone."""
from mutate_persistence import ROOT, BOUNDARY, replace_once, main

DOMAIN = ROOT / 'src/vaeil/domain/messaging.py'
APP = ROOT / 'src/vaeil/application/messaging.py'
SQL = ROOT / 'src/vaeil/adapters/persistence.py'
HTTP = ROOT / 'src/vaeil/http_messaging.py'
CONVERSATION = ROOT / 'src/vaeil/domain/conversation.py'
RUNTIME = ROOT / 'src/vaeil/runtime.py'
A = 'tests/test_t7_application.py::'
R = 'tests/test_t7_repository.py::'
P = 'tests/test_t7_assessment.py::'
MUTATIONS = []


def add(name, path, old, new, test):
    MUTATIONS.append((name, path, replace_once(old, new), test))


add('auto-approve scanner-clean baseline', APP,
    '        if self.moderator is None:\n            return ModerationFailure.UNAVAILABLE',
    '        if self.moderator is None:\n            return Verdict.APPROVED',
    A + 'test_baseline_manual_review_then_one_audited_delivery_at_release_time')
add('clear identifier reasons', DOMAIN,
    'reasons = scan_identifiers(normalize_message_text(text)).reasons', 'reasons = ()',
    P + 'test_approved_assessment_preserves_reason_and_pair_reveal_policy')
add('deliver technical or review Withheld', DOMAIN,
    'return MessageAssessment(MessageOutcome.WITHHELD, reasons, reason)',
    'return MessageAssessment(MessageOutcome.DELIVERED, reasons, reason)',
    P + 'test_review_and_technical_outcomes_never_deliver_even_when_flagged')
add('ignore Conversation Reveal', DOMAIN,
    'reasons and conversation.identifier_escalation_required', 'reasons and True',
    P + 'test_approved_assessment_preserves_reason_and_pair_reveal_policy')
for limit in (1999, 2001):
    add(f'Message limit {limit}', DOMAIN, 'MAX_MESSAGE_CODE_POINTS = 2000', f'MAX_MESSAGE_CODE_POINTS = {limit}',
        P + ('test_normalized_code_point_boundary_and_chat_whitespace_are_accepted' if limit == 1999 else 'test_invalid_text_is_refused_without_echo'))
add('drop control refusal', DOMAIN,
    "if any(unicodedata.category(char) in {'Cc', 'Cf', 'Cs'} and char not in {'\\n', '\\t'} for char in text):",
    'if False:', P + 'test_invalid_text_is_refused_without_echo')
add('bypass stored role', APP,
    'principal.role is not role', 'False',
    A + 'test_roles_pair_and_request_collision_cannot_bypass_policy')
add('bypass participant pair', APP,
    'if actor.principal_id not in conversation.participant_ids:', 'if False:',
    A + 'test_roles_pair_and_request_collision_cannot_bypass_policy')
add('bypass Conversation Block policy', CONVERSATION,
    'return not self.blocked', 'return True',
    A + 'test_block_during_external_call_prevents_delivery')
add('omit fresh state recheck after moderation', APP,
    '        moderation = self._moderate(body)\n        with self.repository.transaction() as unit:\n            conversation = self._pair(unit, actor, conversation_id, sending=True)',
    '        moderation = self._moderate(body)\n        with self.repository.transaction() as unit:\n            conversation = conversation',
    A + 'test_block_during_external_call_prevents_delivery')
add('omit request replay lookup', APP,
    'previous = unit.find_message_by_request(conversation_id, actor.principal_id, key)', 'previous = None',
    A + 'test_roles_pair_and_request_collision_cannot_bypass_policy')
add('remove durable request unique constraint', SQL,
    "    UniqueConstraint('conversation_id', 'sender_id', 'request_id', name='message_request_owner'),\n", '',
    R + 'test_database_request_and_review_uniqueness_cannot_be_bypassed_by_another_writer')
add('remove durable review digest unique constraint', SQL,
    "    UniqueConstraint('conversation_id', 'sender_id', 'text_digest', name='review_digest_owner'),\n", '',
    R + 'test_database_request_and_review_uniqueness_cannot_be_bypassed_by_another_writer')
add('ignore existing review text before moderation', SQL,
    '    def review_text_exists(self, conversation_id, sender_id, digest):\n',
    '    def review_text_exists(self, conversation_id, sender_id, digest):\n        return False\n',
    A + 'test_model_review_prevents_normalized_resend_even_after_discard')
add('permit repeated Admin release', APP,
    'if message.review_state is not ReviewState.PENDING or unit.message_is_processing(message_id):',
    'if False:', A + 'test_baseline_manual_review_then_one_audited_delivery_at_release_time')
add('drop terminal storage guard', SQL,
    '        if not allowed:\n            raise m.MessageConflictError',
    '        if False:\n            raise m.MessageConflictError',
    R + 'test_review_reserves_digest_and_terminal_delivery_is_immutable')
add('omit human decision audit', APP,
    '            self._event(unit, kind, finished, actor.principal_id)', '            pass',
    A + 'test_baseline_manual_review_then_one_audited_delivery_at_release_time')
add('commit human delivery before audit', APP,
    '            unit.update_message(finished)\n            self._event',
    '            unit.update_message(finished)\n            unit.commit()\n            self._event',
    A + 'test_failed_release_audit_rolls_back_delivery_and_preserves_review')
add('timestamp release at submission', APP,
    'provenance=MessageProvenance.HUMAN, delivered_at=self.clock.now()',
    'provenance=MessageProvenance.HUMAN, delivered_at=message.created_at',
    A + 'test_baseline_manual_review_then_one_audited_delivery_at_release_time')
add('show pending sender receipts to the other participant', APP,
    'unit.list_sender_messages(conversation_id, actor.principal_id)',
    'unit.list_sender_messages(conversation_id, conversation.participant_ids[0])',
    A + 'test_baseline_manual_review_then_one_audited_delivery_at_release_time')
add('count Withheld as delivered storage', SQL,
    'messages.c.outcome != m.MessageOutcome.WITHHELD.value',
    'messages.c.outcome == m.MessageOutcome.WITHHELD.value',
    R + 'test_canonical_message_roundtrip_redacted_and_not_delivered')
add('copy Message body into audit identifier', APP,
    'actor_id, message.message_id, kind, reasons', 'actor_id, message.text, kind, reasons',
    A + 'test_baseline_manual_review_then_one_audited_delivery_at_release_time')
add('copy Message body into review queue', SQL,
    'text_digest=message.text_digest, message_id=message.message_id',
    'text_digest=message.text_digest, message_id=message.text',
    A + 'test_baseline_manual_review_then_one_audited_delivery_at_release_time')
add('allow demo failure config in production', RUNTIME,
    "if switch not in {'0', '1'} or (switch == '1' and os.environ.get('VAEIL_ENV') != 'demo'):",
    'if False:', 'tests/test_t7_runtime.py::test_runtime_failure_switch_never_enables_approval')
add('accept client Reveal flag', HTTP,
    "exact(body, {'request_id', 'text'})", "exact(body, {'request_id', 'text'}, {'revealed'})",
    'tests/test_t7_http.py::test_send_cannot_supply_authority_or_production_approval_switch')
MUTATIONS.append(('extract identity from unapproved Message helper', APP,
    lambda source: source + '\n\ndef unsafe_message_identity(value):\n    return value.UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE()\n', BOUNDARY))


add('omit model-review decision provenance', APP,
    'provenance=MessageProvenance.MODEL if type(moderation) is Verdict else MessageProvenance.NONE,',
    'provenance=MessageProvenance.MODEL if delivered else MessageProvenance.NONE,',
    A + 'test_model_review_prevents_normalized_resend_even_after_discard')


add('omit review lock recheck after moderation', APP,
    "            if unit.review_text_exists(conversation_id, actor.principal_id, digest):\n                raise MessageConflictError('This Message text entered review while it was checked.')",
    "            if False:\n                raise MessageConflictError('This Message text entered review while it was checked.')",
    A + 'test_review_lock_created_during_moderation_prevents_matching_late_delivery')
add('advertise retry of already reviewed matching text', APP,
    'and open_for_chat and not review_locked', 'and open_for_chat',
    A + 'test_manual_review_digest_prevents_two_pending_copies')


if __name__ == '__main__':
    main(MUTATIONS, 'docs/audit/t7-mutations.json')
