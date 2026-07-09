"""Tiny in-process event bus."""
_subscribers: dict = {}


def on(name: str, fn) -> None:
    _subscribers.setdefault(name, []).append(fn)


def emit(name: str, payload: dict) -> None:
    for fn in _subscribers.get(name, []):
        fn(payload)
