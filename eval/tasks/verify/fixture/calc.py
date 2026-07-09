"""A tiny calculator. One of these functions has a bug."""


def add(a: int, b: int) -> int:
    return a - b            # BUG: should be a + b


def multiply(a: int, b: int) -> int:
    return a * b
