"""Tiny type-spec -> hypothesis strategy expression language."""
from groundwork.core.runner import ToolError

_SCALARS = {
    "int": "st.integers()",
    "float": "st.floats(allow_nan=False)",
    "text": "st.text()",
    "bool": "st.booleans()",
    "none": "st.none()",
}


def _split_top(s: str) -> list[str]:
    """Split on top-level commas. Nested tuples inside a tuple are deferred
    (v1 treats all commas as top-level); documented limitation."""
    return [x.strip() for x in s.split(",") if x.strip()]


def strategy_expr(spec: str) -> str:
    """Map a spec (int|float|text|bool|none|list:<t>|tuple:<t,...>) to st...."""
    spec = spec.strip()
    if spec in _SCALARS:
        return _SCALARS[spec]
    if spec.startswith("list:"):
        return f"st.lists({strategy_expr(spec[len('list:'):])})"
    if spec.startswith("tuple:"):
        inners = _split_top(spec[len("tuple:"):])
        return f"st.tuples({', '.join(strategy_expr(i) for i in inners)})"
    raise ToolError("BAD_STRATEGY",
                    f"unknown strategy {spec!r} (int|float|text|bool|none|"
                    "list:<t>|tuple:<t,...>)", exit_code=2)
