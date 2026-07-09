"""Build the git state covdiff needs: a committed baseline WITHOUT divide(),
then divide() added as the uncommitted change under test."""
import subprocess
from pathlib import Path


def g(*a):
    subprocess.run(["git", *a], check=True, capture_output=True, text=True)


BASE = ("def add(a, b):\n    return a + b\n\n\n"
        "def subtract(a, b):\n    return a - b\n")
WITH_DIVIDE = BASE + ('\n\ndef divide(a, b):          # new, untested\n'
                      '    if b == 0:\n        raise ValueError("division by zero")\n'
                      '    return a / b\n')

g("init", "-q")
g("config", "user.email", "t@t")
g("config", "user.name", "t")
Path("calc.py").write_text(BASE, encoding="utf-8")
g("add", "-A")
g("commit", "-qm", "baseline calc")
Path("calc.py").write_text(WITH_DIVIDE, encoding="utf-8")   # the diff under test
print("covdiff repo ready (divide() is the uncommitted new code)")
