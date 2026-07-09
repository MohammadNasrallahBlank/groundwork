import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.datalens.loader import list_tables, load


def test_load_csv_registers_view_and_no_malformed(csv_file):
    con, fmt, malformed = load(csv_file)
    assert fmt == "csv" and malformed == 0
    assert con.sql("select count(*) from d").fetchone()[0] == 4
    con.close()


def test_load_counts_malformed_rows(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("a,b\n1,2\nBROKEN_ONE_COLUMN\n3,4\n", encoding="utf-8")
    con, fmt, malformed = load(p)
    assert fmt == "csv" and malformed == 1
    assert con.sql("select count(*) from d").fetchone()[0] == 2
    con.close()


def test_load_parquet_reports_null_malformed(parquet_file):
    con, fmt, malformed = load(parquet_file)
    assert fmt == "parquet" and malformed is None
    con.close()


def test_sqlite_without_table_lists_and_escalates(sqlite_file):
    with pytest.raises(ToolError) as ei:
        load(sqlite_file)
    assert ei.value.code == "NEED_TABLE" and ei.value.exit_code == 4
    assert "people" in str(ei.value.detail)
    assert list_tables(sqlite_file) == ["people"]


def test_sqlite_with_table_loads(sqlite_file):
    con, fmt, _ = load(sqlite_file, table="people")
    assert fmt == "sqlite" and con.sql("select count(*) from d").fetchone()[0] == 3
    con.close()


def test_missing_file_and_unknown_format(tmp_path):
    with pytest.raises(ToolError) as ei:
        load(tmp_path / "nope.csv")
    assert ei.value.code == "NO_FILE"
    weird = tmp_path / "x.weird"
    weird.write_text("data", encoding="utf-8")
    with pytest.raises(ToolError) as ei2:
        load(weird)
    assert ei2.value.code == "UNKNOWN_FORMAT"
