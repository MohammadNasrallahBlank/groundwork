"""ArgumentParser variant whose errors carry the real message into the envelope."""
import argparse

from groundwork.core.runner import ToolError


class UsageParser(argparse.ArgumentParser):
    """error() raises ToolError("USAGE", <real message>) instead of exiting."""

    def error(self, message: str) -> None:
        raise ToolError("USAGE", message, exit_code=2)
