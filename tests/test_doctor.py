import json
import subprocess

import pytest

from groundwork.builtins import doctor_cmd
from groundwork.builtins.doctor_cmd import check_deps


def test_check_deps_flags_missing_python_module():
    r = check_deps({"python": ["definitely_not_a_real_module_xyz"], "system": [], "optional": []})
    assert r["ok"] is False
    assert "definitely_not_a_real_module_xyz" in r["missing_python"]


def test_check_deps_passes_stdlib_and_real_binaries():
    r = check_deps({"python": ["json"], "system": ["git"], "optional": ["not_a_binary_xyz"]})
    assert r["ok"] is True
    assert r["missing_optional"] == ["not_a_binary_xyz"]  # degradation note, not failure


def test_doctor_cli_reports_hello_healthy():
    p = subprocess.run(["uv", "run", "groundwork", "doctor"], capture_output=True, text=True)
    assert p.returncode == 0, p.stderr
    out = json.loads(p.stdout)
    hello = next(t for t in out["data"]["tools"] if t["name"] == "hello")
    assert hello["deps_ok"] is True and hello["self_test"] == "pass"


def test_self_test_degrades_on_timeout(monkeypatch):
    def _raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="x", timeout=60)

    monkeypatch.setattr(doctor_cmd.subprocess, "run", _raise_timeout)
    assert doctor_cmd._self_test("hello") == "timeout"


def test_doctor_handler_degrades_report_on_hung_self_test(monkeypatch):
    def _raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="x", timeout=60)

    monkeypatch.setattr(doctor_cmd.subprocess, "run", _raise_timeout)
    report = doctor_cmd.handler([])
    assert report["tools"], "expected a full report, not an empty one"
    for t in report["tools"]:
        if t["deps_ok"]:
            assert t["self_test"] == "timeout"
    assert report["healthy"] is False


def test_doctor_gates_ci_by_exiting_1_when_unhealthy(monkeypatch, capsys):
    # CI's doctor step must fail the build when the report is unhealthy — the
    # envelope itself still reports ok:true (the doctor tool ran successfully;
    # it's the *health verdict* that's bad), same shape as verify's _exit_override.
    def _raise_timeout(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="x", timeout=60)

    monkeypatch.setattr(doctor_cmd.subprocess, "run", _raise_timeout)
    with pytest.raises(SystemExit) as e:
        doctor_cmd.main([])
    assert e.value.code == 1
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["data"]["healthy"] is False
