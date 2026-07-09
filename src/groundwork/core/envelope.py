"""Every Groundwork tool prints exactly one of these envelopes to stdout."""
from typing import Any

EXIT_OK = 0
EXIT_ERROR = 1
EXIT_USAGE = 2
EXIT_MISSING_DEP = 3
EXIT_ESCALATE = 4


def _meta(tool: str, version: str, elapsed_ms: int, cache: str) -> dict[str, Any]:
    return {"tool": tool, "version": version, "elapsed_ms": elapsed_ms, "cache": cache}


def ok(data: dict[str, Any], *, tool: str, version: str,
       elapsed_ms: int = 0, cache: str = "off") -> dict[str, Any]:
    return {"ok": True, "data": data, "meta": _meta(tool, version, elapsed_ms, cache)}


def err(code: str, message: str, *, detail: Any = None, tool: str, version: str,
        elapsed_ms: int = 0, cache: str = "off") -> dict[str, Any]:
    return {"ok": False,
            "error": {"code": code, "message": message, "detail": detail},
            "meta": _meta(tool, version, elapsed_ms, cache)}
