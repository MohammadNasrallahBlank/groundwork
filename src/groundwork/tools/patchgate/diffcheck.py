"""Validate a unified diff: applies cleanly? post-image still parses?
Never touches the working tree - post-images are built in a temp copy."""
import re
import subprocess
import tempfile
from pathlib import Path

from groundwork.core.runner import ToolError
from groundwork.tools.patchgate.checks import check_content

_DIFF_TARGET = re.compile(r"^\+\+\+ b/(.+)$", re.MULTILINE)
_DIFF_SOURCE = re.compile(r"^--- a/(.+)$", re.MULTILINE)


def _run_git(args: list[str], cwd: Path, input_text: str | None = None):
    try:
        return subprocess.run(["git", *args], cwd=cwd, input=input_text,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=120)
    except OSError as e:
        raise ToolError("NO_GIT", f"git not runnable: {e}", exit_code=3) from e
    except subprocess.TimeoutExpired as e:
        raise ToolError("NO_GIT", "git timed out", exit_code=3) from e


def _touched_files(diff_text: str) -> list[str]:
    targets = set(_DIFF_TARGET.findall(diff_text))
    sources = set(_DIFF_SOURCE.findall(diff_text))
    return sorted(targets | sources)


def check_diff(root: Path, diff_text: str) -> dict:
    """Gate a diff: clean apply against root, then parse-check post-images."""
    root = Path(root).resolve()
    if not diff_text.strip():
        return {"passed": True, "applies": True, "files": [], "findings": []}
    files = _touched_files(diff_text)
    findings = []

    apply_check = _run_git(["apply", "--check", "-"], root, diff_text)
    applies = apply_check.returncode == 0
    if not applies:
        findings.append({"file": files[0] if files else "(diff)",
                         "check": "apply", "ok": False,
                         "message": (apply_check.stderr or "git apply --check "
                                     "failed").strip()[-500:]})
        return {"passed": False, "applies": False, "files": files,
                "findings": findings, "_exit_override": 1}

    with tempfile.TemporaryDirectory() as td:
        tdp = Path(td)
        for rel in files:
            src = root / rel
            if src.is_file():
                dst = tdp / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(src.read_bytes())
        applied = _run_git(["apply", "-"], tdp, diff_text)
        if applied.returncode != 0:
            findings.append({"file": files[0] if files else "(diff)",
                             "check": "apply", "ok": False,
                             "message": (applied.stderr or "apply in temp copy "
                                         "failed").strip()[-500:]})
            return {"passed": False, "applies": False, "files": files,
                    "findings": findings, "_exit_override": 1}
        for rel in files:
            p = tdp / rel
            if not p.is_file():
                continue  # deleted by the diff: applied-and-gone, nothing to parse
            try:
                text = p.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError) as e:
                findings.append({"file": rel, "check": "read", "ok": False,
                                 "message": f"unreadable post-image: {e}"})
                continue
            res = check_content(rel, text)
            if res["checked"]:
                findings.append({"file": rel, "check": res["checker"],
                                 "ok": res["ok"],
                                 "message": res["error"] or "ok"})

    findings.sort(key=lambda f: (f["file"], f["check"]))
    passed = all(f["ok"] for f in findings)
    out = {"passed": passed, "applies": True, "files": files,
           "findings": findings}
    if not passed:
        out["_exit_override"] = 1
    return out
