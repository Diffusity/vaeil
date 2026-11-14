"""Vetted stdlib password hashing; only verification extracts the stored hash."""
import hashlib
import hmac
import secrets
import threading
from vaeil.domain.privacy import PrivateText

MIN_PASSWORD_CODE_POINTS = 12
MAX_PASSWORD_CODE_POINTS = 128
SCRYPT_N = 2 ** 17
SCRYPT_R = 8
SCRYPT_P = 1
_PASSWORD_WORKER = threading.BoundedSemaphore(1)


class PasswordPolicyError(Exception):
    """A password violates the approved length policy; no input is echoed."""


class PasswordBusyError(Exception):
    """The bounded password worker is busy; retry without leaking credentials."""


def _derive(password, salt):
    if not _PASSWORD_WORKER.acquire(blocking=False):
        raise PasswordBusyError("Authentication is busy; retry later.")
    try:
        return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=SCRYPT_N, r=SCRYPT_R,
                              p=SCRYPT_P, dklen=32, maxmem=256 * 1024 * 1024)
    finally:
        _PASSWORD_WORKER.release()


def hash_password(password: str) -> PrivateText:
    if not isinstance(password, str) or not MIN_PASSWORD_CODE_POINTS <= len(password) <= MAX_PASSWORD_CODE_POINTS:
        raise PasswordPolicyError("Use a password between 12 and 128 characters.")
    salt = secrets.token_bytes(16)
    digest = _derive(password, salt)
    return PrivateText(f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${salt.hex()}${digest.hex()}")


def verify_password(password: str, encoded_hash: PrivateText) -> bool:
    if not isinstance(password, str) or not MIN_PASSWORD_CODE_POINTS <= len(password) <= MAX_PASSWORD_CODE_POINTS:
        return False
    if not isinstance(encoded_hash, PrivateText):
        return False
    try:
        scheme, n, r, p, salt_hex, digest_hex = encoded_hash.UNWRAP_PRIVATE_VALUE_FOR_AUTHORIZED_USE().split("$")
        if (scheme, n, r, p) != ("scrypt", str(SCRYPT_N), str(SCRYPT_R), str(SCRYPT_P)):
            return False
        salt, expected = bytes.fromhex(salt_hex), bytes.fromhex(digest_hex)
        if len(salt) != 16 or len(expected) != 32:
            return False
        actual = _derive(password, salt)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, UnicodeError, MemoryError):
        return False
