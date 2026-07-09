"""Run a snippet in the project interpreter as a timed subprocess."""
import os
import subprocess
import tempfile
import time
from pathlib import Path

from groundwork.core.envelope import EXIT_MISSING_DEP, EXIT_USAGE
from groundwork.core.runner import ToolError
from groundwork.tools.snipeval.interpreters import node_interpreter, python_interpreter

_HARNESS = Path(__file__).parent / "_harness.py"


def _norm(s):
    # subprocess.TimeoutExpired's .stdout/.stderr are raw BYTES on POSIX even in text
    # mode (only Windows re-decodes to str). Bytes passed unnormalized into the result
    # dict crash run_tool's json.dumps(out) OUTSIDE its try/except -> zero envelope on
    # stdout. Normalize both str and bytes (and None) to str here, unconditionally.
    if isinstance(s, bytes):
        return s.decode("utf-8", "replace")
    return s or ""


def _result(lang, interp, proc, timed_out, elapsed_ms, result_repr):
    return {"lang": lang, "interpreter": interp.as_posix(),
            "returncode": None if timed_out else proc.returncode,
            "timed_out": timed_out, "duration_ms": elapsed_ms,
            "stdout": _norm(proc.stdout),
            "stderr": _norm(proc.stderr),
            "result_repr": result_repr}


def _run_python(code: str, root: Path, timeout: int) -> dict:
    interp = python_interpreter(root)
    if interp is None:
        raise ToolError("NO_INTERPRETER",
                        f"no project .venv python under {root.as_posix()}",
                        exit_code=EXIT_MISSING_DEP)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as td:
        code_file = Path(td) / "snippet.py"
        code_file.write_text(code, encoding="utf-8", newline="\n")
        repr_file = Path(td) / "repr.out"
        full_env = {**os.environ,
                    "GROUNDWORK_SNIPEVAL_REPR_OUT": str(repr_file),
                    "PYTHONIOENCODING": "utf-8",
                    "PYTHONUTF8": "1"}
        start = time.perf_counter()
        try:
            proc = subprocess.run(
                [str(interp), str(_HARNESS), str(code_file)],
                cwd=root, capture_output=True, encoding="utf-8",
                errors="replace", timeout=timeout, env=full_env)
            timed_out = False
        except subprocess.TimeoutExpired as e:
            proc = e  # has .stdout/.stderr (may be None; bytes on POSIX, str on Windows)
            timed_out = True
        except OSError as e:
            # A broken venv shim (or any launch-time failure) is a dependency problem,
            # not an unnamed INTERNAL crash.
            raise ToolError("EXEC_FAILED", f"could not launch interpreter: {e}",
                            exit_code=EXIT_MISSING_DEP) from e
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        result_repr = None
        if not timed_out and repr_file.exists():
            result_repr = repr_file.read_text(encoding="utf-8", errors="replace")
    return _result("python", interp, proc, timed_out, elapsed_ms, result_repr)


def _run_node(code: str, root: Path, timeout: int) -> dict:
    interp = node_interpreter(root)
    if interp is None:
        raise ToolError("NO_INTERPRETER", "node not on PATH",
                        exit_code=EXIT_MISSING_DEP)
    start = time.perf_counter()
    try:
        proc = subprocess.run([str(interp), "-e", code], cwd=root,
                              capture_output=True, encoding="utf-8",
                              errors="replace", timeout=timeout)
        timed_out = False
    except subprocess.TimeoutExpired as e:
        proc = e
        timed_out = True
    except OSError as e:
        raise ToolError("EXEC_FAILED", f"could not launch interpreter: {e}",
                        exit_code=EXIT_MISSING_DEP) from e
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    return _result("node", interp, proc, timed_out, elapsed_ms, None)


def run_snippet(lang: str, code: str, root: Path, timeout: int) -> dict:
    if lang == "python":
        return _run_python(code, root, timeout)
    if lang == "node":
        return _run_node(code, root, timeout)
    raise ToolError("BAD_LANG", f"unsupported language: {lang!r} (python|node)",
                    exit_code=EXIT_USAGE)
