"""Business logic for Review."""
from core.config import settings
from core.events import emit
from domains.review.model import Review
from domains.review.repository import ReviewRepository


class ReviewService:
    def __init__(self) -> None:
        self.repo = ReviewRepository()

    def register(self, name: str) -> int:
        obj = Review(id=settings.next_id("review"), name=name)
        new_id = self.repo.create(obj)
        emit("review.created", {"id": new_id})
        return new_id

    def fetch(self, id: int) -> Review:
        return self.repo.get(id)
