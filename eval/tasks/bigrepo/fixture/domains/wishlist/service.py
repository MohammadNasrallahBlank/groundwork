"""Business logic for Wishlist."""
from core.config import settings
from core.events import emit
from domains.wishlist.model import Wishlist
from domains.wishlist.repository import WishlistRepository


class WishlistService:
    def __init__(self) -> None:
        self.repo = WishlistRepository()

    def register(self, name: str) -> int:
        obj = Wishlist(id=settings.next_id("wishlist"), name=name)
        new_id = self.repo.create(obj)
        emit("wishlist.created", {"id": new_id})
        return new_id

    def fetch(self, id: int) -> Wishlist:
        return self.repo.get(id)
