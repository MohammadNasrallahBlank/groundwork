import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
from calc import add, sub


def test_add_passes():
    assert add(2, 3) == 5


def test_sub_fails():
    assert sub(5, 3) == 2
