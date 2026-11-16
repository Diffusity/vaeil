"""Demo failure injection is composition-only; production has no approval selector."""
import pytest
from vaeil.adapters.persistence import open_repository
from vaeil.domain.repository import RepositoryError
from vaeil.runtime import RuntimeAdmission
from test_t7_application import setup, REQUEST

pytest_plugins = ['test_repository_contract']


@pytest.mark.parametrize('environment,switch,expected', [
    ('production', '1', 'invalid'), ('demo', 'yes', 'invalid'),
    ('demo', '1', 'timeout'), ('demo', '0', 'unavailable'), ('production', None, 'unavailable'),
])
def test_runtime_failure_switch_never_enables_approval(repository_url, monkeypatch, environment, switch, expected):
    monkeypatch.setenv('DATABASE_URL', repository_url)
    monkeypatch.delenv('VAEIL_ADMIN_EMAIL', raising=False)
    monkeypatch.delenv('VAEIL_ADMIN_PASSWORD', raising=False)
    monkeypatch.setenv('VAEIL_ENV', environment)
    if switch is None:
        monkeypatch.delenv('VAEIL_DEMO_LLM_FAILURE', raising=False)
    else:
        monkeypatch.setenv('VAEIL_DEMO_LLM_FAILURE', switch)
    with open_repository(repository_url) as repo:
        _, actors, _ = setup(repo)
    runtime = RuntimeAdmission()
    try:
        if expected == 'invalid':
            with pytest.raises(RepositoryError):
                runtime.get_messages()
        else:
            message = runtime.get_messages().send_message(actor=actors['a'], conversation_id='ab', request_id=REQUEST, text='hello')
            assert message.outcome.value == 'Withheld' and message.reason.value == expected
    finally:
        runtime.close()
