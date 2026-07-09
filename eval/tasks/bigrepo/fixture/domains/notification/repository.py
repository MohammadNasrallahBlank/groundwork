"""Persistence for Notification."""
from core.exceptions import NotFoundError
from db.base import BaseRepository
from domains.notification.model import Notification


class NotificationRepository(BaseRepository):
    table = "notifications"

    def get(self, id: int) -> Notification:
        row = self._row(id)
        if row is None:
            raise NotFoundError("notification %d not found" % id)
        return Notification(**row)

    def create(self, obj: Notification) -> int:
        obj.validate()
        return self._insert(obj.__dict__)
