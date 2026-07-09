"""Project-local SQLite ledger: claims (calibration) + runs (proof-of-value)."""
import datetime
import sqlite3
from pathlib import Path

from groundwork.core.runner import ToolError

_SCHEMA = """
create table if not exists claims(
    id integer primary key autoincrement,
    ts text not null, statement text not null, confidence real not null,
    source text, tags text,
    resolved integer not null default 0, outcome integer, resolved_ts text
);
create table if not exists runs(
    id integer primary key autoincrement,
    ts text not null, tool text not null, cache text,
    avoided integer not null default 0, caught integer not null default 0
);
"""


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _ts(at: str | None) -> str:
    if at is None:
        return _now()
    try:
        datetime.datetime.fromisoformat(at.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        raise ToolError("USAGE", f"--at must be ISO-8601, got {at!r}",
                        exit_code=2) from None
    return at


def open_store(root: Path) -> sqlite3.Connection:
    path = Path(root).resolve() / ".groundwork" / "ledger.db"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        conn = sqlite3.connect(path)
        conn.executescript(_SCHEMA)
        conn.commit()
    except sqlite3.DatabaseError as e:
        raise ToolError("BAD_STORE", f"cannot open ledger: {e}") from e
    return conn


def add_claim(root: Path, *, statement: str, confidence, source, tags,
              at) -> dict:
    if not statement or not statement.strip():
        raise ToolError("USAGE", "statement is required", exit_code=2)
    try:
        conf = float(confidence)
    except (TypeError, ValueError):
        raise ToolError("USAGE", f"confidence must be numeric, got {confidence!r}",
                        exit_code=2) from None
    if not 0.0 <= conf <= 1.0:
        raise ToolError("USAGE", f"confidence must be in [0,1], got {conf}",
                        exit_code=2)
    ts = _ts(at)
    conn = open_store(root)
    try:
        cur = conn.execute(
            "insert into claims(ts, statement, confidence, source, tags) "
            "values (?,?,?,?,?)", [ts, statement, conf, source, tags])
        conn.commit()
        rid = cur.lastrowid
    finally:
        conn.close()
    return {"id": rid, "ts": ts, "statement": statement, "confidence": conf,
            "source": source, "tags": tags, "resolved": False}


def resolve_claim(root: Path, claim_id: int, outcome: bool, *, at) -> dict:
    ts = _ts(at)
    conn = open_store(root)
    try:
        row = conn.execute("select resolved from claims where id=?",
                           [claim_id]).fetchone()
        if row is None:
            raise ToolError("NO_CLAIM", f"no claim id {claim_id}", exit_code=2)
        if row[0]:
            raise ToolError("USAGE", f"claim {claim_id} is already resolved",
                            exit_code=2)
        conn.execute("update claims set resolved=1, outcome=?, resolved_ts=? "
                     "where id=?", [1 if outcome else 0, ts, claim_id])
        conn.commit()
    finally:
        conn.close()
    return {"id": claim_id, "resolved": True, "outcome": bool(outcome),
            "resolved_ts": ts}


def record_run(root: Path, *, tool: str, cache, avoided: bool, caught: bool,
               at) -> dict:
    if not tool or not tool.strip():
        raise ToolError("USAGE", "tool is required", exit_code=2)
    ts = _ts(at)
    conn = open_store(root)
    try:
        conn.execute("insert into runs(ts, tool, cache, avoided, caught) "
                     "values (?,?,?,?,?)",
                     [ts, tool, cache, 1 if avoided else 0, 1 if caught else 0])
        conn.commit()
    finally:
        conn.close()
    return {"tool": tool, "cache": cache, "avoided": bool(avoided),
            "caught": bool(caught), "ts": ts}
