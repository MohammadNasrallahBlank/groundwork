"""Persistence for Order."""
from core.exceptions import NotFoundError
from db.base import BaseRepository
from domains.order.model import Order


class OrderRepository(BaseRepository):
    table = "orders"

    def get(self, id: int) -> Order:
        row = self._row(id)
        if row is None:
            raise NotFoundError("order %d not found" % id)
        return Order(**row)

    def create(self, obj: Order) -> int:
        obj.validate()
        return self._insert(obj.__dict__)
