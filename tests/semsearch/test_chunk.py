from groundwork.tools.semsearch.chunk import chunk_file, iter_chunks


def test_chunks_functions_and_classes(tmp_path):
    (tmp_path / "m.py").write_text(
        "def alpha():\n    return 1\n\n\n"
        "class Beta:\n    def gamma(self):\n        return 2\n",
        encoding="utf-8", newline="\n")
    chunks = chunk_file(tmp_path / "m.py", tmp_path)
    names = {c["symbol"] for c in chunks}
    assert "alpha" in names and "Beta" in names
    alpha = [c for c in chunks if c["symbol"] == "alpha"][0]
    assert alpha["file"] == "m.py" and alpha["start_line"] == 1
    assert "return 1" in alpha["text"] and alpha["kind"] in ("function", "method")


def test_symbolless_file_yields_one_whole_file_chunk(tmp_path):
    (tmp_path / "notes.md").write_text("# title\n\nprose only\n", encoding="utf-8")
    # markdown has no cartographer grammar -> whole-file fallback chunk
    chunks = chunk_file(tmp_path / "notes.md", tmp_path)
    assert len(chunks) == 1 and chunks[0]["symbol"] == "notes.md"
    assert "prose only" in chunks[0]["text"]


def test_iter_chunks_skips_venv_and_unparseable(tmp_path):
    (tmp_path / "good.py").write_text("def f():\n    pass\n",
                                      encoding="utf-8", newline="\n")
    (tmp_path / ".venv").mkdir()
    (tmp_path / ".venv" / "x.py").write_text("def hidden(): pass\n", encoding="utf-8")
    chunks = list(iter_chunks(tmp_path))
    files = {c["file"] for c in chunks}
    assert "good.py" in files and not any(".venv" in f for f in files)


def test_posix_paths_in_chunks(tmp_path):
    d = tmp_path / "pkg"
    d.mkdir()
    (d / "a.py").write_text("def g():\n    pass\n", encoding="utf-8", newline="\n")
    chunks = chunk_file(d / "a.py", tmp_path)
    assert chunks[0]["file"] == "pkg/a.py" and "\\" not in chunks[0]["file"]
