import shutil
from pathlib import Path

import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.snipeval import engine, interpreters

# This repo has a .venv (uv-managed); use the repo root as the project root.
REPO_ROOT = Path(__file__).resolve().parents[2]
HAS_PY_VENV = interpreters.python_interpreter(REPO_ROOT) is not None
HAS_NODE = shutil.which("node") is not None


@pytest.mark.skipif(not HAS_PY_VENV, reason="no project .venv python")
def test_python_stdout_and_returncode():
    r = engine.run_snippet("python", "print('hi')", REPO_ROOT, timeout=30)
    assert r["lang"] == "python" and r["returncode"] == 0
    assert r["timed_out"] is False and r["stdout"].strip() == "hi"
    assert "/" in r["interpreter"] and "\\\\" not in r["interpreter"]
    # print()'s trailing-expr value is None; REPL convention suppresses it (defect #4).
    assert r["result_repr"] is None


@pytest.mark.skipif(not HAS_PY_VENV, reason="no project .venv python")
def test_python_trailing_expression_repr():
    r = engine.run_snippet("python", "x = 40\nx + 2", REPO_ROOT, timeout=30)
    assert r["result_repr"] == "42"
    assert r["stdout"] == ""  # the value did not print, only its repr was captured


@pytest.mark.skipif(not HAS_PY_VENV, reason="no project .venv python")
def test_python_no_trailing_expression_gives_null_repr():
    r = engine.run_snippet("python", "y = 1\n", REPO_ROOT, timeout=30)
    assert r["result_repr"] is None


@pytest.mark.skipif(not HAS_PY_VENV, reason="no project .venv python")
def test_python_error_is_captured_not_raised():
    r = engine.run_snippet("python", "raise ValueError('boom')", REPO_ROOT, timeout=30)
    assert r["returncode"] != 0
    assert "ValueError" in r["stderr"] and "boom" in r["stderr"]
    assert r["result_repr"] is None


@pytest.mark.skipif(not HAS_PY_VENV, reason="no project .venv python")
def test_python_timeout():
    r = engine.run_snippet("python", "import time; time.sleep(30)", REPO_ROOT, timeout=1)
    assert r["timed_out"] is True and r["returncode"] is None


def test_no_interpreter_raises(tmp_path):
    with pytest.raises(ToolError) as e:
        engine.run_snippet("python", "1", tmp_path, timeout=5)  # empty dir, no .venv
    assert e.value.code == "NO_INTERPRETER" and e.value.exit_code == 3


def test_bad_lang_raises():
    with pytest.raises(ToolError) as e:
        engine.run_snippet("ruby", "1", REPO_ROOT, timeout=5)
    assert e.value.code == "BAD_LANG" and e.value.exit_code == 2


@pytest.mark.skipif(not HAS_NODE, reason="node not installed")
def test_node_stdout():
    r = engine.run_snippet("node", "console.log(6*7)", REPO_ROOT, timeout=30)
    assert r["lang"] == "node" and r["returncode"] == 0
    assert r["stdout"].strip() == "42" and r["result_repr"] is None


@pytest.mark.skipif(not HAS_PY_VENV, reason="no project .venv python")
def test_python_unicode_stdout_does_not_crash():
    r = engine.run_snippet("python", 'print("café — 你好")', REPO_ROOT, timeout=30)
    assert r["returncode"] == 0, r["stderr"]
    assert "café — 你好" in r["stdout"]


@pytest.mark.skipif(not HAS_PY_VENV, reason="no project .venv python")
def test_python_unicode_result_repr():
    r = engine.run_snippet("python", '"café"', REPO_ROOT, timeout=30)
    assert r["result_repr"] == "'café'"


@pytest.mark.skipif(not HAS_PY_VENV, reason="no project .venv python")
def test_python_syntax_error_is_captured():
    r = engine.run_snippet("python", "def (", REPO_ROOT, timeout=30)
    assert r["returncode"] != 0 and "SyntaxError" in r["stderr"]
    assert r["result_repr"] is None


@pytest.mark.skipif(not HAS_PY_VENV, reason="no project .venv python")
def test_python_eval_time_exception_in_trailing_expr_is_captured():
    r = engine.run_snippet("python", "x = 1\nx / 0", REPO_ROOT, timeout=30)
    assert r["returncode"] != 0
    assert "ZeroDivisionError" in r["stderr"]
    assert r["result_repr"] is None


def test_timeout_with_bytes_output_is_serializable(monkeypatch):
    # POSIX regression (reproduced on any OS via monkeypatch): subprocess.TimeoutExpired's
    # .stdout/.stderr are raw BYTES on POSIX even in text mode (only Windows re-decodes
    # to str). Before the _norm fix, bytes passed straight into the result dict, and
    # run_tool's json.dumps(out) raised TypeError OUTSIDE its try/except -> zero envelope
    # on stdout. This is the headline defect: the JSON-envelope contract must hold on
    # every platform.
    if not HAS_PY_VENV:
        pytest.skip("no project .venv python")
    import json
    import subprocess as sp

    def _timeout(*a, **kw):
        raise sp.TimeoutExpired(cmd="x", timeout=1, output=b"partial\n", stderr=b"err\n")

    monkeypatch.setattr(engine.subprocess, "run", _timeout)
    r = engine.run_snippet("python", "1", REPO_ROOT, timeout=1)
    assert r["timed_out"] is True and r["returncode"] is None
    assert r["stdout"] == "partial\n" and r["stderr"] == "err\n"
    json.dumps(r)  # must not raise -- this is the contract that was broken


@pytest.mark.skipif(not HAS_PY_VENV, reason="no project .venv python")
def test_exec_failed_when_interpreter_launch_raises_oserror(monkeypatch):
    # A broken venv shim (or any launch-time OSError) is a dependency problem,
    # not an unnamed INTERNAL crash -> ToolError EXEC_FAILED, exit 3.
    def _boom(*a, **kw):
        raise FileNotFoundError("no such file or directory")

    monkeypatch.setattr(engine.subprocess, "run", _boom)
    with pytest.raises(ToolError) as e:
        engine.run_snippet("python", "1", REPO_ROOT, timeout=5)
    assert e.value.code == "EXEC_FAILED" and e.value.exit_code == 3


@pytest.mark.skipif(not HAS_PY_VENV, reason="no project .venv python")
def test_snippet_imports_resolve_against_project_root():
    # _harness.py runs as `python _harness.py <codefile>`, so sys.path[0] defaults to
    # groundwork's own snipeval package dir -- polluting a snippet's imports with
    # groundwork internals and shadowing project-local modules of the same name.
    # sys.path[0] must be the cwd (the project root), not the snipeval pkg dir.
    r = engine.run_snippet("python", "import sys; sys.path[0]", REPO_ROOT, timeout=30)
    assert r["result_repr"] is not None
    assert "snipeval" not in r["result_repr"]
