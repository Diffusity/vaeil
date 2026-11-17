"""Approved pure Reveal seam, independent literal boundary oracles."""
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
import pytest
from vaeil.domain.conversation import Conversation
from vaeil.domain.reveal import (
    DeliveredMessageEvidence, RevealConsents, RevealEvidenceError, RevealActorError,
    RevealBlockedError, RevealNotEligibleError, RevealCompletedError,
    is_reveal_eligible, change_reveal_consent,
)

FIRST = datetime(2026, 11, 1, 12, tzinfo=timezone.utc)
NOW = datetime(2026, 11, 4, 12, tzinfo=timezone.utc)
PAIR = Conversation('ab', ('a', 'b'))


def evidence(a=15, b=5, conversation_id='ab'):
    return tuple(DeliveredMessageEvidence(str(index), conversation_id, sender, FIRST)
                 for index, sender in enumerate(['a'] * a + ['b'] * b))


@pytest.mark.parametrize('a,b,elapsed,expected', [
    (14, 5, timedelta(hours=72), False),
    (15, 5, timedelta(hours=72), True),
    (16, 4, timedelta(hours=72), False),
    (4, 16, timedelta(hours=72), False),
    (5, 15, timedelta(hours=72), True),
    (15, 5, timedelta(hours=72, microseconds=-1), False),
    (15, 5, timedelta(hours=72, microseconds=1), True),
    (0, 0, timedelta(hours=72), False),
], ids=['total19','total20','side4','other-side4','side5','before72h','after72h','empty'])
def test_all_threshold_boundaries(a, b, elapsed, expected):
    assert is_reveal_eligible(PAIR, delivered=evidence(a,b), now=FIRST+elapsed) is expected


def test_first_actual_delivery_not_last_or_input_order_starts_the_clock():
    rows = evidence()
    later = tuple(replace(row, delivered_at=FIRST+timedelta(hours=71)) for row in rows[1:])
    assert is_reveal_eligible(PAIR, delivered=later+rows[:1], now=NOW)
    assert not is_reveal_eligible(PAIR, delivered=tuple(replace(row, delivered_at=NOW) for row in rows), now=NOW)


@pytest.mark.parametrize('bad', ['duplicate','conversation','sender','naive','future','type'])
def test_invalid_evidence_cannot_inflate_or_supply_eligibility(bad):
    rows = evidence()
    if bad == 'duplicate':
        rows = rows[:-1]+rows[:1]
    elif bad == 'conversation':
        rows = (replace(rows[0], conversation_id='ac'),)+rows[1:]
    elif bad == 'sender':
        rows = (replace(rows[0], sender_id='outsider'),)+rows[1:]
    elif bad == 'naive':
        rows = (replace(rows[0], delivered_at=FIRST.replace(tzinfo=None)),)+rows[1:]
    elif bad == 'future':
        rows = (replace(rows[0], delivered_at=NOW+timedelta(seconds=1)),)+rows[1:]
    else:
        rows = ('PrivateCanaryInvalid',)
    with pytest.raises(RevealEvidenceError) as caught:
        is_reveal_eligible(PAIR, delivered=rows, now=NOW)
    assert 'PrivateCanaryInvalid' not in str(caught.value)


def test_bilateral_consent_withdrawal_idempotence_and_irreversibility():
    empty = RevealConsents('ab', frozenset())
    def act(state, actor, consent, conversation=PAIR):
        return change_reveal_consent(conversation, consents=state, actor_id=actor, consent=consent, delivered=evidence(), now=NOW)
    first = act(empty, 'a', True)
    assert first.consents.consented_member_ids == frozenset({'a'})
    assert not first.conversation.revealed and not first.revealed_now
    assert act(first.consents, 'a', True) == first
    assert act(first.consents, 'b', False).consents == first.consents
    assert act(first.consents, 'a', False).consents == empty
    done = act(first.consents, 'b', True)
    assert done.revealed_now and done.conversation.revealed
    assert not done.conversation.active and done.conversation.open_for_chat
    assert not done.conversation.identifier_escalation_required
    repeated = act(done.consents, 'b', True, done.conversation)
    assert not repeated.revealed_now and repeated.conversation == done.conversation
    with pytest.raises(RevealCompletedError):
        act(done.consents, 'a', False, done.conversation)


@pytest.mark.parametrize('actor,consent,conversation,state,error', [
    ('c', True, PAIR, RevealConsents('ab', frozenset()), RevealActorError),
    ('a', True, replace(PAIR, blocked=True), RevealConsents('ab', frozenset()), RevealBlockedError),
    ('a', True, PAIR, RevealConsents('ac', frozenset()), RevealEvidenceError),
    ('a', True, PAIR, RevealConsents('ab', frozenset({'c'})), RevealEvidenceError),
    ('a', 'true', PAIR, RevealConsents('ab', frozenset()), RevealEvidenceError),
])
def test_consent_authority_and_state_are_validated(actor, consent, conversation, state, error):
    with pytest.raises(error):
        change_reveal_consent(conversation, consents=state, actor_id=actor, consent=consent, delivered=evidence(), now=NOW)


def test_ineligible_cannot_consent_and_does_not_contaminate_another_pair():
    state = RevealConsents('ab', frozenset())
    with pytest.raises(RevealNotEligibleError):
        change_reveal_consent(PAIR, consents=state, actor_id='a', consent=True, delivered=evidence(14,5), now=NOW)
    assert change_reveal_consent(PAIR, consents=state, actor_id='a', consent=False, delivered=(), now=NOW).consents == state
    other = Conversation('ac', ('a','c'))
    with pytest.raises(RevealEvidenceError):
        change_reveal_consent(other, consents=state, actor_id='a', consent=True, delivered=evidence(), now=NOW)
    assert not other.revealed and other.active


def test_body_free_shapes_are_frozen_slotted_and_no_ceremony_on_closed_pair():
    from dataclasses import fields
    row, state = evidence()[0], RevealConsents('ab', frozenset())
    assert {field.name for field in fields(row)} == {'message_id','conversation_id','sender_id','delivered_at'}
    for value in (row,state):
        assert not hasattr(value, '__dict__')
        with pytest.raises(FrozenInstanceError):
            value.conversation_id = 'changed'
    assert isinstance(state.consented_member_ids, frozenset)
    assert not is_reveal_eligible(replace(PAIR, blocked=True), delivered=evidence(), now=NOW)
    assert not is_reveal_eligible(replace(PAIR, revealed=True), delivered=evidence(), now=NOW)


def test_72_hours_means_elapsed_utc_time_across_a_dst_change():
    from datetime import tzinfo
    class SpringClockZone(tzinfo):
        def utcoffset(self, value):
            return timedelta(hours=-5 if value.day < 8 else -4)
        def dst(self, value):
            return timedelta(0)
    zone = SpringClockZone()
    first = datetime(2026,3,6,12,tzinfo=zone)
    rows = tuple(replace(row, delivered_at=first) for row in evidence())
    #6Mar17:00UTC ->9Mar16:00UTC is71hours; at17:00UTC it is72.
    assert not is_reveal_eligible(PAIR, delivered=rows, now=datetime(2026,3,9,12,tzinfo=zone))
    assert is_reveal_eligible(PAIR, delivered=rows, now=datetime(2026,3,9,13,tzinfo=zone))
