"""sqlite-vec index: meta + files(sha256) + chunks + a vec0 virtual table.
Incremental by file content hash."""
import hashlib
import sqlite3
from pathlib import Path

from groundwork.core.runner import ToolError
from groundwork.tools.semsearch.chunk import iter_chunks
from groundwork.tools.semsearch.embed import Embedder


NO_EXT_MSG = (
    "this Python's sqlite3 was built without loadable-extension support, which "
    "sqlite-vec requires; use a CPython that enables extensions (python.org, "
    "Homebrew, or a system python3) to run semsearch here"
)


def loadable_extensions_available() -> bool:
    """True iff this Python's sqlite3 can load compiled extensions.

    sqlite-vec is a loadable extension. Some CPython builds — notably uv's
    python-build-standalone on macOS — are compiled without loadable-extension
    support, so ``enable_load_extension`` is absent entirely. Probe the
    capability up front so callers fail cleanly instead of crashing with an
    AttributeError deep inside a query.
    """
    return hasattr(sqlite3.Connection, "enable_load_extension")


def _index_path(root: Path) -> Path:
    return Path(root).resolve() / ".groundwork" / "semsearch" / "index.db"


def _connect(path: Path) -> sqlite3.Connection:
    import sqlite_vec
    if not loadable_extensions_available():
        raise ToolError("NO_VEC", NO_EXT_MSG, exit_code=3)
    conn = sqlite3.connect(path)
    conn.enable_load_extension(True)
    try:
        sqlite_vec.load(conn)
    except Exception as e:
        raise ToolError("NO_VEC", f"sqlite-vec did not load: {e}", exit_code=3) from e
    conn.enable_load_extension(False)
    return conn


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _init_schema(conn: sqlite3.Connection, model: str, dim: int) -> None:
    conn.execute("create table if not exists meta(key text primary key, value text)")
    conn.execute("create table if not exists files("
                 "path text primary key, sha256 text)")
    conn.execute("create table if not exists chunks("
                 "rowid integer primary key, file text, symbol text, kind text, "
                 "start_line integer, end_line integer, text text)")
    conn.execute(f"create virtual table if not exists vec_chunks "
                 f"using vec0(embedding float[{dim}])")
    conn.execute("insert or replace into meta values('model', ?)", [model])
    conn.execute("insert or replace into meta values('dim', ?)", [str(dim)])


def build_index(root: Path, model: str, *, rebuild: bool = False) -> dict:
    """Build or incrementally refresh the semantic index under .groundwork/."""
    root = Path(root).resolve()
    embedder = Embedder(model)
    path = _index_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    if rebuild and path.exists():
        path.unlink()
    conn = _connect(path)
    _init_schema(conn, model, embedder.dim)

    import sqlite_vec
    prior = dict(conn.execute("select path, sha256 from files").fetchall())
    seen_files: set[str] = set()
    by_file: dict[str, list[dict]] = {}
    errors: list[dict] = []
    for ch in iter_chunks(root):
        by_file.setdefault(ch["file"], []).append(ch)

    files_indexed = reused = 0
    for rel, chunks in by_file.items():
        seen_files.add(rel)
        sha = _sha(root / rel)
        if not rebuild and prior.get(rel) == sha:
            reused += 1
            continue
        old = [r[0] for r in conn.execute(
            "select rowid from chunks where file=?", [rel]).fetchall()]
        for rid in old:
            conn.execute("delete from vec_chunks where rowid=?", [rid])
        conn.execute("delete from chunks where file=?", [rel])
        vectors = embedder.embed_documents([c["text"] for c in chunks])
        for c, v in zip(chunks, vectors):
            cur = conn.execute(
                "insert into chunks(file, symbol, kind, start_line, end_line, text)"
                " values(?,?,?,?,?,?)",
                [c["file"], c["symbol"], c["kind"], c["start_line"],
                 c["end_line"], c["text"]])
            conn.execute("insert into vec_chunks(rowid, embedding) values(?, ?)",
                         [cur.lastrowid, sqlite_vec.serialize_float32(v)])
        conn.execute("insert or replace into files values(?, ?)", [rel, sha])
        files_indexed += 1

    for gone in set(prior) - seen_files:
        old = [r[0] for r in conn.execute(
            "select rowid from chunks where file=?", [gone]).fetchall()]
        for rid in old:
            conn.execute("delete from vec_chunks where rowid=?", [rid])
        conn.execute("delete from chunks where file=?", [gone])
        conn.execute("delete from files where path=?", [gone])

    conn.commit()
    total = conn.execute("select count(*) from chunks").fetchone()[0]
    conn.close()
    return {"model": model, "dim": embedder.dim, "files_indexed": files_indexed,
            "files_skipped": 0, "chunks": total, "reused": reused,
            "errors": errors}


def open_index(root: Path) -> sqlite3.Connection:
    """Open the index connection with sqlite-vec loaded; NO_INDEX (4) if absent."""
    path = _index_path(root)
    if not path.is_file():
        raise ToolError("NO_INDEX",
                        f"no index at {path.as_posix()}; run: groundwork "
                        "semsearch index", exit_code=4)
    return _connect(path)
