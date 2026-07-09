"""Core engine."""


class Engine:
    """Engine that runs things."""

    max_rpm: int = 9000

    def start(self, speed: int = 1) -> bool:
        """Start the engine."""
        return True

    def _tune(self) -> None:
        return None


def start(engine: Engine, *, retries: int = 3) -> bool:
    """Start an engine with retries."""
    return True
