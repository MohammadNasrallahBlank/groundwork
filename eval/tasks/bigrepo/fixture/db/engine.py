"""Fake DB engine/session handle."""
from core.config import settings


class Engine:
    def __init__(self) -> None:
        self.echo = settings.debug

    def connect(self):
        return self
