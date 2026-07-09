"""Project-local SQLite record store under <root>/.groundwork/recordstore.db."""
import sqlite3
from pathlib import Path

from groundwork.core.runner import ToolError

_SCHEMA = """
create table if not exists records(
    id integer primary key autoincrement,
    type text not null,
    ts text not null,
    label text not null,
    status text,
    value real,
    tags text,
    data text not null
);
create index if not exists idx_records_type_ts on records(type, ts);
"""


def store_path(root: Path) -> Path:
    return Path(root).resolve() / ".groundwork" / "recordstore.db"


def open_store(root: Path) -> sqlite3.Connection:
    """Open (creating schema if absent) the project record store."""
    path = store_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        conn = sqlite3.connect(path)
        conn.executescript(_SCHEMA)
        conn.commit()
    except sqlite3.DatabaseError as e:
        raise ToolError("BAD_STORE", f"cannot open record store: {e}") from e
    return conn
