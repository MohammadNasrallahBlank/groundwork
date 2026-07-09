import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.propcheck.strategies import strategy_expr


@pytest.mark.parametrize("spec,expr", [
    ("int", "st.integers()"),
    ("float", "st.floats(allow_nan=False)"),
    ("text", "st.text()"),
    ("bool", "st.booleans()"),
    ("none", "st.none()"),
    ("list:int", "st.lists(st.integers())"),
    ("tuple:int,text", "st.tuples(st.integers(), st.text())"),
    ("list:list:int", "st.lists(st.lists(st.integers()))"),
])
def test_known_strategies(spec, expr):
    assert strategy_expr(spec) == expr


def test_unknown_strategy_rejected():
    with pytest.raises(ToolError) as ei:
        strategy_expr("banana")
    assert ei.value.code == "BAD_STRATEGY" and ei.value.exit_code == 2
