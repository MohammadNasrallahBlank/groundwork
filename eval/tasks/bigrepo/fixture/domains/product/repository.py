"""Persistence for Product."""
from core.exceptions import NotFoundError
from db.base import BaseRepository
from domains.product.model import Product


class ProductRepository(BaseRepository):
    table = "products"

    def get(self, id: int) -> Product:
        row = self._row(id)
        if row is None:
            raise NotFoundError("product %d not found" % id)
        return Product(**row)

    def create(self, obj: Product) -> int:
        obj.validate()
        return self._insert(obj.__dict__)
