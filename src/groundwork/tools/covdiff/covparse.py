"""coverage.py JSON report -> per-file executed/missing line sets."""
import json
from pathlib import Path

from groundwork.core.runner import ToolError


def parse_coverage_obj(obj: dict, root: Path) -> dict[str, dict]:
    """Normalize a coverage.json object to {rel_posix: {executed, missing}}."""
    root = Path(root).resolve()
    out: dict[str, dict] = {}
    for path, info in obj.get("files", {}).items():
        p = Path(path)
        try:
            rel = (p.resolve().relative_to(root).as_posix() if p.is_absolute()
                   else Path(path).as_posix())
        except ValueError:
            rel = p.as_posix()  # outside root: keep as-is
        out[rel] = {"executed": set(info.get("executed_lines", [])),
                    "missing": set(info.get("missing_lines", []))}
    return out


def load_coverage(json_path: Path, root: Path) -> dict[str, dict]:
    p = Path(json_path)
    if not p.is_file():
        raise ToolError("BAD_COVERAGE", f"no coverage report: {p.as_posix()}",
                        exit_code=2)
    try:
        obj = json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        raise ToolError("BAD_COVERAGE", f"unreadable coverage report: {e}",
                        exit_code=2) from e
    return parse_coverage_obj(obj, root)
