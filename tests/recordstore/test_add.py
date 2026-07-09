import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.recordstore.records import (add_decision, add_event,
                                                  add_measurement)


def test_add_decision_round_trip(tmp_path):
    rec = add_decision(tmp_path, subject="API auth", choice="OAuth2",
                       status="accepted", rationale="fewer moving parts",
                       tags="api,security", at="2026-03-01T10:00:00Z")
    assert rec["id"] == 1 and rec["type"] == "decision"
    assert rec["label"] == "API auth" and rec["status"] == "accepted"
    assert rec["ts"] == "2026-03-01T10:00:00Z"
    assert rec["data"]["choice"] == "OAuth2"
    assert rec["data"]["rationale"] == "fewer moving parts"
    assert rec["tags"] == "api,security"


def test_add_measurement_is_numeric(tmp_path):
    rec = add_measurement(tmp_path, metric="p95_latency_ms", value=120.5,
                          unit="ms", at="2026-03-01T10:00:00Z")
    assert rec["type"] == "measurement" and rec["value"] == 120.5
    assert rec["data"]["unit"] == "ms"


def test_add_event_round_trip(tmp_path):
    rec = add_event(tmp_path, name="deploy", outcome="success",
                    at="2026-03-01T10:00:00Z")
    assert rec["type"] == "event" and rec["label"] == "deploy"
    assert rec["data"]["outcome"] == "success"


def test_ids_autoincrement(tmp_path):
    a = add_event(tmp_path, name="a", at="2026-03-01T10:00:00Z")
    b = add_event(tmp_path, name="b", at="2026-03-01T10:00:01Z")
    assert a["id"] == 1 and b["id"] == 2


def test_timestamp_stamped_when_absent(tmp_path):
    rec = add_event(tmp_path, name="now")
    assert rec["ts"].endswith("Z") and "T" in rec["ts"]  # ISO-8601 UTC


def test_bad_status_rejected(tmp_path):
    with pytest.raises(ToolError) as ei:
        add_decision(tmp_path, subject="x", choice="y", status="maybe")
    assert ei.value.code == "USAGE" and ei.value.exit_code == 2


def test_empty_required_field_rejected(tmp_path):
    with pytest.raises(ToolError) as ei:
        add_decision(tmp_path, subject="", choice="y")
    assert ei.value.code == "USAGE"


def test_bad_timestamp_rejected(tmp_path):
    with pytest.raises(ToolError) as ei:
        add_event(tmp_path, name="x", at="not-a-timestamp")
    assert ei.value.code == "USAGE"
