"""Persistence for Discount."""
from core.exceptions import NotFoundError
from db.base import BaseRepository
from domains.discount.model import Discount


class DiscountRepository(BaseRepository):
    table = "discounts"

    def get(self, id: int) -> Discount:
        row = self._row(id)
        if row is None:
            raise NotFoundError("discount %d not found" % id)
        return Discount(**row)

    def create(self, obj: Discount) -> int:
        obj.validate()
        return self._insert(obj.__dict__)
