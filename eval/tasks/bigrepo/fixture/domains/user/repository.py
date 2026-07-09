"""Persistence for User."""
from core.exceptions import NotFoundError
from db.base import BaseRepository
from domains.user.model import User


class UserRepository(BaseRepository):
    table = "users"

    def get(self, id: int) -> User:
        row = self._row(id)
        if row is None:
            raise NotFoundError("user %d not found" % id)
        return User(**row)

    def create(self, obj: User) -> int:
        obj.validate()
        return self._insert(obj.__dict__)
