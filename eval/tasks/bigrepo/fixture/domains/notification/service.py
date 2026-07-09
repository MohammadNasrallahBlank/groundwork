"""Business logic for Notification."""
from core.config import settings
from core.events import emit
from domains.notification.model import Notification
from domains.notification.repository import NotificationRepository


class NotificationService:
    def __init__(self) -> None:
        self.repo = NotificationRepository()

    def register(self, name: str) -> int:
        obj = Notification(id=settings.next_id("notification"), name=name)
        new_id = self.repo.create(obj)
        emit("notification.created", {"id": new_id})
        return new_id

    def fetch(self, id: int) -> Notification:
        return self.repo.get(id)
