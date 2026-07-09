"""Manifest = the single source of truth per tool. Skills are generated from these."""
import json
from pathlib import Path
from typing import Any

REQUIRED = ("name", "version", "purpose", "reach_for_me_when",
            "commands", "danger_level", "cache", "deps")
DANGER_LEVELS = ("read_only", "writes_workspace", "writes_repo", "destructive")
CACHE_POLICIES = ("off", "content")


class ManifestError(Exception):
    pass


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        m = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise ManifestError(f"{path.as_posix()}: unreadable manifest: {e}") from e
    for field in REQUIRED:
        if field not in m:
            raise ManifestError(f"{path.as_posix()}: missing required field: {field}")
    if m["danger_level"] not in DANGER_LEVELS:
        raise ManifestError(f"{path.as_posix()}: danger_level must be one of {DANGER_LEVELS}")
    if m["cache"] not in CACHE_POLICIES:
        raise ManifestError(f"{path.as_posix()}: cache must be one of {CACHE_POLICIES}")
    if not isinstance(m["reach_for_me_when"], list) or not m["reach_for_me_when"]:
        raise ManifestError(f"{path.as_posix()}: reach_for_me_when must be non-empty list")
    if not isinstance(m["commands"], list) or not m["commands"]:
        raise ManifestError(f"{path.as_posix()}: commands must be non-empty list")
    return m


def discover(tools_dir: Path) -> list[dict[str, Any]]:
    out = []
    for mf in sorted(tools_dir.glob("*/manifest.json")):
        out.append(load_manifest(mf))
    return out
