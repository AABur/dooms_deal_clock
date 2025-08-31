"""Tests for TelegramService media handling (no network)."""

import pytest

from app.telegram_api.client import TelegramService


@pytest.mark.asyncio
async def test_get_message_image_data_returns_none_without_media():
    service = TelegramService()

    class Message:
        media = None

    result = await service.get_message_image_data(Message())
    assert result is None


@pytest.mark.asyncio
async def test_get_message_image_data_returns_none_with_non_photo_media():
    service = TelegramService()

    class Message:
        media = object()  # Not a MessageMediaPhoto

    result = await service.get_message_image_data(Message())
    assert result is None
