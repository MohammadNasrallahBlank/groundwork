"""Generate a realistic ~66-file Python web-service codebase for the scale A/B.

Deterministic (no randomness). Two things are deliberate:
  * The rate-limiting logic is named 'throttle' / 'TokenBucket' / '429' and NOT
    'rate limit', so a keyword grep on the task's wording misses it and a
    *semantic* search has to understand intent.
  * Imports are structured so a handful of core modules (core.exceptions,
    core.config, db.base, utils.validation) are depended on by nearly every
    domain — giving reference-centrality a real, checkable answer that `ls`
    alone can't produce.

    python eval/tasks/_gen_bigrepo.py eval/tasks/bigrepo/fixture
"""
import sys
from pathlib import Path

DOMAINS = ["user", "product", "order", "cart", "payment", "inventory",
           "shipping", "review", "notification", "discount", "wishlist",
           "address"]


def w(base: Path, rel: str, text: str) -> None:
    p = base / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text.lstrip("\n"), encoding="utf-8", newline="\n")


def _cap(d: str) -> str:
    return d.capitalize()


def model_tmpl(d: str) -> str:
    C = _cap(d)
    return f'''
"""{C} domain model."""
from dataclasses import dataclass

from core.exceptions import ValidationError
from utils.validation import require


@dataclass
class {C}:
    id: int
    name: str

    def validate(self) -> None:
        require(self.id > 0, ValidationError("{d} id must be positive"))
        require(bool(self.name), ValidationError("{d} name required"))
'''


def repo_tmpl(d: str) -> str:
    C = _cap(d)
    return f'''
"""Persistence for {C}."""
from core.exceptions import NotFoundError
from db.base import BaseRepository
from domains.{d}.model import {C}


class {C}Repository(BaseRepository):
    table = "{d}s"

    def get(self, id: int) -> {C}:
        row = self._row(id)
        if row is None:
            raise NotFoundError("{d} %d not found" % id)
        return {C}(**row)

    def create(self, obj: {C}) -> int:
        obj.validate()
        return self._insert(obj.__dict__)
'''


def service_tmpl(d: str) -> str:
    C = _cap(d)
    return f'''
"""Business logic for {C}."""
from core.config import settings
from core.events import emit
from domains.{d}.model import {C}
from domains.{d}.repository import {C}Repository


class {C}Service:
    def __init__(self) -> None:
        self.repo = {C}Repository()

    def register(self, name: str) -> int:
        obj = {C}(id=settings.next_id("{d}"), name=name)
        new_id = self.repo.create(obj)
        emit("{d}.created", {{"id": new_id}})
        return new_id

    def fetch(self, id: int) -> {C}:
        return self.repo.get(id)
'''


def api_tmpl(d: str) -> str:
    C = _cap(d)
    return f'''
"""HTTP routes for {C}."""
from core.exceptions import to_response
from domains.{d}.service import {C}Service
from middleware.throttle import throttle_request

service = {C}Service()


@throttle_request(cost=1)
def get_{d}(request: dict) -> dict:
    try:
        return {{"status": 200, "data": service.fetch(request["id"]).__dict__}}
    except Exception as e:  # noqa: BLE001
        return to_response(e)


@throttle_request(cost=2)
def create_{d}(request: dict) -> dict:
    new_id = service.register(request["name"])
    return {{"status": 201, "id": new_id}}
'''


CONFIG = '''
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
'''

EXCEPTIONS = '''
"""Shared exception hierarchy + HTTP mapping. The most depended-on module."""


class AppError(Exception):
    status = 500


class ValidationError(AppError):
    status = 400


class NotFoundError(AppError):
    status = 404


class ThrottledError(AppError):
    status = 429           # Too Many Requests


def to_response(err: Exception) -> dict:
    status = getattr(err, "status", 500)
    return {"status": status, "error": str(err)}
'''

EVENTS = '''
"""Tiny in-process event bus."""
_subscribers: dict = {}


def on(name: str, fn) -> None:
    _subscribers.setdefault(name, []).append(fn)


def emit(name: str, payload: dict) -> None:
    for fn in _subscribers.get(name, []):
        fn(payload)
'''

CONTAINER = '''
"""Very small service locator."""
_instances: dict = {}


def provide(key: str, factory):
    if key not in _instances:
        _instances[key] = factory()
    return _instances[key]
'''

DB_BASE = '''
"""Base repository — the persistence primitive every domain repo extends."""
from core.exceptions import AppError


class BaseRepository:
    table = "base"
    _store: dict = {}

    def _row(self, id: int):
        return self._store.get((self.table, id))

    def _insert(self, data: dict) -> int:
        key = (self.table, data["id"])
        if key in self._store:
            raise AppError("duplicate key")
        self._store[key] = dict(data)
        return data["id"]
'''

