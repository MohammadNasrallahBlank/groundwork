import pytest

from groundwork.tools.visdiff import store


@pytest.fixture(autouse=True)
def _isolated_store(tmp_path, monkeypatch):
    monkeypatch.setenv("GROUNDWORK_DATA_DIR", str(tmp_path / "data"))


def test_platform_key_shape():
    key = store.platform_key()
    assert key.endswith("-chromium")
    assert key == key.lower()


def test_save_then_load_round_trip():
    p = store.save_baseline("home", "linux-chromium", b"\x89PNGfake", {"url": "http://x"})
    assert p.exists()
    got = store.load_baseline("home", "linux-chromium")
    assert got is not None
    png, meta = got
    assert png == b"\x89PNGfake" and meta["url"] == "http://x"


def test_load_missing_returns_none():
    assert store.load_baseline("nope", "linux-chromium") is None


def test_list_baselines_groups_keys():
    store.save_baseline("a", "linux-chromium", b"x", {})
    store.save_baseline("a", "windows-chromium", b"x", {})
    store.save_baseline("b", "linux-chromium", b"x", {})
    listed = store.list_baselines()
    assert {"name": "a", "keys": ["linux-chromium", "windows-chromium"]} in listed
    assert {"name": "b", "keys": ["linux-chromium"]} in listed


@pytest.mark.parametrize("bad", ["../evil", "a/b", "", "x" * 65, "sp ace"])
def test_bad_names_rejected(bad):
    with pytest.raises(ValueError):
        store.save_baseline(bad, "linux-chromium", b"x", {})
    with pytest.raises(ValueError):
        store.load_baseline(bad, "linux-chromium")
