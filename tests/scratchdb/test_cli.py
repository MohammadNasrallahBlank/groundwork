import json
import os
import subprocess
from pathlib import Path


def run_cli(*args, cwd, data_dir):
    env = {**os.environ, "GROUNDWORK_DATA_DIR": str(data_dir)}
    return subprocess.run(["uv", "run", "groundwork", "scratchdb", *args],
                          capture_output=True, text=True, env=env, cwd=cwd)


def _csv(tmp_path: Path):
    p = tmp_path / "sales.csv"
    p.write_text("region,amt\nx,10\ny,20\nx,30\n", encoding="utf-8")
    return p


def test_load_then_query_round_trip(tmp_path):
    d = tmp_path / "data"
    csv = _csv(tmp_path)
    p1 = run_cli("load", "--name", "pad", "--file", str(csv),
                 cwd=str(tmp_path), data_dir=d)
    assert p1.returncode == 0, p1.stdout
    assert json.loads(p1.stdout)["data"]["view"] == "sales"
    p2 = run_cli("q", "--name", "pad", "--sql",
                 "select region, sum(amt) t from sales group by region order by region",
                 cwd=str(tmp_path), data_dir=d)
    assert p2.returncode == 0, p2.stdout
    data = json.loads(p2.stdout)["data"]
    assert data["columns"] == ["region", "t"] and data["row_count"] == 2


def test_query_missing_pad_exits_4(tmp_path):
    p = run_cli("q", "--name", "ghost", "--sql", "select 1",
                cwd=str(tmp_path), data_dir=tmp_path / "data")
    assert p.returncode == 4
    assert json.loads(p.stdout)["error"]["code"] == "NO_PAD"


def test_query_sql_error_exits_1(tmp_path):
    d = tmp_path / "data"
    run_cli("load", "--name", "pad", "--file", str(_csv(tmp_path)),
            cwd=str(tmp_path), data_dir=d)
    p = run_cli("q", "--name", "pad", "--sql", "select * from nope",
                cwd=str(tmp_path), data_dir=d)
    assert p.returncode == 1
    assert json.loads(p.stdout)["error"]["code"] == "SQL_ERROR"


def test_tables_and_list_and_drop(tmp_path):
    d = tmp_path / "data"
    run_cli("load", "--name", "pad", "--file", str(_csv(tmp_path)),
            cwd=str(tmp_path), data_dir=d)
    t = run_cli("tables", "--name", "pad", cwd=str(tmp_path), data_dir=d)
    assert any(v["name"] == "sales" for v in json.loads(t.stdout)["data"]["tables"])
    ls = run_cli("list", cwd=str(tmp_path), data_dir=d)
    assert "pad" in json.loads(ls.stdout)["data"]["pads"]
    dr = run_cli("drop", "--name", "pad", cwd=str(tmp_path), data_dir=d)
    assert json.loads(dr.stdout)["data"]["dropped_pad"] == "pad"
    ls2 = run_cli("list", cwd=str(tmp_path), data_dir=d)
    assert "pad" not in json.loads(ls2.stdout)["data"]["pads"]


def test_self_test(tmp_path):
    p = run_cli("self-test", cwd=str(tmp_path), data_dir=tmp_path / "data")
    assert p.returncode == 0, p.stdout
    assert json.loads(p.stdout)["data"]["self_test"] == "pass"
