"""doctor: every tool's deps checked, every tool's self-test run. Degrade, don't die."""
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

import groundwork
from groundwork.core.envelope import EXIT_ERROR
from groundwork.core.manifest import discover
from groundwork.core.runner import run_tool


def check_deps(deps: dict) -> dict:
    missing_py = [m for m in deps["python"] if importlib.util.find_spec(m) is None]
    missing_sys = [b for b in deps["system"] if shutil.which(b) is None]
    missing_opt = [b for b in deps["optional"] if shutil.which(b) is None
                   and importlib.util.find_spec(b) is None]
    return {"ok": not (missing_py or missing_sys),
            "missing_python": missing_py, "missing_system": missing_sys,
            "missing_optional": missing_opt}


def _self_test(tool: str) -> str:
    try:
        p = subprocess.run([sys.executable, "-m", "groundwork", tool, "self-test"],
                           capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return "timeout"
    except OSError:
        return "fail"
    if p.returncode != 0:
        return "fail"
    try:
        payload = json.loads(p.stdout)
    except json.JSONDecodeError:
        return "fail"
    if not payload.get("ok"):
        return "fail"
    # A tool may report that this platform genuinely cannot support it (e.g.
    # semsearch on a Python built without loadable SQLite extensions). That is
    # a clean, expected degradation — surface it, but don't call it broken.
    data = payload.get("data")
    if isinstance(data, dict) and data.get("self_test") == "unsupported":
        return "unsupported"
    return "pass"


def handler(args: list[str]) -> dict:
    tools_dir = Path(groundwork.__file__).parent / "tools"
    report = []
    for m in discover(tools_dir):
        deps = check_deps(m["deps"])
        entry = {"name": m["name"], "version": m["version"], "deps_ok": deps["ok"], **deps}
        entry["self_test"] = _self_test(m["name"]) if deps["ok"] else "skipped"
        report.append(entry)
    healthy = all(t["deps_ok"] and t["self_test"] in ("pass", "unsupported")
                  for t in report)
    result = {"tools": report, "healthy": healthy}
    if not healthy:
        # Gate CI on health: the envelope stays ok:true (doctor itself ran fine),
        # but the exit code must fail the build so an unhealthy report can't
        # silently pass a doctor step. Same _exit_override sentinel verify uses.
        result["_exit_override"] = EXIT_ERROR
    return result


def main(args: list[str]) -> None:
    run_tool("doctor", "0.1.0", handler, args)
