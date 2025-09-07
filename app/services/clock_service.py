"""Service for managing clock updates and database operations."""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from app.utils.db import ClockUpdate
from app.telegram_api.client import TelegramService


class ClockService:
    """Service for handling clock updates."""

    def __init__(self) -> None:
        """Initialize the clock service."""
        self.telegram_service = TelegramService()

    async def fetch_and_store_updates(self, db: Session) -> int:
        """Fetch latest messages from Telegram and store clock updates.

        Args:
            db: Database session

        Returns:
            Number of new updates stored

        Raises:
            Exception: If fetching or storing updates fails
        """
        await self.telegram_service.connect()

        try:
            messages = await self.telegram_service.get_latest_messages(limit=5)
            updates_count = 0

            for message in messages:
                if not message.text:
                    continue

                existing = db.query(ClockUpdate).filter(ClockUpdate.message_id == message.id).first()

                if existing:
                    continue

                time_value = self.telegram_service.extract_time_from_message(message.text)

                image_data = await self.telegram_service.get_message_image_data(message)
                clock_update = ClockUpdate(
                    message_id=message.id,
                    content=message.text,
                    time_value=time_value,
                    image_data=image_data,
                    created_at=message.date or datetime.utcnow(),
                )

                db.add(clock_update)
                updates_count += 1

                logger.info(f"Stored clock update from message {message.id}: {time_value}")

            db.commit()
            logger.info(f"Successfully stored {updates_count} new clock updates")
            return updates_count

        except Exception as e:
            db.rollback()
            logger.error(f"Error fetching and storing updates: {e}")
            return 0
        finally:
            await self.telegram_service.disconnect()

    async def fetch_and_store_since_days(self, db: Session, days: int | None = 30) -> int:
        """Fetch messages for a period and store updates.

        Args:
            db: Database session
            days: Number of days back to fetch. 0 → fetch all messages; default 30.

        Returns:
            Number of new updates stored
        """
        await self.telegram_service.connect()
        try:
            # Determine date boundary
            if days is None:
                days = 30
            if days <= 0:
                min_date = None
            else:
                # Use aware UTC for comparing with Telethon message dates
                min_date = (datetime.utcnow() - timedelta(days=days)).replace(tzinfo=timezone.utc)

            updates_count = 0
            async for message in self.telegram_service.iter_channel_messages(min_date=min_date):
                if not getattr(message, "text", None):
                    continue

                existing = db.query(ClockUpdate).filter(ClockUpdate.message_id == message.id).first()
                if existing:
                    continue

                time_value = self.telegram_service.extract_time_from_message(message.text)
                image_data = await self.telegram_service.get_message_image_data(message)

                clock_update = ClockUpdate(
                    message_id=message.id,
                    content=message.text,
                    time_value=time_value,
                    image_data=image_data,
                    created_at=message.date or datetime.utcnow(),
                )
                db.add(clock_update)
                updates_count += 1

                # Periodic lightweight flush to avoid huge transactions
                if updates_count % 50 == 0:
                    db.flush()

            db.commit()
            logger.info(f"Period fetch stored {updates_count} new updates (days={days})")
            return updates_count
        except Exception as e:
            db.rollback()
            logger.error(f"Error in period fetch: {e}")
            return 0
        finally:
            await self.telegram_service.disconnect()

    def get_latest_update(self, db: Session) -> Optional[ClockUpdate]:
        """Get the most recent clock update.

        Args:
            db: Database session

        Returns:
            Latest clock update or None if no updates exist
        """
        return db.query(ClockUpdate).order_by(ClockUpdate.created_at.desc()).first()

    def get_recent_updates(self, db: Session, limit: int = 10) -> List[ClockUpdate]:
        """Get recent clock updates ordered by creation date.

        Args:
            db: Database session
            limit: Maximum number of updates to retrieve

        Returns:
            List of recent clock updates
        """
        return db.query(ClockUpdate).order_by(ClockUpdate.created_at.desc()).limit(limit).all()

    def get_updates_count(self, db: Session) -> int:
        """Get total count of clock updates in database.

        Args:
            db: Database session

        Returns:
            Total number of clock updates
        """
        return db.query(ClockUpdate).count()
