"""Persistence for Review."""
from core.exceptions import NotFoundError
from db.base import BaseRepository
from domains.review.model import Review


class ReviewRepository(BaseRepository):
    table = "reviews"

    def get(self, id: int) -> Review:
        row = self._row(id)
        if row is None:
            raise NotFoundError("review %d not found" % id)
        return Review(**row)

    def create(self, obj: Review) -> int:
        obj.validate()
        return self._insert(obj.__dict__)
