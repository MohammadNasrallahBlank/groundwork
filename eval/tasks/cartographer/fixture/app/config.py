"""Configuration loading."""
import tomllib
from pathlib import Path


def load_config(path: str) -> dict:
    """Read a TOML config file, returning {} if it does not exist."""
    p = Path(path)
    if not p.is_file():
        return {}
    return tomllib.loads(p.read_text(encoding="utf-8"))
