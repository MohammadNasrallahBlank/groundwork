"""Offset pagination helper."""


def paginate(items: list, page: int, size: int = 20) -> list:
    start = (page - 1) * size
    return items[start:start + size]
