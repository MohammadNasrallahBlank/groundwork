from pathlib import Path
from groundwork.tools.verify.adapters import Adapter, detect_adapters, register


class FakeAdapter:
    name = "fake"
    def detect(self, root: Path) -> bool:
        return (root / "fake.marker").exists()
    def run(self, root: Path, changed: list[str] | None):
        return []


def test_registry_detects_by_marker(tmp_path):
    register(FakeAdapter(), _test_slot=True)
    assert [a.name for a in detect_adapters(tmp_path)] == []
    (tmp_path / "fake.marker").touch()
    assert [a.name for a in detect_adapters(tmp_path)] == ["fake"]


def test_protocol_is_structural():
    assert isinstance(FakeAdapter(), Adapter)


class FakeAdapterDup:
    name = "fake"
    def detect(self, root: Path) -> bool:
        return (root / "fake.marker").exists()
    def run(self, root: Path, changed: list[str] | None):
        return []


def test_register_is_idempotent_by_name(tmp_path):
    register(FakeAdapter(), _test_slot=True)
    register(FakeAdapterDup(), _test_slot=True)
    (tmp_path / "fake.marker").touch()
    # Without the dedup guard both instances would detect() == True here,
    # double-counting diagnostics from a single logical adapter.
    assert [a.name for a in detect_adapters(tmp_path)] == ["fake"]
