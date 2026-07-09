import subprocess
from pathlib import Path

import pytest

from conftest_data import JUNIT
from groundwork.core.runner import ToolError
from groundwork.tools.verify.adapters import pytest_adapter
from groundwork.tools.verify.adapters.pytest_adapter import PytestAdapter, parse_junit


def test_parse_junit_emits_one_error_diagnostic():
    diags = parse_junit(JUNIT)
    assert len(diags) == 1
    d = diags[0]
    assert d.source == "pytest" and d.severity == "error"
    assert d.file == "tests/test_calc.py" and d.line == 13
    assert "test_sub_fails" in d.message and "assert 8 == 2" in d.message
    assert d.duration_ms == 2


def test_detect_requires_python_project_markers(tmp_path):
    a = PytestAdapter()
    assert a.detect(tmp_path) is False
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "tests").mkdir()
    assert a.detect(tmp_path) is True


def test_run_against_pyfail_fixture():
    a = PytestAdapter()
    root = Path("tests/fixtures/pyfail")
    diags = a.run(root, changed=None)
    assert len(diags) == 1
    assert "test_sub_fails" in diags[0].message


def test_parse_junit_raises_tool_error_on_malformed_xml():
    with pytest.raises(ToolError) as exc_info:
        parse_junit("not xml <<<")
    assert exc_info.value.code == "PARSE_ERROR"


def test_parse_junit_raises_tool_error_on_empty_string():
    with pytest.raises(ToolError) as exc_info:
        parse_junit("")
    assert exc_info.value.code == "PARSE_ERROR"


def test_run_raises_timeout_tool_error_on_timeout(monkeypatch):
    def fake_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs.get("timeout", 600))

    monkeypatch.setattr(pytest_adapter.subprocess, "run", fake_run)
    a = PytestAdapter()
    with pytest.raises(ToolError) as exc_info:
        a.run(Path("tests/fixtures/pyfail"), changed=None)
    assert exc_info.value.code == "TIMEOUT"


def test_run_raises_pytest_failed_when_xml_never_written(monkeypatch):
    def fake_run(cmd, **kwargs):
        return subprocess.CompletedProcess(
            cmd, returncode=1, stdout="", stderr="ModuleNotFoundError: no module named pytest"
        )

    monkeypatch.setattr(pytest_adapter.subprocess, "run", fake_run)
    a = PytestAdapter()
    with pytest.raises(ToolError) as exc_info:
        a.run(Path("tests/fixtures/pyfail"), changed=None)
    assert exc_info.value.code == "PYTEST_FAILED"
