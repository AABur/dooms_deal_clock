"""Telegram Client API service for fetching channel updates."""

import asyncio
import re
from typing import List, Optional

from telethon import TelegramClient
from telethon.tl.types import Message
from loguru import logger

from app.config import config


class TelegramService:
    """Service for interacting with Telegram API."""
    
    def __init__(self):
        """Initialize Telegram client."""
        self.client = None
        self.channel_username = config.TELEGRAM_CHANNEL_USERNAME
        
    def _get_client(self):
        """Get or create Telegram client."""
        if self.client is None:
            self.client = TelegramClient(
                'dooms_deal_session',
                config.TELEGRAM_API_ID,
                config.TELEGRAM_API_HASH
            )
        return self.client
    
    async def connect(self) -> None:
        """Connect to Telegram and authenticate."""
        client = self._get_client()
        await client.start(phone=config.TELEGRAM_PHONE)
        logger.info("Connected to Telegram API")
    
    async def disconnect(self) -> None:
        """Disconnect from Telegram."""
        if self.client:
            await self.client.disconnect()
            logger.info("Disconnected from Telegram API")
    
    async def get_latest_messages(self, limit: int = 10) -> List[Message]:
        """Get latest messages from the channel."""
        try:
            client = self._get_client()
            messages = []
            async for message in client.iter_messages(
                self.channel_username, 
                limit=limit
            ):
                messages.append(message)
            
            logger.info(f"Retrieved {len(messages)} messages from {self.channel_username}")
            return messages
            
        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return []
    
    async def get_channel_info(self) -> Optional[dict]:
        """Get information about the channel."""
        try:
            client = self._get_client()
            entity = await client.get_entity(self.channel_username)
            return {
                'id': entity.id,
                'title': entity.title,
                'username': entity.username,
                'participants_count': getattr(entity, 'participants_count', None)
            }
        except Exception as e:
            logger.error(f"Error getting channel info: {e}")
            return None
    
    def extract_time_from_message(self, message_text: str) -> Optional[str]:
        """Extract time value from message text (e.g., '23:58' or '11:45')."""
        time_patterns = [
            r'(\d{1,2}:\d{2})',  # Match HH:MM or H:MM format
            r'(\d{1,2}\.\d{2})',  # Match HH.MM format
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, message_text)
            if match:
                return match.group(1)
        
        return None