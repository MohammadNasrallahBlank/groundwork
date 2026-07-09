import json
import pytest
from groundwork.core import runner
from groundwork.core.envelope import EXIT_OK, EXIT_ERROR


def test_runner_prints_ok_envelope_and_exits_zero(capsys):
    def handler(args: list[str]) -> dict:
        return {"echo": args}
    with pytest.raises(SystemExit) as e:
        runner.run_tool("hello", "0.1.0", handler, ["a", "b"])
    assert e.value.code == EXIT_OK
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["data"] == {"echo": ["a", "b"]}
    assert out["meta"]["tool"] == "hello"
    assert isinstance(out["meta"]["elapsed_ms"], int)


def test_runner_catches_exceptions_as_internal_error(capsys):
    def handler(args: list[str]) -> dict:
        raise ValueError("boom")
    with pytest.raises(SystemExit) as e:
        runner.run_tool("hello", "0.1.0", handler, [])
    assert e.value.code == EXIT_ERROR
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is False
    assert out["error"]["code"] == "INTERNAL"
    assert "boom" in out["error"]["message"]


def test_runner_respects_tool_error(capsys):
    from groundwork.core.runner import ToolError
    def handler(args: list[str]) -> dict:
        raise ToolError("BAD_INPUT", "nope", exit_code=4, detail={"x": 1})
    with pytest.raises(SystemExit) as e:
        runner.run_tool("hello", "0.1.0", handler, [])
    assert e.value.code == 4
    out = json.loads(capsys.readouterr().out)
    assert out["error"]["code"] == "BAD_INPUT" and out["error"]["detail"] == {"x": 1}


def test_exit_override_keeps_ok_envelope(capsys):
    def handler(args):
        return {"verdict": "failures", "_exit_override": 1}
    with pytest.raises(SystemExit) as e:
        runner.run_tool("t", "1", handler, [])
    assert e.value.code == 1
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True and out["data"] == {"verdict": "failures"}
