import pytest

from groundwork.tools.recordstore.records import (add_decision, add_event,
                                                  add_measurement, query,
                                                  timeline)


@pytest.fixture()
def seeded(tmp_path):
    add_decision(tmp_path, subject="API auth", choice="OAuth2",
                 status="accepted", tags="api", at="2026-03-01T10:00:00Z")
    add_decision(tmp_path, subject="API paging", choice="cursor",
                 status="open", tags="api", at="2026-04-01T10:00:00Z")
    add_decision(tmp_path, subject="DB engine", choice="Postgres",
                 status="accepted", tags="db", at="2026-05-01T10:00:00Z")
    add_measurement(tmp_path, metric="p95_ms", value=120, at="2026-03-02T10:00:00Z")
    add_measurement(tmp_path, metric="p95_ms", value=90, at="2026-05-02T10:00:00Z")
    add_event(tmp_path, name="deploy", outcome="success",
              at="2026-05-03T10:00:00Z")
    return tmp_path


def test_query_by_type(seeded):
    decisions = query(seeded, type="decision")
    assert len(decisions) == 3 and all(r["type"] == "decision" for r in decisions)


def test_query_by_status_and_tag(seeded):
    out = query(seeded, type="decision", status="accepted", tag="api")
    assert len(out) == 1 and out[0]["label"] == "API auth"


def test_query_label_like(seeded):
    out = query(seeded, label_like="API%")
    assert {r["label"] for r in out} == {"API auth", "API paging"}


def test_query_date_range(seeded):
    out = query(seeded, type="decision", since="2026-04-01T00:00:00Z")
    assert {r["label"] for r in out} == {"API paging", "DB engine"}


def test_query_newest_first_and_parsed_data(seeded):
    out = query(seeded, type="decision")
    assert out[0]["ts"] >= out[-1]["ts"]
    assert isinstance(out[0]["data"], dict) and "choice" in out[0]["data"]


def test_measurement_timeseries(seeded):
    out = query(seeded, type="measurement", label_like="p95_ms")
    assert [r["value"] for r in sorted(out, key=lambda r: r["ts"])] == [120.0, 90.0]


def test_timeline_chronological_with_summaries(seeded):
    tl = timeline(seeded)
    assert tl[0]["ts"] <= tl[-1]["ts"]
    dec = [t for t in tl if t["type"] == "decision"][0]
    assert "OAuth2" in dec["summary"] and "accepted" in dec["summary"]
    meas = [t for t in tl if t["type"] == "measurement"][0]
    assert "120" in meas["summary"]


def test_empty_store_queries_are_empty(tmp_path):
    assert query(tmp_path) == [] and timeline(tmp_path) == []
