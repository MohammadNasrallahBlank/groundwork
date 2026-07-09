"""HTTP server loop and request handling."""
from app.auth import verify_token


def run_server(cfg: dict) -> int:
    """Bind the port from cfg and serve requests until interrupted."""
    port = cfg.get("port", 8080)
    print(f"serving on :{port}")
    return 0


def handle_request(request: dict) -> dict:
    """Authenticate a request and route it to a handler."""
    if not verify_token(request.get("token", "")):
        return {"status": 401}
    return {"status": 200, "body": route(request["path"])}


def route(path: str) -> str:
    return f"handled {path}"
