from groundwork.core import envelope as env

def test_ok_envelope_shape():
    e = env.ok({"answer": 42}, tool="hello", version="0.1.0", elapsed_ms=3, cache="off")
    assert e["ok"] is True
    assert e["data"] == {"answer": 42}
    assert e["meta"] == {"tool": "hello", "version": "0.1.0", "elapsed_ms": 3, "cache": "off"}
    assert "error" not in e

def test_err_envelope_shape():
    e = env.err("BAD_INPUT", "width must be >= 0", detail={"got": -1},
                tool="hello", version="0.1.0", elapsed_ms=1, cache="off")
    assert e["ok"] is False
    assert e["error"] == {"code": "BAD_INPUT", "message": "width must be >= 0", "detail": {"got": -1}}
    assert "data" not in e

def test_exit_codes_are_stable():
    assert (env.EXIT_OK, env.EXIT_ERROR, env.EXIT_USAGE,
            env.EXIT_MISSING_DEP, env.EXIT_ESCALATE) == (0, 1, 2, 3, 4)
