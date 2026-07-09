"""Authentication helpers."""
import hashlib


def verify_token(token: str) -> bool:
    """Return True iff the token is a well-formed 40-char hex session token."""
    return len(token) == 40 and all(c in "0123456789abcdef" for c in token)


def hash_password(password: str, salt: str) -> str:
    """Salted SHA-256 password hash."""
    return hashlib.sha256((salt + password).encode()).hexdigest()
