from calc import add, multiply


def test_add():
    assert add(2, 3) == 5
    assert add(-1, 1) == 0


def test_multiply():
    assert multiply(4, 5) == 20
