"""`groundwork <tool> [args...]` — routes to tools/<tool>/cli.py:main."""
import importlib
import json
import sys

from groundwork.core.envelope import EXIT_MISSING_DEP, EXIT_USAGE, err

BUILTINS: dict[str, str] = {
    "cache": "groundwork.builtins.cache_cmd",
    "manifest": "groundwork.builtins.manifest_cmd",
    "skillgen": "groundwork.builtins.skillgen_cmd",
    "doctor": "groundwork.builtins.doctor_cmd",
    "new-tool": "groundwork.builtins.new_tool_cmd",
}


def _fail(code: str, message: str, *, exit_code: int = EXIT_USAGE) -> None:
    print(json.dumps(err(code, message, tool="groundwork", version="0.1.0")))
    raise SystemExit(exit_code)


def main() -> None:
    argv = sys.argv[1:]
    if not argv:
        _fail("USAGE", "usage: groundwork <tool> <command> [args]")
    tool, rest = argv[0], argv[1:]
    module_name = BUILTINS.get(tool, f"groundwork.tools.{tool}.cli")
    try:
        mod = importlib.import_module(module_name)
    except ModuleNotFoundError as e:
        if module_name == e.name or module_name.startswith(f"{e.name}."):
            _fail("UNKNOWN_TOOL", f"no such tool: {tool}")
        else:
            _fail("MISSING_DEP", f"missing dependency: {e.name}", exit_code=EXIT_MISSING_DEP)
        return
    mod.main(rest)
