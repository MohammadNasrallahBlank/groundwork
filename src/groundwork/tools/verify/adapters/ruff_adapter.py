"""Ruff emits machine JSON natively; lint findings are warnings, not errors."""
import json
import shutil
import subprocess
from pathlib import Path

from groundwork.core.envelope import EXIT_MISSING_DEP
from groundwork.core.runner import ToolError
from groundwork.tools.verify.models import Diagnostic


def parse_ruff(json_text: str) -> list[Diagnostic]:
    try:
        items = json.loads(json_text or "[]")
    except json.JSONDecodeError as e:
        raise ToolError("PARSE_ERROR", f"ruff json parse failed: {e}",
                         detail=json_text[:200]) from e
    out = []
    try:
        for v in items:
            location = v.get("location") or {}
            out.append(Diagnostic(
                source="ruff", suite="lint",
                file=(v.get("filename") or "").replace("\\", "/") or None,
                line=location["row"], col=location["column"],
                rule=v.get("code"), severity="warning",
                message=v.get("message", ""), duration_ms=None))
    except (KeyError, TypeError) as e:
        raise ToolError("PARSE_ERROR", f"ruff json shape unexpected: {e}",
                         detail=json_text[:200]) from e
    return out


class RuffAdapter:
    name = "ruff"

    def detect(self, root: Path) -> bool:
        return (root / "pyproject.toml").exists() and shutil.which("ruff") is not None

    def run(self, root: Path, changed: list[str] | None) -> list[Diagnostic]:
        if shutil.which("ruff") is None:
            raise ToolError("MISSING_DEP", "ruff not on PATH", exit_code=EXIT_MISSING_DEP)
        targets = ["."]
        if changed is not None:
            targets = [c for c in changed if c.endswith(".py")] or []
            if not targets:
                return []
        try:
            p = subprocess.run(["ruff", "check", *targets, "--output-format", "json",
                                "--exit-zero"],
                               cwd=root, capture_output=True, encoding="utf-8",
                               errors="replace", timeout=120)
        except subprocess.TimeoutExpired as e:
            raise ToolError("TIMEOUT", "ruff exceeded 120s", exit_code=1) from e
        return parse_ruff(p.stdout)
