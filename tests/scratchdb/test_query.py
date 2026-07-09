import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.scratchdb.pad import (drop_view, list_views, load_file,
                                            query)


@pytest.fixture(autouse=True)
def _isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("GROUNDWORK_DATA_DIR", str(tmp_path / "data"))


@pytest.fixture()
def loaded(tmp_path):
    p = tmp_path / "sales.csv"
    p.write_text("region,amt\nx,10\ny,20\nx,30\n", encoding="utf-8")
    load_file("pad", p)
    return "pad"


def test_query_returns_columns_and_rows(loaded):
    out = query(loaded, "select region, sum(amt) as total from sales "
                        "group by region order by region")
    assert out["columns"] == ["region", "total"]
    assert [r[0] for r in out["rows"]] == ["x", "y"]
    assert out["row_count"] == 2 and out["truncated"] is False


def test_query_limit_and_truncation(loaded):
    out = query(loaded, "select * from sales", limit=2)
    assert out["row_count"] == 2 and out["truncated"] is True


def test_query_coerces_nonjson_scalars(loaded):
    out = query(loaded, "select date '2026-07-08' as d, "
                        "cast(1.5 as decimal(4,2)) as m")
    import json
    json.dumps(out["rows"])          # must not raise
    assert out["rows"][0][0] == "2026-07-08"


def test_query_sql_error_is_reported(loaded):
    with pytest.raises(ToolError) as ei:
        query(loaded, "select * from nonexistent_table")
    assert ei.value.code == "SQL_ERROR" and ei.value.exit_code == 1


def test_query_on_missing_pad_escalates(tmp_path):
    with pytest.raises(ToolError) as ei:
        query("ghost", "select 1")
    assert ei.value.code == "NO_PAD" and ei.value.exit_code == 4


def test_list_and_drop_views(loaded):
    views = {v["name"] for v in list_views(loaded)}
    assert "sales" in views
    drop_view(loaded, "sales")
    assert "sales" not in {v["name"] for v in list_views(loaded)}
    with pytest.raises(ToolError) as ei:
        drop_view(loaded, "sales")
    assert ei.value.code == "NO_VIEW"
