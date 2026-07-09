import sqlite3

import pytest


@pytest.fixture()
def csv_file(tmp_path):
    p = tmp_path / "data.csv"
    p.write_text("id,score,cat\n1,10.5,x\n2,20.0,y\n3,,x\n4,15.5,x\n",
                 encoding="utf-8")
    return p


@pytest.fixture()
def jsonl_file(tmp_path):
    p = tmp_path / "data.jsonl"
    p.write_text('{"id":1,"score":10.5,"cat":"x"}\n'
                 '{"id":2,"score":20.0,"cat":"y"}\n', encoding="utf-8")
    return p


@pytest.fixture()
def parquet_file(tmp_path):
    import duckdb
    p = tmp_path / "data.parquet"
    con = duckdb.connect()
    con.execute(
        "copy (select * from (values (1,10.5,'x'),(2,20.0,'y')) t(id,score,cat)) "
        f"to '{p.as_posix()}' (format parquet)")
    con.close()
    return p


@pytest.fixture()
def sqlite_file(tmp_path):
    p = tmp_path / "data.db"
    c = sqlite3.connect(p)
    c.execute("create table people(id integer, name text, age integer)")
    c.executemany("insert into people values (?,?,?)",
                  [(1, "a", 30), (2, "b", 40), (3, "c", 50)])
    c.commit()
    c.close()
    return p
