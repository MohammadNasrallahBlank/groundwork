"""Central configuration and id sequencing. Imported almost everywhere."""


class _Settings:
    def __init__(self) -> None:
        self.debug = False
        self.throttle_capacity = 60
        self.throttle_refill_per_sec = 1.0
        self._counters: dict = {}

    def next_id(self, kind: str) -> int:
        self._counters[kind] = self._counters.get(kind, 0) + 1
        return self._counters[kind]


settings = _Settings()
