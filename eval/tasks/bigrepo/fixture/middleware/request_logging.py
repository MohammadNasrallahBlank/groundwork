"""Structured request logging middleware."""
from utils.timeutils import now_iso


def log_request(request: dict, status: int) -> None:
    print("%s %s -> %d" % (now_iso(), request.get("path", "?"), status))
