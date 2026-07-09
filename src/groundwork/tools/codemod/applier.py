"""Replay a stored plan: refuse dirty trees and stale hashes, write byte-
faithfully, chain verify --changed-only."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

from groundwork.core.runner import ToolError
from groundwork.tools.codemod.planner import load_plan


def _git_status(root: Path) -> list[str]:
    try:
        proc = subprocess.run(["git", "status", "--porcelain"], cwd=root,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=60)
    except OSError as e:
        raise ToolError("NO_GIT", f"git not runnable: {e}") from e
    if proc.returncode != 0:
        raise ToolError("NO_GIT",
                        f"not a git repository: {root.as_posix()} "
                        "(apply requires git for its dirty-tree guarantee)")
    return proc.stdout.splitlines()


def _dirty_tracked(status_lines: list[str]) -> list[str]:
    # porcelain: XY <path>; untracked is '??' and does not block.
    return [ln[3:] for ln in status_lines if ln[:2] != "??"]


def apply_plan(root: Path, plan_id: str, *, no_verify: bool = False) -> dict:
    """Apply a stored plan to an unchanged, clean tree; then chain verify."""
    root = Path(root).resolve()
    plan = load_plan(root, plan_id)
    dirty = _dirty_tracked(_git_status(root))
    if dirty:
        raise ToolError("DIRTY_TREE",
                        "tracked files have uncommitted changes; commit or "
                        "stash before applying", detail={"dirty": sorted(dirty)})
    stale = []
    for f in plan["files"]:
        p = root / f["file"]
        current = None
        if p.is_file():
            # open(), not Path.read_text(): read_text gained newline= only in 3.13
            with open(p, encoding="utf-8", newline="") as fh:
                current = fh.read()
        if current is None or hashlib.sha256(
                current.encode("utf-8")).hexdigest() != f["old_sha256"]:
            stale.append(f["file"])
    if stale:
        raise ToolError("STALE_PLAN",
                        "files changed since the plan was computed; re-plan",
                        detail={"stale": sorted(stale)})
    written = []
    for f in plan["files"]:
        p = root / f["file"]
        with open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(f["new_content"])
        written.append(f["file"])

    verify = None
    if written and not no_verify:
        proc = subprocess.run(
            [sys.executable, "-m", "groundwork", "verify", "run",
             "--changed-only", "--root", str(root)],
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=600)
        errors = None
        try:
            # Verified at authoring against the live verify tool: the envelope
            # carries data.summary.counts.error directly.
            errors = json.loads(proc.stdout)["data"]["summary"]["counts"]["error"]
        except (json.JSONDecodeError, KeyError, TypeError):
            pass  # verify's exit code still travels below
        verify = {"exit_code": proc.returncode, "errors": errors}
    return {"plan_id": plan_id, "files_written": sorted(written),
            "verify": verify}
