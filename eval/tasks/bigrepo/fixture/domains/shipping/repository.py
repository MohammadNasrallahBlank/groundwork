"""Persistence for Shipping."""
from core.exceptions import NotFoundError
from db.base import BaseRepository
from domains.shipping.model import Shipping


class ShippingRepository(BaseRepository):
    table = "shippings"

    def get(self, id: int) -> Shipping:
        row = self._row(id)
        if row is None:
            raise NotFoundError("shipping %d not found" % id)
        return Shipping(**row)

    def create(self, obj: Shipping) -> int:
        obj.validate()
        return self._insert(obj.__dict__)
