"""gates.yaml over safe defaults. A broken config NEVER disarms the gate."""
import copy
from pathlib import Path

import yaml

DEFAULTS: dict = {
    "fail_mode": "open",
    "secrets": {"enabled": True, "allow_files": []},
    "commands": {"enabled": True, "extra_deny": [], "extra_ask": []},
    "paths": {"deny": [], "ask": ["**/.env", "**/.env.*"]},
}


def _merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in over.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(root: Path) -> dict:
    """Full effective config: defaults merged under .groundwork/gates.yaml.

    A missing config is not an error (defaults apply); a malformed one falls
    back to armed defaults with `config_error` set — never disarmed.
    """
    p = Path(root) / ".groundwork" / "gates.yaml"
    if not p.is_file():
        return copy.deepcopy(DEFAULTS)
    try:
        loaded = yaml.safe_load(p.read_text(encoding="utf-8"))
    except (yaml.YAMLError, OSError, UnicodeDecodeError) as e:
        cfg = copy.deepcopy(DEFAULTS)
        cfg["config_error"] = f"gates.yaml unreadable, defaults applied: {e}"
        return cfg
    if not isinstance(loaded, dict):
        cfg = copy.deepcopy(DEFAULTS)
        cfg["config_error"] = "gates.yaml is not a mapping, defaults applied"
        return cfg
    return _merge(DEFAULTS, loaded)
