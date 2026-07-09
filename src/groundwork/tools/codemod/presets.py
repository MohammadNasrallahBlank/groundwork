"""Engine 2: libcst bundled codemod commands behind a named registry."""
import libcst as cst
from libcst.codemod import CodemodContext
from libcst.codemod.commands.convert_format_to_fstring import (
    ConvertFormatStringCommand)
from libcst.codemod.commands.remove_unused_imports import (
    RemoveUnusedImportsCommand)

from groundwork.core.runner import ToolError

_COMMANDS = {
    "py-fstringify": ConvertFormatStringCommand,
    "py-remove-unused-imports": RemoveUnusedImportsCommand,
}
PRESETS = {
    "py-fstringify": 'convert "...".format(...) calls to f-strings (libcst)',
    "py-remove-unused-imports": "remove imports nothing references (libcst)",
}


def run_preset(source: str, name: str) -> tuple[str, None]:
    """Run a named libcst codemod command; returns (new_source, None)."""
    if name not in _COMMANDS:
        raise ToolError("USAGE", f"unknown preset {name!r}; "
                                 f"available: {sorted(PRESETS)}", exit_code=2)
    try:
        module = cst.parse_module(source)
    except cst.ParserSyntaxError as e:
        raise ValueError(f"libcst could not parse source: {e}") from e
    out = _COMMANDS[name](CodemodContext()).transform_module(module)
    return out.code, None
