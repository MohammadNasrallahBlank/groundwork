"""Optionally run coverage over a test command to produce the JSON report."""
import importlib.util
import subprocess
import sys
from pathlib import Path

from groundwork.core.runner import ToolError


def _importable(mod: str) -> bool:
    return importlib.util.find_spec(mod) is not None


def run_coverage(root: Path, cmd: str) -> Path:
    """Run `coverage run -m <cmd>` then `coverage json` in root; return the report."""
    if not _importable("coverage"):
        raise ToolError("NO_COVERAGE", "coverage.py is not available", exit_code=3)
    out = Path(root) / ".groundwork" / "covdiff-coverage.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    run = subprocess.run([sys.executable, "-m", "coverage", "run",
                          "-m", *cmd.split()], cwd=root, capture_output=True,
                         text=True, encoding="utf-8", errors="replace",
                         timeout=1800)
    # pytest exit codes: 0 pass, 1 tests failed, 5 none collected - all yield
    # coverage data. Other codes are a real run failure.
    if run.returncode not in (0, 1, 5):
        raise ToolError("COVERAGE_RUN_FAILED",
                        f"coverage run exited {run.returncode}",
                        detail=run.stderr[-2000:])
    rep = subprocess.run([sys.executable, "-m", "coverage", "json",
                          "-o", str(out)], cwd=root, capture_output=True,
                         text=True, encoding="utf-8", errors="replace",
                         timeout=300)
    if rep.returncode != 0 or not out.is_file():
        raise ToolError("COVERAGE_RUN_FAILED",
                        "coverage json produced no report",
                        detail=rep.stderr[-2000:])
    return out
