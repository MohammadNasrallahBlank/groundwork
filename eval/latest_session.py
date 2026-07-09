"""Print the newest Claude Code session transcript for a given working dir.

Claude Code stores each project's sessions under
``~/.claude/projects/<mangled-cwd>/<session-id>.jsonl`` where <mangled-cwd> is
the absolute working directory with every non-alphanumeric char replaced by
'-'. After you run a task in a workdir, this finds that session for grading:

    uv run python eval/latest_session.py eval/work/cartographer-with-1
"""
import re
import sys
from pathlib import Path


def project_dir(workdir: Path) -> Path:
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(Path(workdir).resolve()))
    return Path.home() / ".claude" / "projects" / slug


def latest_session(workdir: Path) -> Path | None:
    d = project_dir(workdir)
    if not d.is_dir():
        return None
    sessions = sorted(d.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    return sessions[-1] if sessions else None


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    if not argv:
        print("usage: latest_session.py <workdir>", file=sys.stderr)
        return 2
    wd = Path(argv[0])
    s = latest_session(wd)
    if s is None:
        print(f"no session found under {project_dir(wd)}", file=sys.stderr)
        return 1
    print(s)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
