import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.semsearch import _DEFAULT_MODEL
from groundwork.tools.semsearch.index import (build_index,
                                              loadable_extensions_available,
                                              open_index)

requires_vec = pytest.mark.skipif(
    not loadable_extensions_available(),
    reason="Python built without loadable SQLite extensions (sqlite-vec unavailable)")


@pytest.fixture()
def proj(tmp_path):
    (tmp_path / "a.py").write_text(
        "def retry(fn):\n    return fn()\n\n"
        "def charge(card):\n    return bill(card)\n",
        encoding="utf-8", newline="\n")
    return tmp_path


@requires_vec
def test_build_creates_index_with_chunks(proj):
    out = build_index(proj, _DEFAULT_MODEL)
    assert out["model"] == _DEFAULT_MODEL and out["dim"] in (384, 512)
    assert out["files_indexed"] == 1 and out["chunks"] >= 2
    assert (proj / ".groundwork" / "semsearch" / "index.db").is_file()


@requires_vec
def test_incremental_reuses_unchanged_files(proj):
    build_index(proj, _DEFAULT_MODEL)
    out = build_index(proj, _DEFAULT_MODEL)              # nothing changed
    assert out["reused"] >= 1 and out["files_indexed"] == 0


@requires_vec
def test_changed_file_is_reembedded(proj):
    build_index(proj, _DEFAULT_MODEL)
    (proj / "a.py").write_text("def retry(fn):\n    return fn()\n\n"
                               "def refund(card):\n    return unbill(card)\n",
                               encoding="utf-8", newline="\n")
    out = build_index(proj, _DEFAULT_MODEL)
    assert out["files_indexed"] == 1


@requires_vec
def test_removed_file_chunks_are_deleted(proj):
    (proj / "b.py").write_text("def gamma():\n    pass\n",
                               encoding="utf-8", newline="\n")
    build_index(proj, _DEFAULT_MODEL)
    (proj / "b.py").unlink()
    build_index(proj, _DEFAULT_MODEL)
    conn = open_index(proj)
    rows = conn.execute("select count(*) from files where path='b.py'").fetchone()
    conn.close()
    assert rows[0] == 0


def test_query_without_index_raises_no_index(tmp_path):
    with pytest.raises(ToolError) as ei:
        open_index(tmp_path)
    assert ei.value.code == "NO_INDEX" and ei.value.exit_code == 4
