import base64
import binascii

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError, VerifyMismatchError

from app.exceptions import UnauthorizedError

_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password_hash: str, password: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def parse_basic_auth(header: str | None) -> tuple[str, str]:
    """Extract (username, password) from an HTTP Basic Authorization header."""
    if not header or not header.lower().startswith("basic "):
        raise UnauthorizedError("Missing or invalid Authorization header")
    try:
        decoded = base64.b64decode(header[6:].strip(), validate=True).decode("utf-8")
    except (binascii.Error, UnicodeDecodeError) as exc:
        raise UnauthorizedError("Malformed Basic credentials") from exc
    username, sep, password = decoded.partition(":")
    if not sep or not username:
        raise UnauthorizedError("Malformed Basic credentials")
    return username, password
