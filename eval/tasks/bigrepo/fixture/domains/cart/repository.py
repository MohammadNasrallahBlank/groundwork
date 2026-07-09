"""Persistence for Cart."""
from core.exceptions import NotFoundError
from db.base import BaseRepository
from domains.cart.model import Cart


class CartRepository(BaseRepository):
    table = "carts"

    def get(self, id: int) -> Cart:
        row = self._row(id)
        if row is None:
            raise NotFoundError("cart %d not found" % id)
        return Cart(**row)

    def create(self, obj: Cart) -> int:
        obj.validate()
        return self._insert(obj.__dict__)
