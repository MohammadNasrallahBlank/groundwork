"""Business logic for Inventory."""
from core.config import settings
from core.events import emit
from domains.inventory.model import Inventory
from domains.inventory.repository import InventoryRepository


class InventoryService:
    def __init__(self) -> None:
        self.repo = InventoryRepository()

    def register(self, name: str) -> int:
        obj = Inventory(id=settings.next_id("inventory"), name=name)
        new_id = self.repo.create(obj)
        emit("inventory.created", {"id": new_id})
        return new_id

    def fetch(self, id: int) -> Inventory:
        return self.repo.get(id)
