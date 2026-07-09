"""Business logic for User."""
from core.config import settings
from core.events import emit
from domains.user.model import User
from domains.user.repository import UserRepository


class UserService:
    def __init__(self) -> None:
        self.repo = UserRepository()

    def register(self, name: str) -> int:
        obj = User(id=settings.next_id("user"), name=name)
        new_id = self.repo.create(obj)
        emit("user.created", {"id": new_id})
        return new_id

    def fetch(self, id: int) -> User:
        return self.repo.get(id)
