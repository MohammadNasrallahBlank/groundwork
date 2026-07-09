"""Probe known toolchain binaries. Missing binary = absent entry, never an error."""
import re
import shutil
import subprocess

RUNTIMES = ("python", "uv", "git", "node", "npm", "go", "cargo", "rustc", "java")
_VERSION_RE = re.compile(r"(\d+\.\d+(?:\.\d+)*)")

# Most runtimes accept "--version"; named exceptions below override that default.
_PROBE_ARGS: dict[str, tuple[str, ...]] = {"go": ("version",)}
# If the primary probe exits non-zero, retry once with these args before giving up
# (JDK 8's `java` rejects "--version" and only understands "-version").
_FALLBACK_ARGS: dict[str, tuple[str, ...]] = {"java": ("-version",)}


def _run_probe(binary: str, args: tuple[str, ...]):
    try:
        return subprocess.run([binary, *args], capture_output=True,
                              encoding="utf-8", errors="replace", timeout=10)
    except (subprocess.TimeoutExpired, OSError):
        return None


def _probe_one(binary: str) -> dict | None:
    exe = shutil.which(binary)
    if exe is None:
        return None
    # argv[0] is the which()-resolved path: on Windows, bare names skip
    # PATHEXT resolution in CreateProcess, so .cmd/.bat shims (npm) would
    # fail with WinError 2. Args stay fixed constants (no BatBadBut surface).
    p = _run_probe(exe, _PROBE_ARGS.get(binary, ("--version",)))
    if p is not None and p.returncode != 0 and binary in _FALLBACK_ARGS:
        retry = _run_probe(exe, _FALLBACK_ARGS[binary])
        if retry is not None:
            p = retry
    if p is None or p.returncode != 0:
        # Exists but cannot answer (hung, vanished, or flag unsupported):
        # degrade to an honest "present, unknown" — never error text as raw.
        return {"version": None, "raw": "probe failed"}
    # Scope note: probed binaries inherit the parent env; a wrapper binary that
    # echoes env content into --version output is out of scope for the privacy
    # guarantee (which covers os.environ values read by envprobe itself).
    lines = (p.stdout or "").strip().splitlines() or (p.stderr or "").strip().splitlines()
    raw = lines[0] if lines else ""
    m = _VERSION_RE.search(raw)
    return {"version": m.group(1) if m else None, "raw": raw}


def probe_runtimes() -> dict[str, dict]:
    out: dict[str, dict] = {}
    for name in RUNTIMES:
        r = _probe_one(name)
        if r is not None:
            out[name] = r
    return out
