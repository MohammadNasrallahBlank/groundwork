"""Shared exception hierarchy + HTTP mapping. The most depended-on module."""


class AppError(Exception):
    status = 500


class ValidationError(AppError):
    status = 400


class NotFoundError(AppError):
    status = 404


class ThrottledError(AppError):
    status = 429           # Too Many Requests


def to_response(err: Exception) -> dict:
    status = getattr(err, "status", 500)
    return {"status": status, "error": str(err)}
