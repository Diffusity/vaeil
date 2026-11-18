"""Reveal consent contract shared by SQLite and disposable PostgreSQL."""
import pytest
from vaeil.adapters.persistence import open_repository
from vaeil.domain.reveal import RevealConsents, RevealEvidenceError
from test_t7_repository import seed

pytest_plugins = ['test_repository_contract']


def test_pair_consents_roundtrip_and_rollback(repository_url):
    with open_repository(repository_url) as repo:
        seed(repo)
        with repo.transaction() as unit:
            assert unit.get_reveal_consents('ab') == RevealConsents('ab', frozenset())
            unit.store_reveal_consents(RevealConsents('ab', frozenset({'a'})))
            unit.commit()
        with repo.transaction() as unit:
            assert unit.get_reveal_consents('ab').consented_member_ids == frozenset({'a'})
            unit.store_reveal_consents(RevealConsents('ab', frozenset({'b'})))
        with repo.transaction() as unit:
            assert unit.get_reveal_consents('ab').consented_member_ids == frozenset({'a'})
    with open_repository(repository_url) as repo:
        with repo.transaction() as unit:
            assert unit.get_reveal_consents('ab') == RevealConsents('ab', frozenset({'a'}))
            unit.store_reveal_consents(RevealConsents('ab', frozenset()))
            unit.commit()
        with repo.transaction() as unit:
            assert unit.get_reveal_consents('ab').consented_member_ids == frozenset()


def test_consent_storage_refuses_outside_pair(repository_url):
    with open_repository(repository_url) as repo:
        seed(repo)
        with repo.transaction() as unit:
            with pytest.raises(RevealEvidenceError):
                unit.store_reveal_consents(RevealConsents('ab', frozenset({'c'})))
        with repo.transaction() as unit:
            assert unit.get_reveal_consents('ab').consented_member_ids == frozenset()
