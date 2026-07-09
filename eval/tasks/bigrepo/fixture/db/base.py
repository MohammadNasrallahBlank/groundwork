"""Base repository — the persistence primitive every domain repo extends."""
from core.exceptions import AppError


class BaseRepository:
    table = "base"
    _store: dict = {}

    def _row(self, id: int):
        return self._store.get((self.table, id))

    def _insert(self, data: dict) -> int:
        key = (self.table, data["id"])
        if key in self._store:
            raise AppError("duplicate key")
        self._store[key] = dict(data)
        return data["id"]
