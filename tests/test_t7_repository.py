"""Same Message repository contract for SQLite and disposable PostgreSQL."""
import copy
import dataclasses
from datetime import datetime, timezone
import json
import pickle
import pytest
from vaeil.adapters.persistence import open_repository
from vaeil.domain.conversation import Conversation
from vaeil.domain.vetting import Verdict
from test_repository_contract import example_member

pytest_plugins = ['test_repository_contract']
NOW = datetime(2026, 11, 16, 12, tzinfo=timezone.utc)
REQUEST = '00000000-0000-4000-8000-000000000001'


def seed(repo):
    with repo.transaction() as unit:
        unit.add_member(example_member('a', 'Comet'))
        unit.add_member(example_member('b', 'Orbit'))
        unit.store_conversation(Conversation('ab', ('a', 'b')))
        unit.commit()


def record(message_id='m1', request_id=REQUEST, text='MessageBodyCanaryZXQ hello there.'):
    from vaeil.domain.messaging import MessageRecord, assess_message, ModerationFailure
    return MessageRecord(message_id, 'ab', 'a', text, request_id,
        assess_message(text, sender_id='a', conversation=Conversation('ab', ('a', 'b')), moderation=ModerationFailure.UNAVAILABLE), NOW)


def test_canonical_message_roundtrip_redacted_and_not_delivered(repository_url, caplog):
    import logging
    caplog.set_level(logging.INFO, logger='sqlalchemy.engine')
    with open_repository(repository_url) as repo:
        seed(repo)
        message = record(text='  Ｈｅｌｌｏ MessageBodyCanaryZXQ  ')
        with repo.transaction() as unit:
            unit.add_message(message)
            unit.commit()
    with open_repository(repository_url) as repo:
        with repo.transaction() as unit:
            stored = unit.get_message('m1')
            assert stored.text == 'Hello MessageBodyCanaryZXQ'
            assert unit.find_message_by_request('ab', 'a', REQUEST) == stored
            assert unit.list_delivered_messages('ab') == ()
            assert unit.list_sender_messages('ab', 'b') == ()
            assert unit.list_sender_messages('ab', 'a') == (stored,)
        assert 'MessageBodyCanaryZXQ' not in repr(stored) + str(stored) + caplog.text


def test_message_body_record_refuses_accidental_export_copy_and_mutation():
    message = record()
    assert not hasattr(message, '__dict__')
    for export in (copy.copy, copy.deepcopy, dataclasses.asdict, pickle.dumps, json.dumps, lambda value: value.__getstate__()):
        with pytest.raises(TypeError) as caught:
            export(message)
        assert 'MessageBodyCanaryZXQ' not in str(caught.value)
    with pytest.raises(AttributeError):
        message.text = 'changed'


def test_request_key_is_unique_and_failed_unit_rolls_back(repository_url):
    from vaeil.domain.messaging import MessageConflictError
    with open_repository(repository_url) as repo:
        seed(repo)
        with repo.transaction() as unit:
            unit.add_message(record())
            unit.commit()
        with pytest.raises(MessageConflictError):
            with repo.transaction() as unit:
                unit.add_message(record('other'))
                unit.commit()
        with repo.transaction() as unit:
            assert unit.find_message_by_request('ab', 'a', REQUEST).message_id == 'm1'
            assert len(unit.list_sender_messages('ab', 'a')) == 1


def test_review_reserves_digest_and_terminal_delivery_is_immutable(repository_url):
    from vaeil.domain.messaging import ReviewState, MessageProvenance, MessageConflictError, assess_message
    with open_repository(repository_url) as repo:
        seed(repo)
        message = record()
        with repo.transaction() as unit:
            unit.add_message(message)
            pending = message.transition(review_state=ReviewState.PENDING)
            unit.update_message(pending)
            assert unit.list_review_message_ids() == ('m1',)
            assert unit.review_text_exists('ab', 'a', message.text_digest)
            unit.commit()
        with pytest.raises(MessageConflictError):
            with repo.transaction() as unit:
                unit.add_message(record('m2', '00000000-0000-4000-8000-000000000002'))
                unit.commit()
        with repo.transaction() as unit:
            approved = assess_message(message.text, sender_id='a', conversation=Conversation('ab', ('a', 'b')), moderation=Verdict.APPROVED)
            released = pending.transition(assessment=approved, review_state=ReviewState.RELEASED,
                                          provenance=MessageProvenance.HUMAN, delivered_at=NOW)
            unit.update_message(released)
            unit.commit()
        with pytest.raises(MessageConflictError):
            with repo.transaction() as unit:
                unit.update_message(message)
                unit.commit()
        with repo.transaction() as unit:
            assert unit.list_delivered_messages('ab') == (released,)
            assert unit.review_text_exists('ab', 'a', message.text_digest)


def test_uncommitted_message_and_review_claim_are_rolled_back(repository_url):
    from vaeil.domain.messaging import ReviewState, MessageNotFoundError
    with open_repository(repository_url) as repo:
        seed(repo)
        message = record().transition(review_state=ReviewState.PENDING)
        with repo.transaction() as unit:
            unit.add_message(message)
        with repo.transaction() as unit:
            assert not unit.review_text_exists('ab', 'a', message.text_digest)
            with pytest.raises(MessageNotFoundError):
                unit.get_message('m1')


def test_database_request_and_review_uniqueness_cannot_be_bypassed_by_another_writer(repository_url):
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import IntegrityError
    from vaeil.domain.messaging import ReviewState
    with open_repository(repository_url) as repo:
        seed(repo)
        with repo.transaction() as unit:
            unit.add_message(record().transition(review_state=ReviewState.PENDING))
            unit.add_message(record('m2', '00000000-0000-4000-8000-000000000002', 'A different message.'))
            unit.commit()
    engine = create_engine(repository_url.replace('postgresql://', 'postgresql+psycopg://', 1), hide_parameters=True)
    try:
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(text('INSERT INTO messages (message_id, conversation_id, sender_id, text, request_id, '
                    'text_digest, processing, outcome, reason, identifier_reasons, review_state, provenance, created_at, delivered_at) '
                    "SELECT 'different-id', conversation_id, sender_id, text, request_id, text_digest, processing, outcome, reason, "
                    "identifier_reasons, review_state, provenance, created_at, delivered_at FROM messages WHERE message_id = 'm1'"))
        with pytest.raises(IntegrityError):
            with engine.begin() as connection:
                connection.execute(text('INSERT INTO message_review_claims (conversation_id, sender_id, text_digest, message_id) '
                    "SELECT conversation_id, sender_id, text_digest, 'm2' FROM message_review_claims WHERE message_id = 'm1'"))
    finally:
        engine.dispose()
