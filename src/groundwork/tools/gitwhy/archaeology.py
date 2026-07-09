"""Region -> unique commits -> condensed answer with refs."""
import subprocess
from pathlib import Path

from groundwork.core.runner import ToolError
from groundwork.tools.gitwhy.blame import parse_porcelain, unique_commits
from groundwork.tools.gitwhy.refs import extract_refs

_NUL = "\x00"
# git's %x00 placeholder (literal ASCII in the format ARG) makes git emit a
# NUL in its OUTPUT; a real \x00 in the argv is rejected by Windows subprocess.
_FMT = "--format=%an%x00%aI%x00%B"


def _git(root: Path, args: list[str]):
    try:
        return subprocess.run(["git", *args], cwd=root, capture_output=True,
                              text=True, encoding="utf-8", errors="replace",
                              timeout=120)
    except OSError as e:
        raise ToolError("NO_GIT", f"git not runnable: {e}", exit_code=3) from e


def _commit_detail(root: Path, sha: str) -> tuple[str, str, str]:
    proc = _git(root, ["show", "-s", _FMT, sha])
    if proc.returncode != 0:
        return "", "", ""
    author, date, body = (proc.stdout.split(_NUL, 2) + ["", "", ""])[:3]
    return author.strip(), date.strip(), body


def explain(root: Path, file: str, start: int, end: int) -> dict:
    """Blame [start,end] of file -> condensed commits/authors/dates/refs."""
    root = Path(root).resolve()
    proc = _git(root, ["blame", "--porcelain", "-L", f"{start},{end}",
                       "--", file])
    if proc.returncode != 0:
        raise ToolError("NO_BLAME",
                        f"cannot blame {file}:{start}-{end}: "
                        f"{proc.stderr.strip()[:200]}", exit_code=2)
    commits = unique_commits(parse_porcelain(proc.stdout))
    detailed, authors, refs_by_num = [], [], {}
    for c in commits:
        author, date, body = _commit_detail(root, c["sha"])
        refs = extract_refs(body)
        for r in refs:
            prev = refs_by_num.get(r["number"])
            if prev is None or (r["closing"] and not prev["closing"]):
                refs_by_num[r["number"]] = r
        detailed.append({"sha": c["sha"][:12], "author": author or c["author"],
                         "date": date, "summary": (c["summary"] or "").strip(),
                         "refs": refs})
        if author and author not in authors:
            authors.append(author)
    detailed.sort(key=lambda d: (d["date"], d["sha"]), reverse=True)
    dates = [d["date"] for d in detailed if d["date"]]
    return {"file": file, "region": [start, end], "commits": detailed,
            "authors": authors,
            "refs": [refs_by_num[n] for n in sorted(refs_by_num)],
            "span": {"oldest": min(dates) if dates else None,
                     "newest": max(dates) if dates else None}}
