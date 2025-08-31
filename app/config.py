"""Application configuration module."""

import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration class."""

    # Telegram API configuration
    TELEGRAM_API_ID: Optional[str] = os.getenv("TELEGRAM_API_ID")
    TELEGRAM_API_HASH: Optional[str] = os.getenv("TELEGRAM_API_HASH")
    TELEGRAM_PHONE: Optional[str] = os.getenv("TELEGRAM_PHONE")
    TELEGRAM_CHANNEL_USERNAME: str = os.getenv("TELEGRAM_CHANNEL_USERNAME", "dooms_deal_clock")

    # API configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    DEBUG: bool = os.getenv("DEBUG", "False").lower() == "true"

    # Database configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./clock_data.db")

    # Update configuration
    UPDATE_INTERVAL_SECONDS: int = int(os.getenv("UPDATE_INTERVAL_SECONDS", "300"))

    # Logging configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration values."""
        required_fields = ["TELEGRAM_API_ID", "TELEGRAM_API_HASH", "TELEGRAM_PHONE"]
        missing_fields = [field for field in required_fields if not getattr(cls, field)]

        if missing_fields:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_fields)}")


# Create global config instance
config = Config()
