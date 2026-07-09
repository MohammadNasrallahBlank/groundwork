"""Adapter protocol + registry. detect() must be cheap: file-presence only."""
from pathlib import Path
from typing import Protocol, runtime_checkable

from groundwork.tools.verify.models import Diagnostic


@runtime_checkable
class Adapter(Protocol):
    name: str
    def detect(self, root: Path) -> bool: ...
    def run(self, root: Path, changed: list[str] | None) -> list[Diagnostic]: ...


_REGISTRY: list[Adapter] = []
_TEST_SLOTS: list[Adapter] = []


def register(adapter: Adapter, _test_slot: bool = False) -> None:
    # No-op on a duplicate name: a module imported twice (or re-registered)
    # must not silently double-count diagnostics from the same logical adapter.
    target = _TEST_SLOTS if _test_slot else _REGISTRY
    if any(a.name == adapter.name for a in target):
        return
    target.append(adapter)


def detect_adapters(root: Path) -> list[Adapter]:
    pool = _REGISTRY + _TEST_SLOTS
    return [a for a in pool if a.detect(root)]
