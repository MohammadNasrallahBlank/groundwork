"""Persistence for Payment."""
from core.exceptions import NotFoundError
from db.base import BaseRepository
from domains.payment.model import Payment


class PaymentRepository(BaseRepository):
    table = "payments"

    def get(self, id: int) -> Payment:
        row = self._row(id)
        if row is None:
            raise NotFoundError("payment %d not found" % id)
        return Payment(**row)

    def create(self, obj: Payment) -> int:
        obj.validate()
        return self._insert(obj.__dict__)
