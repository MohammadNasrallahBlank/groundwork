"""Demo package for depsurface ground truth."""
from demopkg.core import Engine, start

__all__ = ["Engine", "start", "VERSION"]

VERSION = "1.2.3"


def _private_helper():
    return None
