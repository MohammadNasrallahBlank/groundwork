"""Security helpers."""
import secrets


def token(nbytes: int = 32) -> str:
    return secrets.token_hex(nbytes)
