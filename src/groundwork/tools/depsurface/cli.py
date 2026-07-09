"""`groundwork depsurface` — extract, snapshot, and diff a project's installed API surfaces."""
import argparse
import re
from pathlib import Path

from groundwork.core.cache import Cache, cache_key
from groundwork.core.cliparse import UsageParser
from groundwork.core.runner import ToolError, run_tool
from groundwork.tools.depsurface.diffsurface import diff_snapshots, flatten
from groundwork.tools.depsurface.envresolve import find_site_packages, package_version
from groundwork.tools.depsurface.extract import extract_surface
from groundwork.tools.depsurface.store import list_versions, load_snapshot, save_snapshot

TOOL, VERSION = "depsurface", "0.1.0"

_NAME_RE = re.compile(r"[A-Za-z0-9._-]+")


def _validate_name(kind: str, value: str) -> str:
    # Package/version names are interpolated straight into a snapshot-store
    # filename (store.py's `{package}@{version}.json`). Left unvalidated, a
    # caller-controlled `..` component lets `api`/`diff` write, delete
    # (corrupt-eviction unlink), or read files outside the store directory.
    # `.` alone stays legal (dotted package names, dotted versions); `..` as
    # a substring is what actually enables traversal, so that's what's banned.
    if not _NAME_RE.fullmatch(value) or ".." in value:
        raise ToolError("USAGE", f"invalid {kind}: {value!r} "
                        "(letters, digits, dot, dash, underscore only)",
                        exit_code=2)
    return value


def _resolve_sp(ns) -> Path:
    if ns.site_packages:
        sp = Path(ns.site_packages).resolve()
        if not sp.is_dir():
            raise ToolError("NO_SITE_PACKAGES",
                            f"not a directory: {sp.as_posix()}")
        return sp
    sp = find_site_packages(Path(ns.root).resolve())
    if sp is None:
        raise ToolError("NO_SITE_PACKAGES",
                        f"no .venv site-packages under {Path(ns.root).resolve().as_posix()}"
                        " (pass --site-packages to point elsewhere)")
    return sp


def _metadata_file(sp: Path, package: str) -> list[Path]:
    hits = sorted(sp.glob(f"{package}-*.dist-info/METADATA"))
    return hits[:1]


def _api(ns) -> dict:
    _validate_name("package", ns.package)
    sp = _resolve_sp(ns)
    version = package_version(sp, ns.package) or "unknown"
    key = cache_key(TOOL, VERSION,
                    {"package": ns.package, "site_packages": sp.as_posix(),
                     "version": version},
                    files=_metadata_file(sp, ns.package))
    cache = Cache()
    surface, state = None, "miss"
    if not ns.no_cache:
        surface = cache.get(key)
        if surface is not None:
            state = "hit"
    if surface is None:
        surface = extract_surface(ns.package, sp, version)
        save_snapshot(surface)
        if not ns.no_cache:
            cache.put(key, surface)
    if ns.symbol:
        want = ns.symbol if (ns.symbol == ns.package
                             or ns.symbol.startswith(f"{ns.package}.")) \
            else f"{ns.package}.{ns.symbol}"
        flat = flatten(surface)
        matches = {k: v for k, v in flat.items()
                   if k == want or k.startswith(f"{want}.")}
        if not matches:
            raise ToolError("SYMBOL_NOT_FOUND",
                            f"no public symbol {want} in {ns.package} {version}")
        return {"package": ns.package, "version": version,
                "symbol": want, "matches": matches, "_cache": state}
    return {**surface, "_cache": state}


def _diff(ns) -> dict:
    _validate_name("package", ns.package)
    _validate_name("version", ns.version_a)
    _validate_name("version", ns.version_b)
    snaps = {}
    for v in (ns.version_a, ns.version_b):
        s = load_snapshot(ns.package, v)
        if s is None:
            raise ToolError("MISSING_SNAPSHOT",
                            f"no stored snapshot {ns.package}@{v}; "
                            f"available: {list_versions(ns.package)}")
        snaps[v] = s
    return {"package": ns.package, "from": ns.version_a, "to": ns.version_b,
            **diff_snapshots(snaps[ns.version_a], snaps[ns.version_b])}


def handler(args: list[str]) -> dict:
    p = UsageParser(prog=f"groundwork {TOOL}", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    api = sub.add_parser("api")
    api.add_argument("package")
    api.add_argument("--root", default=".")
    api.add_argument("--site-packages")
    api.add_argument("--symbol")
    api.add_argument("--no-cache", action="store_true")
    d = sub.add_parser("diff")
    d.add_argument("package")
    d.add_argument("version_a")
    d.add_argument("version_b")
    sub.add_parser("self-test")
    try:
        ns = p.parse_args(args)
    except argparse.ArgumentError as e:
        raise ToolError("USAGE", str(e), exit_code=2) from e
    if ns.cmd == "self-test":
        return {"self_test": "pass"}
    if ns.cmd == "diff":
        return _diff(ns)
    return _api(ns)


def main(args: list[str]) -> None:
    run_tool(TOOL, VERSION, handler, args)
