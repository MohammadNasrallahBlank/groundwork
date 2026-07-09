"""Dataset drift: PSI per numeric column, share-shift per categorical."""
import math
from pathlib import Path

from groundwork.core.runner import ToolError
from groundwork.tools.datalens.loader import load
from groundwork.tools.datalens.profile import _is_numeric

_EPS = 1e-6


def _psi(ref: list[float], cur: list[float]) -> float:
    total = 0.0
    for p_a, p_b in zip(ref, cur):
        a = max(p_a, _EPS)
        b = max(p_b, _EPS)
        total += (b - a) * math.log(b / a)
    return total


def _reading(psi: float) -> str:
    return "stable" if psi < 0.1 else "moderate" if psi < 0.25 else "significant"


def _schema(con) -> dict:
    z = con.sql("select * from d limit 0")
    return {n: str(t) for n, t in zip(z.columns, z.types)}


def _hist(con, col: str, lo: float, hi: float, bins: int) -> list[float]:
    w = (hi - lo) / bins if hi > lo else 1.0
    rows = dict(con.sql(
        f'select least({bins - 1}, greatest(0, '
        f'cast(floor(("{col}" - {lo}) / {w}) as int))) as bkt, count(*) '
        f'from d where "{col}" is not null group by bkt').fetchall())
    counts = [rows.get(i, 0) for i in range(bins)]
    total = sum(counts) or 1
    return [c / total for c in counts]


def _shares(con, col: str) -> dict:
    rows = con.sql(f'select "{col}", count(*) from d group by 1').fetchall()
    total = sum(r[1] for r in rows) or 1
    return {r[0]: r[1] / total for r in rows}


def compare_datasets(a: Path, b: Path, *, table_a=None, table_b=None,
                     bins: int = 10, balance_max: int = 20) -> dict:
    """PSI drift per numeric column, share-shift per categorical, across a/b."""
    con_a, _fa, _ma = load(a, table=table_a)
    con_b, _fb, _mb = load(b, table=table_b)
    try:
        sa, sb = _schema(con_a), _schema(con_b)
        shared = [c for c in sa if c in sb]
        only_a = [c for c in sa if c not in sb]
        only_b = [c for c in sb if c not in sa]
        numeric_drift, categorical_drift, type_mismatch = {}, {}, []
        for col in shared:
            if sa[col] != sb[col]:
                type_mismatch.append(col)
                continue
            if _is_numeric(sa[col]):
                rng = con_a.sql(f'select min("{col}"), max("{col}") from d').fetchone()
                if rng[0] is None:
                    continue
                lo, hi = float(rng[0]), float(rng[1])
                psi = _psi(_hist(con_a, col, lo, hi, bins),
                           _hist(con_b, col, lo, hi, bins))
                numeric_drift[col] = {"psi": round(psi, 4),
                                      "reading": _reading(psi)}
            else:
                da = con_a.sql(f'select count(distinct "{col}") from d').fetchone()[0]
                if not da or da > balance_max:
                    continue
                sha = _shares(con_a, col)
                shb = _shares(con_b, col)
                keys = sorted(set(sha) | set(shb))
                categorical_drift[col] = [
                    [k, round(sha.get(k, 0.0), 4), round(shb.get(k, 0.0), 4),
                     round(shb.get(k, 0.0) - sha.get(k, 0.0), 4)] for k in keys]
        if not numeric_drift and not categorical_drift and not type_mismatch:
            raise ToolError("NO_COMMON_COLUMNS",
                            "no comparable columns between the two datasets",
                            exit_code=4,
                            detail={"only_in_a": only_a, "only_in_b": only_b})
        return {"a": a.as_posix(), "b": b.as_posix(),
                "numeric_drift": numeric_drift,
                "categorical_drift": categorical_drift,
                "only_in_a": only_a, "only_in_b": only_b,
                "type_mismatch": type_mismatch}
    finally:
        con_a.close()
        con_b.close()
