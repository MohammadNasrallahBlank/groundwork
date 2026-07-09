import pytest

from groundwork.core.cliparse import UsageParser
from groundwork.core.runner import ToolError


def test_missing_required_subcommand_raises_toolerror_with_message():
    p = UsageParser(prog="x", exit_on_error=False)
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("go")
    with pytest.raises(ToolError) as e:
        p.parse_args([])
    assert e.value.code == "USAGE" and e.value.exit_code == 2
    assert "cmd" in str(e.value) or "arguments" in str(e.value)


def test_unknown_argument_raises_toolerror():
    p = UsageParser(prog="x", exit_on_error=False)
    p.add_subparsers(dest="cmd", required=True).add_parser("go")
    with pytest.raises(ToolError) as e:
        p.parse_args(["go", "--bogus"])
    assert e.value.code == "USAGE"
