import subprocess

from groundwork.tools.envprobe import runtimes


def test_probe_one_absent_binary_returns_none():
    assert runtimes._probe_one("definitely_not_a_real_binary_xyz") is None


def test_probe_one_parses_git_version():
    r = runtimes._probe_one("git")  # git is a repo dev/CI prerequisite
    assert r is not None
    assert r["version"] and r["version"][0].isdigit()
    assert "git" in r["raw"].lower()


def test_probe_one_survives_timeout(monkeypatch):
    monkeypatch.setattr(runtimes.shutil, "which", lambda b: "C:/fake/bin.exe")

    def _hang(*a, **kw):
        raise subprocess.TimeoutExpired(cmd="x", timeout=10)
    monkeypatch.setattr(runtimes.subprocess, "run", _hang)
    assert runtimes._probe_one("anything") == {"version": None, "raw": "probe failed"}


def test_probe_one_reads_stderr_when_stdout_empty(monkeypatch):
    monkeypatch.setattr(runtimes.shutil, "which", lambda b: "C:/fake/java.exe")

    def _stderr_version(*a, **kw):
        return subprocess.CompletedProcess(a, 0, stdout="", stderr='java 21.0.2 2024\nmore')
    monkeypatch.setattr(runtimes.subprocess, "run", _stderr_version)
    r = runtimes._probe_one("java")
    assert r == {"version": "21.0.2", "raw": "java 21.0.2 2024"}


def test_probe_runtimes_includes_git_excludes_missing():
    out = runtimes.probe_runtimes()
    assert "git" in out
    assert "definitely_not_a_real_binary_xyz" not in out
    for entry in out.values():
        assert set(entry) == {"version", "raw"}


def test_go_probe_uses_version_subcommand(monkeypatch):
    seen = {}
    monkeypatch.setattr(runtimes.shutil, "which", lambda b: "C:/fake/go.exe")

    def _capture(cmd, **kw):
        seen["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="go version go1.22.0 windows/amd64", stderr="")
    monkeypatch.setattr(runtimes.subprocess, "run", _capture)
    r = runtimes._probe_one("go")
    assert seen["cmd"] == ["C:/fake/go.exe", "version"]
    assert r == {"version": "1.22.0", "raw": "go version go1.22.0 windows/amd64"}


def test_probe_uses_resolved_executable_path(monkeypatch):
    # Review-fixed: on Windows, npm resolves to npm.CMD; CreateProcess does not
    # apply PATHEXT to a bare "npm" argv[0], so the bare name raises WinError 2
    # even though shutil.which() found it. argv[0] must be the resolved path.
    seen = {}
    monkeypatch.setattr(runtimes.shutil, "which",
                        lambda b: "C:/Program Files/nodejs/npm.CMD")

    def _capture(cmd, **kw):
        seen["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="10.9.2", stderr="")
    monkeypatch.setattr(runtimes.subprocess, "run", _capture)
    r = runtimes._probe_one("npm")
    assert seen["cmd"][0] == "C:/Program Files/nodejs/npm.CMD"
    assert r == {"version": "10.9.2", "raw": "10.9.2"}


def test_nonzero_exit_degrades_to_probe_failed(monkeypatch):
    monkeypatch.setattr(runtimes.shutil, "which", lambda b: "C:/fake/x.exe")
    monkeypatch.setattr(runtimes.subprocess, "run",
                        lambda cmd, **kw: subprocess.CompletedProcess(cmd, 1, stdout="", stderr="Unrecognized option"))
    assert runtimes._probe_one("node") == {"version": None, "raw": "probe failed"}


def test_java_falls_back_to_dash_version(monkeypatch):
    monkeypatch.setattr(runtimes.shutil, "which", lambda b: "C:/fake/java.exe")
    calls = []

    def _seq(cmd, **kw):
        calls.append(cmd)
        if cmd[1] == "--version":
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="Unrecognized option: --version")
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr='java version "1.8.0_402"')
    monkeypatch.setattr(runtimes.subprocess, "run", _seq)
    r = runtimes._probe_one("java")
    assert calls == [["C:/fake/java.exe", "--version"], ["C:/fake/java.exe", "-version"]]
    assert r["version"] == "1.8.0" and "1.8.0_402" in r["raw"]
