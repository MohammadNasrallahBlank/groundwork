"""Top-level error handler middleware."""
from core.exceptions import to_response


def handle(fn):
    def inner(request: dict):
        try:
            return fn(request)
        except Exception as e:  # noqa: BLE001
            return to_response(e)
    return inner
