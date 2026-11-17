"""Transactional Reveal public seam, shared across both database URLs."""
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import timedelta
from uuid import UUID
import threading
import pytest
from vaeil.adapters.persistence import open_repository
from vaeil.domain import serialize_member_view
from vaeil.domain.conversation import Conversation, MemberAlreadyActiveError
from vaeil.domain.messaging import MessageRecord, assess_message, ModerationFailure, MessageReviewDecision
from vaeil.domain.reveal import RevealNotEligibleError, RevealActorError, RevealBlockedError, RevealCompletedError
from vaeil.domain.repository import AuditKind, AuditEvent, RepositoryError
from vaeil.domain.authentication import AccessDeniedError, Role
from vaeil.domain.vetting import Verdict
from test_t7_application import REQUEST
from test_t6_application import FixedClock, Tokens
from test_repository_contract import example_member
from vaeil import domain as d
from vaeil.domain.authentication import PrincipalRecord, AdmissionStatus
from vaeil.domain.privacy import PrivateText
from vaeil.application.admission import SessionPrincipal
from vaeil.application.messaging import MessageApplication

pytest_plugins = ['test_repository_contract']


def reveal_setup(repo, *, delivered=20, first_age=72):
    from vaeil.application.reveal import RevealApplication
    clock = FixedClock()
    messages = MessageApplication(repo, tokens=Tokens(), clock=clock)
    actors = {}
    with repo.transaction() as unit:
        for identifier, name in [('a','Comet'),('b','Orbit'),('c','Star'),('admin','Nova')]:
            sample = example_member(identifier, name)
            identity = d.MemberIdentity(identifier, 'LegalCanaryZXQ'+identifier, identifier+'@example.invalid',
                                        '+919876543210' if identifier == 'b' else None, sample.identity.date_of_birth)
            role = Role.ADMIN if identifier == 'admin' else Role.MEMBER
            unit.add_principal(PrincipalRecord(identity, identity.email, PrivateText('test-only:fiction password'), role, AdmissionStatus.APPROVED))
            if role is Role.MEMBER:
                unit.add_member(d.Member(identity, sample.pseudonym, sample.values_profile))
            actors[identifier] = SessionPrincipal(identifier, role, AdmissionStatus.APPROVED)
        unit.store_conversation(Conversation('ab', ('a','b')))
        unit.commit()
    first = clock.now()-timedelta(hours=first_age)
    with repo.transaction() as unit:
        conversation = unit.get_conversation('ab')
        for index in range(delivered):
            sender = 'b' if index < 5 else 'a'
            text = '9876543210' if index == 0 else 'Thoughtful conversation.'
            assessment = assess_message(text, sender_id=sender, conversation=conversation, moderation=Verdict.APPROVED)
            unit.add_message(MessageRecord('seed'+str(index), 'ab', sender, text, str(UUID(int=index+20)),
                assessment, clock.now()-timedelta(days=9), delivered_at=first))
        unit.commit()
    return RevealApplication(repo, tokens=messages.tokens, clock=clock), messages, actors, clock


def events(repo):
    with repo.transaction() as unit:
        return [event for event in unit.list_audit(subject_id='ab') if event.kind is AuditKind.CONVERSATION_REVEALED]


def consent(app, actor, value=True, pair='ab'):
    return app.set_reveal_consent(actor=actor, conversation_id=pair, consent=value)


def test_durable_bilateral_reveal_exact_payload_audit_slot_release_and_isolation(repository_url):
    with open_repository(repository_url) as repo:
        app, messages, actors, _ = reveal_setup(repo)
        assert app.read_reveal(actor=actors['a'], conversation_id='ab').eligible
        before = app.read_partner(actor=actors['a'], conversation_id='ab')
        assert set(serialize_member_view(before)) == {'pseudonym','values_profile'}
        for canary in ['LegalCanaryZXQb','b@example.invalid','+919876543210','1987-03-14']:
            assert canary not in repr(before) and canary not in str(before)
            assert canary not in str(serialize_member_view(before))
        assert not consent(app, actors['a']).revealed
        assert consent(app, actors['a']).viewer_consented
        assert not consent(app, actors['a'], False).viewer_consented
        consent(app, actors['a'])
        assert consent(app, actors['b']).revealed
        assert consent(app, actors['b']).revealed
        with pytest.raises(RevealCompletedError):
            consent(app, actors['a'], False)
        after = app.read_partner(actor=actors['a'], conversation_id='ab')
        payload = serialize_member_view(after)
        assert set(payload) == {'pseudonym','values_profile','legal_name','email','phone'}
        assert payload['email'] == 'b@example.invalid'
        assert payload['pseudonym'] == 'Orbit' and payload['phone'] == '+919876543210'
        assert payload['legal_name'] == 'LegalCanaryZXQb'
        assert '1987-03-14' not in str(payload)
        assert 'b@example.invalid' not in repr(after) and 'b@example.invalid' not in str(after)
        assert len(events(repo)) == 1
        with repo.transaction() as unit:
            assert unit.get_reveal_consents('ab').consented_member_ids == frozenset({'a','b'})
            unit.store_conversation(Conversation('ac', ('a','c')))
            unit.commit()
        ac = app.read_reveal(actor=actors['a'], conversation_id='ac')
        assert not ac.revealed and not ac.viewer_consented
        assert set(serialize_member_view(app.read_partner(actor=actors['c'], conversation_id='ac'))) == {'pseudonym','values_profile'}
        # Revealed chat stays open but safety is still required.
        sent = messages.send_message(actor=actors['a'], conversation_id='ab', request_id=REQUEST, text='Hello again.')
        assert sent.reason is ModerationFailure.UNAVAILABLE
    with open_repository(repository_url) as repo:
        from vaeil.application.reveal import RevealApplication
        restored = RevealApplication(repo, tokens=app.tokens, clock=app.clock)
        assert restored.read_reveal(actor=actors['a'], conversation_id='ab').revealed


