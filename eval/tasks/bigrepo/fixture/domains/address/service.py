"""Business logic for Address."""
from core.config import settings
from core.events import emit
from domains.address.model import Address
from domains.address.repository import AddressRepository


class AddressService:
    def __init__(self) -> None:
        self.repo = AddressRepository()

    def register(self, name: str) -> int:
        obj = Address(id=settings.next_id("address"), name=name)
        new_id = self.repo.create(obj)
        emit("address.created", {"id": new_id})
        return new_id

    def fetch(self, id: int) -> Address:
        return self.repo.get(id)
