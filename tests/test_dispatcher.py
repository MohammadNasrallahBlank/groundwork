import importlib
import json
import subprocess

import pytest

from groundwork import dispatcher


def run_cli(*args):
    return subprocess.run(["uv", "run", "groundwork", *args],
                          capture_output=True, text=True)


def test_hello_roundtrip():
    p = run_cli("hello", "greet", "--name", "Moe")
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    assert out["ok"] and out["data"] == {"greeting": "Hello, Moe"}


def test_unknown_tool_is_usage_error():
    p = run_cli("nope")
    assert p.returncode == 2
    out = json.loads(p.stdout)
    assert out["error"]["code"] == "UNKNOWN_TOOL"


def test_hello_self_test():
    p = run_cli("hello", "self-test")
    assert p.returncode == 0
    assert json.loads(p.stdout)["data"] == {"self_test": "pass"}


def test_unknown_tool_module_missing_is_unknown_tool(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["groundwork", "nope"])

    def fake_import_module(name):
        assert name == "groundwork.tools.nope.cli"
        raise ModuleNotFoundError(
            "No module named 'groundwork.tools.nope'", name="groundwork.tools.nope"
        )

    monkeypatch.setattr(importlib, "import_module", fake_import_module)
    with pytest.raises(SystemExit) as exc_info:
        dispatcher.main()
    assert exc_info.value.code == 2
    out = json.loads(capsys.readouterr().out)
    assert out["error"]["code"] == "UNKNOWN_TOOL"


def test_missing_third_party_dependency_is_missing_dep(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["groundwork", "somtool", "cmd"])

    def fake_import_module(name):
        raise ModuleNotFoundError("No module named 'platformdirs'", name="platformdirs")

    monkeypatch.setattr(importlib, "import_module", fake_import_module)
    with pytest.raises(SystemExit) as exc_info:
        dispatcher.main()
    assert exc_info.value.code == 3
    out = json.loads(capsys.readouterr().out)
    assert out["error"]["code"] == "MISSING_DEP"
    assert "platformdirs" in out["error"]["message"]
