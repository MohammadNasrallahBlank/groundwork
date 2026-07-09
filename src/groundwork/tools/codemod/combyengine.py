"""Engine 3: the comby binary (OPTIONAL - no native Windows build exists)."""
import shutil
import subprocess

from groundwork.core.runner import ToolError


def comby_available() -> bool:
    return shutil.which("comby") is not None


def build_args(pattern: str, rewrite: str, ext: str) -> list[str]:
    return ["comby", pattern, rewrite, ext, "-stdin", "-stdout"]


def rewrite_source(source: str, pattern: str, rewrite: str, ext: str) -> tuple[str, None]:
    """Rewrite source through the comby binary; returns (new_source, None)."""
    if not comby_available():
        raise ToolError("NO_ENGINE",
                        "comby is not on PATH (no native Windows build; "
                        "install via opam/brew/docker on POSIX)", exit_code=3)
    try:
        proc = subprocess.run(build_args(pattern, rewrite, ext), input=source,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=120)
    except subprocess.TimeoutExpired as e:
        raise ToolError("ENGINE_ERROR", "comby timed out") from e
    except OSError as e:
        raise ToolError("ENGINE_ERROR", f"comby failed to start: {e}") from e
    if proc.returncode != 0:
        raise ToolError("ENGINE_ERROR", "comby exited non-zero",
                        detail=proc.stderr[-2000:])
    return proc.stdout, None
