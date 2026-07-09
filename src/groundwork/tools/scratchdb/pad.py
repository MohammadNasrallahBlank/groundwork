"""Load a file as a live view in a named pad; query/list/drop views."""
import datetime
import decimal
import uuid
from pathlib import Path

from groundwork.core.runner import ToolError
from groundwork.tools.scratchdb import store

_CSV = {".csv", ".tsv"}
_PARQUET = {".parquet", ".pq"}
_JSONL = {".jsonl", ".ndjson"}
_JSON = {".json"}


def _connect(name: str):
    try:
        import duckdb
    except ImportError as e:
        raise ToolError("NO_DUCKDB", f"duckdb not importable: {e}", exit_code=3) from e
    path = store.pad_path(name)
    path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(str(path))


def reader_expr(path: Path) -> str:
    """Absolute-path read expression by extension (persisted-view safe)."""
    posix = Path(path).resolve().as_posix()
    suffix = Path(path).suffix.lower()
    if suffix in _CSV:
        delim = ", delim='\\t'" if suffix == ".tsv" else ""
        return f"read_csv_auto('{posix}'{delim}, ignore_errors=true)"
    if suffix in _PARQUET:
        return f"read_parquet('{posix}')"
    if suffix in _JSONL:
        return (f"read_json_auto('{posix}', format='newline_delimited', "
                "ignore_errors=true)")
    if suffix in _JSON:
        return f"read_json_auto('{posix}')"
    raise ToolError("UNKNOWN_FORMAT", f"unsupported extension {suffix!r}", exit_code=2)


def _fmt(suffix: str) -> str:
    return ("csv" if suffix in _CSV else "parquet" if suffix in _PARQUET
            else "jsonl" if suffix in _JSONL else "json")


def _safe_view(stem: str) -> str:
    cleaned = "".join(c if c.isalnum() or c == "_" else "_" for c in stem)
    return cleaned or "view"


def load_file(name: str, file: Path, *, as_name: str | None = None) -> dict:
    """Register a data file as a live view in pad `name` (creates the pad)."""
    file = Path(file)
    if not file.is_file():
        raise ToolError("NO_FILE", f"no such file: {file.as_posix()}", exit_code=2)
    expr = reader_expr(file)                       # raises UNKNOWN_FORMAT
    view = as_name or _safe_view(file.stem)
    con = _connect(name)
    try:
        con.execute(f'create or replace view "{view}" as select * from {expr}')
        rows = con.sql(f'select count(*) from "{view}"').fetchone()[0]
    finally:
        con.close()
    return {"pad": name, "view": view, "file": file.resolve().as_posix(),
            "format": _fmt(file.suffix.lower()), "rows": rows}


def _require_pad(name: str):
    if not store.pad_exists(name):
        raise ToolError("NO_PAD", f"no scratchpad {name!r}; "
                                  f"existing: {store.list_pads()}", exit_code=4)
    return _connect(name)


def _coerce(v):
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    if isinstance(v, (datetime.date, datetime.datetime, datetime.time,
                      decimal.Decimal, uuid.UUID)):
        return str(v)
    if isinstance(v, (bytes, bytearray, memoryview)):
        return bytes(v).hex()
    return str(v)


def query(name: str, sql: str, *, limit: int = 1000) -> dict:
    """Run SQL against pad `name`; JSON-coerced rows, capped at `limit`."""
    con = _require_pad(name)
    try:
        wrapped = f"select * from ({sql}) _q limit {limit + 1}"
        try:
            rel = con.sql(wrapped)
            columns = list(rel.columns)
            fetched = rel.fetchall()
        except Exception as e:
            raise ToolError("SQL_ERROR", f"query failed: {e}",
                            exit_code=1, detail=str(e)) from e
        truncated = len(fetched) > limit
        rows = [[_coerce(v) for v in r] for r in fetched[:limit]]
        return {"columns": columns, "rows": rows, "row_count": len(rows),
                "truncated": truncated}
    finally:
        con.close()


def list_views(name: str) -> list[dict]:
    """Views and user tables in pad `name`, sorted by name."""
    con = _require_pad(name)
    try:
        views = [{"name": r[0], "kind": "view"} for r in con.sql(
            "select view_name from duckdb_views() where not internal "
            "order by view_name").fetchall()]
        tables = [{"name": r[0], "kind": "table"} for r in con.sql(
            "select table_name from duckdb_tables() where not internal "
            "order by table_name").fetchall()]
        return sorted(views + tables, key=lambda d: d["name"])
    finally:
        con.close()


def drop_view(name: str, view: str) -> dict:
    """Drop one view or user table from pad `name`."""
    con = _require_pad(name)
    try:
        existing = {r[0] for r in con.sql(
            "select view_name from duckdb_views() where not internal").fetchall()}
        existing |= {r[0] for r in con.sql(
            "select table_name from duckdb_tables() where not internal").fetchall()}
        if view not in existing:
            raise ToolError("NO_VIEW", f"no view/table {view!r} in pad {name!r}",
                            exit_code=2)
        con.execute(f'drop view if exists "{view}"')
        con.execute(f'drop table if exists "{view}"')
        return {"pad": name, "dropped": view}
    finally:
        con.close()
