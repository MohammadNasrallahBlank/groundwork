"""Network helpers."""
import time


def retry_with_backoff(fn, attempts: int = 3, base_delay: float = 0.5):
    """Call fn(), retrying on exception with exponential backoff."""
    for i in range(attempts):
        try:
            return fn()
        except Exception:
            if i == attempts - 1:
                raise
            time.sleep(base_delay * (2 ** i))


def fetch(url: str) -> bytes:
    return b"..."
