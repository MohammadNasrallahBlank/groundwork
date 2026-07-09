"""Address domain model."""
from dataclasses import dataclass

from core.exceptions import ValidationError
from utils.validation import require


@dataclass
class Address:
    id: int
    name: str

    def validate(self) -> None:
        require(self.id > 0, ValidationError("address id must be positive"))
        require(bool(self.name), ValidationError("address name required"))
