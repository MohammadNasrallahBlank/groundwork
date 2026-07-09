import json
import os
import subprocess


def run_cli(*args, cwd, stdin=None):
    return subprocess.run(["uv", "run", "groundwork", "gates", *args],
                          capture_output=True, text=True, env={**os.environ},
                          input=stdin, cwd=cwd)


def test_scan_finds_and_exits_1(tmp_path):
    p = run_cli("scan", cwd=str(tmp_path), stdin="k = 'AKIAIOSFODNN7EXAMPLE'\n")
    assert p.returncode == 1
    out = json.loads(p.stdout)
    assert out["ok"] is True
    assert out["data"]["findings"][0]["rule"] == "aws-access-key-id"


def test_scan_clean_exits_0(tmp_path):
    p = run_cli("scan", cwd=str(tmp_path), stdin="def f():\n    return 1\n")
    assert p.returncode == 0
    assert json.loads(p.stdout)["data"]["findings"] == []


def test_scan_from_file_with_exempt_path(tmp_path):
    f = tmp_path / "uv.lock"
    f.write_text("h = 'Zk9xJ2mQ7vRt4Wp8Ns6Lc3Hd5Fg1Ba0YeUiOq'\n", encoding="utf-8")
    p = run_cli("scan", "--file", str(f), "--path", "uv.lock", cwd=str(tmp_path))
    assert p.returncode == 0


def test_check_command_verdicts(tmp_path):
    p = run_cli("check-command", "--command", "rm -rf /", cwd=str(tmp_path))
    assert p.returncode == 1
    assert json.loads(p.stdout)["data"]["findings"][0]["rule"] == "bash-rm-root"
    p2 = run_cli("check-command", "--command", "git status", cwd=str(tmp_path))
    assert p2.returncode == 0


def test_show_config_reports_effective_config(tmp_path):
    (tmp_path / ".groundwork").mkdir()
    (tmp_path / ".groundwork" / "gates.yaml").write_text(
        "fail_mode: closed\n", encoding="utf-8")
    p = run_cli("show-config", cwd=str(tmp_path))
    data = json.loads(p.stdout)["data"]
    assert data["fail_mode"] == "closed"
    assert data["secrets"]["enabled"] is True


def test_self_test(tmp_path):
    p = run_cli("self-test", cwd=str(tmp_path))
    assert p.returncode == 0, p.stdout
    assert json.loads(p.stdout)["data"]["self_test"] == "pass"
