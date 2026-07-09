import json
import os
import subprocess
from pathlib import Path

import pytest

from groundwork.tools.semsearch.index import loadable_extensions_available

requires_vec = pytest.mark.skipif(
    not loadable_extensions_available(),
    reason="Python built without loadable SQLite extensions (sqlite-vec unavailable)")


def run_cli(*args, cwd):
    return subprocess.run(["uv", "run", "groundwork", "semsearch", *args],
                          capture_output=True, text=True, env={**os.environ},
                          cwd=cwd)


def _proj(tmp_path: Path):
    (tmp_path / "a.py").write_text(
        "def retry(fn):\n    return fn()\n\n"
        "def charge_card(amount):\n    return bill(amount)\n",
        encoding="utf-8", newline="\n")
    return tmp_path


@requires_vec
def test_index_then_query_round_trip(tmp_path):
    proj = _proj(tmp_path)
    p1 = run_cli("index", cwd=str(proj))
    assert p1.returncode == 0, p1.stdout
    assert json.loads(p1.stdout)["data"]["chunks"] >= 2
    p2 = run_cli("query", "--q", "where is the retry logic", "--k", "3", cwd=str(proj))
    assert p2.returncode == 0, p2.stdout
    out = json.loads(p2.stdout)["data"]
    assert out["results"] and "a.py" in out["results"][0]["file"]


def test_query_without_index_exits_4(tmp_path):
    p = run_cli("query", "--q", "anything", cwd=str(tmp_path))
    assert p.returncode == 4
    assert json.loads(p.stdout)["error"]["code"] == "NO_INDEX"


def test_models_reports_default_and_availability(tmp_path):
    p = run_cli("models", cwd=str(tmp_path))
    assert p.returncode == 0
    data = json.loads(p.stdout)["data"]
    assert data["default_model"]
    assert isinstance(data["default_available"], bool)


def test_self_test_is_model_free(tmp_path):
    # Model-free on every platform: a clean "pass" where sqlite-vec can load,
    # a clean "unsupported" where this Python lacks loadable extensions —
    # never a crash, and never a false "pass".
    p = run_cli("self-test", cwd=str(tmp_path))
    assert p.returncode == 0, p.stdout
    st = json.loads(p.stdout)["data"]["self_test"]
    if loadable_extensions_available():
        assert st == "pass"
    else:
        assert st == "unsupported"
