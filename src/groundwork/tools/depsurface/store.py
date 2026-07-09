"""Version-stamped snapshot store: <data-dir>/depsurface/<package>@<version>.json."""
import json
import os
from pathlib import Path

import platformdirs

from groundwork.core.atomicjson import write_atomic


def store_dir() -> Path:
    env = os.environ.get("GROUNDWORK_DATA_DIR")
    base = Path(env) if env else platformdirs.user_data_path("groundwork")
    return base / "depsurface"


def _snapshot_path(package: str, version: str) -> Path:
    # Defense-in-depth: the CLI boundary (cli.py's _validate_name) already
    # rejects traversal in package/version before either reaches here, so this
    # should be unreachable in normal operation. It exists so a bypass of the
    # CLI (a future caller, a test, a bug) can't turn `..`/separators in these
    # fields into an arbitrary write/delete/read outside the store dir.
    d = store_dir().resolve()
    p = (d / f"{package}@{version}.json").resolve()
    if p.parent != d:
        raise ValueError(f"snapshot path escapes store dir: {package}@{version}")
    return p


def save_snapshot(snap: dict) -> Path:
    p = _snapshot_path(snap["package"], snap["version"])
    write_atomic(p, json.dumps(snap, sort_keys=True))
    return p


def load_snapshot(package: str, version: str) -> dict | None:
    # ValueError from _snapshot_path is allowed to propagate here (not caught
    # as a miss): the CLI boundary makes this unreachable, so if it ever
    # fires it means something bypassed CLI validation — an honest INTERNAL
    # error is the right signal, not a silently swallowed miss.
    p = _snapshot_path(package, version)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        try:
            p.unlink(missing_ok=True)
        except OSError:
            # Eviction is best-effort; a locked file degrades to a plain miss.
            pass
        return None


def list_versions(package: str) -> list[str]:
    d = store_dir()
    if not d.is_dir():
        return []
    prefix = f"{package}@"
    return sorted(p.name[len(prefix):-len(".json")]
                  for p in d.glob(f"{prefix}*.json"))
