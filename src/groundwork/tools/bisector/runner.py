"""Worktree lifecycle + oracle subprocess + culprit gitwhy context."""
import shutil
import subprocess
import tempfile
from pathlib import Path

from groundwork.core.runner import ToolError
from groundwork.tools.bisector.bisect import bisect_culprit
from groundwork.tools.gitwhy.archaeology import _commit_detail
from groundwork.tools.gitwhy.refs import extract_refs


def _git(cwd: Path, args: list[str]):
    try:
        return subprocess.run(["git", *args], cwd=cwd, capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=120)
    except OSError as e:
        raise ToolError("NO_GIT", f"git not runnable: {e}", exit_code=3) from e


def _oracle_factory(cmd: str, timeout: int = 600):
    import os
    parts = cmd.split()
    # PYTHONDONTWRITEBYTECODE: each bisect step checks out a different source;
    # without it a stale .pyc from a prior step is imported and the oracle
    # judges the wrong commit -> wrong culprit (same trap as mutcheck).
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}

    def oracle(worktree: Path) -> int:
        try:
            proc = subprocess.run(parts, cwd=worktree, capture_output=True,
                                  text=True, encoding="utf-8", errors="replace",
                                  env=env, timeout=timeout)
        except FileNotFoundError as e:
            raise ToolError("NO_ORACLE", f"oracle not runnable: {cmd!r}: {e}",
                            exit_code=3) from e
        except subprocess.TimeoutExpired:
            return 125                            # untestable -> skip
        return proc.returncode

    return oracle


def run_bisect(root: Path, good: str, bad: str, oracle_cmd: str, *,
               skip_codes: set[int]) -> dict:
    """Bisect good..bad with an oracle subprocess in an isolated worktree."""
    root = Path(root).resolve()
    if _git(root, ["rev-parse", "--git-dir"]).returncode != 0:
        raise ToolError("NO_GIT", f"not a git repository: {root.as_posix()}",
                        exit_code=3)
    tmp = Path(tempfile.mkdtemp(prefix="gw-bisect-"))
    wt = tmp / "wt"
    add = _git(root, ["worktree", "add", "-q", "--detach", str(wt), bad])
    if add.returncode != 0:
        shutil.rmtree(tmp, ignore_errors=True)
        raise ToolError("WORKTREE_FAILED",
                        f"cannot create worktree at {bad}: "
                        f"{add.stderr.strip()[:200]}", exit_code=1)
    try:
        result = bisect_culprit(wt, good, bad, _oracle_factory(oracle_cmd),
                                skip_codes=skip_codes)
        culprit = None
        if result["culprit"]:
            author, date, body = _commit_detail(root, result["culprit"])
            summary = body.splitlines()[0] if body else ""
            culprit = {"sha": result["culprit"][:12], "author": author,
                       "date": date, "summary": summary,
                       "refs": extract_refs(body)}
        return {"good": good, "bad": bad, "oracle": oracle_cmd,
                "culprit": culprit, "steps": result["steps"],
                "inconclusive": result["inconclusive"],
                "skipped": [s[:12] for s in result["skipped"]]}
    finally:
        _git(wt, ["bisect", "reset"])
        _git(root, ["worktree", "remove", "--force", str(wt)])
        shutil.rmtree(tmp, ignore_errors=True)
