"""One JSON report per dataset: schema, per-column stats, balance, outliers."""
from pathlib import Path

from groundwork.tools.datalens.loader import load

_NUMERIC_TYPES = ("TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT",
                  "UTINYINT", "USMALLINT", "UINTEGER", "UBIGINT",
                  "FLOAT", "DOUBLE", "DECIMAL", "REAL")


def _is_numeric(duck_type: str) -> bool:
    return any(duck_type.upper().startswith(t) for t in _NUMERIC_TYPES)


def _round(v):
    return round(v, 4) if isinstance(v, float) else v


def _num(row, idx, key):
    if row is None:
        return None
    v = row[idx[key]]
    try:
        return float(v) if v is not None else None
    except (TypeError, ValueError):
        return v  # min/max on a string column are lexical


def _outliers(con, name: str) -> dict:
    q = con.sql(f'select quantile_cont("{name}", 0.25), '
                f'quantile_cont("{name}", 0.75) from d').fetchone()
    if q[0] is None or q[1] is None:
        return {"count": 0, "low": 0, "high": 0}
    q25, q75 = float(q[0]), float(q[1])
    iqr = q75 - q25
    lo, hi = q25 - 1.5 * iqr, q75 + 1.5 * iqr
    low = con.sql(f'select count(*) from d where "{name}" < {lo}').fetchone()[0]
    high = con.sql(f'select count(*) from d where "{name}" > {hi}').fetchone()[0]
    return {"count": low + high, "low": low, "high": high}


def profile_dataset(path: Path, *, table: str | None = None,
                    balance_max: int = 20) -> dict:
    """Schema, per-column stats, class balance, and IQR outliers for a dataset."""
    con, fmt, malformed = load(path, table=table)
    try:
        head = con.sql("select * from d limit 0")
        schema = [{"name": n, "type": str(t)}
                  for n, t in zip(head.columns, head.types)]
        rows = con.sql("select count(*) from d").fetchone()[0]
        summ_rel = con.sql("summarize d")
        sc = summ_rel.columns
        idx = {name: i for i, name in enumerate(sc)}
        summ = {r[idx["column_name"]]: r for r in summ_rel.fetchall()}

        column_stats, balance, outliers = [], {}, {}
        for col in schema:
            name, dtype = col["name"], col["type"]
            row = summ.get(name)
            count = row[idx["count"]] if row else 0
            null_pct = float(row[idx["null_percentage"]] or 0) if row else 0.0
            nulls = int(round(rows * null_pct / 100)) if rows else 0
            # Exact, not SUMMARIZE's approx_unique (HyperLogLog): a profiler
            # that reports "distinct: 21" for a 20-unique column is worse than
            # useless. count(distinct) excludes NULLs, which is what we want.
            distinct = con.sql(
                f'select count(distinct "{name}") from d').fetchone()[0]
            base = {"name": name, "type": dtype, "count": count,
                    "nulls": nulls, "null_pct": _round(null_pct),
                    "distinct": distinct,
                    "min": _round(_num(row, idx, "min")),
                    "max": _round(_num(row, idx, "max"))}
            if _is_numeric(dtype):
                base.update({"mean": _round(_num(row, idx, "avg")),
                             "std": _round(_num(row, idx, "std")),
                             "q25": _round(_num(row, idx, "q25")),
                             "q50": _round(_num(row, idx, "q50")),
                             "q75": _round(_num(row, idx, "q75"))})
                oc = _outliers(con, name)
                if oc["count"]:
                    outliers[name] = oc
            column_stats.append(base)
            if 0 < (distinct or 0) <= balance_max:
                bal = con.sql(f'select "{name}", count(*) from d group by 1 '
                              "order by 2 desc, 1 limit ?", params=[balance_max]
                              ).fetchall()
                balance[name] = [[b[0], b[1]] for b in bal]
        return {"path": path.as_posix(), "format": fmt, "rows": rows,
                "columns": len(schema), "malformed_rows": malformed,
                "schema": schema, "column_stats": column_stats,
                "balance": balance, "outliers": outliers}
    finally:
        con.close()
