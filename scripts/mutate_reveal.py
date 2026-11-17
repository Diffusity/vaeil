"""T8 product faults using the existing exact-restore runner; run alone."""
from mutate_persistence import ROOT, BOUNDARY, replace_once, main

D = ROOT / 'src/vaeil/domain/reveal.py'
A = ROOT / 'src/vaeil/application/reveal.py'
S = ROOT / 'src/vaeil/adapters/persistence.py'
H = ROOT / 'src/vaeil/http_reveal.py'
V = ROOT / 'src/vaeil/domain/member.py'
P = 'tests/test_t8_reveal.py::'
T = 'tests/test_t8_application.py::'
R = 'tests/test_t8_repository.py::'
F = 'tests/test_t8_http.py::'
MUTATIONS = []


def add(name, path, old, new, test):
    MUTATIONS.append((name, path, replace_once(old, new), test))


for constant, wrong in [('MIN_DELIVERED_MESSAGES = 20','MIN_DELIVERED_MESSAGES = 19'),
                        ('MIN_DELIVERED_MESSAGES = 20','MIN_DELIVERED_MESSAGES = 21'),
                        ('MIN_MESSAGES_PER_MEMBER = 5','MIN_MESSAGES_PER_MEMBER = 4'),
                        ('MIN_MESSAGES_PER_MEMBER = 5','MIN_MESSAGES_PER_MEMBER = 6'),
                        ('timedelta(hours=72)','timedelta(hours=71)'),
                        ('timedelta(hours=72)','timedelta(hours=73)')]:
    add('threshold '+wrong, D, constant, wrong, P+'test_all_threshold_boundaries')
MUTATIONS.append(('measure DST wall time', D, lambda source: source.replace('now = now.astimezone(timezone.utc)', 'now = now').replace('min(row.delivered_at.astimezone(timezone.utc) for row in delivered)', 'min(row.delivered_at for row in delivered)'), P+'test_72_hours_means_elapsed_utc_time_across_a_dst_change'))
add('unilateral completion', D, 'complete = updated.consented_member_ids == frozenset(conversation.participant_ids)',
    'complete = bool(updated.consented_member_ids)', P+'test_bilateral_consent_withdrawal_idempotence_and_irreversibility')
add('ignore withdrawal', D, 'else consents.consented_member_ids - {actor_id}',
    'else consents.consented_member_ids', P+'test_bilateral_consent_withdrawal_idempotence_and_irreversibility')
add('permit completed withdrawal', D, 'if not consent:', 'if False:',
    P+'test_bilateral_consent_withdrawal_idempotence_and_irreversibility')
add('ignore participant authority', A, 'if actor.principal_id not in conversation.participant_ids:', 'if False:',
    T+'test_role_pair_block_guards_and_active_slot_before_completion')
add('trust forged Member role', A, 'principal.role is not Role.MEMBER', 'actor.role is not Role.MEMBER',
    T+'test_role_pair_block_guards_and_active_slot_before_completion')
add('count Withheld evidence', S, 'messages.c.outcome != m.MessageOutcome.WITHHELD.value', 'True',
    T+'test_withheld_and_creation_time_cannot_satisfy_threshold_late_release_counts_once')
add('use creation not actual delivery', A, 'row.sender_id, row.delivered_at)', 'row.sender_id, row.created_at)',
    T+'test_twenty_recent_deliveries_cannot_use_old_creation_time')
add('omit completion audit', A, 'unit.append_audit(AuditEvent(', 'unused = (AuditEvent(',
    T+'test_durable_bilateral_reveal_exact_payload_audit_slot_release_and_isolation')
add('audit again on repeated consent', A, 'if changed.revealed_now:', 'if changed.conversation.revealed:',
    T+'test_durable_bilateral_reveal_exact_payload_audit_slot_release_and_isolation')
add('commit Reveal before audit', A, '                unit.append_audit(AuditEvent(',
    '                unit.commit()\n                unit.append_audit(AuditEvent(', T+'test_reveal_and_consent_rollback_if_audit_fails')
add('share consent across Conversations', S, 'reveal_consents.c.conversation_id == conversation_id)).scalars()',
    "reveal_consents.c.conversation_id == 'ab')).scalars()", T+'test_durable_bilateral_reveal_exact_payload_audit_slot_release_and_isolation')
add('retain withdrawn consent in storage', S, 'self._execute(delete(reveal_consents).where(reveal_consents.c.conversation_id == consents.conversation_id))',
    'pass', R+'test_pair_consents_roundtrip_and_rollback')
add('expose pre-Reveal identity', A, 'conversation=conversation.reveal_state())',
    'conversation=type(conversation.reveal_state())(conversation.conversation_id, conversation.participant_ids, True))',
    T+'test_durable_bilateral_reveal_exact_payload_audit_slot_release_and_isolation')
add('add DOB to revealed JSON', V, '    return result',
    '    if type(view) is RevealedMemberView:\n        result["date_of_birth"] = "2000-01-01"\n    return result',
    F+'test_exact_status_and_partner_payload_only_after_both_consents')
MUTATIONS.append(('accept client Reveal flag', H, lambda source: source.replace('exact(body, set())', "exact(body, set(), {'revealed'})"), F+'test_session_role_pair_origin_and_safe_unknown_input_guards'))
MUTATIONS.append(('bypass all Block checks', D,
    lambda source: replace_once('if conversation.blocked:', 'if False:')(
        replace_once('return (conversation.active and', 'return (not conversation.revealed and')(source)),
    T+'test_role_pair_block_guards_and_active_slot_before_completion'))
MUTATIONS.append(('unwrap outside approved Reveal sites', A,
    lambda source: source+'\n\ndef unsafe_reveal_identity(value):\n    return value.UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE()\n', BOUNDARY))

if __name__ == '__main__':
    main(MUTATIONS, 'docs/audit/t8-mutations.json')
