"""Request throttling. THIS is where the service stops a single client from
overwhelming the API with too many requests in a short window — a classic
token-bucket limiter. Exceeding the bucket raises ThrottledError (HTTP 429).

Named 'throttle' rather than 'rate limit' on purpose."""
import time
from functools import wraps

from core.config import settings
from core.exceptions import ThrottledError

_buckets: dict = {}


class TokenBucket:
    """Refills `refill` tokens/sec up to `capacity`; each call spends `cost`."""

    def __init__(self, capacity: int, refill: float) -> None:
        self.capacity = capacity
        self.refill = refill
        self.tokens = float(capacity)
        self.stamp = time.monotonic()

    def take(self, cost: int) -> bool:
        now = time.monotonic()
        self.tokens = min(self.capacity,
                          self.tokens + (now - self.stamp) * self.refill)
        self.stamp = now
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False


def throttle_request(cost: int = 1):
    """Decorator: reject a caller who has spent their token budget with a 429."""
    def deco(fn):
        @wraps(fn)
        def inner(request: dict):
            client = request.get("client_ip", "anon")
            bucket = _buckets.setdefault(client, TokenBucket(
                settings.throttle_capacity, settings.throttle_refill_per_sec))
            if not bucket.take(cost):
                raise ThrottledError("too many requests from %s" % client)
            return fn(request)
        return inner
    return deco
