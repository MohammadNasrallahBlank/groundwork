"""Typed record builders + query/timeline over the SQLite store."""
import datetime
import json
from pathlib import Path

from groundwork.core.runner import ToolError
from groundwork.tools.recordstore.store import open_store

_STATUSES = ("open", "accepted", "rejected", "superseded")


def _now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


def _valid_ts(at: str) -> str:
    # accept ISO-8601; normalize a trailing Z, reject anything unparseable
    try:
        datetime.datetime.fromisoformat(at.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        raise ToolError("USAGE", f"--at must be ISO-8601, got {at!r}",
                        exit_code=2) from None
    return at


def _require(field: str, value: str) -> str:
    if not value or not str(value).strip():
        raise ToolError("USAGE", f"{field} is required and cannot be empty",
                        exit_code=2)
    return value


def _insert(root: Path, *, type_: str, ts: str | None, label: str,
            status: str | None, value: float | None, tags: str | None,
            data: dict) -> dict:
    ts = _valid_ts(ts) if ts else _now_iso()
    conn = open_store(root)
    try:
        cur = conn.execute(
            "insert into records(type, ts, label, status, value, tags, data) "
            "values (?,?,?,?,?,?,?)",
            [type_, ts, label, status, value, tags,
             json.dumps(data, sort_keys=True)])
        conn.commit()
        rid = cur.lastrowid
    finally:
        conn.close()
    return {"id": rid, "type": type_, "ts": ts, "label": label,
            "status": status, "value": value, "tags": tags, "data": data}


def add_decision(root: Path, *, subject: str, choice: str, status: str = "open",
                 rationale: str | None = None, tags: str | None = None,
                 at: str | None = None) -> dict:
    _require("subject", subject)
    _require("choice", choice)
    if status not in _STATUSES:
        raise ToolError("USAGE", f"status must be one of {_STATUSES}, "
                                 f"got {status!r}", exit_code=2)
    data = {"choice": choice, "status": status, "rationale": rationale}
    return _insert(root, type_="decision", ts=at, label=subject, status=status,
                   value=None, tags=tags, data=data)


def add_measurement(root: Path, *, metric: str, value, unit: str | None = None,
                    tags: str | None = None, at: str | None = None) -> dict:
    _require("metric", metric)
    try:
        num = float(value)
    except (TypeError, ValueError):
        raise ToolError("USAGE", f"value must be numeric, got {value!r}",
                        exit_code=2) from None
    data = {"value": num, "unit": unit}
    return _insert(root, type_="measurement", ts=at, label=metric, status=None,
                   value=num, tags=tags, data=data)


def add_event(root: Path, *, name: str, outcome: str | None = None,
              tags: str | None = None, at: str | None = None) -> dict:
    _require("name", name)
    data = {"outcome": outcome}
    return _insert(root, type_="event", ts=at, label=name, status=None,
                   value=None, tags=tags, data=data)


def _rows(root: Path, *, type_=None, status=None, label_like=None, tag=None,
          since=None, until=None, order="desc", limit=100):
    where, params = [], []
    if type_:
        where.append("type = ?")
        params.append(type_)
    if status:
        where.append("status = ?")
        params.append(status)
    if label_like:
        where.append("label like ?")
        params.append(label_like)
    if tag:
        # tags is a comma-joined list; match a whole element
        where.append("(',' || ifnull(tags,'') || ',') like ?")
        params.append(f"%,{tag},%")
    if since:
        where.append("ts >= ?")
        params.append(_valid_ts(since))
    if until:
        where.append("ts < ?")
        params.append(_valid_ts(until))
    clause = (" where " + " and ".join(where)) if where else ""
    sql = (f"select id, type, ts, label, status, value, tags, data from records"
           f"{clause} order by ts {order}, id {order} limit ?")
    conn = open_store(root)
    try:
        return conn.execute(sql, [*params, limit]).fetchall()
    finally:
        conn.close()


def query(root: Path, *, type=None, status=None, label_like=None, tag=None,
          since=None, until=None, limit=100) -> list[dict]:
    """Filtered records, newest first, with parsed data."""
    rows = _rows(root, type_=type, status=status, label_like=label_like,
                 tag=tag, since=since, until=until, order="desc", limit=limit)
    out = []
    for rid, typ, ts, label, st, value, tags, data in rows:
        out.append({"id": rid, "type": typ, "ts": ts, "label": label,
                    "status": st, "value": value, "tags": tags,
                    "data": json.loads(data)})
    return out


def _summary(typ: str, label: str, status, value, data: dict) -> str:
    if typ == "decision":
        return f"{data.get('choice', '')} [{data.get('status', '')}]".strip()
    if typ == "measurement":
        unit = data.get("unit") or ""
        v = value if value is not None else data.get("value")
        return f"{v} {unit}".strip()
    return str(data.get("outcome") or "")


def timeline(root: Path, *, type=None, since=None, until=None, desc=False,
             limit=100) -> list[dict]:
    """Records chronologically with a condensed per-type summary."""
    rows = _rows(root, type_=type, since=since, until=until,
                 order="desc" if desc else "asc", limit=limit)
    out = []
    for _rid, typ, ts, label, st, value, _tags, data in rows:
        d = json.loads(data)
        out.append({"ts": ts, "type": typ, "label": label,
                    "summary": _summary(typ, label, st, value, d)})
    return out
