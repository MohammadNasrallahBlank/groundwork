"""Run pytest with --junit-xml into a temp file; parse failures/errors to Diagnostics."""
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from groundwork.core.runner import ToolError
from groundwork.tools.verify.models import Diagnostic


def parse_junit(xml_text: str) -> list[Diagnostic]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        raise ToolError("PARSE_ERROR", f"junit xml parse failed: {e}",
                         detail=xml_text[:200]) from e
    diags: list[Diagnostic] = []
    for case in root.iter("testcase"):
        problems = list(case.iter("failure")) + list(case.iter("error"))
        if not problems:
            continue
        prob = problems[0]
        name = f"{case.get('classname', '')}::{case.get('name', '')}"
        msg = prob.get("message", "") or (prob.text or "").strip().splitlines()[-1:]
        time_s = float(case.get("time", "0") or 0)
        diags.append(Diagnostic(
            source="pytest", suite="tests",
            file=(case.get("file") or "").replace("\\", "/") or None,
            line=int(case.get("line")) if case.get("line") else None,
            col=None, rule=None, severity="error",
            message=f"{name}: {msg if isinstance(msg, str) else ' '.join(msg)}",
            duration_ms=int(time_s * 1000)))
    return diags


class PytestAdapter:
    name = "pytest"

    def detect(self, root: Path) -> bool:
        has_project = (root / "pyproject.toml").exists() or (root / "pytest.ini").exists()
        has_tests = (root / "tests").is_dir()
        return has_project and has_tests

    def run(self, root: Path, changed: list[str] | None) -> list[Diagnostic]:
        with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tf:
            xml_path = tf.name
        cmd = [sys.executable, "-m", "pytest", "tests", "-q", f"--junit-xml={xml_path}"]
        if changed is not None:
            test_files = [c for c in changed
                          if c.startswith("tests/") and c.endswith(".py")]
            if test_files:
                cmd = [sys.executable, "-m", "pytest", *test_files, "-q",
                       f"--junit-xml={xml_path}"]
            # changed but no test files changed -> run full tests (honest v1 rule)
        try:
            try:
                result = subprocess.run(cmd, cwd=root, capture_output=True,
                                        encoding="utf-8", errors="replace", timeout=600)
            except subprocess.TimeoutExpired as e:
                raise ToolError("TIMEOUT", "pytest exceeded 600s", exit_code=1) from e
            xml_file = Path(xml_path)
            if not xml_file.exists() or xml_file.stat().st_size == 0:
                stderr_tail = (result.stderr or "")[-500:]
                raise ToolError("PYTEST_FAILED",
                                 "pytest did not write junit-xml results",
                                 detail=stderr_tail)
            xml_text = xml_file.read_text(encoding="utf-8", errors="replace")
        finally:
            Path(xml_path).unlink(missing_ok=True)
        return parse_junit(xml_text)
