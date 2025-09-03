"""Background task service for periodic updates."""

import asyncio

from loguru import logger

from app.config import config
from app.utils.db import SessionLocal
from app.services.clock_service import ClockService


class BackgroundTaskService:
    """Service for running background tasks."""

    def __init__(self) -> None:
        """Initialize the background task service."""
        self.clock_service = ClockService()
        self.is_running: bool = False
        self.task: asyncio.Task[None] | None = None

    async def start_periodic_updates(self) -> None:
        """Start periodic updates from Telegram channel."""
        if self.is_running:
            logger.warning("Periodic updates already running")
            return

        self.is_running = True
        logger.info(f"Starting periodic updates every {config.UPDATE_INTERVAL_SECONDS} seconds")

        while self.is_running:
            try:
                db = SessionLocal()
                try:
                    updates_count = await self.clock_service.fetch_and_store_updates(db)
                    if updates_count > 0:
                        logger.info(f"Background task: fetched {updates_count} new updates")
                    else:
                        logger.debug("Background task: no new updates found")
                finally:
                    db.close()

                # Wait for the next update cycle
                await asyncio.sleep(config.UPDATE_INTERVAL_SECONDS)

            except Exception as e:
                logger.error(f"Error in background update task: {e}")
                # Wait a minute before retrying on error
                await asyncio.sleep(60)

    def start(self) -> None:
        """Start the background task."""
        if self.task is None or self.task.done():
            self.task = asyncio.create_task(self.start_periodic_updates())
            logger.info("Background task started")
        else:
            logger.warning("Background task already running")

    def stop(self) -> None:
        """Stop the background task."""
        self.is_running = False
        if self.task and not self.task.done():
            self.task.cancel()
            logger.info("Background task stopped")

    def is_task_running(self) -> bool:
        """Check if background task is running."""
        return bool(self.is_running and self.task and not self.task.done())


# Global background task service instance
background_service = BackgroundTaskService()
