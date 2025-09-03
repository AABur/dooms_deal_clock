"""Print quick authorization status for the Telegram client session.

Usage (Docker):
  docker compose run --rm dooms-deal-clock python scripts/telegram_status.py
"""

import asyncio

from loguru import logger

from app.telegram_api.client import TelegramService


async def main() -> None:
    svc = TelegramService()
    client = svc._get_client()  # internal, but fine for a diagnostic utility
    try:
        await client.connect()
        me = await client.get_me()
        if me:
            logger.info(f"Authorized as: {getattr(me, 'username', None) or me.id}")
        else:
            logger.info("Not authorized (no user returned)")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())