DB_ENGINE = '''
"""Fake DB engine/session handle."""
from core.config import settings


class Engine:
    def __init__(self) -> None:
        self.echo = settings.debug

    def connect(self):
        return self
'''

THROTTLE = '''
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
'''

AUTH = '''
"""Authentication middleware."""
import hashlib

from core.exceptions import AppError


class Unauthorized(AppError):
    status = 401


def verify_bearer(token: str) -> bool:
    return len(token) == 64 and all(c in "0123456789abcdef" for c in token)


def hash_secret(secret: str, salt: str) -> str:
    return hashlib.sha256((salt + secret).encode()).hexdigest()
'''

REQ_LOG = '''
"""Structured request logging middleware."""
from utils.timeutils import now_iso


def log_request(request: dict, status: int) -> None:
    print("%s %s -> %d" % (now_iso(), request.get("path", "?"), status))
'''

CORS = '''
"""CORS headers middleware."""
ALLOWED = ["https://app.example.com"]


def cors_headers(origin: str) -> dict:
    return {"Access-Control-Allow-Origin": origin if origin in ALLOWED else "null"}
'''

ERR_HANDLER = '''
"""Top-level error handler middleware."""
from core.exceptions import to_response


def handle(fn):
    def inner(request: dict):
        try:
            return fn(request)
        except Exception as e:  # noqa: BLE001
            return to_response(e)
    return inner
'''

VALIDATION = '''
"""Validation helpers used by every model."""


def require(cond: bool, err: Exception) -> None:
    if not cond:
        raise err


def is_email(s: str) -> bool:
    return "@" in s and "." in s.split("@")[-1]
'''

PAGINATION = '''
"""Offset pagination helper."""


def paginate(items: list, page: int, size: int = 20) -> list:
    start = (page - 1) * size
    return items[start:start + size]
'''

SERIALIZATION = '''
"""(De)serialization helpers."""
import json


def dumps(obj) -> str:
    return json.dumps(obj, sort_keys=True)


def loads(s: str):
    return json.loads(s)
'''

SECURITY = '''
"""Security helpers."""
import secrets


def token(nbytes: int = 32) -> str:
    return secrets.token_hex(nbytes)
'''

TIMEUTILS = '''
"""Time helpers."""
import datetime


def now_iso() -> str:
    return datetime.datetime.now(datetime.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")
'''


def app_py(domains) -> str:
    imports = "\n".join(f"from domains.{d}.api import get_{d}, create_{d}"
                        for d in domains)
    routes = ",\n    ".join(f'"GET /{d}s": get_{d}, "POST /{d}s": create_{d}'
                            for d in domains)
    return f'''
"""Application wiring: routes -> handlers, through the middleware chain."""
from middleware.error_handler import handle
from middleware.request_logging import log_request
{imports}

ROUTES = {{
    {routes}
}}


def dispatch(request: dict) -> dict:
    handler = ROUTES.get(request.get("route"))
    if handler is None:
        return {{"status": 404, "error": "no route"}}
    response = handle(handler)(request)
    log_request(request, response.get("status", 0))
    return response
'''


def gen(base: Path) -> int:
    w(base, "core/config.py", CONFIG)
    w(base, "core/exceptions.py", EXCEPTIONS)
    w(base, "core/events.py", EVENTS)
    w(base, "core/container.py", CONTAINER)
    w(base, "db/base.py", DB_BASE)
    w(base, "db/engine.py", DB_ENGINE)
    w(base, "middleware/throttle.py", THROTTLE)
    w(base, "middleware/auth.py", AUTH)
    w(base, "middleware/request_logging.py", REQ_LOG)
    w(base, "middleware/cors.py", CORS)
    w(base, "middleware/error_handler.py", ERR_HANDLER)
    w(base, "utils/validation.py", VALIDATION)
    w(base, "utils/pagination.py", PAGINATION)
    w(base, "utils/serialization.py", SERIALIZATION)
    w(base, "utils/security.py", SECURITY)
    w(base, "utils/timeutils.py", TIMEUTILS)
    for d in DOMAINS:
        w(base, f"domains/{d}/__init__.py", "")
        w(base, f"domains/{d}/model.py", model_tmpl(d))
        w(base, f"domains/{d}/repository.py", repo_tmpl(d))
        w(base, f"domains/{d}/service.py", service_tmpl(d))
        w(base, f"domains/{d}/api.py", api_tmpl(d))
    w(base, "app.py", app_py(DOMAINS))
    w(base, "README.md", "# shopfront\n\nA small modular commerce API service.\n")
    for pkg in ("core", "db", "middleware", "utils", "domains"):
        w(base, f"{pkg}/__init__.py", "")
    return sum(1 for _ in base.rglob("*.py"))


if __name__ == "__main__":
    target = Path(sys.argv[1] if len(sys.argv) > 1 else "eval/tasks/bigrepo/fixture")
    n = gen(target)
    print(f"generated {n} .py files under {target}")
