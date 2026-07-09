"""Resolve the TARGET project's site-packages and installed package versions.

Never consults groundwork's own environment: truth comes from the project.
"""
from importlib.metadata import distributions
from pathlib import Path


def _py_minor(d: Path) -> int:
    try:
        return int(d.name.split(".", 1)[1])
    except (IndexError, ValueError):
        return -1


def find_site_packages(root: Path) -> Path | None:
    venv = root / ".venv"
    win = venv / "Lib" / "site-packages"
    if win.is_dir():
        return win
    lib = venv / "lib"
    if lib.is_dir():
        # Highest minor wins when several python3.* dirs exist. A plain
        # lexicographic sort is wrong here: "python3.10" < "python3.9" as
        # strings (correct by luck) but also "python3.10" < "python3.12"
        # (wrong — would return 3.10 when 3.12 is present).
        candidates = sorted(lib.glob("python3.*"), key=_py_minor, reverse=True)
        for d in candidates:
            sp = d / "site-packages"
            if sp.is_dir():
                return sp
    return None


def _norm(name: str) -> str:
    return name.lower().replace("-", "_")


def package_version(site_packages: Path, package: str) -> str | None:
    for dist in distributions(path=[str(site_packages)]):
        if _norm(dist.metadata["Name"] or "") == _norm(package):
            return dist.version
    return None
