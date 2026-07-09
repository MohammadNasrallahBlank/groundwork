"""Pins the ast_grep_py and libcst contracts plan 10 targets (probe-verified
at authoring, 2026-07-08: ast-grep-py 0.44.1, libcst 1.8.6). If the installed
versions differ, correct the PLAN and its code to the real shapes."""


def test_astgrep_find_match_replace_commit():
    from ast_grep_py import SgRoot
    src = "def f():\n    print(1)\n\ndef g():\n    print(2)\n"
    root = SgRoot(src, "python").root()
    hits = root.find_all(pattern="print($A)")
    assert [h.text() for h in hits] == ["print(1)", "print(2)"]
    edits = [h.replace(f"log({h.get_match('A').text()})") for h in hits]
    out = root.commit_edits(edits)
    assert out == "def f():\n    log(1)\n\ndef g():\n    log(2)\n"


def test_astgrep_no_match_is_empty_not_error():
    from ast_grep_py import SgRoot
    root = SgRoot("x = 1\n", "python").root()
    assert root.find_all(pattern="print($A)") == []


def test_libcst_fstringify_command():
    import libcst as cst
    from libcst.codemod import CodemodContext
    from libcst.codemod.commands.convert_format_to_fstring import (
        ConvertFormatStringCommand)
    src = 'def f(name):\n    return "hello {}".format(name)\n'
    out = ConvertFormatStringCommand(CodemodContext()).transform_module(
        cst.parse_module(src))
    assert 'f"hello {name}"' in out.code


def test_libcst_remove_unused_imports_command():
    import libcst as cst
    from libcst.codemod import CodemodContext
    from libcst.codemod.commands.remove_unused_imports import (
        RemoveUnusedImportsCommand)
    src = "import os\nimport sys\n\nprint(sys.argv)\n"
    out = RemoveUnusedImportsCommand(CodemodContext()).transform_module(
        cst.parse_module(src))
    assert "import os" not in out.code and "import sys" in out.code
