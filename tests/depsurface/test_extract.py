# tests/depsurface/test_extract.py
from pathlib import Path

import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.depsurface.extract import extract_surface

FIXTURE_SP = Path("tests/fixtures/sitepkgs").resolve()
BROKEN_SP = Path("tests/fixtures/sitepkgs_broken").resolve()


def test_extract_demopkg_matches_ground_truth():
    s = extract_surface("demopkg", FIXTURE_SP, "1.2.3")
    assert s["package"] == "demopkg" and s["version"] == "1.2.3"
    assert s["language"] == "python"
    top = s["modules"]["demopkg"]
    assert top["doc"] == "Demo package for depsurface ground truth."
    assert top["exports"] == ["Engine", "start", "VERSION"]
    assert top["aliases"] == {"Engine": "demopkg.core.Engine",
                              "start": "demopkg.core.start"}
    assert "VERSION" in top["attributes"]
    assert "_private_helper" not in top["functions"]
    core = s["modules"]["demopkg.core"]
    assert core["functions"]["start"]["sig"] == \
        "(engine: Engine, *, retries: int = 3) -> bool"
    eng = core["classes"]["Engine"]
    assert eng["methods"]["start"]["sig"] == "(self, speed: int = 1) -> bool"
    assert "_tune" not in eng["methods"]
    assert "max_rpm" in eng["attributes"]
    assert "demopkg._internal" not in s["modules"]
    assert s["modules"]["demopkg.util"]["functions"]["call"]["sig"] == \
        "(fn, /, *args, timeout: int = 5, **kwargs) -> object"


def test_extract_is_deterministic():
    import json
    a = json.dumps(extract_surface("demopkg", FIXTURE_SP, "1.2.3"), sort_keys=True)
    b = json.dumps(extract_surface("demopkg", FIXTURE_SP, "1.2.3"), sort_keys=True)
    assert a == b


def test_missing_package_raises_named_error():
    with pytest.raises(ToolError) as e:
        extract_surface("nosuchpkg", FIXTURE_SP, "unknown")
    assert e.value.code == "PACKAGE_NOT_FOUND"


def test_broken_package_raises_named_error():
    with pytest.raises(ToolError) as e:
        extract_surface("brokenpkg", BROKEN_SP, "unknown")
    assert e.value.code == "EXTRACT_ERROR"
