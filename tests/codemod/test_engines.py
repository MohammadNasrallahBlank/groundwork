import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.codemod.astgrep import LANG_GLOBS, rewrite_source
from groundwork.tools.codemod.combyengine import (build_args, comby_available,
                                                  rewrite_source as comby_rewrite)
from groundwork.tools.codemod.presets import run_preset

requires_comby = pytest.mark.skipif(
    not comby_available(), reason="comby binary not on PATH (no native Windows build)")


def test_astgrep_rewrite_with_metavars():
    src = "def f():\n    print(1)\n    print(2)\n"
    out, count = rewrite_source(src, "python", "print($A)", "logger.info($A)")
    assert count == 2
    assert out == "def f():\n    logger.info(1)\n    logger.info(2)\n"


def test_astgrep_preserves_crlf_outside_edits():
    src = "def f():\r\n    print(1)\r\n"
    out, count = rewrite_source(src, "python", "print($A)", "log($A)")
    assert count == 1
    assert out == "def f():\r\n    log(1)\r\n"


def test_astgrep_no_match_returns_source_unchanged():
    out, count = rewrite_source("x = 1\n", "python", "print($A)", "log($A)")
    assert count == 0 and out == "x = 1\n"


def test_astgrep_lang_globs_cover_v1_set():
    assert LANG_GLOBS == {"python": "**/*.py", "javascript": "**/*.js",
                          "typescript": "**/*.ts", "tsx": "**/*.tsx",
                          "java": "**/*.java", "kotlin": "**/*.kt"}


def test_preset_fstringify():
    src = 'x = "hi {}".format(name)\n'
    out, count = run_preset(src, "py-fstringify")
    assert 'f"hi {name}"' in out and count is None


def test_preset_remove_unused_imports():
    src = "import os\nimport sys\n\nprint(sys.argv)\n"
    out, _ = run_preset(src, "py-remove-unused-imports")
    assert "import os" not in out and "import sys" in out


def test_preset_unknown_is_usage():
    with pytest.raises(ToolError) as ei:
        run_preset("x = 1\n", "py-make-it-better")
    assert ei.value.code == "USAGE" and ei.value.exit_code == 2


def test_preset_unparseable_source_raises_valueerror():
    with pytest.raises(ValueError):
        run_preset("def broken(:\n", "py-fstringify")


def test_comby_args_shape():
    assert build_args("foo(:[a])", "bar(:[a])", ".py") == [
        "comby", "foo(:[a])", "bar(:[a])", ".py", "-stdin", "-stdout"]


def test_comby_absent_raises_no_engine():
    if comby_available():
        pytest.skip("comby present; absence path not testable here")
    with pytest.raises(ToolError) as ei:
        comby_rewrite("foo(1)\n", "foo(:[a])", "bar(:[a])", ".py")
    assert ei.value.code == "NO_ENGINE" and ei.value.exit_code == 3


@requires_comby
def test_comby_rewrites_when_present():
    out, _ = comby_rewrite("foo(1)\n", "foo(:[a])", "bar(:[a])", ".py")
    assert out == "bar(1)\n"
