#!/usr/bin/env python3
"""Application entry point."""

import uvicorn

from app.config import config
from app.main import app


def main() -> None:
    """Run the FastAPI application."""
    config.validate()

    uvicorn.run(
        app, host=config.API_HOST, port=config.API_PORT, reload=config.DEBUG, log_level=config.LOG_LEVEL.lower()
    )


if __name__ == "__main__":
    main()
