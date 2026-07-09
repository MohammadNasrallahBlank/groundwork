import pytest

from conftest_data import JUNIT
from groundwork.core.runner import ToolError
from groundwork.tools.verify.adapters.junit_ingest import ingest_junit_file


def test_ingest_labels_source_as_junit(tmp_path):
    f = tmp_path / "results.xml"
    f.write_text(JUNIT)
    diags = ingest_junit_file(f)
    assert len(diags) == 1 and diags[0].source == "junit"


def test_ingest_junit_file_raises_tool_error_on_malformed_xml(tmp_path):
    f = tmp_path / "garbage.xml"
    f.write_text("not xml <<<")
    with pytest.raises(ToolError) as exc_info:
        ingest_junit_file(f)
    assert exc_info.value.code == "PARSE_ERROR"


def test_ingest_junit_file_raises_named_error_when_unreadable(tmp_path):
    missing = tmp_path / "does" / "not" / "exist.xml"
    with pytest.raises(ToolError) as exc_info:
        ingest_junit_file(missing)
    assert exc_info.value.code == "JUNIT_UNREADABLE"
