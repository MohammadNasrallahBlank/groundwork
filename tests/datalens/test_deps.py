"""Pins the duckdb contract plan 14 targets (verified 2026-07-08, duckdb 1.5.4)."""
import duckdb


def test_summarize_columns_shape(csv_file):
    con = duckdb.connect()
    con.execute(f"create view d as select * from read_csv_auto('{csv_file.as_posix()}')")
    cols = con.sql("summarize d").columns
    for expected in ("column_name", "column_type", "min", "max", "avg", "std",
                     "q25", "q50", "q75", "count", "null_percentage"):
        assert expected in cols


def test_reads_all_formats(csv_file, jsonl_file, parquet_file, sqlite_file):
    con = duckdb.connect()
    assert con.sql(
        f"select count(*) from read_csv_auto('{csv_file.as_posix()}')").fetchone()[0] == 4
    assert con.sql(
        f"select count(*) from read_json_auto('{jsonl_file.as_posix()}')").fetchone()[0] == 2
    assert con.sql(
        f"select count(*) from read_parquet('{parquet_file.as_posix()}')").fetchone()[0] == 2
    con.execute("install sqlite")
    con.execute("load sqlite")
    assert con.sql(
        f"select count(*) from sqlite_scan('{sqlite_file.as_posix()}', 'people')"
    ).fetchone()[0] == 3
