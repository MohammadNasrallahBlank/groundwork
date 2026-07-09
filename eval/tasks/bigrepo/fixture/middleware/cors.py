"""CORS headers middleware."""
ALLOWED = ["https://app.example.com"]


def cors_headers(origin: str) -> dict:
    return {"Access-Control-Allow-Origin": origin if origin in ALLOWED else "null"}
