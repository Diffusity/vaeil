"""Approved pure Message assessment seam; no delivery policy in the scanner."""
import dataclasses
import pytest
from vaeil.domain.conversation import Conversation
from vaeil.domain.identifiers import IdentifierReason
from vaeil.domain.vetting import Verdict


@pytest.mark.parametrize('revealed', [False, True])
@pytest.mark.parametrize('text,reasons', [
    ('A thoughtful hello.', ()),
    ('Write to person@example.invalid', (IdentifierReason.EMAIL,)),
    ('Call 9876543210', (IdentifierReason.PHONE,)),
    ('Meet @orbit', (IdentifierReason.HANDLE,)),
    ('person (at) example (dot) com', (IdentifierReason.OBFUSCATED_EMAIL,)),
    ('Visit https://example.invalid', (IdentifierReason.URL,)),
])
def test_approved_assessment_preserves_reason_and_pair_reveal_policy(revealed, text, reasons):
    from vaeil.domain.messaging import assess_message, MessageOutcome
    pair = Conversation('ab', ('a', 'b'), revealed=revealed)
    result = assess_message(text, sender_id='a', conversation=pair, moderation=Verdict.APPROVED)
    assert result.outcome is (MessageOutcome.ESCALATED if reasons and not revealed else MessageOutcome.DELIVERED)
    assert result.identifier_reasons == reasons
    assert result.reason is None
    assert set(dataclasses.asdict(result)) == {'outcome', 'identifier_reasons', 'reason'}


@pytest.mark.parametrize('moderation', ['needs_review', 'unavailable', 'timeout', 'unreachable', 'busy', 'queue_full', 'malformed', 'unexpected'])
def test_review_and_technical_outcomes_never_deliver_even_when_flagged(moderation):
    from vaeil.domain.messaging import assess_message, MessageOutcome, ModerationFailure, ReviewReason
    value = Verdict.NEEDS_REVIEW if moderation == 'needs_review' else (object() if moderation == 'unexpected' else ModerationFailure(moderation))
    result = assess_message('Contact 9876543210', sender_id='a', conversation=Conversation('ab', ('a', 'b')), moderation=value)
    assert result.outcome is MessageOutcome.WITHHELD
    expected = ReviewReason.REQUIRED if moderation == 'needs_review' else ModerationFailure('malformed' if moderation == 'unexpected' else moderation)
    assert result.reason is expected
    assert result.identifier_reasons == (IdentifierReason.PHONE,)


@pytest.mark.parametrize('text,kind', [('', 'shape'), (' \n\t ', 'shape'), (None, 'shape'),
    ('x' * 2001, 'length'), ('\x00', 'control'), ('hidden\u200btext', 'control'), ('\ud800', 'control')],
    ids=['empty', 'whitespace', 'not-text', 'too-long', 'nul', 'zero-width', 'surrogate'])
def test_invalid_text_is_refused_without_echo(text, kind):
    from vaeil.domain.messaging import assess_message, MessageShapeError, MessageLengthError, MessageControlError
    error = {'shape': MessageShapeError, 'length': MessageLengthError, 'control': MessageControlError}[kind]
    with pytest.raises(error) as caught:
        assess_message(text, sender_id='a', conversation=Conversation('ab', ('a', 'b')), moderation=Verdict.APPROVED)
    assert 'hidden' not in str(caught.value)
    assert '2001' not in str(caught.value)


@pytest.mark.parametrize('text', ['x', 'x' * 2000, '🙂' * 2000, 'e\u0301' * 2000, 'Hello\nthere\tfriend'])
def test_normalized_code_point_boundary_and_chat_whitespace_are_accepted(text):
    from vaeil.domain.messaging import assess_message, MessageOutcome
    assert assess_message(text, sender_id='a', conversation=Conversation('ab', ('a', 'b')), moderation=Verdict.APPROVED).outcome is MessageOutcome.DELIVERED


def test_only_other_participant_and_open_conversation_can_send():
    from vaeil.domain.messaging import assess_message, MessageActorError, MessageBlockedError
    with pytest.raises(MessageActorError):
        assess_message('hello', sender_id='c', conversation=Conversation('ab', ('a', 'b')), moderation=Verdict.APPROVED)
    with pytest.raises(MessageBlockedError):
        assess_message('hello', sender_id='a', conversation=Conversation('ab', ('a', 'b'), blocked=True), moderation=Verdict.APPROVED)
