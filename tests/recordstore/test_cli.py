import json
import os
import subprocess


def run_cli(*args, cwd):
    return subprocess.run(["uv", "run", "groundwork", "recordstore", *args],
                          capture_output=True, text=True, env={**os.environ},
                          cwd=cwd)


def test_add_and_query_decision(tmp_path):
    a = run_cli("add", "decision", "--subject", "API auth", "--choice", "OAuth2",
                "--status", "accepted", "--tags", "api",
                "--at", "2026-03-01T10:00:00Z", cwd=str(tmp_path))
    assert a.returncode == 0, a.stdout
    assert json.loads(a.stdout)["data"]["id"] == 1
    q = run_cli("query", "--type", "decision", "--status", "accepted",
                cwd=str(tmp_path))
    assert q.returncode == 0
    recs = json.loads(q.stdout)["data"]["records"]
    assert len(recs) == 1 and recs[0]["data"]["choice"] == "OAuth2"


def test_measurement_timeline(tmp_path):
    run_cli("add", "measurement", "--metric", "p95_ms", "--value", "120",
            "--at", "2026-03-02T10:00:00Z", cwd=str(tmp_path))
    run_cli("add", "measurement", "--metric", "p95_ms", "--value", "90",
            "--at", "2026-05-02T10:00:00Z", cwd=str(tmp_path))
    t = run_cli("timeline", "--type", "measurement", cwd=str(tmp_path))
    tl = json.loads(t.stdout)["data"]["timeline"]
    assert [e["ts"] for e in tl] == ["2026-03-02T10:00:00Z", "2026-05-02T10:00:00Z"]


def test_bad_status_exits_2(tmp_path):
    p = run_cli("add", "decision", "--subject", "x", "--choice", "y",
                "--status", "maybe", cwd=str(tmp_path))
    assert p.returncode == 2
    assert json.loads(p.stdout)["error"]["code"] == "USAGE"


def test_non_numeric_measurement_exits_2(tmp_path):
    p = run_cli("add", "measurement", "--metric", "m", "--value", "notanum",
                cwd=str(tmp_path))
    assert p.returncode == 2


def test_self_test(tmp_path):
    p = run_cli("self-test", cwd=str(tmp_path))
    assert p.returncode == 0, p.stdout
    assert json.loads(p.stdout)["data"]["self_test"] == "pass"
