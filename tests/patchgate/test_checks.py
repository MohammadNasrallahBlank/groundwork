from groundwork.tools.patchgate.checks import check_content


def test_valid_python_passes():
    out = check_content("pkg/a.py", "def f():\n    return 1\n")
    assert out == {"file": "pkg/a.py", "checked": True, "ok": True,
                   "checker": "compile", "error": None}


def test_broken_python_fails_with_line_info():
    out = check_content("pkg/a.py", "def f(:\n    return 1\n")
    assert out["ok"] is False and out["checker"] == "compile"
    assert "line 1" in out["error"]


def test_python_indentation_error_fails():
    out = check_content("a.py", "def f():\nreturn 1\n")
    assert out["ok"] is False


def test_valid_json_passes_and_broken_fails():
    assert check_content("m.json", '{"a": 1}\n')["ok"] is True
    bad = check_content("m.json", '{"a": 1,,}\n')
    assert bad["ok"] is False and bad["checker"] == "json"


def test_treesitter_languages_pass_and_fail():
    good = check_content("x.ts", "const a: number = 1;\n")
    assert good["ok"] is True and good["checker"] == "tree-sitter"
    bad = check_content("x.ts", "const a: = = = ;;;{{{\n")
    assert bad["ok"] is False and bad["checker"] == "tree-sitter"


def test_unknown_extension_passes_unchecked():
    out = check_content("notes.txt", "anything at all")
    assert out == {"file": "notes.txt", "checked": False, "ok": True,
                   "checker": None, "error": None}


def test_java_and_kotlin_are_covered():
    assert check_content("A.java", "class A { int x = 1; }\n")["checked"] is True
    assert check_content("A.kt", "val x = 1\n")["checked"] is True
