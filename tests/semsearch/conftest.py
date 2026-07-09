"""Labelled benchmark fixture: code chunks with concepts, and queries whose
correct answer is a known chunk id. Small but real - enough to separate models."""
import pytest

_CHUNKS = [
    {"id": "retry", "text": "def retry(fn, times=3, delay=1):\n"
     "    for i in range(times):\n        try:\n            return fn()\n"
     "        except Exception:\n            time.sleep(delay)"},
    {"id": "charge", "text": "def charge_card(amount, token):\n"
     "    return stripe.Charge.create(amount=amount, source=token)"},
    {"id": "config", "text": "def load_config(path):\n"
     "    with open(path) as f:\n        return yaml.safe_load(f)"},
    {"id": "auth", "text": "def verify_password(raw, hashed):\n"
     "    return bcrypt.checkpw(raw.encode(), hashed)"},
    {"id": "cache", "text": "class LRUCache:\n    def get(self, key):\n"
     "        self._touch(key)\n        return self._store.get(key)"},
    {"id": "email", "text": "def send_welcome_email(user):\n"
     "    smtp.send(user.email, template='welcome')"},
    {"id": "paginate", "text": "def paginate(query, page, size=20):\n"
     "    return query.offset((page-1)*size).limit(size)"},
    {"id": "sanitize", "text": "def strip_html(text):\n"
     "    return re.sub(r'<[^>]+>', '', text)"},
]
_QUERIES = [
    {"query": "where is the retry logic", "answer": "retry"},
    {"query": "code that touches billing or payment state", "answer": "charge"},
    {"query": "how are passwords checked", "answer": "auth"},
    {"query": "reading settings from a file", "answer": "config"},
    {"query": "sending email to users", "answer": "email"},
    {"query": "in-memory caching", "answer": "cache"},
    {"query": "splitting results into pages", "answer": "paginate"},
    {"query": "removing html tags from a string", "answer": "sanitize"},
]


@pytest.fixture()
def code_chunks():
    return list(_CHUNKS)


@pytest.fixture()
def labelled_queries():
    return list(_QUERIES)
