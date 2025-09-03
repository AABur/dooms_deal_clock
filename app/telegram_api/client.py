"""Telegram Client API service for fetching channel updates."""

import base64
import io
import os
import re
from typing import Any, Dict, List, Optional

from loguru import logger
from telethon import TelegramClient
from telethon.tl.types import Message, MessageMediaPhoto

from app.config import config


class TelegramService:
    """Service for interacting with Telegram API."""

    def __init__(self) -> None:
        """Initialize Telegram client."""
        self.client = None
        self.channel_username = config.TELEGRAM_CHANNEL_USERNAME

    def _get_client(self) -> TelegramClient:
        """Get or create Telegram client."""
        if self.client is None:
            # Telethon expects api_id as an integer. Cast safely for real runs,
            # but keep tests tolerant if a non-numeric stub is injected.
            api_id_cfg = config.TELEGRAM_API_ID
            api_id: Optional[int | str]
            try:
                api_id = int(api_id_cfg) if api_id_cfg is not None else None
            except (TypeError, ValueError):
                # Fall back to original (useful in tests where a stub like "id" is set)
                api_id = api_id_cfg  # type: ignore[assignment]
            # Store session inside data/ to persist in Docker volume
            session_path = os.path.join("data", "dooms_deal_session")
            self.client = TelegramClient(session_path, api_id, config.TELEGRAM_API_HASH)
        return self.client

    async def connect(self, password: Optional[str] = None) -> None:
        """Connect to Telegram and authenticate.

        Args:
            password: Optional 2FA password. If not provided, uses value from config.
        """
        client = self._get_client()
        pw = password if password not in (None, "") else config.TELEGRAM_2FA_PASSWORD
        await client.start(phone=config.TELEGRAM_PHONE, password=pw)
        # Tighten permissions on session file if present
        try:
            sess_file = os.path.join("data", "dooms_deal_session.session")
            if os.path.exists(sess_file):
                os.chmod(sess_file, 0o600)
        except Exception as _perm_err:  # pragma: no cover - best effort
            logger.warning(f"Could not set permissions on session file: {_perm_err}")
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
            async for message in client.iter_messages(self.channel_username, limit=limit):
                messages.append(message)

            logger.info(f"Retrieved {len(messages)} messages from {self.channel_username}")
            return messages

        except Exception as e:
            logger.error(f"Error fetching messages: {e}")
            return []

    async def get_channel_info(self) -> Optional[Dict[str, Any]]:
        """Get information about the channel."""
        try:
            client = self._get_client()
            entity = await client.get_entity(self.channel_username)
            return {
                "id": entity.id,
                "title": entity.title,
                "username": entity.username,
                "participants_count": getattr(entity, "participants_count", None),
            }
        except Exception as e:
            logger.error(f"Error getting channel info: {e}")
            return None

    def extract_time_from_message(self, message_text: str) -> Optional[str]:
        """Extract time value from message text (e.g., '23:58:05' or '23:58')."""
        time_patterns = [
            r"(\d{1,2}:\d{2}:\d{2})",  # Match HH:MM:SS format first
            r"(\d{1,2}:\d{2})",  # Match HH:MM or H:MM format
            r"(\d{1,2}\.\d{2})",  # Match HH.MM format
        ]

        for pattern in time_patterns:
            match = re.search(pattern, message_text)
            if match:
                logger.info(f"Extracted time '{match.group(1)}' from message")
                return match.group(1)

        logger.warning(f"No time pattern found in message: {message_text[:100]}...")
        return None

    async def get_message_image_data(self, message: Message) -> Optional[str]:
        """Get image data from message as base64 string."""
        if not message.media or not isinstance(message.media, MessageMediaPhoto):
            return None

        try:
            client = self._get_client()
            # Download photo to bytes buffer
            photo_bytes = io.BytesIO()
            await client.download_media(message, file=photo_bytes)
            photo_bytes.seek(0)

            # Convert to base64
            image_data = base64.b64encode(photo_bytes.read()).decode("utf-8")
            logger.info(f"Downloaded image data for message {message.id}")
            return image_data

        except Exception as e:
            logger.error(f"Error downloading image from message {message.id}: {e}")
            return None
