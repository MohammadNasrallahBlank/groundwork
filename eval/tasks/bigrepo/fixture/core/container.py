"""Very small service locator."""
_instances: dict = {}


def provide(key: str, factory):
    if key not in _instances:
        _instances[key] = factory()
    return _instances[key]
