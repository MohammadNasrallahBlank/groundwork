"""Entry point for the widget service."""
from app.server import run_server
from app.config import load_config


def main() -> int:
    cfg = load_config("service.toml")
    return run_server(cfg)


if __name__ == "__main__":
    raise SystemExit(main())
