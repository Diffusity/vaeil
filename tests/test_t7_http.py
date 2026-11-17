"""T7 authenticated HTTP boundary; real application/repository, fake external ports."""
import json
from fastapi.testclient import TestClient
import pytest
from test_t6_application import app_for
from test_t7_application import setup, Moderator, REQUEST
from vaeil.adapters.persistence import open_repository
from vaeil.domain.vetting import Verdict

pytest_plugins = ['test_repository_contract']
ORIGIN = 'https://testserver'


def client_for(repo, model=None):
    from vaeil.web import create_app
    messages, _, _ = setup(repo, model)
    return TestClient(create_app(admission_application=app_for(repo), message_application=messages),
                      base_url=ORIGIN, headers={'Origin': ORIGIN})


def login(client, identifier):
    response = client.post('/api/sessions', json={'email': identifier + '@example.invalid', 'password': 'fiction password'})
    assert response.status_code == 200


def test_baseline_http_no_recipient_text_until_explicit_human_release(repository_url, caplog):
    with open_repository(repository_url) as repo:
        with client_for(repo) as client:
            login(client, 'a')
            sent = client.post('/api/conversations/ab/messages', json={'request_id': REQUEST, 'text': 'MessageCanaryZXQ hello.'})
            assert sent.status_code == 202
            payload = sent.json()
            assert payload['outcome'] == 'Withheld' and payload['reason'] == 'unavailable' and payload['retry_allowed']
            assert 'MessageCanaryZXQ' not in sent.text
            identifier = payload['message_id']
            assert client.post(f'/api/messages/{identifier}/review').json()['review_state'] == 'pending'
            login(client, 'b')
            before = client.get('/api/conversations/ab/messages')
            assert before.json() == {'conversation_id': 'ab', 'delivered': [], 'attempts': []}
            assert 'MessageCanaryZXQ' not in before.text
            login(client, 'admin')
            queue = client.get('/api/admin/messages')
            assert queue.status_code == 200 and queue.json()['messages'][0]['text'] == 'MessageCanaryZXQ hello.'
            assert client.post(f'/api/admin/messages/{identifier}/decision', json={'decision': 'release'}).status_code == 204
            login(client, 'b')
            delivered = client.get('/api/conversations/ab/messages')
            assert delivered.json()['delivered'][0]['text'] == 'MessageCanaryZXQ hello.'
            assert delivered.headers['cache-control'] == 'no-store'
            assert 'MessageCanaryZXQ' not in caplog.text


@pytest.mark.parametrize('extra', [{'actor_id': 'admin'}, {'revealed': True}, {'model': 'approve'}])
def test_send_cannot_supply_authority_or_production_approval_switch(repository_url, extra):
    with open_repository(repository_url) as repo:
        with client_for(repo, Moderator(Verdict.APPROVED)) as client:
            login(client, 'a')
            assert client.post('/api/conversations/ab/messages', json={'request_id': REQUEST, 'text': 'hello'} | extra).status_code == 400


def test_roles_participants_origin_and_pending_message_existence_are_protected(repository_url):
    with open_repository(repository_url) as repo:
        with client_for(repo) as client:
            assert client.get('/api/conversations/ab/messages').status_code == 401
            login(client, 'a')
            sent = client.post('/api/conversations/ab/messages', json={'request_id': REQUEST, 'text': 'PendingCanary'}).json()
            assert client.get('/api/admin/messages').status_code == 403
            assert client.post('/api/conversations/ab/messages', json={'request_id': REQUEST, 'text': 'hello'}, headers={'Origin': 'https://evil.invalid'}).status_code == 403
            login(client, 'c')
            assert client.get('/api/conversations/ab/messages').status_code == 404
            assert client.post(f"/api/messages/{sent['message_id']}/review").status_code == 404
            assert client.post('/api/messages/absent/review').status_code == 404


@pytest.mark.parametrize('body', [{'request_id': 'InvalidRequestCanary', 'text': 'hello'},
    {'request_id': REQUEST, 'text': 'x' * 2001}, {'request_id': REQUEST, 'text': '\ud800'},
    {'request_id': REQUEST, 'text': ''}], ids=['invalid-key', 'length', 'surrogate', 'empty'])
def test_invalid_message_is_safe_before_model_and_store(repository_url, body, caplog):
    model = Moderator(Verdict.APPROVED)
    with open_repository(repository_url) as repo:
        with client_for(repo, model) as client:
            login(client, 'a')
            response = client.post('/api/conversations/ab/messages', content=json.dumps(body), headers={'Content-Type': 'application/json'})
            assert response.status_code == 400
            assert 'InvalidRequestCanary' not in response.text + caplog.text
            assert not model.seen
            assert client.get('/api/conversations/ab/messages').json()['attempts'] == []


def test_pending_admission_cannot_use_message_or_queue_apis(repository_url):
    from vaeil.domain import MemberIdentity
    from vaeil.domain.authentication import PrincipalRecord, Role, AdmissionStatus
    from vaeil.domain.privacy import PrivateText
    from test_repository_contract import example_member
    model = Moderator(Verdict.APPROVED)
    with open_repository(repository_url) as repo:
        client = client_for(repo, model)
        sample = example_member('pending')
        identity = MemberIdentity('pending', sample.identity.legal_name, 'pending@example.invalid', None, sample.identity.date_of_birth)
        with repo.transaction() as unit:
            unit.add_principal(PrincipalRecord(identity, identity.email, PrivateText('test-only:fiction password'), Role.APPLICANT, AdmissionStatus.NEEDS_REVIEW))
            unit.commit()
        with client:
            login(client, 'pending')
            assert client.get('/api/conversations/ab/messages').status_code == 403
            assert client.get('/api/admin/messages').status_code == 403
            assert client.post('/api/conversations/ab/messages', json={'request_id': REQUEST, 'text': 'hello'}).status_code == 403
            assert model.seen == []
