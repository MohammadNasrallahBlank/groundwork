"""Business logic for Discount."""
from core.config import settings
from core.events import emit
from domains.discount.model import Discount
from domains.discount.repository import DiscountRepository


class DiscountService:
    def __init__(self) -> None:
        self.repo = DiscountRepository()

    def register(self, name: str) -> int:
        obj = Discount(id=settings.next_id("discount"), name=name)
        new_id = self.repo.create(obj)
        emit("discount.created", {"id": new_id})
        return new_id

    def fetch(self, id: int) -> Discount:
        return self.repo.get(id)
