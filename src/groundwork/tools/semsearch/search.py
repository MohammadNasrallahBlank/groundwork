"""KNN search with an honest confidence floor. Distance -> similarity is
pinned; results below the floor are flagged, never dropped silently."""
from pathlib import Path

from groundwork.core.runner import ToolError
from groundwork.tools.semsearch import _DEFAULT_MODEL, _MIN_SCORE
from groundwork.tools.semsearch.embed import Embedder
from groundwork.tools.semsearch.index import open_index


def _similarity(distance: float) -> float:
    """Measured at build time (2026-07-08): sqlite-vec's default is PLAIN L2,
    d = sqrt(2(1-cos)) on unit vectors, range [0, 2]. cos = 1 - d^2/2, so the
    [0,1] similarity (1+cos)/2 = 1 - d^2/4. Monotonic decreasing; d=0 -> 1.0,
    d=2 -> 0.0."""
    return max(0.0, min(1.0, 1.0 - (distance * distance) / 4.0))


def search(root: Path, query: str, *, k: int = 10,
           min_score: float | None = None, _model_override: str | None = None) -> dict:
    """Semantic KNN over the index; results below the floor are flagged."""
    if not query.strip():
        raise ToolError("USAGE", "empty query", exit_code=2)
    floor = _MIN_SCORE if min_score is None else min_score
    conn = open_index(root)
    try:
        meta = dict(conn.execute("select key, value from meta").fetchall())
        index_model = meta.get("model", _DEFAULT_MODEL)
        want_model = _model_override or index_model
        if want_model != index_model:
            raise ToolError("MODEL_MISMATCH",
                            f"index built with {index_model!r}, query wants "
                            f"{want_model!r}; re-index with --rebuild",
                            exit_code=4)
        import sqlite_vec
        qv = Embedder(index_model).embed_query(query)
        # The LIMIT must sit directly on the vec0 KNN, not on a join result
        # (sqlite-vec requires a k/LIMIT constraint on the match); do the KNN
        # in a subquery, then join the metadata. (build-time finding.)
        rows = conn.execute(
            "select c.file, c.symbol, c.kind, c.start_line, c.end_line, v.distance "
            "from (select rowid, distance from vec_chunks "
            "      where embedding match ? order by distance limit ?) v "
            "join chunks c on c.rowid = v.rowid order by v.distance",
            [sqlite_vec.serialize_float32(qv), k]).fetchall()
    finally:
        conn.close()
    results = []
    for file, symbol, kind, start, end, dist in rows:
        score = round(_similarity(dist), 4)
        results.append({"file": file, "symbol": symbol, "kind": kind,
                        "start_line": start, "end_line": end, "score": score,
                        "low_confidence": score < floor})
    results.sort(key=lambda r: (-r["score"], r["file"], r["start_line"]))
    return {"query": query, "model": index_model, "results": results,
            "confident_results": sum(1 for r in results if not r["low_confidence"])}
