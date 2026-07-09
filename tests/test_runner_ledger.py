"""The opt-in proof-of-value feed: run_tool records into a ledger only when
GROUNDWORK_LEDGER_ROOT is set, best-effort, never recording the ledger itself
and never letting a recording failure break the tool."""
import sqlite3
from pathlib import Path

import pytest

from groundwork.core.runner import run_tool


def _runs(root: Path):
    db = Path(root) / ".groundwork" / "ledger.db"
    if not db.exists():
        return []
    conn = sqlite3.connect(db)
    try:
        return conn.execute(
            "select tool, cache, avoided, caught from runs order by id").fetchall()
    finally:
        conn.close()


def _call(tool, handler, monkeypatch, root=None):
    if root is not None:
        monkeypatch.setenv("GROUNDWORK_LEDGER_ROOT", str(root))
    else:
        monkeypatch.delenv("GROUNDWORK_LEDGER_ROOT", raising=False)
    with pytest.raises(SystemExit) as ei:
        run_tool(tool, "0.1.0", handler, [])
    return ei.value.code


def test_no_env_records_nothing(tmp_path, monkeypatch, capsys):
    _call("cartographer", lambda a: {"x": 1}, monkeypatch, root=None)
    assert _runs(tmp_path) == []


def test_successful_run_is_recorded_and_avoided(tmp_path, monkeypatch, capsys):
    code = _call("cartographer", lambda a: {"x": 1}, monkeypatch, root=tmp_path)
    assert code == 0
    rows = _runs(tmp_path)
    assert rows == [("cartographer", "off", 1, 0)]


def test_cache_hit_is_captured(tmp_path, monkeypatch, capsys):
    _call("semsearch", lambda a: {"x": 1, "_cache": "hit"}, monkeypatch, root=tmp_path)
    assert _runs(tmp_path) == [("semsearch", "hit", 1, 0)]


def test_negative_verdict_counts_as_a_catch(tmp_path, monkeypatch, capsys):
    # A verify/gate tool signals a caught problem via a non-zero exit override.
    _call("gates", lambda a: {"blocked": True, "_exit_override": 3},
          monkeypatch, root=tmp_path)
    assert _runs(tmp_path) == [("gates", "off", 1, 1)]


def test_error_run_is_not_avoided(tmp_path, monkeypatch, capsys):
    def boom(_a):
        raise RuntimeError("nope")

    code = _call("cartographer", boom, monkeypatch, root=tmp_path)
    assert code == 1
    assert _runs(tmp_path) == [("cartographer", "off", 0, 0)]


def test_ledger_itself_is_never_recorded(tmp_path, monkeypatch, capsys):
    _call("ledger", lambda a: {"x": 1}, monkeypatch, root=tmp_path)
    assert _runs(tmp_path) == []


def test_recording_failure_never_breaks_the_tool(tmp_path, monkeypatch, capsys):
    # Point the root at a regular file: the ledger cannot create
    # <file>/.groundwork/, so recording fails — the tool must still exit 0.
    bad = tmp_path / "not-a-dir"
    bad.write_text("x", encoding="utf-8")
    code = _call("cartographer", lambda a: {"x": 1}, monkeypatch, root=bad)
    assert code == 0
