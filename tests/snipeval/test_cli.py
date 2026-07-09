import json
import subprocess
from pathlib import Path

import pytest

from groundwork.tools.snipeval import interpreters
from groundwork.tools.snipeval.cli import handler

REPO_ROOT = Path(__file__).resolve().parents[2]
HAS_PY_VENV = interpreters.python_interpreter(REPO_ROOT) is not None


def run_cli(*args, stdin=None):
    return subprocess.run(["uv", "run", "groundwork", "snipeval", *args],
                          capture_output=True, text=True, input=stdin)


@pytest.mark.skipif(not HAS_PY_VENV, reason="no project .venv python")
def test_run_python_from_code_flag():
    p = run_cli("run", "--lang", "python", "--root", str(REPO_ROOT),
                "--code", "print('ok')\n21*2")
    assert p.returncode == 0, p.stdout
    out = json.loads(p.stdout)
    assert out["ok"] and out["data"]["stdout"].strip() == "ok"
    assert out["data"]["result_repr"] == "42"


@pytest.mark.skipif(not HAS_PY_VENV, reason="no project .venv python")
def test_run_python_from_stdin():
    p = run_cli("run", "--lang", "python", "--root", str(REPO_ROOT), stdin="print(1+1)")
    out = json.loads(p.stdout)
    assert out["data"]["stdout"].strip() == "2"


@pytest.mark.skipif(not HAS_PY_VENV, reason="no project .venv python")
def test_relative_root_resolves_to_absolute_interpreter_path():
    # cli.py's handler used a bare Path(ns.root) (root-relative). With cwd=root passed
    # to subprocess.run, a relative root gets re-resolved against itself on POSIX ->
    # FileNotFoundError. Resolving --root to an absolute path in the handler (before the
    # NO_ROOT check) fixes this at the source: the interpreter path handed to the engine
    # is always absolute, regardless of platform. This test runs the handler directly
    # (portable, no subprocess-launch quirk needed) assuming pytest's cwd is REPO_ROOT.
    data = handler(["run", "--lang", "python", "--root", ".", "--code", "1"])
    assert Path(data["interpreter"]).is_absolute()


def test_no_interpreter_exits_3(tmp_path):
    p = run_cli("run", "--lang", "python", "--root", str(tmp_path), "--code", "1")
    assert p.returncode == 3
    assert json.loads(p.stdout)["error"]["code"] == "NO_INTERPRETER"


def test_bad_lang_exits_2():
    p = run_cli("run", "--lang", "ruby", "--code", "1")
    assert p.returncode == 2
    assert json.loads(p.stdout)["error"]["code"] == "BAD_LANG"


def test_missing_required_lang_is_usage():
    p = run_cli("run", "--code", "1")
    assert p.returncode == 2
    err = json.loads(p.stdout)["error"]
    assert err["code"] == "USAGE" and err["message"] not in ("2", "")


def test_self_test():
    assert run_cli("self-test").returncode == 0


def test_bad_root_without_code_does_not_hang(tmp_path):
    # No --code and no stdin piped: the old handler read sys.stdin.read()
    # before validating --root, so a real interactive invocation would block
    # waiting for EOF instead of fast-failing NO_ROOT. Reordering root
    # validation before the stdin read fixes that. stdin=DEVNULL gives
    # immediate EOF here (so this alone can't prove the old code would hang
    # interactively), but the wall-clock timeout plus NO_ROOT assertion is a
    # regression guard for the fix and for accidental future reordering.
    p = subprocess.run(
        ["uv", "run", "groundwork", "snipeval", "run", "--lang", "python",
         "--root", str(tmp_path / "nope")],
        capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=60)
    assert p.returncode == 2
    assert json.loads(p.stdout)["error"]["code"] == "NO_ROOT"
