# tests/depsurface/test_render.py
from pathlib import Path

import griffe

from groundwork.tools.depsurface.extract import first_doc_line, render_signature

FIXTURE_SP = str(Path("tests/fixtures/sitepkgs").resolve())


def load_core():
    return griffe.load("demopkg.core", search_paths=[FIXTURE_SP],
                       allow_inspection=False)


def test_render_signature_keyword_only_and_defaults():
    core = load_core()
    assert render_signature(core.members["start"]) == \
        "(engine: Engine, *, retries: int = 3) -> bool"


def test_render_signature_method_with_default():
    core = load_core()
    engine = core.members["Engine"]
    assert render_signature(engine.members["start"]) == \
        "(self, speed: int = 1) -> bool"


def test_first_doc_line():
    core = load_core()
    assert first_doc_line(core) == "Core engine."
    assert first_doc_line(core.members["start"]) == "Start an engine with retries."


def test_first_doc_line_none_when_absent():
    core = load_core()
    assert first_doc_line(core.members["Engine"].members["_tune"]) is None


def test_render_signature_varargs_positional_only_and_kwargs():
    util = griffe.load("demopkg.util", search_paths=[FIXTURE_SP],
                       allow_inspection=False)
    assert render_signature(util.members["call"]) == \
        "(fn, /, *args, timeout: int = 5, **kwargs) -> object"
