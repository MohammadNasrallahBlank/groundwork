"""Import a property file, run each @given test in-process, extract the
shrunk counterexample from the failing exception's __notes__."""
import importlib.util
import re
import sys
from pathlib import Path

from groundwork.core.runner import ToolError

_ARG = re.compile(r"^\s*([A-Za-z_]\w*)=(.+?),?\s*$")


def parse_counterexample(note: str) -> dict:
    r"""Parse hypothesis's 'Falsifying example: name(\n  arg=value,\n)' note."""
    out = {}
    for line in note.splitlines()[1:]:            # skip the 'Falsifying...' header
        if line.strip() in (")", ""):
            continue
        m = _ARG.match(line)
        if m:
            out[m.group(1)] = m.group(2).rstrip(",").strip()
    return out


def _counterexample_from_exc(exc: BaseException) -> dict | None:
    for note in getattr(exc, "__notes__", []):
        if "Falsifying example" in note:
            return parse_counterexample(note)
    return None


def run_property_file(path: Path) -> dict:
    """Run every @given property in the file; report per-property verdicts."""
    path = Path(path).resolve()
    spec = importlib.util.spec_from_file_location(f"_prop_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    added = str(path.parent)
    sys.path.insert(0, added)                     # target modules import here
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        raise ToolError("BAD_PROPERTY",
                        f"cannot import property file {path.name}: {e}",
                        exit_code=1) from e
    finally:
        if sys.path and sys.path[0] == added:
            sys.path.pop(0)

    try:
        from hypothesis import is_hypothesis_test
    except ImportError as e:
        raise ToolError("BAD_PROPERTY", f"hypothesis unavailable: {e}",
                        exit_code=1) from e

    props = []
    for name in sorted(dir(module)):
        fn = getattr(module, name)
        if not callable(fn) or not is_hypothesis_test(fn):
            continue
        entry = {"name": name, "passed": True, "counterexample": None,
                 "error": None}
        try:
            fn()
        except Exception as e:  # noqa: BLE001 - any falsification is a finding
            entry["passed"] = False
            entry["error"] = type(e).__name__
            entry["counterexample"] = _counterexample_from_exc(e)
        props.append(entry)

    return {"file": path.as_posix(), "properties": props,
            "passed": all(p["passed"] for p in props), "checked": len(props)}
