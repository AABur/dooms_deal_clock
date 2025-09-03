"""Tests for the clock service module - only working tests."""

from datetime import UTC, datetime

import pytest

from app.utils.db import ClockUpdate
from app.services.clock_service import ClockService


@pytest.fixture
def clock_service(mock_telegram_service):
    """Create a ClockService instance with mocked telegram service."""
    service = ClockService()
    service.telegram_service = mock_telegram_service
    return service


@pytest.mark.asyncio
async def test_fetch_and_store_updates_success(clock_service, test_db_session, mock_telegram_message):
    """Test successful fetching and storing of updates."""
    # Setup mock telegram service
    clock_service.telegram_service.get_latest_messages.return_value = [mock_telegram_message]
    clock_service.telegram_service.extract_time_from_message.return_value = "23:42"

    # Execute
    result = await clock_service.fetch_and_store_updates(test_db_session)

    # Verify
    assert result == 1

    # Check database
    stored_update = test_db_session.query(ClockUpdate).first()
    assert stored_update is not None
    assert stored_update.message_id == 12345
    assert stored_update.content == "🕐 23:42 - Дедлайн приближается!"
    assert stored_update.time_value == "23:42"

    # Verify telegram service was called
    clock_service.telegram_service.connect.assert_called_once()
    clock_service.telegram_service.get_latest_messages.assert_called_once_with(limit=5)
    clock_service.telegram_service.disconnect.assert_called_once()


@pytest.mark.asyncio
async def test_fetch_and_store_updates_duplicate_message(clock_service, test_db_session, mock_telegram_message):
    """Test that duplicate messages are not stored."""
    # Setup: Add existing message to database
    existing_update = ClockUpdate(
        message_id=12345, content="Existing message", time_value="12:00", created_at=datetime.now(UTC)
    )
    test_db_session.add(existing_update)
    test_db_session.commit()

    # Setup mock telegram service
    clock_service.telegram_service.get_latest_messages.return_value = [mock_telegram_message]

    # Execute
    result = await clock_service.fetch_and_store_updates(test_db_session)

    # Verify
    assert result == 0  # No new updates stored

    # Check that only one record exists
    updates_count = test_db_session.query(ClockUpdate).count()
    assert updates_count == 1


@pytest.mark.asyncio
async def test_fetch_and_store_updates_no_text_message(clock_service, test_db_session, mocker):
    """Test handling of messages without text."""
    # Create message without text
    message_without_text = mocker.MagicMock()
    message_without_text.text = None
    message_without_text.id = 12345

    clock_service.telegram_service.get_latest_messages.return_value = [message_without_text]

    # Execute
    result = await clock_service.fetch_and_store_updates(test_db_session)

    # Verify
    assert result == 0

    # Check no records in database
    updates_count = test_db_session.query(ClockUpdate).count()
    assert updates_count == 0


@pytest.mark.asyncio
async def test_fetch_and_store_updates_multiple_messages(clock_service, test_db_session, mocker):
    """Test handling of multiple messages."""
    # Create multiple messages
    message1 = mocker.MagicMock()
    message1.id = 1
    message1.text = "First message with time 10:30"
    message1.date = datetime(2024, 1, 1, 10, 30, 0)

    message2 = mocker.MagicMock()
    message2.id = 2
    message2.text = "Second message with time 15:45"
    message2.date = datetime(2024, 1, 1, 15, 45, 0)

    clock_service.telegram_service.get_latest_messages.return_value = [message1, message2]
    clock_service.telegram_service.extract_time_from_message.side_effect = ["10:30", "15:45"]

    # Execute
    result = await clock_service.fetch_and_store_updates(test_db_session)

    # Verify
    assert result == 2

    # Check database
    updates = test_db_session.query(ClockUpdate).all()
    assert len(updates) == 2


@pytest.mark.asyncio
async def test_fetch_and_store_updates_exception_handling(clock_service, test_db_session):
    """Test exception handling during fetch and store."""
    # Setup telegram service to raise exception
    clock_service.telegram_service.get_latest_messages.side_effect = Exception("Connection error")

    # Execute
    result = await clock_service.fetch_and_store_updates(test_db_session)

    # Verify
    assert result == 0
    clock_service.telegram_service.disconnect.assert_called_once()


def test_get_latest_update_empty_database(clock_service, test_db_session):
    """Test getting latest update from empty database."""
    result = clock_service.get_latest_update(test_db_session)
    assert result is None


def test_get_recent_updates(clock_service, test_db_session):
    """Test getting recent updates."""
    # Setup: Add multiple updates
    updates_data = [
        (1, "Update 1", "10:00", datetime(2024, 1, 1, 10, 0, 0)),
        (2, "Update 2", "11:00", datetime(2024, 1, 1, 11, 0, 0)),
        (3, "Update 3", "12:00", datetime(2024, 1, 1, 12, 0, 0)),
        (4, "Update 4", "13:00", datetime(2024, 1, 1, 13, 0, 0)),
        (5, "Update 5", "14:00", datetime(2024, 1, 1, 14, 0, 0)),
    ]

    for msg_id, content, time_val, created in updates_data:
        update = ClockUpdate(message_id=msg_id, content=content, time_value=time_val, created_at=created)
        test_db_session.add(update)

    test_db_session.commit()

    # Execute
    recent = clock_service.get_recent_updates(test_db_session, limit=3)

    # Verify
    assert len(recent) == 3
    assert recent[0].message_id == 5  # Most recent first
    assert recent[1].message_id == 4
    assert recent[2].message_id == 3


def test_get_updates_count(clock_service, test_db_session):
    """Проверка, что get_updates_count возвращает общее число записей."""
    # Arrange: добавить N записей
    for i in range(1, 6):
        update = ClockUpdate(message_id=1000 + i, content=f"Update {i}", time_value=None)
        test_db_session.add(update)
    test_db_session.commit()

    # Act
    total = clock_service.get_updates_count(test_db_session)

    # Assert
    assert total == 5
