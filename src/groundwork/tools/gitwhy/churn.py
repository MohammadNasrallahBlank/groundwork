"""File change-frequency ranking, optionally crossed with coverage."""
from collections import Counter
from pathlib import Path

from groundwork.core.runner import ToolError
from groundwork.tools.gitwhy.archaeology import _git


def churn_report(root: Path, *, since: str | None, count: int, top: int,
                 coverage_json: Path | None) -> dict:
    """Rank files by change count; join coverage for a risk score if given."""
    root = Path(root).resolve()
    args = ["log", "--name-only", "--format="]
    if since:
        args.append(f"--since={since}")
    else:
        args.append(f"-n{count}")
    proc = _git(root, args)
    if proc.returncode != 0:
        raise ToolError("NO_GIT",
                        f"git log failed (not a repo?): "
                        f"{proc.stderr.strip()[:200]}", exit_code=3)
    counts = Counter(f for f in proc.stdout.splitlines() if f.strip())

    cov = {}
    if coverage_json is not None:
        from groundwork.tools.covdiff.covparse import load_coverage
        raw = load_coverage(Path(coverage_json), root)
        for f, info in raw.items():
            testable = len(info["executed"]) + len(info["missing"])
            cov[f] = (len(info["executed"]) / testable) if testable else None

    files = []
    for path, n in counts.items():
        ratio = cov.get(path)
        risk = round(n * (1 - ratio), 4) if ratio is not None else None
        files.append({"file": path, "changes": n, "coverage_ratio": ratio,
                      "risk": risk})
    # risk desc when present, else changes desc, then path
    files.sort(key=lambda f: (-(f["risk"] if f["risk"] is not None else -1),
                              -f["changes"], f["file"]))
    window = f"since {since}" if since else f"last {count} commits"
    return {"window": window, "files": files[:top]}
