from pathlib import Path

import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.cartographer.extract import extract
from groundwork.tools.cartographer.languages import detect_language

FIX = Path("tests/fixtures/cartomap").resolve()


def test_detect_language_by_extension():
    assert detect_language(Path("a/b.py")) == "python"
    assert detect_language(Path("a/b.tsx")) == "tsx"
    assert detect_language(Path("a/b.kt")) == "kotlin"
    assert detect_language(Path("a/b.txt")) is None


def test_extract_python_symbols():
    src = (FIX / "pkg" / "util.py").read_bytes()
    symbols, refs = extract(FIX / "pkg" / "util.py", src, "python")
    by_name = {s.name: s for s in symbols}
    assert by_name["helper"].kind == "function" and by_name["helper"].line == 1
    assert by_name["Formatter"].kind == "class"
    assert by_name["format"].kind == "method"
    assert "helper" in {r.name for r in refs}


def test_extract_python_references():
    src = (FIX / "pkg" / "app.py").read_bytes()
    symbols, refs = extract(FIX / "pkg" / "app.py", src, "python")
    ref_names = {r.name for r in refs}
    assert {"Formatter", "helper", "format", "App", "run"} <= ref_names


def test_extract_broken_source_raises():
    with pytest.raises(ToolError) as e:
        extract(Path("x.py"), b"def (:\n", "python")
    assert e.value.code == "PARSE_ERROR"


def test_nested_function_in_method_is_function_not_method():
    src = (FIX / "pkg" / "nested.py").read_bytes()
    symbols, _ = extract(FIX / "pkg" / "nested.py", src, "python")
    by_name = {s.name: s for s in symbols}
    assert by_name["method_a"].kind == "method"
    assert by_name["closure"].kind == "function"   # nested closure, NOT a method
    assert by_name["top"].kind == "function"


def test_qualified_name_reflects_scope():
    src = (FIX / "pkg" / "nested.py").read_bytes()
    symbols, _ = extract(FIX / "pkg" / "nested.py", src, "python")
    by_name = {s.name: s for s in symbols}
    assert by_name["method_a"].qualified_name == "Outer.method_a"
    assert by_name["closure"].qualified_name == "Outer.method_a.closure"
    assert by_name["top"].qualified_name == "top"


def test_languages_populated_after_load():
    from groundwork.tools.cartographer.languages import LANGUAGES, load_spec
    load_spec("python")
    assert "python" in LANGUAGES
