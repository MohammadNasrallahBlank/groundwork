"""Format detection -> a DuckDB `d` view. CSV/JSON malformed rows counted via
strict-vs-ignore_errors; SQLite needs a table selector."""
from pathlib import Path

from groundwork.core.runner import ToolError

_CSV = {".csv", ".tsv"}
_PARQUET = {".parquet", ".pq"}
_JSONL = {".jsonl", ".ndjson"}
_JSON = {".json"}
_SQLITE = {".db", ".sqlite", ".sqlite3"}


def _connect():
    try:
        import duckdb
    except ImportError as e:
        raise ToolError("NO_DUCKDB", f"duckdb not importable: {e}", exit_code=3) from e
    return duckdb.connect()


def _reader(path: Path, suffix: str) -> str:
    posix = path.as_posix()
    if suffix in _CSV:
        # ignore_errors=true lets read_csv_auto sniff the real schema AND drop
        # malformed rows, instead of collapsing a ragged file to one column
        # (build-time finding). Delimiter forced only for TSV.
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


def list_tables(path: Path):
    con = _connect()
    con.execute("install sqlite")
    con.execute("load sqlite")
    rows = con.sql(
        f"select name from sqlite_scan('{path.as_posix()}', 'sqlite_master') "
        "where type='table' order by name").fetchall()
    con.close()
    return [r[0] for r in rows]


def _raw_data_lines(path: Path, has_header: bool) -> int:
    lines = [ln for ln in path.read_text(encoding="utf-8", errors="replace")
             .splitlines() if ln.strip()]
    return max(0, len(lines) - (1 if has_header else 0))


def _malformed_count(con, path: Path, suffix: str) -> int | None:
    # loaded = rows the (ignore_errors) view kept; malformed = raw data rows
    # the reader dropped. Only meaningful for line-oriented text formats.
    if suffix in _CSV:
        loaded = con.sql("select count(*) from d").fetchone()[0]
        return max(0, _raw_data_lines(path, has_header=True) - loaded)
    if suffix in _JSONL:
        loaded = con.sql("select count(*) from d").fetchone()[0]
        return max(0, _raw_data_lines(path, has_header=False) - loaded)
    return None  # parquet/sqlite are schema-typed; .json is not line-oriented


def load(path: Path, *, table: str | None = None):
    """Open the file as a DuckDB `d` view; returns (connection, format, malformed)."""
    path = Path(path)
    if not path.is_file():
        raise ToolError("NO_FILE", f"no such file: {path.as_posix()}", exit_code=2)
    suffix = path.suffix.lower()
    con = _connect()
    if suffix in _SQLITE:
        con.execute("install sqlite")
        con.execute("load sqlite")
        tables = [r[0] for r in con.sql(
            f"select name from sqlite_scan('{path.as_posix()}', 'sqlite_master') "
            "where type='table' order by name").fetchall()]
        if table is None:
            con.close()
            raise ToolError("NEED_TABLE",
                            f"{path.name} has tables {tables}; pass --table",
                            exit_code=4, detail={"tables": tables})
        if table not in tables:
            con.close()
            raise ToolError("USAGE", f"no table {table!r}; have {tables}", exit_code=2)
        con.execute(f"create view d as select * from "
                    f"sqlite_scan('{path.as_posix()}', '{table}')")
        return con, "sqlite", None
    reader = _reader(path, suffix)
    try:
        con.execute(f"create view d as select * from {reader}")
        # force materialization so an unreadable file fails here, not later
        con.sql("select count(*) from d").fetchone()
        malformed = _malformed_count(con, path, suffix)
    except Exception as e:
        con.close()
        raise ToolError("BAD_DATA", f"cannot read {path.name}: {e}") from e
    fmt = ("csv" if suffix in _CSV else "parquet" if suffix in _PARQUET
           else "jsonl" if suffix in _JSONL else "json")
    return con, fmt, malformed
