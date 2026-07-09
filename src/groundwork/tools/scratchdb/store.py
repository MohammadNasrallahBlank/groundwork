"""Named scratchpads = <data-dir>/scratchdb/<name>.duckdb."""
import os
import re
from pathlib import Path

import platformdirs

from groundwork.core.runner import ToolError

_NAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def _root() -> Path:
    env = os.environ.get("GROUNDWORK_DATA_DIR")
    base = Path(env) if env else platformdirs.user_data_path("groundwork")
    return base / "scratchdb"


def pad_path(name: str) -> Path:
    if not _NAME_RE.fullmatch(name):
        raise ToolError("BAD_NAME",
                        f"invalid pad name {name!r} (must match {_NAME_RE.pattern})",
                        exit_code=2)
    return _root() / f"{name}.duckdb"


def pad_exists(name: str) -> bool:
    return pad_path(name).is_file()


def list_pads() -> list[str]:
    root = _root()
    if not root.is_dir():
        return []
    return sorted(p.stem for p in root.glob("*.duckdb"))


def drop_pad(name: str) -> bool:
    p = pad_path(name)
    if not p.is_file():
        return False
    p.unlink()
    return True
