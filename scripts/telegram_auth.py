"""Interactive Telegram authorization inside Docker or local env.

Usage (Docker):
  docker compose run --rm dooms-deal-clock python scripts/telegram_auth.py

Requirements:
  - .env with TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE
  - Optional: TELEGRAM_2FA_PASSWORD (to skip manual password entry on 2FA)

This script will prompt for the SMS/Telegram code in the attached TTY and
create/update the session file at data/dooms_deal_session.session.
"""

import asyncio

from getpass import getpass
from loguru import logger

from app.config import config
from app.telegram_api.client import TelegramService


async def main() -> None:
    svc = TelegramService()
    # Ask for 2FA password interactively if not provided via env
    pw = config.TELEGRAM_2FA_PASSWORD or getpass(
        "Введите пароль 2FA (если включен, иначе оставьте пустым): "
    )
    await svc.connect(password=pw)
    logger.info("Authorization completed. Session saved under data/dooms_deal_session.session")
    await svc.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
