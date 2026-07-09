"""Hash the root-level lockfiles that pin this project's dependencies."""
from pathlib import Path

from groundwork.core.cache import hash_file

LOCKFILES = ("uv.lock", "poetry.lock", "requirements.txt", "package-lock.json",
             "pnpm-lock.yaml", "yarn.lock", "Cargo.lock", "go.sum")


def hash_lockfiles(root: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for name in LOCKFILES:
        p = root / name
        if p.is_file():
            out[name] = hash_file(p)
    return out
