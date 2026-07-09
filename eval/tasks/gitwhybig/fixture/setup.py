"""Build a git repo whose pricing.py changed for a specific reason."""
import subprocess, sys
from pathlib import Path


def g(*a):
    subprocess.run(["git", *a], cwd=".", check=True,
                   capture_output=True, text=True)


g("init", "-q")
g("config", "user.email", "t@t"); g("config", "user.name", "t")
steps = [
    ("def apply_discount(price, pct):\n    return price * (1 - pct / 100)\n",
     "add discount helper"),
    ("def apply_discount(price, pct):\n    return price * (1 - pct / 100)\n\n"
     "def format_price(p):\n    return f'${p:.2f}'\n", "add price formatter"),
    ("def apply_discount(price, pct):\n    pct = max(0, min(pct, 100))"
     "  # clamp: a negative pct was inflating prices (#42)\n"
     "    return price * (1 - pct / 100)\n\n"
     "def format_price(p):\n    return f'${p:.2f}'\n",
     "clamp discount pct to avoid negative-percent price inflation (#42)"),
]
for src, msg in steps:
    Path("pricing.py").write_text(src, encoding="utf-8")
    g("add", "-A"); g("commit", "-qm", msg)
print("gitwhy repo ready")
