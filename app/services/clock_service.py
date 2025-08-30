"""Service for managing clock updates and database operations."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session
from loguru import logger

from app.models import ClockUpdate, get_db
from app.telegram_api.client import TelegramService


class ClockService:
    """Service for handling clock updates."""
    
    def __init__(self):
        """Initialize the clock service."""
        self.telegram_service = TelegramService()
    
    async def fetch_and_store_updates(self, db: Session) -> int:
        """Fetch latest messages from Telegram and store clock updates."""
        await self.telegram_service.connect()
        
        try:
            messages = await self.telegram_service.get_latest_messages(limit=5)
            updates_count = 0
            
            for message in messages:
                if not message.text:
                    continue
                
                # Check if message already exists
                existing = db.query(ClockUpdate).filter(
                    ClockUpdate.message_id == message.id
                ).first()
                
                if existing:
                    continue
                
                # Extract time from message
                time_value = self.telegram_service.extract_time_from_message(message.text)
                
                # Store the update
                clock_update = ClockUpdate(
                    message_id=message.id,
                    content=message.text,
                    time_value=time_value,
                    created_at=message.date or datetime.utcnow()
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
    
    def get_latest_update(self, db: Session) -> Optional[ClockUpdate]:
        """Get the most recent clock update."""
        return db.query(ClockUpdate).order_by(ClockUpdate.created_at.desc()).first()
    
    def get_recent_updates(self, db: Session, limit: int = 10) -> List[ClockUpdate]:
        """Get recent clock updates."""
        return db.query(ClockUpdate).order_by(
            ClockUpdate.created_at.desc()
        ).limit(limit).all()
    
    def get_updates_count(self, db: Session) -> int:
        """Get total count of clock updates."""
        return db.query(ClockUpdate).count()