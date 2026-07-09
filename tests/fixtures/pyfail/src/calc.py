import os  # ruff F401: deliberately unused


def add(a, b):
    return a + b


def sub(a, b):
    return a + b  # deliberate bug: should be a - b
