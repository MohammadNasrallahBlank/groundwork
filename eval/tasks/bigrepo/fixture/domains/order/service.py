"""Business logic for Order."""
from core.config import settings
from core.events import emit
from domains.order.model import Order
from domains.order.repository import OrderRepository


class OrderService:
    def __init__(self) -> None:
        self.repo = OrderRepository()

    def register(self, name: str) -> int:
        obj = Order(id=settings.next_id("order"), name=name)
        new_id = self.repo.create(obj)
        emit("order.created", {"id": new_id})
        return new_id

    def fetch(self, id: int) -> Order:
        return self.repo.get(id)
