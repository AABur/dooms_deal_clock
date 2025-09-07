"""Telegram Client API service for fetching channel updates."""

import base64
import io
import os
import re
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Dict, List, Optional

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
            # Allow overriding session directory via env to persist in Docker volume.
            # Default keeps original name for tests/local runs.
            session_dir = os.getenv("TELEGRAM_SESSION_DIR")
            session_name = "dooms_deal_session"
            session_path = (
                os.path.join(session_dir, session_name) if session_dir else session_name
            )
            self.client = TelegramClient(session_path, api_id, config.TELEGRAM_API_HASH)
        return self.client

    async def connect(self, password: Optional[str] = None) -> None:
        """Connect to Telegram and authenticate.

        Args:
            password: Optional 2FA password. If not provided, uses value from config.
        """
        client = self._get_client()
        kwargs: Dict[str, Any] = {"phone": config.TELEGRAM_PHONE}
        pw = password if password not in (None, "") else config.TELEGRAM_2FA_PASSWORD
        if pw:
            try:
                import inspect

                if "password" in inspect.signature(client.start).parameters:
                    kwargs["password"] = pw
            except Exception:
                # If inspection fails, fall back to not passing password to keep compatibility in tests
                pass
        await client.start(**kwargs)
        # Tighten permissions on session file if present
        try:
            session_dir = os.getenv("TELEGRAM_SESSION_DIR")
            sess_file = (
                os.path.join(session_dir, "dooms_deal_session.session")
                if session_dir
                else "dooms_deal_session.session"
            )
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

    async def iter_channel_messages(self, min_date: Optional[datetime] = None) -> AsyncIterator[Message]:
        """Iterate channel messages, stopping when older than ``min_date``.

        Telethon's ``iter_messages`` in our pinned version doesn't support
        ``min_date`` kwarg. We iterate from newest to oldest and stop once a
        message is older than the provided ``min_date``.

        Args:
            min_date: Minimum datetime (UTC). Messages older than this are not yielded.
        """
        client = self._get_client()

        # Normalize to aware UTC for safe comparison with Telethon datetimes
        min_date_utc: Optional[datetime]
        if min_date is None:
            min_date_utc = None
        else:
            min_date_utc = min_date if min_date.tzinfo else min_date.replace(tzinfo=timezone.utc)

        async for message in client.iter_messages(self.channel_username):
            try:
                msg_dt: Optional[datetime] = getattr(message, "date", None)
                if msg_dt is not None and min_date_utc is not None:
                    # Telethon message dates are typically tz-aware (UTC)
                    if msg_dt < min_date_utc:
                        break
                yield message
            except Exception as e:  # pragma: no cover - skip problematic message
                logger.warning(f"Skipping message during iteration due to error: {e}")
                continue

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
