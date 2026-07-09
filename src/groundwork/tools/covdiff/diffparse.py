"""git diff --unified=0 -> per-file added/changed line numbers."""
import re
import subprocess
from pathlib import Path

from groundwork.core.runner import ToolError

_TARGET = re.compile(r"^\+\+\+ b/(.+)$")
_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def parse_diff(diff_text: str) -> dict[str, set[int]]:
    """Map each file in a unified=0 diff to its added/changed line numbers."""
    files: dict[str, set[int]] = {}
    cur: str | None = None
    for line in diff_text.splitlines():
        m = _TARGET.match(line)
        if m:
            cur = m.group(1)
            files.setdefault(cur, set())
            continue
        h = _HUNK.match(line)
        if h and cur is not None:
            start = int(h.group(1))
            count = int(h.group(2)) if h.group(2) is not None else 1
            for i in range(start, start + count):
                files[cur].add(i)
    return files


def git_diff(root: Path, *, base: str = "HEAD", staged: bool = False) -> str:
    args = ["git", "diff", "--unified=0"]
    if staged:
        args.append("--cached")
    elif base:
        args.append(base)
    try:
        proc = subprocess.run(args, cwd=root, capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=120)
    except OSError as e:
        raise ToolError("NO_GIT", f"git not runnable: {e}", exit_code=3) from e
    if proc.returncode != 0:
        raise ToolError("NO_GIT",
                        f"git diff failed (not a repo?): "
                        f"{proc.stderr.strip()[:200]}", exit_code=3)
    return proc.stdout
