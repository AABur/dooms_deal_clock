"""Logging configuration module using loguru."""

import sys
from pathlib import Path
from typing import Any

from loguru import logger

from app.config import config


def setup_logging() -> None:
    """Configure loguru logging for the application."""
    # Remove default handler
    logger.remove()

    # Ensure logs directory exists
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)

    # Console handler with colors and formatting
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>",
        level=config.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # File handler for all logs
    logger.add(
        logs_dir / "app.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
    )

    # Separate file for errors only
    logger.add(
        logs_dir / "errors.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level="ERROR",
        rotation="5 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
    )

    # JSON format for structured logging (if needed for monitoring)
    logger.add(
        logs_dir / "structured.log",
        format="{message}",
        level="INFO",
        serialize=True,
        rotation="20 MB",
        retention="7 days",
        compression="zip",
    )

    logger.info(f"Logging configured with level: {config.LOG_LEVEL}")


def get_logger(name: str) -> Any:
    """Get a logger instance with the specified name.

    Args:
        name: Logger name, typically __name__ of the calling module.

    Returns:
        Configured logger instance.
    """
    return logger.bind(name=name)
