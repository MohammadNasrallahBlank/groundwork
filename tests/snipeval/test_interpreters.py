from groundwork.tools.snipeval import interpreters


def test_python_interpreter_windows_layout(tmp_path):
    exe = tmp_path / ".venv" / "Scripts" / "python.exe"
    exe.parent.mkdir(parents=True)
    exe.write_text("", encoding="utf-8")
    assert interpreters.python_interpreter(tmp_path) == exe


def test_python_interpreter_posix_layout(tmp_path):
    exe = tmp_path / ".venv" / "bin" / "python"
    exe.parent.mkdir(parents=True)
    exe.write_text("", encoding="utf-8")
    assert interpreters.python_interpreter(tmp_path) == exe


def test_python_interpreter_none_without_venv(tmp_path):
    assert interpreters.python_interpreter(tmp_path) is None


def test_node_interpreter_uses_which(monkeypatch):
    from pathlib import Path
    monkeypatch.setattr(interpreters.shutil, "which",
                        lambda b: "C:/Program Files/nodejs/node.exe" if b == "node" else None)
    assert interpreters.node_interpreter(Path(".")) == Path("C:/Program Files/nodejs/node.exe")


def test_node_interpreter_none_when_absent(monkeypatch):
    from pathlib import Path
    monkeypatch.setattr(interpreters.shutil, "which", lambda b: None)
    assert interpreters.node_interpreter(Path(".")) is None
