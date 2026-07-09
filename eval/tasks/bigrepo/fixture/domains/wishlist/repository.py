"""Persistence for Wishlist."""
from core.exceptions import NotFoundError
from db.base import BaseRepository
from domains.wishlist.model import Wishlist


class WishlistRepository(BaseRepository):
    table = "wishlists"

    def get(self, id: int) -> Wishlist:
        row = self._row(id)
        if row is None:
            raise NotFoundError("wishlist %d not found" % id)
        return Wishlist(**row)

    def create(self, obj: Wishlist) -> int:
        obj.validate()
        return self._insert(obj.__dict__)
