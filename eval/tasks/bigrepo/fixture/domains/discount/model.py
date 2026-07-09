"""Discount domain model."""
from dataclasses import dataclass

from core.exceptions import ValidationError
from utils.validation import require


@dataclass
class Discount:
    id: int
    name: str

    def validate(self) -> None:
        require(self.id > 0, ValidationError("discount id must be positive"))
        require(bool(self.name), ValidationError("discount name required"))
