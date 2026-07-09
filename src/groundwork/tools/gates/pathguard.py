"""Protected-path enforcement for Edit/Write file paths. Deny wins over ask."""
from fnmatch import fnmatch
from pathlib import PurePosixPath


def _posix(p: str) -> str:
    return PurePosixPath(p.replace("\\", "/")).as_posix()


def check_path(file_path: str, *, deny: tuple[str, ...],
               ask: tuple[str, ...]) -> dict | None:
    """First deny glob wins, else first ask glob, else None."""
    posix = _posix(file_path)
    for glob in deny:
        if fnmatch(posix, glob):
            return {"action": "deny", "glob": glob}
    for glob in ask:
        if fnmatch(posix, glob):
            return {"action": "ask", "glob": glob}
    return None
