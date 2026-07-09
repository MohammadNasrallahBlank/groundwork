import json
import os
import subprocess


def run_cli(*args, cwd):
    return subprocess.run(["uv", "run", "groundwork", "ledger", *args],
                          capture_output=True, text=True, env={**os.environ},
                          cwd=cwd)


def test_claim_resolve_report_round_trip(tmp_path):
    c = run_cli("claim", "--statement", "tests pass", "--confidence", "0.9",
                "--at", "2026-06-01T00:00:00Z", cwd=str(tmp_path))
    assert c.returncode == 0, c.stdout
    cid = json.loads(c.stdout)["data"]["id"]
    r = run_cli("resolve", "--id", str(cid), "--outcome", "true",
                "--at", "2026-06-01T01:00:00Z", cwd=str(tmp_path))
    assert r.returncode == 0, r.stdout
    rep = run_cli("report", cwd=str(tmp_path))
    data = json.loads(rep.stdout)["data"]
    assert data["calibration"]["resolved"] == 1
    assert "Brier" in data["methodology"]


def test_bad_confidence_exits_2(tmp_path):
    p = run_cli("claim", "--statement", "x", "--confidence", "1.5",
                cwd=str(tmp_path))
    assert p.returncode == 2
    assert json.loads(p.stdout)["error"]["code"] == "USAGE"


def test_record_and_efficiency(tmp_path):
    run_cli("record", "--tool", "depsurface", "--cache", "hit", "--avoided",
            cwd=str(tmp_path))
    run_cli("record", "--tool", "verify", "--cache", "miss", "--caught",
            cwd=str(tmp_path))
    rep = run_cli("report", cwd=str(tmp_path))
    eff = json.loads(rep.stdout)["data"]["efficiency"]
    assert eff["runs"] == 2 and eff["cache_hits"] == 1
    assert eff["calls_avoided"] == 1 and eff["verification_catches"] == 1


def test_double_resolve_exits_2(tmp_path):
    c = run_cli("claim", "--statement", "x", "--confidence", "0.5",
                "--at", "2026-06-01T00:00:00Z", cwd=str(tmp_path))
    cid = json.loads(c.stdout)["data"]["id"]
    run_cli("resolve", "--id", str(cid), "--outcome", "true",
            "--at", "2026-06-01T00:00:00Z", cwd=str(tmp_path))
    p = run_cli("resolve", "--id", str(cid), "--outcome", "false",
                "--at", "2026-06-01T00:00:00Z", cwd=str(tmp_path))
    assert p.returncode == 2


def test_self_test(tmp_path):
    p = run_cli("self-test", cwd=str(tmp_path))
    assert p.returncode == 0, p.stdout
    assert json.loads(p.stdout)["data"]["self_test"] == "pass"
