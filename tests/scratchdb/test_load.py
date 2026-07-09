import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.scratchdb import store
from groundwork.tools.scratchdb.pad import load_file, reader_expr


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("GROUNDWORK_DATA_DIR", str(tmp_path / "data"))


@pytest.fixture()
def sales_csv(tmp_path):
    p = tmp_path / "sales.csv"
    p.write_text("region,amt\nx,10\ny,20\nx,30\n", encoding="utf-8")
    return p


def test_reader_expr_uses_absolute_path(sales_csv):
    expr = reader_expr(sales_csv)
    assert "read_csv_auto" in expr and sales_csv.resolve().as_posix() in expr


def test_load_creates_pad_and_view(sales_csv):
    out = load_file("pad1", sales_csv)
    assert out["pad"] == "pad1" and out["view"] == "sales" and out["rows"] == 3
    assert store.pad_exists("pad1")


def test_view_is_live_not_a_copy(sales_csv):
    load_file("pad1", sales_csv)
    sales_csv.write_text("region,amt\nx,10\ny,20\nx,30\nz,99\n", encoding="utf-8")
    import duckdb
    con = duckdb.connect(str(store.pad_path("pad1")))
    assert con.sql("select count(*) from sales").fetchone()[0] == 4
    con.close()


def test_custom_view_name_and_second_file(sales_csv, tmp_path):
    load_file("pad1", sales_csv, as_name="s1")
    other = tmp_path / "costs.csv"
    other.write_text("region,cost\nx,5\n", encoding="utf-8")
    load_file("pad1", other)
    import duckdb
    con = duckdb.connect(str(store.pad_path("pad1")))
    views = {r[0] for r in con.sql("select view_name from duckdb_views() "
                                   "where not internal").fetchall()}
    con.close()
    assert {"s1", "costs"} <= views


def test_load_missing_file_and_unknown_format(tmp_path):
    with pytest.raises(ToolError) as ei:
        load_file("pad1", tmp_path / "nope.csv")
    assert ei.value.code == "NO_FILE"
    weird = tmp_path / "x.weird"
    weird.write_text("z", encoding="utf-8")
    with pytest.raises(ToolError) as ei2:
        load_file("pad1", weird)
    assert ei2.value.code == "UNKNOWN_FORMAT"
