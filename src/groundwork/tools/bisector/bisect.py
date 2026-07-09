"""Drive a manual git bisect in a worktree with an injected oracle."""
import re
import subprocess
from pathlib import Path
from typing import Callable

from groundwork.core.runner import ToolError

# git >= ~2.44 quotes the bisect term: "<sha> is the first 'bad' commit";
# older git writes it bare: "<sha> is the first bad commit". Match both — the
# quoted form on macOS runners was silently defeating convergence detection.
_FIRST_BAD = re.compile(r"([0-9a-f]{7,40}) is the first '?bad'? commit")


def map_verdict(exit_code: int, skip_codes: set[int]) -> str:
    if exit_code == 0:
        return "good"
    if exit_code in skip_codes:
        return "skip"
    return "bad"


def _git(worktree: Path, args: list[str]):
    try:
        return subprocess.run(["git", *args], cwd=worktree, capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=120)
    except OSError as e:
        raise ToolError("NO_GIT", f"git not runnable: {e}", exit_code=3) from e


def bisect_culprit(worktree: Path, good: str, bad: str,
                   oracle: Callable[[Path], int], *, skip_codes: set[int],
                   max_steps: int = 60) -> dict:
    """Bisect good..bad in `worktree`, oracle deciding each step; find culprit.

    Every result carries a `transcript`: the per-step (head, verdict, exit,
    git output) trail. When a bisect ends inconclusive that trail is the
    evidence for *why*, and on success it is an audit log of the decisions.
    """
    worktree = Path(worktree)
    transcript: list[dict] = []

    def _record(label: str, res, *, head: str = "", verdict: str = ""):
        transcript.append({
            "step": label, "head": head[:12], "verdict": verdict,
            "rc": res.returncode, "out": (res.stdout + res.stderr).strip()[:300]})

    _git(worktree, ["bisect", "reset"])           # clean any prior state
    _record("reset", _git(worktree, ["bisect", "start"]))
    _record("bad", _git(worktree, ["bisect", "bad", bad]))
    started = _git(worktree, ["bisect", "good", good])
    _record("good", started)
    if started.returncode != 0:
        raise ToolError("BAD_RANGE",
                        f"cannot bisect {good}..{bad}: "
                        f"{started.stderr.strip()[:200]}", exit_code=2,
                        detail={"transcript": transcript})

    skipped: list[str] = []
    last_out = started.stdout + started.stderr
    for step in range(max_steps):
        m = _FIRST_BAD.search(last_out)
        if m:
            return {"culprit": m.group(1), "steps": step,
                    "inconclusive": False, "skipped": skipped,
                    "transcript": transcript}
        head = _git(worktree, ["rev-parse", "HEAD"]).stdout.strip()
        verdict = map_verdict(oracle(worktree), skip_codes)
        if verdict == "skip" and head not in skipped:
            skipped.append(head)
        res = _git(worktree, ["bisect", verdict])
        _record(f"bisect-{step}", res, head=head, verdict=verdict)
        combined = res.stdout + res.stderr
        if res.returncode != 0 and not _FIRST_BAD.search(combined):
            if "merge base" in combined.lower() or skipped:
                return {"culprit": None, "steps": step + 1,
                        "inconclusive": True, "skipped": skipped,
                        "transcript": transcript}
            raise ToolError("BISECT_FAILED",
                            f"git bisect {verdict} failed: "
                            f"{res.stderr.strip()[:200]}", exit_code=1,
                            detail={"transcript": transcript})
        last_out = combined
    return {"culprit": None, "steps": max_steps, "inconclusive": True,
            "skipped": skipped, "transcript": transcript}
