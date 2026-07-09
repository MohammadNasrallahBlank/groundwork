"""Resolve the PROJECT's interpreter, not groundwork's own."""
import shutil
from pathlib import Path


def python_interpreter(root: Path) -> Path | None:
    venv = root / ".venv"
    win = venv / "Scripts" / "python.exe"
    if win.exists():
        return win
    posix = venv / "bin" / "python"
    if posix.exists():
        return posix
    return None


def node_interpreter(root: Path) -> Path | None:
    exe = shutil.which("node")
    return Path(exe) if exe else None
