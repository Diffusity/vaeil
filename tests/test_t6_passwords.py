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


@pytest.mark.parametrize("encoded", ["not-a-hash", "scrypt$131072$8$1$xx$yy", "scrypt$9999999999999999$8$1$00$00"])
def test_malformed_or_unapproved_cost_hash_fails_closed(encoded):
    from vaeil.adapters.authentication import verify_password
    assert verify_password(PASSWORD, PrivateText(encoded)) is False
