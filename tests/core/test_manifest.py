import json
import pytest
from groundwork.core.manifest import ManifestError, discover, load_manifest

GOOD = {
    "name": "hello", "version": "0.1.0",
    "purpose": "Reference tool proving the contract.",
    "reach_for_me_when": ["you need to verify groundwork is installed"],
    "commands": [{"name": "greet", "summary": "Say hello", "args": "--name <str>"}],
    "danger_level": "read_only", "cache": "off",
    "deps": {"python": [], "system": [], "optional": []},
}


def test_load_good_manifest(tmp_path):
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps(GOOD))
    m = load_manifest(p)
    assert m["name"] == "hello"


@pytest.mark.parametrize("mutate,fragment", [
    (lambda d: d.pop("purpose"), "missing required field: purpose"),
    (lambda d: d.update(danger_level="yolo"), "danger_level"),
    (lambda d: d.update(reach_for_me_when=[]), "reach_for_me_when must be non-empty"),
])
def test_bad_manifests_raise(tmp_path, mutate, fragment):
    bad = json.loads(json.dumps(GOOD))
    mutate(bad)
    p = tmp_path / "manifest.json"
    p.write_text(json.dumps(bad))
    with pytest.raises(ManifestError, match=fragment):
        load_manifest(p)


def test_discover_finds_hello():
    from pathlib import Path
    import groundwork
    tools_dir = Path(groundwork.__file__).parent / "tools"
    names = [m["name"] for m in discover(tools_dir)]
    assert "hello" in names
