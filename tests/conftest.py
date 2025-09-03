"""Base fixtures for Dooms Deal Clock tests.

This module contains common fixtures used across all test modules to ensure
proper isolation and consistent behavior of tests regardless of execution order.
Fixes include aligning test schema with app models and proper async mocking.
"""

import sys
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Add project root to path to ensure imports work correctly
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="session")
def test_db_engine(tmp_path_factory):
    """Create a test database engine using a temporary SQLite file.

    Using a file-based SQLite allows multiple connections to see the same data,
    which is needed when FastAPI creates separate sessions per request.
    """
    db_dir = tmp_path_factory.mktemp("db")
    db_path = db_dir / "test_db.sqlite"
    engine = create_engine(
        f"sqlite:///{db_path}",
        echo=False,
        connect_args={"check_same_thread": False},
    )
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture
def test_db_session(test_db_engine) -> Generator[Session, None, None]:
    """Create a fresh test DB schema and session per test."""
    # Use the application's models metadata to ensure schema matches (including image_data)
    from app.utils.db import Base

    Base.metadata.create_all(bind=test_db_engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_db_engine)
    session = TestSessionLocal()

    try:
        yield session
    finally:
        session.close()
        # Drop all tables to isolate tests
        Base.metadata.drop_all(bind=test_db_engine)


@pytest.fixture
def test_client(test_db_session, mocker):
    """Create a FastAPI test client with test database."""
    # Clear any existing module imports to prevent cached values
    import sys

    modules_to_remove = [key for key in sys.modules.keys() if key.startswith("app.")]
    for module in modules_to_remove:
        sys.modules.pop(module, None)

    # Mock the config to prevent loading from .env
    mocker.patch.dict(
        "os.environ",
        {
            "DATABASE_URL": "sqlite:///:memory:",
            "TELEGRAM_API_ID": "12345",
            "TELEGRAM_API_HASH": "test_hash",
            "TELEGRAM_PHONE": "+1234567890",
            "DEBUG": "false",
            "LOG_LEVEL": "INFO",
        },
        clear=False,
    )

    # Patch app models to use the test engine/session (no migrations in dev)
    try:
        from sqlalchemy.orm import sessionmaker as _sessionmaker

        import app.utils.db as models_module

        models_module.engine = test_db_session.bind
        models_module.SessionLocal = _sessionmaker(autocommit=False, autoflush=False, bind=test_db_session.bind)

    except Exception:
        pass

    # Now import after environment is mocked
    import app.main as app_main
    import app.utils.db as models_module
    from app.main import app

    # Override the get_db dependency to use the shared test session
    def override_get_db():
        yield test_db_session

    app.dependency_overrides[app_main.get_db] = override_get_db

    with TestClient(app) as client:
        yield client

    # Clean up dependency override
    app.dependency_overrides.clear()


@pytest.fixture
def test_clock_update_model(test_db_session, mocker):
    """Provide ClockUpdate model that works with test database."""
    # Mock environment first
    mocker.patch.dict(
        "os.environ",
        {
            "DATABASE_URL": "sqlite:///:memory:",
            "TELEGRAM_API_ID": "12345",
            "TELEGRAM_API_HASH": "test_hash",
            "TELEGRAM_PHONE": "+1234567890",
        },
        clear=False,
    )

    from app.utils.db import ClockUpdate

    return ClockUpdate


@pytest.fixture
def mock_telegram_service(mocker):
    """Mock Telegram service using pytest-mock."""
    from app.telegram_api.client import TelegramService

    mock_service = mocker.Mock(spec=TelegramService)
    # Async methods
    mock_service.connect = mocker.AsyncMock()
    mock_service.disconnect = mocker.AsyncMock()
    mock_service.get_latest_messages = mocker.AsyncMock()
    mock_service.get_message_image_data = mocker.AsyncMock(return_value=None)
    # Sync helper
    mock_service.extract_time_from_message = mocker.MagicMock()

    return mock_service


@pytest.fixture
def mock_telegram_message(mocker):
    """Create a mock Telegram message."""
    from datetime import datetime

    message = mocker.MagicMock()
    message.id = 12345
    message.text = "🕐 23:42 - Дедлайн приближается!"
    message.date = datetime(2024, 1, 1, 23, 42, 0)

    return message


@pytest.fixture
def sample_clock_data():
    """Sample clock data for testing."""
    return {
        "message_id": 12345,
        "content": "🕐 23:42 - Дедлайн приближается!",
        "time_value": "23:42",
        "created_at": "2024-01-01T23:42:00Z",
    }


@pytest.fixture
def mock_config(mocker):
    """Mock configuration variables for testing."""
    test_config = {
        "DATABASE_URL": "sqlite:///:memory:",
        "DEBUG": False,
        "TELEGRAM_API_ID": 12345,
        "TELEGRAM_API_HASH": "test_hash",
        "TELEGRAM_PHONE": "+1234567890",
        "TELEGRAM_CHANNEL": "test_channel",
        "FETCH_INTERVAL": 60,
    }

    # Mock config attributes
    for key, value in test_config.items():
        mocker.patch(f"app.config.config.{key}", value)

    yield test_config


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset any singleton instances between tests."""
    # Clear any cached instances if they exist
    yield
    # Cleanup after test - can add specific cleanup here if needed


@pytest.fixture
def temp_directory():
    """Create a temporary directory for file operations."""
    import shutil

    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="ddc_test_")

    yield temp_dir

    # Clean up after test
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def mock_clock_service(mocker, mock_telegram_service):
    """Mock ClockService using pytest-mock."""
    from app.services.clock_service import ClockService

    mock_service = mocker.Mock(spec=ClockService)
    mock_service.telegram_service = mock_telegram_service
    mock_service.fetch_and_store_updates = mocker.AsyncMock()
    mock_service.get_latest_update = mocker.MagicMock()
    mock_service.get_time_remaining = mocker.MagicMock()
    return mock_service


@pytest.fixture
def authorized_telegram_client(mocker):
    """Mock authorized Telegram client."""
    mock_client = mocker.MagicMock()
    mock_client.connect = mocker.AsyncMock()
    mock_client.disconnect = mocker.AsyncMock()
    mock_client.is_connected = mocker.MagicMock(return_value=True)
    mock_client.get_messages = mocker.AsyncMock()

    mocker.patch("app.telegram_api.client.TelegramClient", return_value=mock_client)

    yield mock_client
