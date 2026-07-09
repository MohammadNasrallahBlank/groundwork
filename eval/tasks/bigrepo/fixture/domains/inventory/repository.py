"""Persistence for Inventory."""
from core.exceptions import NotFoundError
from db.base import BaseRepository
from domains.inventory.model import Inventory


class InventoryRepository(BaseRepository):
    table = "inventorys"

    def get(self, id: int) -> Inventory:
        row = self._row(id)
        if row is None:
            raise NotFoundError("inventory %d not found" % id)
        return Inventory(**row)

    def create(self, obj: Inventory) -> int:
        obj.validate()
        return self._insert(obj.__dict__)
