"""Password adapter seam: real stdlib scrypt, opaque stored hashes."""
import pytest
from vaeil.domain.privacy import PrivateText

PASSWORD = "Strong fiction pass 123!"


def test_scrypt_roundtrip_salts_redaction_and_no_normalization():
    from vaeil.adapters.authentication import hash_password, verify_password
    first, second = hash_password(PASSWORD), hash_password(PASSWORD)
    assert isinstance(first, PrivateText) and isinstance(second, PrivateText)
    assert first != second
    assert verify_password(PASSWORD, first) is True
    assert verify_password(PASSWORD + "wrong", first) is False
    assert verify_password(PASSWORD.lower(), first) is False
    assert PASSWORD not in repr(first) + str(first)
    assert verify_password("é" * 12, hash_password("e\u0301" * 12)) is False


@pytest.mark.parametrize("password", ["a" * 12, "a" * 128, " " * 12], ids=["min", "max", "no-composition-rule"])
def test_approved_password_boundaries(password):
    from vaeil.adapters.authentication import hash_password, verify_password
    assert verify_password(password, hash_password(password)) is True


@pytest.mark.parametrize("password", [None, [], "a" * 11, "a" * 129], ids=["none", "list", "below", "above"])
def test_password_policy_refuses_without_echoing(password):
    from vaeil.adapters.authentication import PasswordPolicyError, hash_password
    with pytest.raises(PasswordPolicyError) as result:
        hash_password(password)
    assert "aaa" not in str(result.value)


@pytest.mark.parametrize("encoded", ["not-a-hash", "scrypt-v1$131072$8$1$xx$yy", "scrypt-v1$9999999999999999$8$1$00$00"])
def test_malformed_or_unapproved_cost_hash_fails_closed(encoded):
    from vaeil.adapters.authentication import verify_password
    assert verify_password(PASSWORD, PrivateText(encoded)) is False


def test_password_workers_refuse_overlap_instead_of_allocating_unbounded_memory():
    from concurrent.futures import ThreadPoolExecutor
    import threading
    from vaeil.adapters.authentication import PasswordBusyError, hash_password
    start = threading.Barrier(2)
    def attempt():
        start.wait(timeout=5)
        try:
            hash_password(PASSWORD)
            return "completed"
        except PasswordBusyError:
            return "busy"
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: attempt(), range(2)))
    assert sorted(results) == ["busy", "completed"]


def test_verifier_accepts_a_frozen_independent_scrypt_vector_and_versioned_format():
    from vaeil.adapters.authentication import hash_password, verify_password
    reference = PrivateText("scrypt-v1$131072$8$1$000102030405060708090a0b0c0d0e0f$284a357c3ae912808cf3c68ca883509118d444d42a43507b54bcc9b5eec718dc")
    assert verify_password("Independent reference phrase", reference) is True
    encoded = hash_password(PASSWORD).UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE()
    assert encoded.split("$")[:4] == ["scrypt-v1", "131072", "8", "1"]


def test_verification_respects_the_vetted_constant_time_comparison(monkeypatch):
    import hmac
    from vaeil.adapters.authentication import verify_password
    calls = []
    def mismatch(left, right):
        calls.append((len(left), len(right)))
        return False
    monkeypatch.setattr(hmac, "compare_digest", mismatch)
    reference = PrivateText("scrypt-v1$131072$8$1$000102030405060708090a0b0c0d0e0f$284a357c3ae912808cf3c68ca883509118d444d42a43507b54bcc9b5eec718dc")
    assert verify_password("Independent reference phrase", reference) is False
    assert calls == [(32, 32)]
