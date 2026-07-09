"""Platform-keyed baseline store: <data-dir>/visdiff/<name>/<platform-key>.png (+ meta)."""
import json
import os
import platform
import re
from pathlib import Path

import platformdirs

from groundwork.core.atomicjson import write_atomic

_NAME_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def store_dir() -> Path:
    env = os.environ.get("GROUNDWORK_DATA_DIR")
    base = Path(env) if env else platformdirs.user_data_path("groundwork")
    return base / "visdiff"


def platform_key() -> str:
    return f"{platform.system().lower()}-chromium"


def _baseline_dir(name: str) -> Path:
    if not _NAME_RE.fullmatch(name):
        raise ValueError(f"invalid baseline name: {name!r} (must match {_NAME_RE.pattern})")
    return store_dir() / name


def save_baseline(name: str, key: str, png: bytes, meta: dict) -> Path:
    d = _baseline_dir(name)
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{key}.png"
    p.write_bytes(png)
    write_atomic(d / f"{key}.meta.json", json.dumps(meta))
    return p


def load_baseline(name: str, key: str) -> tuple[bytes, dict] | None:
    d = _baseline_dir(name)
    p = d / f"{key}.png"
    if not p.exists():
        return None
    meta_path = d / f"{key}.meta.json"
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
    except (json.JSONDecodeError, OSError):
        meta = {}  # a corrupt sidecar degrades to empty meta, never a crash
    return p.read_bytes(), meta


def list_baselines() -> list[dict]:
    root = store_dir()
    if not root.is_dir():
        return []
    out = []
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        keys = sorted(p.stem for p in d.glob("*.png"))
        if keys:
            out.append({"name": d.name, "keys": keys})
    return out
