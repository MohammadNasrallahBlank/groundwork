"""Business logic for Cart."""
from core.config import settings
from core.events import emit
from domains.cart.model import Cart
from domains.cart.repository import CartRepository


class CartService:
    def __init__(self) -> None:
        self.repo = CartRepository()

    def register(self, name: str) -> int:
        obj = Cart(id=settings.next_id("cart"), name=name)
        new_id = self.repo.create(obj)
        emit("cart.created", {"id": new_id})
        return new_id

    def fetch(self, id: int) -> Cart:
        return self.repo.get(id)
