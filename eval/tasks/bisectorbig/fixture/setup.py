"""Build a git repo with a regression introduced mid-history."""
import subprocess
from pathlib import Path


def g(*a):
    subprocess.run(["git", *a], cwd=".", check=True,
                   capture_output=True, text=True)


g("init", "-q")
g("config", "user.email", "t@t"); g("config", "user.name", "t")
for i in range(7):
    # commit 4 flips a boundary from <= to < : an off-by-one regression
    op = "<" if i >= 4 else "<="
    Path("range.py").write_text(
        f"# rev {i}\ndef in_range(x, lo, hi):\n    return lo <= x and x {op} hi\n",
        encoding="utf-8")
    Path("test_range.py").write_text(
        "from range import in_range\n"
        "def test_upper_inclusive():\n    assert in_range(10, 0, 10) is True\n",
        encoding="utf-8")
    g("add", "-A"); g("commit", "-qm", f"work item {i}")
print("bisector repo ready")
