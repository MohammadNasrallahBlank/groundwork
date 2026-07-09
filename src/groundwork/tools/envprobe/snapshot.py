"""Assemble, persist, and diff environment snapshots. Env VALUES never leave."""
import hashlib
import json
import os
import platform
from pathlib import Path

import platformdirs

from groundwork.core.atomicjson import write_atomic
from groundwork.tools.envprobe.lockfiles import hash_lockfiles
from groundwork.tools.envprobe.runtimes import probe_runtimes


def build_snapshot(root: Path) -> dict:
    names = sorted(os.environ)
    return {
        "root": root.resolve().as_posix(),
        "os": {"system": platform.system(), "release": platform.release(),
               "machine": platform.machine(),
               "groundwork_python": platform.python_version()},
        "runtimes": probe_runtimes(),
        "lockfiles": hash_lockfiles(root),
        "env_names": names,
        "env_count": len(names),
    }


def _store_dir() -> Path:
    env = os.environ.get("GROUNDWORK_DATA_DIR")
    base = Path(env) if env else platformdirs.user_data_path("groundwork")
    return base / "envprobe"


def _baseline_path(root: Path) -> Path:
    rid = hashlib.sha256(root.resolve().as_posix().encode()).hexdigest()[:16]
    return _store_dir() / f"{rid}.json"


def save_baseline(snap: dict) -> Path:
    p = _baseline_path(Path(snap["root"]))
    write_atomic(p, json.dumps(snap, sort_keys=True))
    return p


def load_baseline(root: Path) -> dict | None:
    p = _baseline_path(root)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        try:
            p.unlink(missing_ok=True)
        except OSError:
            pass
        return None


def _dict_drift(old: dict, new: dict, describe) -> dict:
    changed = [{"name": k, "before": describe(old[k]), "after": describe(new[k])}
               for k in sorted(old.keys() & new.keys())
               if describe(old[k]) != describe(new[k])]
    return {"added": sorted(new.keys() - old.keys()),
            "removed": sorted(old.keys() - new.keys()),
            "changed": changed}


def _runtime_desc(r: dict) -> str:
    return r["version"] or r["raw"]


def diff_env(old: dict, new: dict) -> dict:
    d = {
        "os": _dict_drift(old["os"], new["os"], str),
        "runtimes": _dict_drift(old["runtimes"], new["runtimes"], _runtime_desc),
        "lockfiles": _dict_drift(old["lockfiles"], new["lockfiles"], str),
        "env_names": {"added": sorted(set(new["env_names"]) - set(old["env_names"])),
                      "removed": sorted(set(old["env_names"]) - set(new["env_names"]))},
    }
    d["drift"] = any((sec["added"] or sec["removed"] or sec.get("changed"))
                     for sec in (d["os"], d["runtimes"], d["lockfiles"], d["env_names"]))
    return d


def render_digest(snap: dict) -> str:
    rt = " ".join(f"{n}={v['version'] or '?'}"
                  for n, v in sorted(snap["runtimes"].items()))
    locks = " ".join(f"{name}@{h[:8]}"
                     for name, h in sorted(snap["lockfiles"].items()))
    o = snap["os"]
    return (f"os:{o['system']}-{o['release']}-{o['machine']}"
            f" | runtimes: {rt or 'none'}"
            f" | locks: {locks or 'none'}"
            f" | env:{snap['env_count']} names")
