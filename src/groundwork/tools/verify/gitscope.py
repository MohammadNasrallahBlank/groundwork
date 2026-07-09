"""Changed = modified vs HEAD + untracked. Returns None outside a git repo."""
import os
import subprocess
from pathlib import Path


def _git(root: Path, *args: str) -> subprocess.CompletedProcess | None:
    # GIT_CEILING_DIRECTORIES stops git's upward search for a .git directory at
    # root's parent. Without this, a `root` that happens to sit inside some
    # unrelated ancestor repo's working tree (e.g. a tmp dir nested under this
    # very repo's own repo-local --basetemp) would be misreported as "inside a
    # work tree" by finding that ancestor's .git instead of failing honestly.
    env = {**os.environ, "GIT_CEILING_DIRECTORIES": str(Path(root).resolve().parent)}
    try:
        return subprocess.run(["git", *args], cwd=root, capture_output=True,
                              encoding="utf-8", errors="replace", timeout=30, env=env)
    except FileNotFoundError:
        return None


def changed_files(root: Path) -> list[str] | None:
    probe = _git(root, "rev-parse", "--is-inside-work-tree")
    if probe is None or probe.returncode != 0:
        return None
    diff = _git(root, "diff", "--name-only", "HEAD")
    untracked = _git(root, "ls-files", "--others", "--exclude-standard")
    files = set()
    for p in (diff, untracked):
        if p and p.returncode == 0:
            files.update(line for line in p.stdout.splitlines() if line)
    return sorted(files)
