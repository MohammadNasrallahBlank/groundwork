from groundwork.tools.datalens.profile import profile_dataset


def test_profile_csv_reports_schema_and_stats(csv_file):
    out = profile_dataset(csv_file)
    assert out["rows"] == 4 and out["columns"] == 3
    assert any(c["name"] == "score" for c in out["schema"])
    score = [c for c in out["column_stats"] if c["name"] == "score"][0]
    assert score["nulls"] == 1
    assert score["min"] == 10.5 and score["max"] == 20.0
    assert score["mean"] is not None and score["q50"] is not None


def test_balance_attached_for_low_cardinality(csv_file):
    out = profile_dataset(csv_file)
    assert "cat" in out["balance"]
    counts = dict(out["balance"]["cat"])
    assert counts["x"] == 3 and counts["y"] == 1


def test_outliers_flagged_for_numeric(tmp_path):
    p = tmp_path / "o.csv"
    rows = "\n".join(str(v) for v in list(range(1, 20)) + [9999])
    p.write_text("v\n" + rows + "\n", encoding="utf-8")
    out = profile_dataset(p)
    assert out["outliers"]["v"]["count"] >= 1
    assert out["outliers"]["v"]["high"] >= 1


def test_string_column_omits_numeric_fields(csv_file):
    out = profile_dataset(csv_file)
    cat = [c for c in out["column_stats"] if c["name"] == "cat"][0]
    assert "mean" not in cat and "distinct" in cat


def test_distinct_count_is_exact_not_approximate(tmp_path):
    # 30 unique ids + a 3-value category. SUMMARIZE's approx_unique
    # (HyperLogLog) mis-counts high-cardinality columns (e.g. 31 for 30);
    # the profiler must report EXACT distinct counts.
    p = tmp_path / "d.csv"
    lines = ["id,grp"] + [f"{i},{['a', 'b', 'c'][i % 3]}" for i in range(30)]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    out = profile_dataset(p)
    stats = {c["name"]: c for c in out["column_stats"]}
    assert stats["id"]["distinct"] == 30, stats["id"]["distinct"]
    assert stats["grp"]["distinct"] == 3, stats["grp"]["distinct"]


def test_empty_file_is_valid_report(tmp_path):
    p = tmp_path / "e.csv"
    p.write_text("a,b\n", encoding="utf-8")
    out = profile_dataset(p)
    assert out["rows"] == 0 and out["columns"] == 2


def test_sqlite_needs_table_then_profiles(sqlite_file):
    out = profile_dataset(sqlite_file, table="people")
    assert out["rows"] == 3
    age = [c for c in out["column_stats"] if c["name"] == "age"][0]
    assert age["min"] == 30 and age["max"] == 50
