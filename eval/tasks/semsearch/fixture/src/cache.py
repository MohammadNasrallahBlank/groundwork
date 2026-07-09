"""A small LRU cache."""
from collections import OrderedDict


class LRUCache:
    def __init__(self, capacity: int = 128):
        self._store: OrderedDict = OrderedDict()
        self.capacity = capacity

    def get(self, key):
        if key not in self._store:
            return None
        self._store.move_to_end(key)
        return self._store[key]

    def put(self, key, value):
        self._store[key] = value
        self._store.move_to_end(key)
        if len(self._store) > self.capacity:
            self._store.popitem(last=False)
