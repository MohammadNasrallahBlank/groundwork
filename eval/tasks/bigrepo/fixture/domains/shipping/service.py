"""Business logic for Shipping."""
from core.config import settings
from core.events import emit
from domains.shipping.model import Shipping
from domains.shipping.repository import ShippingRepository


class ShippingService:
    def __init__(self) -> None:
        self.repo = ShippingRepository()

    def register(self, name: str) -> int:
        obj = Shipping(id=settings.next_id("shipping"), name=name)
        new_id = self.repo.create(obj)
        emit("shipping.created", {"id": new_id})
        return new_id

    def fetch(self, id: int) -> Shipping:
        return self.repo.get(id)
