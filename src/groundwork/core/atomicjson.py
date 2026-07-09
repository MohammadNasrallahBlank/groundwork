"""Atomic text write with a named STORE_WRITE error. Shared by every store."""
import os
import uuid
from pathlib import Path

from groundwork.core.runner import ToolError


def write_atomic(path: Path, text: str) -> None:
    tmp = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        # mkdir must be inside the try: mkdir(exist_ok=True) still raises
        # FileExistsError (an OSError) when the "parent" is actually an existing
        # FILE, not a directory — exist_ok only tolerates an existing directory.
        # This is pathlib behavior on every OS, not a Windows quirk. That case
        # (e.g. a misconfigured GROUNDWORK_DATA_DIR pointing at a file) must
        # become a named STORE_WRITE error too, not an unnamed crash escaping
        # from before the try.
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp.write_text(text, encoding="utf-8", newline="\n")
        os.replace(tmp, path)
    except OSError as e:
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass
        raise ToolError("STORE_WRITE", f"cannot write {path.as_posix()}",
                        detail=str(e)) from e
