from clamp import clamp


def test_clamp_middle():
    assert clamp(5, 0, 10) == 5      # only tests the interior - boundaries
    assert clamp(-3, 0, 10) == 0     # and > hi are never tested, so a mutant
