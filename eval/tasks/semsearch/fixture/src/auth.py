"""Auth."""
import hmac


def verify_password(raw: str, expected_hash: str, salt: str) -> bool:
    import hashlib
    got = hashlib.sha256((salt + raw).encode()).hexdigest()
    return hmac.compare_digest(got, expected_hash)
