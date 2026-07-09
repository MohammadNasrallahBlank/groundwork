"""Authentication middleware."""
import hashlib

from core.exceptions import AppError


class Unauthorized(AppError):
    status = 401


def verify_bearer(token: str) -> bool:
    return len(token) == 64 and all(c in "0123456789abcdef" for c in token)


def hash_secret(secret: str, salt: str) -> str:
    return hashlib.sha256((salt + secret).encode()).hexdigest()
