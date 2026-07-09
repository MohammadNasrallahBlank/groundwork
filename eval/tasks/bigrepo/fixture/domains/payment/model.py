"""Payment domain model."""
from dataclasses import dataclass

from core.exceptions import ValidationError
from utils.validation import require


@dataclass
class Payment:
    id: int
    name: str

    def validate(self) -> None:
        require(self.id > 0, ValidationError("payment id must be positive"))
        require(bool(self.name), ValidationError("payment name required"))
