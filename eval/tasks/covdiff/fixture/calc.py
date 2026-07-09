def add(a, b):
    return a + b


def subtract(a, b):
    return a - b


def divide(a, b):          # added later, NOT covered by the test suite
    if b == 0:
        raise ValueError("division by zero")
    return a / b
