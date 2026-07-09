"""Content-addressed cache: sha256(tool+version+canonical-input+file-hashes) -> JSON blob."""
import hashlib
import json
import os
from pathlib import Path
from typing import Any

import platformdirs

from groundwork.core.atomicjson import write_atomic


def hash_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def cache_key(tool: str, version: str, payload: dict[str, Any],
              files: list[Path] | None = None) -> str:
    h = hashlib.sha256()
    h.update(f"{tool}\x00{version}\x00".encode())
    h.update(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode())
    for f in sorted(files or [], key=str):
        h.update(f"\x00{f}\x00{hash_file(f)}".encode())
    return h.hexdigest()


class Cache:
    def __init__(self, root: Path | None = None):
        if root is None:
            # platformdirs, not a hand-built ~/... : %LOCALAPPDATA% on Windows,
            # ~/Library/Caches on macOS, XDG on Linux. GROUNDWORK_CACHE_DIR
            # mirrors the store's GROUNDWORK_DATA_DIR override, letting
            # subprocess-based integration tests isolate the cache.
            env = os.environ.get("GROUNDWORK_CACHE_DIR")
            root = Path(env) if env else platformdirs.user_cache_path("groundwork")
        self.root = root
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.root / key[:2] / f"{key}.json"

    def get(self, key: str) -> dict[str, Any] | None:
        p = self._path(key)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            # A truncated/corrupt blob must be a miss, not a permanent poison.
            try:
                p.unlink(missing_ok=True)
            except OSError:
                # Eviction is best-effort: a locked/permission-denied file must
                # not turn a cache miss into a raised exception.
                pass
            return None

    def put(self, key: str, value: dict[str, Any]) -> None:
        p = self._path(key)
        write_atomic(p, json.dumps(value))

    def stats(self) -> dict[str, int]:
        blobs = list(self.root.rglob("*.json"))
        return {"entries": len(blobs), "bytes": sum(b.stat().st_size for b in blobs)}

    def clear(self) -> None:
        for b in self.root.rglob("*.json"):
            b.unlink()
