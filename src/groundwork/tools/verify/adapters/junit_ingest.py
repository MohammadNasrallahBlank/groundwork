"""Ingest any JUnit XML file: gradle, go-junit-report, cargo-nextest, etc."""
import dataclasses
from pathlib import Path

from groundwork.core.runner import ToolError
from groundwork.tools.verify.adapters.pytest_adapter import parse_junit
from groundwork.tools.verify.models import Diagnostic


def ingest_junit_file(path: Path) -> list[Diagnostic]:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError as e:
        # Missing/unreadable --junit input must surface as a named error, not
        # bubble up as a generic INTERNAL crash from run_tool's catch-all.
        raise ToolError("JUNIT_UNREADABLE", f"cannot read junit xml: {path.as_posix()}",
                         detail=str(e)) from e
    return [dataclasses.replace(d, source="junit") for d in parse_junit(text)]
