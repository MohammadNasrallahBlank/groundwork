import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.scratchdb import store


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("GROUNDWORK_DATA_DIR", str(tmp_path / "data"))


def test_pad_path_under_data_dir_and_named():
    p = store.pad_path("mypad")
    assert p.name == "mypad.duckdb" and "scratchdb" in p.as_posix()


@pytest.mark.parametrize("bad", ["../evil", "a/b", "", "x" * 65, "sp ace"])
def test_bad_names_rejected(bad):
    with pytest.raises(ToolError) as ei:
        store.pad_path(bad)
    assert ei.value.code == "BAD_NAME" and ei.value.exit_code == 2


def test_list_and_exists_and_drop(tmp_path):
    assert store.list_pads() == []
    store.pad_path("a").parent.mkdir(parents=True, exist_ok=True)
    store.pad_path("a").write_bytes(b"")     # simulate a created pad
    store.pad_path("b").write_bytes(b"")
    assert store.list_pads() == ["a", "b"] and store.pad_exists("a")
    assert store.drop_pad("a") is True and not store.pad_exists("a")
    assert store.drop_pad("nope") is False
