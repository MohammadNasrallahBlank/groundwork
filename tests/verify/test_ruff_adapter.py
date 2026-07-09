import json
import subprocess
from pathlib import Path

import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.verify.adapters import ruff_adapter
from groundwork.tools.verify.adapters.ruff_adapter import RuffAdapter, parse_ruff

RUFF_JSON = json.dumps([{
    "code": "F401",
    "message": "`os` imported but unused",
    "filename": "src/calc.py",
    "location": {"row": 1, "column": 8},
    "end_location": {"row": 1, "column": 10},
    "fix": None, "url": "https://docs.astral.sh/ruff/rules/unused-import",
}])


def test_parse_ruff_maps_to_warning_diagnostic():
    diags = parse_ruff(RUFF_JSON)
    assert len(diags) == 1
    d = diags[0]
    assert (d.source, d.suite, d.severity) == ("ruff", "lint", "warning")
    assert d.file == "src/calc.py" and d.line == 1 and d.col == 8 and d.rule == "F401"


def test_run_against_pyfail_fixture():
    diags = RuffAdapter().run(Path("tests/fixtures/pyfail"), changed=None)
    assert any(d.rule == "F401" for d in diags)


def test_changed_only_filters_files():
    diags = RuffAdapter().run(Path("tests/fixtures/pyfail"),
                              changed=["tests/test_calc.py"])  # calc.py NOT in changed
    assert not any(d.rule == "F401" for d in diags)


def test_parse_ruff_raises_tool_error_on_malformed_json():
    with pytest.raises(ToolError) as exc_info:
        parse_ruff("{bad json")
    assert exc_info.value.code == "PARSE_ERROR"


def test_parse_ruff_raises_tool_error_on_missing_location():
    with pytest.raises(ToolError) as exc_info:
        parse_ruff('[{"code":"X"}]')
    assert exc_info.value.code == "PARSE_ERROR"


def test_run_raises_timeout_tool_error_on_timeout(monkeypatch):
    def fake_run(cmd, **kwargs):
        raise subprocess.TimeoutExpired(cmd, kwargs.get("timeout", 120))

    monkeypatch.setattr(ruff_adapter.subprocess, "run", fake_run)
    a = RuffAdapter()
    with pytest.raises(ToolError) as exc_info:
        a.run(Path("tests/fixtures/pyfail"), changed=None)
    assert exc_info.value.code == "TIMEOUT"
