"""Business logic for Payment."""
from core.config import settings
from core.events import emit
from domains.payment.model import Payment
from domains.payment.repository import PaymentRepository


class PaymentService:
    def __init__(self) -> None:
        self.repo = PaymentRepository()

    def register(self, name: str) -> int:
        obj = Payment(id=settings.next_id("payment"), name=name)
        new_id = self.repo.create(obj)
        emit("payment.created", {"id": new_id})
        return new_id

    def fetch(self, id: int) -> Payment:
        return self.repo.get(id)
