import pymupdf
import pytest

from groundwork.core.runner import ToolError
from groundwork.tools.doc2md.convert import convert


def _pdf(path, pages):
    doc = pymupdf.open()
    for text in pages:
        page = doc.new_page()
        page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def test_converts_pdf_to_markdown(tmp_path):
    p = tmp_path / "d.pdf"
    _pdf(p, ["Alpha section\nhello world", "Beta section\ngoodbye moon"])
    out = convert(p)
    assert out["pages"] == 2
    assert "hello world" in out["markdown"] and "goodbye moon" in out["markdown"]
    assert out["est_tokens"] == out["chars"] // 4


def test_page_slice(tmp_path):
    p = tmp_path / "d.pdf"
    _pdf(p, ["page one text", "page two text", "page three text"])
    out = convert(p, pages="2")
    assert "page two text" in out["markdown"]
    assert "page one text" not in out["markdown"]


def test_grep_keeps_only_matching_blocks(tmp_path):
    p = tmp_path / "d.pdf"
    # separate pages -> separate blocks (joined by a blank line)
    _pdf(p, ["invoice total is 42.50", "unrelated footer text"])
    out = convert(p, grep="total")
    assert "42.50" in out["markdown"]
    assert "footer" not in out["markdown"]


def test_out_of_range_pages_is_usage_error(tmp_path):
    p = tmp_path / "d.pdf"
    _pdf(p, ["only one page"])
    with pytest.raises(ToolError) as ei:
        convert(p, pages="5")
    assert ei.value.code == "USAGE" and ei.value.exit_code == 2


def test_missing_file_is_usage_error(tmp_path):
    with pytest.raises(ToolError) as ei:
        convert(tmp_path / "nope.pdf")
    assert ei.value.exit_code == 2
