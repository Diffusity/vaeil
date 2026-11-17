"""Authenticated T8 HTTP seam with real repository/application and fixed ports."""
from fastapi.testclient import TestClient
from test_t6_application import app_for
from test_t7_http import login, ORIGIN
from test_t8_application import reveal_setup
from vaeil.adapters.persistence import open_repository

pytest_plugins = ['test_repository_contract']


def client_for(repo, delivered=20):
    from vaeil.web import create_app
    reveal, messages, _, _ = reveal_setup(repo, delivered=delivered)
    return TestClient(create_app(admission_application=app_for(repo), message_application=messages, reveal_application=reveal),
                      base_url=ORIGIN, headers={'Origin': ORIGIN})


def test_exact_status_and_partner_payload_only_after_both_consents(repository_url):
    with open_repository(repository_url) as repo:
        with client_for(repo) as client:
            login(client, 'a')
            state = client.get('/api/conversations/ab/reveal')
            assert state.status_code == 200
            assert state.json() == dict(conversation_id='ab', eligible=True, viewer_consented=False, revealed=False)
            before = client.get('/api/conversations/ab/partner')
            assert set(before.json()) == {'pseudonym','values_profile'}
            assert all(value not in before.text for value in ['b@example.invalid','2000-01-01','legal_name','date_of_birth','phone'])
            assert client.put('/api/conversations/ab/reveal/consent').json()['viewer_consented']
            assert not client.get('/api/conversations/ab/reveal').json()['revealed']
            assert not client.delete('/api/conversations/ab/reveal/consent').json()['viewer_consented']
            login(client, 'b')
            assert not client.put('/api/conversations/ab/reveal/consent').json()['revealed']
            login(client, 'a')
            assert client.put('/api/conversations/ab/reveal/consent').json()['revealed']
            after = client.get('/api/conversations/ab/partner')
            assert set(after.json()) == {'pseudonym','values_profile','legal_name','email','phone'}
            assert after.json()['email'] == 'b@example.invalid' and after.json()['pseudonym'] == 'Orbit'
            assert after.headers['cache-control'] == 'no-store'
            assert 'date_of_birth' not in after.text
            assert client.delete('/api/conversations/ab/reveal/consent').status_code == 409


def test_ineligible_cannot_use_http_to_consent(repository_url):
    with open_repository(repository_url) as repo:
        with client_for(repo, delivered=19) as client:
            login(client, 'a')
            assert not client.get('/api/conversations/ab/reveal').json()['eligible']
            assert client.put('/api/conversations/ab/reveal/consent').status_code == 409


def test_session_role_pair_origin_and_safe_unknown_input_guards(repository_url):
    with open_repository(repository_url) as repo:
        with client_for(repo) as client:
            assert client.get('/api/conversations/ab/partner').status_code == 401
            login(client, 'admin')
            assert client.put('/api/conversations/ab/reveal/consent').status_code == 403
            login(client, 'c')
            refused = client.get('/api/conversations/ab/reveal')
            missing = client.get('/api/conversations/missing/reveal')
            assert refused.status_code == missing.status_code == 404
            assert refused.json() == missing.json()
            login(client, 'a')
            assert client.put('/api/conversations/ab/reveal/consent', headers={'Origin':'https://elsewhere.invalid'}).status_code == 403
            for method in ('PUT', 'DELETE'):
                for key in ['revealed','actor_id','now','delivered','consent']:
                    result = client.request(method, '/api/conversations/ab/reveal/consent', json={key:'PrivateInputCanaryZXQ'})
                    assert result.status_code == 400 and 'PrivateInputCanaryZXQ' not in result.text
            assert not client.get('/api/conversations/ab/reveal').json()['viewer_consented']
