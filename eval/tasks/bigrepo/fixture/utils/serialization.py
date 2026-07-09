"""(De)serialization helpers."""
import json


def dumps(obj) -> str:
    return json.dumps(obj, sort_keys=True)


def loads(s: str):
    return json.loads(s)
