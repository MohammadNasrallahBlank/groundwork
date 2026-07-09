"""Business logic for Product."""
from core.config import settings
from core.events import emit
from domains.product.model import Product
from domains.product.repository import ProductRepository


class ProductService:
    def __init__(self) -> None:
        self.repo = ProductRepository()

    def register(self, name: str) -> int:
        obj = Product(id=settings.next_id("product"), name=name)
        new_id = self.repo.create(obj)
        emit("product.created", {"id": new_id})
        return new_id

    def fetch(self, id: int) -> Product:
        return self.repo.get(id)
