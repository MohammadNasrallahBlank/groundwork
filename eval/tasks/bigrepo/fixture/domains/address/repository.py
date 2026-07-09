"""Persistence for Address."""
from core.exceptions import NotFoundError
from db.base import BaseRepository
from domains.address.model import Address


class AddressRepository(BaseRepository):
    table = "addresss"

    def get(self, id: int) -> Address:
        row = self._row(id)
        if row is None:
            raise NotFoundError("address %d not found" % id)
        return Address(**row)

    def create(self, obj: Address) -> int:
        obj.validate()
        return self._insert(obj.__dict__)