def test_withheld_and_creation_time_cannot_satisfy_threshold_late_release_counts_once(repository_url):
    with open_repository(repository_url) as repo:
        app, messages, actors, clock = reveal_setup(repo, delivered=19, first_age=0)
        attempt = messages.send_message(actor=actors['a'], conversation_id='ab', request_id=REQUEST, text='A new message.')
        assert not app.read_reveal(actor=actors['a'], conversation_id='ab').eligible
        with pytest.raises(RevealNotEligibleError):
            consent(app, actors['a'])
        messages.submit_for_review(actor=actors['a'], message_id=attempt.message_id)
        clock.moment += timedelta(hours=72)
        #19old +1newlyreleased; the first actual delivery remains72hoursold.
        assert not app.read_reveal(actor=actors['a'], conversation_id='ab').eligible
        messages.decide_message(actor=actors['admin'], message_id=attempt.message_id, decision=MessageReviewDecision.RELEASE)
        assert app.read_reveal(actor=actors['a'], conversation_id='ab').eligible
        with repo.transaction() as unit:
            rows = unit.list_delivered_messages('ab')
            assert len(rows) == 20 and rows[-1].delivered_at == clock.now()


def test_role_pair_block_guards_and_active_slot_before_completion(repository_url):
    with open_repository(repository_url) as repo:
        app, _, actors, _ = reveal_setup(repo)
        for operation in (app.read_reveal, app.read_partner):
            with pytest.raises(RevealActorError):
                operation(actor=actors['c'], conversation_id='ab')
            with pytest.raises(AccessDeniedError):
                operation(actor=actors['admin'], conversation_id='ab')
        forged = replace(actors['admin'], role=Role.MEMBER)
        with pytest.raises(AccessDeniedError):
            consent(app, forged)
        with repo.transaction() as unit:
            with pytest.raises(MemberAlreadyActiveError):
                unit.store_conversation(Conversation('ac', ('a','c')))
        consent(app, actors['a'])
        with repo.transaction() as unit:
            unit.store_conversation(replace(unit.get_conversation('ab'), blocked=True))
            unit.commit()
        with pytest.raises(RevealBlockedError):
            consent(app, actors['b'])
        assert events(repo) == []


def test_reveal_and_consent_rollback_if_audit_fails(repository_url):
    with open_repository(repository_url) as repo:
        app, _, actors, clock = reveal_setup(repo)
        consent(app, actors['a'])
        with repo.transaction() as unit:
            unit.append_audit(AuditEvent('duplicate', clock.now(), 'a', 'fixture', AuditKind.INVITE_REDEEMED))
            unit.commit()
        class DuplicateTokens:
            def new_id(self): return 'duplicate'
        app.tokens = DuplicateTokens()
        with pytest.raises(RepositoryError):
            consent(app, actors['b'])
        with repo.transaction() as unit:
            assert not unit.get_conversation('ab').revealed
            assert unit.get_reveal_consents('ab').consented_member_ids == frozenset({'a'})
        assert events(repo) == []


@pytest.mark.parametrize('competing', ['consent','withdraw','block'])
def test_concurrent_transitions_commit_a_valid_serial_result_once(repository_url, competing):
    with open_repository(repository_url) as repo:
        app, _, actors, _ = reveal_setup(repo)
        if competing != 'consent':
            consent(app, actors['a'])
        barrier = threading.Barrier(2)
        def perform(index):
            barrier.wait(timeout=10)
            try:
                if competing == 'block' and index == 0:
                    with repo.transaction() as unit:
                        unit.store_conversation(replace(unit.get_conversation('ab'), blocked=True))
                        unit.commit()
                else:
                    consent(app, actors['a' if index == 0 else 'b'], not (competing == 'withdraw' and index == 0))
                return 'ok'
            except (RevealCompletedError, RevealBlockedError):
                return 'refused'
        with ThreadPoolExecutor(max_workers=2) as pool:
            outcomes = list(pool.map(perform, [0,1]))
        assert 'ok' in outcomes
        with repo.transaction() as unit:
            conversation = unit.get_conversation('ab')
            consents = unit.get_reveal_consents('ab')
        assert len(events(repo)) == int(conversation.revealed)
        if conversation.revealed:
            assert consents.consented_member_ids == frozenset({'a','b'})
        if competing == 'consent':
            assert conversation.revealed
        if competing == 'block':
            assert conversation.blocked


def test_twenty_recent_deliveries_cannot_use_old_creation_time(repository_url):
    with open_repository(repository_url) as repo:
        app, _, actors, clock = reveal_setup(repo, first_age=0)
        assert not app.read_reveal(actor=actors['a'], conversation_id='ab').eligible
        with pytest.raises(RevealNotEligibleError):
            consent(app, actors['a'])
        clock.moment += timedelta(hours=72)
        assert app.read_reveal(actor=actors['a'], conversation_id='ab').eligible
