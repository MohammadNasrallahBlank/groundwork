"""Validation helpers used by every model."""


def require(cond: bool, err: Exception) -> None:
    if not cond:
        raise err


def is_email(s: str) -> bool:
    return "@" in s and "." in s.split("@")[-1]
