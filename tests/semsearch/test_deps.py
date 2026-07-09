"""Pins the sqlite-vec and fastembed contracts plan 13 targets (verified at
authoring, 2026-07-08: sqlite-vec 0.1.9, fastembed 0.8.0). Correct the PLAN
to reality if the installed versions differ."""
import sqlite3

import numpy as np
import pytest

from groundwork.tools.semsearch.index import loadable_extensions_available

requires_vec = pytest.mark.skipif(
    not loadable_extensions_available(),
    reason="Python built without loadable SQLite extensions (sqlite-vec unavailable)")


@requires_vec
def test_sqlite_vec_loads_and_knn_on_this_platform():
    import sqlite_vec
    db = sqlite3.connect(":memory:")
    db.enable_load_extension(True)
    sqlite_vec.load(db)
    db.enable_load_extension(False)
    db.execute("create virtual table vt using vec0(embedding float[4])")
    db.execute("insert into vt(rowid, embedding) values (1, ?)",
               [sqlite_vec.serialize_float32([0.1, 0.2, 0.3, 0.4])])
    db.execute("insert into vt(rowid, embedding) values (2, ?)",
               [sqlite_vec.serialize_float32([0.9, 0.8, 0.7, 0.6])])
    rows = db.execute(
        "select rowid, distance from vt where embedding match ? "
        "order by distance limit 2",
        [sqlite_vec.serialize_float32([0.1, 0.2, 0.3, 0.4])]).fetchall()
    assert rows[0] == (1, 0.0)          # exact match is distance 0
    assert rows[1][0] == 2 and rows[1][1] > 0


def test_fastembed_embeds_documents_and_queries():
    from fastembed import TextEmbedding

    from groundwork.tools.semsearch import _DEFAULT_MODEL
    m = TextEmbedding(model_name=_DEFAULT_MODEL)
    docs = list(m.embed(["def retry(fn): ...", "def charge(card): ..."]))
    assert len(docs) == 2 and docs[0].dtype == np.float32
    dim = docs[0].shape[0]
    assert dim in (384, 512)            # small-model dimensions
    q = list(m.query_embed(["retry logic"]))
    assert q[0].shape[0] == dim
